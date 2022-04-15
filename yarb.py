#!/usr/bin/python3

import os
import json
import time
import schedule
import pyfiglet
import argparse
import datetime
import listparser
import feedparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from bot import *
from utils import Color, Pattern

import requests
requests.packages.urllib3.disable_warnings()

today = datetime.datetime.now().strftime("%Y-%m-%d")


def update_today(data: list=[]):
    """更新today"""
    root_path = Path(__file__).absolute().parent
    data_path = root_path.joinpath('temp_data.json')
    today_path = root_path.joinpath('today.md')
    archive_path = root_path.joinpath(f'archive/{today.split("-")[0]}/{today}.md')

    if not data and data_path.exists():
        with open(data_path, 'r') as f1:
            data = json.load(f1)

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with open(today_path, 'w+') as f1, open(archive_path, 'w+') as f2:
        content = f'# 每日安全资讯（{today}）\n\n'
        for item in data:
            (feed, value), = item.items()
            content += f'- {feed}\n'
            for title, url in value.items():
                content += f'  - [{title}]({url})\n'
        f1.write(content)
        f2.write(content)


def update_rss(rss: dict, proxy_url=''):
    """更新订阅源文件"""
    proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

    (key, value), = rss.items()
    rss_path = root_path.joinpath(f'rss/{value["filename"]}')

    result = None
    if url := value.get('url'):
        r = requests.get(value['url'], proxies=proxy)
        if r.status_code == 200:
            with open(rss_path, 'w+') as f:
                f.write(r.text)
            print(f'[+] 更新完成：{key}')
            result = {key: rss_path}
        elif rss_path.exists():
            print(f'[-] 更新失败，使用旧文件：{key}')
            result = {key: rss_path}
        else:
            print(f'[-] 更新失败，跳过：{key}')
    else:
        print(f'[+] 本地文件：{key}')

    return result


def parseThread(url: str, proxy_url=''):
    """获取文章线程"""
    proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    title = ''
    result = {}
    try:
        r = requests.get(url, timeout=10, headers=headers, verify=False, proxies=proxy)
        r = feedparser.parse(r.content)
        title = r.feed.title
        for entry in r.entries:
            d = entry.get('published_parsed')
            if not d:
                d = entry.updated_parsed
            yesterday = datetime.date.today() + datetime.timedelta(-1)
            pubday = datetime.date(d[0], d[1], d[2])
            if pubday == yesterday:
                item = {entry.title: entry.link}
                print(item)
                result.update(item)
        Color.print_success(f'[+] {title}\t{url}\t{len(result.values())}/{len(r.entries)}')
    except Exception as e:
        Color.print_failed(f'[-] failed: {url}')
        print(e)
    return title, result


def init_bot(conf: dict, proxy_url=''):
    """初始化机器人"""
    bots = []
    for name, v in conf.items():
        if v['enabled']:
            key = os.getenv(v['secrets'])
            if not key:
                key = v['key']

            if name == 'qq':
                bot = globals()[f'{name}Bot'](v['group_id'])
                if bot.start_server(v['qq_id'], key):
                    bots.append(bot)
            elif name == 'telegram':
                bot = globals()[f'{name}Bot'](key, v['chat_id'], proxy_url)
                if bot.test_connect():
                    bots.append(bot)
            elif name == 'mail':
                bot = globals()[f'{name}Bot'](v['address'], key, v['receiver'], v['server'])
                bots.append(bot)
            else:
                bot = globals()[f'{name}Bot'](key, proxy_url)
                bots.append(bot)
    return bots


def init_rss(conf: dict, update: bool=False, proxy_url=''):
    """初始化订阅源"""
    rss_list = []
    enabled = [{k: v} for k, v in conf.items() if v['enabled']]
    for rss in enabled:
        if update:
            if rss := update_rss(rss, proxy_url):
                rss_list.append(rss)
        else:
            (key, value), = rss.items()
            rss_list.append({key: root_path.joinpath(f'rss/{value["filename"]}')})

    # 合并相同链接
    feeds = []
    for rss in rss_list:
        (_, value), = rss.items()
        try:
            rss = listparser.parse(open(value).read())
            for feed in rss.feeds:
                url = feed.url.strip().rstrip('/')
                short_url = url.split('://')[-1].split('www.')[-1]
                check = [feed for feed in feeds if short_url in feed]
                if not check:
                    feeds.append(url)
        except Exception as e:
            Color.print_failed(f'[-] 解析失败：{value}')
            print(e)

    Color.print_focus(f'[+] {len(feeds)} feeds')
    return feeds


def cleanup():
    """结束清理"""
    qqBot.kill_server()


def job(args):
    """定时任务"""
    print(f'{pyfiglet.figlet_format("yarb")}\n{today}')

    global root_path
    root_path = Path(__file__).absolute().parent
    if args.config:
        config_path = Path(args.config).expanduser().absolute()
    else:
        config_path = root_path.joinpath('config.json')
    with open(config_path) as f:
        conf = json.load(f)

    proxy_bot = conf['proxy']['url'] if conf['proxy']['bot'] else ''
    bots = init_bot(conf['bot'], proxy_bot)

    proxy_rss = conf['proxy']['url'] if conf['proxy']['rss'] else ''
    feeds = init_rss(conf['rss'], args.update, proxy_rss)

    results = []
    if args.test:
        # 测试数据
        results.extend({f'test{i}': {Pattern.create(i*500): 'test'}} for i in range(1, 20))
    else:
        # 获取文章
        numb = 0
        tasks = []
        with ThreadPoolExecutor(100) as executor:
            tasks.extend(executor.submit(parseThread, url, proxy_rss) for url in feeds)
            for task in as_completed(tasks):
                title, result = task.result()            
                if result:
                    numb += len(result.values())
                    results.append({title: result})
        Color.print_focus(f'[+] {len(results)} feeds, {numb} articles')

        # temp_path = root_path.joinpath('temp_data.json')
        # with open(temp_path, 'w+') as f:
        #     f.write(json.dumps(results, indent=4, ensure_ascii=False))
        #     Color.print_focus(f'[+] temp data: {temp_path}')

        # 更新today
        update_today(results)

    # 推送文章
    for bot in bots:
        bot.send(bot.parse_results(results))

    cleanup()


def argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', help='Update RSS config file', action='store_true', required=False)
    parser.add_argument('--cron', help='Execute scheduled tasks every day (eg:"11:00")', type=str, required=False)
    parser.add_argument('--config', help='Use specified config file', type=str, required=False)
    parser.add_argument('--test', help='Test bot', action='store_true', required=False)
    return parser.parse_args()


if __name__ == '__main__':
    args = argument()
    if args.cron:
        schedule.every().day.at(args.cron).do(job, args)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        job(args)

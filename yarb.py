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
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from bot import *
from utils import Color

import requests
requests.packages.urllib3.disable_warnings()


def update_today(data: list=[]):
    """更新today"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    root_path = Path(__file__).absolute().parent
    data_path = root_path.joinpath('temp_data.json')
    today_path = root_path.joinpath('today.md')
    archive_path = root_path.joinpath(f'archive/{today.split("-")[0]}/{today}.md')

    if not data:
        if data_path.exists():
            with open(data_path, 'r') as f1:
                data = json.load(f1)
            # data_path.unlink(missing_ok=True)
        else:
            Color.print_failed(f'[-] 文件不存在 {data_path}')
            return

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


def update_rss(rss: dict):
    """更新订阅源文件"""
    (key, value), = rss.items()
    rss_path = root_path.joinpath(f'rss/{value["filename"]}')

    result = None
    url = value.get('url')
    if url:
        r = requests.get(value['url'])
        if r.status_code == 200:
            with open(rss_path, 'w+') as f:
                f.write(r.text)
            print(f'[+] 更新完成：{key}')
            result = {key: rss_path}
        else:
            if rss_path.exists():
                print(f'[-] 更新失败，使用旧文件：{key}')
                result = {key: rss_path}
            else:
                print(f'[-] 更新失败，跳过：{key}')
    else:
        print(f'[+] 本地文件：{key}')

    return result


def parseThread(url: str):
    """获取文章线程"""
    title = ''
    result = {}
    try:
        r = requests.get(url, timeout=10, verify=False)
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


def init_bot(conf: dict):
    """初始化机器人"""
    bots = defaultdict(list)
    for k, v in conf.items():
        if v['enabled']:
            key = os.getenv(v['secrets'])
            if not key:
                key = v['key']
            bot = globals()[f'{k}Bot'](key)
            bots[v['msgtype']].append(bot)
    return bots


def init_rss(conf: dict, update: bool=False):
    """初始化订阅源"""
    temp_list = [{k: v} for k, v in conf.items() if v['enabled']]
    rss_list = []
    if update:
        for rss in temp_list:
            rss = update_rss(rss)
            if rss:
                rss_list.append(rss)
    else:
        for rss in temp_list:
            (key, value), = rss.items()
            rss_list.append({key: root_path.joinpath(f'rss/{value["filename"]}')})

    # 合并相同链接
    feeds = []
    for rss in rss_list:
        (_, value), = rss.items()
        try:
            rss = listparser.parse(open(value).read())
            for feed in rss.feeds:
                url = feed.url.rstrip('/')
                short_url = url.split('://')[-1].split('www.')[-1]
                check = [feed for feed in feeds if short_url in feed]
                if not check:
                    feeds.append(url)
        except Exception as e:
            Color.print_failed(f'[-] 解析失败：{value}')
            print(e)

    Color.print_focus(f'[+] {len(feeds)} feeds')
    return feeds


def send_text(bots: list, results: list):
    """发送text格式的消息"""
    if not bots or not results:
        return
    Color.print_focus(f'[+] text: {str(bots)}')

    num1 = 0
    num2 = 0
    text = ''
    for result in results:
        (key, value), = result.items()
        text += f'{key}\n\n'
        for k, v in value.items():
            text += f'{k}\n{v}\n\n'
            num1 += 1

        # 合并消息，最少10行/条
        if num1 >= 10:
            text = text.strip()
            print(text)

            # 发送
            for bot in bots:
                bot.send_text(text)

            # 频率限制，最多20条/分钟
            num2 += 1
            if num2 >= 20:
                time.sleep(60)

            # 恢复
            num1 = 0
            text = ''


def send_markdown(bots: list, results: list):
    """发送markdown格式的消息"""
    if not bots or not results:
        return

    Color.print_focus(f'[+] markdown: {str(bots)}')
    for result in results:
        (title, value), = result.items()
        text = ''
        for k, v in value.items():
            text += f'> {k}\n\n[{v}]({v})\n'
        print(text)

        for bot in bots:
            bot.send_markdown(title, text)


def job(args):
    """定时任务"""
    print(pyfiglet.figlet_format('yarb'))
    print(datetime.datetime.now())

    global root_path
    root_path = Path(__file__).absolute().parent
    if args.config:
        config_path = Path(args.config).expanduser().absolute()
    else:
        config_path = root_path.joinpath('config.json')
    with open(config_path) as f:
        conf = json.load(f)
    bots = init_bot(conf['bot'])
    feeds = init_rss(conf['rss'], args.update)

    # 获取文章
    results = []
    numb = 0
    tasks = []
    with ThreadPoolExecutor(100) as executor:
        for url in feeds:
            tasks.append(executor.submit(parseThread, url))
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

    # 推送文章
    send_text(bots.get('text'), results)
    send_markdown(bots.get('markdown'), results)

    # 更新today
    update_today(results)


def argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', help='Update RSS config file', action='store_true', required=False)
    parser.add_argument('--cron', help='Execute scheduled tasks every day (eg:"11:00")', type=str, required=False)
    parser.add_argument('--config', help='Use specified config file', type=str, required=False)
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

import time
import json
import yaml
import telegram
import requests
import smtplib
import subprocess
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime
from pyrate_limiter import Duration, Rate, InMemoryBucket, Limiter

from utils import *

__all__ = ["feishuBot", "wecomBot", "dingtalkBot", "qqBot", "telegramBot", "mailBot"]
today = datetime.now().strftime("%Y-%m-%d")


class feishuBot:
    """飞书群机器人
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
    """

    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {
            'http': None, 'https': None}

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = f'[ {feed} ]\n\n'
            for title, link in value.items():
                text += f'{title}\n{link}\n\n'
            text_list.append(text.strip())
        return text_list

    async def send(self, text_list: list):
        for text in text_list:
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            data = {"msg_type": "text", "content": {"text": text}}
            headers = {'Content-Type': 'application/json'}
            url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.key}'
            r = requests.post(url=url, headers=headers,
                              data=json.dumps(data), proxies=self.proxy)

            if r.status_code == 200:
                console.print('[+] feishuBot 发送成功', style='bold green')
            else:
                console.print('[-] feishuBot 发送失败', style='bold red')
                print(r.text)

    async def send_markdown(self, text):
        # TODO 富文本
        data = {"msg_type": "text", "content": {"text": text}}
        self.send(data)


class wecomBot:
    """企业微信群机器人
    https://developer.work.weixin.qq.com/document/path/91770
    """

    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {
            'http': None, 'https': None}

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = f'## {feed}\n'
            for title, link in value.items():
                text += f'- [{title}]({link})\n'
            text_list.append(text.strip())
        return text_list

    async def send(self, text_list: list):
        rates = [Rate(20, Duration.MINUTE)] # 频率限制，20条/分钟
        bucket = InMemoryBucket(rates)
        limiter = Limiter(bucket, max_delay=Duration.MINUTE.value)

        for text in text_list:
            limiter.try_acquire('identity')
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            data = {"msgtype": "markdown", "markdown": {"content": text}}
            headers = {'Content-Type': 'application/json'}
            url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}'
            r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

            if r.status_code == 200:
                console.print('[+] wecomBot 发送成功', style='bold green')
            else:
                console.print('[-] wecomBot 发送失败', style='bold red')
                print(r.text)


class dingtalkBot:
    """钉钉群机器人
    https://open.dingtalk.com/document/robots/custom-robot-access
    """

    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {
            'http': None, 'https': None}

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = ''.join(
                f'- [{title}]({link})\n' for title, link in value.items())
            text_list.append([feed, text.strip()])
        return text_list

    async def send(self, text_list: list):
        rates = [Rate(20, Duration.MINUTE)] # 频率限制，20条/分钟
        bucket = InMemoryBucket(rates)
        limiter = Limiter(bucket, max_delay=Duration.MINUTE.value)

        for (feed, text) in text_list:
            limiter.try_acquire('identity')

            text = f'## {feed}\n{text}'
            text += f"\n\n <!-- Powered by Yarb. -->"
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            data = {"msgtype": "markdown", "markdown": {
                "title": feed, "text": text}}
            headers = {'Content-Type': 'application/json'}
            url = f'https://oapi.dingtalk.com/robot/send?access_token={self.key}'
            r = requests.post(url=url, headers=headers,
                                data=json.dumps(data), proxies=self.proxy)

            if r.status_code == 200:
                console.print('[+] dingtalkBot 发送成功', style='bold green')
            else:
                console.print('[-] dingtalkBot 发送失败', style='bold red')
                print(r.text)


class qqBot:
    """QQ群机器人
    https://github.com/Mrs4s/go-cqhttp
    """
    cqhttp_path = Path(__file__).absolute().parent.joinpath('cqhttp')

    def __init__(self, group_id: list) -> None:
        self.server = 'http://127.0.0.1:5700'
        self.group_id = group_id

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = f'[ {feed} ]\n\n'
            for title, link in value.items():
                text += f'{title}\n{link}\n\n'
            text_list.append(text.strip())
        return text_list

    async def send(self, text_list: list):
        rates = [Rate(20, Duration.MINUTE)] # 频率限制，20条/分钟
        bucket = InMemoryBucket(rates)
        limiter = Limiter(bucket, max_delay=Duration.MINUTE.value)

        for text in text_list:
            limiter.try_acquire('identity')
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            for id in self.group_id:
                try:
                    r = requests.post(f'{self.server}/send_group_msg?group_id={id}&&message={text}')
                    if r.status_code == 200:
                        console.print(f'[+] qqBot 发送成功 {id}', style='bold green')
                    else:
                        console.print(f'[-] qqBot 发送失败 {id}', style='bold red')
                except Exception as e:
                    console.print(f'[-] qqBot 发送失败 {id}', style='bold red')
                    print(e)

    async def start_server(self, qq_id, qq_passwd, timeout=60):
        config_path = self.cqhttp_path.joinpath('config.yml')
        with open(config_path, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            data['account']['uin'] = int(qq_id)
            data['account']['password'] = qq_passwd
        with open(config_path, 'w+') as f:
            yaml.dump(data, f)

        subprocess.run('cd cqhttp && ./go-cqhttp -d', shell=True)

        timeout = time.time() + timeout
        while True:
            try:
                requests.get(self.server)
                console.print('[+] qqBot 启动成功', style='bold green')
                return True
            except Exception as e:
                time.sleep(1)

            if time.time() > timeout:
                qqBot.kill_server()
                console.print('[-] qqBot 启动失败', style='bold red')
                return False

    @classmethod
    def kill_server(cls):
        pid_path = cls.cqhttp_path.joinpath('go-cqhttp.pid')
        subprocess.run(f'cat {pid_path} | xargs kill',
                       stderr=subprocess.DEVNULL, shell=True)


class mailBot:
    """邮件机器人
    """

    def __init__(self, sender, passwd, receiver: str, fromwho='', server='') -> None:
        self.sender = sender
        self.receiver = receiver
        self.fromwho = fromwho or sender
        server = server or self.get_server(sender)

        self.smtp = smtplib.SMTP_SSL(server)
        self.smtp.login(sender, passwd)

    def get_server(self, sender: str):
        key = sender.rstrip('.com').split('@')[-1]
        server = {
            'qq': 'smtp.qq.com',
            'foxmail': 'smtp.qq.com',
            '163': 'smtp.163.com',
            'sina': 'smtp.sina.com',
            'gmail': 'smtp.gmail.com',
            'outlook': 'smtp.live.com',
        }
        return server.get(key, f'smtp.{key}.com')

    @staticmethod
    def parse_results(results: list):
        text = f'<html><head><h1>每日安全资讯（{today}）</h1></head><body>'
        for result in results:
            (feed, value), = result.items()
            text += f'<h3>{feed}</h3><ul>'
            for title, link in value.items():
                text += f'<li><a href="{link}">{title}</a></li>'
            text += '</ul>'
        text += '<br><br><b>如不需要，可直接回复本邮件退订。</b></body></html>'
        print(text)
        return text

    async def send(self, text: str):
        print(f'{len(text)} {text[:50]}...{text[-50:]}')

        msg = MIMEText(text, 'html')
        msg['Subject'] = Header(f'每日安全资讯（{today}）')
        msg['From'] = self.fromwho
        msg['To'] = self.receiver

        try:
            self.smtp.sendmail(
                self.sender, self.receiver.split(','), msg.as_string())
            console.print('[+] mailBot 发送成功', style='bold green')
        except Exception as e:
            console.print('[+] mailBot 发送失败', style='bold red')
            print(e)


class telegramBot:
    """Telegram机器人
    https://core.telegram.org/bots/api
    """

    def __init__(self, key, chat_id: list, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {
            'http': None, 'https': None}

        proxy = telegram.request.HTTPXRequest(proxy_url=None)
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=key, request=proxy)

    async def test_connect(self):
        try:
            await self.bot.get_me()
            return True
        except Exception as e:
            console.print('[-] telegramBot 连接失败', style='bold red')
            return False

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = f'<b>{feed}</b>\n'
            for idx, (title, link) in enumerate(value.items()):
                text += f'{idx+1}. <a href="{link}">{title}</a>\n'
            text_list.append(text.strip())
        return text_list

    async def send(self, text_list: list):
        rates = [Rate(20, Duration.MINUTE)] # 频率限制，20条/分钟
        bucket = InMemoryBucket(rates)
        limiter = Limiter(bucket, max_delay=Duration.MINUTE.value)

        for text in text_list:
            limiter.try_acquire('identity')
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            for id in self.chat_id:
                try:
                    self.bot.send_message(chat_id=id, text=text, parse_mode='HTML')
                    console.print(f'[+] telegramBot 发送成功 {id}', style='bold green')
                except Exception as e:
                    console.print(f'[-] telegramBot 发送失败 {id}', style='bold red')
                    print(e)

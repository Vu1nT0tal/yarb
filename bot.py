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
from pyrate_limiter import Duration, Limiter, RequestRate

from utils import Color

__all__ = ["feishuBot", "wecomBot", "dingtalkBot", "qqBot", "telegramBot", "mailBot"]
today = datetime.now().strftime("%Y-%m-%d")


class feishuBot:
    """飞书群机器人
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
    """
    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

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

    def send(self, text_list: list):
        for text in text_list:
            print(f'{len(text)} {text[:50]}...{text[-50:]}')

            data = {"msg_type": "text", "content": {"text": text}}
            headers = {'Content-Type': 'application/json'}
            url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.key}'
            r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

            if r.status_code == 200:
                Color.print_success('[+] feishuBot 发送成功')
            else:
                Color.print_failed('[-] feishuBot 发送失败')
                print(r.text)

    def send_markdown(self, text):
        # TODO 富文本
        data = {"msg_type": "text", "content": {"text": text}}
        self.send(data)


class wecomBot:
    """企业微信群机器人
    https://developer.work.weixin.qq.com/document/path/91770
    """
    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

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

    def send(self, text_list: list):
        limiter = Limiter(RequestRate(20, Duration.MINUTE))     # 频率限制，20条/分钟
        for text in text_list:
            with limiter.ratelimit('identity', delay=True):
                print(f'{len(text)} {text[:50]}...{text[-50:]}')

                data = {"msgtype": "markdown", "markdown": {"content": text}}
                headers = {'Content-Type': 'application/json'}
                url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}'
                r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

                if r.status_code == 200:
                    Color.print_success('[+] wecomBot 发送成功')
                else:
                    Color.print_failed('[-] wecomBot 发送失败')
                    print(r.text)


class dingtalkBot:
    """钉钉群机器人
    https://open.dingtalk.com/document/robots/custom-robot-access
    """
    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

    @staticmethod
    def parse_results(results: list):
        text_list = []
        for result in results:
            (feed, value), = result.items()
            text = ''.join(f'- [{title}]({link})\n' for title, link in value.items())
            text_list.append([feed, text.strip()])
        return text_list

    def send(self, text_list: list):
        limiter = Limiter(RequestRate(20, Duration.MINUTE))     # 频率限制，20条/分钟
        for (feed, text) in text_list:
            with limiter.ratelimit('identity', delay=True):
                print(f'{len(text)} {text[:50]}...{text[-50:]}')

                data = {"msgtype": "markdown", "markdown": {"title": feed, "text": text}}
                headers = {'Content-Type': 'application/json'}
                url = f'https://oapi.dingtalk.com/robot/send?access_token={self.key}'
                r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

                if r.status_code == 200:
                    Color.print_success('[+] dingtalkBot 发送成功')
                else:
                    Color.print_failed('[-] dingtalkBot 发送失败')
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

    def send(self, text_list: list):
        limiter = Limiter(RequestRate(20, Duration.MINUTE))     # 频率限制，20条/分钟
        for text in text_list:
            with limiter.ratelimit('identity', delay=True):
                print(f'{len(text)} {text[:50]}...{text[-50:]}')

                for id in self.group_id:
                    try:
                        r = requests.post(f'{self.server}/send_group_msg?group_id={id}&&message={text}')
                        if r.status_code == 200:
                            Color.print_success(f'[+] qqBot 发送成功 {id}')
                        else:
                            Color.print_failed(f'[-] qqBot 发送失败 {id}')
                    except Exception as e:
                        Color.print_failed(f'[-] qqBot 发送失败 {id}')
                        print(e)

    def start_server(self, qq_id, qq_passwd, timeout=60):
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
                Color.print_success('[+] qqBot 启动成功')
                return True
            except Exception as e:
                time.sleep(1)

            if time.time() > timeout:
                qqBot.kill_server()
                Color.print_failed('[-] qqBot 启动失败')
                return False

    @classmethod
    def kill_server(cls):
        pid_path = cls.cqhttp_path.joinpath('go-cqhttp.pid')
        subprocess.run(f'cat {pid_path} | xargs kill', stderr=subprocess.DEVNULL, shell=True)


class mailBot:
    """邮件机器人
    """
    def __init__(self, sender, passwd, receiver: list, server='') -> None:
        self.sender = sender
        self.receiver = receiver
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
        return text

    def send(self, text: str):
        print(f'{len(text)} {text[:50]}...{text[-50:]}')
        print(text)

        msg = MIMEText(text, 'html')
        msg['Subject'] = Header(f'每日安全资讯（{today}）')
        msg['From'] = f'security-bot <{self.sender}>'
        msg['To'] = ','.join(self.receiver)

        try:
            self.smtp.sendmail(self.sender, self.receiver, msg.as_string())
            Color.print_success('[+] mailBot 发送成功')
        except Exception as e:
            Color.print_failed('[+] mailBot 发送失败')
            print(e)


class telegramBot:
    """Telegram机器人
    https://core.telegram.org/bots/api
    """
    def __init__(self, key, chat_id: list, proxy_url='') -> None:
        proxy = telegram.utils.request.Request(proxy_url=proxy_url)
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=key, request=proxy)

    def test_connect(self):
        try:
            self.bot.get_me()
            return True
        except Exception as e:
            Color.print_failed('[-] telegramBot 连接失败')
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

    def send(self, text_list: list):
        limiter = Limiter(RequestRate(20, Duration.MINUTE))     # 频率限制，20条/分钟
        for text in text_list:
            with limiter.ratelimit('identity', delay=True):
                print(f'{len(text)} {text[:50]}...{text[-50:]}')

                for id in self.chat_id:
                    try:
                        self.bot.send_message(chat_id=id, text=text, parse_mode='HTML')
                        Color.print_success(f'[+] telegramBot 发送成功 {id}')
                    except Exception as e:
                        Color.print_failed(f'[-] telegramBot 发送失败 {id}')
                        print(e)

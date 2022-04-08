import os
import time
import json
import yaml
import requests
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

from utils import Color

__all__ = ["feishuBot", "wecomBot", "dingtalkBot", "qqBot", "mailBot"]


class feishuBot:
    """飞书群机器人
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
    """
    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

        if r.status_code == 200:
            Color.print_success('[+] feishuBot 发送成功')
        else:
            Color.print_failed('[-] feishuBot 发送失败')
            print(r.text)

    def send_text(self, text):
        data = {"msg_type": "text", "content": {"text": text}}
        self.send(data)

    def send_markdown(self, title, text):
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

    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

        if r.status_code == 200:
            Color.print_success('[+] wecomBot 发送成功')
        else:
            Color.print_failed('[-] wecomBot 发送失败')
            print(r.text)

    def send_text(self, text):
        data = {"msgtype": "text", "text": {"content": text}}
        self.send(data)

    def send_markdown(self, title, text):
        data = {"msgtype": "markdown", "markdown": {"content": f'## {title}\n{text}'}}
        self.send(data)


class dingtalkBot:
    """钉钉群机器人
    https://open.dingtalk.com/document/robots/custom-robot-access
    """
    def __init__(self, key, proxy_url='') -> None:
        self.key = key
        self.proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://oapi.dingtalk.com/robot/send?access_token={self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data), proxies=self.proxy)

        if r.status_code == 200:
            Color.print_success('[+] dingtalkBot 发送成功')
        else:
            Color.print_failed('[-] dingtalkBot 发送失败')
            print(r.text)

    def send_text(self, text):
        data = {"msgtype": "text", "text": {"content": text}}
        self.send(data)

    def send_markdown(self, title, text):
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
        self.send(data)


class qqBot:
    """QQ群机器人
    https://github.com/Mrs4s/go-cqhttp
    """
    cqhttp_path = Path(__file__).absolute().parent.joinpath('cqhttp')

    def __init__(self, group_id) -> None:
        self.server = 'http://127.0.0.1:5700'
        self.group_id = group_id

    def send_text(self, text):
        try:
            r = requests.post(f'{self.server}/send_group_msg?group_id={self.group_id}&&message={text}')
            if r.status_code == 200:
                Color.print_success('[+] qqBot 发送成功')
            else:
                Color.print_failed('[-] qqBot 发送失败')
        except Exception as e:
            Color.print_failed('[-] qqBot 发送失败')
            print(e)

    def start_server(self, qq_id, qq_passwd, timeout=60):
        config_path = self.cqhttp_path.joinpath('config.yml')
        with open(config_path, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            data['account']['uin'] = int(qq_id)
            data['account']['password'] = qq_passwd
        with open(config_path, 'w+') as f:
            yaml.dump(data, f)

        os.system('cd cqhttp && ./go-cqhttp -d')

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
        os.system(f'cat {pid_path} | xargs kill >/dev/null 2>&1')


class mailBot:
    """邮件机器人
    """
    def __init__(self, sender, passwd, receiver: list, server='') -> None:
        self.sender = sender
        self.receiver = receiver
        server = server if server else self.get_server(sender)

        self.smtp = smtplib.SMTP_SSL(server)
        self.smtp.login(sender, passwd)

    def get_server(self, sender):
        key = sender.rstrip('.com').split('@')[-1]
        server = {
            'qq': 'smtp.qq.com',
            'foxmail': 'smtp.qq.com',
            '163': 'smtp.163.com',
            'sina': 'smtp.sina.com',
            'gmail': 'smtp.gmail.com',
            'outlook': 'smtp.live.com',
        }
        if key in server:
            return server[key]
        else:
            return f'smtp.{key}.com'

    def send_long_text(self, text):
        today = datetime.now().strftime("%Y-%m-%d")
        msg = MIMEText(text)
        msg['Subject'] = Header(f'每日安全资讯（{today}）')
        msg['From'] = 'yarb-security-bot'

        self.smtp.sendmail(self.sender, self.receiver, msg.as_string())

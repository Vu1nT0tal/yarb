import json
import requests

from utils import Color

__all__ = ["feishuBot", "wecomBot", "dingtalkBot"]


class feishuBot:
    """飞书群机器人
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
    """
    def __init__(self, key) -> None:
        self.key = key

    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data))

        if r.status_code == 200:
            Color.print_success(f'[+] feishuBot 发送成功')
        else:
            Color.print_failed(f'[-] feishuBot 发送失败')
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
    def __init__(self, key) -> None:
        self.key = key

    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data))

        if r.status_code == 200:
            Color.print_success(f'[+] wecomBot 发送成功')
        else:
            Color.print_failed(f'[-] wecomBot 发送失败')
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
    def __init__(self, key) -> None:
        self.key = key
    
    def send(self, data):
        headers = {'Content-Type': 'application/json'}
        url = f'https://oapi.dingtalk.com/robot/send?access_token={self.key}'
        r = requests.post(url=url, headers=headers, data=json.dumps(data))

        if r.status_code == 200:
            Color.print_success(f'[+] dingtalkBot 发送成功')
        else:
            Color.print_failed(f'[-] dingtalkBot 发送失败')
            print(r.text)

    def send_text(self, text):
        data = {"msgtype": "text", "text": {"content": text}}
        self.send(data)

    def send_markdown(self, title, text):
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
        self.send(data)

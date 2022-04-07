import json
import requests

from utils import Color


class feishuBot:
    """飞书群机器人
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
    """
    def __init__(self, key) -> None:
        self.key = key

    def send_text(self, text):
        headers = {'Content-Type': 'application/json'}
        data = {"msg_type": "text", "content": {"text": text}}
        r = requests.post(f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.key}', headers=headers, data=json.dumps(data))

        if r.status_code == 200:
            Color.print_success(f'[+] feishuBot 发送成功')
        else:
            Color.print_failed(f'[-] feishuBot 发送失败')
            print(r.text)

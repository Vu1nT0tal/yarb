# yarb (Yet Another Rss Bot)

另一个方便安全研究人员获取每日安全日报的爬虫和推送程序。支持导入 opml 文件从而批量订阅 RSS，因此可以订阅任何东西，而不局限于安全。

**懒人福音，每日自动更新，点击右上角 Watch 即可：[每日安全资讯](./today.md)，[历史存档](./archive)**

- [yarb (Yet Another Rss Bot)](#yarb-yet-another-rss-bot)
  - [安装](#安装)
  - [运行](#运行)
    - [本地运行](#本地运行)
    - [Github Actions](#github-actions)
  - [订阅源](#订阅源)
  - [开源协议](#开源协议)
  - [Stargazers over time](#stargazers-over-time)

## 安装

```sh
$ git clone https://github.com/firmianay/yarb.git
$ cd yarb && ./install.sh
```

## 运行

### 本地运行

编辑配置文件 `config.json`，启用所需的订阅源和机器人（key 也可以通过环境变量传入），最好启用代理。

```sh
$ ./yarb.py --help
usage: yarb.py [-h] [--update] [--cron CRON] [--config CONFIG]

optional arguments:
  -h, --help       show this help message and exit
  --update         Update RSS config file
  --cron CRON      Execute scheduled tasks every day (eg:"11:00")
  --config CONFIG  Use specified config file

# 单次任务
$ ./yarb.py

# 每日定时任务
$ nohup ./yarb.py --cron 11:00 > run.log 2>&1 &
```

### Github Actions

利用 Github Actions 提供的服务，你只需要 fork 本项目，在 Settings 中添加 Actions secrets，就部署完成了。

目前支持的推送机器人及对应的 secrets：

- [飞书群机器人](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN)：`FEISHU_KEY`
- [企业微信群机器人](https://developer.work.weixin.qq.com/document/path/91770)：`WECOM_KEY`
- [钉钉群机器人](https://open.dingtalk.com/document/robots/custom-robot-access)：`DINGTALK_KEY`
- [QQ群机器人](https://github.com/Mrs4s/go-cqhttp)：`QQ_KEY`（需要关闭登录设备锁）

## 订阅源

订阅源默认来自以下仓库，自动去重。

- [CyberSecurityRSS](https://github.com/zer0yu/CyberSecurityRSS)
- [Chinese-Security-RSS](https://github.com/zhengjim/Chinese-Security-RSS)
- [awesome-security-feed](https://github.com/mrtouch93/awesome-security-feed)
- [chinese-independent-blogs](https://github.com/timqian/chinese-independent-blogs)

添加自定义订阅有两种方法：

1. 在 `config.json` 中添加本地或远程仓库：

```json
{
  "rss": {
      "CustomRSS": {
          "enabled": true,
          "filename": "CustomRSS.opml"
      },
      "CyberSecurityRSS": {
          "enabled": true,
          "url": "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/CyberSecurityRSS.opml",
          "filename": "CyberSecurityRSS.opml"
      },
```

2. 在 `rss/CustomRSS.opml` 中添加链接：

```opml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
<head><title>CustomRSS</title></head>
<body>
<outline xmlUrl="https://rsshub.app/hackerone/hacktivity" title="HackerOne Hacker Activity" text="HackerOne Hacker Activity" type="rss" htmlUrl="https://hackerone.com/hacktivity" />
</body>
</opml>
```

## 开源协议

yarb use SATA(Star And Thank Author) [License](./LICENSE), so you have to star this project before using. 🙏

## Stargazers over time

[![Stargazers over time](https://starchart.cc/firmianay/yarb.svg)](https://starchart.cc/firmianay/yarb)

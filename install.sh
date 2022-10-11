#!/bin/bash

python3 -m pip install -r requirements.txt

sudo apt-get install -y wget
wget -q https://github.com/Mrs4s/go-cqhttp/releases/download/v1.0.0-rc2/go-cqhttp_linux_amd64.tar.gz -O ./cqhttp/go-cqhttp.tar.gz
cd cqhttp && tar xzf go-cqhttp.tar.gz go-cqhttp && rm go-cqhttp.tar.gz

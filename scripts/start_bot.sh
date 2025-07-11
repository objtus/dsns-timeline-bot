#!/bin/bash
# DSNS Timeline Bot 起動スクリプト（systemd用）

cd /home/objtus/dsns_timeline_bot

# 仮想環境を有効化してmain.pyを実行
source .venv/bin/activate
exec python main.py 
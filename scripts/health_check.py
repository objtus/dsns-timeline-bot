#!/usr/bin/env python3
"""
分散SNS関連年表bot - systemd用データ更新・定期投稿スクリプト

このスクリプトはsystemd-timerから呼び出され、
データ更新や定期投稿処理のみを実行します。

main.pyの一部機能を呼び出す形で設計してください。
"""
import asyncio
from main import DSNSTimelineBot

async def main():
    bot = DSNSTimelineBot()
    await bot.start_bot()  # 必要に応じて定期投稿やデータ更新のみ呼び出しに変更可
    await bot.shutdown_bot()

if __name__ == "__main__":
    asyncio.run(main())

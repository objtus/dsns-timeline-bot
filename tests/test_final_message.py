#!/usr/bin/env python3
"""
最終メッセージ生成テスト
"""

import asyncio
import pytest
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.today_handler import TodayHandler

@pytest.mark.asyncio
async def test_message_generation():
    """メッセージ生成テスト"""
    print("🔍 メッセージ生成テスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = TodayHandler(config, database, data_service, None)
        
        # 今日のメッセージ生成
        message = await handler.get_today_message()
        
        print(f"生成されたメッセージ: {message[:100]}...")
        
        assert message is not None, "メッセージが生成されませんでした"
        assert len(message) > 0, "メッセージが空です"
        
        print("✅ メッセージ生成テスト成功")
        assert True, "メッセージ生成テストが成功しました"
        
    except Exception as e:
        print(f"❌ メッセージ生成テスト失敗: {e}")
        pytest.fail(f"メッセージ生成テストが失敗しました: {e}")

if __name__ == "__main__":
    print("🚀 最終メッセージ生成テスト")
    print("pytest形式に変更されたため、以下のコマンドで実行してください:")
    print("PYTHONPATH=. python -m pytest tests/test_final_message.py -v") 
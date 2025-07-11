#!/usr/bin/env python3
"""
ステータス機能テスト
"""

import asyncio
import pytest
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.status_handler import StatusHandler

@pytest.mark.asyncio
async def test_status_functionality():
    """ステータス機能テスト"""
    print("🔍 ステータス機能テスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = StatusHandler(config, database, data_service)
        
        # システムステータス取得（基本ステータスを取得）
        status_message = await handler._handle_basic_status()
        
        print(f"システムステータス: {status_message[:100]}...")
        
        assert status_message is not None, "ステータスが取得できませんでした"
        assert len(status_message) > 0, "ステータスメッセージが空です"
        assert "分散SNS年表bot" in status_message, "ステータスメッセージが不正です"
        
        print("✅ ステータス機能テスト成功")
        assert True, "ステータス機能テストが成功しました"
        
    except Exception as e:
        print(f"❌ ステータス機能テスト失敗: {e}")
        pytest.fail(f"ステータス機能テストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_command_parsing():
    """コマンド解析テスト"""
    print("🔍 コマンド解析テスト開始...")
    
    try:
        from command_router import CommandRouter
        
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        router = CommandRouter(config, database, data_service)
        
        # ステータスコマンドの解析
        command = "status"
        parsed = router.parse_command(command)
        
        print(f"解析結果: {parsed}")
        
        assert parsed is not None, "コマンド解析が失敗しました"
        assert 'type' in parsed, "typeが存在しません"
        assert parsed['type'] == 'status', "ステータスコマンドとして解析されませんでした"
        
        print("✅ コマンド解析テスト成功")
        assert True, "コマンド解析テストが成功しました"
        
    except Exception as e:
        print(f"❌ コマンド解析テスト失敗: {e}")
        pytest.fail(f"コマンド解析テストが失敗しました: {e}")

if __name__ == "__main__":
    print("🚀 ステータス機能テスト")
    print("pytest形式に変更されたため、以下のコマンドで実行してください:")
    print("PYTHONPATH=. python -m pytest tests/test_status_functionality.py -v") 
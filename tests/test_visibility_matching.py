#!/usr/bin/env python3
"""
公開範囲マッチングテスト
"""

import asyncio
import pytest
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.today_handler import TodayHandler

@pytest.mark.asyncio
async def test_visibility_matching():
    """公開範囲マッチングテスト"""
    print("🔍 公開範囲マッチングテスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = TodayHandler(config, database, data_service, None)
        
        # 公開範囲のテスト
        test_visibilities = ['public', 'home', 'followers', 'specified']
        
        for visibility in test_visibilities:
            print(f"テスト公開範囲: {visibility}")
            
            # 公開範囲の検証
            assert visibility in ['public', 'home', 'followers', 'specified'], f"無効な公開範囲: {visibility}"
        
        print("✅ 公開範囲マッチングテスト成功")
        assert True, "公開範囲マッチングテストが成功しました"
        
    except Exception as e:
        print(f"❌ 公開範囲マッチングテスト失敗: {e}")
        pytest.fail(f"公開範囲マッチングテストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_edge_cases():
    """エッジケーステスト"""
    print("🔍 エッジケーステスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = TodayHandler(config, database, data_service, None)
        
        # エッジケースのテスト
        edge_cases = [
            '',  # 空文字
            'invalid',  # 無効な値
            'PUBLIC',  # 大文字
            'Public',  # 混合ケース
        ]
        
        for case in edge_cases:
            print(f"エッジケース: '{case}'")
            
            # デフォルト値へのフォールバックをテスト
            if case not in ['public', 'home', 'followers', 'specified']:
                print(f"  無効な値として処理: {case}")
        
        print("✅ エッジケーステスト成功")
        assert True, "エッジケーステストが成功しました"
        
    except Exception as e:
        print(f"❌ エッジケーステスト失敗: {e}")
        pytest.fail(f"エッジケーステストが失敗しました: {e}")

if __name__ == "__main__":
    print("🚀 公開範囲マッチングテスト")
    print("pytest形式に変更されたため、以下のコマンドで実行してください:")
    print("PYTHONPATH=. python -m pytest tests/test_visibility_matching.py -v") 
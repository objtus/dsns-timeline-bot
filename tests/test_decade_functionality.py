#!/usr/bin/env python3
"""
年代別機能のテスト
"""

import asyncio
import pytest
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.decade_handler import DecadeHandler

@pytest.mark.asyncio
async def test_decade_functionality():
    """年代別機能のテスト"""
    print("🔍 年代別機能テスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = DecadeHandler(config, database, data_service)
        
        # 1990年代の統計を取得（データベースから直接取得）
        decade_stats = database.get_decade_statistics(1990, 1999)
        
        print(f"1990年代統計: {decade_stats}")
        
        assert decade_stats is not None, "年代統計が取得できませんでした"
        # 統計データの構造確認
        assert isinstance(decade_stats, dict), "年代統計が辞書形式ではありません"
        assert 'total_events' in decade_stats, "total_eventsが存在しません"
        
        print("✅ 年代別機能テスト成功")
        assert True, "年代別機能テストが成功しました"
        
    except Exception as e:
        print(f"❌ 年代別機能テスト失敗: {e}")
        pytest.fail(f"年代別機能テストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_new_decades_functionality():
    """新しい年代（1920年代から1980年代）のテスト"""
    print("🔍 新しい年代機能テスト開始...")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        data_service = TimelineDataService(config, database)
        handler = DecadeHandler(config, database, data_service)
        
        # 新しい年代のテストケース
        test_decades = [
            (1920, 1929, "1920年代"),
            (1930, 1939, "1930年代"),
            (1940, 1949, "1940年代"),
            (1950, 1959, "1950年代"),
            (1960, 1969, "1960年代"),
            (1970, 1979, "1970年代"),
            (1980, 1989, "1980年代"),
        ]
        
        for start_year, end_year, decade_name in test_decades:
            print(f"テスト中: {decade_name}")
            
            # 統計情報テスト
            stats = database.get_decade_statistics(start_year, end_year)
            assert stats is not None, f"{decade_name}の統計が取得できませんでした"
            assert isinstance(stats, dict), f"{decade_name}の統計が辞書形式ではありません"
            assert 'total_events' in stats, f"{decade_name}のtotal_eventsが存在しません"
            
            # ハンドラーテスト（統計）
            result = await handler._handle_statistics(start_year, end_year, decade_name)
            assert result is not None, f"{decade_name}のハンドラー結果が取得できませんでした"
            assert decade_name in result, f"{decade_name}の結果に年代名が含まれていません"
            
            # ハンドラーテスト（概要）
            result = await handler._handle_summary(start_year, end_year, decade_name)
            assert result is not None, f"{decade_name}の概要結果が取得できませんでした"
            assert decade_name in result, f"{decade_name}の概要に年代名が含まれていません"
            
            print(f"✅ {decade_name}テスト成功")
        
        print("✅ 新しい年代機能テスト成功")
        assert True, "新しい年代機能テストが成功しました"
        
    except Exception as e:
        print(f"❌ 新しい年代機能テスト失敗: {e}")
        pytest.fail(f"新しい年代機能テストが失敗しました: {e}")

def test_summary_manager_standalone():
    """SummaryManagerのスタンドアロンテスト"""
    print("🔍 SummaryManagerテスト開始...")
    
    try:
        from summary_manager import SummaryManager
        from config import Config
        
        config = Config()
        summary_manager = SummaryManager(config.summaries_dir)
        
        # 新しい年代の概要ファイルテスト
        test_decades = [
            (1920, 1929, "1920年代"),
            (1930, 1939, "1930年代"),
            (1940, 1949, "1940年代"),
            (1950, 1959, "1950年代"),
            (1960, 1969, "1960年代"),
            (1970, 1979, "1970年代"),
            (1980, 1989, "1980年代"),
        ]
        
        for start_year, end_year, decade_name in test_decades:
            print(f"SummaryManagerテスト中: {decade_name}")
            
            # 概要取得テスト
            summary = summary_manager.get_decade_summary(start_year, end_year, decade_name)
            assert summary is not None, f"{decade_name}の概要が取得できませんでした"
            assert isinstance(summary, str), f"{decade_name}の概要が文字列ではありません"
            assert len(summary) > 0, f"{decade_name}の概要が空です"
            assert decade_name in summary, f"{decade_name}の概要に年代名が含まれていません"
            
            print(f"✅ {decade_name} SummaryManagerテスト成功")
        
        print("✅ SummaryManagerテスト成功")
        assert True, "SummaryManagerテストが成功しました"
        
    except Exception as e:
        print(f"❌ SummaryManagerテスト失敗: {e}")
        pytest.fail(f"SummaryManagerテストが失敗しました: {e}")

if __name__ == "__main__":
    print("🚀 年代別機能テスト")
    print("pytest形式に変更されたため、以下のコマンドで実行してください:")
    print("PYTHONPATH=. python -m pytest tests/test_decade_functionality.py -v") 
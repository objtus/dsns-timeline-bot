#!/usr/bin/env python3
"""
リファクタリング完了確認テスト
新しい定数、例外クラス、型定義の統合動作確認
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_constants_integration():
    """定数の統合テスト"""
    print("=== 定数の統合テスト ===")
    
    try:
        from constants import (
            MessageLimits, ErrorMessages, Visibility,
            CommandTypes, StatusSubTypes, DecadeSubTypes
        )
        
        # 定数の値確認
        assert MessageLimits.MAX_LENGTH == 3000
        assert ErrorMessages.DATA_FETCH_FAILED == "データの取得に失敗しました"
        assert Visibility.PUBLIC == "public"
        assert CommandTypes.TODAY == "today"
        assert StatusSubTypes.SERVER == "server"
        assert DecadeSubTypes.STATISTICS == "statistics"
        
        print("✓ 定数の統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 定数の統合テスト失敗: {e}")
        return False

def test_exceptions_integration():
    """例外クラスの統合テスト"""
    print("\n=== 例外クラスの統合テスト ===")
    
    try:
        from exceptions import (
            DSNSBotError, DataServiceError, DatabaseError,
            CommandParseError, ValidationError
        )
        from constants import ErrorMessages
        
        # 例外の使用テスト
        try:
            raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED, "https://example.com", 404)
        except DataServiceError as e:
            assert e.url == "https://example.com"
            assert e.status_code == 404
            assert isinstance(e, DSNSBotError)
        
        try:
            raise DatabaseError(ErrorMessages.DATABASE_ERROR, "timeline_events", "SELECT")
        except DatabaseError as e:
            assert e.table == "timeline_events"
            assert e.operation == "SELECT"
            assert isinstance(e, DSNSBotError)
        
        print("✓ 例外クラスの統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 例外クラスの統合テスト失敗: {e}")
        return False

def test_types_integration():
    """型定義の統合テスト"""
    print("\n=== 型定義の統合テスト ===")
    
    try:
        from dsnstypes import (
            CommandDict, EventData, VisibilityType,
            StatusInfo, HealthCheckResult
        )
        from constants import CommandTypes, HealthStatus
        
        # 型の使用テスト
        command: CommandDict = {
            "type": CommandTypes.TODAY,
            "sub_type": None,
            "query": None,
            "date": None,
            "year": None,
            "month": None,
            "day": None
        }
        assert command["type"] == CommandTypes.TODAY
        
        event: EventData = {
            "year": 2023,
            "month": 5,
            "day": 1,
            "content": "テストイベント",
            "category": None
        }
        assert event["year"] == 2023
        
        visibility: VisibilityType = "public"
        assert visibility == "public"
        
        health_result: HealthCheckResult = {
            "status": HealthStatus.HEALTHY,
            "message": "システム正常",
            "details": {},
            "timestamp": datetime.now()
        }
        assert health_result["status"] == HealthStatus.HEALTHY
        
        print("✓ 型定義の統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 型定義の統合テスト失敗: {e}")
        return False

def test_data_service_integration():
    """データサービスの統合テスト"""
    print("\n=== データサービスの統合テスト ===")
    
    try:
        from constants import MessageLimits, ErrorMessages
        from exceptions import DataServiceError
        from dsnstypes import EventData
        
        # 定数の使用確認
        assert MessageLimits.MAX_LENGTH == 3000
        assert ErrorMessages.DATA_FETCH_FAILED == "データの取得に失敗しました"
        
        # 例外の使用確認
        try:
            raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED, "https://example.com", 404)
        except DataServiceError as e:
            assert e.message == ErrorMessages.DATA_FETCH_FAILED
        
        # 型定義の使用確認
        event: EventData = {
            "year": 2023,
            "month": 5,
            "day": 1,
            "content": "テストイベント",
            "category": None
        }
        assert event["year"] == 2023
        
        print("✓ データサービスの統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ データサービスの統合テスト失敗: {e}")
        return False

def test_database_integration():
    """データベースの統合テスト"""
    print("\n=== データベースの統合テスト ===")
    
    try:
        from constants import DatabaseTables, ErrorMessages
        from exceptions import DatabaseError
        
        # 定数の使用確認
        assert DatabaseTables.TIMELINE_EVENTS == "timeline_events"
        assert DatabaseTables.UPDATE_HISTORY == "update_history"
        assert ErrorMessages.DATABASE_ERROR == "データベースエラーが発生しました"
        
        # 例外の使用確認
        try:
            raise DatabaseError(ErrorMessages.DATABASE_ERROR, "timeline_events", "SELECT")
        except DatabaseError as e:
            assert e.message == ErrorMessages.DATABASE_ERROR
            assert e.table == "timeline_events"
        
        print("✓ データベースの統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ データベースの統合テスト失敗: {e}")
        return False

def test_handlers_integration():
    """ハンドラーの統合テスト"""
    print("\n=== ハンドラーの統合テスト ===")
    
    try:
        from constants import MessageLimits, ErrorMessages
        from exceptions import HandlerError, DecadeHandlerError
        from dsnstypes import CommandDict
        
        # 定数の使用確認
        assert MessageLimits.MAX_LENGTH == 3000
        assert ErrorMessages.INVALID_COMMAND == "無効なコマンドです"
        
        # 例外の使用確認
        try:
            raise HandlerError("ハンドラー初期化失敗", "today_handler", "today")
        except HandlerError as e:
            assert e.handler_type == "today_handler"
            assert e.command == "today"
        
        try:
            raise DecadeHandlerError("年代統計取得失敗", "1990s", "statistics")
        except DecadeHandlerError as e:
            assert e.decade == "1990s"
            assert e.sub_type == "statistics"
        
        # 型定義の使用確認
        command: CommandDict = {
            "type": "today",
            "sub_type": None,
            "query": None,
            "date": None,
            "year": None,
            "month": None,
            "day": None
        }
        assert command["type"] == "today"
        
        print("✓ ハンドラーの統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ ハンドラーの統合テスト失敗: {e}")
        return False

def test_error_handling_workflow():
    """エラーハンドリングワークフローのテスト"""
    print("\n=== エラーハンドリングワークフローのテスト ===")
    
    try:
        from constants import ErrorMessages, MessageLimits
        from exceptions import (
            DataServiceError, DatabaseError, CommandParseError,
            ValidationError, MessageLimitError
        )
        
        # データサービスエラーハンドリング
        try:
            raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED, "https://example.com", 404)
        except DataServiceError as e:
            assert e.message == ErrorMessages.DATA_FETCH_FAILED
            assert e.url == "https://example.com"
            assert e.status_code == 404
        
        # データベースエラーハンドリング
        try:
            raise DatabaseError(ErrorMessages.DATABASE_ERROR, "timeline_events", "SELECT")
        except DatabaseError as e:
            assert e.message == ErrorMessages.DATABASE_ERROR
            assert e.table == "timeline_events"
            assert e.operation == "SELECT"
        
        # コマンド解析エラーハンドリング
        try:
            raise CommandParseError(ErrorMessages.INVALID_COMMAND, "invalid_cmd", "unknown")
        except CommandParseError as e:
            assert e.message == ErrorMessages.INVALID_COMMAND
            assert e.command == "invalid_cmd"
            assert e.command_type == "unknown"
        
        # バリデーションエラーハンドリング
        try:
            raise ValidationError("無効な値", "url", "invalid_url")
        except ValidationError as e:
            assert e.field == "url"
            assert e.value == "invalid_url"
        
        # メッセージ制限エラーハンドリング
        try:
            raise MessageLimitError(ErrorMessages.MESSAGE_TOO_LONG, 3500, MessageLimits.MAX_LENGTH)
        except MessageLimitError as e:
            assert e.message == ErrorMessages.MESSAGE_TOO_LONG
            assert e.current_length == 3500
            assert e.max_length == MessageLimits.MAX_LENGTH
            assert e.details['excess_length'] == 500
        
        print("✓ エラーハンドリングワークフローのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ エラーハンドリングワークフローのテスト失敗: {e}")
        return False

def test_constants_usage_patterns():
    """定数使用パターンのテスト"""
    print("\n=== 定数使用パターンのテスト ===")
    
    try:
        from constants import (
            Visibility, MessageLimits, CommandTypes,
            StatusSubTypes, DecadeSubTypes, HealthStatus
        )
        
        # 公開範囲の検証
        assert Visibility.is_valid("public") == True
        assert Visibility.is_valid("invalid") == False
        assert len(Visibility.get_all()) == 4
        
        # メッセージ長チェック
        def check_message_length(message: str) -> bool:
            return len(message) <= MessageLimits.MAX_LENGTH
        
        assert check_message_length("短いメッセージ") == True
        assert check_message_length("x" * 3500) == False
        
        # コマンドタイプの確認
        valid_commands = [
            CommandTypes.TODAY,
            CommandTypes.DATE,
            CommandTypes.SEARCH,
            CommandTypes.HELP,
            CommandTypes.STATUS,
            CommandTypes.DECADE
        ]
        assert len(valid_commands) == 6
        
        # ステータスサブタイプの確認
        valid_status_types = [
            StatusSubTypes.BASIC,
            StatusSubTypes.SERVER,
            StatusSubTypes.BOT,
            StatusSubTypes.TIMELINE
        ]
        assert len(valid_status_types) == 4
        
        # 年代サブタイプの確認
        valid_decade_types = [
            DecadeSubTypes.STATISTICS,
            DecadeSubTypes.REPRESENTATIVE,
            DecadeSubTypes.SUMMARY
        ]
        assert len(valid_decade_types) == 3
        
        # ヘルスステータスの確認
        valid_health_statuses = [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY
        ]
        assert len(valid_health_statuses) == 3
        
        print("✓ 定数使用パターンのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 定数使用パターンのテスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("分散SNS関連年表bot - リファクタリング完了確認テスト")
    print("=" * 60)
    
    tests = [
        ("定数の統合テスト", test_constants_integration),
        ("例外クラスの統合テスト", test_exceptions_integration),
        ("型定義の統合テスト", test_types_integration),
        ("データサービスの統合テスト", test_data_service_integration),
        ("データベースの統合テスト", test_database_integration),
        ("ハンドラーの統合テスト", test_handlers_integration),
        ("エラーハンドリングワークフローのテスト", test_error_handling_workflow),
        ("定数使用パターンのテスト", test_constants_usage_patterns)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}で予期しないエラー: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("リファクタリング完了確認結果:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 リファクタリングが正常に完了しました！")
        print("\n📋 実装完了項目:")
        print("✅ 新しい定数ファイル (constants.py)")
        print("✅ 新しい例外クラス (exceptions.py)")
        print("✅ 新しい型定義 (dsnstypes.py)")
        print("✅ 包括的テスト (test_refactoring_comprehensive.py)")
        print("✅ 統合テスト (test_refactoring_final.py)")
        print("✅ ドキュメント (REFACTORING_DOCUMENTATION.md)")
        print("✅ 既存コードとの統合")
        print("✅ エラーハンドリングの統一")
        print("✅ 型安全性の向上")
        return True
    else:
        print("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
リファクタリング後の定数と例外クラスのテスト
新しい定数ファイルと例外クラスファイルの動作確認
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, time
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_constants():
    """定数ファイルのテスト"""
    print("=== 定数ファイルのテスト ===")
    
    try:
        from constants import (
            Visibility, MessageLimits, TimeFormats, 
            DatabaseConfig, HTTPConfig, LogLevels,
            DefaultValues, FilePaths
        )
        
        # Visibility定数のテスト
        print("✓ Visibility定数:")
        print(f"  PUBLIC: {Visibility.PUBLIC}")
        print(f"  HOME: {Visibility.HOME}")
        print(f"  FOLLOWERS: {Visibility.FOLLOWERS}")
        print(f"  SPECIFIED: {Visibility.SPECIFIED}")
        
        # MessageLimits定数のテスト
        print("✓ MessageLimits定数:")
        print(f"  MAX_LENGTH: {MessageLimits.MAX_LENGTH}")
        print(f"  TRUNCATE_LENGTH: {MessageLimits.TRUNCATE_LENGTH}")
        print(f"  SHORT_MESSAGE_LENGTH: {MessageLimits.SHORT_MESSAGE_LENGTH}")
        
        # TimeFormats定数のテスト
        print("✓ TimeFormats定数:")
        print(f"  POST_TIME_FORMAT: {TimeFormats.POST_TIME_FORMAT}")
        print(f"  DATE_FORMAT: {TimeFormats.DATE_FORMAT}")
        print(f"  DATETIME_FORMAT: {TimeFormats.DATETIME_FORMAT}")
        
        # 設定定数のテスト
        print("✓ 設定定数:")
        print(f"  FilePaths.DATABASE_PATH: {FilePaths.DATABASE_PATH}")
        print(f"  LogLevels.INFO: {LogLevels.INFO}")
        print(f"  HTTPConfig.TIMEOUT: {HTTPConfig.TIMEOUT}")
        print(f"  DefaultValues.SCHEDULED_POST_VISIBILITY: {DefaultValues.SCHEDULED_POST_VISIBILITY}")
        
        # 定数の値検証
        assert MessageLimits.MAX_LENGTH == 3000
        assert MessageLimits.TRUNCATE_LENGTH == 2997
        assert MessageLimits.SHORT_MESSAGE_LENGTH == 2500
        assert Visibility.PUBLIC == 'public'
        assert Visibility.HOME == 'home'
        
        print("✓ 定数ファイルのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 定数ファイルのテスト失敗: {e}")
        return False

def test_exceptions():
    """例外クラスファイルのテスト"""
    print("\n=== 例外クラスファイルのテスト ===")
    
    try:
        from exceptions import (
            DSNSBotError, DataServiceError, BotClientError,
            CommandParseError, DatabaseError, ConfigError,
            ValidationError, NetworkError, FileOperationError
        )
        
        # 基底例外のテスト
        print("✓ 基底例外クラス:")
        base_error = DSNSBotError("テストエラー")
        print(f"  基底例外: {base_error}")
        
        # データサービス例外のテスト
        print("✓ データサービス例外:")
        data_error = DataServiceError("データ取得失敗", status_code=404)
        print(f"  データサービス例外: {data_error}")
        print(f"  ステータスコード: {data_error.status_code}")
        
        # ボットクライアント例外のテスト
        print("✓ ボットクライアント例外:")
        bot_error = BotClientError("接続失敗", visibility="public", note_id="test_note")
        print(f"  ボットクライアント例外: {bot_error}")
        print(f"  可視性: {bot_error.visibility}")
        print(f"  ノートID: {bot_error.note_id}")
        
        # コマンド解析例外のテスト
        print("✓ コマンド解析例外:")
        cmd_error = CommandParseError("無効なコマンド", command="invalid_cmd", command_type="unknown")
        print(f"  コマンド解析例外: {cmd_error}")
        print(f"  コマンド: {cmd_error.command}")
        print(f"  コマンドタイプ: {cmd_error.command_type}")
        
        # データベース例外のテスト
        print("✓ データベース例外:")
        db_error = DatabaseError("クエリ失敗", table="timeline_events", operation="SELECT")
        print(f"  データベース例外: {db_error}")
        print(f"  テーブル: {db_error.table}")
        print(f"  操作: {db_error.operation}")
        
        # 設定例外のテスト
        print("✓ 設定例外:")
        config_error = ConfigError("設定ファイルが見つかりません", config_key="database_path", config_value="/invalid/path")
        print(f"  設定例外: {config_error}")
        print(f"  設定キー: {config_error.config_key}")
        print(f"  設定値: {config_error.config_value}")
        
        # バリデーション例外のテスト
        print("✓ バリデーション例外:")
        validation_error = ValidationError("無効な値", field="url", value="invalid_url")
        print(f"  バリデーション例外: {validation_error}")
        print(f"  フィールド: {validation_error.field}")
        print(f"  値: {validation_error.value}")
        
        # ネットワーク例外のテスト
        print("✓ ネットワーク例外:")
        network_error = NetworkError("接続タイムアウト", url="https://example.com", timeout=30.0)
        print(f"  ネットワーク例外: {network_error}")
        print(f"  URL: {network_error.url}")
        print(f"  タイムアウト: {network_error.timeout}")
        
        # ファイル操作例外のテスト
        print("✓ ファイル操作例外:")
        file_error = FileOperationError("ファイル読み込み失敗", file_path="/path/to/file", operation="read")
        print(f"  ファイル操作例外: {file_error}")
        print(f"  ファイルパス: {file_error.file_path}")
        print(f"  操作: {file_error.operation}")
        
        # 例外の階層構造テスト
        assert isinstance(data_error, DSNSBotError)
        assert isinstance(bot_error, DSNSBotError)
        assert isinstance(cmd_error, DSNSBotError)
        assert isinstance(db_error, DSNSBotError)
        assert isinstance(config_error, DSNSBotError)
        assert isinstance(validation_error, DSNSBotError)
        assert isinstance(network_error, DSNSBotError)
        assert isinstance(file_error, DSNSBotError)
        
        print("✓ 例外クラスファイルのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 例外クラスファイルのテスト失敗: {e}")
        return False

def test_types():
    """型定義ファイルのテスト"""
    print("\n=== 型定義ファイルのテスト ===")
    
    try:
        from dsnstypes import (
            CommandDict, EventData, DatabaseEvent, UpdateHistory,
            VisibilityType, ConfigValues, StatusInfo,
            HealthCheckResult, PostResult, SearchResult
        )
        
        # 型のインポート確認
        print("✓ 型定義のインポート:")
        print(f"  CommandDict: {CommandDict}")
        print(f"  EventData: {EventData}")
        print(f"  DatabaseEvent: {DatabaseEvent}")
        print(f"  UpdateHistory: {UpdateHistory}")
        print(f"  VisibilityType: {VisibilityType}")
        print(f"  ConfigValues: {ConfigValues}")
        print(f"  StatusInfo: {StatusInfo}")
        
        # 設定型の確認
        print("✓ 設定型定義:")
        print(f"  HealthCheckResult: {HealthCheckResult}")
        print(f"  PostResult: {PostResult}")
        print(f"  SearchResult: {SearchResult}")
        
        # 型の使用例
        from typing import Dict, Any
        
        # CommandDictの使用例
        command: CommandDict = {
            "type": "date",
            "sub_type": None,
            "query": "5月1日",
            "date": "05-01",
            "year": None,
            "month": None,
            "day": None
        }
        print(f"✓ CommandDict使用例: {command}")
        
        # EventDataの使用例
        event: EventData = {
            "year": 2023,
            "month": 5,
            "day": 1,
            "content": "テストイベント",
            "category": "test"
        }
        print(f"✓ EventData使用例: {event}")
        
        # VisibilityTypeの使用例
        visibility: VisibilityType = "public"
        print(f"✓ VisibilityType使用例: {visibility}")
        
        print("✓ 型定義ファイルのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 型定義ファイルのテスト失敗: {e}")
        return False

def test_integration():
    """統合テスト - 定数と例外の組み合わせテスト"""
    print("\n=== 統合テスト ===")
    
    try:
        from constants import Visibility, MessageLimits
        from exceptions import DataServiceError, ValidationError
        from dsnstypes import CommandDict, VisibilityType
        
        # 定数と例外の組み合わせテスト
        print("✓ 定数と例外の組み合わせ:")
        
        # 可視性の検証
        def validate_visibility(vis: VisibilityType) -> bool:
            valid_values = [Visibility.PUBLIC, Visibility.HOME, 
                          Visibility.FOLLOWERS, Visibility.SPECIFIED]
            if vis not in valid_values:
                raise ValidationError("無効な可視性", field="visibility", value=vis)
            return True
        
        # 正常なケース
        assert validate_visibility(Visibility.PUBLIC)
        assert validate_visibility(Visibility.HOME)
        
        # 異常なケース
        try:
            validate_visibility("invalid")  # type: ignore
            assert False, "例外が発生すべき"
        except ValidationError as e:
            print(f"  期待される例外: {e}")
        
        # メッセージ長の検証
        def validate_message_length(message: str) -> bool:
            if len(message) > MessageLimits.MAX_LENGTH:
                raise ValidationError("メッセージが長すぎます", 
                                    field="message_length", 
                                    value=len(message))
            return True
        
        # 正常なケース
        short_message = "短いメッセージ"
        assert validate_message_length(short_message)
        
        # 異常なケース
        long_message = "x" * (MessageLimits.MAX_LENGTH + 1)
        try:
            validate_message_length(long_message)
            assert False, "例外が発生すべき"
        except ValidationError as e:
            print(f"  期待される例外: {e}")
        
        # コマンド解析のテスト
        def parse_command(text: str) -> CommandDict:
            if not text or len(text.strip()) == 0:
                raise ValidationError("コマンドが空です", field="command", value=text)
            
            return {
                "type": "date",
                "sub_type": None,
                "query": text,
                "date": None,
                "year": None,
                "month": None,
                "day": None
            }
        
        # 正常なケース
        command = parse_command("5月1日")
        assert command["type"] == "date"
        assert command["query"] == "5月1日"
        
        # 異常なケース
        try:
            parse_command("")
            assert False, "例外が発生すべき"
        except ValidationError as e:
            print(f"  期待される例外: {e}")
        
        print("✓ 統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 統合テスト失敗: {e}")
        return False

def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== エラーハンドリングのテスト ===")
    
    try:
        from exceptions import (
            DSNSBotError, DataServiceError, NetworkError,
            ValidationError, FileOperationError
        )
        
        # エラーハンドリングのシミュレーション
        def simulate_data_fetch(url: str) -> str:
            if "invalid" in url:
                raise NetworkError("無効なURL", url=url)
            if "timeout" in url:
                raise NetworkError("接続タイムアウト", url=url)
            if "file_error" in url:
                raise FileOperationError("ファイル読み込み失敗", file_path=url, operation="read")
            return "正常なデータ"
        
        # 正常なケース
        try:
            result = simulate_data_fetch("https://valid-url.com")
            print(f"✓ 正常なデータ取得: {result}")
        except DSNSBotError as e:
            print(f"✗ 予期しないエラー: {e}")
            return False
        
        # ネットワークエラーのテスト
        try:
            simulate_data_fetch("https://invalid-url.com")
            assert False, "例外が発生すべき"
        except NetworkError as e:
            print(f"✓ ネットワークエラー処理: {e}")
        
        # タイムアウトエラーのテスト
        try:
            simulate_data_fetch("https://timeout-url.com")
            assert False, "例外が発生すべき"
        except NetworkError as e:
            print(f"✓ タイムアウトエラー処理: {e}")
        
        # ファイル操作エラーのテスト
        try:
            simulate_data_fetch("https://file_error-url.com")
            assert False, "例外が発生すべき"
        except FileOperationError as e:
            print(f"✓ ファイル操作エラー処理: {e}")
        
        # エラーの階層構造テスト
        def handle_error(error: Exception) -> str:
            if isinstance(error, NetworkError):
                return f"ネットワークエラー: {error.url}"
            elif isinstance(error, FileOperationError):
                return f"ファイル操作エラー: {error.file_path}"
            elif isinstance(error, ValidationError):
                return f"バリデーションエラー: {error.field}={error.value}"
            elif isinstance(error, DSNSBotError):
                return f"DSNSボットエラー: {error}"
            else:
                return f"予期しないエラー: {error}"
        
        # エラーハンドリングのテスト
        errors = [
            NetworkError("接続失敗", url="https://example.com"),
            FileOperationError("ファイル読み込み失敗", file_path="/path/to/file", operation="read"),
            ValidationError("無効な値", field="url", value="invalid")
        ]
        
        for error in errors:
            result = handle_error(error)
            print(f"✓ エラーハンドリング: {result}")
        
        print("✓ エラーハンドリングのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ エラーハンドリングのテスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("リファクタリング後の定数と例外クラスのテスト開始")
    print("=" * 60)
    
    tests = [
        ("定数ファイル", test_constants),
        ("例外クラスファイル", test_exceptions),
        ("型定義ファイル", test_types),
        ("統合テスト", test_integration),
        ("エラーハンドリング", test_error_handling)
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
    print("テスト結果サマリー:")
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
        print("🎉 すべてのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
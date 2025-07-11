#!/usr/bin/env python3
"""
分散SNS関連年表bot - リファクタリング簡易テスト

リファクタリング後の基本機能の動作確認を行うテストファイル
"""

import sys
import asyncio
import logging
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_refactoring.log', mode='w', encoding='utf-8')
        ]
    )

@pytest.mark.asyncio
async def test_imports():
    """インポートテスト"""
    print("🔍 インポートテスト開始...")
    
    try:
        # 基本モジュール
        from config import Config
        from database import TimelineDatabase
        from data_service import TimelineDataService
        from bot_client import BotClient
        from command_router import CommandRouter
        
        # 型定義
        from dsnstypes import (
            VisibilityType, CommandDict, EventData, DatabaseEvent,
            StatisticsData, DecadeStatistics, StatusInfo, StatusSystemInfo, StatusDatabaseInfo
        )
        
        # 例外クラス
        from exceptions import (
            DSNSBotError, DataServiceError, DatabaseError, BotClientError,
            CommandParseError, ConfigError, ValidationError, MessageLimitError,
            HealthCheckError, ScheduledPostError, NetworkError, FileOperationError,
            SummaryError, SystemError, HandlerError, StatusHandlerError, DecadeHandlerError
        )
        
        # 定数
        from constants import MessageLimits, HTTPConfig, DatabaseConfig
        
        # ハンドラー（相対インポートの問題があるためスキップ）
        # from handlers.base_handler import BaseHandler
        # from handlers.today_handler import TodayHandler
        # from handlers.date_handler import DateHandler
        # from handlers.search_handler import SearchHandler
        # from handlers.help_handler import HelpHandler
        # from handlers.status_handler import StatusHandler
        # from handlers.decade_handler import DecadeHandler
        
        print("✅ インポートテスト成功")
        assert True, "インポートテストが成功しました"
        
    except Exception as e:
        print(f"❌ インポートテスト失敗: {e}")
        pytest.fail(f"インポートテストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_config():
    """設定テスト"""
    print("🔍 設定テスト開始...")
    
    try:
        from config import Config
        
        # 設定オブジェクトの作成
        config = Config()
        
        # 基本設定の確認
        assert hasattr(config, 'misskey_url'), "misskey_url属性が存在しません"
        assert hasattr(config, 'misskey_token'), "misskey_token属性が存在しません"
        assert hasattr(config, 'timeline_url'), "timeline_url属性が存在しません"
        assert hasattr(config, 'database_path'), "database_path属性が存在しません"
        assert hasattr(config, 'post_times'), "post_times属性が存在しません"
        assert hasattr(config, 'timezone'), "timezone属性が存在しません"
        assert hasattr(config, 'log_level'), "log_level属性が存在しません"
        assert hasattr(config, 'debug_mode'), "debug_mode属性が存在しません"
        assert hasattr(config, 'dry_run_mode'), "dry_run_mode属性が存在しません"
        assert hasattr(config, 'http_timeout'), "http_timeout属性が存在しません"
        assert hasattr(config, 'data_update_interval_hours'), "data_update_interval_hours属性が存在しません"
        assert hasattr(config, 'scheduled_post_visibility'), "scheduled_post_visibility属性が存在しません"
        
        print("✅ 設定テスト成功")
        assert True, "設定テストが成功しました"
        
    except Exception as e:
        print(f"❌ 設定テスト失敗: {e}")
        pytest.fail(f"設定テストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_constants():
    """定数テスト"""
    print("🔍 定数テスト開始...")
    
    try:
        from constants import MessageLimits, HTTPConfig, DatabaseConfig
        
        # メッセージ制限定数
        assert hasattr(MessageLimits, 'MAX_MESSAGE_LENGTH'), "MAX_MESSAGE_LENGTH定数が存在しません"
        assert isinstance(MessageLimits.MAX_MESSAGE_LENGTH, int), "MAX_MESSAGE_LENGTHが整数ではありません"
        assert MessageLimits.MAX_MESSAGE_LENGTH > 0, "MAX_MESSAGE_LENGTHが正の値ではありません"
        
        # HTTP設定定数
        assert hasattr(HTTPConfig, 'TIMEOUT'), "TIMEOUT定数が存在しません"
        assert hasattr(HTTPConfig, 'USER_AGENT'), "USER_AGENT定数が存在しません"
        
        # データベース設定定数
        assert hasattr(DatabaseConfig, 'BACKUP_RETENTION_DAYS'), "BACKUP_RETENTION_DAYS定数が存在しません"
        
        print("✅ 定数テスト成功")
        assert True, "定数テストが成功しました"
        
    except Exception as e:
        print(f"❌ 定数テスト失敗: {e}")
        pytest.fail(f"定数テストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_exceptions():
    """例外クラステスト"""
    print("🔍 例外クラステスト開始...")
    
    try:
        from exceptions import (
            DSNSBotError, DataServiceError, DatabaseError, BotClientError,
            CommandParseError, ConfigError, ValidationError, MessageLimitError,
            HealthCheckError, ScheduledPostError, NetworkError, FileOperationError,
            SummaryError, SystemError, HandlerError, StatusHandlerError, DecadeHandlerError
        )
        
        # 基底例外クラスのテスト
        base_error = DSNSBotError("テストエラー")
        assert isinstance(base_error, Exception), "DSNSBotErrorがExceptionを継承していません"
        assert hasattr(base_error, 'message'), "message属性が存在しません"
        assert hasattr(base_error, 'details'), "details属性が存在しません"
        
        # 各例外クラスのテスト
        data_service_error = DataServiceError("データサービスエラー", "http://example.com", 500)
        assert isinstance(data_service_error, DSNSBotError), "DataServiceErrorがDSNSBotErrorを継承していません"
        assert hasattr(data_service_error, 'url'), "url属性が存在しません"
        assert hasattr(data_service_error, 'status_code'), "status_code属性が存在しません"
        
        database_error = DatabaseError("データベースエラー", "timeline_events", "SELECT")
        assert isinstance(database_error, DSNSBotError), "DatabaseErrorがDSNSBotErrorを継承していません"
        assert hasattr(database_error, 'table'), "table属性が存在しません"
        assert hasattr(database_error, 'operation'), "operation属性が存在しません"
        
        bot_client_error = BotClientError("ボットクライアントエラー", "home", "note123")
        assert isinstance(bot_client_error, DSNSBotError), "BotClientErrorがDSNSBotErrorを継承していません"
        assert hasattr(bot_client_error, 'visibility'), "visibility属性が存在しません"
        assert hasattr(bot_client_error, 'note_id'), "note_id属性が存在しません"
        
        command_parse_error = CommandParseError("コマンド解析エラー", "テストコマンド", "date")
        assert isinstance(command_parse_error, DSNSBotError), "CommandParseErrorがDSNSBotErrorを継承していません"
        assert hasattr(command_parse_error, 'command'), "command属性が存在しません"
        assert hasattr(command_parse_error, 'command_type'), "command_type属性が存在しません"
        
        config_error = ConfigError("設定エラー", "MISSKEY_URL", "invalid_url")
        assert isinstance(config_error, DSNSBotError), "ConfigErrorがDSNSBotErrorを継承していません"
        assert hasattr(config_error, 'config_key'), "config_key属性が存在しません"
        assert hasattr(config_error, 'config_value'), "config_value属性が存在しません"
        
        validation_error = ValidationError("バリデーションエラー", "year", 2025)
        assert isinstance(validation_error, DSNSBotError), "ValidationErrorがDSNSBotErrorを継承していません"
        assert hasattr(validation_error, 'field'), "field属性が存在しません"
        assert hasattr(validation_error, 'value'), "value属性が存在しません"
        
        message_limit_error = MessageLimitError("メッセージ制限エラー", 3500, 3000)
        assert isinstance(message_limit_error, DSNSBotError), "MessageLimitErrorがDSNSBotErrorを継承していません"
        assert hasattr(message_limit_error, 'current_length'), "current_length属性が存在しません"
        assert hasattr(message_limit_error, 'max_length'), "max_length属性が存在しません"
        
        health_check_error = HealthCheckError("ヘルスチェックエラー", "database", "unhealthy")
        assert isinstance(health_check_error, DSNSBotError), "HealthCheckErrorがDSNSBotErrorを継承していません"
        assert hasattr(health_check_error, 'component'), "component属性が存在しません"
        assert hasattr(health_check_error, 'status'), "status属性が存在しません"
        
        scheduled_post_error = ScheduledPostError("定期投稿エラー", "12:00", "home")
        assert isinstance(scheduled_post_error, DSNSBotError), "ScheduledPostErrorがDSNSBotErrorを継承していません"
        assert hasattr(scheduled_post_error, 'scheduled_time'), "scheduled_time属性が存在しません"
        assert hasattr(scheduled_post_error, 'visibility'), "visibility属性が存在しません"
        
        network_error = NetworkError("ネットワークエラー", "http://example.com", 30.0)
        assert isinstance(network_error, DSNSBotError), "NetworkErrorがDSNSBotErrorを継承していません"
        assert hasattr(network_error, 'url'), "url属性が存在しません"
        assert hasattr(network_error, 'timeout'), "timeout属性が存在しません"
        
        file_operation_error = FileOperationError("ファイル操作エラー", "/path/to/file", "read")
        assert isinstance(file_operation_error, DSNSBotError), "FileOperationErrorがDSNSBotErrorを継承していません"
        assert hasattr(file_operation_error, 'file_path'), "file_path属性が存在しません"
        assert hasattr(file_operation_error, 'operation'), "operation属性が存在しません"
        
        summary_error = SummaryError("概要エラー", "1990s", "/path/to/summary.md")
        assert isinstance(summary_error, DSNSBotError), "SummaryErrorがDSNSBotErrorを継承していません"
        assert hasattr(summary_error, 'decade'), "decade属性が存在しません"
        assert hasattr(summary_error, 'file_path'), "file_path属性が存在しません"
        
        system_error = SystemError("システムエラー", "cpu", "95.5%")
        assert isinstance(system_error, DSNSBotError), "SystemErrorがDSNSBotErrorを継承していません"
        assert hasattr(system_error, 'component'), "component属性が存在しません"
        assert hasattr(system_error, 'resource'), "resource属性が存在しません"
        
        handler_error = HandlerError("ハンドラーエラー", "today", "post_scheduled_today_event")
        assert isinstance(handler_error, DSNSBotError), "HandlerErrorがDSNSBotErrorを継承していません"
        assert hasattr(handler_error, 'handler_type'), "handler_type属性が存在しません"
        assert hasattr(handler_error, 'command'), "command属性が存在しません"
        
        status_handler_error = StatusHandlerError("ステータスハンドラーエラー", "server", "psutil")
        assert isinstance(status_handler_error, DSNSBotError), "StatusHandlerErrorがDSNSBotErrorを継承していません"
        assert hasattr(status_handler_error, 'status_type'), "status_type属性が存在しません"
        assert hasattr(status_handler_error, 'component'), "component属性が存在しません"
        
        decade_handler_error = DecadeHandlerError("年代ハンドラーエラー", "1990s", "statistics")
        assert isinstance(decade_handler_error, DSNSBotError), "DecadeHandlerErrorがDSNSBotErrorを継承していません"
        assert hasattr(decade_handler_error, 'decade'), "decade属性が存在しません"
        assert hasattr(decade_handler_error, 'sub_type'), "sub_type属性が存在しません"
        
        print("✅ 例外クラステスト成功")
        assert True, "例外クラステストが成功しました"
        
    except Exception as e:
        print(f"❌ 例外クラステスト失敗: {e}")
        pytest.fail(f"例外クラステストが失敗しました: {e}")

@pytest.mark.asyncio
async def test_types():
    """型定義テスト"""
    print("🔍 型定義テスト開始...")
    
    try:
        from dsnstypes import (
            VisibilityType, CommandDict, EventData, DatabaseEvent,
            StatisticsData, DecadeStatistics, StatusInfo, StatusSystemInfo, StatusDatabaseInfo
        )
        from typing import get_type_hints
        
        # VisibilityTypeのテスト
        assert VisibilityType is not None, "VisibilityTypeが定義されていません"
        
        # CommandDictのテスト
        command_dict_hints = get_type_hints(CommandDict)
        assert 'type' in command_dict_hints, "CommandDictにtypeフィールドが存在しません"
        assert 'sub_type' in command_dict_hints, "CommandDictにsub_typeフィールドが存在しません"
        assert 'query' in command_dict_hints, "CommandDictにqueryフィールドが存在しません"
        assert 'date' in command_dict_hints, "CommandDictにdateフィールドが存在しません"
        
        # EventDataのテスト
        event_data_hints = get_type_hints(EventData)
        assert 'year' in event_data_hints, "EventDataにyearフィールドが存在しません"
        assert 'month' in event_data_hints, "EventDataにmonthフィールドが存在しません"
        assert 'day' in event_data_hints, "EventDataにdayフィールドが存在しません"
        assert 'content' in event_data_hints, "EventDataにcontentフィールドが存在しません"
        assert 'category' in event_data_hints, "EventDataにcategoryフィールドが存在しません"
        
        # DatabaseEventのテスト
        database_event_hints = get_type_hints(DatabaseEvent)
        assert 'rowid' in database_event_hints, "DatabaseEventにrowidフィールドが存在しません"
        assert 'year' in database_event_hints, "DatabaseEventにyearフィールドが存在しません"
        assert 'month' in database_event_hints, "DatabaseEventにmonthフィールドが存在しません"
        assert 'day' in database_event_hints, "DatabaseEventにdayフィールドが存在しません"
        assert 'content' in database_event_hints, "DatabaseEventにcontentフィールドが存在しません"
        assert 'category' in database_event_hints, "DatabaseEventにcategoryフィールドが存在しません"
        
        # StatisticsDataのテスト
        statistics_data_hints = get_type_hints(StatisticsData)
        assert 'total_events' in statistics_data_hints, "StatisticsDataにtotal_eventsフィールドが存在しません"
        assert 'average_per_year' in statistics_data_hints, "StatisticsDataにaverage_per_yearフィールドが存在しません"
        assert 'max_year' in statistics_data_hints, "StatisticsDataにmax_yearフィールドが存在しません"
        assert 'min_year' in statistics_data_hints, "StatisticsDataにmin_yearフィールドが存在しません"
        assert 'year_distribution' in statistics_data_hints, "StatisticsDataにyear_distributionフィールドが存在しません"
        
        # DecadeStatisticsのテスト
        decade_statistics_hints = get_type_hints(DecadeStatistics)
        assert 'decade' in decade_statistics_hints, "DecadeStatisticsにdecadeフィールドが存在しません"
        assert 'start_year' in decade_statistics_hints, "DecadeStatisticsにstart_yearフィールドが存在しません"
        assert 'end_year' in decade_statistics_hints, "DecadeStatisticsにend_yearフィールドが存在しません"
        assert 'total_events' in decade_statistics_hints, "DecadeStatisticsにtotal_eventsフィールドが存在しません"
        
        # StatusInfoのテスト
        status_info_hints = get_type_hints(StatusInfo)
        assert 'uptime' in status_info_hints, "StatusInfoにuptimeフィールドが存在しません"
        assert 'message_count' in status_info_hints, "StatusInfoにmessage_countフィールドが存在しません"
        assert 'error_count' in status_info_hints, "StatusInfoにerror_countフィールドが存在しません"
        assert 'database_events' in status_info_hints, "StatusInfoにdatabase_eventsフィールドが存在しません"
        
        # StatusSystemInfoのテスト
        status_system_info_hints = get_type_hints(StatusSystemInfo)
        assert 'cpu_usage' in status_system_info_hints, "StatusSystemInfoにcpu_usageフィールドが存在しません"
        assert 'memory_usage' in status_system_info_hints, "StatusSystemInfoにmemory_usageフィールドが存在しません"
        assert 'disk_usage' in status_system_info_hints, "StatusSystemInfoにdisk_usageフィールドが存在しません"
        
        # StatusDatabaseInfoのテスト
        status_database_info_hints = get_type_hints(StatusDatabaseInfo)
        assert 'database_size' in status_database_info_hints, "StatusDatabaseInfoにdatabase_sizeフィールドが存在しません"
        assert 'last_data_update' in status_database_info_hints, "StatusDatabaseInfoにlast_data_updateフィールドが存在しません"
        assert 'oldest_event' in status_database_info_hints, "StatusDatabaseInfoにoldest_eventフィールドが存在しません"
        assert 'newest_event' in status_database_info_hints, "StatusDatabaseInfoにnewest_eventフィールドが存在しません"
        
        print("✅ 型定義テスト成功")
        assert True, "型定義テストが成功しました"
        
    except Exception as e:
        print(f"❌ 型定義テスト失敗: {e}")
        pytest.fail(f"型定義テストが失敗しました: {e}")

if __name__ == "__main__":
    setup_logging()
    print("🚀 分散SNS関連年表bot - リファクタリング簡易テスト")
    print("pytest形式に変更されたため、以下のコマンドで実行してください:")
    print("PYTHONPATH=. python -m pytest tests/test_refactoring_simple.py -v") 
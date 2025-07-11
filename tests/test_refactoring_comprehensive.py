#!/usr/bin/env python3
"""
リファクタリング後の包括的テスト
新しい定数、例外クラス、型定義の動作確認と統合テスト
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, time
from typing import Dict, Any, List
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_constants_comprehensive():
    """定数の包括的テスト"""
    print("=== 定数の包括的テスト ===")
    
    try:
        from constants import (
            Visibility, MessageLimits, TimeFormats, CommandTypes,
            StatusSubTypes, DecadeSubTypes, HealthStatus, LogLevels,
            DatabaseTables, HTTPStatus, ErrorMessages, SuccessMessages,
            DefaultValues, FilePaths, RegexPatterns, HTMLClasses,
            SystemdServices, HTTPConfig, DatabaseConfig
        )
        
        # Visibility定数のテスト
        print("✓ Visibility定数:")
        assert Visibility.PUBLIC == 'public'
        assert Visibility.HOME == 'home'
        assert Visibility.FOLLOWERS == 'followers'
        assert Visibility.SPECIFIED == 'specified'
        assert Visibility.is_valid('public') == True
        assert Visibility.is_valid('invalid') == False
        assert len(Visibility.get_all()) == 4
        
        # MessageLimits定数のテスト
        print("✓ MessageLimits定数:")
        assert MessageLimits.MAX_LENGTH == 3000
        assert MessageLimits.MAX_MESSAGE_LENGTH == 3000
        assert MessageLimits.TRUNCATE_LENGTH == 2997
        assert MessageLimits.SHORT_MESSAGE_LENGTH == 2500
        assert MessageLimits.SAFETY_MARGIN == 50
        
        # TimeFormats定数のテスト
        print("✓ TimeFormats定数:")
        assert TimeFormats.POST_TIME_FORMAT == '%H:%M'
        assert TimeFormats.DATE_FORMAT == '%Y-%m-%d'
        assert TimeFormats.DATETIME_FORMAT == '%Y-%m-%d %H:%M:%S'
        assert TimeFormats.TIME_ONLY_FORMAT == '%H:%M:%S'
        
        # CommandTypes定数のテスト
        print("✓ CommandTypes定数:")
        assert CommandTypes.TODAY == 'today'
        assert CommandTypes.DATE == 'date'
        assert CommandTypes.SEARCH == 'search'
        assert CommandTypes.HELP == 'help'
        assert CommandTypes.STATUS == 'status'
        assert CommandTypes.DECADE == 'decade'
        
        # StatusSubTypes定数のテスト
        print("✓ StatusSubTypes定数:")
        assert StatusSubTypes.BASIC == 'basic'
        assert StatusSubTypes.SERVER == 'server'
        assert StatusSubTypes.BOT == 'bot'
        assert StatusSubTypes.TIMELINE == 'timeline'
        
        # DecadeSubTypes定数のテスト
        print("✓ DecadeSubTypes定数:")
        assert DecadeSubTypes.STATISTICS == 'statistics'
        assert DecadeSubTypes.REPRESENTATIVE == 'representative'
        assert DecadeSubTypes.SUMMARY == 'summary'
        
        # HealthStatus定数のテスト
        print("✓ HealthStatus定数:")
        assert HealthStatus.HEALTHY == 'healthy'
        assert HealthStatus.DEGRADED == 'degraded'
        assert HealthStatus.UNHEALTHY == 'unhealthy'
        
        # LogLevels定数のテスト
        print("✓ LogLevels定数:")
        assert LogLevels.DEBUG == 'DEBUG'
        assert LogLevels.INFO == 'INFO'
        assert LogLevels.WARNING == 'WARNING'
        assert LogLevels.ERROR == 'ERROR'
        assert LogLevels.CRITICAL == 'CRITICAL'
        
        # DatabaseTables定数のテスト
        print("✓ DatabaseTables定数:")
        assert DatabaseTables.TIMELINE_EVENTS == 'timeline_events'
        assert DatabaseTables.UPDATE_HISTORY == 'update_history'
        
        # HTTPStatus定数のテスト
        print("✓ HTTPStatus定数:")
        assert HTTPStatus.OK == 200
        assert HTTPStatus.BAD_REQUEST == 400
        assert HTTPStatus.UNAUTHORIZED == 401
        assert HTTPStatus.FORBIDDEN == 403
        assert HTTPStatus.NOT_FOUND == 404
        assert HTTPStatus.INTERNAL_SERVER_ERROR == 500
        assert HTTPStatus.SERVICE_UNAVAILABLE == 503
        
        # ErrorMessages定数のテスト
        print("✓ ErrorMessages定数:")
        assert ErrorMessages.DATA_FETCH_FAILED == "データの取得に失敗しました"
        assert ErrorMessages.DATABASE_ERROR == "データベースエラーが発生しました"
        assert ErrorMessages.INVALID_COMMAND == "無効なコマンドです"
        assert ErrorMessages.MESSAGE_TOO_LONG == "メッセージが長すぎます"
        assert ErrorMessages.CONNECTION_FAILED == "接続に失敗しました"
        
        # SuccessMessages定数のテスト
        print("✓ SuccessMessages定数:")
        assert SuccessMessages.POST_SUCCESS == "投稿が完了しました"
        assert SuccessMessages.DATA_UPDATE_SUCCESS == "データの更新が完了しました"
        assert SuccessMessages.COMMAND_PROCESSED == "コマンドが正常に処理されました"
        
        # DefaultValues定数のテスト
        print("✓ DefaultValues定数:")
        assert DefaultValues.POST_TIMES == ['00:01', '12:00']
        assert DefaultValues.TIMEZONE == 'Asia/Tokyo'
        assert DefaultValues.HTTP_TIMEOUT == 30
        assert DefaultValues.DATA_UPDATE_INTERVAL_HOURS == 24
        assert DefaultValues.LOG_LEVEL == 'INFO'
        assert DefaultValues.SCHEDULED_POST_VISIBILITY == 'home'
        
        # FilePaths定数のテスト
        print("✓ FilePaths定数:")
        assert FilePaths.DATABASE_PATH == 'data/timeline.db'
        assert FilePaths.LOG_DIR == 'logs'
        assert FilePaths.SUMMARIES_DIR == 'data/summaries'
        assert FilePaths.TEMPLATE_FILE == 'data/summaries/template.md'
        
        # RegexPatterns定数のテスト
        print("✓ RegexPatterns定数:")
        assert len(RegexPatterns.DATE_PATTERNS) == 4
        assert RegexPatterns.HTML_LINK_PATTERN == r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        assert RegexPatterns.LINK_TEMP_PATTERN == r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND'
        assert RegexPatterns.MARKDOWN_LINK_PATTERN == r'\[([^\]]+)\]\(([^)]+)\)'
        
        # HTMLClasses定数のテスト
        print("✓ HTMLClasses定数:")
        assert HTMLClasses.IMPORTANT_CLASSES == ['str', 'str2']
        assert HTMLClasses.YEAR_CLASS == 'year'
        assert HTMLClasses.EVENT_CLASS == 'event'
        
        # SystemdServices定数のテスト
        print("✓ SystemdServices定数:")
        assert SystemdServices.MAIN_SERVICE == 'dsns-timeline-bot-main'
        assert SystemdServices.DATA_UPDATE_SERVICE == 'dsns-bot-data-update'
        assert SystemdServices.BACKUP_SERVICE == 'dsns-bot-backup'
        assert SystemdServices.DATA_UPDATE_TIMER == 'dsns-bot-data-update.timer'
        assert SystemdServices.BACKUP_TIMER == 'dsns-bot-backup.timer'
        
        # HTTPConfig定数のテスト
        print("✓ HTTPConfig定数:")
        assert HTTPConfig.TIMEOUT == 30
        assert HTTPConfig.USER_AGENT == 'DSNS-Timeline-Bot/1.0'
        assert HTTPConfig.MAX_RETRIES == 3
        assert HTTPConfig.RETRY_DELAY == 1.0
        assert HTTPConfig.CONNECTION_LIMIT == 100
        assert HTTPConfig.CONNECTION_LIMIT_PER_HOST == 10
        
        # DatabaseConfig定数のテスト
        print("✓ DatabaseConfig定数:")
        assert DatabaseConfig.BACKUP_RETENTION_DAYS == 7
        assert DatabaseConfig.MAX_BACKUP_SIZE_MB == 100
        assert DatabaseConfig.VACUUM_THRESHOLD == 1000
        assert DatabaseConfig.JOURNAL_MODE == 'WAL'
        assert DatabaseConfig.SYNCHRONOUS == 'NORMAL'
        assert DatabaseConfig.CACHE_SIZE == -64000
        assert DatabaseConfig.TEMP_STORE == 'MEMORY'
        
        print("✓ 定数の包括的テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 定数の包括的テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exceptions_comprehensive():
    """例外クラスの包括的テスト"""
    print("\n=== 例外クラスの包括的テスト ===")
    
    try:
        from exceptions import (
            DSNSBotError, DataServiceError, BotClientError,
            CommandParseError, DatabaseError, ConfigError,
            ValidationError, MessageLimitError, HealthCheckError,
            ScheduledPostError, NetworkError, FileOperationError,
            SummaryError, SystemError, HandlerError,
            StatusHandlerError, DecadeHandlerError
        )
        
        # 基底例外のテスト
        print("✓ 基底例外クラス:")
        base_error = DSNSBotError("テストエラー", {"key": "value"})
        assert str(base_error) == "テストエラー (詳細: {'key': 'value'})"
        assert base_error.message == "テストエラー"
        assert base_error.details == {"key": "value"}
        
        # データサービス例外のテスト
        print("✓ データサービス例外:")
        data_error = DataServiceError("データ取得失敗", "https://example.com", 404)
        assert data_error.url == "https://example.com"
        assert data_error.status_code == 404
        assert "データ取得失敗" in str(data_error)
        
        # ボットクライアント例外のテスト
        print("✓ ボットクライアント例外:")
        bot_error = BotClientError("接続失敗", "public", "test_note")
        assert bot_error.visibility == "public"
        assert bot_error.note_id == "test_note"
        
        # コマンド解析例外のテスト
        print("✓ コマンド解析例外:")
        cmd_error = CommandParseError("無効なコマンド", "invalid_cmd", "unknown")
        assert cmd_error.command == "invalid_cmd"
        assert cmd_error.command_type == "unknown"
        
        # データベース例外のテスト
        print("✓ データベース例外:")
        db_error = DatabaseError("クエリ失敗", "timeline_events", "SELECT")
        assert db_error.table == "timeline_events"
        assert db_error.operation == "SELECT"
        
        # 設定例外のテスト
        print("✓ 設定例外:")
        config_error = ConfigError("設定ファイルが見つかりません", "database_path", "/invalid/path")
        assert config_error.config_key == "database_path"
        assert config_error.config_value == "/invalid/path"
        
        # バリデーション例外のテスト
        print("✓ バリデーション例外:")
        validation_error = ValidationError("無効な値", "url", "invalid_url")
        assert validation_error.field == "url"
        assert validation_error.value == "invalid_url"
        
        # メッセージ制限例外のテスト
        print("✓ メッセージ制限例外:")
        limit_error = MessageLimitError("メッセージが長すぎます", 3500, 3000)
        assert limit_error.current_length == 3500
        assert limit_error.max_length == 3000
        assert limit_error.details['excess_length'] == 500
        
        # ヘルスチェック例外のテスト
        print("✓ ヘルスチェック例外:")
        health_error = HealthCheckError("ヘルスチェック失敗", "database", "unhealthy")
        assert health_error.component == "database"
        assert health_error.status == "unhealthy"
        
        # 定期投稿例外のテスト
        print("✓ 定期投稿例外:")
        scheduled_error = ScheduledPostError("定期投稿失敗", "12:00", "public")
        assert scheduled_error.scheduled_time == "12:00"
        assert scheduled_error.visibility == "public"
        
        # ネットワーク例外のテスト
        print("✓ ネットワーク例外:")
        network_error = NetworkError("接続タイムアウト", "https://example.com", 30.0)
        assert network_error.url == "https://example.com"
        assert network_error.timeout == 30.0
        
        # ファイル操作例外のテスト
        print("✓ ファイル操作例外:")
        file_error = FileOperationError("ファイル読み込み失敗", "/path/to/file", "read")
        assert file_error.file_path == "/path/to/file"
        assert file_error.operation == "read"
        
        # 概要例外のテスト
        print("✓ 概要例外:")
        summary_error = SummaryError("概要ファイルが見つかりません", "1990s", "/path/to/file")
        assert summary_error.decade == "1990s"
        assert summary_error.file_path == "/path/to/file"
        
        # システム例外のテスト
        print("✓ システム例外:")
        system_error = SystemError("システムリソース不足", "memory", "RAM")
        assert system_error.component == "memory"
        assert system_error.resource == "RAM"
        
        # ハンドラー例外のテスト
        print("✓ ハンドラー例外:")
        handler_error = HandlerError("ハンドラー初期化失敗", "today_handler", "today")
        assert handler_error.handler_type == "today_handler"
        assert handler_error.command == "today"
        
        # ステータスハンドラー例外のテスト
        print("✓ ステータスハンドラー例外:")
        status_error = StatusHandlerError("ステータス取得失敗", "server", "system")
        assert status_error.status_type == "server"
        assert status_error.component == "system"
        
        # 年代ハンドラー例外のテスト
        print("✓ 年代ハンドラー例外:")
        decade_error = DecadeHandlerError("年代統計取得失敗", "1990s", "statistics")
        assert decade_error.decade == "1990s"
        assert decade_error.sub_type == "statistics"
        
        # 例外の階層構造テスト
        print("✓ 例外階層構造:")
        exceptions = [
            data_error, bot_error, cmd_error, db_error, config_error,
            validation_error, limit_error, health_error, scheduled_error,
            network_error, file_error, summary_error, system_error,
            handler_error, status_error, decade_error
        ]
        
        for exc in exceptions:
            assert isinstance(exc, DSNSBotError), f"{type(exc).__name__} is not a DSNSBotError"
        
        print("✓ 例外クラスの包括的テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 例外クラスの包括的テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_types_comprehensive():
    """型定義の包括的テスト"""
    print("\n=== 型定義の包括的テスト ===")
    
    try:
        from dsnstypes import (
            CommandDict, EventData, DatabaseEvent, StatisticsData,
            DecadeStatistics, SystemInfo, BotStatus, DatabaseStatus,
            HealthCheckResult, PostResult, SearchResult, ConfigValues,
            LogEntry, UpdateHistory, DecadeSummary, MentionNotification,
            ScheduledPostConfig, ErrorInfo, PerformanceStats, CacheEntry,
            ConfigValidationResult, TestResult, BackupInfo, MonitoringAlert,
            StatusInfo, StatusSystemInfo, StatusDatabaseInfo,
            VisibilityType
        )
        
        # 基本型のテスト
        print("✓ 基本型定義:")
        
        # CommandDictのテスト
        command: CommandDict = {
            "type": "date",
            "sub_type": None,
            "query": "5月1日",
            "date": "05-01",
            "year": None,
            "month": None,
            "day": None
        }
        assert command["type"] == "date"
        assert command["query"] == "5月1日"
        
        # EventDataのテスト
        event: EventData = {
            "year": 2023,
            "month": 5,
            "day": 1,
            "content": "テストイベント",
            "category": "test"
        }
        assert event["year"] == 2023
        assert event["content"] == "テストイベント"
        
        # DatabaseEventのテスト
        db_event: DatabaseEvent = {
            "rowid": 1,
            "year": 2023,
            "month": 5,
            "day": 1,
            "content": "テストイベント",
            "category": "test"
        }
        assert db_event["rowid"] == 1
        
        # StatisticsDataのテスト
        stats: StatisticsData = {
            "total_events": 1000,
            "average_per_year": 50.0,
            "max_year": 2023,
            "min_year": 1990,
            "year_distribution": {2023: 100, 2022: 90}
        }
        assert stats["total_events"] == 1000
        assert stats["average_per_year"] == 50.0
        
        # DecadeStatisticsのテスト
        decade_stats: DecadeStatistics = {
            "decade": "1990s",
            "start_year": 1990,
            "end_year": 1999,
            "total_events": 500,
            "average_per_year": 50.0,
            "max_year": 1995,
            "min_year": 1990,
            "year_distribution": {1995: 60, 1990: 40}
        }
        assert decade_stats["decade"] == "1990s"
        assert decade_stats["start_year"] == 1990
        
        # SystemInfoのテスト
        system_info: SystemInfo = {
            "cpu_percent": 25.5,
            "memory_percent": 60.0,
            "disk_percent": 45.0,
            "uptime": 86400.0,
            "load_average": [1.0, 1.5, 2.0]
        }
        assert system_info["cpu_percent"] == 25.5
        assert len(system_info["load_average"]) == 3
        
        # BotStatusのテスト
        bot_status: BotStatus = {
            "is_connected": True,
            "uptime": 3600.0,
            "message_count": 100,
            "error_count": 5,
            "last_message_time": datetime.now(),
            "last_error_time": None
        }
        assert bot_status["is_connected"] == True
        assert bot_status["message_count"] == 100
        
        # DatabaseStatusのテスト
        db_status: DatabaseStatus = {
            "total_events": 1000,
            "oldest_event": event,
            "newest_event": event,
            "last_update": datetime.now(),
            "decade_distribution": {"1990s": 200, "2000s": 300}
        }
        assert db_status["total_events"] == 1000
        assert len(db_status["decade_distribution"]) == 2
        
        # HealthCheckResultのテスト
        health_result: HealthCheckResult = {
            "status": "healthy",
            "message": "システム正常",
            "details": {"component": "database", "response_time": 0.1},
            "timestamp": datetime.now()
        }
        assert health_result["status"] == "healthy"
        
        # PostResultのテスト
        post_result: PostResult = {
            "success": True,
            "message": "投稿完了",
            "visibility": "public",
            "timestamp": datetime.now(),
            "error": None
        }
        assert post_result["success"] == True
        assert post_result["visibility"] == "public"
        
        # SearchResultのテスト
        search_result: SearchResult = {
            "query": "テスト",
            "events": [event],
            "total_count": 1,
            "truncated": False,
            "remaining_count": 0
        }
        assert search_result["query"] == "テスト"
        assert len(search_result["events"]) == 1
        
        # ConfigValuesのテスト
        config_values: ConfigValues = {
            "misskey_url": "https://example.com",
            "misskey_token": "token123",
            "timeline_url": "https://timeline.com",
            "database_path": "data/timeline.db",
            "post_times": ["00:01", "12:00"],
            "timezone": "Asia/Tokyo",
            "log_level": "INFO",
            "debug_mode": False,
            "dry_run_mode": False,
            "http_timeout": 30,
            "data_update_interval_hours": 24,
            "scheduled_post_visibility": "home"
        }
        assert config_values["misskey_url"] == "https://example.com"
        assert config_values["scheduled_post_visibility"] == "home"
        
        # VisibilityTypeのテスト
        print("✓ VisibilityType:")
        valid_visibilities: List[VisibilityType] = ["public", "home", "followers", "specified"]
        for vis in valid_visibilities:
            assert vis in ["public", "home", "followers", "specified"]
        
        # 複雑な型のテスト
        print("✓ 複雑な型定義:")
        
        # StatusInfoのテスト
        status_info: StatusInfo = {
            "uptime": "1日",
            "message_count": 100,
            "error_count": 5,
            "database_events": 1000,
            "startup_time": datetime.now(),
            "is_connected": True,
            "error_rate": 0.05,
            "dry_run_mode": False,
            "avg_response_time": "0.1秒",
            "memory_usage": "50MB",
            "success_rate": 0.95,
            "cpu_usage": "25%",
            "disk_usage": "45%",
            "connection_count": 10,
            "last_connection": "2023-01-01 12:00:00",
            "debug_mode": False,
            "log_level": "INFO",
            "last_command_time": "2023-01-01 12:00:00",
            "handlers_count": 5,
            "available_handlers": "today,date,search,help,status",
            "last_heartbeat": "2023-01-01 12:00:00",
            "max_response_time": "0.5秒",
            "min_response_time": "0.05秒",
            "database_size": "10MB",
            "last_data_update": "2023-01-01 12:00:00",
            "last_update_result": "success",
            "oldest_event": "1990年1月1日",
            "newest_event": "2023年12月31日",
            "decade_distribution": "1990s:200, 2000s:300",
            "timeline_url": "https://timeline.com",
            "last_fetch_time": "2023-01-01 12:00:00",
            "last_fetch_result": "success"
        }
        assert status_info["message_count"] == 100
        assert status_info["is_connected"] == True
        
        print("✓ 型定義の包括的テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 型定義の包括的テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_existing_code():
    """既存コードとの統合テスト"""
    print("\n=== 既存コードとの統合テスト ===")
    
    try:
        # 既存のモジュールが新しい定数と例外を使用できるかテスト
        from constants import MessageLimits, ErrorMessages, Visibility
        from exceptions import DSNSBotError, DataServiceError
        
        # 定数の使用テスト
        print("✓ 定数の使用:")
        assert MessageLimits.MAX_LENGTH == 3000
        assert ErrorMessages.DATA_FETCH_FAILED == "データの取得に失敗しました"
        assert Visibility.PUBLIC == "public"
        
        # 例外の使用テスト
        print("✓ 例外の使用:")
        try:
            raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED, "https://example.com", 404)
        except DataServiceError as e:
            assert e.url == "https://example.com"
            assert e.status_code == 404
            assert isinstance(e, DSNSBotError)
        
        # 型定義の使用テスト
        print("✓ 型定義の使用:")
        from dsnstypes import CommandDict, EventData, VisibilityType
        
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
        
        print("✓ 既存コードとの統合テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ 既存コードとの統合テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_scenarios():
    """エラーハンドリングシナリオのテスト"""
    print("\n=== エラーハンドリングシナリオのテスト ===")
    
    try:
        from constants import ErrorMessages, MessageLimits
        from exceptions import (
            DataServiceError, DatabaseError, BotClientError,
            CommandParseError, ValidationError, MessageLimitError
        )
        
        # データサービスエラーのシナリオ
        print("✓ データサービスエラーシナリオ:")
        try:
            raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED, "https://example.com", 404)
        except DataServiceError as e:
            assert e.message == ErrorMessages.DATA_FETCH_FAILED
            assert e.url == "https://example.com"
            assert e.status_code == 404
        
        # データベースエラーのシナリオ
        print("✓ データベースエラーシナリオ:")
        try:
            raise DatabaseError(ErrorMessages.DATABASE_ERROR, "timeline_events", "SELECT")
        except DatabaseError as e:
            assert e.message == ErrorMessages.DATABASE_ERROR
            assert e.table == "timeline_events"
            assert e.operation == "SELECT"
        
        # ボットクライアントエラーのシナリオ
        print("✓ ボットクライアントエラーシナリオ:")
        try:
            raise BotClientError("投稿失敗", "public", "note123")
        except BotClientError as e:
            assert e.visibility == "public"
            assert e.note_id == "note123"
        
        # コマンド解析エラーのシナリオ
        print("✓ コマンド解析エラーシナリオ:")
        try:
            raise CommandParseError(ErrorMessages.INVALID_COMMAND, "invalid_cmd", "unknown")
        except CommandParseError as e:
            assert e.message == ErrorMessages.INVALID_COMMAND
            assert e.command == "invalid_cmd"
            assert e.command_type == "unknown"
        
        # バリデーションエラーのシナリオ
        print("✓ バリデーションエラーシナリオ:")
        try:
            raise ValidationError("無効なURL", "url", "invalid_url")
        except ValidationError as e:
            assert e.field == "url"
            assert e.value == "invalid_url"
        
        # メッセージ制限エラーのシナリオ
        print("✓ メッセージ制限エラーシナリオ:")
        try:
            raise MessageLimitError(ErrorMessages.MESSAGE_TOO_LONG, 3500, MessageLimits.MAX_LENGTH)
        except MessageLimitError as e:
            assert e.message == ErrorMessages.MESSAGE_TOO_LONG
            assert e.current_length == 3500
            assert e.max_length == MessageLimits.MAX_LENGTH
            assert e.details['excess_length'] == 500
        
        print("✓ エラーハンドリングシナリオのテスト完了")
        return True
        
    except Exception as e:
        print(f"✗ エラーハンドリングシナリオのテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("分散SNS関連年表bot - リファクタリング後の包括的テスト")
    print("=" * 60)
    
    tests = [
        ("定数の包括的テスト", test_constants_comprehensive),
        ("例外クラスの包括的テスト", test_exceptions_comprehensive),
        ("型定義の包括的テスト", test_types_comprehensive),
        ("既存コードとの統合テスト", test_integration_with_existing_code),
        ("エラーハンドリングシナリオのテスト", test_error_handling_scenarios)
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
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
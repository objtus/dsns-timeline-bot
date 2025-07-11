"""
分散SNS関連年表bot - 型定義

アプリケーション全体で使用する型定義を定義します。
"""

from typing import TypedDict, Literal, Union, Optional, List, Dict, Any
from datetime import datetime, date

# 公開範囲の型
VisibilityType = Literal['public', 'home', 'followers', 'specified']

# コマンド辞書の型
class CommandDict(TypedDict):
    """パースされたコマンド辞書"""
    type: str
    sub_type: Optional[str]
    query: Optional[str]
    date: Optional[str]
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]

# イベントデータの型
class EventData(TypedDict):
    """イベントデータ"""
    year: int
    month: int
    day: int
    content: str
    category: Optional[str]

# データベースイベントの型
class DatabaseEvent(TypedDict):
    """データベースから取得したイベント"""
    rowid: int
    year: int
    month: int
    day: int
    content: str
    category: Optional[str]

# 統計情報の型
class StatisticsData(TypedDict):
    """統計情報"""
    total_events: int
    average_per_year: float
    max_year: int
    min_year: int
    year_distribution: Dict[int, int]

# 年代別統計の型
class DecadeStatistics(TypedDict):
    """年代別統計"""
    decade: str
    start_year: int
    end_year: int
    total_events: int
    average_per_year: float
    max_year: int
    min_year: int
    year_distribution: Dict[int, int]

# システム情報の型
class SystemInfo(TypedDict):
    """システム情報"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime: float
    load_average: List[float]

# ボット状態の型
class BotStatus(TypedDict):
    """ボット状態"""
    is_connected: bool
    uptime: float
    message_count: int
    error_count: int
    last_message_time: Optional[datetime]
    last_error_time: Optional[datetime]

# データベース状態の型
class DatabaseStatus(TypedDict):
    """データベース状態"""
    total_events: int
    oldest_event: Optional[EventData]
    newest_event: Optional[EventData]
    last_update: Optional[datetime]
    decade_distribution: Dict[str, int]

# ヘルスチェック結果の型
class HealthCheckResult(TypedDict):
    """ヘルスチェック結果"""
    status: Literal['healthy', 'degraded', 'unhealthy']
    message: str
    details: Dict[str, Any]
    timestamp: datetime

# 投稿結果の型
class PostResult(TypedDict):
    """投稿結果"""
    success: bool
    message: str
    visibility: VisibilityType
    timestamp: datetime
    error: Optional[str]

# 検索結果の型
class SearchResult(TypedDict):
    """検索結果"""
    query: str
    events: List[EventData]
    total_count: int
    truncated: bool
    remaining_count: int

# 設定値の型
class ConfigValues(TypedDict):
    """設定値"""
    misskey_url: str
    misskey_token: str
    timeline_url: str
    database_path: str
    post_times: List[str]
    timezone: str
    log_level: str
    debug_mode: bool
    dry_run_mode: bool
    http_timeout: int
    data_update_interval_hours: int
    scheduled_post_visibility: VisibilityType

# ログエントリの型
class LogEntry(TypedDict):
    """ログエントリ"""
    timestamp: datetime
    level: str
    message: str
    module: str
    function: str
    line: int
    exception: Optional[str]

# 更新履歴の型
class UpdateHistory(TypedDict):
    """更新履歴"""
    id: int
    timestamp: datetime
    events_added: int
    events_updated: int
    events_deleted: int
    status: str
    error_message: Optional[str]

# 年代別概要の型
class DecadeSummary(TypedDict):
    """年代別概要"""
    decade: str
    title: str
    content: str
    file_path: str
    last_modified: datetime

# メンション通知の型
class MentionNotification(TypedDict):
    """メンション通知"""
    id: str
    user_id: str
    note_id: str
    text: str
    timestamp: datetime
    visibility: VisibilityType

# 定期投稿設定の型
class ScheduledPostConfig(TypedDict):
    """定期投稿設定"""
    enabled: bool
    times: List[str]
    visibility: VisibilityType
    timezone: str
    duplicate_prevention_hours: int

# エラー情報の型
class ErrorInfo(TypedDict):
    """エラー情報"""
    error_type: str
    message: str
    timestamp: datetime
    module: str
    function: str
    line: int
    traceback: Optional[str]

# パフォーマンス統計の型
class PerformanceStats(TypedDict):
    """パフォーマンス統計"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    max_response_time: float
    min_response_time: float
    last_request_time: Optional[datetime]

# キャッシュエントリの型
class CacheEntry(TypedDict):
    """キャッシュエントリ"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime

# 設定検証結果の型
class ConfigValidationResult(TypedDict):
    """設定検証結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_config: ConfigValues

# テスト結果の型
class TestResult(TypedDict):
    """テスト結果"""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str]
    details: Dict[str, Any]

# バックアップ情報の型
class BackupInfo(TypedDict):
    """バックアップ情報"""
    file_path: str
    size_bytes: int
    created_at: datetime
    backup_type: Literal['database', 'config', 'logs']
    status: Literal['success', 'failed', 'in_progress']

# 監視アラートの型
class MonitoringAlert(TypedDict):
    """監視アラート"""
    alert_id: str
    severity: Literal['info', 'warning', 'error', 'critical']
    title: str
    message: str
    timestamp: datetime
    component: str
    resolved: bool
    resolved_at: Optional[datetime]

# ステータス情報の型
class StatusInfo(TypedDict):
    """ステータス情報"""
    # 基本情報
    uptime: str
    message_count: int
    error_count: int
    database_events: int
    startup_time: Optional[datetime]
    is_connected: bool
    error_rate: float
    dry_run_mode: bool
    avg_response_time: str
    memory_usage: str
    success_rate: float
    
    # サーバー情報
    cpu_usage: str
    disk_usage: str
    connection_count: int
    last_connection: str
    debug_mode: bool
    log_level: str
    
    # ボット情報
    last_command_time: str
    handlers_count: int
    available_handlers: str
    last_heartbeat: str
    max_response_time: str
    min_response_time: str
    
    # 年表情報
    database_size: str
    last_data_update: str
    last_update_result: str
    oldest_event: str
    newest_event: str
    decade_distribution: str
    timeline_url: str
    last_fetch_time: str
    last_fetch_result: str

# システム情報の型（StatusHandler用）
class StatusSystemInfo(TypedDict):
    """システム情報（StatusHandler用）"""
    cpu_usage: str
    memory_usage: str
    disk_usage: str

# データベース情報の型（StatusHandler用）
class StatusDatabaseInfo(TypedDict):
    """データベース情報（StatusHandler用）"""
    database_size: str
    last_data_update: str
    last_update_result: str
    oldest_event: str
    newest_event: str
    decade_distribution: str
    last_fetch_time: str
    last_fetch_result: str 
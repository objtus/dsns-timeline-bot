"""
分散SNS関連年表bot - 定数定義

アプリケーション全体で使用する定数を定義します。
"""

from typing import List

class Visibility:
    """投稿の公開範囲"""
    PUBLIC = 'public'
    HOME = 'home'
    FOLLOWERS = 'followers'
    SPECIFIED = 'specified'
    
    @classmethod
    def get_all(cls) -> List[str]:
        """全ての公開範囲を取得"""
        return [cls.PUBLIC, cls.HOME, cls.FOLLOWERS, cls.SPECIFIED]
    
    @classmethod
    def is_valid(cls, visibility: str) -> bool:
        """公開範囲が有効かチェック"""
        return visibility in cls.get_all()

class MessageLimits:
    """メッセージの文字数制限"""
    MAX_LENGTH = 3000
    MAX_MESSAGE_LENGTH = 3000
    TRUNCATE_LENGTH = 2997
    SHORT_MESSAGE_LENGTH = 2500
    SAFETY_MARGIN = 50

class TimeFormats:
    """時刻フォーマット"""
    POST_TIME_FORMAT = '%H:%M'
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    TIME_ONLY_FORMAT = '%H:%M:%S'

class CommandTypes:
    """コマンドタイプ"""
    TODAY = 'today'
    DATE = 'date'
    SEARCH = 'search'
    HELP = 'help'
    STATUS = 'status'
    DECADE = 'decade'

class StatusSubTypes:
    """ステータスサブタイプ"""
    BASIC = 'basic'
    SERVER = 'server'
    BOT = 'bot'
    TIMELINE = 'timeline'

class DecadeSubTypes:
    """年代別統計サブタイプ"""
    STATISTICS = 'statistics'
    REPRESENTATIVE = 'representative'
    SUMMARY = 'summary'

class CategorySubTypes:
    """カテゴリサブタイプ"""
    LIST = 'list'
    STATISTICS = 'statistics'
    FILTER = 'filter'

class CategoryConfig:
    """カテゴリ設定"""
    MAX_FILTER_RESULTS = 50
    MAX_CATEGORY_LENGTH = 50
    CATEGORY_SEPARATOR = ' '
    EXCLUDE_PREFIX = '-'
    INCLUDE_PREFIX = '+'

class HealthStatus:
    """ヘルスチェック状態"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'

class LogLevels:
    """ログレベル"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class DatabaseTables:
    """データベーステーブル名"""
    TIMELINE_EVENTS = 'timeline_events'
    UPDATE_HISTORY = 'update_history'

class HTTPStatus:
    """HTTPステータスコード"""
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503

class ErrorMessages:
    """エラーメッセージ"""
    DATA_FETCH_FAILED = "データの取得に失敗しました"
    DATABASE_ERROR = "データベースエラーが発生しました"
    INVALID_COMMAND = "無効なコマンドです"
    MESSAGE_TOO_LONG = "メッセージが長すぎます"
    CONNECTION_FAILED = "接続に失敗しました"
    TIMEOUT_ERROR = "タイムアウトエラーが発生しました"
    SESSION_INIT_FAILED = "セッション初期化に失敗しました"
    NETWORK_ERROR = "ネットワークエラーが発生しました"
    VALIDATION_ERROR = "データ検証エラーが発生しました"

class SuccessMessages:
    """成功メッセージ"""
    POST_SUCCESS = "投稿が完了しました"
    DATA_UPDATE_SUCCESS = "データの更新が完了しました"
    COMMAND_PROCESSED = "コマンドが正常に処理されました"

class DefaultValues:
    """デフォルト値"""
    POST_TIMES = ['00:01', '12:00']
    TIMEZONE = 'Asia/Tokyo'
    HTTP_TIMEOUT = 30
    DATA_UPDATE_INTERVAL_HOURS = 24
    LOG_LEVEL = 'INFO'
    SCHEDULED_POST_VISIBILITY = 'home'

class FilePaths:
    """ファイルパス"""
    DATABASE_PATH = 'data/timeline.db'
    LOG_DIR = 'logs'
    SUMMARIES_DIR = 'data/summaries'
    TEMPLATE_FILE = 'data/summaries/template.md'

class RegexPatterns:
    """正規表現パターン"""
    DATE_PATTERNS = [
        r'(\d{2})月(\d{2})日',  # 05月01日
        r'(\d{1,2})月(\d{1,2})日',  # 5月1日
        r'(\d{2})/(\d{2})',  # 05/01
        r'(\d{1,2})/(\d{1,2})',  # 5/1
    ]
    
    HTML_LINK_PATTERN = r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
    LINK_TEMP_PATTERN = r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND'
    MARKDOWN_LINK_PATTERN = r'\[([^\]]+)\]\(([^)]+)\)'

class HTMLClasses:
    """HTMLクラス名"""
    IMPORTANT_CLASSES = ['str', 'str2']
    YEAR_CLASS = 'year'
    EVENT_CLASS = 'event'

class SystemdServices:
    """systemdサービス名"""
    MAIN_SERVICE = 'dsns-timeline-bot-main'
    DATA_UPDATE_SERVICE = 'dsns-bot-data-update'
    BACKUP_SERVICE = 'dsns-bot-backup'
    DATA_UPDATE_TIMER = 'dsns-bot-data-update.timer'
    BACKUP_TIMER = 'dsns-bot-backup.timer'

class HTTPConfig:
    """HTTP設定"""
    TIMEOUT = 30
    USER_AGENT = 'DSNS-Timeline-Bot/1.0'
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    CONNECTION_LIMIT = 100
    CONNECTION_LIMIT_PER_HOST = 10

class DatabaseConfig:
    """データベース設定"""
    BACKUP_RETENTION_DAYS = 7
    MAX_BACKUP_SIZE_MB = 100
    VACUUM_THRESHOLD = 1000
    JOURNAL_MODE = 'WAL'
    SYNCHRONOUS = 'NORMAL'
    CACHE_SIZE = -64000  # 64MB
    TEMP_STORE = 'MEMORY' 
"""
分散SNS関連年表bot - カスタム例外

アプリケーション全体で使用するカスタム例外クラスを定義します。
"""

from typing import Optional, Dict, Any


class DSNSBotError(Exception):
    """分散SNS関連年表botの基底例外クラス"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        例外を初期化
        
        Args:
            message: エラーメッセージ
            details: 詳細情報
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = None  # 後で設定される場合がある
    
    def __str__(self) -> str:
        """文字列表現"""
        if self.details:
            return f"{self.message} (詳細: {self.details})"
        return self.message


class DataServiceError(DSNSBotError):
    """データサービス関連エラー"""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        """
        データサービスエラーを初期化
        
        Args:
            message: エラーメッセージ
            url: リクエストURL
            status_code: HTTPステータスコード
        """
        details = {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class DatabaseError(DSNSBotError):
    """データベース関連エラー"""
    
    def __init__(self, message: str, table: Optional[str] = None, operation: Optional[str] = None):
        """
        データベースエラーを初期化
        
        Args:
            message: エラーメッセージ
            table: 対象テーブル
            operation: 実行操作
        """
        details = {}
        if table:
            details['table'] = table
        if operation:
            details['operation'] = operation
        
        super().__init__(message, details)
        self.table = table
        self.operation = operation


class BotClientError(DSNSBotError):
    """ボットクライアント関連エラー"""
    
    def __init__(self, message: str, visibility: Optional[str] = None, note_id: Optional[str] = None):
        """
        ボットクライアントエラーを初期化
        
        Args:
            message: エラーメッセージ
            visibility: 投稿公開範囲
            note_id: ノートID
        """
        details = {}
        if visibility:
            details['visibility'] = visibility
        if note_id:
            details['note_id'] = note_id
        
        super().__init__(message, details)
        self.visibility = visibility
        self.note_id = note_id


class CommandParseError(DSNSBotError):
    """コマンド解析エラー"""
    
    def __init__(self, message: str, command: Optional[str] = None, command_type: Optional[str] = None):
        """
        コマンド解析エラーを初期化
        
        Args:
            message: エラーメッセージ
            command: 元のコマンド文字列
            command_type: コマンドタイプ
        """
        details = {}
        if command:
            details['command'] = command
        if command_type:
            details['command_type'] = command_type
        
        super().__init__(message, details)
        self.command = command
        self.command_type = command_type


class ConfigError(DSNSBotError):
    """設定関連エラー"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[str] = None):
        """
        設定エラーを初期化
        
        Args:
            message: エラーメッセージ
            config_key: 設定キー
            config_value: 設定値
        """
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value:
            details['config_value'] = config_value
        
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class ValidationError(DSNSBotError):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        """
        バリデーションエラーを初期化
        
        Args:
            message: エラーメッセージ
            field: 検証対象フィールド
            value: 検証対象値
        """
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = value
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class MessageLimitError(DSNSBotError):
    """メッセージ制限エラー"""
    
    def __init__(self, message: str, current_length: int, max_length: int):
        """
        メッセージ制限エラーを初期化
        
        Args:
            message: エラーメッセージ
            current_length: 現在の文字数
            max_length: 最大文字数
        """
        details = {
            'current_length': current_length,
            'max_length': max_length,
            'excess_length': current_length - max_length
        }
        
        super().__init__(message, details)
        self.current_length = current_length
        self.max_length = max_length


class HealthCheckError(DSNSBotError):
    """ヘルスチェックエラー"""
    
    def __init__(self, message: str, component: Optional[str] = None, status: Optional[str] = None):
        """
        ヘルスチェックエラーを初期化
        
        Args:
            message: エラーメッセージ
            component: 対象コンポーネント
            status: ヘルスステータス
        """
        details = {}
        if component:
            details['component'] = component
        if status:
            details['status'] = status
        
        super().__init__(message, details)
        self.component = component
        self.status = status


class ScheduledPostError(DSNSBotError):
    """定期投稿エラー"""
    
    def __init__(self, message: str, scheduled_time: Optional[str] = None, visibility: Optional[str] = None):
        """
        定期投稿エラーを初期化
        
        Args:
            message: エラーメッセージ
            scheduled_time: 予定時刻
            visibility: 公開範囲
        """
        details = {}
        if scheduled_time:
            details['scheduled_time'] = scheduled_time
        if visibility:
            details['visibility'] = visibility
        
        super().__init__(message, details)
        self.scheduled_time = scheduled_time
        self.visibility = visibility


class NetworkError(DSNSBotError):
    """ネットワーク関連エラー"""
    
    def __init__(self, message: str, url: Optional[str] = None, timeout: Optional[float] = None):
        """
        ネットワークエラーを初期化
        
        Args:
            message: エラーメッセージ
            url: リクエストURL
            timeout: タイムアウト時間
        """
        details = {}
        if url:
            details['url'] = url
        if timeout:
            details['timeout'] = timeout
        
        super().__init__(message, details)
        self.url = url
        self.timeout = timeout


class FileOperationError(DSNSBotError):
    """ファイル操作エラー"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        """
        ファイル操作エラーを初期化
        
        Args:
            message: エラーメッセージ
            file_path: ファイルパス
            operation: 実行操作
        """
        details = {}
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        
        super().__init__(message, details)
        self.file_path = file_path
        self.operation = operation


class SummaryError(DSNSBotError):
    """年代別概要関連エラー"""
    
    def __init__(self, message: str, decade: Optional[str] = None, file_path: Optional[str] = None):
        """
        年代別概要エラーを初期化
        
        Args:
            message: エラーメッセージ
            decade: 対象年代
            file_path: ファイルパス
        """
        details = {}
        if decade:
            details['decade'] = decade
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(message, details)
        self.decade = decade
        self.file_path = file_path


class SystemError(DSNSBotError):
    """システム関連エラー"""
    
    def __init__(self, message: str, component: Optional[str] = None, resource: Optional[str] = None):
        """
        システムエラーを初期化
        
        Args:
            message: エラーメッセージ
            component: 対象コンポーネント
            resource: 対象リソース
        """
        details = {}
        if component:
            details['component'] = component
        if resource:
            details['resource'] = resource
        
        super().__init__(message, details)
        self.component = component
        self.resource = resource


class HandlerError(DSNSBotError):
    """ハンドラー関連エラー"""
    
    def __init__(self, message: str, handler_type: Optional[str] = None, command: Optional[str] = None):
        """
        ハンドラーエラーを初期化
        
        Args:
            message: エラーメッセージ
            handler_type: ハンドラータイプ
            command: 処理対象コマンド
        """
        details = {}
        if handler_type:
            details['handler_type'] = handler_type
        if command:
            details['command'] = command
        
        super().__init__(message, details)
        self.handler_type = handler_type
        self.command = command


class StatusHandlerError(DSNSBotError):
    """ステータスハンドラー関連エラー"""
    
    def __init__(self, message: str, status_type: Optional[str] = None, component: Optional[str] = None):
        """
        ステータスハンドラーエラーを初期化
        
        Args:
            message: エラーメッセージ
            status_type: ステータスタイプ
            component: 対象コンポーネント
        """
        details = {}
        if status_type:
            details['status_type'] = status_type
        if component:
            details['component'] = component
        
        super().__init__(message, details)
        self.status_type = status_type
        self.component = component


class DecadeHandlerError(DSNSBotError):
    """年代別ハンドラー関連エラー"""
    
    def __init__(self, message: str, decade: Optional[str] = None, sub_type: Optional[str] = None):
        """
        年代別ハンドラーエラーを初期化
        
        Args:
            message: エラーメッセージ
            decade: 対象年代
            sub_type: サブタイプ（統計・代表・概要）
        """
        details = {}
        if decade:
            details['decade'] = decade
        if sub_type:
            details['sub_type'] = sub_type
        
        super().__init__(message, details)
        self.decade = decade
        self.sub_type = sub_type
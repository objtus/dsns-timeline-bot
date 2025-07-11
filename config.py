"""
分散SNS関連年表bot - 設定管理モジュール

このモジュールは以下を提供します：
- 環境変数からの設定読み込み
- 設定値の検証
- デフォルト値の管理
- 設定エラーハンドリング
"""

import os
from pathlib import Path
from typing import Optional, List
import logging

from constants import (
    DefaultValues, FilePaths, LogLevels, Visibility, 
    ErrorMessages, HTTPStatus
)
from exceptions import ConfigError, ValidationError
# 型定義のインポート
# from dsnstypes import VisibilityType  # 必要に応じて利用

class Config:
    """
    アプリケーション設定管理クラス
    
    環境変数から設定を読み込み、必要な検証を行う。
    .envファイルまたはシステム環境変数から設定を取得。
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        設定初期化
        
        Args:
            env_file: .envファイルのパス（指定しない場合は .env を使用）
        """
        self._load_env_file(env_file)
        self._validate_config()
        self._setup_logging()
    
    def _load_env_file(self, env_file: Optional[str] = None):
        """環境変数ファイルを読み込み"""
        if env_file is None:
            env_file = ".env"
        
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 環境変数が既に設定されていない場合のみ設定
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip()
    
    # Misskey関連設定
    @property
    def misskey_url(self) -> str:
        """MisskeyインスタンスのWebSocket URL"""
        url = os.getenv('MISSKEY_URL', '')
        if not url:
            raise ConfigError("MISSKEY_URL が設定されていません")
        return url
    
    @property
    def misskey_token(self) -> str:
        """Misskeyアクセストークン"""
        token = os.getenv('MISSKEY_TOKEN', '')
        if not token:
            raise ConfigError("MISSKEY_TOKEN が設定されていません")
        return token
    
    @property
    def misskey_instance_url(self) -> str:
        """MisskeyインスタンスのHTTP URL（WebSocket URLから生成）"""
        ws_url = self.misskey_url
        if ws_url.startswith('wss://'):
            return ws_url.replace('wss://', 'https://').replace('/streaming', '')
        elif ws_url.startswith('ws://'):
            return ws_url.replace('ws://', 'http://').replace('/streaming', '')
        else:
            raise ConfigError(f"不正なMISSKEY_URL形式: {ws_url}")
    
    # データソース設定
    @property
    def timeline_url(self) -> str:
        """分散SNS年表のURL"""
        return os.getenv(
            'TIMELINE_URL', 
            'https://yuinoid.neocities.org/txt/my_dsns_timeline'
        )
    
    @property
    def data_update_interval_hours(self) -> int:
        """データ更新間隔（時間）"""
        try:
            return int(os.getenv('DATA_UPDATE_INTERVAL_HOURS', '6'))
        except ValueError:
            return 6
    
    # データベース設定
    @property
    def database_path(self) -> Path:
        """SQLiteデータベースファイルのパス"""
        db_path = os.getenv('DATABASE_PATH', FilePaths.DATABASE_PATH)
        path = Path(db_path)
        # データディレクトリを自動作成
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def summaries_dir(self) -> Path:
        """概要ファイルディレクトリのパス"""
        summaries_path = os.getenv('SUMMARIES_DIR', FilePaths.SUMMARIES_DIR)
        path = Path(summaries_path)
        # 概要ディレクトリを自動作成
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # 投稿設定
    @property
    def post_times(self) -> List[str]:
        """定期投稿時刻のリスト（HH:MM形式）"""
        times_str = os.getenv('POST_TIMES', ','.join(DefaultValues.POST_TIMES))
        return [time.strip() for time in times_str.split(',')]
    
    @property
    def scheduled_post_visibility(self) -> str:
        """定期投稿の公開範囲"""
        visibility = os.getenv('SCHEDULED_POST_VISIBILITY', DefaultValues.SCHEDULED_POST_VISIBILITY)
        # 有効な公開範囲かチェック
        if not Visibility.is_valid(visibility):
            print(f"警告: 無効な公開範囲: {visibility}, デフォルトで{DefaultValues.SCHEDULED_POST_VISIBILITY}を使用")
            return DefaultValues.SCHEDULED_POST_VISIBILITY
        return visibility
    
    @property
    def timezone(self) -> str:
        """タイムゾーン"""
        return os.getenv('TIMEZONE', DefaultValues.TIMEZONE)
    
    # ログ設定
    @property
    def log_level(self) -> str:
        """ログレベル"""
        return os.getenv('LOG_LEVEL', DefaultValues.LOG_LEVEL).upper()
    
    @property
    def log_dir(self) -> Path:
        """ログディレクトリ"""
        log_path = Path(os.getenv('LOG_DIR', FilePaths.LOG_DIR))
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path
    
    @property
    def log_file(self) -> Path:
        """メインログファイルのパス"""
        return self.log_dir / 'dsns_bot.log'
    
    # HTTP設定
    @property
    def http_timeout(self) -> int:
        """HTTP リクエストタイムアウト（秒）"""
        try:
            return int(os.getenv('HTTP_TIMEOUT', str(DefaultValues.HTTP_TIMEOUT)))
        except ValueError:
            return DefaultValues.HTTP_TIMEOUT
    
    @property
    def user_agent(self) -> str:
        """HTTP User-Agent"""
        return os.getenv(
            'USER_AGENT', 
            'dsns-timeline-bot/1.0 (分散SNS関連年表bot)'
        )
    
    # 開発・デバッグ設定
    @property
    def debug_mode(self) -> bool:
        """デバッグモード"""
        return os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes')
    
    @property
    def dry_run_mode(self) -> bool:
        """ドライランモード（投稿を実際に行わない）"""
        return os.getenv('DRY_RUN_MODE', 'false').lower() in ('true', '1', 'yes')
    
    def _validate_config(self):
        """設定値の検証"""
        errors = []
        
        # 必須設定の確認
        try:
            self.misskey_url
        except ConfigError as e:
            errors.append(str(e))
        
        try:
            self.misskey_token
        except ConfigError as e:
            errors.append(str(e))
        
        # 投稿時刻の形式確認
        for time_str in self.post_times:
            if not self._is_valid_time_format(time_str):
                errors.append(f"不正な投稿時刻形式: {time_str} (HH:MM形式で指定してください)")
        
        # 公開範囲の確認
        if not Visibility.is_valid(self.scheduled_post_visibility):
            errors.append(f"不正な公開範囲: {self.scheduled_post_visibility} ({', '.join(Visibility.get_all())}のいずれかを指定してください)")
        
        # タイムアウト値の確認
        if self.http_timeout <= 0:
            errors.append("HTTP_TIMEOUT は正の整数で指定してください")
        
        if errors:
            raise ConfigError(f"設定エラー:\n" + "\n".join(f"- {error}" for error in errors))
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """時刻文字列がHH:MM形式かチェック"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except ValueError:
            return False
    
    def _setup_logging(self):
        """ログ設定の初期化"""
        log_level = getattr(logging, self.log_level, logging.INFO)
        
        # ルートロガーの設定
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # デバッグモード時の詳細ログ
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def get_env_summary(self) -> dict:
        """
        設定値の概要を取得（機密情報は隠す）
        
        Returns:
            設定値の辞書（トークンなどは一部隠蔽）
        """
        return {
            'misskey_url': self.misskey_url,
            'misskey_token': f"{self.misskey_token[:8]}..." if len(self.misskey_token) > 8 else "***",
            'timeline_url': self.timeline_url,
            'database_path': str(self.database_path),
            'post_times': self.post_times,
            'scheduled_post_visibility': self.scheduled_post_visibility,
            'timezone': self.timezone,
            'log_level': self.log_level,
            'debug_mode': self.debug_mode,
            'dry_run_mode': self.dry_run_mode,
            'http_timeout': self.http_timeout,
            'data_update_interval_hours': self.data_update_interval_hours
        }
    
    def __str__(self) -> str:
        """設定の文字列表現"""
        summary = self.get_env_summary()
        lines = ["=== DSNS Timeline Bot Configuration ==="]
        for key, value in summary.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


# 使用例とテスト用の関数
def test_config():
    """設定クラスのテスト関数"""
    try:
        config = Config()
        print("✅ 設定読み込み成功")
        print(config)
        return True
    except ConfigError as e:
        print(f"❌ 設定エラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


if __name__ == "__main__":
    # スタンドアロン実行時のテスト
    print("DSNS Timeline Bot - 設定管理モジュールテスト")
    print("=" * 50)
    test_config()
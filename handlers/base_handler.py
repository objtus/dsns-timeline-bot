"""
ハンドラー基底クラス

全てのハンドラーの共通機能を提供します。
"""

import logging
from typing import Any, Dict, Optional

from constants import ErrorMessages
from exceptions import HandlerError

logger = logging.getLogger(__name__)

class BaseHandler:
    """全ハンドラーの基底クラス"""
    
    def __init__(self, config, database, data_service, bot_client: Optional[Any] = None):
        """
        ハンドラーの初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            bot_client: ボットクライアント（Phase 3で追加予定）
        """
        self.config = config
        self.database = database
        self.data_service = data_service
        self.bot_client = bot_client
        
    async def handle(self, note, command):
        """
        各ハンドラーで実装必須のメソッド
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書
            
        Returns:
            str: 応答メッセージ
            
        Raises:
            NotImplementedError: サブクラスで実装されていない場合
        """
        raise NotImplementedError("handle method must be implemented by subclass")
        
    async def send_reply(self, note, message: str):
        """
        共通のリプライ送信処理（Phase 3で実装予定）
        
        現在は戻り値としてメッセージを返すのみ
        
        Args:
            note: リプライ対象のnote
            message: 送信メッセージ
            
        Returns:
            str: 送信予定のメッセージ
        """
        # Phase 3でbot_client経由の実装に変更予定
        logger.debug(f"リプライ準備: {message[:50]}...")
        return message
    
    def _add_timeline_url(self, message: str, search_type: str, **kwargs) -> str:
        """
        メッセージに年表URLを付加する共通処理
        
        Args:
            message: 元のメッセージ
            search_type: 検索タイプ ('today', 'date', 'search', 'decade')
            **kwargs: 検索タイプに応じたパラメータ
                - date: month, day
                - search: query
                - decade: start_year, end_year
        
        Returns:
            URL付加済みメッセージ（失敗時は元のメッセージ）
        """
        try:
            if not self.data_service:
                logger.warning("データサービスが利用できません")
                return message
            
            timeline_url = self.data_service.generate_timeline_url(search_type, **kwargs)
            message_with_url = f"{message}\n\n[年表はこちら]({timeline_url})"
            logger.debug(f"URL付加完了: {len(message_with_url)}文字")
            return message_with_url
            
        except Exception as e:
            logger.warning(f"URL付加エラー: {e}")
            # URL付加に失敗しても元のメッセージを返す
            return message
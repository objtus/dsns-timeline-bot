"""
LLM会話専用ハンドラー
"""

import logging

from constants import ErrorMessages
from exceptions import HandlerError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class LLMHandler(BaseHandler):
    """LLM会話専用ハンドラー"""
    
    def __init__(self, config, database, data_service, bot_client, llm_service):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            bot_client: ボットクライアント
            llm_service: LLMサービスオブジェクト
        """
        super().__init__(config, database, data_service, bot_client)
        self.llm_service = llm_service
    
    async def handle(self, note, command):
        """
        LLM会話要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='llm'）
            
        Returns:
            str: LLMの応答
        """
        try:
            logger.info("LLM会話処理開始")
            
            # LLM機能が有効かチェック
            if not self.llm_service.is_enabled():
                logger.warning("LLM機能が無効です")
                return "申し訳ございません。現在LLM機能は無効になっていますわ。"
            
            # メッセージを取得
            message = command.get('message', '').strip()
            
            if not message:
                logger.warning("LLMメッセージが空です")
                return "何かお話ししたいことがありますの？「/llm メッセージ」の形式で話しかけてくださいませ。"
            
            logger.info(f"LLMにメッセージ送信: {message[:50]}...")
            
            # LLMで応答生成
            response = self.llm_service.generate(prompt=message)
            
            if response:
                logger.info(f"LLM応答取得: {len(response)}文字")
                return response
            else:
                logger.error("LLM応答の生成に失敗しました")
                return "あら...わたくしったら、うまくお答えできませんでしたわ。もう一度お試しくださいませ。"
            
        except Exception as e:
            logger.error(f"LLM会話処理エラー: {e}", exc_info=True)
            raise HandlerError(
                f"LLM会話処理エラー: {e}",
                handler_type="llm",
                command=str(command)
            )

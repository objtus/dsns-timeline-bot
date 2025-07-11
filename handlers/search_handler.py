"""
検索機能専用ハンドラー
"""

import logging

from constants import ErrorMessages
from exceptions import HandlerError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class SearchHandler(BaseHandler):
    """検索機能専用ハンドラー"""
    
    async def handle(self, note, command):
        """
        検索要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='search', query='検索語', categories, exclude_categories）
            
        Returns:
            str: 検索結果メッセージ
        """
        try:
            query = command['query']
            categories = command.get('categories')
            exclude_categories = command.get('exclude_categories')
            logger.info(f"検索処理開始: '{query}', categories={categories}, exclude={exclude_categories}")
            
            if self.data_service:
                if categories:
                    message = self.data_service.search_events_message(
                        query, categories=categories, exclude_categories=exclude_categories
                    )
                else:
                    message = self.data_service.search_events_message(query)
                logger.info(f"検索結果メッセージ生成完了: {len(message)}文字")
                # URL付加
                if categories:
                    return self._add_timeline_url(message, 'search', query=query, categories=categories, exclude_categories=exclude_categories)
                else:
                    return self._add_timeline_url(message, 'search', query=query)
            else:
                logger.error("データサービスが利用できません")
                raise HandlerError(
                    f"データサービスが利用できません: 「{query}」",
                    handler_type="search",
                    command=str(command)
                )
                
        except Exception as e:
            logger.error(f"検索処理エラー: {e}")
            query = command.get('query', '不明')
            raise HandlerError(
                f"検索処理エラー: {e} (「{query}」)",
                handler_type="search",
                command=str(command)
            )
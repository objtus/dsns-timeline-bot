"""
特定日付のイベント処理専用ハンドラー
"""

import logging

from constants import ErrorMessages
from exceptions import HandlerError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class DateHandler(BaseHandler):
    """特定日付のイベント処理専用ハンドラー"""
    
    async def handle(self, note, command):
        """
        特定日付のイベント要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='date', month=X, day=Y）
            
        Returns:
            str: 指定日付のイベントメッセージ
        """
        try:
            month = command['month']
            day = command['day']
            
            logger.info(f"特定日付処理開始: {month}月{day}日")
            
            if self.data_service:
                message = self.data_service.get_date_events_message(month, day)
                logger.info(f"日付イベントメッセージ生成完了: {len(message)}文字")
                
                # 共通のURL付加処理を使用
                return self._add_timeline_url(message, 'date', month=month, day=day)
            else:
                logger.error("データサービスが利用できません")
                raise HandlerError(
                    f"データサービスが利用できません: {month:02d}月{day:02d}日",
                    handler_type="date",
                    command=str(command)
                )
                
        except Exception as e:
            logger.error(f"特定日付処理エラー: {e}")
            month = command.get('month', '?')
            day = command.get('day', '?')
            raise HandlerError(
                f"特定日付処理エラー: {e} ({month}月{day}日)",
                handler_type="date",
                command=str(command)
            )
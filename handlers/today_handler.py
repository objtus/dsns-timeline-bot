"""
今日のイベント処理専用ハンドラー

"""

import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any
import traceback

from config import Config
from database import TimelineDatabase as Database
from data_service import TimelineDataService as DataService
from bot_client import BotClient
from constants import (
    TimeFormats, DefaultValues, ErrorMessages, 
    SuccessMessages, Visibility
)
from exceptions import HandlerError, ScheduledPostError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class TodayHandler(BaseHandler):
    """今日のイベント処理専用ハンドラー"""
    
    def __init__(self, config: Config, database: Database, data_service: DataService, bot_client: Optional[BotClient] = None):
        """
        ハンドラー初期化
        
        Args:
            config: アプリケーション設定
            database: データベース管理オブジェクト
            data_service: データ取得サービス
            bot_client: ボットクライアント（Phase 3で使用）
        """
        super().__init__(config, database, data_service, bot_client)
        
        # 投稿履歴（重複投稿防止用）
        self.posted_dates: Dict[str, datetime] = {}
        
        # エラー統計
        self.error_count = 0
        self.last_error_time: Optional[datetime] = None
        self.last_successful_post: Optional[datetime] = None
    
    async def handle(self, note, command):
        """
        今日のイベント要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='today'）
            
        Returns:
            str: 今日のイベントメッセージ
        """
        try:
            logger.info("今日のイベント処理開始")
            
            # コマンドから対象日付を取得（通常は今日）
            target_date = command.get('date', date.today())
            
            message = await self.get_today_message(target_date)
            logger.info(f"今日のイベントメッセージ生成完了: {len(message)}文字")
            return message
            
        except Exception as e:
            logger.error(f"今日のイベント処理エラー: {e}")
            logger.debug(traceback.format_exc())
            raise HandlerError(
                f"今日のイベント処理エラー: {e}",
                handler_type="today",
                command=str(command)
            )

    async def get_today_message(self, target_date: Optional[date] = None) -> str:
        """
        今日のイベントメッセージを取得
        
        既存TodayEventHandlerのロジックを移行・統合
        
        Args:
            target_date: 対象日付（指定しない場合は今日）
            
        Returns:
            投稿用メッセージ
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            logger.info(f"今日のイベント取得: {target_date}")
            
            # データサービスからメッセージ生成
            # 既存のget_today_events_messageを使用するか、
            # get_date_events_messageで代替
            if hasattr(self.data_service, 'get_today_events_message'):
                message = self.data_service.get_today_events_message(target_date)
            else:
                # フォールバック: 月日指定でメッセージ取得
                message = self.data_service.get_date_events_message(target_date.month, target_date.day)
            
            # メッセージの妥当性チェック
            if not message or len(message.strip()) == 0:
                logger.warning("空のメッセージが生成されました")
                return self._get_fallback_message(target_date)
            
            # 共通のURL付加処理を使用
            return self._add_timeline_url(message, 'today')
            
        except Exception as e:
            logger.error(f"今日のメッセージ取得エラー: {e}")
            logger.debug(traceback.format_exc())
            return self._get_error_message(target_date or date.today())
    

    
    def _get_fallback_message(self, target_date: date) -> str:
        """
        フォールバックメッセージを生成
        
        Args:
            target_date: 対象日付
            
        Returns:
            フォールバックメッセージ
        """
        return f"今日は、\n{ErrorMessages.DATA_FETCH_FAILED}\nだそうです！申し訳ございません！"
    
    def _get_error_message(self, target_date: date) -> str:
        """
        エラーメッセージを生成
        
        Args:
            target_date: 対象日付
            
        Returns:
            エラーメッセージ
        """
        return f"今日は、\n{ErrorMessages.DATABASE_ERROR}\nだそうです！しばらくしてからお試しください！"
    
    def _add_hashtag_for_scheduled_post(self, message: str) -> str:
        """
        定期投稿用にハッシュタグを追加
        
        Args:
            message: 元のメッセージ
            
        Returns:
            ハッシュタグ付きメッセージ
        """
        hashtag = "#今日は何の日"
        
        # メッセージの最後にハッシュタグを追加
        if message and not message.endswith('\n'):
            message += '\n'
        
        message += f"\n{hashtag}"
        return message
    
    # 既存のメソッドを保持（将来の機能拡張用）
    def should_post_today(self, target_time: Optional[datetime] = None) -> bool:
        """
        今日の投稿が必要かチェック
        
        定期投稿機能用（Phase 3以降で使用予定）
        """
        if target_time is None:
            target_time = datetime.now()
        
        today_str = target_time.date().isoformat()
        
        logger.debug(f"定期投稿判定開始: {target_time}, 今日: {today_str}")
        
        # 今日既に投稿済みかチェック
        if today_str in self.posted_dates:
            last_post = self.posted_dates[today_str]
            if target_time - last_post < timedelta(hours=23):
                logger.debug(f"本日既に投稿済み: {last_post}")
                return False
        
        # 設定された投稿時刻かチェック
        if not hasattr(self.config, 'post_times'):
            logger.warning(f"投稿時刻設定がありません。デフォルト値: {DefaultValues.POST_TIMES}")
            return False
            
        current_time = target_time.time()
        logger.debug(f"現在時刻: {current_time}, 投稿時刻設定: {self.config.post_times}")
        
        for post_time_str in self.config.post_times:
            try:
                hour, minute = map(int, post_time_str.split(':'))
                post_time = time(hour, minute)
                
                # 投稿時刻の前後10分以内かチェック（より柔軟に）
                target_minutes = current_time.hour * 60 + current_time.minute
                post_minutes = post_time.hour * 60 + post_time.minute
                diff_minutes = abs(target_minutes - post_minutes)
                
                logger.debug(f"投稿時刻 {post_time_str}: 差分={diff_minutes}分, 10分以内={diff_minutes <= 10}")
                
                if diff_minutes <= 10:
                    logger.info(f"投稿時刻に該当: {post_time_str}")
                    return True
                    
            except ValueError:
                logger.warning(f"無効な投稿時刻設定: {post_time_str}")
                continue
        
        logger.debug("投稿タイミングではありません")
        return False
    
    async def post_scheduled_today_event(self, target_time: Optional[datetime] = None) -> bool:
        """
        定期投稿を実行（ホーム公開範囲）
        
        Args:
            target_time: 対象時刻（指定しない場合は現在時刻）
            
        Returns:
            投稿成功時True
        """
        try:
            if target_time is None:
                target_time = datetime.now()
            
            # 投稿タイミングチェック
            if not self.should_post_today(target_time):
                logger.debug("定期投稿タイミングではありません")
                return False
            
            logger.info("定期投稿開始")
            
            # 今日のイベントメッセージを取得
            message = await self.get_today_message(target_time.date())
            
            if not message:
                logger.error("定期投稿用メッセージの取得に失敗")
                return False
            
            # 定期投稿用にハッシュタグを追加
            message = self._add_hashtag_for_scheduled_post(message)
            
            # BotClient経由で投稿（設定された公開範囲）
            if self.bot_client:
                try:
                    # 設定から公開範囲を取得
                    visibility = getattr(self.config, 'scheduled_post_visibility', DefaultValues.SCHEDULED_POST_VISIBILITY)
                    
                    # 統一された投稿処理を使用（戻り値を確認）
                    success = await self.bot_client.send_note(message, visibility=visibility)
                    
                    if success:
                        # 投稿履歴を記録
                        today_str = target_time.date().isoformat()
                        self.posted_dates[today_str] = target_time
                        self.last_successful_post = target_time
                        
                        logger.info(f"✅ 定期投稿完了（{visibility}公開範囲）")
                        return True
                    else:
                        logger.error("BotClient投稿が失敗しました")
                        # 投稿に失敗しても履歴は記録（重複防止のため）
                        today_str = target_time.date().isoformat()
                        self.posted_dates[today_str] = target_time
                        logger.warning("投稿に失敗しましたが、重複防止のため履歴を記録しました")
                        return False
                except Exception as send_error:
                    logger.error(f"BotClient投稿エラー: {send_error}")
                    # 投稿に失敗しても履歴は記録（重複防止のため）
                    today_str = target_time.date().isoformat()
                    self.posted_dates[today_str] = target_time
                    logger.warning("投稿に失敗しましたが、重複防止のため履歴を記録しました")
                    return False
            else:
                logger.error("BotClientが未初期化のため定期投稿できません")
                return False
                
        except Exception as e:
            logger.error(f"定期投稿エラー: {e}")
            logger.debug(traceback.format_exc())
            self.error_count += 1
            self.last_error_time = target_time or datetime.now()
            return False
    
    def get_handler_status(self) -> Dict[str, Any]:
        """
        ハンドラーの状態情報を取得
        
        Returns:
            状態情報の辞書
        """
        return {
            'handler_type': 'today_event',
            'posted_dates_count': len(self.posted_dates),
            'recent_posts': list(self.posted_dates.keys())[-5:],  # 最近5件
            'error_count': self.error_count,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'last_successful_post': self.last_successful_post.isoformat() if self.last_successful_post else None,
            'dry_run_mode': getattr(self.config, 'dry_run_mode', False)
        }
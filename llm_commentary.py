"""
LLMコメンタリー機能

その日のイベントを読んで、LLMがコメントを生成する機能を提供します。
"""

import logging
import re
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMCommentaryService:
    """LLMコメント生成サービス"""
    
    def __init__(self, config, database, data_service, llm_service):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            llm_service: LLMサービスオブジェクト
        """
        self.config = config
        self.database = database
        self.data_service = data_service
        self.llm_service = llm_service
        self.last_note_id: Optional[str] = None
        
        logger.info("LLMCommentaryService初期化完了")
    
    def save_note_id(self, note_id: str):
        """
        元投稿のnote IDを保存
        
        Args:
            note_id: 保存するnote ID
        """
        self.last_note_id = note_id
        logger.info(f"元投稿ID保存: {note_id}")
    
    async def generate_commentary(self, date: Optional[datetime] = None) -> Optional[str]:
        """
        その日のイベントに対するコメントを生成
        
        Args:
            date: 対象日（デフォルトは今日）
            
        Returns:
            str: 生成されたコメント（失敗時はNone）
        """
        try:
            if not self.llm_service or not self.llm_service.is_enabled():
                logger.warning("LLMサービスが無効です")
                return None
            
            # 対象日の取得
            target_date = date or datetime.now()
            month = target_date.month
            day = target_date.day
            
            logger.info(f"LLMコメント生成開始: {month}/{day}")
            
            # その日のイベントを取得
            events = self.database.get_events_by_date(month, day)
            
            if not events:
                logger.warning(f"{month}/{day}のイベントが見つかりません")
                return None
            
            logger.info(f"{month}/{day}のイベント取得: {len(events)}件")
            
            # イベントテキストを構築
            event_texts = []
            for event in events:
                # TimelineEventオブジェクトから属性を取得
                year = getattr(event, 'year', '????')
                content = getattr(event, 'content', '')
                content = content.strip() if content else ''
                
                # Markdown形式のURL（[テキスト](URL)）をテキストのみに変換
                content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
                
                if content:
                    event_texts.append(f"{year}年: {content}")
            
            if not event_texts:
                logger.warning("イベントテキストが空です")
                return None
            
            # LLM用のプロンプトを構築（全イベントを含める）
            events_summary = "\n".join(event_texts)  # 全件
            prompt = f"""今日（{month}月{day}日）の分散SNS関連年表のできごとを読んで、感想を述べてください。

【今日のできごと】
{events_summary}

100-400文字程度で感想を述べてください：
- ネット文化や歴史について、本日の意義について感想を述べる
- 全体の感想をまず述べる
- その後、各できごとについて、簡単に感想を述べる
- 最後に、もっとも印象に残ったできごとについて、その感想を述べる

感想："""
            
            logger.info(f"LLMにプロンプト送信: {len(prompt)}文字, イベント数: {len(event_texts)}件")
            
            # LLMでコメント生成（同期関数）
            commentary = self.llm_service.generate(prompt)
            
            if commentary:
                logger.info(f"LLMコメント生成成功: {len(commentary)}文字")
                return commentary
            else:
                logger.warning("LLMコメント生成失敗")
                return None
                
        except Exception as e:
            logger.error(f"コメント生成エラー: {e}")
            logger.debug("", exc_info=True)
            return None
    
    async def post_commentary(self, bot_client) -> bool:
        """
        生成したコメントを投稿
        
        Args:
            bot_client: BotClientオブジェクト
            
        Returns:
            bool: 投稿成功時True
        """
        try:
            # bot_clientから最後の投稿IDを取得
            note_id = getattr(bot_client, 'last_posted_note_id', None) or self.last_note_id
            
            if not note_id:
                logger.warning("元投稿IDが保存されていません")
                return False
            
            logger.info(f"元投稿ID: {note_id}")
            
            # コメント生成
            commentary = await self.generate_commentary()
            
            if not commentary:
                logger.warning("コメント生成に失敗しました")
                return False
            
            # ハッシュタグを追加
            commentary_with_hashtag = f"{commentary}\n\n#今日はなんの日LLM感想"
            logger.info(f"ハッシュタグ追加: {len(commentary_with_hashtag)}文字")
            
            # 元投稿にリプライ
            note = type('Note', (), {'id': note_id})()  # 簡易noteオブジェクト
            success = await bot_client.send_reply(note, commentary_with_hashtag)
            
            if success:
                logger.info("✅ LLMコメント投稿完了")
                # 投稿後はIDをクリア
                bot_client.last_posted_note_id = None
                self.last_note_id = None
                return True
            else:
                logger.error("LLMコメント投稿失敗")
                return False
                
        except Exception as e:
            logger.error(f"コメント投稿エラー: {e}")
            logger.debug("", exc_info=True)
            return False
    
    def get_stats(self) -> dict:
        """
        統計情報を取得
        
        Returns:
            dict: 統計情報
        """
        return {
            'llm_enabled': self.llm_service and self.llm_service.is_enabled(),
            'last_note_id': self.last_note_id,
        }

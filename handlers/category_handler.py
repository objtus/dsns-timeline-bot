"""
カテゴリ機能専用ハンドラー

カテゴリ複合フィルタリング、カテゴリ一覧、カテゴリ統計機能を提供
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_handler import BaseHandler
from constants import MessageLimits, ErrorMessages, SuccessMessages
from exceptions import HandlerError, DatabaseError
from dsnstypes import CommandDict

logger = logging.getLogger(__name__)

class CategoryHandler(BaseHandler):
    """カテゴリ機能専用ハンドラー"""
    
    def __init__(self, config, database, data_service, bot_client=None):
        """ハンドラー初期化"""
        super().__init__(config, database, data_service, bot_client)
        logger.info("CategoryHandler初期化完了")
    
    async def handle(self, note, command: CommandDict) -> str:
        """
        カテゴリコマンドの処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド情報
            
        Returns:
            str: 処理結果メッセージ
        """
        try:
            sub_type = command.get('sub_type', 'filter')
            
            if sub_type == 'list':
                return await self._handle_category_list()
            elif sub_type == 'statistics':
                return await self._handle_category_statistics()
            elif sub_type == 'analysis':
                return await self._handle_category_analysis(command)
            elif sub_type == 'filter':
                return await self._handle_category_filter(command)
            else:
                raise HandlerError("不明なカテゴリサブタイプ", "category_handler", sub_type)
                
        except Exception as e:
            logger.error(f"CategoryHandler処理エラー: {e}")
            raise HandlerError(f"カテゴリ処理エラー: {e}", "category_handler", command.get('type', 'unknown'))
    
    async def _handle_category_list(self) -> str:
        """
        カテゴリ一覧の表示
        
        Returns:
            str: カテゴリ一覧メッセージ
        """
        try:
            # 利用可能なカテゴリを取得
            available_categories = self.database.get_available_categories()
            
            if not available_categories:
                return "利用可能なカテゴリが見つかりませんでした。"
            
            # メッセージ構築
            message = "🗂️ **利用可能なカテゴリ一覧**\n\n"
            
            # カテゴリをアルファベット順にソート
            sorted_categories = sorted(available_categories)
            
            # カテゴリをグループ化して表示
            current_letter = ""
            for category in sorted_categories:
                if category and category[0] != current_letter:
                    current_letter = category[0].upper()
                    message += f"\n**{current_letter}**\n"
                message += f"• {category}\n"
            
            # 使用例を追加
            message += "\n📝 **使用例**\n"
            message += "• `カテゴリ dsns+tech` → dsnsかつtechカテゴリのイベント\n"
            message += "• `カテゴリ dsns+tech-meme` → dsns・techだがmeme以外のイベント\n"
            message += "• `カテゴリ一覧` → この一覧を表示\n"
            message += "• `カテゴリ統計` → カテゴリ統計情報を表示\n"
            
            # URL付加
            message = self._add_timeline_url(message, 'category')
            
            return message
            
        except Exception as e:
            logger.error(f"カテゴリ一覧取得エラー: {e}")
            return "カテゴリ一覧の取得に失敗しました。"
    
    async def _handle_category_statistics(self) -> str:
        """
        カテゴリ統計情報の表示
        
        Returns:
            str: カテゴリ統計メッセージ
        """
        try:
            # カテゴリ統計を取得
            stats = self.database.get_category_statistics()
            
            if not stats:
                return "カテゴリ統計情報を取得できませんでした。"
            
            # メッセージ構築
            message = "📊 **カテゴリ統計情報**\n\n"
            
            # 基本統計
            message += f"**総カテゴリ数**: {stats['total_categories']}個\n"
            message += f"**カテゴリ付きイベント数**: {stats['total_events_with_categories']}件\n\n"
            
            # 人気カテゴリ（上位10個）
            message += "**人気カテゴリ（上位10個）**\n"
            for i, (category, count) in enumerate(stats['popular_categories'], 1):
                message += f"{i}. {category}: {count}件\n"
            
            # 年代別分布
            message += "\n**年代別カテゴリ分布**\n"
            for decade, decade_stats in stats['decade_distribution'].items():
                if decade_stats:
                    # 各年代の上位3カテゴリ
                    top_categories = sorted(decade_stats.items(), key=lambda x: x[1], reverse=True)[:3]
                    message += f"\n**{decade}**: "
                    category_list = [f"{cat}({count})" for cat, count in top_categories]
                    message += ", ".join(category_list)
            
            # URL付加
            message = self._add_timeline_url(message, 'category')
            
            return message
            
        except Exception as e:
            logger.error(f"カテゴリ統計取得エラー: {e}")
            return "カテゴリ統計情報の取得に失敗しました。"
    
    async def _handle_category_analysis(self, command: CommandDict) -> str:
        """
        カテゴリ分析（共起カテゴリ）
        Args:
            command: パースされたコマンド情報
        Returns:
            str: 分析結果メッセージ
        """
        try:
            categories = command.get('categories', [])
            exclude_categories = command.get('exclude_categories', [])
            if not categories:
                return "分析対象のカテゴリが指定されていません。\n\n使用例: `カテゴリ分析 dsns`"
            # 共起カテゴリを取得
            cooccur = self.database.get_cooccurring_categories(categories, exclude_categories, limit=10)
            if not cooccur:
                return f"指定カテゴリ{'+' .join(categories)}と共起するカテゴリは見つかりませんでした。"
            # メッセージ構築
            cat_str = '+'.join(categories)
            message = f"🧩 **{cat_str}とよく組み合わさるカテゴリ**\n"
            for i, (cat, count) in enumerate(cooccur.items(), 1):
                message += f"{i}. {cat}: {count}回\n"
            # URL付加（カテゴリ分析はsearchタイプで代表カテゴリをクエリに）
            message = self._add_timeline_url(message, 'search', query=cat_str)
            return message
        except Exception as e:
            logger.error(f"カテゴリ分析取得エラー: {e}")
            return "カテゴリ分析情報の取得に失敗しました。"
    
    async def _handle_category_filter(self, command: CommandDict) -> str:
        """
        カテゴリフィルタリングの処理
        
        Args:
            command: パースされたコマンド情報
            
        Returns:
            str: フィルタリング結果メッセージ
        """
        try:
            categories = command.get('categories', [])
            exclude_categories = command.get('exclude_categories', [])
            
            if not categories:
                return "カテゴリが指定されていません。\n\n使用例: `カテゴリ dsns+tech`"
            
            # イベントを取得
            events = self.database.get_events_by_categories(
                categories=categories,
                exclude_categories=exclude_categories,
                limit=50  # 最大50件
            )
            
            if not events:
                # カテゴリが存在するかチェック
                available_categories = self.database.get_available_categories()
                invalid_categories = [cat for cat in categories if cat not in available_categories]
                
                if invalid_categories:
                    message = f"指定されたカテゴリが見つかりません: {', '.join(invalid_categories)}\n\n"
                    message += "`カテゴリ一覧` で利用可能なカテゴリを確認してください。"
                    return message
                else:
                    return f"指定されたカテゴリ条件に該当するイベントが見つかりませんでした。\n\n条件: 含める={categories}, 除外={exclude_categories}"
            
            # メッセージ構築
            category_str = "+".join(categories)
            exclude_str = "-".join(exclude_categories) if exclude_categories else ""
            
            if exclude_str:
                message = f"🗂️ **カテゴリ検索結果** ({category_str}-{exclude_str})\n\n"
            else:
                message = f"🗂️ **カテゴリ検索結果** ({category_str})\n\n"
            
            message += f"**検索条件**: 含める={categories}, 除外={exclude_categories}\n"
            message += f"**結果件数**: {len(events)}件\n\n"
            
            # イベント一覧
            for event in events:
                message += f"**{event.year}年**{event.get_date_str()}　{event.content}\n"
            
            # 文字数制限処理
            if len(message) > MessageLimits.MAX_LENGTH:
                message = self._truncate_message_with_events(message, events, len(events))
            
            # URL付加
            message = self._add_timeline_url(message, 'category')
            
            return message
            
        except Exception as e:
            logger.error(f"カテゴリフィルタリングエラー: {e}")
            return "カテゴリフィルタリングの処理に失敗しました。"
    
    def _truncate_message_with_events(self, message: str, events: List, total_count: int) -> str:
        """
        メッセージを文字数制限内に切り詰める（イベント付き）
        
        Args:
            message: 元のメッセージ
            events: イベントリスト
            total_count: 総イベント数
            
        Returns:
            str: 切り詰められたメッセージ
        """
        # ヘッダー部分を保持
        header_end = message.find("\n\n**結果件数**")
        if header_end == -1:
            header_end = message.find("\n\n")
        
        if header_end == -1:
            return message[:MessageLimits.TRUNCATE_LENGTH] + "..."
        
        header = message[:header_end]
        
        # イベント部分を段階的に追加
        truncated_message = header + "\n\n"
        included_count = 0
        
        for event in events:
            event_line = f"**{event.year}年**{event.get_date_str()}　{event.content}\n"
            
            if len(truncated_message + event_line) > MessageLimits.TRUNCATE_LENGTH:
                break
            
            truncated_message += event_line
            included_count += 1
        
        # 残件数表示
        remaining = total_count - included_count
        if remaining > 0:
            truncated_message += f"\n... 他{remaining}件"
        
        return truncated_message 
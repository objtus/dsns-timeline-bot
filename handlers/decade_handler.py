"""
年代別機能統合ハンドラー

年代別の統計、代表的なイベント、概要を処理するハンドラー
"""

import logging
import re
from typing import List, Tuple, Optional

from config import Config
from database import TimelineDatabase as Database
from data_service import TimelineDataService as DataService
from bot_client import BotClient
from dsnstypes import DecadeStatistics, EventData
from exceptions import DecadeHandlerError, DatabaseError, SummaryError
from constants import MessageLimits
from .base_handler import BaseHandler
from summary_manager import SummaryManager

logger = logging.getLogger(__name__)

class DecadeHandler(BaseHandler):
    """年代別機能統合ハンドラー"""
    
    def __init__(self, config: Config, database: Database, data_service: DataService, bot_client: Optional[BotClient] = None):
        """
        年代別ハンドラーの初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            bot_client: ボットクライアントオブジェクト（オプション）
            
        Raises:
            DecadeHandlerError: 初期化エラー時
        """
        try:
            super().__init__(config, database, data_service, bot_client)
            self.summary_manager = SummaryManager(config.summaries_dir)
            logger.info("DecadeHandler初期化完了")
        except Exception as e:
            logger.error(f"DecadeHandler初期化エラー: {e}")
            raise DecadeHandlerError(f"DecadeHandler初期化失敗: {e}")
    
    async def handle(self, note, command) -> str:
        """
        年代別要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書
            
        Returns:
            str: 処理結果メッセージ
            
        Raises:
            DecadeHandlerError: 処理エラー時
        """
        try:
            sub_type = command['sub_type']
            start_year = command['start_year']
            end_year = command['end_year']
            decade_name = command['decade_name']
            categories = command.get('categories', [])
            exclude_categories = command.get('exclude_categories', [])
            
            logger.info(f"年代別処理開始: {sub_type} - {start_year}-{end_year}, カテゴリ={categories}, 除外={exclude_categories}")
            
            if sub_type == '統計':
                return await self._handle_statistics(start_year, end_year, decade_name, categories, exclude_categories)
            elif sub_type == '代表':
                return await self._handle_representative(start_year, end_year, decade_name, categories, exclude_categories)
            elif sub_type == '概要':
                return await self._handle_summary(start_year, end_year, decade_name, categories, exclude_categories)
            else:
                return f"{decade_name}の機能を指定してください。\n\n利用可能な機能:\n• 統計 - 年代別統計情報\n• 代表 - 重要なイベント\n• 概要 - 年代の概要"
                
        except Exception as e:
            logger.error(f"年代別処理エラー: {e}")
            raise DecadeHandlerError(f"年代別処理失敗: {e}")
    
    async def _handle_statistics(self, start_year: int, end_year: int, decade_name: str, 
                                categories: Optional[List[str]] = None, exclude_categories: Optional[List[str]] = None) -> str:
        """
        統計情報処理
        
        Args:
            start_year: 開始年
            end_year: 終了年
            decade_name: 年代名
            categories: 含めるカテゴリリスト（オプション）
            exclude_categories: 除外するカテゴリリスト（オプション）
            
        Returns:
            str: 統計情報メッセージ
            
        Raises:
            DecadeHandlerError: 統計情報処理エラー時
        """
        try:
            if categories is None:
                categories = []
            if exclude_categories is None:
                exclude_categories = []
                
            if categories:
                # カテゴリ複合条件の場合
                events = self.database.get_events_by_decade_and_categories(
                    start_year, end_year, categories, exclude_categories
                )
                total_events = len(events)
                
                if total_events == 0:
                    category_info = f"（カテゴリ: {', '.join(categories)}"
                    if exclude_categories:
                        category_info += f", 除外: {', '.join(exclude_categories)}"
                    category_info += "）"
                    return f"{decade_name}{category_info}のイベントは見つかりませんでした。"
                
                avg_per_year = total_events / (end_year - start_year + 1) if total_events > 0 else 0
                
                # 年別分布を計算
                year_stats = {}
                for event in events:
                    year_stats[event.year] = year_stats.get(event.year, 0) + 1
                
                # 最多・最少年を計算
                if year_stats:
                    max_year = max(year_stats.items(), key=lambda x: x[1])
                    min_year = min(year_stats.items(), key=lambda x: x[1])
                else:
                    max_year = (start_year, 0)
                    min_year = (start_year, 0)
                
                # カテゴリ情報を追加
                category_info = f"（カテゴリ: {', '.join(categories)}"
                if exclude_categories:
                    category_info += f", 除外: {', '.join(exclude_categories)}"
                category_info += "）"
                
                message_parts = [
                    f"📊 **{decade_name}の統計情報{category_info}**",
                    f"・期間: {start_year}年〜{end_year}年",
                    f"・総イベント数: {total_events}件",
                    f"・年平均: {avg_per_year:.1f}件",
                    f"・最も多い年: {max_year[0]}年 ({max_year[1]}件)",
                    f"・最も少ない年: {min_year[0]}年 ({min_year[1]}件)",
                    "",
                    "📅 **年別分布**"
                ]
                
                # 年別分布（グラフ風表示）
                for year in range(start_year, end_year + 1):
                    count = year_stats.get(year, 0)
                    bar = "█" * min(count, 20)  # 最大20文字
                    message_parts.append(f"{year}年: {bar} {count}件")
                
            else:
                # 通常の年代別統計
                stats = self.database.get_decade_statistics(start_year, end_year)
                
                message_parts = [
                    f"📊 **{decade_name}の統計情報**",
                    f"・期間: {start_year}年〜{end_year}年",
                    f"・総イベント数: {stats['total_events']}件",
                    f"・年平均: {stats['avg_per_year']:.1f}件",
                    f"・最も多い年: {stats['max_year'][0]}年 ({stats['max_year'][1]}件)",
                    f"・最も少ない年: {stats['min_year'][0]}年 ({stats['min_year'][1]}件)",
                    "",
                    "📅 **年別分布**"
                ]
                
                # 年別分布（グラフ風表示）
                for year in range(start_year, end_year + 1):
                    count = stats['year_distribution'].get(year, 0)
                    bar = "█" * min(count, 20)  # 最大20文字
                    message_parts.append(f"{year}年: {bar} {count}件")
            
            result = "\n".join(message_parts)
            
            # 共通のURL付加処理を使用
            result = self._add_timeline_url(result, 'decade', start_year=start_year, end_year=end_year)
            
            logger.info(f"統計情報生成完了: {len(result)}文字")
            return result
            
        except Exception as e:
            logger.error(f"統計情報処理エラー: {e}")
            raise DecadeHandlerError(f"統計情報処理失敗: {e}")
    
    async def _handle_representative(self, start_year: int, end_year: int, decade_name: str,
                                   categories: Optional[List[str]] = None, exclude_categories: Optional[List[str]] = None) -> str:
        """
        代表的なイベント処理
        
        Args:
            start_year: 開始年
            end_year: 終了年
            decade_name: 年代名
            categories: 含めるカテゴリリスト（オプション）
            exclude_categories: 除外するカテゴリリスト（オプション）
            
        Returns:
            str: 代表イベントメッセージ
            
        Raises:
            DecadeHandlerError: 代表イベント処理エラー時
        """
        try:
            if categories is None:
                categories = []
            if exclude_categories is None:
                exclude_categories = []
                
            if categories:
                # カテゴリ複合条件の場合
                events = self.database.get_events_by_decade_and_categories(
                    start_year, end_year, categories, exclude_categories
                )
            else:
                # 通常の年代別検索
                events = self.database.get_events_by_year_range(start_year, end_year)
            
            if not events:
                category_info = ""
                if categories:
                    category_info = f"（カテゴリ: {', '.join(categories)}"
                    if exclude_categories:
                        category_info += f", 除外: {', '.join(exclude_categories)}"
                    category_info += "）"
                return f"{decade_name}{category_info}のイベントは見つかりませんでした。"
            
            # 重要度でフィルタリング：HTMLクラス付きのイベントのみ
            important_events = []
            for event in events:
                importance = self._calculate_event_importance(event, start_year, events)
                if importance > 0:  # HTMLクラス付きのイベントのみ
                    important_events.append(event)
            
            # 時系列順にソート（年→月→日）
            important_events.sort(key=lambda event: (event.year, event.month, event.day))
            
            # 重複除去：同じ内容のイベントは1つだけ表示
            seen_contents = set()
            unique_events = []
            for event in important_events:
                if event.content not in seen_contents:
                    unique_events.append(event)
                    seen_contents.add(event.content)
                    if len(unique_events) >= 500:  # 500件まで取得
                        break
            
            top_events = unique_events
            
            # カテゴリ情報を追加
            category_info = ""
            if categories:
                category_info = f"（カテゴリ: {', '.join(categories)}"
                if exclude_categories:
                    category_info += f", 除外: {', '.join(exclude_categories)}"
                category_info += "）"
            
            # 共通の文字数制限処理を使用
            header_parts = [f"✨ **{decade_name}の主要な出来事{category_info}**", ""]
            footer_parts = []
            context_info = f"代表イベント生成完了"
            
            result = self.data_service._truncate_message_with_events(
                top_events, self._format_decade_event, header_parts, footer_parts, 
                max_chars=MessageLimits.MAX_MESSAGE_LENGTH, context_info=context_info
            )
            
            # 共通のURL付加処理を使用
            result = self._add_timeline_url(result, 'decade', start_year=start_year, end_year=end_year)
            
            logger.info(f"代表イベント生成完了: {len(result)}文字")
            return result
            
        except Exception as e:
            logger.error(f"代表イベント処理エラー: {e}")
            raise DecadeHandlerError(f"代表イベント処理失敗: {e}")
    
    async def _handle_summary(self, start_year: int, end_year: int, decade_name: str,
                            categories: Optional[List[str]] = None, exclude_categories: Optional[List[str]] = None) -> str:
        """
        概要処理
        
        Args:
            start_year: 開始年
            end_year: 終了年
            decade_name: 年代名
            categories: 含めるカテゴリリスト（オプション）
            exclude_categories: 除外するカテゴリリスト（オプション）
            
        Returns:
            str: 概要メッセージ
            
        Raises:
            DecadeHandlerError: 概要処理エラー時
        """
        try:
            if categories is None:
                categories = []
            if exclude_categories is None:
                exclude_categories = []
                
            # SummaryManagerから概要を取得
            summary = self.summary_manager.get_decade_summary(start_year, end_year, decade_name)
            
            # カテゴリ情報を追加
            if categories:
                category_info = f"\n\n**カテゴリフィルタ**: {', '.join(categories)}"
                if exclude_categories:
                    category_info += f"（除外: {', '.join(exclude_categories)}）"
                summary += category_info
            
            # 共通のURL付加処理を使用
            summary = self._add_timeline_url(summary, 'decade', start_year=start_year, end_year=end_year)
            
            logger.info(f"概要生成完了: {len(summary)}文字")
            return summary
            
        except Exception as e:
            logger.error(f"概要処理エラー: {e}")
            raise DecadeHandlerError(f"概要処理失敗: {e}")
    
    def _calculate_event_importance(self, event, start_year: int, all_events: List) -> int:
        """
        イベントの重要度を計算（HTMLクラスのみ）
        
        Args:
            event: イベントオブジェクト
            start_year: 開始年
            all_events: 全イベントリスト
            
        Returns:
            int: 重要度スコア
        """
        return self._calculate_importance_by_html_class(event)
    
    def _calculate_importance_by_html_class(self, event) -> int:
        """
        HTMLクラスによる重要度計算
        
        Args:
            event: イベントオブジェクト
            
        Returns:
            int: 重要度スコア
        """
        importance = 0
        
        if hasattr(event, 'html_content') and event.html_content:
            # span.str, a.str クラス（最重要）
            if re.search(r'<span\s+class=["\']str["\'][^>]*>', event.html_content, re.IGNORECASE):
                importance += 100
            if re.search(r'<a[^>]*class=["\'][^"\']*str[^"\']*["\'][^>]*>', event.html_content, re.IGNORECASE):
                importance += 100
                
            # span.str2, a.str2 クラス（重要）
            if re.search(r'<span\s+class=["\']str2["\'][^>]*>', event.html_content, re.IGNORECASE):
                importance += 80
            if re.search(r'<a[^>]*class=["\'][^"\']*str2[^"\']*["\'][^>]*>', event.html_content, re.IGNORECASE):
                importance += 80
        
        return importance
    
    def _format_decade_event(self, event) -> str:
        """
        年代別イベントをメッセージ用にフォーマット
        最初の文（句点「。」まで）だけを表示
        
        Args:
            event: イベントオブジェクト
            
        Returns:
            str: フォーマットされたイベント文字列
        """
        content = event.content
        # 最初の句点までを抽出
        if "。" in content:
            content = content.split("。", 1)[0] + "。"
        return f"**{event.year}年**{content}"
"""
分散SNS関連年表bot - データ取得・処理サービス（完全修正版）

このモジュールは以下を提供します：
- 年表サイトからのHTMLデータ取得
- JavaScript処理の再現（日付抽出ロジック）
- 年表データのパース・構造化
- データベースへの保存・更新
- 「今日はなんの日？」機能の実装
- HTMLリンクのMarkdown変換
"""

import asyncio
import aiohttp
import logging
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Set, Any
from pathlib import Path
from bs4 import BeautifulSoup
import json

from config import Config
from database import TimelineDatabase, TimelineEvent
from constants import (
    MessageLimits, RegexPatterns, HTMLClasses, 
    ErrorMessages, HTTPStatus, HealthStatus
)
from exceptions import DataServiceError, NetworkError, ValidationError
from dsnstypes import EventData

logger = logging.getLogger(__name__)

class TimelineDataService:
    """
    年表データ取得・処理サービス
    
    元サイトのJavaScript処理を再現して、HTMLから年表データを抽出し、
    データベースに保存・更新する機能を提供
    """
    
    def __init__(self, config: Config, database: TimelineDatabase):
        """
        サービス初期化
        
        Args:
            config: アプリケーション設定
            database: データベース管理オブジェクト
        """
        self.config = config
        self.database = database
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 日付パターン（元サイトのJS処理を参考）
        self.date_patterns = RegexPatterns.DATE_PATTERNS
        
        # 除外パターン（ノイズデータの除去）
        self.exclude_patterns = [
            r'^[\s\-\*\#]*$',  # 空行や記号のみ
            r'^(参考|出典|引用|※)',  # 参考情報
            r'(年表|タイムライン|まとめ)$',  # メタ情報
        ]
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self._close_session()
    
    async def _init_session(self):
        """HTTP セッション初期化"""
        if self.session is None:
            try:
                timeout = aiohttp.ClientTimeout(total=self.config.http_timeout)
                headers = {
                    'User-Agent': self.config.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'ja,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers=headers,
                    connector=aiohttp.TCPConnector(limit=10, ssl=False)  # SSL検証を無効化
                )
                logger.debug("HTTP セッション初期化完了")
            except Exception as e:
                logger.error(f"HTTP セッション初期化エラー: {e}")
                raise DataServiceError(f"セッション初期化に失敗しました: {e}")
    
    async def _close_session(self):
        """HTTP セッション終了"""
        if self.session:
            try:
                await self.session.close()
                logger.debug("HTTP セッション終了完了")
            except Exception as e:
                logger.error(f"HTTP セッション終了エラー: {e}")
            finally:
                self.session = None
    
    async def fetch_timeline_html(self) -> str:
        """
        年表サイトからHTMLを取得
        
        Returns:
            取得したHTMLコンテンツ
            
        Raises:
            DataServiceError: 取得失敗時
        """
        try:
            logger.info(f"年表データ取得開始: {self.config.timeline_url}")
            
            if not self.session:
                raise DataServiceError("HTTP セッションが初期化されていません")
            
            async with self.session.get(self.config.timeline_url) as response:
                if response.status != HTTPStatus.OK:
                    raise DataServiceError(f"HTTP エラー: {response.status}")
                
                html_content = await response.text(encoding='utf-8')
                
                if len(html_content) < 1000:  # 異常に小さいレスポンス
                    raise DataServiceError(ErrorMessages.DATA_FETCH_FAILED)
                
                logger.info(f"HTML取得成功: {len(html_content)} bytes")
                return html_content
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"ネットワークエラー: {e}", url=self.config.timeline_url)
        except Exception as e:
            raise DataServiceError(f"予期しないエラー: {e}")
    
    def parse_timeline_html(self, html_content: str) -> List[TimelineEvent]:
        """
        HTMLから年表イベントを抽出
        
        元サイトのJavaScript処理を再現:
        1. timeline_layout div内の年別セクションを取得
        2. 各年のliタグからイベントを抽出
        3. 日付パターンマッチングでMM月DD日を抽出
        
        Args:
            html_content: パース対象のHTML
            
        Returns:
            抽出されたイベントのリスト
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            events = []
            
            # timeline_layout div を探す
            timeline_layout = soup.find('div', id='timeline_layout')
            if not timeline_layout:
                logger.warning("timeline_layout div が見つかりません")
                return events
            
            # 年別セクション（div[id="YYYY"]）を処理
            year_sections = timeline_layout.find_all('div', id=re.compile(r'^\d{4}$'))  # type: ignore
            logger.info(f"発見した年別セクション: {len(year_sections)}個")
            
            for year_section in year_sections:
                year_id = year_section.get('id')  # type: ignore
                if not year_id or not str(year_id).isdigit():
                    continue
                
                year = int(str(year_id))
                logger.debug(f"処理中の年: {year}")
                
                # 年セクション内のulタグを取得
                ul_elements = year_section.find_all('ul')  # type: ignore
                
                for ul in ul_elements:
                    li_elements = ul.find_all('li')  # type: ignore
                    
                    for li in li_elements:
                        # HTMLの内容を取得（構造保持のため）
                        event_html = str(li)
                        
                        # テキスト抽出（リンクも保持）
                        event_text = self._extract_clean_text(li)
                        
                        if not event_text or self._should_exclude(event_text):
                            continue
                        
                        # カテゴリ情報を取得（class属性から）
                        class_attr = li.get('class', [])  # type: ignore
                        categories = ' '.join(class_attr) if class_attr else ''
                        
                        # 日付抽出
                        dates = self._extract_dates(event_text)
                        
                        if dates:
                            for month, day in dates:
                                event = TimelineEvent(
                                    year=year,
                                    month=month,
                                    day=day,
                                    content=event_text,
                                    categories=categories,
                                    html_content=event_html
                                )
                                events.append(event)
                                
                                logger.debug(f"イベント抽出: {year}年{month:02d}月{day:02d}日 - {event_text[:50]}...")
                        else:
                            # 日付がない場合は1月1日として記録（年単位イベント）
                            event = TimelineEvent(
                                year=year,
                                month=1,
                                day=1,
                                content=event_text,
                                categories=categories,
                                html_content=event_html
                            )
                            events.append(event)
            
            logger.info(f"イベント抽出完了: {len(events)}件")
            return events
            
        except Exception as e:
            logger.error(f"HTML パースエラー: {e}")
            raise DataServiceError(f"HTMLパースに失敗しました: {e}")
    
    def _extract_clean_text(self, li_element) -> str:
        """
        liエレメントからクリーンなテキストを抽出
        
        Args:
            li_element: BeautifulSoupのliエレメント
            
        Returns:
            クリーンなテキスト（リンク情報も保持）
        """
        # HTMLの内容を文字列として取得
        html_str = str(li_element)
        
        # 1. liタグの内容のみを抽出
        li_match = re.search(r'<li[^>]*>(.*?)</li>', html_str, re.DOTALL)
        if li_match:
            content = li_match.group(1)
        else:
            content = html_str
        
        # 2. 改行コードとタブを空白に変換（HTMLの構造由来の改行を除去）
        content = re.sub(r'[\r\n\t]+', ' ', content)
        
        # 3. 複数の空白を単一に変換
        content = re.sub(r'\s{2,}', ' ', content)
        
        # 4. HTMLリンクを保持しつつテキスト抽出
        # <a>タグをテンポラリ形式に変換
        content = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', 
                        r'LINKSTART\1LINKMIDDLE\2LINKEND', content, flags=re.IGNORECASE)
        
        # 5. 他のHTMLタグは通常通り処理
        # <span class="str">を太字に変換
        content = re.sub(r'<span\s+class=["\']str["\'][^>]*>([^<]+)</span>', 
                        r'**\1**', content, flags=re.IGNORECASE)
        
        # 6. <br>タグを改行に変換
        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
        
        # 7. 残りのHTMLタグを削除
        content = re.sub(r'<[^>]+>', '', content)
        
        # 8. テンポラリ形式をMarkdownリンクに変換
        content = re.sub(r'LINKSTART(.*?)LINKMIDDLE(.*?)LINKEND', 
                        r'[\2](\1)', content)
        
        # 9. HTMLエンティティをデコード
        import html
        content = html.unescape(content)
        
        # 10. 前後の空白を除去
        content = content.strip()
        
        return content
    
    def _extract_dates(self, text: str) -> List[Tuple[int, int]]:
        """
        テキストから日付（月、日）を抽出
        
        元サイトのJavaScriptロジックを再現:
        - MM月DD日 形式を最優先
        - M月D日 形式も対応
        - MM/DD 形式も対応
        
        Args:
            text: 抽出対象テキスト
            
        Returns:
            (month, day) のタプルリスト
        """
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    month = int(match[0])
                    day = int(match[1])
                    
                    # 日付妥当性チェック
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        # 2月29日などの詳細チェックは省略（年表データの性質上）
                        if (month, day) not in dates:
                            dates.append((month, day))
                except ValueError:
                    continue
        
        return dates
    
    def _should_exclude(self, text: str) -> bool:
        """
        除外すべきテキストかチェック
        
        Args:
            text: チェック対象テキスト
            
        Returns:
            除外すべき場合True
        """
        if not text or len(text.strip()) < 3:
            return True
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    async def update_timeline_data(self) -> Dict[str, int]:
        """
        年表データの更新
        
        1. HTMLを取得
        2. イベントを抽出
        3. データベースに保存
        4. 更新履歴を記録
        
        Returns:
            更新結果の統計情報
        """
        try:
            logger.info("年表データ更新開始")
            
            # HTMLデータ取得
            html_content = await self.fetch_timeline_html()
            
            # イベント抽出
            events = self.parse_timeline_html(html_content)
            
            if not events:
                logger.warning("抽出されたイベントが0件です")
                return {'added': 0, 'updated': 0, 'total': 0}
            
            # データベース更新
            added_count, updated_count = self.database.add_events_batch(events)
            
            # 統計情報取得
            stats = self.database.get_statistics()
            total_count = stats['total_events']
            
            # 更新履歴記録
            self.database.record_update_history(
                added_count=added_count,
                updated_count=updated_count,
                total_count=total_count,
                source_url=self.config.timeline_url,
                status='success',
                notes=f'パース成功: {len(events)}件のイベントを処理'
            )
            
            logger.info(f"データ更新完了 - 追加: {added_count}, 更新: {updated_count}, 総計: {total_count}")
            
            return {
                'added': added_count,
                'updated': updated_count,
                'total': total_count,
                'parsed': len(events)
            }
            
        except Exception as e:
            logger.error(f"データ更新エラー: {e}")
            
            # エラー履歴記録
            self.database.record_update_history(
                added_count=0,
                updated_count=0,
                total_count=0,
                source_url=self.config.timeline_url,
                status='error',
                notes=str(e)
            )
            
            raise DataServiceError(f"データ更新に失敗しました: {e}")
    
    def _truncate_message_with_events(self, events: List[TimelineEvent], 
                                    formatter_func, 
                                    header_parts: List[str],
                                    footer_parts: List[str],
                                    max_chars: int = MessageLimits.MAX_LENGTH,
                                    context_info: str = "") -> str:
        """
        イベントリストを文字数制限付きでメッセージに変換する共通処理
        
        Args:
            events: イベントリスト
            formatter_func: イベントフォーマット関数
            header_parts: ヘッダー部分のメッセージパーツ
            footer_parts: フッター部分のメッセージパーツ
            max_chars: 最大文字数（デフォルト: MessageLimits.MAX_LENGTH）
            context_info: ログ出力用のコンテキスト情報
            
        Returns:
            文字数制限を適用したメッセージ
        """
        if not events:
            # イベントがない場合はヘッダーとフッターのみ
            message_parts = header_parts + footer_parts
            return "\n".join(message_parts)
        
        # メッセージ構築
        message_parts = header_parts.copy()
        
        # 文字数制限を考慮してイベントを制限
        current_chars = sum(len(part) + 1 for part in message_parts)  # +1 for newline
        displayed_count = 0
        total_count = len(events)
        
        for event in events:
            # フォーマット処理
            formatted_event = formatter_func(event)
            event_chars = len(formatted_event) + 1  # +1 for newline
            
            # 文字数制限チェック
            if current_chars + event_chars > max_chars:
                break
            
            message_parts.append(formatted_event)
            message_parts.append("")  # イベント間の空行
            current_chars += event_chars
            displayed_count += 1
        
        # 末尾の空行を削除してフッターを追加
        if message_parts and message_parts[-1] == "":
            message_parts.pop()
        
        message_parts.extend(footer_parts)
        
        # 追加結果の表示
        if displayed_count < total_count:
            remaining = total_count - displayed_count
            message_parts.append("")
            message_parts.append(f"（他に{remaining}件あります）")
        
        result = "\n".join(message_parts)
        
        # 最終的な文字数チェック（念のため）
        if len(result) > max_chars:
            result = result[:max_chars-3] + "..."
        
        logger.info(f"{context_info}: {displayed_count}/{total_count}件表示, {len(result)}文字")
        return result

    def get_today_events_message(self, target_date: Optional[date] = None) -> str:
        """
        「今日はなんの日？」メッセージを生成（改良版フォーマット、文字数制限対応）
        
        元サイトのJavaScriptロジックを再現し、さらに強化:
        - 今日の日付を MM月DD日 形式で取得
        - 該当する年表イベントを検索
        - 指定フォーマットでメッセージ生成（日付強調、リンク変換等）
        - 文字数制限（MessageLimits.MAX_LENGTH文字）と残件数表示
        
        Args:
            target_date: 対象日付（指定しない場合は今日）
            
        Returns:
            投稿用メッセージ（文字数制限対応）
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # 該当日付のイベント取得
            events = self.database.get_events_by_date(target_date.month, target_date.day)
            
            if not events:
                # イベントがない場合
                return "今日は、\nなんの日でもありません\nだそうです！よかったね！"
            
            # フォーマッター関数を定義
            def format_today_event(event):
                return self._format_event_for_message_v2(event, target_date.month, target_date.day)
            
            # 共通の文字数制限処理を使用
            header_parts = ["今日は、", ""]
            footer_parts = ["", "だそうです！よかったね！"]
            context_info = f"{target_date.month:02d}月{target_date.day:02d}日のイベント"
            
            return self._truncate_message_with_events(
                events, format_today_event, header_parts, footer_parts, 
                max_chars=MessageLimits.MAX_LENGTH, context_info=context_info
            )
            
        except Exception as e:
            logger.error(f"今日のイベントメッセージ生成エラー: {e}")
            return "今日は、\nデータ取得でエラーが発生しました\nだそうです！残念！"
    
    def _format_event_for_message_v2(self, event: TimelineEvent, target_month: int, target_day: int) -> str:
        """
        イベントをメッセージ用にフォーマット（改良版）
        
        Args:
            event: フォーマット対象イベント
            target_month: 対象月
            target_day: 対象日
            
        Returns:
            フォーマット済みイベントテキスト
        """
        
        # 1. 年を太字で表示
        formatted_text = f"**{event.year}年**"
        
        # 2. イベント内容を取得（既にリンクが変換済み）
        event_content = event.content
        
        # 3. 指定日付（今日の日付）を太字で強調
        event_content = self._emphasize_target_date(event_content, target_month, target_day)
        
        # 4. 最終的な改行処理
        event_content = self._preserve_original_line_breaks(event_content)
        
        return formatted_text + event_content
    
    def _emphasize_target_date(self, text: str, target_month: int, target_day: int) -> str:
        """
        指定日付を太字で強調
        
        Args:
            text: 処理前テキスト
            target_month: 対象月
            target_day: 対象日
            
        Returns:
            処理後テキスト
        """
        # 対象日付のパターンを生成
        target_date_patterns = [
            f"{target_month:02d}月{target_day:02d}日",  # 06月29日
            f"{target_month}月{target_day:02d}日",     # 6月29日
            f"{target_month:02d}月{target_day}日",     # 06月29日
            f"{target_month}月{target_day}日",         # 6月29日
        ]
        
        # 重複を避けるために、長い順にソート
        target_date_patterns.sort(key=len, reverse=True)
        
        for pattern in target_date_patterns:
            if pattern in text:
                # 既に太字になっていない場合のみ強調
                if f"**{pattern}**" not in text:
                    text = text.replace(pattern, f"**{pattern}**")
                break  # 最初にマッチしたパターンのみ処理
        
        return text
    
    def _preserve_original_line_breaks(self, text: str) -> str:
        """
        元のHTMLの改行をそのまま保持
        
        HTMLの<br>タグが既に改行に変換されているので、
        それ以外の余計な処理は行わない
        
        Args:
            text: 処理前テキスト（<br>→\n変換済み）
            
        Returns:
            処理後テキスト
        """
        # 1. 先頭・末尾の余分な空白のみ除去
        result = text.strip()
        
        # 2. 単語の途中での不適切な改行を修正
        # 英数字の途中で改行されている場合は空白に変換
        result = re.sub(r'([a-zA-Z0-9])\n+([a-zA-Z0-9])', r'\1 \2', result)
        
        # 3. 日本語文字の後の不適切な改行を修正
        # ひらがな・カタカナ・漢字の後に不適切な改行がある場合
        result = re.sub(r'([ぁ-んァ-ヶ一-龠ー])\n+([ぁ-んァ-ヶ一-龠ーa-zA-Z0-9])', r'\1\2', result)
        
        # 4. 連続する改行を2つまでに制限（3つ以上は2つに）
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 5. 余分な空白の除去（複数の空白を1つに）
        result = re.sub(r' {2,}', ' ', result)
        
        return result
    
    def get_date_events_message(self, month: int, day: int) -> str:
        """
        指定日付のイベントメッセージを生成（改良版フォーマット）
        
        Args:
            month: 月
            day: 日
            
        Returns:
            指定日付のイベントメッセージ
        """
        try:
            events = self.database.get_events_by_date(month, day)
            
            if not events:
                return f"{month}月{day}日は、\nなんの日でもありません\nだそうです！よかったね！"
            
            # フォーマッター関数を定義
            def format_date_event(event):
                return self._format_event_for_message_v2(event, month, day)
            
            # 共通の文字数制限処理を使用
            header_parts = [f"{month}月{day}日は、", ""]
            footer_parts = ["", "だそうです！よかったね！"]
            context_info = f"{month:02d}月{day:02d}日のイベント"
            
            return self._truncate_message_with_events(
                events, format_date_event, header_parts, footer_parts, 
                max_chars=MessageLimits.MAX_LENGTH, context_info=context_info
            )
            
        except Exception as e:
            logger.error(f"日付指定イベントメッセージ生成エラー: {e}")
            return f"{month:02d}月{day:02d}日は、\nデータ取得でエラーが発生しました\nだそうです！"
    
    def search_events_message(self, keyword: str, categories: Optional[list] = None, exclude_categories: Optional[list] = None, limit: int = 10) -> str:
        """
        キーワード検索結果のメッセージを生成（複合カテゴリ対応）
        
        Args:
            keyword: 検索キーワード
            categories: 含めるカテゴリリスト（オプション）
            exclude_categories: 除外カテゴリリスト（オプション）
            limit: 最大表示件数
        Returns:
            検索結果メッセージ（MessageLimits.MAX_LENGTH文字制限対応）
        """
        try:
            if categories:
                events = self.database.get_events_by_categories(categories, exclude_categories, limit=limit)
                # キーワードでさらにフィルタ（大文字小文字を区別しない）
                if keyword:
                    events = [e for e in events if keyword.lower() in e.content.lower()]
            else:
                events = self.database.search_events(keyword, limit)
            
            if not events:
                if categories:
                    return f"「{keyword}」かつカテゴリ{categories}に関するできごとは見つかりませんでした。"
                else:
                    return f"「{keyword}」に関するできごとは見つかりませんでした。"
            
            # フォーマッター関数を定義
            def format_search_event(event):
                date_str = f"{event.month:02d}月{event.day:02d}日"
                content = event.content
                # 大文字小文字を区別しないでキーワードを強調
                if keyword.lower() in content.lower():
                    # 元の大文字小文字を保持して強調
                    import re
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    content = pattern.sub(f"**{keyword}**", content)
                return f"**{event.year}年**{date_str}　{content}"
            
            header_parts = [f"「{keyword}」の検索結果：", ""]
            if categories:
                header_parts[0] = f"「{keyword}」＋カテゴリ{categories}の検索結果："
            footer_parts = []
            context_info = f"検索結果"
            
            return self._truncate_message_with_events(
                events, format_search_event, header_parts, footer_parts, 
                max_chars=MessageLimits.MAX_LENGTH, context_info=context_info
            )
        except Exception as e:
            logger.error(f"検索メッセージ生成エラー: {e}")
            return f"「{keyword}」の検索でエラーが発生しました。"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        サービス正常性チェック
        
        Returns:
            正常性チェック結果
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'status': HealthStatus.HEALTHY,
            'checks': {}
        }
        
        try:
            # HTTP接続チェック
            try:
                logger.debug(f"HTTP接続チェック開始: {self.config.timeline_url}")
                await self._init_session()
                if not self.session:
                    raise DataServiceError(ErrorMessages.SESSION_INIT_FAILED)
                
                async with self.session.get(self.config.timeline_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response_text = await response.text()
                    result['checks']['http_connectivity'] = {
                        'status': 'ok' if response.status == HTTPStatus.OK else 'error',
                        'status_code': response.status,
                        'response_size': len(response_text)
                    }
                    logger.debug(f"HTTP接続チェック成功: ステータス={response.status}, サイズ={len(response_text)}文字")
                    
            except Exception as e:
                logger.error(f"HTTP接続チェック失敗: {e}")
                result['checks']['http_connectivity'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # データベース接続チェック
            try:
                stats = self.database.get_statistics()
                result['checks']['database'] = {
                    'status': 'ok',
                    'total_events': stats['total_events'],
                    'last_update': stats['last_update']
                }
            except Exception as e:
                result['checks']['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # 今日のイベント生成チェック
            try:
                message = self.get_today_events_message()
                result['checks']['today_message'] = {
                    'status': 'ok',
                    'message_length': len(message)
                }
            except Exception as e:
                result['checks']['today_message'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # 全体ステータス判定
            failed_checks = [name for name, check in result['checks'].items() if check['status'] == 'error']
            
            # HTTP接続が失敗しても、データベースにデータがあればdegraded（一部機能制限）
            if failed_checks:
                if 'http_connectivity' in failed_checks and len(failed_checks) == 1:
                    # HTTP接続のみ失敗で、データベースは正常な場合
                    if 'database' in result['checks'] and result['checks']['database']['status'] == 'ok':
                        result['status'] = HealthStatus.DEGRADED
                        result['failed_checks'] = failed_checks
                        result['note'] = 'HTTP接続に問題がありますが、既存データで動作可能です'
                    else:
                        result['status'] = HealthStatus.UNHEALTHY
                        result['failed_checks'] = failed_checks
                else:
                    result['status'] = HealthStatus.DEGRADED if len(failed_checks) < len(result['checks']) else HealthStatus.UNHEALTHY
                    result['failed_checks'] = failed_checks
            
        except Exception as e:
            result['status'] = HealthStatus.UNHEALTHY
            result['error'] = str(e)
        
        finally:
            await self._close_session()
        
        # ヘルスチェック結果の詳細ログ
        logger.info(f"ヘルスチェック結果: {result['status']}")
        for check_name, check_result in result['checks'].items():
            if check_result['status'] == 'error':
                logger.warning(f"  {check_name}: {check_result.get('error', '不明なエラー')}")
            else:
                logger.debug(f"  {check_name}: OK")
        
        return result

    def generate_timeline_url(self, search_type: str, **kwargs) -> str:
        """
        年表サイトの検索URLを生成
        
        Args:
            search_type: 検索タイプ ('today', 'date', 'search')
            **kwargs: 検索タイプに応じたパラメータ
                - today: パラメータなし
                - date: month, day
                - search: query
        
        Returns:
            生成されたURL
        """
        base_url = "https://yuinoid.neocities.org/txt/my_dsns_timeline"
        
        if search_type == 'today':
            # 今日の日付で検索
            today = date.today()
            month_str = f"{today.month:02d}"
            day_str = f"{today.day:02d}"
            search_param = f"{month_str}月{day_str}日"
            
        elif search_type == 'date':
            # 特定日付で検索
            month = kwargs.get('month')
            day = kwargs.get('day')
            if month is None or day is None:
                raise ValueError("date検索にはmonthとdayパラメータが必要です")
            month_str = f"{month:02d}"
            day_str = f"{day:02d}"
            search_param = f"{month_str}月{day_str}日"
            
        elif search_type == 'search':
            # キーワード検索
            query = kwargs.get('query')
            if not query:
                raise ValueError("search検索にはqueryパラメータが必要です")
            search_param = query
            
        elif search_type == 'decade':
            # 年代別検索
            start_year = kwargs.get('start_year')
            end_year = kwargs.get('end_year')
            if start_year is None or end_year is None:
                raise ValueError("decade検索にはstart_yearとend_yearパラメータが必要です")
            search_param = f"{start_year}年代"
            
        else:
            raise ValueError(f"不明な検索タイプ: {search_type}")
        
        # URLエンコード
        import urllib.parse
        encoded_param = urllib.parse.quote(search_param)
        url = f"{base_url}?search={encoded_param}"
        
        logger.debug(f"URL生成: {search_type} -> {url}")
        return url


# スタンドアロン実行用の関数
async def test_data_service():
    """データサービスのテスト関数"""
    from config import Config
    
    print("=== データサービステスト ===")
    
    try:
        # 設定とデータベースの初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        
        async with TimelineDataService(config, database) as service:
            print("✅ サービス初期化成功")
            
            # 正常性チェック
            health = await service.health_check()
            print(f"✅ 正常性チェック: {health['status']}")
            
            # 今日のイベントメッセージ生成
            message = service.get_today_events_message()
            print(f"✅ 今日のメッセージ生成: {len(message)}文字")
            print(f"メッセージプレビュー:\n{message[:200]}...")
            
            # 特定日付のテスト（6月29日）
            test_message = service.get_date_events_message(6, 29)
            print(f"✅ 6月29日のメッセージ生成: {len(test_message)}文字")
            print(f"6月29日メッセージプレビュー:\n{test_message[:300]}...")
            
        print("✅ 全テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_data_service())
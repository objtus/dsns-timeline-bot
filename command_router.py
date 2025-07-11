"""
コマンド解析とハンドラールーティング管理

メンション内容の解析からハンドラー選択・実行までを一元管理
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from handlers import (
    TodayHandler, DateHandler, SearchHandler, 
    HelpHandler, StatusHandler, DecadeHandler, CategoryHandler
)
from constants import CommandTypes, StatusSubTypes, DecadeSubTypes, ErrorMessages
from exceptions import CommandParseError, HandlerError
from dsnstypes import CommandDict

logger = logging.getLogger(__name__)

class CommandRouter:
    """コマンド解析とハンドラールーティング管理"""
    
    def __init__(self, config, database, data_service, bot_client: Optional[Any] = None):
        """
        ルーター初期化
        
        Args:
            config: 設定オブジェクト
            database: データベースオブジェクト
            data_service: データサービスオブジェクト
            bot_client: ボットクライアント（Phase 3で使用）
        """
        self.config = config
        self.database = database
        self.data_service = data_service
        self.bot_client = bot_client
        
        # 全ハンドラーを初期化・管理
        self.handlers = {
            CommandTypes.TODAY: TodayHandler(config, database, data_service, bot_client),
            CommandTypes.DATE: DateHandler(config, database, data_service, bot_client),
            CommandTypes.SEARCH: SearchHandler(config, database, data_service, bot_client),
            CommandTypes.HELP: HelpHandler(config, database, data_service, bot_client),
            CommandTypes.STATUS: StatusHandler(config, database, data_service, bot_client),
            CommandTypes.DECADE: DecadeHandler(config, database, data_service, bot_client),
            'category': CategoryHandler(config, database, data_service, bot_client),
        }
        
        logger.info(f"CommandRouter初期化完了: {len(self.handlers)}個のハンドラー")
        
        # 統計情報
        self.command_count = 0
        self.error_count = 0
        self.last_command_time: Optional[datetime] = None
        
    def parse_command(self, content: str, bot_username: Optional[str] = None) -> Dict[str, Any]:
        """
        メンション内容からボットコマンドを解析
        
        main.pyの_parse_command()ロジックを移行・改良
        
        Args:
            content: メンション内容の文字列
            bot_username: ボットのユーザー名（除去用）
            
        Returns:
            Dict[str, Any]: コマンド情報を含む辞書
        """
        try:
            # ボット名の除去
            if bot_username:
                content = content.replace(f'@{bot_username}', '').strip()
            
            content_lower = content.lower()
            
            logger.debug(f"コマンド解析: '{content}' -> '{content_lower}'")
            
            # 年代コマンド（日付コマンドの前に配置）
            decade_command = self.parse_decade_command(content)
            if decade_command:
                logger.info(f"年代コマンド検出: {decade_command['sub_type']} - {decade_command['start_year']}-{decade_command['end_year']}")
                return decade_command
            
            # 特定日付 (MM月DD日、M月D日など) - 最優先でチェック
            date_match = re.search(r'(\d{1,2})月(\d{1,2})日', content)
            if date_match:
                month, day = int(date_match.group(1)), int(date_match.group(2))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    logger.info(f"日付コマンド検出: {month}月{day}日")
                    return {
                        'type': CommandTypes.DATE,
                        'month': month,
                        'day': day
                    }
            
            # ヘルプ
            if any(keyword in content_lower for keyword in ['help', 'ヘルプ', '使い方', 'つかいかた', 'コマンド']):
                logger.info("ヘルプコマンド検出")
                return {'type': CommandTypes.HELP}
            
            # ステータス（システム監視）- カテゴリコマンドの後にチェック
            if any(keyword in content_lower for keyword in ['status', 'ステータス', '状態', 'じょうたい']):
                # カテゴリコマンドの可能性を除外
                if not content_lower.startswith('カテゴリ'):
                    logger.info("ステータスコマンド検出")
                    # サブコマンドの解析
                    sub_command = None
                    if 'サーバー' in content or 'server' in content_lower:
                        sub_command = StatusSubTypes.SERVER
                    elif 'ボット' in content or 'bot' in content_lower:
                        sub_command = StatusSubTypes.BOT
                    elif '年表' in content or 'timeline' in content_lower:
                        sub_command = StatusSubTypes.TIMELINE
                    
                    return {
                        'type': CommandTypes.STATUS,
                        'sub_command': sub_command
                    }
            
            # 検索 キーワード カテゴリ ... パターン（カテゴリコマンドより優先）
            search_keywords = ['検索', 'けんさく', 'search', '探して', 'さがして']
            for keyword in search_keywords:
                if keyword in content_lower:
                    logger.debug(f"検索キーワード '{keyword}' を検出")
                    # カテゴリコマンドの可能性を除外
                    if content_lower.startswith('カテゴリ'):
                        logger.debug("カテゴリコマンドの可能性があるため検索をスキップ")
                        continue
                    # 「検索 キーワード カテゴリ ...」パターン
                    search_cat_pattern = r'(?:検索|けんさく|search|探して|さがして)\s*([^\s]+)\s*カテゴリ\s*(.+)'
                    match = re.search(search_cat_pattern, content)
                    logger.debug(f"検索カテゴリパターンマッチ: {match is not None}")
                    if match:
                        logger.debug("検索+カテゴリパターンにマッチ")
                        search_query = match.group(1).strip()
                        cat_expr = match.group(2).strip()
                        logger.debug(f"カテゴリ式: '{cat_expr}'")
                        logger.debug(f"'-' in cat_expr: {'-' in cat_expr}")
                        if '-' in cat_expr:
                            include_part, exclude_part = cat_expr.split('-', 1)
                            logger.debug(f"分割結果: 含める='{include_part}', 除外='{exclude_part}'")
                        else:
                            include_part, exclude_part = cat_expr, ''
                            logger.debug(f"分割なし: 含める='{include_part}', 除外='{exclude_part}'")
                        categories = [cat.strip() for cat in include_part.split('+') if cat.strip()]
                        # 除外カテゴリの複雑な解析（+で区切られた複数のカテゴリ）
                        exclude_categories = []
                        if exclude_part:
                            # 除外部分を+で分割して、各カテゴリをさらに-で分割
                            exclude_parts = exclude_part.split('+')
                            for part in exclude_parts:
                                if '-' in part:
                                    # さらに-で分割された場合（例: flame-incident）
                                    sub_parts = part.split('-')
                                    exclude_categories.extend([cat.strip() for cat in sub_parts if cat.strip()])
                                else:
                                    exclude_categories.append(part.strip())
                        logger.info(f"検索+カテゴリコマンド検出: '{search_query}', {categories}, 除外={exclude_categories}")
                        return {
                            'type': CommandTypes.SEARCH,
                            'query': search_query,
                            'categories': categories,
                            'exclude_categories': exclude_categories
                        }
                    else:
                        logger.debug("検索+カテゴリパターンにマッチせず、通常の検索を実行")
                    # 通常の検索（@記号を保持）
                    search_query = content.replace(keyword, '').strip()
                    # @記号を含む検索クエリを正しく処理
                    if search_query:
                        logger.info(f"検索コマンド検出: '{search_query}'")
                        return {
                            'type': CommandTypes.SEARCH,
                            'query': search_query
                        }
            
            # カテゴリコマンド（検索コマンドの後にチェック）
            category_command = self.parse_category_command(content)
            if category_command:
                logger.info(f"カテゴリコマンド検出: {category_command}")
                return category_command
            
            # 今日のイベント
            if any(keyword in content_lower for keyword in ['今日', 'きょう', 'today']):
                logger.info("今日コマンド検出")
                return {'type': CommandTypes.TODAY}
            
            # デフォルト（何も該当しない場合はヘルプ表示）
            logger.info("デフォルトコマンド: ヘルプ")
            return {'type': CommandTypes.HELP}
            
        except Exception as e:
            logger.error(f"コマンド解析エラー: {e}")
            # エラー時はデフォルトコマンドを返す
            raise CommandParseError(ErrorMessages.INVALID_COMMAND, content, "unknown")
    
    def parse_decade_command(self, content: str) -> Optional[Dict[str, Any]]:
        """
        年代別コマンドの解析
        
        Args:
            content: メンション内容の文字列
            
        Returns:
            年代別コマンド情報の辞書、該当しない場合はNone
        """
        try:
            content_lower = content.lower()
            
            # 年代文字列マッチング
            decade_match = None
            start_year = None
            end_year = None
            
            decade_strings = {                '1920年代': (1920, 1929),
                '30年代': (1930, 1939),
                '1930年代': (1930, 1939),
                '40年代': (1940, 1949),
                '1940年代': (1940, 1949),
                '50年代': (1950, 1959),
                '1950年代': (1950, 1959),
                '60年代': (1960, 1969),
                '1960年代': (1960, 1969),
                '70年代': (1970, 1979),
                '1970年代': (1970, 1979),
                '80年代': (1980, 1989),
                '1980年代': (1980, 1989),
                '90年代': (1990, 1999),
                '1990年代': (1990, 1999),
                'ゼロ年代': (2000, 2009),
                '零年代': (2000, 2009),
                '2000年代': (2000, 2009),
                '10年代': (2010, 2019),
                '2010年代': (2010, 2019),
                'テン年代': (2010, 2019),
                '2020年代': (2020, 2029),
            }
            
            for decade_str, (start, end) in decade_strings.items():
                if decade_str in content:
                    start_year = start
                    end_year = end
                    decade_match = True
                    break
            
            # パターン1: 2000年代
            if not decade_match:
                match = re.search(r'(\d{4})年代', content)
                if match:
                    start_year = int(match.group(1))
                    end_year = start_year + 9
                    decade_match = match
            
            # パターン2: 00年代
            if not decade_match:
                match = re.search(r'(\d{2})年代', content)
                if match:
                    decade_num = int(match.group(1))
                    start_year = 1900 + decade_num
                    end_year = start_year + 9
                    decade_match = match
            
            # パターン3: 2000年から2009年
            if not decade_match:
                match = re.search(r'(\d{4})年から(\d{4})年', content)
                if match:
                    start_year = int(match.group(1))
                    end_year = int(match.group(2))
                    decade_match = match
            
            if not decade_match:
                return None
            
            # サブコマンド判定
            sub_commands = {
                '統計': ['統計', 'とうけい', 'stats', 'statistics'],
                '代表': ['代表', 'だいひょう', '重要', 'じゅうよう', 'representative'],
                '概要': ['概要', 'がいよう', 'まとめ', 'summary', 'overview']
            }
            
            sub_command = '統計'  # デフォルト
            
            for cmd_type, keywords in sub_commands.items():
                if any(keyword in content for keyword in keywords):
                    sub_command = cmd_type
                    break
            
            # カテゴリ複合条件の解析
            categories = []
            exclude_categories = []
            
            # カテゴリプレフィックスパターン: カテゴリ dsns+tech-meme
            category_pattern = r'カテゴリ\s+([\w\-\+]+)'
            match = re.search(category_pattern, content)
            if match:
                cat_expr = match.group(1)
                if '-' in cat_expr:
                    include_part, exclude_part = cat_expr.split('-', 1)
                else:
                    include_part, exclude_part = cat_expr, ''
                categories = [cat.strip() for cat in include_part.split('+') if cat.strip()]
                # 除外カテゴリの複雑な解析（+で区切られた複数のカテゴリ）
                if exclude_part:
                    # 除外部分を+で分割して、各カテゴリをさらに-で分割
                    exclude_parts = exclude_part.split('+')
                    for part in exclude_parts:
                        if '-' in part:
                            # さらに-で分割された場合（例: flame-incident）
                            sub_parts = part.split('-')
                            exclude_categories.extend([cat.strip() for cat in sub_parts if cat.strip()])
                        else:
                            exclude_categories.append(part.strip())
                logger.info(f"年代別＋カテゴリ複合コマンド検出: 年代={start_year}-{end_year}, カテゴリ={categories}, 除外={exclude_categories}")
            
            return {
                'type': 'decade',
                'sub_type': sub_command,
                'start_year': start_year,
                'end_year': end_year,
                'decade_name': self._get_decade_name(start_year) if start_year is not None else "不明な年代",
                'categories': categories,
                'exclude_categories': exclude_categories
            }
            
        except Exception as e:
            logger.error(f"年代コマンド解析エラー: {e}")
            return None
    
    def _get_decade_name(self, start_year: int) -> str:
        """年代名を取得"""
        # 1990年代、2000年代などの形式で返す
        decade_start = (start_year // 10) * 10
        return f"{decade_start}年代"
    
    def parse_category_command(self, content: str) -> Optional[Dict[str, Any]]:
        """
        カテゴリコマンドの解析
        
        Args:
            content: メンション内容の文字列
            
        Returns:
            カテゴリコマンド情報の辞書、該当しない場合はNone
        """
        try:
            content_lower = content.lower()

            # カテゴリ統計コマンド
            if any(keyword in content for keyword in ['カテゴリ統計', 'カテゴリ 統計', 'category stats', 'category statistics']):
                logger.info("カテゴリ統計コマンド検出")
                return {
                    'type': 'category',
                    'sub_type': 'statistics',
                    'categories': [],
                    'exclude_categories': []
                }

            # カテゴリ分析コマンド
            # 例: カテゴリ分析 dsns+tech
            import re
            analysis_pattern = r'カテゴリ分析\s+([\w\-\+]+)'
            match = re.search(analysis_pattern, content)
            if match:
                cat_expr = match.group(1)
                if '-' in cat_expr:
                    include_part, exclude_part = cat_expr.split('-', 1)
                else:
                    include_part, exclude_part = cat_expr, ''
                categories = [cat.strip() for cat in include_part.split('+') if cat.strip()]
                # 除外カテゴリの複雑な解析（+で区切られた複数のカテゴリ）
                exclude_categories = []
                if exclude_part:
                    # 除外部分を+で分割して、各カテゴリをさらに-で分割
                    exclude_parts = exclude_part.split('+')
                    for part in exclude_parts:
                        if '-' in part:
                            # さらに-で分割された場合（例: flame-incident）
                            sub_parts = part.split('-')
                            exclude_categories.extend([cat.strip() for cat in sub_parts if cat.strip()])
                        else:
                            exclude_categories.append(part.strip())
                
                logger.info(f"カテゴリ分析コマンド検出: 含める={categories}, 除外={exclude_categories}")
                return {
                    'type': 'category',
                    'sub_type': 'analysis',
                    'categories': categories,
                    'exclude_categories': exclude_categories
                }

            # カテゴリ一覧コマンド
            if any(keyword in content for keyword in ['カテゴリ一覧', 'カテゴリ 一覧', 'category list', 'categories']):
                logger.info("カテゴリ一覧コマンド検出")
                return {
                    'type': 'category',
                    'sub_type': 'list',
                    'categories': [],
                    'exclude_categories': []
                }

            # カテゴリプレフィックスコマンド
            # 例: カテゴリ dsns+tech-meme+incident
            category_pattern = r'カテゴリ\s+([\w\-\+]+)'
            match = re.search(category_pattern, content)
            if match:
                cat_expr = match.group(1)
                if '-' in cat_expr:
                    include_part, exclude_part = cat_expr.split('-', 1)
                else:
                    include_part, exclude_part = cat_expr, ''
                categories = [cat.strip() for cat in include_part.split('+') if cat.strip()]
                # 除外カテゴリの複雑な解析（+で区切られた複数のカテゴリ）
                exclude_categories = []
                if exclude_part:
                    # 除外部分を+で分割して、各カテゴリをさらに-で分割
                    exclude_parts = exclude_part.split('+')
                    for part in exclude_parts:
                        if '-' in part:
                            # さらに-で分割された場合（例: flame-incident）
                            sub_parts = part.split('-')
                            exclude_categories.extend([cat.strip() for cat in sub_parts if cat.strip()])
                        else:
                            exclude_categories.append(part.strip())
                
                # 空のカテゴリリストの場合はヘルプにフォールバック
                if not categories and not exclude_categories:
                    return None
                
                logger.info(f"カテゴリフィルタコマンド検出: 含める={categories}, 除外={exclude_categories}")
                return {
                    'type': 'category',
                    'sub_type': 'filter',
                    'categories': categories,
                    'exclude_categories': exclude_categories
                }

            return None
        except Exception as e:
            logger.error(f"カテゴリコマンド解析エラー: {e}")
            return None
    
    async def route_message(self, note, bot_username: Optional[str] = None) -> str:
        """
        メッセージを適切なハンドラーにルーティングして処理実行
        
        Args:
            note: Misskeyのnoteオブジェクト
            bot_username: ボットのユーザー名
            
        Returns:
            str: 処理結果メッセージ
        """
        try:
            self.command_count += 1
            self.last_command_time = datetime.now()
            
            # コマンド解析
            content = getattr(note, 'text', '').strip()
            command = self.parse_command(content, bot_username)
            
            logger.info(f"ルーティング実行: {command['type']} (#{self.command_count})")
            
            # ハンドラー選択・実行
            command_type = command['type']
            
            if command_type in self.handlers:
                handler = self.handlers[command_type]
                result = await handler.handle(note, command)
                logger.info(f"ルーティング完了: {command_type}")
                return result
            else:
                logger.warning(f"不明なコマンドタイプ: {command_type}")
                # フォールバック: ヘルプ表示
                handler = self.handlers.get('help')
                if handler:
                    result = await handler.handle(note, {'type': 'help'})
                    return result
                else:
                    return "申し訳ございません。処理できませんでした。"
                    
        except Exception as e:
            logger.error(f"ルーティングエラー: {e}")
            self.error_count += 1
            
            # エラー時のフォールバック
            try:
                handler = self.handlers.get('help')
                if handler:
                    result = await handler.handle(note, {'type': 'help'})
                    return result
            except:
                pass
                
            return "申し訳ございません。処理中にエラーが発生しました。"
    
    def get_router_status(self) -> Dict[str, Any]:
        """
        ルーターの状態情報を取得
        
        Returns:
            状態情報の辞書
        """
        return {
            'router_type': 'command_router',
            'handlers_count': len(self.handlers),
            'available_handlers': list(self.handlers.keys()),
            'command_count': self.command_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.command_count, 1),
            'last_command_time': self.last_command_time.isoformat() if self.last_command_time else None,
        }
    
    def reset_statistics(self):
        """統計情報をリセット"""
        self.command_count = 0
        self.error_count = 0
        self.last_command_time = None
        logger.info("ルーター統計情報をリセットしました")


# テスト用関数
async def test_command_router():
    """CommandRouterのテスト"""
    from config import Config
    from database import TimelineDatabase
    from data_service import TimelineDataService
    
    print("=== CommandRouter テスト ===")
    
    try:
        # 設定とサービス初期化
        config = Config()
        database = TimelineDatabase(config.database_path)
        
        async with TimelineDataService(config, database) as data_service:
            router = CommandRouter(config, database, data_service)
            
            print("✅ ルーター初期化成功")
            
            # コマンド解析テスト
            test_commands = [
                '今日',
                '5月1日',
                '検索 Mastodon',
                'ヘルプ',
                'ステータス',
                'こんにちは'
            ]
            
            print("\n--- コマンド解析テスト ---")
            for cmd in test_commands:
                result = router.parse_command(cmd)
                print(f"'{cmd}' -> {result}")
            
            # Mock note for routing test
            class MockNote:
                class MockUser:
                    username = 'test_user'
                user = MockUser()
                def __init__(self, text):
                    self.text = text
                    self.id = 'test_id'
            
            print("\n--- ルーティングテスト ---")
            note = MockNote('今日')
            result = await router.route_message(note)
            print(f"ルーティング結果: {result[:100]}...")
            
            # ステータス確認
            status = router.get_router_status()
            print(f"\n--- ルーターステータス ---")
            print(f"コマンド処理数: {status['command_count']}")
            print(f"ハンドラー数: {status['handlers_count']}")
            
        print("✅ 全テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_command_router())
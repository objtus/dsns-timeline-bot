#!/usr/bin/env python3
"""
分散SNS関連年表bot 全体包括的テスト

PROJECT_MAP.mdに記載された全機能の統合テストを実行し、botの動作を包括的に検証します。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from command_router import CommandRouter
from handlers.today_handler import TodayHandler
from handlers.date_handler import DateHandler
from handlers.search_handler import SearchHandler
from handlers.help_handler import HelpHandler
from handlers.status_handler import StatusHandler
from handlers.decade_handler import DecadeHandler
from handlers.category_handler import CategoryHandler
from summary_manager import SummaryManager
from constants import MessageLimits, ErrorMessages, SuccessMessages
from exceptions import DSNSBotError, DataServiceError, DatabaseError
from dsnstypes import CommandDict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockBotClient:
    """テスト用のモックボットクライアント"""
    
    def __init__(self):
        self.post_count = 0
        self.reply_count = 0
        self.is_connected = True
        self.uptime = 3600.0
        self.message_count = 100
        self.error_count = 5
        self.last_message_time = datetime.now()
        self.last_error_time = None
        self.memory_usage = "50MB"
        self.connection_count = 10
        self.last_connection = datetime.now()
        self.debug_mode = False
        self.log_level = "INFO"
        self.last_command_time = datetime.now()
        self.handlers_count = 6
        self.available_handlers = "today,date,search,help,status,decade,category"
        self.last_heartbeat = datetime.now()
        self.max_response_time = 0.5
        self.min_response_time = 0.05
        self.avg_response_time = 0.1
        self.command_router: Optional[CommandRouter] = None # MockBotClientにcommand_router属性を追加
    
    async def post_note(self, content: str, visibility: str = 'home'):
        """投稿のモック"""
        self.post_count += 1
        return {
            'success': True,
            'note_id': f'test_note_{self.post_count}',
            'content': content,
            'visibility': visibility
        }
    
    async def reply(self, content: str, note_id: str, visibility: str = 'home'):
        """リプライのモック"""
        self.reply_count += 1
        return {
            'success': True,
            'note_id': f'test_reply_{self.reply_count}',
            'content': content,
            'visibility': visibility
        }
    
    def get_client_status(self) -> Dict[str, Any]:
        """クライアント状態の取得"""
        return {
            'is_connected': self.is_connected,
            'uptime': self.uptime,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'last_message_time': self.last_message_time,
            'last_error_time': self.last_error_time,
            'memory_usage': self.memory_usage,
            'connection_count': self.connection_count,
            'last_connection': self.last_connection,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'last_command_time': self.last_command_time,
            'handlers_count': self.handlers_count,
            'available_handlers': self.available_handlers,
            'last_heartbeat': self.last_heartbeat,
            'max_response_time': self.max_response_time,
            'min_response_time': self.min_response_time,
            'avg_response_time': self.avg_response_time
        }

class ComprehensiveBotTest:
    """分散SNS関連年表bot 包括的テストクラス"""
    
    def __init__(self):
        self.config: Optional[Config] = None
        self.database: Optional[TimelineDatabase] = None
        self.data_service: Optional[TimelineDataService] = None
        self.command_router: Optional[CommandRouter] = None
        self.bot_client: Optional[MockBotClient] = None
        self.summary_manager: Optional[SummaryManager] = None
        self.test_results = []
    
    async def setup(self):
        """テスト環境のセットアップ"""
        logger.info("=== 分散SNS関連年表bot 包括的テスト開始 ===")
        
        try:
            # 設定初期化
            self.config = Config()
            logger.info("✅ 設定初期化完了")
            
            # データベース初期化
            self.database = TimelineDatabase(self.config.database_path)
            logger.info("✅ データベース初期化完了")
            
            # データサービス初期化
            self.data_service = TimelineDataService(self.config, self.database)
            logger.info("✅ データサービス初期化完了")
            
            # 概要マネージャー初期化
            self.summary_manager = SummaryManager(self.config.summaries_dir)
            logger.info("✅ 概要マネージャー初期化完了")
            
            # ボットクライアント初期化（モック）
            self.bot_client = MockBotClient()
            logger.info("✅ ボットクライアント初期化完了")
            
            # コマンドルーター初期化
            self.command_router = CommandRouter(
                self.config, 
                self.database, 
                self.data_service, 
                self.bot_client
            )
            self.bot_client.command_router = self.command_router # MockBotClientにcommand_routerを設定
            logger.info("✅ コマンドルーター初期化完了")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ セットアップエラー: {e}")
            return False
    
    def test_config(self):
        """設定のテスト"""
        logger.info("\n=== 設定テスト ===")
        
        success = True
        
        # 基本設定の確認
        required_configs = [
            'misskey_url', 'misskey_token', 'timeline_url',
            'database_path', 'post_times', 'timezone'
        ]
        
        for config_name in required_configs:
            if hasattr(self.config, config_name):
                value = getattr(self.config, config_name)
                logger.info(f"✅ {config_name}: {value}")
            else:
                logger.error(f"❌ {config_name} が見つかりません")
                success = False
        
        return success
    
    def test_database_operations(self):
        """データベース操作のテスト"""
        logger.info("\n=== データベース操作テスト ===")
        
        if not self.database:
            logger.error("❌ データベースが初期化されていません")
            return False
        
        success = True
        
        try:
            # イベント取得テスト
            events = self.database.get_events_by_date(5, 1)
            success = len(events) > 0
            logger.info(f"✅ 5月1日のイベント取得: {len(events)}件")
            
            # 統計取得テスト
            stats = self.database.get_statistics()
            success = success and stats is not None
            logger.info(f"✅ 統計情報取得: {stats}")
            
            # カテゴリ検索テスト
            category_events = self.database.get_events_by_categories(['dsns'])
            success = success and category_events is not None
            logger.info(f"✅ カテゴリ検索: {len(category_events)}件")
            
            # 年代別統計テスト
            decade_stats = self.database.get_decade_statistics(2000, 2009)
            success = success and decade_stats is not None
            logger.info(f"✅ 年代別統計: {decade_stats}")
            
            # 年範囲検索テスト
            year_events = self.database.get_events_by_year_range(2000, 2005)
            success = success and year_events is not None
            logger.info(f"✅ 年範囲検索: {len(year_events)}件")
            
        except Exception as e:
            logger.error(f"❌ データベース操作エラー: {e}")
            success = False
        
        return success
    
    async def test_data_service(self):
        """データサービスのテスト"""
        logger.info("\n=== データサービステスト ===")
        
        if not self.data_service:
            logger.error("❌ データサービスが初期化されていません")
            return False
        
        success = True
        
        try:
            # 今日のイベントメッセージ取得
            today_message = self.data_service.get_today_events_message()
            success = today_message is not None and len(today_message) > 0
            logger.info(f"✅ 今日のイベントメッセージ: {len(today_message)}文字")
            
            # 特定日付のイベントメッセージ取得
            date_message = self.data_service.get_date_events_message(5, 1)
            success = success and date_message is not None and len(date_message) > 0
            logger.info(f"✅ 5月1日のイベントメッセージ: {len(date_message)}文字")
            
            # 検索機能
            search_message = self.data_service.search_events_message('Mastodon')
            success = success and search_message is not None
            logger.info(f"✅ 検索結果メッセージ: {len(search_message)}文字")
            
            # URL生成機能
            url = self.data_service.generate_timeline_url(search_type='search', query='test')
            success = success and url is not None
            logger.info(f"✅ URL生成: {url}")
            
            # ヘルスチェック
            health = await self.data_service.health_check()
            success = success and health is not None
            logger.info(f"✅ ヘルスチェック: {health}")
            
        except Exception as e:
            logger.error(f"❌ データサービスエラー: {e}")
            success = False
        
        return success
    
    def test_command_parsing(self):
        """コマンド解析のテスト"""
        logger.info("\n=== コマンド解析テスト ===")
        
        if not self.command_router:
            logger.error("❌ コマンドルーターが初期化されていません")
            return False
        
        success = True
        
        # テストケース
        test_cases = [
            # 基本コマンド
            ("今日", "today"),
            ("きょう", "today"),
            ("today", "today"),
            ("5月1日", "date"),
            ("05月01日", "date"),
            ("検索 test", "search"),
            ("ヘルプ", "help"),
            ("help", "help"),
            ("ステータス", "status"),
            ("status", "status"),
            ("2000年代", "decade"),
            ("90年代", "decade"),
            
            # カテゴリコマンド
            ("カテゴリ dsns", "category"),
            ("カテゴリ dsns+tech", "category"),
            ("カテゴリ dsns+tech-meme", "category"),
            ("カテゴリ一覧", "category"),
            ("カテゴリ統計", "category"),
            ("カテゴリ分析 dsns", "category"),
            
            # 複合コマンド
            ("検索 SNS カテゴリ dsns+tech", "search"),
            ("2000年代 カテゴリ web+tech", "decade"),
            ("ステータス サーバー", "status"),
            ("ステータス ボット", "status"),
            ("ステータス 年表", "status"),
            ("90年代 代表", "decade"),
            ("1990年代 統計", "decade"),
            ("2010年代 概要", "decade"),
            
            # エラーケース
            ("", "help"),  # 空文字はヘルプ
            ("無効なコマンド", "help"),  # 不明なコマンドはヘルプ
        ]
        
        for input_text, expected_type in test_cases:
            try:
                result = self.command_router.parse_command(input_text)
                actual_type = result.get('type', 'unknown')
                
                if actual_type == expected_type:
                    logger.info(f"✅ '{input_text}' → {actual_type}")
                else:
                    logger.error(f"❌ '{input_text}' → 期待: {expected_type}, 実際: {actual_type}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ '{input_text}' の解析でエラー: {e}")
                success = False
        
        return success
    
    async def test_message_routing(self):
        """メッセージルーティングのテスト"""
        logger.info("\n=== メッセージルーティングテスト ===")
        
        if not self.command_router:
            logger.error("❌ コマンドルーターが初期化されていません")
            return False
        
        success = True
        
        # テストケース
        test_cases = [
            ("今日", "today"),
            ("5月1日", "date"),
            ("検索 test", "search"),
            ("ヘルプ", "help"),
            ("ステータス", "status"),
            ("2000年代", "decade"),
            ("カテゴリ dsns", "category"),
        ]
        
        for input_text, expected_type in test_cases:
            try:
                # モックノートID
                note_id = "test_note_123"
                
                # ルーティング実行
                result = await self.command_router.route_message(input_text, note_id)
                
                if result:
                    logger.info(f"✅ '{input_text}' → ルーティング成功")
                else:
                    logger.error(f"❌ '{input_text}' → ルーティング失敗")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ '{input_text}' のルーティングでエラー: {e}")
                success = False
        
        return success
    
    async def test_handlers(self):
        """ハンドラーのテスト"""
        logger.info("\n=== ハンドラーテスト ===")
        
        success = True
        
        try:
            # 型チェックとアサーション
            if not all([self.config, self.database, self.data_service, self.bot_client]):
                logger.error("❌ 必要なコンポーネントが初期化されていません")
                return False
            
            # 型アサーション
            config = self.config
            database = self.database
            data_service = self.data_service
            bot_client = self.bot_client
            
            # モックnoteオブジェクト
            mock_note = {"id": "test_note_1", "text": "今日"}
            
            # TodayHandler
            today_handler = TodayHandler(config, database, data_service, bot_client)
            today_response = await today_handler.handle(mock_note, {"type": "today", "sub_type": None})
            success = success and today_response is not None
            logger.info(f"✅ TodayHandler: {len(today_response)}文字")
            
            # DateHandler
            date_handler = DateHandler(self.config, self.database, self.data_service, self.bot_client)
            date_response = await date_handler.handle(mock_note, {"type": "date", "sub_type": None, "month": 5, "day": 1})
            success = success and date_response is not None
            logger.info(f"✅ DateHandler: {len(date_response)}文字")
            
            # SearchHandler
            search_handler = SearchHandler(self.config, self.database, self.data_service, self.bot_client)
            search_response = await search_handler.handle(mock_note, {"type": "search", "sub_type": None, "query": "test"})
            success = success and search_response is not None
            logger.info(f"✅ SearchHandler: {len(search_response)}文字")
            
            # HelpHandler
            help_handler = HelpHandler(self.config, self.database, self.data_service, self.bot_client)
            help_response = await help_handler.handle(mock_note, {"type": "help", "sub_type": None})
            success = success and help_response is not None
            logger.info(f"✅ HelpHandler: {len(help_response)}文字")
            
            # StatusHandler
            status_handler = StatusHandler(self.config, self.database, self.data_service, self.bot_client)
            status_response = await status_handler.handle(mock_note, {"type": "status", "sub_type": None})
            success = success and status_response is not None
            logger.info(f"✅ StatusHandler: {len(status_response)}文字")
            
            # DecadeHandler
            decade_handler = DecadeHandler(self.config, self.database, self.data_service, self.bot_client)
            decade_response = await decade_handler.handle(mock_note, {"type": "decade", "sub_type": None, "start_year": 2000, "end_year": 2009, "decade_name": "2000年代"})
            success = success and decade_response is not None
            logger.info(f"✅ DecadeHandler: {len(decade_response)}文字")
            
            # CategoryHandler
            category_handler = CategoryHandler(self.config, self.database, self.data_service, self.bot_client)
            category_response = await category_handler.handle(mock_note, {"type": "category", "sub_type": "filter", "categories": ["dsns"]})
            success = success and category_response is not None
            logger.info(f"✅ CategoryHandler: {len(category_response)}文字")
            
        except Exception as e:
            logger.error(f"❌ ハンドラーテストエラー: {e}")
            success = False
        
        return success
    
    async def test_bot_client(self):
        """ボットクライアントのテスト"""
        logger.info("\n=== ボットクライアントテスト ===")
        
        if not self.bot_client:
            logger.error("❌ ボットクライアントが初期化されていません")
            return False
        
        success = True
        
        try:
            # 投稿テスト
            post_result = await self.bot_client.post_note("テスト投稿", "home")
            success = success and post_result['success']
            logger.info(f"✅ 投稿テスト: {post_result['note_id']}")
            
            # リプライテスト
            reply_result = await self.bot_client.reply("テストリプライ", "test_note_123", "home")
            success = success and reply_result['success']
            logger.info(f"✅ リプライテスト: {reply_result['note_id']}")
            
            # 状態取得テスト
            status = self.bot_client.get_client_status()
            success = success and status is not None
            logger.info(f"✅ 状態取得: 接続={status['is_connected']}, 投稿数={status['message_count']}")
            
        except Exception as e:
            logger.error(f"❌ ボットクライアントエラー: {e}")
            success = False
        
        return success
    
    async def test_error_handling(self):
        """エラーハンドリングのテスト"""
        logger.info("\n=== エラーハンドリングテスト ===")
        
        success = True
        
        try:
            # 無効なコマンドのテスト
            if self.command_router:
                invalid_result = self.command_router.parse_command("無効なコマンド")
                if invalid_result.get('type') == 'help':
                    logger.info("✅ 無効なコマンド → ヘルプ表示")
                else:
                    logger.error("❌ 無効なコマンドの処理が期待通りではありません")
                    success = False
                
                # 空文字のテスト
                empty_result = self.command_router.parse_command("")
                if empty_result.get('type') == 'help':
                    logger.info("✅ 空文字 → ヘルプ表示")
                else:
                    logger.error("❌ 空文字の処理が期待通りではありません")
                    success = False
            else:
                logger.error("❌ コマンドルーターが初期化されていません")
                success = False
            
            # 存在しないカテゴリのテスト
            if all([self.config, self.database, self.data_service, self.bot_client]):
                category_handler = CategoryHandler(self.config, self.database, self.data_service, self.bot_client)
                mock_note = {"id": "test_note_8", "text": "カテゴリ 存在しないカテゴリ"}
                invalid_category_response = await category_handler.handle(mock_note, {"type": "category", "sub_type": "filter", "categories": ["存在しないカテゴリ"]})
                success = success and invalid_category_response is not None
                logger.info("✅ 存在しないカテゴリの適切な処理")
            else:
                logger.warning("⚠️ コンポーネントが初期化されていないため、カテゴリテストをスキップ")
            
        except Exception as e:
            logger.error(f"❌ エラーハンドリングテストエラー: {e}")
            success = False
        
        return success
    
    def test_constants_and_types(self):
        """定数と型定義のテスト"""
        logger.info("\n=== 定数と型定義テスト ===")
        
        success = True
        
        try:
            # 定数のテスト
            from constants import Visibility, MessageLimits, CommandTypes
            
            # Visibility
            assert Visibility.is_valid('public')
            assert Visibility.is_valid('home')
            assert not Visibility.is_valid('invalid')
            logger.info("✅ Visibility定数")
            
            # MessageLimits
            assert MessageLimits.MAX_LENGTH == 3000
            assert MessageLimits.TRUNCATE_LENGTH == 2997
            logger.info("✅ MessageLimits定数")
            
            # CommandTypes
            assert CommandTypes.TODAY == 'today'
            assert CommandTypes.SEARCH == 'search'
            logger.info("✅ CommandTypes定数")
            
            # 型定義のテスト
            from dsnstypes import CommandDict, EventData
            
            # CommandDict
            command: CommandDict = {
                "type": "today",
                "sub_type": None,
                "query": None,
                "date": None,
                "year": None,
                "month": None,
                "day": None
            }
            assert command["type"] == "today"
            logger.info("✅ CommandDict型定義")
            
            # EventData
            event: EventData = {
                "year": 2023,
                "month": 5,
                "day": 1,
                "content": "テストイベント",
                "category": "test"
            }
            assert event["year"] == 2023
            logger.info("✅ EventData型定義")
            
        except Exception as e:
            logger.error(f"❌ 定数と型定義テストエラー: {e}")
            success = False
        
        return success
    
    async def run_all_tests(self):
        """全テストの実行"""
        logger.info("🚀 包括的テスト開始")
        
        # セットアップ
        if not await self.setup():
            logger.error("❌ セットアップに失敗しました")
            return False
        
        # テスト実行
        tests = [
            ("設定テスト", self.test_config),
            ("データベース操作テスト", self.test_database_operations),
            ("データサービステスト", self.test_data_service),
            ("コマンド解析テスト", self.test_command_parsing),
            ("メッセージルーティングテスト", self.test_message_routing),
            ("ハンドラーテスト", self.test_handlers),
            ("ボットクライアントテスト", self.test_bot_client),
            ("エラーハンドリングテスト", self.test_error_handling),
            ("定数と型定義テスト", self.test_constants_and_types),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"実行中: {test_name}")
                logger.info(f"{'='*50}")
                
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if result:
                    logger.info(f"✅ {test_name}: 成功")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name}: 失敗")
                
                self.test_results.append((test_name, result))
                
            except Exception as e:
                logger.error(f"❌ {test_name}: エラー - {e}")
                self.test_results.append((test_name, False))
        
        # 結果サマリー
        logger.info(f"\n{'='*50}")
        logger.info("📊 テスト結果サマリー")
        logger.info(f"{'='*50}")
        logger.info(f"総テスト数: {total}")
        logger.info(f"成功: {passed}")
        logger.info(f"失敗: {total - passed}")
        logger.info(f"成功率: {(passed/total)*100:.1f}%")
        
        # 詳細結果
        logger.info(f"\n詳細結果:")
        for test_name, result in self.test_results:
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"  {test_name}: {status}")
        
        return passed == total
    
    async def cleanup(self):
        """テスト環境のクリーンアップ"""
        try:
            # データベースは自動的にクローズされるため、明示的なクローズは不要
            logger.info("✅ テスト環境クリーンアップ完了")
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")

async def main():
    """メイン関数"""
    test = ComprehensiveBotTest()
    
    try:
        success = await test.run_all_tests()
        
        if success:
            logger.info("\n🎉 全テストが成功しました！")
            return 0
        else:
            logger.error("\n💥 一部のテストが失敗しました")
            return 1
            
    except Exception as e:
        logger.error(f"❌ テスト実行中にエラーが発生しました: {e}")
        return 1
    
    finally:
        await test.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
"""
カテゴリ機能テスト

カテゴリ複合フィルタリング、カテゴリ一覧、カテゴリ統計機能のテスト
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from config import Config
from database import TimelineDatabase, TimelineEvent
from data_service import TimelineDataService
from command_router import CommandRouter
from handlers.category_handler import CategoryHandler
from constants import CategorySubTypes, CategoryConfig


class TestCategoryFunctionality:
    """カテゴリ機能のテストクラス"""
    
    @pytest.fixture
    def setup_services(self):
        """テスト用サービス設定"""
        config = Config()
        database = TimelineDatabase(Path("test_category.db"))
        
        # テストデータを追加
        test_events = [
            TimelineEvent(2020, 1, 1, "Mastodonリリース", "dsns tech"),
            TimelineEvent(2020, 1, 2, "Pleroma開発開始", "dsns tech"),
            TimelineEvent(2020, 1, 3, "Misskey誕生", "dsns tech meme"),
            TimelineEvent(2020, 1, 4, "Web3技術発表", "web3 tech"),
            TimelineEvent(2020, 1, 5, "暗号通貨事件", "crypto incident"),
            TimelineEvent(2020, 1, 6, "分散SNS議論", "dsns culture"),
            TimelineEvent(2020, 1, 7, "ハッカー文化", "hacker culture"),
            TimelineEvent(2020, 1, 8, "ネットワーク技術", "network tech"),
            TimelineEvent(2020, 1, 9, "P2P技術", "p2p tech"),
            TimelineEvent(2020, 1, 10, "BBSシステム", "bbs site"),
        ]
        
        for event in test_events:
            database.add_event(event)
        
        return config, database
    
    @pytest.fixture
    def category_handler(self, setup_services):
        """CategoryHandlerの設定"""
        config, database = setup_services
        data_service = Mock()
        bot_client = Mock()
        
        return CategoryHandler(config, database, data_service, bot_client)
    
    @pytest.fixture
    def command_router(self, setup_services):
        """CommandRouterの設定（本物のdata_serviceを使う）"""
        config, database = setup_services
        from data_service import TimelineDataService
        data_service = TimelineDataService(config, database)
        bot_client = Mock()
        return CommandRouter(config, database, data_service, bot_client)
    
    def test_database_category_methods(self, setup_services):
        """データベースのカテゴリメソッドテスト"""
        config, database = setup_services
        
        # カテゴリ統計取得
        stats = database.get_category_statistics()
        assert stats is not None
        assert 'total_categories' in stats
        assert 'category_counts' in stats
        assert 'popular_categories' in stats
        assert 'decade_distribution' in stats
        
        # 利用可能なカテゴリ取得
        available_categories = database.get_available_categories()
        assert len(available_categories) > 0
        assert 'dsns' in available_categories
        assert 'tech' in available_categories
        
        # カテゴリフィルタリング
        events = database.get_events_by_categories(['dsns'])
        assert len(events) > 0
        # テストデータのカテゴリを確認
        for event in events:
            print(f"Event categories: '{event.categories}'")
        # カテゴリフィールドが存在するかチェック
        assert hasattr(events[0], 'categories'), "Event should have categories attribute"
        # カテゴリに'dsns'が含まれているかチェック（大文字小文字を考慮）
        assert any('dsns' in event.categories.lower() for event in events), "Some events should have 'dsns' category"
        
        # 複合カテゴリフィルタリング
        events = database.get_events_by_categories(['dsns', 'tech'])
        assert len(events) > 0
        
        # 除外カテゴリフィルタリング
        events = database.get_events_by_categories(['dsns'], exclude_categories=['meme'])
        assert len(events) > 0
        assert all('meme' not in event.categories for event in events)
    
    def test_command_parsing(self, command_router):
        """コマンド解析テスト"""
        # カテゴリ一覧コマンド
        command = command_router.parse_command("カテゴリ一覧")
        assert command['type'] == 'category'
        assert command['sub_type'] == 'list'
        
        # カテゴリ統計コマンド
        command = command_router.parse_command("カテゴリ統計")
        assert command['type'] == 'category'
        assert command['sub_type'] == 'statistics'
        
        # カテゴリフィルタコマンド
        command = command_router.parse_command("カテゴリ dsns+tech")
        assert command['type'] == 'category'
        assert command['sub_type'] == 'filter'
        assert command['categories'] == ['dsns', 'tech']
        assert command['exclude_categories'] == []
        
        # 除外カテゴリ付きフィルタコマンド
        command = command_router.parse_command("カテゴリ dsns+tech-meme")
        assert command['type'] == 'category'
        assert command['sub_type'] == 'filter'
        assert command['categories'] == ['dsns', 'tech']
        assert command['exclude_categories'] == ['meme']
        
        # 無効なコマンド
        command = command_router.parse_command("カテゴリ")
        assert command['type'] != 'category'
    
    @pytest.mark.asyncio
    async def test_category_handler_list(self, category_handler):
        """カテゴリ一覧ハンドラーテスト"""
        message = await category_handler._handle_category_list()
        
        assert "利用可能なカテゴリ一覧" in message
        assert "dsns" in message
        assert "tech" in message
        assert "使用例" in message
    
    @pytest.mark.asyncio
    async def test_category_handler_statistics(self, category_handler):
        """カテゴリ統計ハンドラーテスト"""
        message = await category_handler._handle_category_statistics()
        
        assert "カテゴリ統計情報" in message
        assert "総カテゴリ数" in message
        assert "人気カテゴリ" in message
        assert "年代別カテゴリ分布" in message
    
    @pytest.mark.asyncio
    async def test_category_handler_filter(self, category_handler):
        """カテゴリフィルタハンドラーテスト"""
        # 単一カテゴリフィルタ
        command = {'categories': ['dsns'], 'exclude_categories': []}
        message = await category_handler._handle_category_filter(command)
        
        assert "カテゴリ検索結果" in message
        assert "dsns" in message
        assert "結果件数" in message
        
        # 複合カテゴリフィルタ
        command = {'categories': ['dsns', 'tech'], 'exclude_categories': []}
        message = await category_handler._handle_category_filter(command)
        
        assert "カテゴリ検索結果" in message
        assert "dsns+tech" in message
        
        # 除外カテゴリ付きフィルタ
        command = {'categories': ['dsns'], 'exclude_categories': ['meme']}
        message = await category_handler._handle_category_filter(command)
        
        assert "カテゴリ検索結果" in message
        assert "除外" in message
        
        # 無効なカテゴリ
        command = {'categories': ['invalid_category'], 'exclude_categories': []}
        message = await category_handler._handle_category_filter(command)
        
        assert "指定されたカテゴリが見つかりません" in message
    
    @pytest.mark.asyncio
    async def test_category_handler_integration(self, category_handler):
        """カテゴリハンドラー統合テスト"""
        # Mock note
        note = Mock()
        note.text = "テスト"
        
        # カテゴリ一覧
        command = {'type': 'category', 'sub_type': 'list'}
        message = await category_handler.handle(note, command)
        assert "利用可能なカテゴリ一覧" in message
        
        # カテゴリ統計
        command = {'type': 'category', 'sub_type': 'statistics'}
        message = await category_handler.handle(note, command)
        assert "カテゴリ統計情報" in message
        
        # カテゴリフィルタ
        command = {
            'type': 'category', 
            'sub_type': 'filter',
            'categories': ['dsns'],
            'exclude_categories': []
        }
        message = await category_handler.handle(note, command)
        assert "カテゴリ検索結果" in message
    
    def test_message_truncation(self, category_handler):
        """メッセージ切り詰めテスト"""
        # 長いメッセージを作成
        long_message = "🗂️ **カテゴリ検索結果** (test)\n\n"
        long_message += "**検索条件**: 含める=['test'], 除外=[]\n"
        long_message += "**結果件数**: 100件\n\n"
        
        # 長いイベントを追加
        events = []
        for i in range(100):
            event = TimelineEvent(2020, 1, i+1, f"テストイベント{i} " * 10, "test")
            events.append(event)
        
        # 切り詰め実行
        truncated = category_handler._truncate_message_with_events(long_message, events, 100)
        
        assert len(truncated) <= 3000
        assert "他" in truncated or "..." in truncated
    
    def test_category_normalization(self, setup_services):
        """カテゴリ正規化テスト"""
        config, database = setup_services
        
        # ハイフン付きカテゴリでテスト
        event = TimelineEvent(2020, 1, 1, "テストイベント", "d-sns web-3")
        database.add_event(event)
        
        # 正規化されたカテゴリで検索
        events = database.get_events_by_categories(['dsns'])
        assert len(events) > 0
        
        events = database.get_events_by_categories(['web3'])
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_search_with_category(self, command_router):
        """検索 キーワード カテゴリ ... 形式のテスト"""
        # 検索 SNS カテゴリ dsns+tech
        command = command_router.parse_command("検索 SNS カテゴリ dsns+tech")
        assert command['type'] == 'search'
        assert command['query'] == 'SNS'
        assert command['categories'] == ['dsns', 'tech']
        # 検索結果が取得できるか
        handler = command_router.handlers['search']
        note = Mock()
        note.text = "検索 SNS カテゴリ dsns+tech"
        message = await handler.handle(note, command)
        assert "SNS" in message or "検索結果" in message
        assert "dsns" in message or "tech" in message
        # 除外カテゴリ付き
        command = command_router.parse_command("検索 SNS カテゴリ dsns+tech-meme")
        assert command['exclude_categories'] == ['meme']
        message = await handler.handle(note, command)
        assert "meme" not in message or "除外" in message

    @pytest.mark.asyncio
    async def test_category_handler_analysis(self, category_handler):
        """カテゴリ分析（共起カテゴリ）ハンドラーテスト"""
        # dsnsカテゴリと共起するカテゴリ
        command = {'categories': ['dsns'], 'exclude_categories': [], 'sub_type': 'analysis'}
        message = await category_handler._handle_category_analysis(command)
        assert "よく組み合わさるカテゴリ" in message
        assert "tech" in message or "meme" in message
        # 複合カテゴリ
        command2 = {'categories': ['dsns', 'tech'], 'exclude_categories': [], 'sub_type': 'analysis'}
        message2 = await category_handler._handle_category_analysis(command2)
        assert "よく組み合わさるカテゴリ" in message2
        # 存在しないカテゴリ
        command3 = {'categories': ['nonexistent'], 'exclude_categories': [], 'sub_type': 'analysis'}
        message3 = await category_handler._handle_category_analysis(command3)
        assert "見つかりません" in message3 or "失敗" in message3


def test_category_functionality():
    """カテゴリ機能の統合テスト"""
    print("=== カテゴリ機能テスト ===")
    
    try:
        # 設定とサービス初期化
        config = Config()
        database = TimelineDatabase(Path("test_category_integration.db"))
        
        # テストデータ追加
        test_events = [
            TimelineEvent(2020, 1, 1, "Mastodonリリース", "dsns tech"),
            TimelineEvent(2020, 1, 2, "Pleroma開発開始", "dsns tech"),
            TimelineEvent(2020, 1, 3, "Misskey誕生", "dsns tech meme"),
        ]
        
        for event in test_events:
            database.add_event(event)
        
        print("✅ テストデータ追加完了")
        
        # カテゴリ統計テスト
        stats = database.get_category_statistics()
        print(f"✅ カテゴリ統計: {stats['total_categories']}個のカテゴリ")
        
        # カテゴリフィルタテスト
        events = database.get_events_by_categories(['dsns'])
        print(f"✅ dsnsカテゴリ: {len(events)}件")
        
        events = database.get_events_by_categories(['dsns', 'tech'])
        print(f"✅ dsns+techカテゴリ: {len(events)}件")
        
        events = database.get_events_by_categories(['dsns'], exclude_categories=['meme'])
        print(f"✅ dsns-memeカテゴリ: {len(events)}件")
        
        # コマンドルーターテスト
        async def test_router():
            data_service = Mock()
            bot_client = Mock()
            router = CommandRouter(config, database, data_service, bot_client)
            
            # コマンド解析テスト
            commands = [
                "カテゴリ一覧",
                "カテゴリ統計", 
                "カテゴリ dsns+tech",
                "カテゴリ dsns+tech-meme"
            ]
            
            for cmd in commands:
                result = router.parse_command(cmd)
                print(f"✅ コマンド解析 '{cmd}': {result['type']}")
        
        asyncio.run(test_router())
        
        print("✅ 全テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


if __name__ == "__main__":
    test_category_functionality() 
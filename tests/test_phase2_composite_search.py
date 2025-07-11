"""
フェーズ2: 複合カテゴリ検索機能のテスト
"""

import pytest
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from command_router import CommandRouter
from config import Config
from database import TimelineDatabase
from data_service import TimelineDataService
from handlers.search_handler import SearchHandler
from handlers.category_handler import CategoryHandler
from dsnstypes import CommandDict

# ログ設定
logging.basicConfig(level=logging.INFO)

class TestPhase2CompositeSearch:
    """フェーズ2: 複合カテゴリ検索機能のテストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テストセットアップ"""
        self.config = Config()
        self.database = TimelineDatabase(Path('data/timeline.db'))
        self.data_service = TimelineDataService(self.config, self.database)
        self.router = CommandRouter(self.config, self.database, self.data_service, None)
        self.search_handler = SearchHandler(self.config, self.database, self.data_service, None)
        self.category_handler = CategoryHandler(self.config, self.database, self.data_service, None)
    
    def test_command_parsing_basic_categories(self):
        """基本的なカテゴリコマンドのパーステスト"""
        # 単一カテゴリ
        cmd = self.router.parse_command('カテゴリ d')
        assert cmd['type'] == 'category'
        assert cmd['sub_type'] == 'filter'
        assert cmd['categories'] == ['d']
        assert cmd['exclude_categories'] == []
        
        # 複数カテゴリ（AND条件）
        cmd = self.router.parse_command('カテゴリ d+sns')
        assert cmd['type'] == 'category'
        assert cmd['sub_type'] == 'filter'
        assert cmd['categories'] == ['d', 'sns']
        assert cmd['exclude_categories'] == []
        
        # 除外カテゴリ
        cmd = self.router.parse_command('カテゴリ d+sns-meme')
        assert cmd['type'] == 'category'
        assert cmd['sub_type'] == 'filter'
        assert cmd['categories'] == ['d', 'sns']
        assert cmd['exclude_categories'] == ['meme']
    
    def test_command_parsing_composite_search(self):
        """複合検索コマンドのパーステスト"""
        # キーワード+カテゴリ
        cmd = self.router.parse_command('検索 SNS カテゴリ d+sns')
        assert cmd['type'] == 'search'
        assert cmd['query'] == 'SNS'
        assert cmd['categories'] == ['d', 'sns']
        assert cmd['exclude_categories'] == []
        
        # キーワード+カテゴリ+除外
        cmd = self.router.parse_command('検索 SNS カテゴリ d+sns-meme')
        assert cmd['type'] == 'search'
        assert cmd['query'] == 'SNS'
        assert cmd['categories'] == ['d', 'sns']
        assert cmd['exclude_categories'] == ['meme']
        
        # 日本語キーワード
        cmd = self.router.parse_command('検索 分散 カテゴリ d+tech')
        assert cmd['type'] == 'search'
        assert cmd['query'] == '分散'
        assert cmd['categories'] == ['d', 'tech']
    
    def test_database_category_search(self):
        """データベースのカテゴリ検索テスト"""
        # 単一カテゴリ
        events = self.database.get_events_by_categories(['d'], limit=10)
        print('\n[dカテゴリのみ] 実際のevent.categories:')
        for event in events:
            print(f'  {event.categories}')
        assert len(events) > 0
        for event in events:
            # printで値を確認し、次のアクションを決める
            assert 'd' in event.categories.split()
        
        # 複数カテゴリ（AND条件）
        events = self.database.get_events_by_categories(['d', 'sns'], limit=5)
        assert len(events) > 0
        for event in events:
            categories = event.categories.split()
            assert 'd' in categories
            assert 'sns' in categories
        
        # 存在しない組み合わせ
        events = self.database.get_events_by_categories(['d', 'tech'], limit=5)
        assert len(events) == 0  # d+techの組み合わせは存在しない
    
    def test_database_exclude_categories(self):
        """データベースの除外カテゴリテスト"""
        # 除外なし
        events_all = self.database.get_events_by_categories(['d'], limit=10)
        
        # memeを除外
        events_filtered = self.database.get_events_by_categories(['d'], exclude_categories=['meme'], limit=10)
        
        # 除外後の方が少ないか同じ
        assert len(events_filtered) <= len(events_all)
        
        # 除外されたイベントにmemeカテゴリがないことを確認
        for event in events_filtered:
            categories = event.categories.split()
            assert 'meme' not in categories
    
    @pytest.mark.asyncio
    async def test_category_handler_basic(self):
        """CategoryHandlerの基本機能テスト"""
        cmd: CommandDict = {
            'type': 'category',
            'sub_type': 'filter',
            'categories': ['d', 'sns'],
            'exclude_categories': []
        }
        
        result = await self.category_handler.handle(None, cmd)
        assert result is not None
        assert len(result) > 0
        assert 'カテゴリ検索結果' in result
        assert 'd+sns' in result
    
    @pytest.mark.asyncio
    async def test_category_handler_with_exclude(self):
        """CategoryHandlerの除外機能テスト"""
        cmd: CommandDict = {
            'type': 'category',
            'sub_type': 'filter',
            'categories': ['d', 'sns'],
            'exclude_categories': ['meme']
        }
        
        result = await self.category_handler.handle(None, cmd)
        assert result is not None
        assert len(result) > 0
        assert 'd+sns-meme' in result
    
    @pytest.mark.asyncio
    async def test_search_handler_composite(self):
        """SearchHandlerの複合検索テスト"""
        cmd: CommandDict = {
            'type': 'search',
            'query': 'SNS',
            'categories': ['d', 'sns'],
            'exclude_categories': ['meme']
        }
        
        result = await self.search_handler.handle(None, cmd)
        print('\n[SearchHandler複合検索結果]')
        print(result[:500])
        assert result is not None
        assert len(result) > 0
        assert 'SNS' in result
        assert "カテゴリ['d', 'sns']" in result
        assert '**SNS**' in result  # キーワード強調
    
    @pytest.mark.asyncio
    async def test_search_handler_case_insensitive(self):
        """SearchHandlerの大文字小文字区別なしテスト"""
        cmd = {
            'type': 'search',
            'query': 'sns',  # 小文字
            'categories': ['d', 'sns'],
            'exclude_categories': []
        }
        
        result = await self.search_handler.handle(None, cmd)
        assert result is not None
        assert len(result) > 0
        assert '**sns**' in result  # 小文字でも強調
    
    def test_data_service_search_message(self):
        """DataServiceの検索メッセージ生成テスト"""
        # 複合カテゴリ検索
        message = self.data_service.search_events_message(
            'SNS', 
            categories=['d', 'sns'], 
            exclude_categories=['meme']
        )
        assert message is not None
        assert len(message) > 0
        assert 'SNS' in message
        assert 'd+sns' in message
        
        # 結果が見つからない場合
        message = self.data_service.search_events_message(
            '存在しないキーワード', 
            categories=['d', 'tech']
        )
        assert '見つかりませんでした' in message
    
    def test_category_normalization(self):
        """カテゴリ正規化テスト"""
        # ハイフン除去
        events = self.database.get_events_by_categories(['d-sns'], limit=5)
        # d-snsはdとして正規化される
        assert len(events) > 0
        
        # 大文字小文字
        events_upper = self.database.get_events_by_categories(['D'], limit=5)
        events_lower = self.database.get_events_by_categories(['d'], limit=5)
        assert len(events_upper) == len(events_lower)
    
    def test_complex_search_scenarios(self):
        """複雑な検索シナリオテスト"""
        # シナリオ1: 複数カテゴリ+除外+キーワード
        cmd = self.router.parse_command('検索 分散 カテゴリ d+sns+tech-meme-incident')
        assert cmd['type'] == 'search'
        assert cmd['query'] == '分散'
        assert cmd['categories'] == ['d', 'sns', 'tech']
        assert cmd['exclude_categories'] == ['meme', 'incident']
        
        # シナリオ2: 年代+カテゴリ（将来のフェーズ3用）
        cmd = self.router.parse_command('2000年代 カテゴリ d+sns')
        assert cmd['type'] == 'decade'
        # 年代別機能は別途テスト
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # 存在しないカテゴリ
        print(f'\n[デバッグ] 存在しないカテゴリ検索: {["存在しないカテゴリ"]}')
        events = self.database.get_events_by_categories(['存在しないカテゴリ'], limit=5)
        print(f'[デバッグ] 検索結果: {len(events)}件')
        if len(events) > 0:
            print(f'[デバッグ] 最初の3件のカテゴリ:')
            for event in events[:3]:
                print(f'  {event.categories}')
        assert len(events) == 0
        
        # 空のカテゴリ
        print(f'\n[デバッグ] 空のカテゴリリスト検索: {[]}')
        events = self.database.get_events_by_categories([], limit=5)
        print(f'[デバッグ] 検索結果: {len(events)}件')
        if len(events) > 0:
            print(f'[デバッグ] 最初の3件のカテゴリ:')
            for event in events[:3]:
                print(f'  {event.categories}')
        assert len(events) == 0
        
        # 無効なコマンド
        cmd = self.router.parse_command('無効なコマンド')
        assert cmd['type'] == 'help'  # デフォルトでヘルプ表示
    
    def test_performance(self):
        """パフォーマンステスト"""
        import time
        
        # カテゴリ検索の速度
        start_time = time.time()
        events = self.database.get_events_by_categories(['d', 'sns'], limit=100)
        end_time = time.time()
        
        assert end_time - start_time < 1.0  # 1秒以内
        assert len(events) <= 100  # 制限通り
    
    def test_url_generation(self):
        """URL生成テスト"""
        # 検索用URL
        url = self.data_service.generate_timeline_url('search', query='SNS')
        assert 'yuinoid.neocities.org' in url
        assert 'search=SNS' in url
        
        # カテゴリ用URL（将来の拡張用）
        # 年表サイトでは複合カテゴリ検索ができないため、
        # 除外条件がある場合は注意メッセージを表示する必要がある

def test_phase2_integration():
    """フェーズ2統合テスト"""
    config = Config()
    database = TimelineDatabase('data/timeline.db')
    data_service = TimelineDataService(config, database)
    router = CommandRouter(config, database, data_service, None)
    
    # 統合テストシナリオ
    test_cases = [
        {
            'input': 'カテゴリ d+sns-meme',
            'expected_type': 'category',
            'expected_categories': ['d', 'sns'],
            'expected_exclude': ['meme']
        },
        {
            'input': '検索 SNS カテゴリ d+sns',
            'expected_type': 'search',
            'expected_query': 'SNS',
            'expected_categories': ['d', 'sns'],
            'expected_exclude': []
        },
        {
            'input': '検索 分散 カテゴリ d+tech-incident',
            'expected_type': 'search',
            'expected_query': '分散',
            'expected_categories': ['d', 'tech'],
            'expected_exclude': ['incident']
        }
    ]
    
    for test_case in test_cases:
        cmd = router.parse_command(test_case['input'])
        assert cmd['type'] == test_case['expected_type']
        
        if test_case['expected_type'] == 'category':
            assert cmd['categories'] == test_case['expected_categories']
            assert cmd['exclude_categories'] == test_case['expected_exclude']
        elif test_case['expected_type'] == 'search':
            assert cmd['query'] == test_case['expected_query']
            assert cmd['categories'] == test_case['expected_categories']
            assert cmd['exclude_categories'] == test_case['expected_exclude']

if __name__ == '__main__':
    # スタンドアロン実行
    print("=== フェーズ2: 複合カテゴリ検索機能テスト ===")
    
    # 統合テスト実行
    test_phase2_integration()
    print("✅ 統合テスト完了")
    
    # 個別テスト実行
    test_instance = TestPhase2CompositeSearch()
    # 手動でセットアップ
    test_instance.config = Config()
    test_instance.database = TimelineDatabase('data/timeline.db')
    test_instance.data_service = TimelineDataService(test_instance.config, test_instance.database)
    test_instance.router = CommandRouter(test_instance.config, test_instance.database, test_instance.data_service, None)
    test_instance.search_handler = SearchHandler(test_instance.config, test_instance.database, test_instance.data_service, None)
    test_instance.category_handler = CategoryHandler(test_instance.config, test_instance.database, test_instance.data_service, None)
    
    print("\n=== コマンド解析テスト ===")
    test_instance.test_command_parsing_basic_categories()
    test_instance.test_command_parsing_composite_search()
    print("✅ コマンド解析テスト完了")
    
    print("\n=== データベース検索テスト ===")
    test_instance.test_database_category_search()
    test_instance.test_database_exclude_categories()
    print("✅ データベース検索テスト完了")
    
    print("\n=== ハンドラーテスト ===")
    asyncio.run(test_instance.test_category_handler_basic())
    asyncio.run(test_instance.test_search_handler_composite())
    print("✅ ハンドラーテスト完了")
    
    print("\n=== エラーハンドリングテスト ===")
    test_instance.test_error_handling()
    print("✅ エラーハンドリングテスト完了")
    
    print("\n=== パフォーマンステスト ===")
    test_instance.test_performance()
    print("✅ パフォーマンステスト完了")
    
    print("\n🎉 フェーズ2: 複合カテゴリ検索機能の全テスト完了！") 
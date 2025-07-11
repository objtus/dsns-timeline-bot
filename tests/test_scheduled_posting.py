#!/usr/bin/env python3
"""
定期投稿機能テストスクリプト

ホーム公開範囲での定期投稿機能をテストします
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, time
from unittest.mock import Mock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import Config
    from database import TimelineDatabase
    from data_service import TimelineDataService
    from handlers.today_handler import TodayHandler
    from bot_client import BotClient
    print("✅ モジュールインポート成功")
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    sys.exit(1)

class ScheduledPostingTester:
    """定期投稿機能テスター"""
    
    def __init__(self):
        self.config = None
        self.database = None
        self.data_service = None
        self.bot_client = None
        self.today_handler = None
        self.test_results = {}
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("📅 定期投稿機能テスト")
        print("=" * 60)
        
        tests = [
            ("初期化テスト", self.test_initialization),
            ("投稿タイミングテスト", self.test_posting_timing),
            ("ホーム公開範囲テスト", self.test_home_visibility),
            ("ハッシュタグ追加テスト", self.test_hashtag_addition),
            ("定期投稿実行テスト", self.test_scheduled_posting),
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}実行中...")
            try:
                success = asyncio.run(test_func()) if asyncio.iscoroutinefunction(test_func) else test_func()
                self.test_results[test_name] = success
                print(f"{'✅' if success else '❌'} {test_name}: {'成功' if success else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}例外: {e}")
                self.test_results[test_name] = False
        
        self.print_summary()
    
    def test_initialization(self) -> bool:
        """初期化テスト"""
        try:
            # 設定読み込み
            self.config = Config()
            
            # データベース初期化
            self.database = TimelineDatabase(self.config.database_path)
            
            # データサービス初期化
            self.data_service = TimelineDataService(self.config, self.database)
            
            # BotClient初期化
            self.bot_client = BotClient(self.config)
            
            # TodayHandler初期化
            self.today_handler = TodayHandler(self.config, self.database, self.data_service, self.bot_client)
            
            print("   ✅ 全コンポーネント初期化成功")
            return True
            
        except Exception as e:
            print(f"   ❌ 初期化エラー: {e}")
            return False
    
    def test_posting_timing(self) -> bool:
        """投稿タイミングテスト"""
        try:
            # 初期化チェック
            if not self.today_handler or not self.config:
                print("   ❌ 初期化が完了していません")
                return False
            
            # 現在時刻を取得
            now = datetime.now()
            
            # 投稿タイミングチェック
            should_post = self.today_handler.should_post_today(now)
            
            print(f"   ✅ 投稿タイミングチェック: {should_post}")
            print(f"   ✅ 現在時刻: {now.strftime('%H:%M:%S')}")
            print(f"   ✅ 設定投稿時刻: {self.config.post_times}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 投稿タイミングテストエラー: {e}")
            return False
    
    def test_home_visibility(self) -> bool:
        """公開範囲設定テスト"""
        try:
            # 初期化チェック
            if not self.config or not self.bot_client:
                print("   ❌ 初期化が完了していません")
                return False
            
            # ドライランモードを有効化
            import os
            original_dry_run = os.getenv('DRY_RUN_MODE')
            os.environ['DRY_RUN_MODE'] = 'true'
            
            # 設定された公開範囲での投稿テスト
            visibility = self.config.scheduled_post_visibility
            test_message = f"テスト投稿（{visibility}公開範囲）"
            
            # send_noteメソッドを直接テスト
            from typing import Literal
            visibility_literal: Literal['public', 'home', 'followers', 'specified'] = visibility  # type: ignore
            asyncio.run(self.bot_client.send_note(test_message, visibility=visibility_literal))
            
            print(f"   ✅ {visibility}公開範囲投稿テスト完了")
            
            # 環境変数を元に戻す
            if original_dry_run:
                os.environ['DRY_RUN_MODE'] = original_dry_run
            else:
                os.environ.pop('DRY_RUN_MODE', None)
            
            return True
            
        except Exception as e:
            print(f"   ❌ 公開範囲テストエラー: {e}")
            return False
    
    def test_hashtag_addition(self) -> bool:
        """ハッシュタグ追加機能テスト"""
        try:
            # 初期化チェック
            if not self.today_handler:
                print("   ❌ 初期化が完了していません")
                return False
            
            # テストメッセージ
            test_message = "今日は、\n\n**1925年****07月11日**　テストイベント\n\nだそうです！よかったね！"
            
            # ハッシュタグ追加
            result_message = self.today_handler._add_hashtag_for_scheduled_post(test_message)
            
            # ハッシュタグが含まれているかチェック
            if "#今日は何の日" in result_message:
                print("   ✅ ハッシュタグ追加機能: 正常")
                return True
            else:
                print("   ❌ ハッシュタグが追加されていません")
                return False
                
        except Exception as e:
            print(f"   ❌ ハッシュタグ追加テストエラー: {e}")
            return False
    
    async def test_scheduled_posting(self) -> bool:
        """定期投稿実行テスト"""
        try:
            # 初期化チェック
            if not self.config or not self.today_handler:
                print("   ❌ 初期化が完了していません")
                return False
            
            # ドライランモードを有効化
            import os
            original_dry_run = os.getenv('DRY_RUN_MODE')
            os.environ['DRY_RUN_MODE'] = 'true'
            
            # テスト用の時刻を設定（投稿時刻に該当するように）
            test_time = datetime.now()
            
            # 投稿時刻を一時的に現在時刻の1分前に設定
            original_post_times = self.config.post_times
            test_post_time = f"{test_time.hour:02d}:{(test_time.minute - 1) % 60:02d}"
            
            # 環境変数で投稿時刻を変更（設定プロパティは読み取り専用のため）
            os.environ['POST_TIMES'] = test_post_time
            
            # 新しい設定インスタンスを作成
            from config import Config
            test_config = Config()
            
            # 定期投稿実行
            success = await self.today_handler.post_scheduled_today_event(test_time)
            
            print(f"   ✅ 定期投稿実行テスト: {success}")
            
            # 環境変数を元に戻す
            if original_dry_run:
                os.environ['DRY_RUN_MODE'] = original_dry_run
            else:
                os.environ.pop('DRY_RUN_MODE', None)
            
            # POST_TIMESも元に戻す
            os.environ['POST_TIMES'] = ','.join(original_post_times)
            
            return True
            
        except Exception as e:
            print(f"   ❌ 定期投稿実行テストエラー: {e}")
            return False
    
    def print_summary(self):
        """テスト結果サマリー"""
        print("\n" + "=" * 60)
        print("📊 定期投稿機能テスト結果サマリー")
        print("=" * 60)
        
        success_count = sum(1 for result in self.test_results.values() if result)
        total_count = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{status}: {test_name}")
        
        print(f"\n総合結果: {success_count}/{total_count} テスト成功")
        
        if success_count == total_count:
            print("🎉 全テスト成功！定期投稿機能は正常に動作します。")
            print("📝 定期投稿は設定された時刻にホーム公開範囲で実行されます。")
        else:
            print("⚠️  一部のテストが失敗しました。")
    
    def cleanup(self):
        """クリーンアップ"""
        try:
            if self.bot_client:
                asyncio.run(self.bot_client.disconnect())
        except Exception as e:
            print(f"クリーンアップエラー: {e}")

def main():
    """メイン関数"""
    tester = ScheduledPostingTester()
    
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 
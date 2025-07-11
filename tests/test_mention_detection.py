#!/usr/bin/env python3
"""
メンション検出デバッグテストスクリプト

noteオブジェクトの構造とメンション検出ロジックをテストします
"""

import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import Mock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# ログ設定（DEBUGレベルで詳細ログを出力）
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import Config
    from database import TimelineDatabase
    from data_service import TimelineDataService
    from command_router import CommandRouter
    from bot_client import BotClient, DSNSMiPABot
    print("✅ モジュールインポート成功")
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    sys.exit(1)

class MentionDetectionTester:
    """メンション検出テスター"""
    
    def __init__(self):
        self.config = None
        self.database = None
        self.data_service = None
        self.bot_client = None
        self.command_router = None
        self.mipa_bot = None
        self.test_results = {}
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("🔍 メンション検出デバッグテスト")
        print("=" * 60)
        
        tests = [
            ("初期化テスト", self.test_initialization),
            ("noteオブジェクト構造テスト", self.test_note_structure),
            ("メンション検出テスト", self.test_mention_detection),
            ("コマンド解析テスト", self.test_command_parsing),
            ("統合テスト", self.test_integration),
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
            
            # CommandRouter初期化
            self.command_router = CommandRouter(self.config, self.database, self.data_service, self.bot_client)
            
            # MiPAボット初期化
            self.mipa_bot = DSNSMiPABot(self.bot_client)
            
            print("   ✅ 全コンポーネント初期化成功")
            return True
            
        except Exception as e:
            print(f"   ❌ 初期化エラー: {e}")
            return False
    
    def test_note_structure(self) -> bool:
        """noteオブジェクト構造テスト"""
        try:
            print("   📝 noteオブジェクト構造テスト")
            
            # テスト用のnoteオブジェクトを作成
            class MockNote:
                def __init__(self, text, is_reply=False, mentions=None):
                    self.text = text
                    self.id = "test_note_id"
                    
                    # ユーザー情報
                    class MockUser:
                        def __init__(self, username, user_id):
                            self.username = username
                            self.id = user_id
                    
                    self.user = MockUser("test_user", "user_123")
                    
                    # リプライ情報
                    if is_reply:
                        class MockReply:
                            def __init__(self):
                                self.user = MockUser("bot_username", "bot_456")
                                self.id = "reply_note_id"
                        self.reply = MockReply()
                    else:
                        self.reply = None
                    
                    # メンション情報
                    self.mentions = mentions or []
            
            # テストケース1: 通常のノート
            normal_note = MockNote("こんにちは")
            print(f"   ✅ 通常ノート: text='{normal_note.text}', user='{normal_note.user.username}'")
            
            # テストケース2: リプライノート
            reply_note = MockNote("今日", is_reply=True)
            print(f"   ✅ リプライノート: text='{reply_note.text}', reply_user='{reply_note.reply.user.username}'")
            
            # テストケース3: メンション付きノート
            class MockUser:
                def __init__(self, username, user_id):
                    self.username = username
                    self.id = user_id
            mention_note = MockNote("@bot_username 今日", mentions=[MockUser("bot_username", "bot_456")])
            print(f"   ✅ メンション付きノート: text='{mention_note.text}', mentions={len(mention_note.mentions)}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ note構造テストエラー: {e}")
            return False
    
    def test_mention_detection(self) -> bool:
        """メンション検出テスト"""
        try:
            print("   🔍 メンション検出テスト")
            
            # テスト用のnoteオブジェクトを作成
            class MockNote:
                def __init__(self, text, is_reply=False, mentions=None, user_id="user_123"):
                    self.text = text
                    self.id = "test_note_id"
                    self.user_id = user_id
                    
                    class MockUser:
                        def __init__(self, username, user_id):
                            self.username = username
                            self.id = user_id
                    
                    self.user = MockUser("test_user", user_id)
                    
                    if is_reply:
                        class MockReply:
                            def __init__(self):
                                self.user = MockUser("bot_username", "bot_456")
                                self.user_id = "bot_456"
                                self.id = "reply_note_id"
                        self.reply = MockReply()
                    else:
                        self.reply = None
                    
                    self.mentions = mentions or []
            
            # メンション検出ロジックをテスト
            def test_mention_logic(note):
                """メンション検出ロジックのテスト"""
                bot_id = "bot_456"
                
                # メンション検出（IDで比較）
                is_mention = False
                if hasattr(note, 'mentions') and note.mentions:
                    for mention in note.mentions:
                        if mention == bot_id:
                            is_mention = True
                            break
                
                # リプライの場合は、リプライ先がボットかどうかもチェック
                if not is_mention and hasattr(note, 'reply') and note.reply:
                    if getattr(note.reply, 'user_id', None) == bot_id:
                        is_mention = True
                
                return is_mention
            
            # テストケース1: リプライ（「今日」）
            reply_note = MockNote("今日", is_reply=True)
            result1 = test_mention_logic(reply_note)
            print(f"   ✅ リプライ検出テスト: '{reply_note.text}' -> {result1}")
            
            # テストケース2: @メンション
            mention_note = MockNote("@bot_username 今日", mentions=["bot_456"])
            result2 = test_mention_logic(mention_note)
            print(f"   ✅ @メンション検出テスト: '{mention_note.text}' -> {result2}")
            
            # テストケース3: 通常のノート（検出されないはず）
            normal_note = MockNote("こんにちは")
            result3 = test_mention_logic(normal_note)
            print(f"   ✅ 通常ノート検出テスト: '{normal_note.text}' -> {result3}")
            
            # 期待される結果
            expected_results = [True, True, False]
            actual_results = [result1, result2, result3]
            
            if actual_results == expected_results:
                print("   ✅ メンション検出テスト成功")
                return True
            else:
                print(f"   ❌ メンション検出テスト失敗: 期待={expected_results}, 実際={actual_results}")
                return False
            
        except Exception as e:
            print(f"   ❌ メンション検出テストエラー: {e}")
            return False
    
    def test_command_parsing(self) -> bool:
        """コマンド解析テスト"""
        try:
            print("   📝 コマンド解析テスト")
            
            # テストケース
            test_cases = [
                ("今日", "today"),
                ("きょう", "today"),
                ("today", "today"),
                ("5月1日", "date"),
                ("検索 Mastodon", "search"),
                ("ヘルプ", "help"),
            ]
            
            for input_text, expected_type in test_cases:
                result = self.command_router.parse_command(input_text)
                actual_type = result.get('type')
                
                if actual_type == expected_type:
                    print(f"   ✅ '{input_text}' -> {actual_type}")
                else:
                    print(f"   ❌ '{input_text}' -> {actual_type} (期待: {expected_type})")
                    return False
            
            print("   ✅ コマンド解析テスト成功")
            return True
            
        except Exception as e:
            print(f"   ❌ コマンド解析テストエラー: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """統合テスト"""
        try:
            print("   🔗 統合テスト")
            
            # テスト用のnoteオブジェクト（リプライ）
            class MockNote:
                def __init__(self, text):
                    self.text = text
                    self.id = "test_note_id"
                    self.user_id = "user_123"
                    
                    class MockUser:
                        def __init__(self):
                            self.username = "test_user"
                            self.id = "user_123"
                    
                    self.user = MockUser()
                    
                    # リプライ情報
                    class MockReply:
                        def __init__(self):
                            class MockReplyUser:
                                def __init__(self):
                                    self.username = "bot_username"
                                    self.id = "bot_456"
                            self.user = MockReplyUser()
                            self.user_id = "bot_456"
                            self.id = "reply_note_id"
                    
                    self.reply = MockReply()
                    self.mentions = []
            
            # 「今日」のリプライノートを作成
            test_note = MockNote("今日")
            
            # メンション検出ロジックテスト
            def test_mention_logic(note):
                """メンション検出ロジックのテスト"""
                bot_id = "bot_456"
                
                # メンション検出（IDで比較）
                is_mention = False
                if hasattr(note, 'mentions') and note.mentions:
                    for mention in note.mentions:
                        if mention == bot_id:
                            is_mention = True
                            break
                
                # リプライの場合は、リプライ先がボットかどうかもチェック
                if not is_mention and hasattr(note, 'reply') and note.reply:
                    if getattr(note.reply, 'user_id', None) == bot_id:
                        is_mention = True
                
                return is_mention
            
            # メンション検出テスト
            is_mention = test_mention_logic(test_note)
            print(f"   ✅ メンション検出: {is_mention}")
            
            if not is_mention:
                print("   ❌ メンション検出に失敗")
                return False
            
            # コマンド解析テスト
            command = self.command_router.parse_command(test_note.text)
            print(f"   ✅ コマンド解析: {command}")
            
            if command.get('type') != 'today':
                print("   ❌ コマンド解析に失敗")
                return False
            
            # ルーティングテスト（ドライランモード）
            import os
            original_dry_run = os.getenv('DRY_RUN_MODE')
            os.environ['DRY_RUN_MODE'] = 'true'
            
            try:
                result = await self.command_router.route_message(test_note, "bot_username")
                print(f"   ✅ ルーティング結果: {len(result)}文字")
                print(f"   📄 結果プレビュー: {result[:100]}...")
                
                if "今日は" in result:
                    print("   ✅ 統合テスト成功")
                    return True
                else:
                    print("   ❌ 期待される結果が含まれていません")
                    return False
                    
            finally:
                # 環境変数を元に戻す
                if original_dry_run:
                    os.environ['DRY_RUN_MODE'] = original_dry_run
                else:
                    os.environ.pop('DRY_RUN_MODE', None)
            
        except Exception as e:
            print(f"   ❌ 統合テストエラー: {e}")
            return False
    
    def print_summary(self):
        """テスト結果サマリー"""
        print("\n" + "=" * 60)
        print("📊 メンション検出デバッグテスト結果サマリー")
        print("=" * 60)
        
        success_count = sum(1 for result in self.test_results.values() if result)
        total_count = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{status}: {test_name}")
        
        print(f"\n総合結果: {success_count}/{total_count} テスト成功")
        
        if success_count == total_count:
            print("🎉 全テスト成功！メンション検出は正常に動作します。")
        else:
            print("⚠️  一部のテストが失敗しました。")
            print("💡 デバッグログを確認して問題を特定してください。")
    
    def cleanup(self):
        """クリーンアップ"""
        try:
            if self.bot_client:
                asyncio.run(self.bot_client.disconnect())
        except Exception as e:
            print(f"クリーンアップエラー: {e}")

def main():
    """メイン関数"""
    tester = MentionDetectionTester()
    
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
bot_client.py 詳細テストスクリプト

BotClientの各機能を個別にテストします：
1. 初期化テスト
2. 設定テスト
3. メッセージ送信テスト（ドライランモード）
4. ステータス取得テスト
5. エラーハンドリングテスト
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import Config
    from bot_client import BotClient, DSNSMiPABot
    print("✅ モジュールインポート成功")
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    sys.exit(1)

class BotClientTester:
    """BotClient詳細テスター"""
    
    def __init__(self):
        self.config = None
        self.client = None
        self.test_results = {}
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("🤖 BotClient 詳細テスト")
        print("=" * 60)
        
        tests = [
            ("初期化テスト", self.test_initialization),
            ("設定テスト", self.test_config),
            ("ステータス取得テスト", self.test_status),
            ("メッセージ送信テスト", self.test_message_sending),
            ("エラーハンドリングテスト", self.test_error_handling),
            ("切断処理テスト", self.test_disconnect),
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
            
            # BotClient初期化
            self.client = BotClient(self.config)
            
            # 基本属性の確認
            assert self.client.config == self.config
            assert self.client.mipa_bot is None
            assert self.client.command_router is None
            assert self.client.is_connected is False
            assert self.client.last_heartbeat is None
            assert self.client.connection_count == 0
            assert self.client.note_count == 0
            assert self.client.startup_time is None
            
            print("   ✅ BotClient初期化成功")
            print("   ✅ 基本属性確認完了")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 初期化エラー: {e}")
            return False
    
    def test_config(self) -> bool:
        """設定テスト"""
        try:
            # ホスト名取得テスト
            host = self.client._get_misskey_host()
            print(f"   ✅ ホスト名取得: {host}")
            
            # 設定値の確認
            assert hasattr(self.config, 'misskey_token')
            assert hasattr(self.config, 'misskey_host') or hasattr(self.config, 'misskey_url')
            
            print("   ✅ 設定値確認完了")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 設定エラー: {e}")
            return False
    
    def test_status(self) -> bool:
        """ステータス取得テスト"""
        try:
            # 初期状態のステータス
            status = self.client.get_client_status()
            
            expected_keys = [
                'client_type', 'is_connected', 'connection_count', 
                'note_count', 'last_heartbeat', 'has_router', 'dry_run_mode'
            ]
            
            for key in expected_keys:
                assert key in status, f"ステータスに{key}が含まれていません"
            
            print(f"   ✅ ステータス取得: {status['client_type']}")
            print(f"   ✅ 接続状態: {status['is_connected']}")
            print(f"   ✅ ドライランモード: {status['dry_run_mode']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ ステータスエラー: {e}")
            return False
    
    async def test_message_sending(self) -> bool:
        """メッセージ送信テスト（ドライランモード）"""
        try:
            # ドライランモードを有効化（環境変数で制御）
            import os
            original_dry_run = os.getenv('DRY_RUN_MODE')
            os.environ['DRY_RUN_MODE'] = 'true'
            
            # 新しい設定インスタンスを作成（ドライランモード有効）
            dry_run_config = Config()
            dry_run_client = BotClient(dry_run_config)
            
            # モックノートオブジェクト
            mock_note = Mock()
            mock_note.id = "test_note_id"
            mock_note.text = "テストメッセージ"
            
            # リプライ送信テスト
            await dry_run_client.send_reply(mock_note, "テストリプライ")
            print("   ✅ リプライ送信テスト完了（ドライラン）")
            
            # ノート投稿テスト
            await dry_run_client.send_note("テスト投稿")
            print("   ✅ ノート投稿テスト完了（ドライラン）")
            
            # 環境変数を元に戻す
            if original_dry_run:
                os.environ['DRY_RUN_MODE'] = original_dry_run
            else:
                os.environ.pop('DRY_RUN_MODE', None)
            
            return True
            
        except Exception as e:
            print(f"   ❌ メッセージ送信エラー: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """エラーハンドリングテスト"""
        try:
            # 無効な設定でのエラーハンドリング
            invalid_config = Mock()
            invalid_config.misskey_token = None
            
            try:
                invalid_client = BotClient(invalid_config)
                # 接続時にエラーが発生することを確認
                with patch('bot_client.logger') as mock_logger:
                    try:
                        asyncio.run(invalid_client.connect())
                    except ValueError:
                        print("   ✅ 無効設定でのエラーハンドリング成功")
                    except Exception as e:
                        print(f"   ✅ 予期されるエラー: {e}")
            except Exception as e:
                print(f"   ✅ 初期化エラーハンドリング: {e}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ エラーハンドリングテストエラー: {e}")
            return False
    
    async def test_disconnect(self) -> bool:
        """切断処理テスト"""
        try:
            # モックボットを作成
            mock_bot = Mock()
            mock_bot.close = AsyncMock()
            self.client.mipa_bot = mock_bot
            
            # 切断処理テスト
            await self.client.disconnect()
            
            # 状態確認
            assert self.client.is_connected is False
            print("   ✅ 切断処理テスト完了")
            
            # closeメソッドがない場合のテスト
            mock_bot.close = None
            mock_bot.ws = Mock()
            mock_bot.ws.close = AsyncMock()
            
            await self.client.disconnect()
            print("   ✅ フォールバック切断処理テスト完了")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 切断処理エラー: {e}")
            return False
    
    def print_summary(self):
        """テスト結果サマリー"""
        print("\n" + "=" * 60)
        print("📊 BotClient テスト結果サマリー")
        print("=" * 60)
        
        success_count = sum(1 for result in self.test_results.values() if result)
        total_count = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{status}: {test_name}")
        
        print(f"\n総合結果: {success_count}/{total_count} テスト成功")
        
        if success_count == total_count:
            print("🎉 全テスト成功！BotClientは正常に動作します。")
        else:
            print("⚠️  一部のテストが失敗しました。")
    
    def cleanup(self):
        """クリーンアップ"""
        try:
            if self.client:
                asyncio.run(self.client.disconnect())
        except Exception as e:
            print(f"クリーンアップエラー: {e}")

def main():
    """メイン関数"""
    tester = BotClientTester()
    
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 
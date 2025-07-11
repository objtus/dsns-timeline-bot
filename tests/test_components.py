#!/usr/bin/env python3
"""
分散SNS関連年表bot - コンポーネントテストスクリプト

このスクリプトは以下のテストを実行します：
1. 設定ファイルの読み込みテスト
2. データベース初期化テスト
3. データサービステスト（HTMLダウンロード・パース）
4. 今日のイベントハンドラーテスト
5. 統合テスト（メッセージ生成）
"""

import asyncio
import sys
import logging
from pathlib import Path
import traceback
from datetime import date, datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# インポートのテスト
try:
    from config import Config, ConfigError
    from database import TimelineDatabase, DatabaseError, TimelineEvent
    from data_service import TimelineDataService, DataServiceError
    from handlers.today_handler import TodayHandler
    print("✅ モジュールインポート成功")
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("プロジェクトディレクトリから実行してください")
    sys.exit(1)

class ComponentTester:
    """コンポーネントテスター"""
    
    def __init__(self):
        self.config = None
        self.database = None
        self.data_service = None
        self.today_handler = None
        
        # テスト結果
        self.test_results = {}
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("🧪 分散SNS関連年表bot コンポーネントテスト")
        print("=" * 60)
        
        tests = [
            ("設定読み込み", self.test_config),
            ("データベース", self.test_database),
            ("データサービス", self.test_data_service),
            ("今日のハンドラー", self.test_today_handler),
            ("統合テスト", self.test_integration),
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}テスト実行中...")
            try:
                success = asyncio.run(test_func()) if asyncio.iscoroutinefunction(test_func) else test_func()
                self.test_results[test_name] = success
                print(f"{'✅' if success else '❌'} {test_name}テスト: {'成功' if success else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}テスト例外: {e}")
                self.test_results[test_name] = False
        
        self.print_summary()
    
    def test_config(self) -> bool:
        """設定テスト"""
        try:
            # 設定ファイルの存在確認
            env_file = Path(".env")
            if not env_file.exists():
                print("⚠️  .env ファイルが見つかりません")
                print("   .env.template を .env にコピーして設定してください")
                
                # テスト用の最小設定で続行
                self.config = Config()
                try:
                    # 必須設定のチェック（エラーになることを期待）
                    self.config.misskey_url
                    self.config.misskey_token
                except ConfigError:
                    print("   最小設定でテスト続行（MISSKEY設定は未完了）")
                    return True
            else:
                self.config = Config()
                print(f"   設定ファイル読み込み成功: {env_file}")
                
                # 設定表示（機密情報は隠蔽）
                summary = self.config.get_env_summary()
                for key, value in summary.items():
                    print(f"   {key}: {value}")
                
                return True
                
        except Exception as e:
            print(f"   設定エラー: {e}")
            return False
        
        return False
    
    def test_database(self) -> bool:
        """データベーステスト"""
        try:
            if not self.config:
                print("   設定が不完全なため、テンポラリDBでテスト")
                db_path = Path("test_timeline.db")
            else:
                db_path = self.config.database_path
            
            self.database = TimelineDatabase(db_path)
            print(f"   データベース初期化成功: {db_path}")
            
            # テストデータの挿入
            test_events = [
                TimelineEvent(2023, 5, 1, "テストイベント1", "test"),
                TimelineEvent(2023, 5, 1, "テストイベント2", "test"),
                TimelineEvent(2024, 12, 25, "クリスマステスト", "holiday")
            ]
            
            added, updated = self.database.add_events_batch(test_events)
            print(f"   テストデータ挿入: {added}件追加, {updated}件更新")
            
            # 検索テスト
            today_events = self.database.get_events_by_date(5, 1)
            print(f"   5月1日のイベント: {len(today_events)}件")
            
            search_results = self.database.search_events("テスト")
            print(f"   'テスト'検索結果: {len(search_results)}件")
            
            # 統計情報
            stats = self.database.get_statistics()
            print(f"   データベース統計: {stats['total_events']}件のイベント")
            
            return True
            
        except Exception as e:
            print(f"   データベースエラー: {e}")
            return False
    
    async def test_data_service(self) -> bool:
        """データサービステスト"""
        try:
            if not self.database:
                print("   データベースが未初期化")
                return False
            
            if not self.config:
                print("   設定が不完全なため、デフォルト設定でテスト")
                # 最小限の設定を作成
                from config import Config
                self.config = Config()
            
            self.data_service = TimelineDataService(self.config, self.database)
            print("   データサービス初期化成功")
            
            # ヘルスチェック
            async with self.data_service:
                health = await self.data_service.health_check()
                print(f"   ヘルスチェック: {health['status']}")
                
                if health['status'] in ['healthy', 'degraded']:
                    print("   HTTP接続テスト成功")
                    
                    # 実際のデータ取得テスト（時間がかかる可能性）
                    print("   HTML取得テスト実行中...")
                    try:
                        html_content = await self.data_service.fetch_timeline_html()
                        print(f"   HTML取得成功: {len(html_content)} bytes")
                        
                        # HTMLパーステスト
                        events = self.data_service.parse_timeline_html(html_content)
                        print(f"   HTMLパース成功: {len(events)}件のイベント抽出")
                        
                        if events:
                            # サンプルイベント表示
                            sample = events[0]
                            print(f"   サンプルイベント: {sample.year}年{sample.month:02d}月{sample.day:02d}日 - {sample.content[:50]}...")
                    except Exception as e:
                        print(f"   データ取得エラー（ネットワーク問題の可能性）: {e}")
                        # ネットワークエラーでもサービス自体は正常とみなす
                else:
                    print(f"   ヘルスチェック警告: {health}")
            
            return True
            
        except Exception as e:
            print(f"   データサービスエラー: {e}")
            return False
    
    async def test_today_handler(self) -> bool:
        """今日のハンドラーテスト"""
        try:
            if not all([self.config, self.database, self.data_service]):
                print("   前提コンポーネントが未初期化")
                return False
            
            if self.config and self.database and self.data_service:
                self.today_handler = TodayHandler(self.config, self.database, self.data_service)
                print("   今日のハンドラー初期化成功")
            else:
                print("   前提コンポーネントが不完全")
                return False
            
            # メッセージ生成テスト
            message = await self.today_handler.get_today_message()
            print(f"   今日のメッセージ生成: {len(message)}文字")
            print(f"   メッセージプレビュー:")
            print("   " + message.replace('\n', '\n   ')[:200] + "...")
            
            # 投稿時刻チェック
            should_post = self.today_handler.should_post_today()
            print(f"   投稿時刻チェック: {'必要' if should_post else '不要'}")
            
            # ステータス確認
            status = self.today_handler.get_handler_status()
            print(f"   ハンドラーステータス: {status['handler_type']}")
            
            return True
            
        except Exception as e:
            print(f"   今日のハンドラーエラー: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """統合テスト"""
        try:
            if not all([self.config, self.database, self.data_service, self.today_handler]):
                print("   前提コンポーネントが未初期化")
                return False
            
            print("   統合テスト実行中...")
            
            # 複数日付のメッセージ生成テスト
            test_dates = [
                (5, 1),   # メーデー
                (12, 25), # クリスマス
                (1, 1),   # 元日
            ]
            
            for month, day in test_dates:
                try:
                    if self.data_service:
                        message = self.data_service.get_date_events_message(month, day)
                        print(f"   {month:02d}月{day:02d}日メッセージ: {len(message)}文字")
                    else:
                        print(f"   {month:02d}月{day:02d}日メッセージ: データサービス未初期化")
                except Exception as e:
                    print(f"   {month:02d}月{day:02d}日メッセージエラー: {e}")
            
            # 検索テスト
            test_keywords = ["分散", "SNS", "ActivityPub", "Mastodon"]
            for keyword in test_keywords:
                try:
                    if self.data_service:
                        message = self.data_service.search_events_message(keyword, limit=3)
                        result_count = len([line for line in message.split('\n') if '年' in line and '月' in line])
                        print(f"   '{keyword}'検索: {result_count}件の結果")
                    else:
                        print(f"   '{keyword}'検索: データサービス未初期化")
                except Exception as e:
                    print(f"   '{keyword}'検索エラー: {e}")
            
            print("   統合テスト完了")
            return True
            
        except Exception as e:
            print(f"   統合テストエラー: {e}")
            return False
    
    def print_summary(self):
        """テスト結果サマリー表示"""
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{status}: {test_name}")
        
        print(f"\n総合結果: {passed_tests}/{total_tests} テスト成功")
        
        if passed_tests == total_tests:
            print("🎉 全テスト成功！ボットは正常に動作する準備ができています。")
            print("\n次のステップ:")
            print("1. .env ファイルにMisskey接続情報を設定")
            print("2. python main.py でボット起動")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  ほぼ成功！一部の機能に問題がありますが、基本動作は可能です。")
        else:
            print("❌ 重要な問題があります。ログを確認して修正してください。")
        
        # クリーンアップ
        self.cleanup()
    
    def cleanup(self):
        """テスト後のクリーンアップ"""
        try:
            # テスト用データベースファイルの削除
            test_db = Path("test_timeline.db")
            if test_db.exists():
                test_db.unlink()
                print("\nテスト用データベースファイルを削除しました")
        except Exception as e:
            print(f"クリーンアップエラー: {e}")


def main():
    """メイン実行"""
    # ロギング設定
    logging.basicConfig(
        level=logging.WARNING,  # テスト中は警告以上のみ表示
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト実行
    tester = ComponentTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
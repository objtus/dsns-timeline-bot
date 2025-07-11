"""
ヘルプ表示専用ハンドラー
"""

import logging

from constants import ErrorMessages
from exceptions import HandlerError
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class HelpHandler(BaseHandler):
    """ヘルプ表示専用ハンドラー"""
    
    async def handle(self, note, command):
        """
        ヘルプ要求を処理
        
        Args:
            note: Misskeyのnoteオブジェクト
            command: パースされたコマンド辞書（type='help'）
            
        Returns:
            str: ヘルプメッセージ
        """
        try:
            logger.info("ヘルプ処理開始")
            
            help_message = """🤖 分散SNS関連年表bot の使い方

📅 **今日のイベント**
- 「今日」「きょう」「today」→ 今日の年表イベント
- 何もつけずにメンションでも今日のイベントを返します

📆 **特定日付のイベント**
- 「5月1日」「05月01日」→ その日の年表イベント

🔍 **検索機能**
- 「検索 キーワード」→ キーワードで年表を検索
- 「検索 SNS カテゴリ dsns+tech」→ 複合条件での検索

🗂️ **カテゴリ機能**
- 「カテゴリ dsns+tech」→ dsnsかつtechカテゴリのイベント一覧
- 「カテゴリ dsns+tech-meme」→ dsns・techだがmeme以外のイベント
- 「カテゴリ一覧」→ 利用可能なカテゴリ一覧を表示
- 「カテゴリ統計」→ 年代別・年別のカテゴリ分布
- 「カテゴリ分析 dsns」→ dsnsと組み合わせられるカテゴリの統計

📊 **年代別機能**
- 「2000年代」「1990年代 統計」→ 年代別統計情報
- 「90年代 代表」「2000年代 代表」→ 年代別重要イベント
- 「1990年から1999年 概要」「2010年代 概要」→ 年代別概要
- 「2000年代 カテゴリ web+tech」→ 年代＋カテゴリの複合条件

📈 **ステータス機能**（システム監視）
- 「ステータス」「status」→ 基本ステータス情報
- 「ステータス サーバー」「status server」→ サーバー詳細情報
- 「ステータス ボット」「status bot」→ ボット詳細情報
- 「ステータス 年表」「status timeline」→ 年表詳細情報

❓ **その他**
- 「ヘルプ」「help」→ この使い方を表示

データ元: [分散SNS関連年表](https://yuinoid.neocities.org/txt/my_dsns_timeline)"""
            
            logger.info("ヘルプメッセージ生成完了")
            return help_message
            
        except Exception as e:
            logger.error(f"ヘルプ処理エラー: {e}")
            raise HandlerError(
                f"ヘルプ処理エラー: {e}",
                handler_type="help",
                command=str(command)
            )
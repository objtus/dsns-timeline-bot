"""
概要ファイル管理モジュール

年代別の概要テキストを外部ファイルから読み込み・管理する機能を提供
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)

class SummaryManager:
    """概要ファイル管理クラス"""
    
    def __init__(self, summaries_dir: Path):
        """
        概要マネージャー初期化
        
        Args:
            summaries_dir: 概要ファイルのディレクトリパス
        """
        self.summaries_dir = Path(summaries_dir)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        # 年代別ファイル名マッピング
        self.decade_files = {
            (1920, 1929): '1920s.md',
            (1930, 1939): '1930s.md',
            (1940, 1949): '1940s.md',
            (1950, 1959): '1950s.md',
            (1960, 1969): '1960s.md',
            (1970, 1979): '1970s.md',
            (1980, 1989): '1980s.md',
            (1990, 1999): '1990s.md',
            (2000, 2009): '2000s.md',
            (2010, 2019): '2010s.md',
            (2020, 2029): '2020s.md',
        }
        
        # テンプレートファイル
        self.template_file = 'template.md'
        
        logger.info(f"概要マネージャー初期化完了: {self.summaries_dir}")
    
    def get_decade_summary(self, start_year: int, end_year: int, decade_name: str) -> str:
        """
        年代別概要を取得
        
        Args:
            start_year: 開始年
            end_year: 終了年
            decade_name: 年代名
            
        Returns:
            概要テキスト（Markdown形式）
        """
        try:
            # 該当する年代ファイルを探す
            file_path = self._get_decade_file_path(start_year, end_year)
            
            if file_path and file_path.exists():
                # 既存ファイルから読み込み
                content = self._read_summary_file(file_path)
                logger.info(f"概要ファイル読み込み: {file_path}")
            else:
                # テンプレートから生成
                content = self._generate_from_template(start_year, end_year, decade_name)
                logger.info(f"テンプレートから概要生成: {start_year}-{end_year}")
            
            # MarkdownをMisskey投稿用に変換
            formatted_content = self._format_for_misskey(content, decade_name)
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"概要取得エラー: {e}")
            return self._get_fallback_summary(decade_name)
    
    def _get_decade_file_path(self, start_year: int, end_year: int) -> Optional[Path]:
        """年代に対応するファイルパスを取得"""
        for (decade_start, decade_end), filename in self.decade_files.items():
            if start_year == decade_start and end_year == decade_end:
                return self.summaries_dir / filename
        return None
    
    def _read_summary_file(self, file_path: Path) -> str:
        """概要ファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"ファイル読み込みエラー {file_path}: {e}")
            raise
    
    def _generate_from_template(self, start_year: int, end_year: int, decade_name: str) -> str:
        """テンプレートから概要を生成"""
        template_path = self.summaries_dir / self.template_file
        
        if not template_path.exists():
            logger.warning(f"テンプレートファイルが見つかりません: {template_path}")
            return self._get_fallback_summary(decade_name)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # プレースホルダーを置換
            content = template_content.replace('{decade_name}', decade_name)
            content = content.replace('{start_year}', str(start_year))
            content = content.replace('{end_year}', str(end_year))
            
            return content
            
        except Exception as e:
            logger.error(f"テンプレート処理エラー: {e}")
            return self._get_fallback_summary(decade_name)
    
    def _format_for_misskey(self, content: str, decade_name: str) -> str:
        """
        MarkdownをMisskey投稿用に変換
        
        Args:
            content: 元のMarkdownコンテンツ
            decade_name: 年代名
            
        Returns:
            Misskey投稿用のフォーマット済みテキスト
        """
        # ヘッダーを追加
        formatted_parts = [f"📖 **{decade_name}の概要**", ""]
        
        # Markdownの見出しを太字に変換
        content = re.sub(r'^# (.+)$', r'**\1**', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'**\1**', content, flags=re.MULTILINE)
        
        # 箇条書きを保持
        content = re.sub(r'^• (.+)$', r'• \1', content, flags=re.MULTILINE)
        
        # 空行を適切に処理
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        formatted_parts.append(content.strip())
        
        return "\n".join(formatted_parts)
    
    def _get_fallback_summary(self, decade_name: str) -> str:
        """フォールバック用の概要"""
        return f"""📖 **{decade_name}の概要**

{decade_name}の詳細な概要は準備中です。

この年代の分散SNS関連技術の発展について、詳細な情報を収集・整理中です。"""
    
    def list_available_decades(self) -> Dict[str, Any]:
        """利用可能な年代一覧を取得"""
        available = {}
        
        for (start_year, end_year), filename in self.decade_files.items():
            file_path = self.summaries_dir / filename
            available[f"{start_year}-{end_year}"] = {
                'filename': filename,
                'exists': file_path.exists(),
                'path': str(file_path)
            }
        
        return available
    
    def create_decade_file(self, start_year: int, end_year: int, content: str) -> bool:
        """
        年代別概要ファイルを作成
        
        Args:
            start_year: 開始年
            end_year: 終了年
            content: 概要内容
            
        Returns:
            作成成功時True
        """
        try:
            file_path = self._get_decade_file_path(start_year, end_year)
            if not file_path:
                logger.error(f"対応する年代ファイルが見つかりません: {start_year}-{end_year}")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"概要ファイル作成: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"概要ファイル作成エラー: {e}")
            return False
    
    def update_decade_file(self, start_year: int, end_year: int, content: str) -> bool:
        """
        年代別概要ファイルを更新
        
        Args:
            start_year: 開始年
            end_year: 終了年
            content: 新しい概要内容
            
        Returns:
            更新成功時True
        """
        return self.create_decade_file(start_year, end_year, content)


# テスト用関数
def test_summary_manager():
    """SummaryManagerのテスト"""
    import tempfile
    
    print("=== SummaryManager テスト ===")
    
    # テンポラリディレクトリでテスト
    with tempfile.TemporaryDirectory() as temp_dir:
        summaries_dir = Path(temp_dir) / "summaries"
        manager = SummaryManager(summaries_dir)
        
        print("✅ マネージャー初期化成功")
        
        # 利用可能な年代一覧
        available = manager.list_available_decades()
        print(f"✅ 利用可能な年代: {list(available.keys())}")
        
        # 1990年代の概要取得（テンプレートから生成）
        summary = manager.get_decade_summary(1990, 1999, "1990年代")
        print(f"✅ 1990年代概要生成: {len(summary)}文字")
        print(f"   プレビュー: {summary[:100]}...")
        
        # カスタム概要ファイル作成
        custom_content = """# カスタム1990年代

これはテスト用のカスタム概要です。

## 特徴
• テスト項目1
• テスト項目2"""
        
        success = manager.create_decade_file(1990, 1999, custom_content)
        print(f"✅ カスタムファイル作成: {success}")
        
        # 作成したファイルから読み込み
        custom_summary = manager.get_decade_summary(1990, 1999, "1990年代")
        print(f"✅ カスタム概要読み込み: {len(custom_summary)}文字")
        
        print("✅ 全テスト完了")
        return True


if __name__ == "__main__":
    test_summary_manager() 
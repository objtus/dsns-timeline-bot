"""
分散SNS関連年表bot - データベース操作モジュール

このモジュールは以下を提供します：
- SQLiteデータベースの初期化と管理
- 年表データの保存・更新・検索
- 日付別イベント取得
- データ統計情報の取得
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from contextlib import contextmanager
import json

from constants import DatabaseTables, ErrorMessages, TimeFormats
from exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)

class TimelineEvent:
    """年表イベントのデータクラス"""
    
    def __init__(self, year: int, month: int, day: int, content: str, 
                 categories: Optional[str] = None, event_id: Optional[int] = None,
                 html_content: Optional[str] = None):
        self.event_id = event_id
        self.year = year
        self.month = month
        self.day = day
        self.content = content
        self.categories = categories or ""
        self.html_content = html_content or ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def get_date_str(self) -> str:
        """MM月DD日形式の日付文字列を取得"""
        return f"{self.month:02d}月{self.day:02d}日"
    
    def get_iso_date(self) -> str:
        """YYYY-MM-DD形式の日付文字列を取得"""
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'event_id': self.event_id,
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'content': self.content,
            'categories': self.categories,
            'html_content': self.html_content,
            'date_str': self.get_date_str(),
            'iso_date': self.get_iso_date(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return f"{self.year}年{self.get_date_str()} - {self.content[:50]}..."
    
    def __repr__(self) -> str:
        return f"TimelineEvent(year={self.year}, month={self.month}, day={self.day}, content='{self.content[:30]}...')"

class TimelineDatabase:
    """
    年表データベース管理クラス
    
    SQLiteを使用して年表データの永続化と検索機能を提供
    """
    
    def __init__(self, db_path: Path):
        """
        データベース初期化
        
        Args:
            db_path: SQLiteデータベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"データベース初期化完了: {self.db_path}")
    
    def _init_database(self):
        """データベーステーブルの初期化"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # イベントテーブル
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {DatabaseTables.TIMELINE_EVENTS} (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    categories TEXT DEFAULT '',
                    html_content TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year, month, day, content)
                )
            ''')
            
            # 日付別インデックス（検索高速化）
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_date 
                ON {DatabaseTables.TIMELINE_EVENTS} (month, day)
            ''')
            
            # 年別インデックス
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_year 
                ON {DatabaseTables.TIMELINE_EVENTS} (year)
            ''')
            
            # 全文検索用インデックス
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_content 
                ON {DatabaseTables.TIMELINE_EVENTS} (content)
            ''')
            
            # データ更新履歴テーブル
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {DatabaseTables.UPDATE_HISTORY} (
                    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    events_added INTEGER DEFAULT 0,
                    events_updated INTEGER DEFAULT 0,
                    events_total INTEGER DEFAULT 0,
                    source_url TEXT,
                    status TEXT DEFAULT 'success',
                    notes TEXT
                )
            ''')
            
            conn.commit()
            logger.debug("データベーステーブル初期化完了")
            
            # html_contentカラムが存在しない場合は追加
            try:
                cursor.execute(f"SELECT html_content FROM {DatabaseTables.TIMELINE_EVENTS} LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute(f"ALTER TABLE {DatabaseTables.TIMELINE_EVENTS} ADD COLUMN html_content TEXT DEFAULT ''")
                conn.commit()
                logger.info("html_contentカラムを追加しました")
    
    @contextmanager
    def _get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書ライクなアクセス
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"データベースエラー: {e}")
            raise DatabaseError(f"{ErrorMessages.DATABASE_ERROR}: {e}")
        finally:
            if conn:
                conn.close()
    
    def add_event(self, event: TimelineEvent) -> int:
        """
        イベントを追加
        
        Args:
            event: 追加するイベント
            
        Returns:
            追加されたイベントのID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                INSERT OR REPLACE INTO {DatabaseTables.TIMELINE_EVENTS} 
                (year, month, day, content, categories, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (event.year, event.month, event.day, event.content, event.categories))
            
            event_id = cursor.lastrowid
            conn.commit()
            
            logger.debug(f"イベント追加: {event}")
            return event_id or 0
    
    def add_events_batch(self, events: List[TimelineEvent]) -> Tuple[int, int]:
        """
        複数イベントの一括追加
        
        Args:
            events: 追加するイベントのリスト
            
        Returns:
            (追加数, 更新数) のタプル
        """
        if not events:
            return 0, 0
        
        added_count = 0
        updated_count = 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for event in events:
                # 既存チェック
                cursor.execute(f'''
                    SELECT event_id FROM {DatabaseTables.TIMELINE_EVENTS} 
                    WHERE year = ? AND month = ? AND day = ? AND content = ?
                ''', (event.year, event.month, event.day, event.content))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新
                    cursor.execute(f'''
                        UPDATE {DatabaseTables.TIMELINE_EVENTS} 
                        SET categories = ?, html_content = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE event_id = ?
                    ''', (event.categories, event.html_content, existing['event_id']))
                    updated_count += 1
                else:
                    # 新規追加
                    cursor.execute(f'''
                        INSERT INTO {DatabaseTables.TIMELINE_EVENTS} 
                        (year, month, day, content, categories, html_content)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (event.year, event.month, event.day, event.content, event.categories, event.html_content))
                    added_count += 1
            
            conn.commit()
            logger.info(f"一括処理完了 - 追加: {added_count}, 更新: {updated_count}")
            
            return added_count, updated_count
    
    def get_events_by_date(self, month: int, day: int) -> List[TimelineEvent]:
        """
        指定日付のイベントを取得
        
        Args:
            month: 月 (1-12)
            day: 日 (1-31)
            
        Returns:
            該当するイベントのリスト（年代順）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE month = ? AND day = ?
                ORDER BY year ASC
            ''', (month, day))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                event = TimelineEvent(
                    event_id=row['event_id'],
                    year=row['year'],
                    month=row['month'],
                    day=row['day'],
                    content=row['content'],
                    categories=row['categories'],
                    html_content=row['html_content']
                )
                # データベースから取得した時刻を設定
                if row['created_at']:
                    event.created_at = datetime.fromisoformat(row['created_at'])
                if row['updated_at']:
                    event.updated_at = datetime.fromisoformat(row['updated_at'])
                
                events.append(event)
            
            logger.debug(f"{month:02d}月{day:02d}日のイベント: {len(events)}件")
            return events
    
    def get_events_by_today(self) -> List[TimelineEvent]:
        """今日の日付のイベントを取得"""
        today = date.today()
        return self.get_events_by_date(today.month, today.day)
    
    def search_events(self, keyword: str, limit: int = 50) -> List[TimelineEvent]:
        """
        キーワードでイベントを検索
        
        Args:
            keyword: 検索キーワード
            limit: 最大取得件数
            
        Returns:
            検索結果のイベントリスト
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 部分一致検索
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE content LIKE ?
                ORDER BY year ASC, month ASC, day ASC
                LIMIT ?
            ''', (f'%{keyword}%', limit))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                event = TimelineEvent(
                    event_id=row['event_id'],
                    year=row['year'],
                    month=row['month'],
                    day=row['day'],
                    content=row['content'],
                    categories=row['categories'],
                    html_content=row['html_content']
                )
                events.append(event)
            
            logger.debug(f"キーワード検索 '{keyword}': {len(events)}件")
            return events
    
    def get_events_by_year_range(self, start_year: int, end_year: int) -> List[TimelineEvent]:
        """
        指定年代範囲のイベントを取得
        
        Args:
            start_year: 開始年
            end_year: 終了年
            
        Returns:
            該当するイベントのリスト
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE year BETWEEN ? AND ?
                ORDER BY year ASC, month ASC, day ASC
            ''', (start_year, end_year))
            
            rows = cursor.fetchall()
            events = [TimelineEvent(
                event_id=row['event_id'],
                year=row['year'],
                month=row['month'],
                day=row['day'],
                content=row['content'],
                categories=row['categories'],
                html_content=row['html_content']
            ) for row in rows]
            
            logger.debug(f"{start_year}-{end_year}年のイベント: {len(events)}件")
            return events
    
    def get_events_by_categories(self, categories: List[str], exclude_categories: Optional[List[str]] = None, 
                                limit: int = 100) -> List[TimelineEvent]:
        """
        複合カテゴリ条件でイベントを取得
        
        Args:
            categories: 含めるカテゴリのリスト
            exclude_categories: 除外するカテゴリのリスト（オプション）
            limit: 最大取得件数
            
        Returns:
            該当するイベントのリスト
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # カテゴリ正規化（ハイフン除去、小文字化）
            normalized_categories = [cat.replace('-', '').lower() for cat in categories]
            normalized_exclude = [cat.replace('-', '').lower() for cat in (exclude_categories or [])]
            
            # SQLクエリ構築
            query_parts = []
            params = []
            
            # 含めるカテゴリの条件（AND条件：全てのカテゴリを含む）
            if normalized_categories:
                category_conditions = []
                for cat in normalized_categories:
                    category_conditions.append("LOWER(REPLACE(categories, '-', '')) LIKE ?")
                    params.append(f'%{cat}%')
                query_parts.append(f"({' AND '.join(category_conditions)})")
            
            # 除外カテゴリの条件
            if normalized_exclude:
                exclude_conditions = []
                for cat in normalized_exclude:
                    exclude_conditions.append("LOWER(REPLACE(categories, '-', '')) NOT LIKE ?")
                    params.append(f'%{cat}%')
                query_parts.append(f"({' AND '.join(exclude_conditions)})")
            
            # クエリ組み立て
            # 空のカテゴリリストの場合は0件を返す
            if not normalized_categories and not normalized_exclude:
                return []
            
            where_clause = " AND ".join(query_parts) if query_parts else "1=1"
            params.append(limit)
            
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE {where_clause}
                ORDER BY year ASC, month ASC, day ASC
                LIMIT ?
            ''', params)
            
            rows = cursor.fetchall()
            events = [TimelineEvent(
                event_id=row['event_id'],
                year=row['year'],
                month=row['month'],
                day=row['day'],
                content=row['content'],
                categories=row['categories'],
                html_content=row['html_content']
            ) for row in rows]
            
            # 厳密なカテゴリ一致フィルタ（AND条件）
            if normalized_categories:
                def has_all_categories(ev):
                    cats = [c.strip() for c in (ev.categories or '').split()]
                    return all(cat in cats for cat in normalized_categories)
                events = [ev for ev in events if has_all_categories(ev)]
            
            # 除外カテゴリも厳密に
            if normalized_exclude:
                def has_excluded(ev):
                    cats = [c.strip() for c in (ev.categories or '').split()]
                    return any(cat in cats for cat in normalized_exclude)
                events = [ev for ev in events if not has_excluded(ev)]
            
            logger.debug(f"カテゴリ検索 '{categories}' (除外: {exclude_categories}): {len(events)}件")
            return events
    
    def _check_categories(self, event: TimelineEvent, categories: List[str], 
                         exclude_categories: Optional[List[str]] = None) -> bool:
        """
        イベントのカテゴリが指定条件に一致するかチェック
        
        Args:
            event: イベントオブジェクト
            categories: 含めるカテゴリリスト
            exclude_categories: 除外するカテゴリリスト（オプション）
            
        Returns:
            bool: 条件に一致する場合True
        """
        try:
            # カテゴリ正規化
            normalized_categories = [cat.replace('-', '').lower() for cat in categories if cat.strip()]
            normalized_exclude = []
            if exclude_categories:
                normalized_exclude = [cat.replace('-', '').lower() for cat in exclude_categories if cat.strip()]
            
            # イベントのカテゴリを取得
            event_categories = []
            if event.categories:
                event_categories = [cat.strip() for cat in event.categories.split()]
            
            # 含めるカテゴリチェック（AND条件）
            if normalized_categories:
                event_cats_normalized = [cat.replace('-', '').lower() for cat in event_categories]
                if not all(cat in event_cats_normalized for cat in normalized_categories):
                    return False
            
            # 除外カテゴリチェック
            if normalized_exclude:
                event_cats_normalized = [cat.replace('-', '').lower() for cat in event_categories]
                if any(cat in event_cats_normalized for cat in normalized_exclude):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"カテゴリチェックエラー: {e}")
            return False
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """
        カテゴリ統計情報を取得
        
        Returns:
            カテゴリ統計情報の辞書
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 全カテゴリの取得と正規化
            cursor.execute(f'''
                SELECT categories FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE categories != '' AND categories IS NOT NULL
            ''')
            
            all_categories = []
            for row in cursor.fetchall():
                if row['categories']:
                    # スペース区切りでカテゴリを分割
                    event_categories = row['categories'].split()
                    for cat in event_categories:
                        # 正規化（ハイフン除去、小文字化）
                        normalized_cat = cat.replace('-', '').lower()
                        all_categories.append(normalized_cat)
            
            # カテゴリ別カウント
            category_counts = {}
            for cat in all_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # 年代別カテゴリ分布
            cursor.execute(f'''
                SELECT year, categories FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE categories != '' AND categories IS NOT NULL
                ORDER BY year
            ''')
            
            decade_category_counts = {
                '1920s': {},
                '1930s': {},
                '1940s': {},
                '1950s': {},
                '1960s': {},
                '1970s': {},
                '1980s': {},
                '1990s': {},
                '2000s': {},
                '2010s': {},
                '2020s': {}
            }
            
            for row in cursor.fetchall():
                year = row['year']
                categories = row['categories'].split()
                
                # 年代判定
                if 1920 <= year <= 1929:
                    decade = '1920s'
                elif 1930 <= year <= 1939:
                    decade = '1930s'
                elif 1940 <= year <= 1949:
                    decade = '1940s'
                elif 1950 <= year <= 1959:
                    decade = '1950s'
                elif 1960 <= year <= 1969:
                    decade = '1960s'
                elif 1970 <= year <= 1979:
                    decade = '1970s'
                elif 1980 <= year <= 1989:
                    decade = '1980s'
                elif 1990 <= year <= 1999:
                    decade = '1990s'
                elif 2000 <= year <= 2009:
                    decade = '2000s'
                elif 2010 <= year <= 2019:
                    decade = '2010s'
                elif 2020 <= year <= 2029:
                    decade = '2020s'
                else:
                    continue
                
                # カテゴリカウント
                for cat in categories:
                    normalized_cat = cat.replace('-', '').lower()
                    if decade in decade_category_counts:
                        decade_category_counts[decade][normalized_cat] = \
                            decade_category_counts[decade].get(normalized_cat, 0) + 1
            
            # 人気カテゴリ（上位10個）
            popular_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_categories': len(category_counts),
                'category_counts': category_counts,
                'popular_categories': popular_categories,
                'decade_distribution': decade_category_counts,
                'total_events_with_categories': len(all_categories)
            }
    
    def get_available_categories(self) -> List[str]:
        """
        利用可能なカテゴリ一覧を取得
        
        Returns:
            カテゴリ名のリスト（正規化済み）
        """
        stats = self.get_category_statistics()
        return list(stats['category_counts'].keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """データベース統計情報を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 総イベント数
            cursor.execute(f'SELECT COUNT(*) as total FROM {DatabaseTables.TIMELINE_EVENTS}')
            total_events = cursor.fetchone()['total']
            
            # 年代範囲
            cursor.execute(f'''
                SELECT MIN(year) as min_year, MAX(year) as max_year 
                FROM {DatabaseTables.TIMELINE_EVENTS}
            ''')
            year_range = cursor.fetchone()
            
            # 月別統計
            cursor.execute(f'''
                SELECT month, COUNT(*) as count 
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                GROUP BY month 
                ORDER BY month
            ''')
            monthly_stats = {row['month']: row['count'] for row in cursor.fetchall()}
            
            # 最新更新時刻
            cursor.execute(f'''
                SELECT MAX(updated_at) as last_update 
                FROM {DatabaseTables.TIMELINE_EVENTS}
            ''')
            last_update = cursor.fetchone()['last_update']
            
            return {
                'total_events': total_events,
                'year_range': {
                    'min': year_range['min_year'],
                    'max': year_range['max_year']
                },
                'monthly_distribution': monthly_stats,
                'last_update': last_update,
                'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
    
    def get_decade_statistics(self, start_year: int, end_year: int) -> Dict[str, Any]:
        """年代別統計情報を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 総イベント数
            cursor.execute(f'''
                SELECT COUNT(*) as total 
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE year BETWEEN ? AND ?
            ''', (start_year, end_year))
            total_events = cursor.fetchone()['total']
            
            # 年別イベント数
            cursor.execute(f'''
                SELECT year, COUNT(*) as count 
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                WHERE year BETWEEN ? AND ?
                GROUP BY year 
                ORDER BY year
            ''', (start_year, end_year))
            
            year_stats = {row['year']: row['count'] for row in cursor.fetchall()}
            
            # 統計計算
            if year_stats:
                avg_per_year = total_events / (end_year - start_year + 1)
                max_year = max(year_stats.items(), key=lambda x: x[1])
                min_year = min(year_stats.items(), key=lambda x: x[1])
            else:
                avg_per_year = 0
                max_year = (start_year, 0)
                min_year = (start_year, 0)
            
            return {
                'total_events': total_events,
                'avg_per_year': avg_per_year,
                'max_year': max_year,
                'min_year': min_year,
                'year_distribution': year_stats
            }
    
    def get_events_by_decade_and_categories(self, start_year: int, end_year: int, 
                                          categories: List[str], 
                                          exclude_categories: Optional[List[str]] = None,
                                          limit: int = 100) -> List[TimelineEvent]:
        """
        年代別＋カテゴリ複合検索
        
        Args:
            start_year: 開始年
            end_year: 終了年
            categories: 含めるカテゴリリスト
            exclude_categories: 除外するカテゴリリスト（オプション）
            limit: 取得件数制限
            
        Returns:
            イベントリスト
        """
        try:
            # 空のカテゴリリストの場合は0件返す
            if not categories:
                return []
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 基本クエリ：年代範囲で絞り込み
                query = f'''
                    SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                    WHERE year BETWEEN ? AND ?
                '''
                params = [start_year, end_year]
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # カテゴリフィルタリング
                filtered_events = []
                
                for row in rows:
                    event = TimelineEvent(
                        event_id=row['event_id'],
                        year=row['year'],
                        month=row['month'],
                        day=row['day'],
                        content=row['content'],
                        categories=row['categories'],
                        html_content=row['html_content']
                    )
                    
                    # カテゴリチェック
                    if self._check_categories(event, categories, exclude_categories):
                        filtered_events.append(event)
                        if len(filtered_events) >= limit:
                            break
                
                # 時系列順にソート
                filtered_events.sort(key=lambda event: (event.year, event.month, event.day))
                
                logger.info(f"年代別＋カテゴリ検索完了: {start_year}-{end_year}, カテゴリ={categories}, 除外={exclude_categories}, 結果={len(filtered_events)}件")
                return filtered_events
                
        except Exception as e:
            logger.error(f"年代別＋カテゴリ検索エラー: {e}")
            return []
    
    def get_decade_category_statistics(self, start_year: int, end_year: int) -> Dict[str, Any]:
        """
        年代別カテゴリ統計を取得
        
        Args:
            start_year: 開始年
            end_year: 終了年
            
        Returns:
            カテゴリ統計情報
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 年代範囲内の全イベントを取得
                cursor.execute(f'''
                    SELECT categories FROM {DatabaseTables.TIMELINE_EVENTS} 
                    WHERE year BETWEEN ? AND ? AND categories IS NOT NULL AND categories != ''
                ''', (start_year, end_year))
                
                rows = cursor.fetchall()
                
                # カテゴリ統計
                category_counts = {}
                total_events = 0
                
                for row in rows:
                    if row['categories']:
                        categories = row['categories'].split()
                        for category in categories:
                            category = category.lower().strip()
                            if category:
                                category_counts[category] = category_counts.get(category, 0) + 1
                        total_events += 1
                
                # カテゴリ別統計
                category_stats = []
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_events * 100) if total_events > 0 else 0
                    category_stats.append({
                        'category': category,
                        'count': count,
                        'percentage': round(percentage, 1)
                    })
                
                return {
                    'total_events': total_events,
                    'unique_categories': len(category_counts),
                    'category_distribution': category_stats,
                    'top_categories': category_stats[:10]  # 上位10カテゴリ
                }
                
        except Exception as e:
            logger.error(f"年代別カテゴリ統計取得エラー: {e}")
            return {
                'total_events': 0,
                'unique_categories': 0,
                'category_distribution': [],
                'top_categories': []
            }
    
    def record_update_history(self, added_count: int, updated_count: int, 
                            total_count: int, source_url: str, 
                            status: str = 'success', notes: str = ''):
        """データ更新履歴を記録"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                INSERT INTO {DatabaseTables.UPDATE_HISTORY} 
                (events_added, events_updated, events_total, source_url, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (added_count, updated_count, total_count, source_url, status, notes))
            
            conn.commit()
            logger.info(f"更新履歴記録: +{added_count}, ^{updated_count}, total={total_count}")
    
    def get_update_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """データ更新履歴を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.UPDATE_HISTORY} 
                ORDER BY update_time DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_oldest_event(self) -> str:
        """最古のイベントを取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT year, month, day, content 
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                ORDER BY year ASC, month ASC, day ASC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return f"{row['year']}年{row['month']}月{row['day']}日: {row['content'][:50]}..."
            else:
                return "N/A"
    
    def get_newest_event(self) -> str:
        """最新のイベントを取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT year, month, day, content 
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                ORDER BY year DESC, month DESC, day DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return f"{row['year']}年{row['month']}月{row['day']}日: {row['content'][:50]}..."
            else:
                return "N/A"
    
    def get_decade_distribution(self) -> str:
        """年代別分布を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT 
                    (year / 10) * 10 as decade,
                    COUNT(*) as count
                FROM {DatabaseTables.TIMELINE_EVENTS} 
                GROUP BY (year / 10) * 10
                ORDER BY decade
            ''')
            
            rows = cursor.fetchall()
            if rows:
                distribution = []
                for row in rows:
                    decade = int(row['decade'])
                    count = row['count']
                    distribution.append(f"{decade}年代: {count}件")
                return ", ".join(distribution)
            else:
                return "N/A"
    
    def get_last_update_info(self) -> Dict[str, Any]:
        """最終更新情報を取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 最新の更新履歴
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.UPDATE_HISTORY} 
                ORDER BY update_time DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return {
                    'last_update': row['update_time'],
                    'result': row['status'],
                    'last_fetch': row['update_time'],  # 更新時刻を取得時刻として使用
                    'fetch_result': row['status'],
                    'added_count': row['events_added'],
                    'updated_count': row['events_updated'],
                    'total_count': row['events_total']
                }
            else:
                return {
                    'last_update': 'N/A',
                    'result': 'N/A',
                    'last_fetch': 'N/A',
                    'fetch_result': 'N/A',
                    'added_count': 0,
                    'updated_count': 0,
                    'total_count': 0
                }
    
    def clear_all_events(self):
        """全イベントデータを削除（開発・テスト用）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {DatabaseTables.TIMELINE_EVENTS}')
            cursor.execute(f'DELETE FROM {DatabaseTables.UPDATE_HISTORY}')
            conn.commit()
            logger.warning("全イベントデータを削除しました")
    
    def export_events_json(self, output_path: Path) -> int:
        """
        イベントデータをJSONファイルにエクスポート
        
        Args:
            output_path: 出力ファイルパス
            
        Returns:
            エクスポートしたイベント数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT * FROM {DatabaseTables.TIMELINE_EVENTS} 
                ORDER BY year, month, day
            ''')
            
            rows = cursor.fetchall()
            events_data = []
            
            for row in rows:
                event = TimelineEvent(
                    event_id=row['event_id'],
                    year=row['year'],
                    month=row['month'],
                    day=row['day'],
                    content=row['content'],
                    categories=row['categories'],
                    html_content=row['html_content']
                )
                events_data.append(event.to_dict())
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_time': datetime.now().isoformat(),
                    'total_events': len(events_data),
                    'events': events_data
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"データエクスポート完了: {len(events_data)}件 -> {output_path}")
            return len(events_data)
    
    def __str__(self) -> str:
        """データベース情報の文字列表現"""
        stats = self.get_statistics()
        return (f"TimelineDatabase({self.db_path})\n"
                f"  Events: {stats['total_events']}\n"
                f"  Years: {stats['year_range']['min']}-{stats['year_range']['max']}\n"
                f"  Size: {stats['database_size_mb']:.2f}MB")

    def get_cooccurring_categories(self, categories: List[str], exclude_categories: Optional[List[str]] = None, limit: int = 20) -> Dict[str, int]:
        """
        指定カテゴリと共起するカテゴリの頻度を集計
        Args:
            categories: AND条件で含めるカテゴリリスト
            exclude_categories: 除外カテゴリリスト
            limit: 上位何件まで返すか
        Returns:
            共起カテゴリの頻度辞書（指定カテゴリ自身は除外）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # カテゴリ正規化
            normalized_categories = [cat.replace('-', '').lower() for cat in categories if cat.strip()]
            normalized_exclude = [cat.replace('-', '').lower() for cat in (exclude_categories or []) if cat.strip()]

            # SQLクエリ構築
            query_parts = []
            params = []
            if normalized_categories:
                category_conditions = []
                for cat in normalized_categories:
                    category_conditions.append("LOWER(REPLACE(categories, '-', '')) LIKE ?")
                    params.append(f'%{cat}%')
                query_parts.append(f"({' AND '.join(category_conditions)})")
            if normalized_exclude:
                exclude_conditions = []
                for cat in normalized_exclude:
                    exclude_conditions.append("LOWER(REPLACE(categories, '-', '')) NOT LIKE ?")
                    params.append(f'%{cat}%')
                query_parts.append(f"({' AND '.join(exclude_conditions)})")
            if not normalized_categories and not normalized_exclude:
                return {}
            where_clause = " AND ".join(query_parts) if query_parts else "1=1"
            cursor.execute(f'''
                SELECT categories FROM {DatabaseTables.TIMELINE_EVENTS}
                WHERE {where_clause}
            ''', params)
            rows = cursor.fetchall()
            cooccur_counts = {}
            for row in rows:
                if row['categories']:
                    event_cats = [cat.replace('-', '').lower() for cat in row['categories'].split()]
                    # 指定カテゴリ自身は除外
                    for cat in event_cats:
                        if cat not in normalized_categories and cat not in normalized_exclude:
                            cooccur_counts[cat] = cooccur_counts.get(cat, 0) + 1
            # 上位limit件のみ返す
            sorted_counts = dict(sorted(cooccur_counts.items(), key=lambda x: x[1], reverse=True)[:limit])
            return sorted_counts


# テスト用関数
def test_database():
    """データベース機能のテスト"""
    import tempfile
    
    print("=== データベース機能テスト ===")
    
    # テンポラリファイルでテスト
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db_path = Path(tmp.name)
    
    try:
        # データベース初期化
        db = TimelineDatabase(test_db_path)
        print("✅ データベース初期化成功")
        
        # テストイベント追加
        test_events = [
            TimelineEvent(2023, 5, 1, "テストイベント1", "test"),
            TimelineEvent(2023, 5, 1, "テストイベント2", "test"),
            TimelineEvent(2024, 12, 25, "クリスマステスト", "holiday")
        ]
        
        added, updated = db.add_events_batch(test_events)
        print(f"✅ イベント一括追加: {added}件追加, {updated}件更新")
        
        # 日付検索テスト
        events = db.get_events_by_date(5, 1)
        print(f"✅ 日付検索: 5月1日に{len(events)}件のイベント")
        
        # キーワード検索テスト
        results = db.search_events("テスト")
        print(f"✅ キーワード検索: 'テスト'で{len(results)}件")
        
        # 統計情報
        stats = db.get_statistics()
        print(f"✅ 統計情報: {stats['total_events']}件のイベント")
        
        print("✅ 全テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False
    finally:
        # クリーンアップ
        if test_db_path.exists():
            test_db_path.unlink()


if __name__ == "__main__":
    test_database()
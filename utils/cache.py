"""
キャッシュ機能ユーティリティ

メモリベースのキャッシュ、LRUキャッシュ、TTLキャッシュなどの
キャッシュ機能を提供します。
"""

import time
import logging
from typing import Any, Optional, Dict, List, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class LRUCache:
    """LRU（Least Recently Used）キャッシュ"""
    
    def __init__(self, max_size: int = 100):
        """
        LRUキャッシュの初期化
        
        Args:
            max_size: キャッシュの最大サイズ
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから値を取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            Any: キャッシュされた値、存在しない場合はNone
        """
        if key in self.cache:
            # アクセス時間を更新
            self.access_times[key] = time.time()
            # 順序を更新（最新アクセスを最後に）
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        キャッシュに値を設定
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
        """
        if key in self.cache:
            # 既存のキーの場合、順序を更新
            self.cache.move_to_end(key)
        else:
            # 新しいキーの場合、サイズ制限をチェック
            if len(self.cache) >= self.max_size:
                # 最も古いキーを削除
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """
        キャッシュからキーを削除
        
        Args:
            key: 削除するキー
            
        Returns:
            bool: 削除成功時True
        """
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            return True
        return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
        self.access_times.clear()
    
    def size(self) -> int:
        """キャッシュサイズを取得"""
        return len(self.cache)
    
    def keys(self) -> List[str]:
        """キャッシュキーのリストを取得"""
        return list(self.cache.keys())

class TTLCache:
    """TTL（Time To Live）キャッシュ"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        TTLキャッシュの初期化
        
        Args:
            default_ttl: デフォルトのTTL（秒）
        """
        self.default_ttl = default_ttl
        self.cache = {}
        self.expiry_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから値を取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            Any: キャッシュされた値、存在しないか期限切れの場合はNone
        """
        if key in self.cache:
            # 期限切れチェック
            if time.time() > self.expiry_times[key]:
                # 期限切れの場合は削除
                self.delete(key)
                return None
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        キャッシュに値を設定
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
            ttl: TTL（秒）、Noneの場合はデフォルト値を使用
        """
        ttl = ttl or self.default_ttl
        self.cache[key] = value
        self.expiry_times[key] = time.time() + ttl
    
    def delete(self, key: str) -> bool:
        """
        キャッシュからキーを削除
        
        Args:
            key: 削除するキー
            
        Returns:
            bool: 削除成功時True
        """
        if key in self.cache:
            del self.cache[key]
            del self.expiry_times[key]
            return True
        return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
        self.expiry_times.clear()
    
    def cleanup_expired(self) -> int:
        """
        期限切れのエントリを削除
        
        Returns:
            int: 削除されたエントリ数
        """
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self.expiry_times.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self.delete(key)
        
        return len(expired_keys)
    
    def size(self) -> int:
        """キャッシュサイズを取得"""
        return len(self.cache)

class CacheManager:
    """統合キャッシュマネージャー"""
    
    def __init__(self):
        """キャッシュマネージャーの初期化"""
        self.lru_cache = LRUCache(max_size=1000)
        self.ttl_cache = TTLCache(default_ttl=3600)
        self.stats = {
            'lru_hits': 0,
            'lru_misses': 0,
            'ttl_hits': 0,
            'ttl_misses': 0,
        }
    
    def get(self, key: str, cache_type: str = 'lru') -> Optional[Any]:
        """
        キャッシュから値を取得
        
        Args:
            key: キャッシュキー
            cache_type: キャッシュタイプ（'lru' または 'ttl'）
            
        Returns:
            Any: キャッシュされた値
        """
        if cache_type == 'lru':
            value = self.lru_cache.get(key)
            if value is not None:
                self.stats['lru_hits'] += 1
            else:
                self.stats['lru_misses'] += 1
            return value
        elif cache_type == 'ttl':
            value = self.ttl_cache.get(key)
            if value is not None:
                self.stats['ttl_hits'] += 1
            else:
                self.stats['ttl_misses'] += 1
            return value
        else:
            raise ValueError(f"不明なキャッシュタイプ: {cache_type}")
    
    def set(self, key: str, value: Any, cache_type: str = 'lru', ttl: Optional[int] = None) -> None:
        """
        キャッシュに値を設定
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
            cache_type: キャッシュタイプ（'lru' または 'ttl'）
            ttl: TTL（秒）、TTLキャッシュでのみ使用
        """
        if cache_type == 'lru':
            self.lru_cache.set(key, value)
        elif cache_type == 'ttl':
            self.ttl_cache.set(key, value, ttl)
        else:
            raise ValueError(f"不明なキャッシュタイプ: {cache_type}")
    
    def delete(self, key: str, cache_type: str = 'lru') -> bool:
        """
        キャッシュからキーを削除
        
        Args:
            key: 削除するキー
            cache_type: キャッシュタイプ（'lru' または 'ttl'）
            
        Returns:
            bool: 削除成功時True
        """
        if cache_type == 'lru':
            return self.lru_cache.delete(key)
        elif cache_type == 'ttl':
            return self.ttl_cache.delete(key)
        else:
            raise ValueError(f"不明なキャッシュタイプ: {cache_type}")
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """
        キャッシュをクリア
        
        Args:
            cache_type: キャッシュタイプ、Noneの場合は両方クリア
        """
        if cache_type is None:
            self.lru_cache.clear()
            self.ttl_cache.clear()
        elif cache_type == 'lru':
            self.lru_cache.clear()
        elif cache_type == 'ttl':
            self.ttl_cache.clear()
        else:
            raise ValueError(f"不明なキャッシュタイプ: {cache_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得
        
        Returns:
            Dict: キャッシュ統計
        """
        lru_hit_rate = 0
        ttl_hit_rate = 0
        
        if self.stats['lru_hits'] + self.stats['lru_misses'] > 0:
            lru_hit_rate = self.stats['lru_hits'] / (self.stats['lru_hits'] + self.stats['lru_misses'])
        
        if self.stats['ttl_hits'] + self.stats['ttl_misses'] > 0:
            ttl_hit_rate = self.stats['ttl_hits'] / (self.stats['ttl_hits'] + self.stats['ttl_misses'])
        
        return {
            'lru_cache': {
                'size': self.lru_cache.size(),
                'hits': self.stats['lru_hits'],
                'misses': self.stats['lru_misses'],
                'hit_rate': f"{lru_hit_rate:.2%}",
            },
            'ttl_cache': {
                'size': self.ttl_cache.size(),
                'hits': self.stats['ttl_hits'],
                'misses': self.stats['ttl_misses'],
                'hit_rate': f"{ttl_hit_rate:.2%}",
            },
        }
    
    def cleanup(self) -> None:
        """キャッシュのクリーンアップ"""
        self.ttl_cache.cleanup_expired()

# グローバルインスタンス
cache_manager = CacheManager()

def cached(cache_type: str = 'lru', ttl: Optional[int] = None, key_prefix: str = ''):
    """
    関数結果をキャッシュするデコレータ
    
    Args:
        cache_type: キャッシュタイプ（'lru' または 'ttl'）
        ttl: TTL（秒）、TTLキャッシュでのみ使用
        key_prefix: キャッシュキーのプレフィックス
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキーの生成
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"キャッシュヒット: {cache_key}")
                return cached_result
            
            # 関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            cache_manager.set(cache_key, result, cache_type, ttl)
            logger.debug(f"キャッシュ保存: {cache_key}")
            
            return result
        return wrapper
    return decorator 
"""
LLMサービス - Ollama API連携
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMService:
    """Ollama APIとの連携を管理するサービス"""
    
    def __init__(self, config):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.api_url = getattr(config, 'llm_api_url', 'http://localhost:11434')
        self.model = getattr(config, 'llm_model', 'dsns')
        self.timeout = getattr(config, 'llm_timeout', 30)
        self.enabled = getattr(config, 'llm_enabled', False)
        
        # 統計情報
        self.stats = {
            'total_calls': 0,
            'success_calls': 0,
            'failed_calls': 0,
            'total_response_time': 0.0
        }
        
        logger.info(f"LLMサービス初期化: model={self.model}, enabled={self.enabled}")
    
    def is_enabled(self) -> bool:
        """LLM機能が有効かチェック"""
        return self.enabled
    
    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """
        LLMでテキスト生成
        
        Args:
            prompt: プロンプト
            system: システムプロンプト（オプション）
            
        Returns:
            生成されたテキスト、失敗時はNone
        """
        if not self.enabled:
            logger.warning("LLM機能が無効です")
            return None
        
        self.stats['total_calls'] += 1
        
        try:
            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': False
            }
            
            if system:
                payload['system'] = system
            
            logger.debug(f"LLM API呼び出し: model={self.model}, prompt_len={len(prompt)}")
            
            import time
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            self.stats['total_response_time'] += elapsed
            
            response.raise_for_status()
            data = response.json()
            
            # responseフィールドのみを使用（thinkingは無視）
            result = data.get('response', '').strip()
            
            if result:
                self.stats['success_calls'] += 1
                logger.info(f"LLM生成成功: {len(result)}文字, {elapsed:.2f}秒")
                return result
            else:
                self.stats['failed_calls'] += 1
                logger.warning("LLM応答が空です")
                return None
                
        except requests.Timeout:
            self.stats['failed_calls'] += 1
            logger.error(f"LLM APIタイムアウト: {self.timeout}秒")
            return None
            
        except Exception as e:
            self.stats['failed_calls'] += 1
            logger.error(f"LLM生成エラー: {e}", exc_info=True)
            return None
    
    def health_check(self) -> bool:
        """
        Ollama APIの疎通確認
        
        Returns:
            接続可能ならTrue
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            # モデルリストを取得
            models = data.get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            if self.model in model_names:
                logger.info(f"ヘルスチェック成功: モデル'{self.model}'が利用可能")
                return True
            else:
                logger.warning(f"モデル'{self.model}'が見つかりません。利用可能: {model_names}")
                return False
                
        except Exception as e:
            logger.error(f"ヘルスチェック失敗: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            統計情報の辞書
        """
        avg_response_time = 0.0
        if self.stats['success_calls'] > 0:
            avg_response_time = self.stats['total_response_time'] / self.stats['success_calls']
        
        success_rate = 0.0
        if self.stats['total_calls'] > 0:
            success_rate = self.stats['success_calls'] / self.stats['total_calls'] * 100
        
        return {
            **self.stats,
            'avg_response_time': avg_response_time,
            'success_rate': success_rate,
            'model': self.model,
            'enabled': self.enabled
        }

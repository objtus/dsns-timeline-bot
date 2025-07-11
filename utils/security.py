"""
セキュリティ機能ユーティリティ

機密情報の暗号化、ログフィルタリング、入力検証などの
セキュリティ機能を提供します。
"""

import re
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("警告: cryptographyライブラリがインストールされていません。暗号化機能は無効です。")

class SecurityManager:
    """セキュリティ管理クラス"""
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        セキュリティマネージャーの初期化
        
        Args:
            key_file: 暗号化キーファイルのパス
        """
        self.key_file = key_file or Path("data/.secret_key")
        self._setup_encryption()
        self._setup_log_filtering()
    
    def _setup_encryption(self):
        """暗号化機能の初期化"""
        if not CRYPTOGRAPHY_AVAILABLE:
            self.fernet = None
            return
        
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            
            self.fernet = Fernet(key)
        except Exception as e:
            logging.error(f"暗号化初期化エラー: {e}")
            self.fernet = None
    
    def _setup_log_filtering(self):
        """ログフィルタリングの設定"""
        # 機密情報のパターン
        self.sensitive_patterns = [
            r'MISSKEY_TOKEN\s*=\s*[^\s]+',
            r'password\s*=\s*[^\s]+',
            r'secret\s*=\s*[^\s]+',
            r'token\s*=\s*[^\s]+',
        ]
        
        # ログフィルターを設定
        logging.getLogger().addFilter(self._log_filter)
    
    def _log_filter(self, record):
        """ログメッセージから機密情報を除去"""
        if hasattr(record, 'msg'):
            record.msg = self._sanitize_message(record.msg)
        if hasattr(record, 'args'):
            record.args = tuple(self._sanitize_message(str(arg)) for arg in record.args)
        return True
    
    def _sanitize_message(self, message: str) -> str:
        """メッセージから機密情報を除去"""
        for pattern in self.sensitive_patterns:
            message = re.sub(pattern, r'\1=***', message, flags=re.IGNORECASE)
        return message
    
    def encrypt_token(self, token: str) -> str:
        """
        トークンを暗号化
        
        Args:
            token: 暗号化するトークン
            
        Returns:
            str: 暗号化されたトークン
        """
        if not self.fernet:
            return token
        
        try:
            encrypted = self.fernet.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            logging.error(f"トークン暗号化エラー: {e}")
            return token
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        トークンを復号化
        
        Args:
            encrypted_token: 復号化するトークン
            
        Returns:
            str: 復号化されたトークン
        """
        if not self.fernet:
            return encrypted_token
        
        try:
            decrypted = self.fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            logging.error(f"トークン復号化エラー: {e}")
            return encrypted_token
    
    def validate_input(self, text: str, max_length: int = 1000) -> bool:
        """
        ユーザー入力の検証
        
        Args:
            text: 検証するテキスト
            max_length: 最大文字数
            
        Returns:
            bool: 検証結果
        """
        if not text or len(text) > max_length:
            return False
        
        # 危険な文字パターンをチェック
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """
        ファイル名のサニタイゼーション
        
        Args:
            filename: サニタイゼーションするファイル名
            
        Returns:
            str: サニタイゼーションされたファイル名
        """
        # 危険な文字を除去
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 連続するアンダースコアを単一に
        sanitized = re.sub(r'_+', '_', sanitized)
        # 先頭末尾のアンダースコアを除去
        sanitized = sanitized.strip('_')
        
        return sanitized or 'unnamed'
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        セキュアなトークンを生成
        
        Args:
            length: トークンの長さ
            
        Returns:
            str: 生成されたトークン
        """
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """
        パスワードのハッシュ化
        
        Args:
            password: ハッシュ化するパスワード
            
        Returns:
            str: ハッシュ化されたパスワード
        """
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        パスワードの検証
        
        Args:
            password: 検証するパスワード
            hashed: ハッシュ化されたパスワード
            
        Returns:
            bool: 検証結果
        """
        try:
            salt, hash_hex = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_obj.hex() == hash_hex
        except Exception:
            return False

# グローバルインスタンス
security_manager = SecurityManager() 
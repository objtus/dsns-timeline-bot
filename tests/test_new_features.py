#!/usr/bin/env python3
"""
新機能の統合テスト

セキュリティ、キャッシュ、アラート機能の
統合テストを実行します。
"""

import pytest
import asyncio
from utils.security import security_manager
from utils.cache import cache_manager, cached
from utils.alert import alert_manager, AlertSeverity

def test_security_features():
    """セキュリティ機能のテスト"""
    
    # トークン暗号化テスト
    test_token = "test_secret_token_123"
    encrypted = security_manager.encrypt_token(test_token)
    decrypted = security_manager.decrypt_token(encrypted)
    
    assert decrypted == test_token, "トークンの暗号化・復号化が失敗しました"
    
    # 入力検証テスト
    valid_input = "正常なテキスト"
    invalid_input = "<script>alert('xss')</script>"
    
    assert security_manager.validate_input(valid_input), "正常な入力が拒否されました"
    assert not security_manager.validate_input(invalid_input), "危険な入力が許可されました"
    
    # ファイル名サニタイゼーションテスト
    dangerous_filename = "file<>:\"/\\|?*.txt"
    sanitized = security_manager.sanitize_filename(dangerous_filename)
    
    assert "<" not in sanitized, "危険な文字が残っています"
    assert ">" not in sanitized, "危険な文字が残っています"
    assert ":" not in sanitized, "危険な文字が残っています"

def test_cache_features():
    """キャッシュ機能のテスト"""
    
    # LRUキャッシュテスト
    cache_manager.set("test_key", "test_value", "lru")
    value = cache_manager.get("test_key", "lru")
    
    assert value == "test_value", "LRUキャッシュの取得が失敗しました"
    
    # TTLキャッシュテスト
    cache_manager.set("ttl_key", "ttl_value", "ttl", ttl=1)
    value = cache_manager.get("ttl_key", "ttl")
    
    assert value == "ttl_value", "TTLキャッシュの取得が失敗しました"
    
    # キャッシュ統計テスト
    stats = cache_manager.get_stats()
    assert "lru_cache" in stats, "キャッシュ統計が不正です"
    assert "ttl_cache" in stats, "キャッシュ統計が不正です"

@cached(cache_type='lru')
def test_cached_function():
    """デコレータ付き関数のテスト"""
    return "cached_result"

def test_cached_decorator():
    """キャッシュデコレータのテスト"""
    result1 = test_cached_function()
    result2 = test_cached_function()
    
    assert result1 == result2, "キャッシュデコレータが機能していません"

@pytest.mark.asyncio
async def test_alert_features():
    """アラート機能のテスト"""
    
    # アラート送信テスト
    alert_id = await alert_manager.send_alert(
        severity=AlertSeverity.INFO,
        title="テストアラート",
        message="これはテスト用のアラートです",
        component="test"
    )
    
    assert alert_id, "アラートIDが生成されませんでした"
    
    # アクティブアラート取得テスト
    active_alerts = alert_manager.get_active_alerts()
    assert len(active_alerts) > 0, "アクティブアラートが取得できませんでした"
    
    # アラート解決テスト
    success = alert_manager.resolve_alert(alert_id)
    assert success, "アラートの解決が失敗しました"
    
    # アラート統計テスト
    stats = alert_manager.get_alert_stats()
    assert "total_alerts" in stats, "アラート統計が不正です"
    assert "active_alerts" in stats, "アラート統計が不正です"

@pytest.mark.asyncio
async def test_alert_notifiers():
    """アラート通知機能のテスト"""
    
    # ログ通知機能のテスト
    from utils.alert import LogNotifier
    
    log_notifier = LogNotifier()
    test_alert = alert_manager.alerts.get(list(alert_manager.alerts.keys())[0])
    
    if test_alert:
        await log_notifier(test_alert)
        # ログ出力の確認は難しいため、例外が発生しないことを確認

def test_integration():
    """統合テスト"""
    
    # セキュリティ + キャッシュの統合
    sensitive_data = "secret_data"
    encrypted_data = security_manager.encrypt_token(sensitive_data)
    
    # 暗号化されたデータをキャッシュに保存
    cache_manager.set("encrypted_key", encrypted_data, "lru")
    retrieved_data = cache_manager.get("encrypted_key", "lru")
    
    # 復号化して検証
    assert retrieved_data is not None, "キャッシュからデータが取得できませんでした"
    decrypted_data = security_manager.decrypt_token(retrieved_data)
    assert decrypted_data == sensitive_data, "統合テストが失敗しました"

if __name__ == "__main__":
    print("🚀 新機能統合テスト開始...")
    
    # 同期的テスト
    test_security_features()
    test_cache_features()
    test_cached_decorator()
    test_integration()
    
    # 非同期テスト
    asyncio.run(test_alert_features())
    asyncio.run(test_alert_notifiers())
    
    print("✅ 新機能統合テスト完了") 
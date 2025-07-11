# test_import.py
try:
    import mipac
    print("✅ mipac インポート成功:", mipac.__version__)
except ImportError as e:
    print("❌ mipac インポートエラー:", e)

try:
    import mipa
    print("✅ mipa インポート成功")
    from mipa.ext.commands.bot import Bot
    print("✅ Bot クラス インポート成功")
except ImportError as e:
    print("❌ mipa インポートエラー:", e)
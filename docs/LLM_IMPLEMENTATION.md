# `/llm` コマンド実装ガイド

## 📋 実装概要

`/llm` コマンドを使用してLLM（Ollama経由）と会話できる機能を実装しました。
定期投稿の感想機能の前に、LLM連携の基本を試すためのシンプルな実装です。

---

## 🎯 実装したファイル

### 新規作成
1. **`llm_service.py`** - Ollama API連携サービス
   - LLMへのリクエスト送信
   - エラーハンドリング
   - 統計情報収集
   - ヘルスチェック機能

2. **`handlers/llm_handler.py`** - `/llm` コマンド処理ハンドラー
   - コマンドパース
   - LLMサービス呼び出し
   - 応答の整形

3. **`.env.llm.example`** - LLM設定のサンプル

4. **`docs/CHARACTER_CASSANDRA.md`** - キャラクター設定書

5. **`docs/LLM_IMPLEMENTATION.md`** - このドキュメント

### 既存ファイル修正
1. **`command_router.py`**
   - LLMハンドラーのインポート
   - `/llm` コマンドのパース処理追加
   - `__init__`に`llm_service`パラメータ追加

2. **`constants.py`**
   - `CommandTypes.LLM` 追加

3. **`config.py`**
   - LLM関連設定プロパティ追加:
     - `llm_enabled`
     - `llm_api_url`
     - `llm_model`
     - `llm_timeout`
     - `llm_max_tokens`
     - `llm_temperature`

4. **`main.py`**
   - LLMServiceの初期化
   - CommandRouterへの`llm_service`渡し

5. **`handlers/__init__.py`**
   - `LLMHandler`のエクスポート追加

6. **`handlers/help_handler.py`**
   - ヘルプメッセージに`/llm`コマンドの説明追加

---

## ⚙️ 設定方法

### 1. .envファイルに追加

`.env` ファイルに以下の設定を追加：

```bash
# LLM機能を有効化
LLM_ENABLED=true

# Ollama APIのURL
LLM_API_URL=http://localhost:11434

# 使用するモデル名
LLM_MODEL=dsns

# タイムアウト（秒）
LLM_TIMEOUT=30

# 最大トークン数
LLM_MAX_TOKENS=100

# 温度パラメータ
LLM_TEMPERATURE=0.8
```

または `.env.llm.example` を参考にしてください。

### 2. Ollamaとモデルの準備

```bash
# Ollamaが起動しているか確認
systemctl status ollama

# モデルが存在するか確認
ollama list

# dsnsモデルが必要
# Modelfileから作成する場合:
ollama create dsns -f Modelfile
```

---

## 🚀 使用方法

### 基本的な使い方

Misskeyでボットにメンションして、`/llm` コマンドを使用：

```
@bot /llm こんにちは！
```

### コマンドフォーマット

```
/llm メッセージ
```

- `/llm` の後にスペースを入れてメッセージを書く
- 全角スラッシュ `／llm` も使用可能

### 使用例

```
@bot /llm 分散SNSって何ですか？

@bot /llm 今日は良い天気ですね

@bot /llm Misskeyの歴史を教えて
```

---

## 🔍 動作確認

### 1. LLM機能の有効化確認

ボット起動時のログで確認：

```
✅ LLMサービス初期化完了
✅ LLM APIヘルスチェック成功
LLMハンドラーを登録しました
```

`LLM_ENABLED=false` の場合：

```
ℹ️  LLM機能は無効です (LLM_ENABLED=false)
```

### 2. `/llm` コマンドのテスト

```bash
# ボットを起動
python main.py

# Misskeyでテスト
@bot /llm テストメッセージ
```

### 3. ヘルプコマンドで確認

```
@bot ヘルプ
```

ヘルプメッセージに「💬 LLM会話機能」のセクションが表示されるか確認。

---

## 📊 アーキテクチャ

### コンポーネント図

```
┌─────────────────────────────────────┐
│  Misskey (ユーザー)                  │
│  @bot /llm こんにちは                │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  main.py                             │
│  └─ BotClient                        │
│      └─ メンション受信                │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  command_router.py                   │
│  └─ parse_command()                  │
│      └─ /llm 検出                    │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  handlers/llm_handler.py             │
│  └─ LLMHandler.handle()              │
│      └─ llm_service呼び出し          │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  llm_service.py                      │
│  └─ LLMService.generate()            │
│      └─ Ollama API呼び出し           │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Ollama (http://localhost:11434)     │
│  └─ Model: dsns                      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  応答テキスト生成                     │
└─────────────────────────────────────┘
```

### データフロー

1. **ユーザー**: Misskeyで `@bot /llm メッセージ` を投稿
2. **BotClient**: メンションを受信
3. **CommandRouter**: `/llm` コマンドを検出し、パース
4. **LLMHandler**: コマンドを処理、LLMServiceに依頼
5. **LLMService**: Ollama APIにリクエスト送信
6. **Ollama**: モデル（dsns）で応答生成
7. **LLMService**: 応答（responseフィールド）を取得
8. **LLMHandler**: 応答をフォーマット
9. **BotClient**: Misskeyに投稿
10. **ユーザー**: 応答を受信

---

## 🔧 トラブルシューティング

### LLM機能が無効になっている

**症状**: `/llm` コマンドが反応しない、または「LLM機能が無効です」と表示

**解決策**:
1. `.env` ファイルで `LLM_ENABLED=true` を設定
2. ボットを再起動

### Ollamaに接続できない

**症状**: 「LLM APIヘルスチェック失敗」のログ

**解決策**:
```bash
# Ollamaが起動しているか確認
systemctl status ollama

# 起動していない場合
sudo systemctl start ollama

# APIが応答するか確認
curl http://localhost:11434/api/tags
```

### モデルが見つからない

**症状**: 「モデル'dsns'が見つかりません」のログ

**解決策**:
```bash
# モデル一覧確認
ollama list

# dsnsモデルを作成
ollama create dsns -f Modelfile
```

### タイムアウトエラー

**症状**: 「LLM APIタイムアウト」のログ

**解決策**:
1. `.env` で `LLM_TIMEOUT` を増やす（例: 60）
2. より軽量なモデルを使用
3. Raspberry Piのリソースを確認

### 応答が空

**症状**: 「LLM応答が空です」のログ

**解決策**:
1. モデルが正しく動作しているか確認
   ```bash
   ollama run dsns "テスト"
   ```
2. システムプロンプトを確認
3. Modelfileの設定を確認

---

## 📈 統計情報の確認

LLMServiceは以下の統計情報を収集します：

```python
# 統計情報取得
stats = llm_service.get_stats()

# 含まれる情報:
# - total_calls: 総呼び出し回数
# - success_calls: 成功回数
# - failed_calls: 失敗回数
# - avg_response_time: 平均応答時間
# - success_rate: 成功率（%）
```

将来的に、ステータスコマンドで確認できるようにする予定。

---

## 🧪 テストケース

### 基本的な会話

```
@bot /llm こんにちは
→ 期待: 挨拶の応答

@bot /llm 今日の天気は？
→ 期待: 会話の応答
```

### エラーケース

```
@bot /llm 
（メッセージなし）
→ 期待: 「何かお話ししたいことがありますの？」

LLM_ENABLED=false の状態で
@bot /llm テスト
→ 期待: 「現在LLM機能は無効になっていますわ。」
```

### 長いメッセージ

```
@bot /llm 分散SNSの歴史について、特にMisskeyとMastodonの違いや、ActivityPubプロトコルの重要性について詳しく教えてください
→ 期待: 適切な長さに収まった応答
```

---

## 🚀 次のステップ

### 短期（実装済み機能のテスト）
- [ ] 実際に`/llm`コマンドを使用してテスト
- [ ] 様々なメッセージパターンでテスト
- [ ] エラーハンドリングの確認
- [ ] パフォーマンス測定

### 中期（定期投稿感想機能）
- [ ] `llm_scheduler.py` 作成
- [ ] 定期投稿後に感想をリプライする機能
- [ ] 5分後の投稿タイミング実装
- [ ] ドライランモードでテスト

### 長期（拡張機能）
- [ ] 複数キャラクターの切り替え
- [ ] 会話履歴の保持
- [ ] コンテキストの活用
- [ ] RAG (Retrieval-Augmented Generation) 統合

---

## 📚 参考資料

### 内部ドキュメント
- `docs/LLM_COMMENTARY_FEATURE.md` - LLM機能の全体計画
- `docs/CHARACTER_CASSANDRA.md` - カサンドラキャラクター設定
- `Modelfile` - カスタムモデル設定
- `.env.llm.example` - 環境変数設定例

### 外部リンク
- [Ollama公式サイト](https://ollama.com/)
- [Ollama API ドキュメント](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Gemma モデル情報](https://ai.google.dev/gemma)

---

**作成日**: 2026-02-02  
**最終更新**: 2026-02-02  
**ステータス**: 実装完了・テスト待ち 🧪

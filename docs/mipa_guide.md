# MiPA (Misskey Python Bot Framework) 完全ガイド

## 概要

MiPAは、Discord.py風のコーディングスタイルでMisskeyボットを作成できるPythonフレームワークです。内部的にはMiPAC（Misskey Python API Core）を使用してAPI機能を提供しています。

## 基本機能

### 1. インストールとセットアップ

```bash
# 安定版（推奨）
pip install mipa

# 開発版（最新機能）
pip install git+https://github.com/yupix/MiPA.git

# 最新ビルド（MiPAC）
pip install --extra-index-url https://onedev.akarinext.org/yupix/mipac-sync/MiPAC/~pypi/simple/ mipac
```

**注意**: 開発版や最新ビルドは不安定な場合があります。本格的な運用では安定版の使用を推奨します。

### 2. 基本的なボット構造

```python
import asyncio
from aiohttp import ClientWebSocketResponse
from mipac.models.note import Note
from mipa.ext.commands.bot import Bot

class MyBot(Bot):
    def __init__(self):
        super().__init__()
    
    async def _connect_channel(self):
        # 基本的なチャンネル接続（メンション通知受信用）
        await self.router.connect_channel(['main'])
        
        # 注意: mainチャンネルは以下のイベントを受信します：
        # - リプライ（メンション含む）
        # - リアクション
        # - フォロー/フォロー解除
        # - その他の通知
        
        # 他のチャンネルオプション：
        # - 'home': ホームタイムライン（ノートのみ）
        # - 'local': ローカルタイムライン（ノートのみ）
        # - 'global': グローバルタイムライン（ノートのみ）
        
        # 高度な接続方法（辞書形式）
        # await self.router.connect_channel({
        #     'main': None,  # デフォルトハンドラー
        #     'global': CustomTimeline(),  # カスタムハンドラー
        #     'home': None
        # })
    
    async def on_ready(self, ws: ClientWebSocketResponse):
        await self._connect_channel()
        print(f'Logged in as {self.user.username}')
    
    async def on_reconnect(self, ws: ClientWebSocketResponse):
        await self._connect_channel()
        print('Reconnected to Misskey')

if __name__ == '__main__':
    bot = MyBot()
    asyncio.run(bot.start('wss://your-instance.com/streaming', 'your_access_token'))
```

### 3. イベント処理

#### ノートイベント

```python
async def on_note(self, note: Note):
    """新しいノートが投稿された時"""
    print(f'{note.user.username}: {note.text}')
    
    # 特定の条件でリアクション
    if 'こんにちは' in note.text:
        await note.add_reaction('👋')

async def on_mention(self, notice: NotificationNote):
    """メンションされた時（通知オブジェクト）"""
    # 通知オブジェクトから実際のノートを取得
    actual_note = notice.note if hasattr(notice, 'note') and notice.note else notice
    
    if actual_note.text:
        # 自動返信
        await self.client.note.action.send(
            text=f'@{actual_note.user.username} こんにちは！',
            reply_id=actual_note.id
        )
    
    # MENTION_COMMANDを使用する場合は以下を呼び出し
    # await self.progress_command(notice)
```

#### チャットイベント

```python
async def on_chat(self, message: ChatMessage):
    """チャットメッセージを受信した時"""
    print(f'{message.user.username}: {message.text}')
    
    if message.text == 'hello':
        await self.client.chat.action.send(
            f'Hello! {message.user.username}',
            user_id=message.user.id
        )
```

#### フォローイベント

```python
async def on_follow(self, user):
    """フォローされた時"""
    await self.client.note.action.send(
        text=f'@{user.username} フォローありがとうございます！'
    )

async def on_unfollow(self, user):
    """フォロー解除された時"""
    print(f'{user.username} unfollowed')
```

## 応用機能

### 1. ノート操作

#### 基本的なノート投稿

```python
# テキストのみ
await self.client.note.action.send(text='Hello, Misskey!')

# 公開範囲を指定
await self.client.note.action.send(
    text='フォロワー限定投稿',
    visibility='followers'
)

# CW（コンテンツワーニング）付き
await self.client.note.action.send(
    text='ネタバレ内容',
    cw='映画のネタバレ注意'
)

# リプライ
await self.client.note.action.send(
    text='返信です',
    reply_id=target_note.id
)

# リノート
await self.client.note.action.send(
    renote_id=target_note.id
)

# 引用リノート
await self.client.note.action.send(
    text='これいいね！',
    renote_id=target_note.id
)
```

#### ファイル添付

```python
# ファイルをアップロード
file = await self.client.drive.action.upload_file(
    file_path='/path/to/image.jpg',
    name='image.jpg'
)

# ファイル付きノート
await self.client.note.action.send(
    text='画像付き投稿',
    file_ids=[file.id]
)
```

#### 投票（アンケート）

```python
# 投票付きノート
await self.client.note.action.send(
    text='好きな言語は？',
    poll={
        'choices': ['Python', 'JavaScript', 'Rust'],
        'multiple': False,
        'expires_at': None  # 期限なし
    }
)
```

### 2. リアクション操作

```python
# リアクション追加
await note.add_reaction('👍')
await note.add_reaction(':custom_emoji:')

# リアクション削除
await note.remove_reaction('👍')

# リアクション一覧取得
reactions = await note.get_reactions()
for reaction in reactions:
    print(f'{reaction.type}: {reaction.count}')
```

### 3. ユーザー操作

```python
# ユーザー情報取得
user = await self.client.user.action.get(user_id='user_id_here')
print(f'Name: {user.name}, Username: {user.username}')

# フォロー
await user.follow()

# フォロー解除
await user.unfollow()

# ミュート
await user.mute()

# ブロック
await user.block()
```

### 4. タイムライン取得

```python
# ホームタイムライン
home_notes = await self.client.note.action.get_timeline(
    timeline='home',
    limit=20
)

# ローカルタイムライン
local_notes = await self.client.note.action.get_timeline(
    timeline='local',
    limit=20
)

# グローバルタイムライン
global_notes = await self.client.note.action.get_timeline(
    timeline='global',
    limit=20
)
```

### 5. 検索機能

```python
# ノート検索
search_results = await self.client.note.action.search(
    query='Python',
    limit=10
)

# ユーザー検索
users = await self.client.user.action.search(
    query='username',
    limit=10
)
```

### 6. 通知管理

**重要**: MiPAのBotクラスには`on_notification`イベントハンドラーは存在しません。代わりに以下の専用イベントハンドラーを使用してください。

#### リプライ（メンション）処理

```python
async def on_reply(self, note):
    """リプライ受信時 - メンション検出と処理"""
    # 通知オブジェクトから実際のノートを取得
    actual_note = None
    if hasattr(note, 'note') and note.note:
        actual_note = note.note  # 通知オブジェクトの場合
    else:
        actual_note = note       # 直接ノートオブジェクトの場合
    
    username = actual_note.user.username
    text = actual_note.text
    visibility = actual_note.visibility
    
    print(f'リプライ: @{username} ({visibility}) - {text}')
    
    # メンション検出（mentions配列にボットIDが含まれるかチェック）
    bot_id = self.user.id
    mentions = actual_note.mentions
    
    if bot_id in mentions:
        print(f'メンション検出: @{username}')
        # メンション処理を実行
        await self.handle_mention(actual_note)
```

#### メンション処理（通知オブジェクト）

```python
async def on_mention(self, notice: NotificationNote):
    """メンション専用イベント（通知オブジェクト）"""
    # 通知オブジェクトから実際のノートを取得
    actual_note = notice.note if hasattr(notice, 'note') and notice.note else notice
    
    print(f'メンション: {actual_note.user.username} - {actual_note.text}')
    
    # メンションコマンドを使用する場合
    # await self.progress_command(notice)
    
    # または直接処理
    if 'hello' in actual_note.text.lower():
        await self.client.note.action.send(
            text=f'@{actual_note.user.username} こんにちは！',
            reply_id=actual_note.id
        )
```

#### その他の通知イベント

```python
async def on_reaction(self, reaction):
    """リアクション受信時"""
    print(f'リアクション: {reaction.type}')

async def on_user_follow(self, user):
    """フォロー受信時"""
    print(f'フォロー: {user.username}')

async def on_user_unfollow(self, user):
    """フォロー解除受信時"""
    print(f'フォロー解除: {user.username}')
```

### 7. コマンドシステム

#### 基本的なコマンド

```python
from mipa.ext.commands import Bot, command

class CommandBot(Bot):
    def __init__(self):
        super().__init__(command_prefix='!')
    
    @command(name='ping')
    async def ping_command(self, ctx):
        """!pingコマンド"""
        await ctx.send('Pong!')
    
    @command(name='echo')
    async def echo_command(self, ctx, *, message):
        """!echo メッセージ"""
        await ctx.send(f'Echo: {message}')
    
    @command(name='weather')
    async def weather_command(self, ctx, city):
        """!weather 都市名"""
        # 天気API呼び出し（例）
        weather_info = await get_weather(city)
        await ctx.send(f'{city}の天気: {weather_info}')
```

#### メンションコマンド

```python
from mipa.ext.commands import Bot, MENTION_COMMAND

class MentionCommandBot(Bot):
    def __init__(self):
        super().__init__()
    
    async def on_mention(self, notice: NotificationNote):
        """メンション処理 - コマンド実行"""
        # メンションコマンドを処理
        await self.progress_command(notice)
    
    @MENTION_COMMAND(name='help')
    async def help_command(self, ctx):
        """@bot help コマンド"""
        await ctx.send('ヘルプメッセージです')
    
    @MENTION_COMMAND(name='search')
    async def search_command(self, ctx, *, query):
        """@bot search 検索語 コマンド"""
        result = await search_data(query)
        await ctx.send(f'検索結果: {result}')
```

**重要**: メンションコマンドを使用する場合は、`on_mention`イベントで`progress_command(notice)`を呼び出す必要があります。

### 8. 定期実行タスク

```python
import asyncio
from datetime import datetime

class ScheduledBot(Bot):
    def __init__(self):
        super().__init__()
        self.scheduled_tasks = []
    
    async def on_ready(self, ws):
        await super().on_ready(ws)
        # 定期タスクを開始
        self.scheduled_tasks.append(
            asyncio.create_task(self.hourly_task())
        )
        self.scheduled_tasks.append(
            asyncio.create_task(self.daily_task())
        )
    
    async def hourly_task(self):
        """1時間ごとの実行"""
        while True:
            await asyncio.sleep(3600)  # 1時間
            await self.client.note.action.send(
                text=f'時報: {datetime.now().strftime("%H:%M")}'
            )
    
    async def daily_task(self):
        """1日ごとの実行"""
        while True:
            await asyncio.sleep(86400)  # 24時間
            await self.client.note.action.send(
                text='今日も一日お疲れさまでした！'
            )
```

### 9. エラーハンドリング

```python
import logging
import traceback

class RobustBot(Bot):
    def __init__(self):
        super().__init__()
        # ロギング設定
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def on_error(self, error):
        """エラーが発生した時"""
        self.logger.error(f'Bot error: {error}')
        self.logger.debug(traceback.format_exc())
        
        # エラー内容に応じた処理
        if "connection" in str(error).lower():
            self.logger.warning("接続エラーが発生しました")
        elif "timeout" in str(error).lower():
            self.logger.warning("タイムアウトエラーが発生しました")
        elif "rate limit" in str(error).lower():
            self.logger.warning("レート制限に達しました")
        else:
            self.logger.warning("不明なエラーが発生しました")
        
        # 管理者に通知（本番環境でのみ）
        # await self.client.note.action.send(
        #     text=f'エラーが発生しました: {str(error)}',
        #     visibility='specified',
        #     visible_user_ids=['admin_user_id']
        # )
    
    async def on_note(self, note):
        try:
            # ノート処理
            await self.process_note(note)
        except Exception as e:
            self.logger.error(f'Note processing error: {e}')
            self.logger.debug(traceback.format_exc())
    
    async def on_mention(self, notice):
        try:
            # メンション処理
            await self.progress_command(notice)
        except Exception as e:
            self.logger.error(f'Mention processing error: {e}')
            self.logger.debug(traceback.format_exc())
            
            # エラー時のフォールバック
            actual_note = notice.note if hasattr(notice, 'note') and notice.note else notice
            await self.client.note.action.send(
                text='申し訳ございません。処理中にエラーが発生しました。',
                reply_id=actual_note.id
            )
    
    async def process_note(self, note):
        """ノート処理ロジック"""
        if note.text and 'help' in note.text.lower():
            await self.client.note.action.send(
                text='ヘルプメッセージ',
                reply_id=note.id
            )
```

### 10. 設定管理

```python
import json
import os

class ConfigurableBot(Bot):
    def __init__(self, config_file='config.json'):
        super().__init__()
        self.config = self.load_config(config_file)
    
    def load_config(self, config_file):
        """設定ファイル読み込み"""
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定
            default_config = {
                'auto_reaction': True,
                'welcome_message': 'こんにちは！',
                'command_prefix': '!',
                'admin_users': []
            }
            self.save_config(config_file, default_config)
            return default_config
    
    def save_config(self, config_file, config):
        """設定ファイル保存"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    async def on_note(self, note):
        if self.config['auto_reaction'] and 'いいね' in note.text:
            await note.add_reaction('👍')
```

### 11. 切断処理

#### 基本的な切断処理

```python
async def disconnect(self):
    """ボットの切断処理"""
    try:
        # MiPAボットの切断
        if hasattr(self, 'disconnect'):
            await self.disconnect()
        elif hasattr(self, 'stop'):
            await self.stop()
        
        # APIセッションの切断
        if hasattr(self, 'core') and self.core:
            await self.core.close_session()
            
    except Exception as e:
        if "WebSocketNotConnected" in str(e):
            print("WebSocketは既に切断済み")
        else:
            print(f"切断エラー: {e}")
```

#### 使用例

```python
async def main():
    bot = MyBot()
    try:
        await bot.start('wss://your-instance.com/streaming', 'your_token')
        await asyncio.sleep(3600)  # 1時間動作
    finally:
        await bot.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
```

**注意**: 切断時は必ずAPIセッションも閉じることで、リソースリークを防げます。

### 12. 高度なチャンネル接続

#### カスタムタイムライン

```python
from mipa.ext.timelines.core import AbstractTimeline

class CustomGlobalTimeline(AbstractTimeline):
    async def on_note(self, note: Note):
        """グローバルタイムライン専用のノート処理"""
        print(f'[Global] {note.user.username}: {note.text}')
        
        # 特定の条件でリアクション
        if 'hello' in note.text.lower():
            await note.add_reaction('👋')

class MyBot(Bot):
    def __init__(self):
        super().__init__()
    
    async def _connect_channel(self):
        # 辞書形式でカスタムハンドラーを指定
        await self.router.connect_channel({
            'main': None,  # デフォルトハンドラー
            'global': CustomGlobalTimeline(),  # カスタムハンドラー
            'home': None
        })
```

### 13. モデル使用の注意事項

#### 重要な制約

```python
# ❌ 推奨されない方法（モデルの直接インスタンス化）
from mipac.models.note import Note
note = Note(text="Hello", client=client)  # 非推奨

# ✅ 推奨される方法（API経由での取得・作成）
note = await client.note.action.send(text="Hello")
notes = await client.note.action.get_timeline(timeline='home', limit=10)
```

**注意事項**:
- モデルを直接インスタンス化することは推奨されません
- API経由で取得・作成されたモデルを使用してください
- モデルの引数は将来変更される可能性があります
- `client`引数は必須の場合がありますが、省略される場合もあります

## 実践的なボット例

### チャットボット

```python
class ChatBot(Bot):
    def __init__(self):
        super().__init__()
        self.responses = {
            'おはよう': 'おはようございます！',
            'こんにちは': 'こんにちは！',
            'おやすみ': 'おやすみなさい！',
            '天気': '今日はいい天気ですね！',
        }
    
    async def _connect_channel(self):
        # メンション通知を受信するためにmainチャンネルに接続
        await self.router.connect_channel(['main'])
    
    async def on_reply(self, note):
        """リプライ受信時 - メンション検出と処理"""
        # 通知オブジェクトから実際のノートを取得
        actual_note = note.note if hasattr(note, 'note') and note.note else note
        
        # メンション検出
        bot_id = self.user.id
        mentions = actual_note.mentions
        
        if bot_id in mentions:
            # メンション処理
            for keyword, response in self.responses.items():
                if keyword in actual_note.text:
                    await self.client.note.action.send(
                        text=f'@{actual_note.user.username} {response}',
                        reply_id=actual_note.id
                    )
                    break
```

### RSS配信ボット

```python
import feedparser
import asyncio

class RSSBot(Bot):
    def __init__(self, rss_url):
        super().__init__()
        self.rss_url = rss_url
        self.posted_entries = set()
    
    async def on_ready(self, ws):
        await super().on_ready(ws)
        asyncio.create_task(self.check_rss())
    
    async def check_rss(self):
        while True:
            feed = feedparser.parse(self.rss_url)
            for entry in feed.entries:
                if entry.id not in self.posted_entries:
                    await self.client.note.action.send(
                        text=f'📰 {entry.title}\n{entry.link}'
                    )
                    self.posted_entries.add(entry.id)
            
            await asyncio.sleep(600)  # 10分ごとにチェック
```

## 注意事項

1. **開発状況**: MiPAは現在も活発に開発中のため、APIが変更される可能性があります
2. **Python要件**: Python 3.10以上が推奨されています
3. **レート制限**: Misskeyサーバーの負荷を避けるため、適切な間隔でAPI呼び出しを行ってください
4. **アクセストークン**: アクセストークンは安全に管理し、公開しないよう注意してください
5. **モデルインスタンス化**: モデルを直接インスタンス化することは推奨されません
6. **バージョン互換性**: 一部のサーバーバージョンでは正常に動作しない場合があります
7. **エラーハンドリング**: 本格的な運用では適切なエラーハンドリングを実装してください

## 公式リソース

- **公式ドキュメント**: https://mipa.akarinext.org
- **MiPACドキュメント**: https://mipac.akarinext.org
- **GitHub**: https://github.com/yupix/MiPA
- **Discord**: https://discord.gg/CcT997U

## 重要な発見とベストプラクティス

### メンション処理の正しい方法

1. **`on_notification`は存在しない**: MiPAのBotクラスには`on_notification`イベントハンドラーは存在しません
2. **`on_reply`と`on_mention`の使い分け**: 
   - `on_reply`: リプライ（メンション含む）の処理
   - `on_mention`: 直接メンションの処理（`NotificationNote`型）
3. **通知オブジェクトの処理**: `on_mention`で受信されるオブジェクトは`NotificationNote`型で、実際のノートは`notice.note`プロパティにあります
4. **メンション検出**: `mentions`配列にボットIDが含まれているかチェックしてください
5. **メンションコマンド**: `MENTION_COMMAND`を使用する場合は`progress_command(notice)`を呼び出してください

### チャンネル接続の最適化

1. **`main`チャンネル**: メンション通知を受信するには`main`チャンネルに接続してください
2. **`local`チャンネルの制限**: `local`チャンネルはローカルタイムラインのノートのみを受信し、通知は受信しません
3. **ホーム投稿のメンション**: ホーム投稿やフォロワー限定投稿へのメンションも`main`チャンネルで受信できます
4. **カスタムタイムライン**: `AbstractTimeline`を継承してチャンネル固有の処理を実装できます

### オブジェクト型の理解

- **`NotificationNote`**: 通知オブジェクト（`on_mention`で受信）
- **`Note`**: 実際のノートオブジェクト（`notice.note`から取得）
- **`mentions`**: メンションされたユーザーIDの配列
- **`visibility`**: 投稿の公開範囲（`public`, `home`, `followers`, `specified`）

### エラーハンドリングのベストプラクティス

1. **詳細なログ出力**: `traceback.format_exc()`を使用してスタックトレースを記録
2. **エラー内容の分類**: 接続エラー、タイムアウト、レート制限などに応じた処理
3. **フォールバック処理**: エラー時の適切なフォールバックメッセージ
4. **本番環境での通知**: 管理者へのエラー通知は本番環境でのみ有効化

### モデル使用のベストプラクティス

1. **API経由での取得**: モデルを直接インスタンス化せず、API経由で取得
2. **引数の変更に注意**: モデルの引数は将来変更される可能性がある
3. **client引数の扱い**: `client`引数は必須の場合と省略可能な場合がある

## トラブルシューティング

### よくある問題

1. **接続エラー**: WebSocketのURLとアクセストークンを確認
2. **権限エラー**: アクセストークンに必要な権限が付与されているか確認
3. **文字化け**: UTF-8エンコーディングを使用
4. **メモリリーク**: 長時間動作するボットでは適切なリソース管理を実装

#### メンション処理の問題

5. **メンションが受信されない**:
   - `on_notification`イベントは存在しません。`on_mention`を使用してください
   - `main`チャンネルに接続しているか確認してください
   - 通知オブジェクトから実際のノートを取得する必要があります

6. **リプライのテキストが空**:
   - `notice.text`ではなく`notice.note.text`を使用してください
   - 通知オブジェクト（`NotificationNote`）とノートオブジェクト（`Note`）を区別してください

7. **メンション検出ができない**:
   - `mentions`配列にボットIDが含まれているかチェックしてください
   - `self.user.id`と`actual_note.mentions`を比較してください

8. **メンションコマンドが動作しない**:
   - `on_mention`イベントで`progress_command(notice)`を呼び出しているか確認してください
   - `@MENTION_COMMAND`デコレータが正しく設定されているか確認してください

#### チャンネル接続の問題

8. **ホーム投稿のメンションが受信されない**:
   - `main`チャンネルに接続してください（`local`チャンネルでは受信できません）
   - `main`チャンネルはすべての通知イベントを受信します

### デバッグ

```python
import logging

# デバッグレベルのログを有効化
logging.basicConfig(level=logging.DEBUG)

# MiPACのログも表示
logging.getLogger('mipac').setLevel(logging.DEBUG)
```

この包括的なガイドを参考に、用途に応じたMisskeyボットを開発してください。
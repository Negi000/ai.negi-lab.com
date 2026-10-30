---
title: "Claude CodeとCursorを併用したAIコーディング環境の構築と使い方"
date: 2026-10-31T00:00:00+09:00
slug: "claude-code-cursor-ai-development-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング エージェント"
  - "FastAPI 開発環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Cursorで設計し、Claude Codeでテスト・デバッグを自動化するFastAPIのAPIサーバー
- Pythonのモダンなパッケージ管理ツール「uv」を組み合わせた爆速の開発環境
- エラーが発生した際に、AIが自律的にターミナルを操作して修正するワークフロー

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIエージェントとIDE、Dockerを同時並行で動かすなら30GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、基本的なターミナル操作とPythonの基礎がわかることを想定しています。
必要なものは、AnthropicのAPIキーとCursorの有料プラン（Pro推奨）です。

## 先に確認するスペック・料金

AIコーディングを本気で仕事に使うなら、ツールへの投資は必須です。
Cursorは月額$20のProプランを推奨します。無料枠でも動きますが、Claude 3.5 Sonnetを制限なく使えないと開発効率が劇的に落ちます。
Claude CodeはAnthropicのAPIを直接叩くため、従量課金制です。1時間の集中した開発で$1〜$3程度消費される感覚でいてください。

ハードウェアについては、MacBook（M2チップ以降 / メモリ24GB以上）が理想です。
Windowsユーザーは必ずWSL2（Ubuntu）をセットアップしてください。Claude CodeはUnixベースの環境で真価を発揮します。
GPUはローカルLLMを動かさない限り不要ですが、VS Code（Cursor）とブラウザ、Dockerを同時に動かすため、メモリは最低でも16GB、できれば32GB積んでおかないと動作が重くなります。

## なぜこの方法を選ぶのか

Cursorだけでも十分に強力ですが、Cursorは「エディタの中」に閉じています。
ターミナルのコマンド実行や、テストの自動リトライ、複雑なディレクトリ構造の把握においては、Claude Codeの方が圧倒的に自律性が高いです。
一方で、Claude CodeはCLIツールなので、コード全体の構造を俯瞰したり、UIを微調整したりする作業には向きません。

「Cursorで大枠のロジックを書き、Claude Codeにテストとデバッグを丸投げする」という使い分けが、現状のAIコーディングにおけるベストプラクティスだと私は判断しています。
特にClaude Codeの「/test」コマンドや「/fix」コマンドは、一度使うと手動のデバッグに戻れなくなるほどの快適さがあります。

## Step 1: 環境を整える

まずは、Claude Codeをインストールします。これはNode.js環境で動作するCLIツールです。

```bash
# Node.jsがインストールされていることを確認（v18以上推奨）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 初期設定とログイン
claude auth
```

次に、Python環境を汚さないために、高速なパッケージマネージャ「uv」を導入します。
従来のpipよりも10倍以上速く、仮想環境の構築も一瞬で終わるため、AIとの相性が抜群に良いです。

```bash
# uvのインストール（Mac/Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトディレクトリの作成
mkdir ai-fastapi-app && cd ai-fastapi-app
uv init
```

⚠️ **落とし穴:** Node.jsのバージョンが古いと、Claude Codeのインストール時にエラーが出ることがあります。`nvm`などを使って最新のLTS（Long Term Support）バージョンに上げてから実行してください。また、Claude Codeを初めて起動した際に、ファイルの読み書き権限を求められます。これを許可しないと、AIがファイルを修正できなくなるので注意が必要です。

## Step 2: 基本の設定

今回のプロジェクトでは、FastAPIを使用して天気を返す簡単なAPIを作ります。
まず、必要なライブラリをインストールし、環境変数を設定します。

```bash
# 必要なライブラリのインストール
uv add fastapi uvicorn requests

# Cursorで現在のディレクトリを開く
cursor .
```

Cursorを開いたら、プロジェクトのルートに`.env`ファイルを作成し、APIキーを記述します。
今回はデモ用に無料の天気API（Open-Meteoなど）を使いますが、将来的に認証が必要なAPIを扱う際、AIにキーを直書きさせない癖をつけておくのが実務の鉄則です。

```python
# main.py の初期コード（Cursorで作成）
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello Claude Code"}
```

この段階では、まだCursorだけで作業しています。
ここからが本番です。ターミナルで`claude`コマンドを叩き、Claude Codeを起動してください。

## Step 3: 動かしてみる

Claude Codeを起動すると、対話型のインターフェースが立ち上がります。
ここで「FastAPIを起動して、正常にレスポンスが返ってくるかテストして」と指示を出してみてください。

```bash
# Claude Code内での指示
FastAPIを起動して、curlで動作確認をして。エラーが出たら修正して。
```

### 期待される出力

```text
> ⚙️  Running: uvicorn main:app --reload
> ⚙️  Running: curl http://127.0.0.1:8000/
> {"message": "Hello Claude Code"}
> ✅ テストが成功しました。サーバーは正常に動作しています。
```

Claude Codeの凄いところは、バックグラウンドでプロセスを立ち上げ、その出力を監視し、必要があれば自ら修正コードを書いて再テストするところです。
従来のCursorだと「エラーが出ました」とユーザーが報告し、提案されたコードをユーザーがコピペしていましたが、その手間がゼロになります。

## Step 4: 実用レベルにする

次に、外部APIと連携して特定の都市の天気を取得するエンドポイントを追加します。
ここでは「あえて間違ったコード」をCursorで書き、Claude Codeに修正させる体験をしてみましょう。

Cursorで`main.py`を以下のように書き換えてください。

```python
# main.py（あえて不完全なコード）
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/weather/{city}")
def get_weather(city: str):
    # エラーが起きるポイント：URLが不適切、またはエラーハンドリングがない
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude=35.6895&longitude=139.6917")
    return response.json()
```

この状態で、Claude Codeにこう指示します。

```text
/weather/{city} エンドポイントを実装したけど、どの都市を指定しても東京の天気しか返ってこない。
都市名から緯度・経度を特定するように修正して、エラーハンドリングも追加して。
テストコードも作成して実行して。
```

Claude Codeは以下の手順を自動で実行します。
1. 都市名を緯度・経度に変換するロジックが必要だと判断する（追加のライブラリが必要なら勝手に`uv add`する）。
2. `main.py`を書き換える。
3. `pytest`などのテスト環境がなければ構築する。
4. 実際にサーバーを立ててテストを回す。

これが「仕事で使える」レベルのAIエージェントです。
私はこれを「自律デバッグ・ループ」と呼んでいます。人間は設計図（Cursorでの記述）を渡し、細かい「動く・動かない」の不整合はClaude Codeに丸投げする。この役割分担が最も生産性が高いです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm config get prefix` で確認し、パスを通すか `npx @anthropic-ai/claude-code` を使用 |
| APIキーの制限エラー | 無料枠の超過、またはTier不足 | Anthropicのコンソールで$5以上チャージしてTier 1以上にする |
| ファイル編集の競合 | CursorとClaude Codeで同時保存 | Cursorの自動保存をONにし、Claude Codeの操作が終わるまでファイルを閉じない |

## 次のステップ

この環境を構築できたあなたは、すでに「AIにコードを書かせる人」から「AIチームを指揮するリードエンジニア」へとステップアップしています。
次に挑戦すべきは、MCP（Model Context Protocol）の導入です。
Claude CodeはMCPサーバーと連携することで、Googleドライブの資料を読み取ったり、GitHubのIssueを直接操作したりできるようになります。

まずは、自分のプロジェクトに`pytest`を導入し、Claude Codeに「カバレッジ100%になるまでテストを書いて実行し続けて」と指示を出してみてください。
手動でテストを書く苦行から解放される感覚は、エンジニアとしての価値観を変えてくれるはずです。

## よくある質問

### Q1: CursorのComposer機能（Ctrl+I）があれば、Claude Codeはいらないのでは？

CursorのComposerも優秀ですが、ターミナルの出力を完璧にハンドリングし、自らコマンドを試行錯誤する能力はClaude Codeの方が一段上です。特に環境構築や依存関係のトラブル解決はClaude Codeが圧倒的に強いです。

### Q2: 料金が高くなりそうで怖いのですが、抑えるコツはありますか？

Claude Codeを立ち上げっぱなしにせず、特定のタスク（デバッグやテスト）が終わったら一度終了させることです。また、プロジェクト全体のファイルを読み込ませすぎないよう、`.gitignore`を適切に設定して不要なフォルダ（node_modulesなど）をスキャン対象から外しましょう。

### Q3: 日本語での指示は完璧に理解されますか？

はい、実務上全く問題ありません。ただ、プログラミング文脈の用語は英語のまま（例：「バリデーションを追加して」など）伝えたほうが、AIが意図したライブラリを選択しやすくなる傾向があります。

---

## あわせて読みたい

- [Claude CodeとCursorを併用し、バックエンドのAPIサーバー構築から自動テスト、Gitコミットまでを完全にAI主導で完結させる手法を解説します。](/posts/2026-10-04-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築と実践](/posts/2026-10-09-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用した最強のAIコーディング環境構築ガイド](/posts/2026-10-18-claude-code-cursor-ai-coding-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能（Ctrl+I）があれば、Claude Codeはいらないのでは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも優秀ですが、ターミナルの出力を完璧にハンドリングし、自らコマンドを試行錯誤する能力はClaude Codeの方が一段上です。特に環境構築や依存関係のトラブル解決はClaude Codeが圧倒的に強いです。"
      }
    },
    {
      "@type": "Question",
      "name": "料金が高くなりそうで怖いのですが、抑えるコツはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeを立ち上げっぱなしにせず、特定のタスク（デバッグやテスト）が終わったら一度終了させることです。また、プロジェクト全体のファイルを読み込ませすぎないよう、.gitignoreを適切に設定して不要なフォルダ（nodemodulesなど）をスキャン対象から外しましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示は完璧に理解されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、実務上全く問題ありません。ただ、プログラミング文脈の用語は英語のまま（例：「バリデーションを追加して」など）伝えたほうが、AIが意図したライブラリを選択しやすくなる傾向があります。 ---"
      }
    }
  ]
}
</script>

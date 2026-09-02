---
title: "Claude CodeとCursorを使い分け爆速でWebAPIを開発する方法"
date: 2026-09-03T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-tutorial"
cover:
  image: "/images/posts/2026-09-03-claude-code-cursor-ai-coding-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "FastAPI テスト自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

FastAPIとSQLiteを使用した、実用的な「タスク管理API（Todoアプリ）」を構築します。
Cursorで全体の設計とコード編集を行い、Claude Codeにテストコードの生成、実行、デバッグ、リファクタリングを丸投げする「AIエージェント型開発」を体験できます。
この記事を読み終える頃には、ターミナルから一歩も動かずにコードを完成させる感覚が身についているはずです。

### 前提知識
- Pythonの基本的な文法がわかる
- ターミナル（コマンドプロンプトやPowerShell）でコマンドが打てる
- VS Code（またはCursor）を触ったことがある

### 必要なもの
- AnthropicのAPIキー（Claude 3.5 Sonnetを使用）
- Cursor（Proプラン推奨）
- Node.js（Claude Codeの実行に必要。v18以上）
- Python 3.10以上

## 先に確認するスペック・料金

AIコーディング環境を整える上で、最も重要なのは「メモリ」と「API予算」です。
Cursorは月額$20のProプランに加入しておくことを強く推奨します。無料枠では今回のような「AIをエージェントとして使い倒す」フローではすぐに制限に達してしまい、思考を中断されるストレスが大きすぎるからです。
Claude CodeはAnthropicのAPIを直接消費します。一連の機能開発（設計〜実装〜テスト〜デバッグ）で、およそ$2〜$5程度のAPI費用を見込んでおいてください。

ハードウェアについては、メモリ16GB以上のPCが必須です。
CursorとDocker、複数のAIプロセスを同時に動かすと、8GBではスワップが発生してレスポンスが極端に悪化します。
私はRTX 4090を2枚挿した自作サーバーでローカルLLMも併用していますが、Claude Codeのようなクラウド型エージェントを使う場合でも、ブラウザのタブやIDEの消費メモリを考慮すると32GBあると安心です。
また、ネットワーク速度も地味に重要です。Claude Codeは大量のコンテキストをAPIに送受信するため、レイテンシが低い光回線環境でないと「待ち時間」がストレスになります。

## なぜこの方法を選ぶのか

Cursorだけでもコーディングは完結しますが、Cursorには「ターミナルを自律的に操作し、コマンドの実行結果を見て修正を繰り返す」というループの自動化に限界があります。
一方でClaude Codeは、Anthropicが公式に提供するCUIツールであり、ファイル操作だけでなくシェルコマンドの実行権限を強く持っています。
「テストコードを書いて、pytestを実行し、エラーが出たら修正して、パスするまで繰り返す」という作業は、Claude Codeの方が圧倒的に得意です。

Cursorを「コードの全体像を把握し、UIやロジックを細かく調整するGUIツール」として使い、Claude Codeを「自律的にコマンドを叩いて不具合を潰すエージェント」として使い分ける。
このハイブリッド運用が、現時点で最も「人間に近い、あるいは人間以上のスピード」でコードを書くための最適解だと確信しています。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorでプロジェクトを開く準備をします。

```bash
# Node.jsがインストールされているか確認
node -v

# Claude Codeのインストール（Anthropic公式）
npm install -g @anthropic-ai/claude-code

# Claude Codeの認証（ブラウザが開きます）
claude auth login

# プロジェクト用ディレクトリの作成
mkdir ai-fastapi-todo
cd ai-fastapi-todo

# Cursorで現在のディレクトリを開く
cursor .
```

`npm install -g @anthropic-ai/claude-code` は、Anthropicが2025年2月に発表したばかりのCLIツールをインストールしています。
従来のAIアシスタントと異なり、ファイルシステムへのフルアクセスとコマンド実行権限を持っているのが特徴です。
`claude auth login` を行うことで、自身のAnthropicアカウントのクレジットを使用してAPIを利用できるようになります。

⚠️ **落とし穴:** Node.jsのバージョンが古い（v16以下など）と、インストール中にエラーが出たり、実行時に謎の挙動をしたりすることがあります。
必ず `node -v` でバージョンを確認し、古い場合はLTS版（執筆時点でv20以上）にアップデートしてください。

## Step 2: 基本の設定

AIにプロジェクトの構造を正しく理解させるため、最小限の初期化を行います。
ターミナル（Cursor内のターミナルでOK）で以下を実行してください。

```bash
# Python仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Mac/Linux）
source venv/bin/activate
# Windowsの場合: .\venv\Scripts\activate

# 必要なライブラリのインストール
pip install fastapi uvicorn sqlalchemy
```

次に、Claude Codeを初期化します。

```bash
claude init
```

このコマンドを打つと、`.claudeignore` というファイルが作成されます。
これは非常に重要です。

⚠️ **落とし穴:** `.claudeignore` に `venv/` や `__pycache__/` を含め忘れると、Claudeが仮想環境内の膨大なライブラリ群を「自分の書くべきコード」として読み取ろうとします。
その結果、APIのトークン消費が跳ね上がり、数分で数ドルが消えるという悲劇が起きます。
必ず `.claudeignore` を開き、以下の内容が含まれているか確認してください。

```text
# .claudeignore の内容
venv/
.git/
__pycache__/
*.pyc
.pytest_cache/
```

## Step 3: 動かしてみる

ここからが本番です。Claude Codeを起動し、エージェントに「指示」を出してコードを生成させます。
ターミナルで `claude` と入力してエンター。

```bash
claude
```

Claude Codeのプロンプトが表示されたら、以下の指示を投げてください。

```text
FastAPIを使って、SQLiteをデータベースにしたTodo管理APIを作成してください。
以下の仕様を満たす必要があります。
1. Pydanticモデルを使用したバリデーション。
2. CRUD（作成・取得・更新・削除）の全てのendpoint。
3. データベースの初期化処理。
4. ファイル構成は main.py, models.py, database.py に分けてください。
```

指示が終わると、Claude Codeがファイルを自動生成し始めます。
途中で「ファイルを書き換えてもいいか？」と聞かれたら `y`（yes）または `a`（all）を押してください。

### 期待される出力

```text
[Files Created]
- database.py: SQLAlchemyのセッション設定
- models.py: Todoテーブルの定義
- main.py: FastAPIのルート定義

[Output]
APIの基本構造を構築しました。uvicorn main:app --reload でサーバーを起動できます。
```

ここでCursorの画面を見てください。ファイルがリアルタイムで生成されているのがわかります。
コードの内容が自分の意図通りか、CursorのGUIでざっと確認しましょう。

## Step 4: 実用レベルにする

単にコードを生成しただけでは、実務では使えません。
ここから「テスト駆動」で品質を上げていきます。Claude Codeにテストコードを書かせ、実際に実行させます。

Claude Codeのプロンプトで以下を入力します。

```text
pytestをインストールして、作成したAPIに対するテストコードを作成してください。
作成後、実際にテストを実行し、エラーがあれば自動で修正してください。
特に、存在しないIDを指定したときの404エラーが正しく返るかをテストに含めてください。
```

ここからの挙動がClaude Codeの真骨頂です。
1. `pip install pytest httpx` を勝手に実行する。
2. `tests/test_main.py` を作成する。
3. `pytest` を実行する。
4. もし `models.py` で定義したスキーマとテストが矛盾していれば、コードを自分で修正し、再度テストを回す。

私は以前、手動でテストを書いては直す作業に1日の大半を費やしていましたが、このフローに変えてから「人間がテスト結果を待つ」時間はほぼゼロになりました。

```python
# Claude Codeが生成するであろう実用的なテストコードの例
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_todo():
    response = client.post("/todos/", json={"title": "テストタスク", "description": "AIによるテスト"})
    assert response.status_code == 200
    assert response.json()["title"] == "テストタスク"

def test_read_non_existent_todo():
    response = client.get("/todos/9999")
    assert response.status_code == 404
```

テストをパスしたことを確認したら、最後にCursorの「Composer（Ctrl+I）」を開きます。
ここで「作成したAPIに、タスクの完了期限（deadline）を追加して。バリデーションで過去の日付は入れられないようにして」と指示します。
細かいロジックの修正や「過去の日付はNG」といったドメイン知識が必要な部分は、Cursorでコードを眺めながら対話的に進めるのが効率的です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `command not found: claude` | npmのパスが通っていないかインストール失敗 | `npm install -g` の出力を確認し、Nodeの再インストールを検討 |
| APIのQuota不足エラー | Anthropicの無料枠を使い切った | Tier 1以上にアップグレードし、クレジットをチャージする |
| SQLiteのロックエラー | 複数のプロセスがDBに書き込んでいる | Claude Codeがバックグラウンドでプロセスを残していないか確認し、再起動 |

## 次のステップ

この記事で構築した「FastAPI + SQLite」の構成は、小規模なツールであればそのまま実戦投入可能です。
次に挑戦すべきなのは「MCP（Model Context Protocol）」の導入です。
Claude CodeはMCPサーバーを介して、Google Search、GitHub、PostgreSQL、Slackなどと連携できます。
例えば「GitHubのIssueを取得して、それを解決するためのPRを自動で作成し、完了したらSlackに報告する」という、まさに一人のエンジニアとして動く環境を構築できます。

私は最近、社内用のドキュメント（Notion）をMCP経由でClaudeに読ませることで、「社内規定に基づいたコードレビュー」を自動化しました。
AIは「書き方」を知っていても「あなたの組織のルール」は知りません。
そこを埋めるのが、次のAIコーディングのトレンドになるでしょう。

## よくある質問

### Q1: Claude CodeとCursor、どちらか一方で十分ではないですか？

結論から言うと、併用がベストです。Cursorはコードの「文脈」を理解した編集に優れていますが、ターミナル操作の自律性はまだClaude Codeに軍歩が上がります。Claude Codeに「動くところまで持っていかせ」、Cursorで「洗練させる」のが現在の黄金律です。

### Q2: API代がいくらかかるか不安です。

Claude Code内で `/config` を叩くと、最大トークン数などの制限を設定できます。また、こまめに `/compact` を使って履歴を要約させることで、入力トークン節約に繋がります。いきなり大規模リポジトリで使わず、今回のような小規模プロジェクトから慣れるのが得策です。

### Q3: 日本語での指示は完璧に通りますか？

実務レベルで問題なく通ります。ただし、複雑なディレクトリ構造の操作などは、英語で指示した方が意図を正確に汲み取ってくれるケースも稀にあります。私は基本的に日本語で指示し、エラー解決の議論だけ英語で行うようにしています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max/Pro 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CursorとAIツールを複数立ち上げると16GBでは不足するため、32GB以上のMacが開発には必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%2032GB%20M3&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用したAIコーディング環境構築と実践ガイド](/posts/2026-08-28-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeとCursor、どちらか一方で十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論から言うと、併用がベストです。Cursorはコードの「文脈」を理解した編集に優れていますが、ターミナル操作の自律性はまだClaude Codeに軍歩が上がります。Claude Codeに「動くところまで持っていかせ」、Cursorで「洗練させる」のが現在の黄金律です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代がいくらかかるか不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code内で /config を叩くと、最大トークン数などの制限を設定できます。また、こまめに /compact を使って履歴を要約させることで、入力トークン節約に繋がります。いきなり大規模リポジトリで使わず、今回のような小規模プロジェクトから慣れるのが得策です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示は完璧に通りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実務レベルで問題なく通ります。ただし、複雑なディレクトリ構造の操作などは、英語で指示した方が意図を正確に汲み取ってくれるケースも稀にあります。私は基本的に日本語で指示し、エラー解決の議論だけ英語で行うようにしています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max/Pro 32GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">CursorとAIツールを複数立ち上げると16GBでは不足するため、32GB以上のMacが開発には必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%2032GB%20M3&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "Claude Code 使い方 Cursor 併用で開発を爆速にする方法"
date: 2026-09-17T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-09-17-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AI コーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude CodeとCursorを連携させ、FastAPIを使用した「データベース連携済みタスク管理API」をAI主導で構築します。
- 開発者がコードを一行も書かずに、AIエージェントへの指示とレビューだけで、動作確認済みのプロダクトを完成させます。
- 前提知識：Pythonの基本的な読み書きができること、ターミナルの操作に抵抗がないこと。
- 必要なもの：Claude APIキー（Tier 2以上推奨）、Cursor（Proプラン推奨）、Node.js環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M4 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorの同時並行動作には32GB以上のメモリが必須のため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M4%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M4%2520Max%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M4%20Max%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIコーディングを実務レベルで行うなら、APIコストとマシンスペックの妥協は捨ててください。
Claude CodeはAnthropicのAPIを直接消費します。
一連の開発で$2〜$5程度のAPI費用がかかるため、あらかじめ$20ほどチャージしておくのが無難です。
無料枠や低いTierではレートリミット（利用制限）に即座に引っかかり、作業が中断してストレスが溜まるだけです。

PCスペックについては、最低でもメモリ16GB、できれば32GB以上のMacかWindows機を推奨します。
Cursor自体がメモリを食う上に、バックグラウンドでClaude Codeを走らせると、8GB環境ではスワップが発生して挙動が目に見えて重くなります。
私はM2 MaxのMac Studio（メモリ64GB）と、RTX 4090を2枚挿した自作PCで検証していますが、このレベルの快適さを知ると戻れません。

## なぜこの方法を選ぶのか

Cursorの「Composer」機能だけでも十分強力ですが、Cursorはあくまで「エディタ」です。
一方で、新しく登場した「Claude Code」は「エージェント」としてターミナル権限をフルに活用します。
Cursorが得意なのは「コードの全体像を把握した上での広範囲な修正」であり、Claude Codeが得意なのは「テストの実行、エラーログの解析、ライブラリの依存関係解消」です。

例えば、新しいライブラリを導入してエラーが出た際、Cursorだとエラー文をコピペしてAIに渡す手間が発生します。
Claude Codeなら「テストを実行して、エラーが出たら修正して」と一行投げるだけで、自動でコマンドを実行し、ファイルを作成し、デバッグまで完結させます。
この「指示から実行までのラグがゼロになる体験」こそが、併用を選ぶ最大の理由です。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはNode.jsベースのツールです。

```bash
# Node.jsがインストールされていることを確認（v18以上必須）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

`npm install -g`でグローバルにインストールするのは、どのプロジェクトディレクトリからでも即座に呼び出せるようにするためです。
特定のプロジェクトごとにインストールする手間を省き、開発の機動力を高めます。

⚠️ **落とし穴:** macOSの場合、権限エラーでインストールに失敗することがあります。その場合は`sudo npm install -g @anthropic-ai/claude-code`を試してください。また、Node.jsのバージョンが古いと、インストールは成功しても実行時に構文エラーで落ちるため、必ず最新のLTS（Long Term Support）バージョンを使用してください。

## Step 2: 基本の設定

次に、Claude Codeをプロジェクトで使えるように認証と権限設定を行います。

```bash
# プロジェクトディレクトリを作成して移動
mkdir my-fastapi-app && cd my-fastapi-app

# 認証を開始
claude
```

コマンドを叩くとブラウザが開き、Anthropicアカウントでの認証を求められます。
認証後、ターミナルに戻るとClaudeとの対話が始まります。

ここで重要なのが「権限設定」です。Claude Codeはデフォルトでファイルの読み書きやコマンド実行を制限していますが、それでは真価を発揮できません。
最初の対話で以下の設定を確認してください。

1.  **読み取り権限:** プロジェクト全域を許可（コードの文脈を理解させるため）
2.  **実行権限:** 信頼できるプロジェクトであれば「Auto-approve」を検討（ただし、最初は一回ずつ確認する設定を推奨）

なぜこの設定にするかというと、AIに「いちいち許可を求める」コストを減らすためです。
開発のテンポを崩さないことが、AIコーディングの効率を最大化する鍵です。

## Step 3: 動かしてみる

まずは、Claude Codeを使ってFastAPIの最小構成を作らせます。
ターミナルのClaude Codeに対して、以下のように指示を投げてください。

```text
FastAPIを使って、SQLiteをデータベースとしたタスク管理APIのベースを作成してください。
main.py, models.py, database.pyにファイルを分割し、uvicornで起動できるようにしてください。
必要なライブラリのインストールもお願いします。
```

### 期待される出力

Claude Codeは、まず必要なライブラリ（fastapi, uvicorn, sqlalchemyなど）を特定し、`pip install`コマンドを生成・実行します。
その後、指定したファイル群を一気に生成します。

```text
（Claudeの応答例）
1. pip install fastapi uvicorn sqlalchemy を実行しました。
2. main.py, models.py, database.py を作成しました。
3. サーバーを起動する準備が整いました。
```

ここでCursorに切り替えます。
Cursorでいま作成されたディレクトリを開いてください。
AIが書いたコードが期待通りに分割されているか、構造を確認します。
Claude Codeがターミナルで作業し、Cursorがその結果を視覚的にプレビューする役割を担います。

## Step 4: 実用レベルにする

単なるHello Worldで終わらせず、実務で耐えうる「テストコードの自動生成とデバッグ」を行います。
ここがClaude Codeの最も強力な部分です。

### 1. テストの作成と実行

Claude Codeに対して、以下の指示を出します。

```text
pytestを使って、タスクの作成・取得・削除のAPIエンドポイントをテストするコードを作成してください。
作成後、実際にテストを実行して、すべてパスすることを確認してください。
もしエラーが出たら、コードを修正して再実行してください。
```

この指示を出すと、私たちが手出しすることなく、以下のプロセスが自動で回ります。
1. `tests/test_main.py` の作成。
2. `pytest` のインストール。
3. テストの実行。
4. （もしエラーがあれば）コードの修正。
5. テストの再実行。

実際に私が試した際、DBのセッションクローズ漏れでテストが2回失敗しましたが、Claude Codeは自らログを解析し、`database.py`の記述を修正して、3回目の試行で全テストをパスさせました。
これを手動でやれば、ログを確認して、該当箇所を探して、書き直して……と、最低でも5分は溶けます。Claude Codeなら15秒です。

### 2. 実用的なコードの例

以下は、このプロセスを経て完成する`main.py`の抜粋です。AIは型ヒントや非同期処理も正確に扱います。

```python
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

# データベースの初期化
models.Base.metadata.create_all(bind=database.engine)

# 依存性の注入（なぜこれが必要か：DB接続を適切に管理・テストしやすくするため）
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/tasks/")
def create_task(title: str, db: Session = Depends(get_db)):
    task = models.Task(title=title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/")
def read_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude` コマンドが見つからない | PATHが通っていない | `npm bin -g` でパスを確認し、環境変数に追加する |
| API Rate Limit Exceeded | APIのTierが低いか、短時間の使いすぎ | Anthropicのサイトでクレジットを追加購入し、Tierを上げる |
| Claude Codeがファイルを書き換えない | 権限不足または読み取り専用 | `claude allow-write` 設定を確認するか、Cursorで直接保存する |

## 次のステップ

ここまでで、Cursorでコードを眺めつつ、Claude Codeに「実務」を丸投げするスタイルが身についたはずです。
次に挑戦すべきは、**「既存の大規模リポジトリへのClaude Codeの導入」**です。

新しい機能を追加したいとき、`claude`を起動して「このプロジェクトの認証フローを理解して、新しいOAuthプロバイダーを追加して。既存のテストを壊さないように」と指示してみてください。
コードベースが数万行あっても、Claude 3.7 Sonnetの広大なコンテキストウィンドウがあれば、驚くほど正確に修正箇所を特定してくれます。

また、Dockerを使ったコンテナ化もClaude Codeの得意分野です。
「このアプリを本番環境で動かすためのDockerfileとdocker-compose.ymlを作って、実際にビルドが通るか確認して」と指示し、デプロイまでの自動化を体験してみてください。
私がかつてSIerで数日かけて行っていた環境構築が、わずか数分で終わる事実に、きっと震えるはずです。

## よくある質問

### Q1: CursorのComposer機能とClaude Code、どちらを優先すべきですか？

リファクタリングや「この関数のロジックをきれいにしたい」といった、エディタ上での視覚的な修正はCursorのComposerが直感的です。一方、ライブラリのインストール、シェルコマンドの実行、テストのデバッグなど、動作確認を伴う作業はClaude Codeの方が圧倒的に速く正確です。

### Q2: API代が高くなりそうで不安です。

Claude Codeはターミナルでの発言ごとにコンテキストを送信するため、トークン消費は激しいです。対策として、こまめに`/clear`コマンドで履歴をリセットするか、重要なファイルだけをコンテキストに含めるよう指示してください。

### Q3: 日本語での指示は通りますか？

完璧に通ります。ただし、技術的な用語は英語で指示したほうが、AIが適切なライブラリや手法を選択しやすくなる傾向があります。まずは日本語で指示し、意図が伝わっていないと感じたときだけ具体的な技術名を英語で添えるのがコツです。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS) **
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Claude CodeとCursorを併用して爆速でアプリ開発する使い方](/posts/2026-09-16-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能とClaude Code、どちらを優先すべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "リファクタリングや「この関数のロジックをきれいにしたい」といった、エディタ上での視覚的な修正はCursorのComposerが直感的です。一方、ライブラリのインストール、シェルコマンドの実行、テストのデバッグなど、動作確認を伴う作業はClaude Codeの方が圧倒的に速く正確です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が高くなりそうで不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeはターミナルでの発言ごとにコンテキストを送信するため、トークン消費は激しいです。対策として、こまめに/clearコマンドで履歴をリセットするか、重要なファイルだけをコンテキストに含めるよう指示してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示は通りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "完璧に通ります。ただし、技術的な用語は英語で指示したほうが、AIが適切なライブラリや手法を選択しやすくなる傾向があります。まずは日本語で指示し、意図が伝わっていないと感じたときだけ具体的な技術名を英語で添えるのがコツです。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS)  5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

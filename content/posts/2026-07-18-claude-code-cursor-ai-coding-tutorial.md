---
title: "Claude CodeとCursorを併用してAI開発を完全自動化する方法"
date: 2026-07-18T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-tutorial"
cover:
  image: "/images/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

ターミナルから直接コードを生成・実行・修正する「Claude Code」と、視覚的なコード編集に優れた「Cursor」を組み合わせ、FastAPIを用いたタスク管理APIをわずか数分で完成させます。

- Claude Codeでプロジェクトの雛形作成とライブラリ選定、テスト実行を自動化
- Cursorで生成されたコードの微調整とレビュー、ディレクトリ構造の把握を効率化
- 人間が1行もコードを書かずに、仕様定義から動作確認までを完結させるフロー

前提知識として、ターミナルの基本操作とPythonの基礎（仮想環境の作り方など）が必要です。

## 先に確認するスペック・料金

この環境を構築する前に、コストとハードウェアの要件を確認してください。まず、Claude CodeはAnthropicのAPI（主にClaude 3.5 Sonnet）を叩くため、月額定額ではなく「従量課金」となります。1つのプロジェクトをゼロから立ち上げるのに、$1〜$5程度のAPI費用を見込んでおくべきです。月額$20のClaude Proとは別枠なので注意してください。

エディタ側のCursorは、無料枠でも利用可能ですが、今回の「併用」を実務で回すならProプラン（月額$20）が必須です。モデルの推論回数制限に引っかかると開発効率が激減するからです。

ハードウェアについては、LLMをローカルで動かすわけではないため、RTX 4090のような怪物GPUは不要です。ただし、Claude CodeはNode.js上で動き、背後でファイル変更を監視し続けるため、メモリは最低でも16GB、できれば32GB以上を推奨します。私はM2 MaxのMacBook Pro（64GB）で運用していますが、ブラウザとCursor、Claude Codeを同時に動かすとメモリ消費が20GBを超えることも珍しくありません。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor（GUI）」と「Claude Code / Aider（CUI）」の2派閥に分かれています。Cursorはコードの書き換えやシンボル参照に強い一方、プロジェクト全体に跨るライブラリのインストールや、テスト結果をフィードバックして修正を繰り返す「自律的なループ」はまだ弱いです。

対してClaude Codeは、ターミナル上でシェルコマンドを実行し、その結果を見てコードを修正する能力に長けています。しかし、CUIだけではコードの全体像を俯瞰しにくく、複雑なUIの調整には不向きです。

この2つを併用することで、「Claude Codeに土台作りとデバッグを丸投げし、Cursorで人間が最終確認・微調整する」という、最もストレスの少ない開発体験が得られます。実際に私が実務で行っている、最も生産性が高いと断言できる構成です。

## Step 1: 環境を整える

まずはClaude Codeを使える状態にします。Claude CodeはNode.js環境を必要とするため、事前にインストールしておいてください。

```bash
# Node.js 18以上が必要です
node -v

# Claude Codeのグローバルインストール
npm install -g @anthropic-ai/claude-code

# 初期設定とログイン
claude auth
```

`npm install -g` を使うのは、どのプロジェクトからでも `claude` コマンドを呼び出せるようにするためです。`claude auth` を実行するとブラウザが開き、Anthropicアカウントでの認証を求められます。

⚠️ **落とし穴:**
Node.jsのバージョンが古いと、インストール時にエラーが出るか、実行中に予期せぬ挙動をします。`nvm` などのバージョン管理ツールを使い、安定版のLTS（Long Term Support）を利用しているか必ず確認してください。また、APIのクレジット（Credits）が0円の状態では動作しません。Anthropic Consoleから最低$5以上をチャージしておく必要があります。

## Step 2: 基本の設定

Claude Codeを動かす前に、プロジェクト専用のディレクトリを作成し、Cursorでそのディレクトリを開きます。この「同じディレクトリをGUIとCUIで同時に見る」のがポイントです。

```bash
mkdir ai-fastapi-app
cd ai-fastapi-app
# Cursorで現在のディレクトリを開く
cursor .
```

次に、Claude Codeを起動して初期設定を行います。

```bash
# Claude Codeの起動
claude
```

起動すると、プロジェクトのインデックス作成の許可を求められます。これはClaudeがプロジェクト内のファイルを理解するために必要な工程なので、迷わず `Yes` を選択してください。

次に、Cursor側の設定です。`.cursorrules` というファイルを作成し、AIに対して「Claude Codeと一緒に作業していること」を教えます。これをしないと、CursorがClaude Codeの変更を正しく検知できず、コードが先祖返りするリスクがあります。

```text: .cursorrules
- このプロジェクトではターミナルでClaude Codeが稼働しています。
- ファイルの作成や大規模なリファクタリングはClaude Codeが行います。
- あなた（Cursor）は、提供されたコードのレビュー、細かい型定義の修正、UIの調整に集中してください。
- ファイルが外部で変更された場合、即座にインデックスを再構築してください。
```

## Step 3: 動かしてみる

いよいよ、Claude Codeに命令を出してAPIの骨格を作らせます。ターミナル（Claude Codeのプロンプト）に以下を入力してください。

```text
Pythonの仮想環境を作成し、FastAPIとuvicornをインストールしてください。
その後、タスクを登録・取得できるシンプルなAPI（main.py）を作成して。
Pydanticを使ってリクエストのバリデーションも入れてください。
```

### 期待される出力

Claude Codeが自律的に以下のステップを実行します。
1. `python -m venv .venv` を実行
2. `source .venv/bin/activate`（またはWindowsのactivate）を実行
3. `pip install fastapi uvicorn` を実行
4. `main.py` を作成し、コードを書き込む

```python:main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

tasks = []

@app.post("/tasks")
def create_task(task: Task):
    tasks.append(task)
    return task

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks
```

この時、Cursorの画面を横に並べておくと、リアルタイムでファイルが生成され、コードが書き込まれていく様子が見えます。これが最高に気持ちいい瞬間です。

## Step 4: 実用レベルにする

ここからが本番です。単にコードを書くだけならCursorだけでもできますが、Claude Codeの本領は「エラー修正の自動化」にあります。わざとエラーが出るような命令を出して、それを修正させます。

```text
このAPIにSQLiteを使ったデータベース保存機能を追加してください。
SQLAlchemyを導入して、CRUD操作をすべて実装し直して。
実装が終わったら、実際にテストを実行して動作確認まで行ってください。
```

### 実装のポイント

Claude Codeは、`pip install sqlalchemy` を実行し、`database.py` や `models.py` を分割して作成することを提案してくるはずです。ここでの「なぜ」は明確です。実務では1ファイルにすべてを詰め込むとメンテナンス性が落ちるため、AIにも「関心の分離」を意識させることが重要だからです。

### テストの自動化

Claude Codeに「pytestを使ってテストコードを書いて、テストが通るまで修正して」と指示してください。

```python:test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"id": 1, "title": "Test Task"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"
```

Claude Codeは自ら `pytest` を実行し、エラーが出ればそのスタックトレースを読み取り、`main.py` や `models.py` を修正しに行きます。人間は、ターミナルで流れるログを眺めているだけで、最終的に「All tests passed」の文字を見ることになります。

最後に、Cursor側でコードの見た目を整えます。Cursorの「Composer（Ctrl+I）」を開き、「コード全体をPEP8に準拠するようにリファクタリングして」と頼めば、インポート順の整理やコメントの追加を綺麗に仕上げてくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm list -g` で場所を確認しパスを通すか、再起動する |
| APIのタイムアウト | コンテキストが大きすぎる | `/compact` コマンドで会話履歴を要約し、メモリを節約する |
| ライブラリの競合 | 仮想環境が未有効 | `source .venv/bin/activate` が実行されているか確認 |

## 次のステップ

お疲れ様でした。Claude CodeとCursorの併用フローが身につけば、これまで数時間かかっていたプロトタイプ作成が数十分に短縮されます。

次のステップとしては、以下のことに挑戦してみてください。
1.  **Docker化の自動化**: Claude Codeに「このアプリをDockerコンテナで動かせるようにDockerfileとdocker-compose.ymlを作って」と頼む。
2.  **CI/CDの設定**: GitHub Actionsの設定ファイルを生成させ、自動テスト環境を構築する。
3.  **フロントエンドとの接続**: Next.jsなどを同じプロジェクト内に構築させ、APIと連携するUIを作らせる。

特に、Claude Codeに「ブラウザでの動作確認」まで実行させる（最近のアップデートで可能になりつつあります）と、さらに開発の自動化レベルが上がります。AIはもはや「相談相手」ではなく、指示を完遂する「自律型の部下」として扱う時代です。

## よくある質問

### Q1: Claude Codeを使うとAPI料金が高くなりそうで怖いのですが？

確かに、何も考えずに大規模なリファクタリングを繰り返すと数ドル単位で消費します。対策として、`/usage` コマンドで現在の消費額をこまめにチェックしてください。また、不要なファイルは `.claudeignore` に記述して、AIが読み込まないように制限するのが鉄則です。

### Q2: CursorのAIとClaude Code、どちらを信じればいいですか？

実行結果（ターミナルの出力）を伴う作業については、常にClaude Codeを優先してください。Cursorはコードの見た目や構造を提案する「設計士」、Claude Codeは実際に手を動かして動くものを作る「現場監督」という役割分担が、実務では最も安定します。

### Q3: 日本語での指示でも大丈夫ですか？

全く問題ありません。Claude 3.5 Sonnetは日本語の理解力が極めて高く、複雑なニュアンスも汲み取ってくれます。ただし、プログラミング用語（リファクタリング、バリデーション、デプロイなど）はカタカナや英語で明確に伝える方が、AIも迷わずに正確なコードを生成します。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorの同時稼働には32GB以上のメモリが実務上必須です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)
- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うとAPI料金が高くなりそうで怖いのですが？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "確かに、何も考えずに大規模なリファクタリングを繰り返すと数ドル単位で消費します。対策として、/usage コマンドで現在の消費額をこまめにチェックしてください。また、不要なファイルは .claudeignore に記述して、AIが読み込まないように制限するのが鉄則です。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのAIとClaude Code、どちらを信じればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実行結果（ターミナルの出力）を伴う作業については、常にClaude Codeを優先してください。Cursorはコードの見た目や構造を提案する「設計士」、Claude Codeは実際に手を動かして動くものを作る「現場監督」という役割分担が、実務では最も安定します。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示でも大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。Claude 3.5 Sonnetは日本語の理解力が極めて高く、複雑なニュアンスも汲み取ってくれます。ただし、プログラミング用語（リファクタリング、バリデーション、デプロイなど）はカタカナや英語で明確に伝える方が、AIも迷わずに正確なコードを生成します。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Claude CodeとCursorの同時稼働には32GB以上のメモリが実務上必須です</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

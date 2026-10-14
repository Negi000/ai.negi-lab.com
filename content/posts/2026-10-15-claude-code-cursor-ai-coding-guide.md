---
title: "CursorとClaude Codeを併用して爆速でAPI開発を行う方法｜AIコーディング環境入門"
date: 2026-10-15T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-10-15-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 開発効率"
  - "AIコーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- FastAPIとSQLiteを使用した「AIによる自動タグ付け機能付きタスク管理API」
- Cursorで全体の設計とコード確認を行い、Claude Codeに実装・テスト・デバッグを丸投げする開発フロー
- 最終的にローカル環境でAPIが動作し、自動テストがパスする状態を目指します

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorを同時並行で動かしても詰まらないメモリ性能が必要</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Pythonの基本的な文法とターミナルの操作ができることを想定しています。

## 先に確認するスペック・料金

AIコーディングを本気で実務に投入するなら、ツールへの投資は必須です。
まず、Cursorは月額$20のProプランを契約してください。
無料枠でも動きますが、Claude 3.5 Sonnetを制限なく使えないと開発体験が著しく落ちます。

次にClaude Codeですが、これはAnthropicのAPIキーを直接利用するため、従量課金制です。
大規模なリファクタリングをさせると1回で$1〜$5程度飛ぶこともあります。
目安として、月額予算$50程度（Cursor $20 + API $30）を見込んでおけば、実務レベルの恩恵を十分に受けられます。

ハードウェアについては、VS Codeが快適に動くスペックなら問題ありません。
私はMacBook Pro (M3 Max / 64GB) で検証していますが、メモリは最低でも16GB、できれば32GB以上あると、複数のAIツールを走らせても挙動が安定します。

## なぜこの方法を選ぶのか

Cursorの「Composer」機能は非常に強力ですが、ターミナルでのコマンド実行やテストの修正ループにはまだ弱点があります。
一方でClaude Codeは、ターミナルそのものにAIが常駐しているため、ファイルの作成、テストの実行、エラーの修正を自律的に繰り返す「エージェント」として極めて優秀です。

設計や大きな構造の変更はCursorのGUIで視覚的に管理し、面倒な実装作業やテスト駆動開発のループはClaude Codeに任せる。
この「視覚的な管理」と「実行力の自動化」を組み合わせるのが、2025年現在で最も効率的な開発手法だと断言できます。
どちらか一方だけを使うよりも、お互いの弱点を補完し合うことで、開発速度は体感で3倍以上変わります。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。
これはNode.js環境が必要になるため、事前にインストールしておいてください。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

次に、AnthropicのコンソールからAPIキーを取得し、環境変数に設定します。
`~/.zshrc` や `~/.bashrc` に追記しておくと便利です。

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

なぜこの設定が必要かというと、Claude Codeはあなたの代わりにコマンドを実行し、ファイルを書き換えるため、常に最新のClaude 3.5 Sonnetモデルと通信する必要があるからです。

⚠️ **落とし穴:**
Claude Codeを初めて起動した際、`/auth` での認証を求められることがあります。
また、macOSの場合、ターミナルからのファイル操作権限（フルディスクアクセス）を許可していないと、AIがファイルを書き換える際にエラーで止まることがあります。
「Permission denied」が出たら、システム設定から権限を確認してください。

## Step 2: プロジェクトの初期化と設計

ここからはCursorを開き、新しいディレクトリで作業を開始します。
まずはプロジェクトのルートで、最低限必要な依存関係を定義した `requirements.txt` を作成します。

```text
fastapi
uvicorn
sqlalchemy
pydantic
openai
```

次に、Cursorのチャット（Ctrl+L / Cmd+L）を開き、以下の指示を出して設計の骨子を作らせます。

> 「FastAPIとSQLiteを使って、タスク管理APIを作りたい。タスクにはタイトル、内容、ステータス、そしてAIが自動生成する『カテゴリタグ』を含める。まずはプロジェクト構造とデータベースのスキーマ設計を提案して。」

Cursorが提案した設計を確認し、「OK、それで進めて」と返せば、必要なフォルダ構造が作られます。
ここでCursorを使う理由は、提案されたコードをエディタ上で即座にプレビューでき、設計の全体像を視覚的に把握しやすいからです。

## Step 3: Claude Codeに実装を丸投げする

設計が決まったら、いよいよClaude Codeの出番です。
ターミナルで `claude` コマンドを叩いて起動してください。

```bash
claude
```

Claude Codeが起動したら、以下のプロンプトを投げます。

> 「現在のディレクトリにある設計を元に、FastAPIの実装を行って。特に、タスクが作成された時にOpenAI API（または互換API）を使って内容から適切なカテゴリタグを自動生成して保存するロジックを実装して。実装が終わったら、実際にサーバーを起動して動作確認用のテストスクリプトも作成・実行して、すべてパスすることを確認して。」

Claude Codeは、指示を受けると以下の手順を勝手に進めます。
1. `main.py` や `models.py` のコードを書き込む
2. `pytest` や自前のテストスクリプトを作成する
3. サーバーをバックグラウンドで起動し、実際にリクエストを送ってテストする
4. テストが失敗したら、エラーログを読み取り、コードを修正して再試行する

### 期待される出力

Claude Codeの画面上で、以下のようなログが流れるはずです。

```
[Thinking] 実装を開始します...
[Write] main.py を作成しました
[Run] uvicorn main:app --reload &
[Run] pytest test_main.py
[Result] 3 tests passed, 1 failed.
[Thinking] 自動タグ付け部分でAPIキーが設定されていないエラーが発生しました。修正します。
[Write] main.py を修正（エラーハンドリングを追加）
[Run] pytest test_main.py
[Result] All tests passed!
```

この「自分でテストして、自分で直す」というプロセスがClaude Codeの真骨頂です。
人間はコーヒーを飲んで待っているだけで、バグのない初期実装が完了します。

## Step 4: 実用レベルにするためのCursor連携

Claude Codeが作ったコードは、時として「機能は満たすが、可読性が低い」あるいは「ディレクトリ構成が独特」な場合があります。
ここで再びCursorに戻ります。

CursorのComposer（Ctrl+I / Cmd+I）を開き、生成された全ファイルを対象にして、以下のリファクタリングを指示します。

```python
# 実用的なコード例のイメージ
# main.py の一部を以下のようにリファクタリングさせる
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 依存性注入の定義
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # AIによるタグ生成ロジックをサービス層に分離させる指示を出す
    return crud.create_ai_task(db=db, task=task)
```

Cursorを使う理由は、コードの「見た目」や「プロジェクトの作法」を調整するのには、GUIベースの差分確認（Diff）が最適だからです。
Claude Codeに任せた部分を、自分の好みのコーディングスタイルに一括修正させます。

また、APIキーの設定などは `.env` ファイルに切り出し、`pydantic-settings` を使うように指示すると、より実務的な構成になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが止まる | ファイルの書き込み権限不足 | ターミナルの「フルディスクアクセス」を許可する |
| API料金が高すぎる | Claude Codeが無限ループしている | `Ctrl+C` で即座に停止し、指示を具体的にする |
| テストが通らない | 依存ライブラリの不足 | `claude` に「不足しているライブラリをpipで入れて」と指示 |

## 次のステップ

ここまでで、AIエージェントとIDEを組み合わせた最短の開発フローを体験できました。
次に挑戦すべきは、「既存の巨大なプロジェクトへの適用」です。

新しい機能を追加したい時に、Claude Codeに対して「このディレクトリにある既存の認証ロジックを読み取って、新しい管理画面用のAPIを追加して」と指示を出してみてください。
その際、Cursorで事前に `git diff` を確認できるようにしておくと、AIが予期せぬ場所を書き換えた時にもすぐに気づけます。

また、ローカルLLM（Ollama等）と接続して、機密性の高いコードはローカルで、複雑なロジックはClaudeで、という使い分けを模索するのも面白いでしょう。
私の環境ではRTX 4090を活用して、簡単なリファクタリングはローカルのQwen 2.5 32Bで行っています。

## よくある質問

### Q1: Cursorだけで十分ではないですか？

CursorのComposerも素晴らしいですが、複数のターミナルコマンドを組み合わせて、テスト結果を見ながらコードを自己修正する自律性は、現状Claude Codeの方が一歩先を行っています。
「AIに丸投げできる範囲」を広げたいなら、併用がベストです。

### Q2: API課金が怖いです。節約する方法は？

Claude Codeに渡すコンテキスト（読み込ませるファイル）を最小限に絞ることです。
不要な `node_modules` や `__pycache__` を読み込ませないよう、`.gitignore` を適切に設定してください。
また、作業の区切りで一度終了させるのも効果的です。

### Q3: 日本語での指示でも大丈夫ですか？

全く問題ありません。
Claude 3.5 Sonnetは日本語のニュアンスを完璧に理解します。
ただし、技術的な用語は英語のままの方が、AIがドキュメントを参照する際に正確性が増すことがあります。

---

## あわせて読みたい

- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用！爆速AIコーディング環境構築ガイド](/posts/2026-07-11-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorだけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも素晴らしいですが、複数のターミナルコマンドを組み合わせて、テスト結果を見ながらコードを自己修正する自律性は、現状Claude Codeの方が一歩先を行っています。 「AIに丸投げできる範囲」を広げたいなら、併用がベストです。"
      }
    },
    {
      "@type": "Question",
      "name": "API課金が怖いです。節約する方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeに渡すコンテキスト（読み込ませるファイル）を最小限に絞ることです。 不要な nodemodules や pycache を読み込ませないよう、.gitignore を適切に設定してください。 また、作業の区切りで一度終了させるのも効果的です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示でも大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。 Claude 3.5 Sonnetは日本語のニュアンスを完璧に理解します。 ただし、技術的な用語は英語のままの方が、AIがドキュメントを参照する際に正確性が増すことがあります。 ---"
      }
    }
  ]
}
</script>

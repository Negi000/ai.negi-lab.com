---
title: "Claude CodeとCursorを併用して爆速でアプリ開発する環境構築ガイド"
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
  - "Cursor 活用術"
  - "AIコーディング 環境構築"
  - "FastAPI 自動開発"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、エディタ型のCursorとCLI型のClaude Codeをシームレスに使い分け、FastAPIを使用した「タスク管理API（データベース連携・認証機能付き）」をほぼ自動で作り上げます。
単にコードを書くだけでなく、テストの実行、バグの自動修正、GitコミットまでをAIに完結させるフローを構築します。
Pythonの基礎知識があり、ターミナル操作に抵抗がない方を対象としています。

## 先に確認するスペック・料金

AIコーディングを本気で仕事に使うなら、ケチってはいけないのが「ツールへの課金」です。
CursorのProプラン（月額$20）は必須と言えます。無料枠では「Composer」という最強の複数ファイル編集機能が制限され、真価を発揮できません。
Claude CodeはAnthropicのAPI（Claude 3.5 Sonnet）を直接消費します。
私が中規模な機能を1つ実装させるのに使った感触では、1タスクあたり$0.5〜$2程度のAPI費用がかかります。

ハードウェアについては、MacBook ProならM2/M3チップ、メモリ32GB以上を強く推奨します。
AIツールを複数立ち上げ、ローカルでテストサーバーを動かしながらブラウザで検証すると、16GBではスワップが発生してレスポンスが目に見えて落ちるからです。
Windowsユーザーなら、WSL2環境の構築は必須です。Claude Codeのファイル操作はUnixライクな環境で最も安定します。

## なぜこの方法を選ぶのか

現在、GitHub CopilotやCline（旧Claude Dev）など多くの選択肢がありますが、現時点での最適解は「Cursor」と「Claude Code」の併用です。
Cursorは「静的なコード記述」において右に出るものがいません。コードの補完や、エディタ上での対話的な修正には最適です。
一方、Claude Codeは「動的な実行と解決」に特化しています。
ターミナル上でテストを走らせ、エラーが出たらその内容を読み取り、自律的にファイルを修正して再度テストする。このループの速さはCursorを超えています。
「UIで微調整したい時はCursor、プロジェクト全体の構造変更やバグ修正はClaude Code」という使い分けが、最も開発効率を高めると結論づけました。

## Step 1: 環境を整える

まずはClaude Codeを動かすためのNode.js環境と、本体のインストールを行います。

```bash
# Node.jsが20.0.0以上であることを確認
node -v

# Claude Codeのインストール（Anthropic公式のCLIツール）
npm install -g @anthropic-ai/claude-code

# インストールの確認
claude --version
```

Claude CodeはNode.jsで動作するCLIツールです。
なぜnpmでインストールするのかというと、これがAnthropicが提供するエージェント型AIの実行環境そのものだからです。
次に、プロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-app-demo
cd ai-app-demo
cursor .
```

⚠️ **落とし穴:** Claude Codeを動かす際、環境変数 `ANTHROPIC_API_KEY` が設定されていないと起動しません。`.bashrc` や `.zshrc` に書き込むか、起動時に渡す必要があります。また、初回起動時に `claude auth` での認証を求められる場合があります。

## Step 2: 基本の設定

Claude Codeをプロジェクトに最適化させるため、設定ファイルを作成します。
といっても、手動で書く必要はありません。Claude Codeに「初期設定をして」と頼むのが正解です。

```bash
# ターミナルで実行
claude
```

初回起動時にいくつかの許可を求められますが、すべて「y（Yes）」で進めて問題ありません。
特に、ファイル読み書きの権限とターミナル実行の権限は、Claude Codeが自律的に動くために不可欠です。

```python
# .env ファイルの作成（手動またはCursorで）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxx
DATABASE_URL=sqlite:///./test.db
```

私はAPIキーを直接スクリプトに書く習慣をSIer時代に厳しく禁じられました。
AIにコードを書かせると、たまにハードコードしようとするので、「環境変数から読み込むように」と指示する癖をつけておきましょう。
これはセキュリティ上の理由だけでなく、本番環境へのデプロイをスムーズにするためでもあります。

## Step 3: 動かしてみる

それでは、Claude Codeに「FastAPIの最小構成」を作らせてみましょう。
ターミナルの `claude` プロンプトに対して以下のように入力します。

```text
/task FastAPIで「Hello World」を返すAPIを作成して。
ディレクトリ構成は、src/配下にmain.pyを置く形にして。
作成できたら、uvicornでサーバーを起動するコマンドも教えて。
```

### 期待される出力

```text
（Claudeがファイルを生成し、以下のような実行コマンドを提示します）
I have created the FastAPI application.
You can run it using:
uvicorn src.main:app --reload
```

Claude Codeが凄いのは、ここで実際に `ls` や `cat` を自分で叩いて、ファイルが正しく生成されたかを確認しに行く点です。
Cursorを使っているなら、左側のファイルツリーに即座に `src/main.py` が現れるはずです。
このように「CLIで命令し、エディタで確認する」のが基本スタイルになります。

## Step 4: 実用レベルにする

ここからが本番です。単なるHello Worldではなく、データベース（SQLite）と連携したタスク管理機能を追加します。
以下の指示をClaude Codeに投げてください。

```text
/task 以下の機能を実装してください。
1. SQLAlchemyを使用したSQLite連携。
2. Taskモデル（id, title, description, status）の作成。
3. タスクの作成、一覧取得、更新のAPIエンドポイント。
4. 全ての実装が終わったら、実際にテストコードを書いて実行し、成功することを確認して。
```

Claude Codeは、必要なライブラリ（sqlalchemy, pydanticなど）が足りなければ、自分で `pip install` を提案、または実行します。
もしテストでエラーが出れば、そのスタックトレースを読み取り、自力で `main.py` を修正してくれます。
私は以前、自力でこのデバッグ作業を行っていましたが、Claude Codeに任せることで修正までのレスポンスは0.5秒程度、実際の修正完了まで数分という驚異的な速さを体感しました。

```python
# 実用的なコードの断片（Claudeが生成するはずのコード例）
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    status = Column(String, default="todo")

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ここにエンドポイントが続く...
```

コードが生成されたら、Cursorの「Composer（Cmd+I）」を開き、生成されたコードに対して「このAPIにバリデーションを追加して」などと、エディタ側でUIを見ながら微調整を行います。
「ロジックの構築はClaude Code、UIや細かな仕様変更はCursor」という役割分担が、最もストレスなく開発を進められます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが同じ修正を繰り返す | テストコード自体に不備がある | 一度 `/stop` で止めて、手動でテストコードを修正するか、具体的に「テストを修正して」と指示する |
| APIキーのクォータ制限 | 短時間に大量のトークンを消費した | Tierを上げるか、Claude 3.5 SonnetではなくHaiku（安価版）への切り替えを検討する |
| Cursorとファイルが競合する | 両方で同時にファイルを保存しようとした | Claude Codeが実行中のときは、Cursor側での編集を控えるのが無難 |

## 次のステップ

この環境が整えば、次は「自律型エージェント」としての側面を強化しましょう。
例えば、「GitHubのIssueを読み取って、自動でプルリクエストを作成するスクリプト」をこの環境で作ってみてください。
Claude Codeには `/compact` コマンドがあり、コンテキスト（会話の履歴）を整理してトークンを節約する機能もあります。

AIコーディングの本質は、AIにコードを書かせることではなく、「AIが正しく動ける環境を整え、自分はレビューに専念する」という役割の転換にあります。
今回構築したCursor × Claude Codeの体制は、その第一歩として、現時点で間違いなく最強の組み合わせです。
ぜひ、自分の既存プロジェクトをこの環境に取り込んで、その圧倒的な開発速度を体験してみてください。

## よくある質問

### Q1: Claude Codeを使うとAPI料金が高くなりそうで不安です。

確かに、自律的に動くためトークン消費は激しいです。しかし、エンジニアの時給を$50と考えるなら、数ドルのAPI代で1時間の作業が5分で終わるのは圧倒的に安上がりです。`/stats` コマンドで現在の消費量を確認しながら使いましょう。

### Q2: Cursorだけで十分ではないですか？

CursorのComposerも優秀ですが、ターミナルの出力結果（テスト結果やサーバーのログ）をリアルタイムに、かつ深いコンテキストで理解して修正する能力は、現時点ではClaude Code（CLI）に軍配が上がります。

### Q3: 日本語での指示で問題ありませんか？

全く問題ありません。Claude 3.5 Sonnetは非常に高い日本語理解能力を持っています。ただし、専門用語（「冪等性を担保して」「非同期処理にして」など）を混ぜることで、より正確なコードが生成されやすくなります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツール複数起動とローカル検証には32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを最強にするclaude-skills比較とおすすめPC構成｜買う前に知るべきVRAMとメモリ](/posts/2026-07-06-claude-skills-pc-specs-comparison-guide/)
- [Munder Difflin 使い方と実務評価：Claude Codeを自律型エージェント化する実践ガイド](/posts/2026-08-15-munder-difflin-claude-code-agent-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うとAPI料金が高くなりそうで不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "確かに、自律的に動くためトークン消費は激しいです。しかし、エンジニアの時給を$50と考えるなら、数ドルのAPI代で1時間の作業が5分で終わるのは圧倒的に安上がりです。/stats コマンドで現在の消費量を確認しながら使いましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "Cursorだけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも優秀ですが、ターミナルの出力結果（テスト結果やサーバーのログ）をリアルタイムに、かつ深いコンテキストで理解して修正する能力は、現時点ではClaude Code（CLI）に軍配が上がります。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示で問題ありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。Claude 3.5 Sonnetは非常に高い日本語理解能力を持っています。ただし、専門用語（「冪等性を担保して」「非同期処理にして」など）を混ぜることで、より正確なコードが生成されやすくなります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIツール複数起動とローカル検証には32GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

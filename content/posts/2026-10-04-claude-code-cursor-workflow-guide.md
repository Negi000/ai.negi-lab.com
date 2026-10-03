---
title: "Claude CodeとCursorを併用し、バックエンドのAPIサーバー構築から自動テスト、Gitコミットまでを完全にAI主導で完結させる手法を解説します。"
date: 2026-10-04T00:00:00+09:00
slug: "claude-code-cursor-workflow-guide"
cover:
  image: "/images/posts/2026-10-04-claude-code-cursor-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "FastAPI チュートリアル"
  - "AIコーディング エージェント"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

FastAPIを使用した「非同期処理対応のタスク管理API」を構築します。
単なるコード生成ではなく、Claude Codeによる「テスト実行→エラー修正→ドキュメント生成→Gitコミット」という一連のエージェントワークフローを体験するのが目的です。

- **前提知識:** Pythonの基本的な文法がわかること、ターミナルの基本操作ができること。
- **必要なもの:** Anthropic APIキー（クレジットのチャージが必要）、Node.js（v18以上）、Python環境。

## 先に確認するスペック・料金

AIコーディングを本気で行うなら、ハードウェア以上に「APIコスト」への理解が重要です。
Claude Codeはターミナルの出力を読み取り、ファイル全体をコンテキストに含めるため、1回の命令で$0.1〜$0.5程度のトークンを消費することがあります。
月額$20のCursor Proとは別に、AnthropicのAPIコンソールで$20〜$50程度のプリペイド枠を確保しておくのが実務的なラインです。

マシン性能については、CursorもClaude CodeもクラウドのLLMを叩くため、ローカルLLM運用のようなVRAM 24GB超えのモンスターマシンは必須ではありません。
ただし、Cursorのインデックス作成や複数プロセスの実行を考慮すると、メモリは最低でも32GB、CPUはApple SiliconのM2/M3 Pro以上があると、入力の遅延（チャタリング）に悩まされず快適に作業できます。

## なぜこの方法を選ぶのか

Cursorだけでもコーディングは完結しますが、Cursorの「Composer」はあくまでエディタ上のコード書き換えに特化しています。
一方でClaude Codeは「ターミナルを操作できるエージェント」であり、テストの実行結果を見て自律的にデバッグを行う能力が圧倒的に高いです。

「Cursorで全体の構造を眺めながらUIを整え、Claude Codeに重たいロジックの実装とテスト、リファクタリングを丸投げする」
この役割分担が、2024年現在のAIエンジニアリングにおいて最も生産性が高いと断言できます。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorからターミナルを開いて連携の準備をします。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが立ち上がります）
claude auth

# プロジェクトディレクトリの作成と移動
mkdir ai-build-app && cd ai-build-app
git init
```

Claude CodeはNode.js環境で動作するCLIツールです。
`npm install`でグローバルにインストールすることで、ターミナルのどこからでも`claude`コマンドを呼び出せるようになります。
また、Gitリポジトリを初期化しておくのは、Claude Codeが変更履歴を読み取ってコミットメッセージを自動生成するために必須の作業です。

⚠️ **落とし穴:** Node.jsのバージョンが古いとインストールに失敗します。`node -v`で18.x以上であることを確認してください。また、AnthropicのAPIキーにクレジット（お金）が入っていないと、認証は通っても動作時にエラーが出ます。

## Step 2: 基本の設定

プロジェクトのルートで`claude`コマンドを叩き、エージェントを起動します。
この際、Cursorも同じディレクトリで開いておき、常にファイルの変化を可視化できるようにします。

```bash
# ターミナルでClaudeを起動
claude
```

Claude Codeが起動したら、まず最初に「このプロジェクトのルール」を定義させます。
これをすることで、生成されるコードの品質が安定します。

```text
# Claudeの対話画面で入力
プロジェクトを初期化して。Python 3.11、FastAPI、Pydantic v2を使用。
テストはpytestで行い、ディレクトリ構成は src/ と tests/ に分けること。
```

なぜこの構成にするのか。
それは、Claude Codeが「標準的な構成」を好むからです。
独自のオレオレ構成にするよりも、一般的でドキュメントが豊富な構成を指定する方が、AIが生成するコードのバグ率が劇的に下がります。

## Step 3: 動かしてみる

次に、APIの骨格を作らせます。
ここでのポイントは、一度にすべてを作らせようとせず、まずは「動く最小単位」を指定することです。

```text
# Claudeへの指示
src/main.pyに、健康状態を返す /health エンドポイントと、
タスク一覧を返す /tasks エンドポイントを作成して。
タスクはメモリ上で保持する形でOK。
作成が終わったら、実際にサーバーを起動してcurlで動作確認までやって。
```

### 期待される出力

Claude Codeが勝手にファイルを生成し、ターミナルで`uvicorn`を実行し、別のプロセスで`curl`を叩いて結果を表示します。

```text
> [Running: touch src/main.py]
> [Running: pip install fastapi uvicorn]
> [Running: curl http://localhost:8000/health]
{"status": "ok"}
```

私たちがコードを一行も書かずに、環境構築から動作確認までが終わりました。
結果の読み方として重要なのは、Claude Codeが「コマンドの実行結果（標準出力）」を正しく認識しているかどうかを確認することです。

## Step 4: 実用レベルにする

ここからがClaude Codeの真骨頂です。
「テスト駆動開発（TDD）」をAIに代行させます。
Cursorでコードを眺めながら、不備がある部分や追加したい機能をClaude Codeに伝えます。

```text
# Claudeへの指示
タスクの追加（POST）と更新（PUT）機能を追加して。
その後、tests/test_main.pyを作成して、正常系と異常系（存在しないIDの更新など）のテストコードを書いて。
最後に pytest を実行して、全てのテストが通るまで自分でコードを修正して。
```

この「テストが通るまで自分で修正して」という指示が、Cursor単体では難しいポイントです。
Claude Codeはテスト結果のエラーログを読み取り、`main.py`のロジックミスを特定し、修正して再テストする、というループを勝手に回します。

```python
# Claudeが生成する実用的なコード例の一部
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

tasks = []

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    if any(t.id == task.id for t in tasks):
        raise HTTPException(status_code=400, detail="ID already exists")
    tasks.append(task)
    return task
```

実務レベルにするための「エラーハンドリング（HTTPException）」や「型定義（Pydantic）」が、指示しなくても正確に組み込まれているのがわかるはずです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm bin -g`でパスを確認し、環境変数に追加する |
| `Overloaded Error` | Anthropicのサーバー負荷 | 30秒待って再試行。改善しない場合はAPIキーのティアを確認 |
| 無限ループでトークン消費 | テストが一生通らない指示 | `Ctrl+C`で即停止し、手動でコードの矛盾を修正する |

## 次のステップ

この環境が整えば、次は「DB（PostgreSQL）との連携」や「認証（Auth0やFirebase Auth）の実装」をClaude Codeに依頼してみてください。
その際、Cursorの「Chat」機能で「このコードの設計に問題はないか？」とレビューさせ、実際の修正作業はClaude Codeに「ターミナル経由」でやらせるのがベストな運用です。

AIは「書く」のは得意ですが、「実行して確認する」プロセスを自動化できるClaude Codeを併用することで、あなたの開発スピードは従来の3倍以上に加速します。
まずは今日作ったAPIに、1つだけ新しいバリデーションを追加するところから始めてみてください。

## よくある質問

### Q1: CursorのComposer機能とClaude Code、どちらを優先すべき？

基本はCursorでコードを読み書きし、CLI操作が伴う作業（ライブラリ導入、テスト実行、マイグレーション、デバッグ）はClaude Codeに任せるのが効率的です。画面で確認しながらの方が安心な作業はCursor、結果がバイナリやログで出るものはClaude Codeと使い分けましょう。

### Q2: APIコストを抑えるコツはありますか？

`.claudeignore`ファイルを作成し、AIに読み込ませる必要のない大きなログファイルやバイナリ、依存ライブラリ（node_modulesなど）を除外してください。コンテキスト（読み取る情報量）を減らすことが、直接的な節約に繋がります。

### Q3: 会社のプロジェクトで使っても大丈夫？

Claude Codeは、入力したデータを学習に利用しない設定（API経由のため）が可能ですが、社内規定で「外部AIへのコード送信」自体が制限されている場合があります。必ず自社のセキュリティポリシーを確認し、必要に応じてオプトアウト申請を行ってください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールとローカル検証を同時に回す開発環境に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-08-19-claude-code-cursor-ai-coding-tutorial/)
- [Claude Code 使い方 Cursor 併用で開発を爆速にする方法](/posts/2026-09-17-claude-code-cursor-ai-coding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能とClaude Code、どちらを優先すべき？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本はCursorでコードを読み書きし、CLI操作が伴う作業（ライブラリ導入、テスト実行、マイグレーション、デバッグ）はClaude Codeに任せるのが効率的です。画面で確認しながらの方が安心な作業はCursor、結果がバイナリやログで出るものはClaude Codeと使い分けましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "APIコストを抑えるコツはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ".claudeignoreファイルを作成し、AIに読み込ませる必要のない大きなログファイルやバイナリ、依存ライブラリ（nodemodulesなど）を除外してください。コンテキスト（読み取る情報量）を減らすことが、直接的な節約に繋がります。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロジェクトで使っても大丈夫？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeは、入力したデータを学習に利用しない設定（API経由のため）が可能ですが、社内規定で「外部AIへのコード送信」自体が制限されている場合があります。必ず自社のセキュリティポリシーを確認し、必要に応じてオプトアウト申請を行ってください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">複数のAIツールとローカル検証を同時に回す開発環境に最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

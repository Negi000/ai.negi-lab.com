---
title: "Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド"
date: 2026-08-19T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-tutorial"
cover:
  image: "/images/posts/2026-08-19-claude-code-cursor-ai-coding-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIエージェント コーディング"
  - "FastAPI テスト自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Cursorでフロントエンドとバックエンドの骨組みを作り、Claude Codeで複雑なロジックの実装と全自動テストを実行する、FastAPIを用いた「タスク管理API」を作成します。
Pythonの基本的な読み書きができることを前提に、AIエージェントに「丸投げ」するのではなく「並走」するための具体的なワークフローを構築します。
必要なものは、AnthropicのAPIキー（Tier 2以上推奨）、Cursor Pro、Node.js環境、そしてPython 3.10以上です。

## 先に確認するスペック・料金

この環境を構築する前に、財布とマシンの準備が必要です。
まず、Claude CodeはAnthropicのAPI（Claude 3.5 Sonnet）を直接叩くため、月額20ドルのCursor Proとは別に、プリペイド式のAPI利用料がかかります。
目安として、中規模なプロジェクトで1日ガッツリ触ると$5〜$10程度は平気で飛びますが、それ以上に「自分の時間が浮く」価値があるかを判断基準にしてください。
APIのTier（ランク）が低いとレートリミットですぐ止まるため、最低でも$50以上の入金を済ませてTier 2にしておくのが実務で使うための最低条件です。

PCスペックについては、Cursorのインデックス処理とClaude Codeのローカル解析が走るため、メモリ32GB以上のMac（M2/M3以上）か、Linux機を推奨します。
私はRTX 4090を2枚積んだ自宅サーバーで開発していますが、Claude Code自体はクラウドのLLMを叩くCLIツールなので、ネット回線の安定性の方が重要です。
WindowsユーザーはWSL2環境が必須だと思ってください。PowerShell直叩きだとClaude Codeのシェル実行機能でパスの解釈がバグることが多々あります。

## なぜこの方法を選ぶのか

Cursorの「Composer」機能は非常に優秀ですが、あくまで「エディタが見ている範囲」の修正がメインです。
プロジェクト全体を俯瞰した大規模なリファクタリングや、実際にテストコードを走らせてエラーを修正し続ける「自律的なデバッグ」に関しては、Claude Codeの方が圧倒的に粘り強いです。
一方で、Claude CodeはCLI（黒い画面）なので、UIの微調整や1行単位のコード補完には向きません。

「Cursorで構造を書き、Claude Codeで中身を詰め、実行結果を見てCursorで微修正する」というループが、現時点で最も開発速度が速い。
Aider（別のAIコーディングツール）も試しましたが、Claude CodeはAnthropic公式ツールなだけあって、最新モデルのトークン上限やシステムプロンプトの最適化が群を抜いています。
自律型エージェントに勝手にコードを書き換えられる恐怖感はありますが、その「制御方法」をこの記事で解説します。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorからターミナルを呼び出せる状態にします。

```bash
# Node.js 18以上が必要です
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 初期設定と認証（ブラウザが立ち上がります）
claude auth login
```

Claude Codeは、あなたの代わりに「ターミナルでコマンドを叩く」権限を持ちます。
そのため、必ず自分が信頼できるディレクトリ内でのみ実行するようにしてください。
インストールが終わったら、適当な空ディレクトリを作成し、Cursorでそのディレクトリを開きます。

⚠️ **落とし穴:**
Node.jsのバージョンが古いと、Claude Codeのインストール時にエラーが出る、あるいは実行時にWebSocketが切断されることがあります。
nvmなどで最新のLTS（Long Term Support）バージョンに切り替えてからインストールしてください。
また、APIのクレジットが残高不足だと、認証は通っても実行時に「Credit balance too low」という素っ気ないエラーで止まります。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに、Claude Codeが「勝手に触ってはいけないファイル」を教えるための設定を行います。

```bash
# プロジェクト用ディレクトリ作成
mkdir ai-task-app && cd ai-task-app
# Cursorで開く
cursor .
```

次に、`.gitignore` と同じように `.claudecodeignore` を作成します。
ここには、ビルド成果物や仮想環境、巨大なデータファイルを含めます。
これを忘れると、Claude Codeが全ファイルをスキャンしようとしてトークン代が数千円単位で溶ける可能性があります。

```text
# .claudecodeignore
node_modules/
__pycache__/
venv/
.venv/
.git/
*.log
dist/
```

次に、Pythonの仮想環境を作成し、FastAPIをインストールします。

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linuxの場合
pip install fastapi uvicorn pytest httpx
```

## Step 3: 動かしてみる

ここからが本番です。Cursorを立ち上げたまま、その中のターミナルで `claude` コマンドを叩きます。
すると、対話型のインターフェースが始まります。

```bash
claude
```

まず、Claude Codeに「これから作るものの概要」を伝えます。

**私への入力例:**
> 「FastAPIを使って、タスク管理ができるAPIを作成してください。
> 機能はタスクの一覧取得、作成、削除。データはメモリ上に保持でOK。
> まずは `main.py` を作成して、サーバーが起動することを確認して。」

### 期待される出力

Claude Codeがカチャカチャとファイルを生成し始めます。
途中で「`pip install` を実行してもいいですか？」などの許可を求められるので、内容を確認して `y` を押します。

```python
# main.py の例
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

tasks = []

@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    tasks.append(task)
    return task
```

ファイルが作成されたら、Cursorのエディタ画面を確認してください。
リアルタイムで `main.py` が生成されているはずです。
このように「生成はClaude Code、中身の閲覧はCursor」という役割分担が基本です。

## Step 4: 実用レベルにする

ここからClaude Codeの真骨頂である「テスト駆動開発（TDD）」を自動で行わせます。
手動でテストを書くのは面倒ですが、AIなら一瞬です。

**私への入力例:**
> 「作成したAPIに対して、pytestを使ったテストコードを `tests/test_main.py` に作成して。
> その後、実際にテストを実行して、全てのテストがパスすることを確認して。
> エラーが出たら、`main.py` を修正して解決するまで繰り返して。」

この指示により、Claude Codeは以下のループに入ります。
1. `tests/test_main.py` を作成
2. `pytest` コマンドを実行
3. エラーが出ればスタックトレースを読み取り、修正案を考える
4. `main.py` またはテストコードを書き換える
5. 再び `pytest` を実行

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"id": 1, "title": "Test Task"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"

def test_get_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

実務でよくある「パスの通し忘れ」や「型定義のミス」も、Claude Codeは自分で実行して気づくため、私たちがデバッグする必要はありません。
私はこの機能を使って、既存の1,000行クラスのリファクタリングを15分で終わらせました。
テストが通ることを担保しながら書き換えてくれる安心感は、Cursorの補完だけでは得られないものです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Command not found: claude` | パスが通っていない | `npm list -g` で場所を確認しパスを通す |
| `Permission denied` | 実行権限がない | `chmod +x` するか `sudo` ではなく環境を見直す |
| `Token limit exceeded` | ファイルが多すぎる | `.claudecodeignore` を正しく設定する |
| `API Error: 402` | クレジット不足 | Anthropicのコンソールで課金設定を確認 |

## 次のステップ

この「Cursor + Claude Code」の連携に慣れてきたら、次は **MCP（Model Context Protocol）** を試してみてください。
Claude Codeから、あなたのローカルにあるデータベースや、Google検索、GitHubのIssueを直接参照できるようになります。
例えば「GitHubのIssue #12の内容を読み取って、その機能を実装してテストまで終わらせて」という指示が可能になります。

また、複雑なリファクタリングをする際は、一度に全部をやらせようとせず、「まずは関数の分割だけ」「次に型ヒントの追加」「最後にテストの作成」というように、段階的にClaude Codeと会話するのがコツです。
一度指示を投げたら、手を離してコーヒーを飲んで待つ。
画面上でファイルが書き換わり、ターミナルでテストが緑色（パス）に染まっていくのを眺めるのが、これからのエンジニアの仕事になります。

## よくある質問

### Q1: CursorのComposer機能だけで十分ではないですか？

Composerは「UIを見ながら、その場でコードを直す」のには最適です。しかし、複数のターミナルコマンドを組み合わせて結果を検証したり、プロジェクト全体の整合性を数分間にわたって思考し続けるタスクには、Claude Codeの「エージェント性」が勝ります。使い分けが重要です。

### Q2: API代が怖いです。節約する方法はありますか？

`.claudecodeignore` を徹底することと、不要な履歴を食わせないために適宜 `/compact` コマンド（コンテキストの圧縮）を使うのが有効です。また、大きな修正の前には必ず `git commit` しておき、AIが暴走して変な修正をしてもすぐに戻せるようにしておきましょう。

### Q3: 会社のプロプライエタリなコードに使っても大丈夫ですか？

Claude Codeはデフォルトで、入力したデータがモデルの学習に使われない設定になっています（API経由のため）。ただし、会社のセキュリティポリシーによります。機密情報が含まれるファイルは必ず `.claudecodeignore` に入れ、個人情報などが含まれないように注意してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIエージェントの並列処理とIDEの同時稼働には64GB以上のメモリが理想的</p>
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
- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能だけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Composerは「UIを見ながら、その場でコードを直す」のには最適です。しかし、複数のターミナルコマンドを組み合わせて結果を検証したり、プロジェクト全体の整合性を数分間にわたって思考し続けるタスクには、Claude Codeの「エージェント性」が勝ります。使い分けが重要です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ".claudecodeignore を徹底することと、不要な履歴を食わせないために適宜 /compact コマンド（コンテキストの圧縮）を使うのが有効です。また、大きな修正の前には必ず git commit しておき、AIが暴走して変な修正をしてもすぐに戻せるようにしておきましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロプライエタリなコードに使っても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeはデフォルトで、入力したデータがモデルの学習に使われない設定になっています（API経由のため）。ただし、会社のセキュリティポリシーによります。機密情報が含まれるファイルは必ず .claudecodeignore に入れ、個人情報などが含まれないように注意してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIエージェントの並列処理とIDEの同時稼働には64GB以上のメモリが理想的</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド"
date: 2026-10-19T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-10-19-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング"
  - "自動デバッグ"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

GitHubのリポジトリ情報を取得し、要約してSlackに通知する「AI駆動型ニュースレターBot」を構築します。
Cursorで全体の設計とUIを作成し、Claude Codeでテスト実装とデバッグを自動化する、現在の私が行き着いた最強のワークフローを再現します。
Pythonの基礎知識（仮想環境の構築ができる程度）があれば、この記事の手順をなぞるだけで、AIエージェントが自律的にコードを修正する感覚を体験できます。

## 先に確認するスペック・料金

AIコーディングを本気で仕事に使うなら、無料枠で粘るのは時間の無駄です。
まず、Cursor Pro（月額$20）は必須です。無料版のClaude 3.5 Sonnet制限は、実務では1時間で使い切ります。
次にClaude Codeを使用するためのAnthropic APIクレジットが必要です。
プリペイド式で最低$5からチャージできますが、本気で開発するなら最初に$20ほど入れておくと、途中で思考が止まらずに済みます。

ハードウェアについては、MacBook Air（M2/M3）のメモリ16GB以上を推奨します。
私はRTX 4090を2枚挿した自作サーバーでローカルLLMも動かしていますが、Claude Codeのようなクラウドベースのツールを使う際も、ブラウザ、IDE、ターミナルを同時に立ち上げるため、メモリ8GBではスワップが発生してレスポンスが悪化します。
また、VS Codeに慣れている人は多いと思いますが、CursorはVS Codeをフォークしているため、移行コストはほぼゼロです。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「IDE型（Cursor）」と「CLIエージェント型（Claude Code, Aider）」の2つに二極化しています。
Cursorはコード全体の構造を把握し、複数ファイルを跨いだ変更を「提案」するのが得意ですが、実行結果を見て修正を繰り返す「試行錯誤」には、まだ人間の手動操作（コマンド実行など）が介入する余地が多いです。
一方で、Claude Codeはターミナル上で動作し、テストの実行、エラーログの読み取り、修正、再テストというループを自律的に回す能力に長けています。

私は当初、どちらか一方で完結させようとしましたが、それは非効率だと気づきました。
Cursorで「設計図」を書き、Claude Codeに「現場監督」を任せる。
この役割分担により、人間がコードをコピペしてターミナルに貼り付ける作業が消滅し、開発速度は体感で3倍以上になりました。
レスポンスが0.5秒遅れるだけで思考は途切れますが、この組み合わせは今のところ最も「脳の延長」に近いツールチェーンです。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。Node.js（v18以上）が必要です。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが立ち上がります）
claude auth
```

次に、Pythonの開発環境を整えます。

```bash
mkdir ai-news-bot
cd ai-news-bot
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
pip install fastapi uvicorn requests python-dotenv pytest
```

ここで重要なのは、`.venv`（仮想環境）を必ず作成することです。
Claude Codeは環境を読み取ってコマンドを実行するため、グローバルな環境を汚さないように配慮しておかないと、依存関係の解決でAIが混乱して無駄なトークンを消費します。

⚠️ **落とし穴:**
Claude Codeの初回実行時に、ファイルへの書き込み権限やコマンドの実行権限を求められます。
ここで慎重になりすぎて制限をかけすぎると、AIが「テストが実行できないので修正が完了したか判断できない」という状態に陥ります。
信頼できるプロジェクトディレクトリであれば、`Allow all` を選択するのが、作業を止めないコツです。

## Step 2: 基本の設定

プロジェクトのルートに、環境変数を管理する `.env` ファイルと、Cursor用の設定ファイルを作成します。

```python
# .env
GITHUB_TOKEN=your_github_token
SLACK_WEBHOOK_URL=your_webhook_url
```

次に、Cursorの「Composer」機能（Cmd+I）を開きます。
ここで、プロジェクト全体の骨組みを作るための指示を出します。

**指示プロンプト例:**
> FastAPIを使って、GitHubの特定リポジトリのスター数と最新のIssueを取得し、Slackに通知するスクリプト `main.py` を作成して。
> 1. `config.py` で環境変数を読み込む。
> 2. `github_client.py` でAPIリクエストを行う。
> 3. `slack_client.py` で通知を行う。
> 非同期処理（httpxなど）を使って効率的に動作させて。

なぜこの設定にするのか。それは「関心の分離」をAIに徹底させるためです。
一つのファイルに全てを書き込むと、後の修正でClaude Codeが読み込むトークン量が増え、コストと精度の両方が悪化します。
最初からモジュール化を指示しておくのが、AIと長く付き合うための基本テクニックです。

## Step 3: 動かしてみる

Cursorがコードを生成したら、次はClaude Codeの出番です。
ターミナルで `claude` と打ち込み、エージェントを起動します。

```bash
claude
```

ここからの操作は、対話型になります。

```text
> github_client.py の動作を確認するための pytest コードを作成して。
> その後、実際にテストを実行して、エラーがあれば自動で修正して。
```

### 期待される出力

```
[Claude Code]
1. github_client_test.py を作成しました。
2. pytest を実行中...
3. 401 Unauthorized エラーを検出しました。GITHUB_TOKEN が正しく読み込まれていない可能性があります。
4. .env の読み込み処理を config.py に追加しました。
5. テストを再実行... 100% Passed.
```

このように、Claude Codeは「エラーを自分で見つけて自分で直す」というフェーズで真価を発揮します。
Cursorで作成したコードには、大抵の場合、環境依存の小さなバグが混入します。
それを人間がいちいち直すのではなく、エージェントに「直るまで回せ」と命じるのが現代のやり方です。

## Step 4: 実用レベルにする

ここからが本番です。実務で使えるレベルにするために、リトライトライ（再試行）処理とエラーハンドリングを追加します。
これはClaude Codeが得意とする「コードの堅牢化」のプロセスです。

```text
> 現在の実装だと、GitHub APIのレート制限に引っかかった時に即座にエラーになります。
> 指数バックオフ（Exponential Backoff）を用いたリトライ処理を github_client.py に追加してください。
> また、Slackへの通知が失敗した際もログに出力し、再試行するように変更してください。
```

具体的に出力されるコードの一部は、以下のようになるはずです。

```python
import time
import functools
import logging

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logging.error(f"Failed after {retries} retries.")
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x)
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator
```

この変更を加える際、Claude Codeは既存の関数定義を壊さずに、デコレータを適切に挿入してくれます。
私が以前、手動でこれを行った時は、インポート忘れや引数の渡しミスで2〜3回やり直しましたが、Claude Codeなら一発です。
実務においては、「動くコード」よりも「落ちないコード」の方が価値が高い。
その「落ちないための泥臭い実装」をAIに丸投げできるのは、大きなアドバンテージです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `command not found: claude` | パスが通っていない | `npm list -g` で場所を確認し、PATHに追加するか再インストールする |
| `Rate limit reached` (Anthropic API) | 短時間の大量リクエスト | APIのTierを上げるか、Claude Codeの `compact` オプションを検討する |
| `.env` が無視される | Claude Codeのコンテキスト不足 | `claude -p "READ .env file"` のように明示的にファイルを読ませる |

## 次のステップ

ここまでで、CursorとClaude Codeを併用した「設計」→「実装」→「自律デバッグ」のサイクルが完成しました。
このワークフローをマスターした後は、以下のカスタマイズに挑戦してみてください。

1.  **GitHub Actionsとの連携**:
    今回作ったスクリプトを、GitHub Actionsで定期実行するように変更します。Claude Codeに「このプロジェクトを毎日午前9時に実行するためのworkflow yamlファイルを作って」と頼むだけです。
2.  **LLMによる要約の追加**:
    GitHubのIssueの内容を、Claude APIを使って3行に要約してからSlackに送るように拡張します。
3.  **ローカルLLMとのハイブリッド運用**:
    機密性の高いロジックはCursor + ローカルLLM（Ollama等）で書き、公開可能な外部API連携部分はClaude Codeで高速に仕上げる。

AIコーディングは、もはや「コードを書いてもらう」段階から「エージェントを指揮する」段階に移行しています。
最初はAPI料金が気になるかもしれませんが、自分の時給と、バグ修正に溶ける数時間を天秤にかけてみてください。
月数千円の投資で、24時間文句を言わずにテストを回し続けるジュニアエンジニアを雇えると考えれば、これほど安い投資はありません。

## よくある質問

### Q1: Cursorだけで十分ではないですか？

CursorのComposerも進化していますが、ターミナルでのコマンド実行結果をループして修正する能力は、現時点ではClaude Codeの方が専用設計されている分、強力です。特に複雑なライブラリの依存関係エラーを解消する際は、Claude Codeの方が迷いが少ない印象です。

### Q2: API利用料が跳ね上がるのが怖いです。

Claude Codeを起動しっぱなしにせず、特定のタスク（例：テストをパスさせる）が終わったら一旦終了する癖をつけましょう。また、指示を出す前に `claude status` で現在のトークン消費量を確認するのも有効です。私は1プロジェクトのデバッグで$1〜$2程度を基準にしています。

### Q3: 日本語での指示でも問題ないですか？

全く問題ありません。むしろ、複雑なロジックの意図を伝えるには日本語の方が精度が高い場合もあります。ただし、エラーメッセージやログは英語で出力されることが多いため、AIへのフィードバックは「このErrorログを見て直して」と、英語の事実をベースに日本語で指示を出すのが最も効率的です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Air M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツールとIDEを同時駆動させるには16GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築と実践](/posts/2026-10-09-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用し、バックエンドのAPIサーバー構築から自動テスト、Gitコミットまでを完全にAI主導で完結させる手法を解説します。](/posts/2026-10-04-claude-code-cursor-workflow-guide/)

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
        "text": "CursorのComposerも進化していますが、ターミナルでのコマンド実行結果をループして修正する能力は、現時点ではClaude Codeの方が専用設計されている分、強力です。特に複雑なライブラリの依存関係エラーを解消する際は、Claude Codeの方が迷いが少ない印象です。"
      }
    },
    {
      "@type": "Question",
      "name": "API利用料が跳ね上がるのが怖いです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeを起動しっぱなしにせず、特定のタスク（例：テストをパスさせる）が終わったら一旦終了する癖をつけましょう。また、指示を出す前に claude status で現在のトークン消費量を確認するのも有効です。私は1プロジェクトのデバッグで$1〜$2程度を基準にしています。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示でも問題ないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。むしろ、複雑なロジックの意図を伝えるには日本語の方が精度が高い場合もあります。ただし、エラーメッセージやログは英語で出力されることが多いため、AIへのフィードバックは「このErrorログを見て直して」と、英語の事実をベースに日本語で指示を出すのが最も効率的です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Air M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIツールとIDEを同時駆動させるには16GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "Claude CodeとCursorを併用して爆速でアプリ開発する使い方"
date: 2026-09-16T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/og-default.png"
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

Claude Codeでバックエンド（FastAPI）のロジックとテストを自動生成し、CursorのComposer機能でフロントエンドを整える「AIフル活用開発フロー」を実践します。
Pythonの基礎知識があれば、指示を出すだけで「非同期処理を含むAPIサーバー」と「その動作を確認するクライアント」が完結した状態で手に入ります。
ローカル環境のファイルをAIエージェントに直接操作させる快感と、エディタでの精密な修正を組み合わせるハイブリッドな手法を体験してください。

## 先に確認するスペック・料金

AIコーディングの最前線を走るには、無料枠だけでは限界があります。
まず、Cursorは月額$20のProプランが必須です。無料枠のClaude 3.5 Sonnet回数制限では、今回のような大規模な生成で思考が中断されるストレスに耐えられません。
次にClaude Codeですが、これはAnthropicのAPI（従量課金）を使用します。1プロジェクトをゼロから立ち上げるのに、$1〜$5程度のデポジットは覚悟してください。

ハードウェア面では、M1チップ以降のMacBook（メモリ16GB以上）を推奨します。
Windowsでも動作しますが、Node.jsのバージョン管理や実行権限周りで詰まることが多いため、WSL2環境の構築が前提となります。
「ローカルLLMを動かすわけではないから低スペックでいい」というのは誤解です。
IDE（Cursor）、ブラウザ、バックエンドサーバー、そしてClaude Codeのプロセスを同時に動かすと、メモリ8GBのPCではスワップが発生して開発効率が著しく落ちます。

## なぜこの方法を選ぶのか

現在、Cursor単体でも開発は可能ですが、ファイル数が増えてくると「どのファイルに影響があるか」を人間が指示する手間が発生します。
Claude Codeは「エージェント」として動作するため、ターミナルから「この機能を実装してテストまで通しておいて」と投げるだけで、複数のファイルを跨いだ修正、ライブラリのインストール、テストの実行までを自律的に行います。

一方で、Claude CodeはCLIツールであるため、複雑なコードの微調整や、UIの細かいデザイン修正には向きません。
そこで、プロジェクトの骨組みや重たいロジック生成を「Claude Code」に任せ、成果物を「Cursor」のGUIで確認・ブラッシュアップする分業体制が現状のベストプラクティスです。
GitHub CopilotやCline（旧Devin）も試しましたが、Anthropic純正エージェントの「指示への忠実さ」とCursorの「エディタとしての完成度」の組み合わせが、最も手戻りが少なく、実務で使える速度が出ます。

## Step 1: 環境を整える

まずはClaude CodeをインストールするためのNode.js環境を確認します。

```bash
# Node.jsのバージョン確認（v18以上が必須）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストールが成功したか確認
claude --version
```

Claude CodeはAnthropicの公式ツールですが、実行にはAPIキーが必要です。
ブラウザでAnthropicのコンソールを開き、`Settings` > `Billing` から数ドル分をチャージしておいてください。

⚠️ **落とし穴:**
Macの場合、`npm install -g` で権限エラー（EACCES）が出ることがあります。
その場合は `sudo` を使いたくなりますが、環境が汚れるため推奨しません。
`nvm`（Node Version Manager）を使用して、ユーザーディレクトリ配下にNode.jsをインストールし直すのが、後々のトラブルを防ぐ王道です。

## Step 2: 基本の設定

インストールが終わったら、プロジェクト用のディレクトリを作成し、Claude Codeを認証します。

```bash
mkdir ai-app-dev && cd ai-app-dev
claude auth
```

ブラウザが立ち上がるので、ログインして認証を完了させてください。
次に、Claude Codeがプロジェクトをどう扱うかの初期設定を行います。

```bash
claude init
```

ここで `.claudecode/` フォルダが作成されます。
なぜこの初期化が必要かというと、Claude Codeが「このプロジェクトで実行して良いコマンド」や「無視すべきファイル（.gitignoreの代わり）」を把握するためです。
これを怠ると、AIが無限ループするスクリプトを実行してしまい、API料金を数分で溶かすリスクがあります。

## Step 3: 動かしてみる

それでは、Claude Codeに最初の大きな仕事を任せます。
「FastAPIを使って、SQLiteにデータを保存する簡単なTODOアプリのバックエンドを作って」と指示します。

```bash
claude "FastAPIを使ってTODO管理APIを作ってください。データベースはSQLiteを使用し、Pydanticでバリデーションも入れてください。完了したらuvicornで起動できるようにして。"
```

### 期待される出力

```text
1. main.py を作成しました（FastAPIの定義）
2. database.py を作成しました（SQLAlchemyの設定）
3. models.py を作成しました（テーブル定義）
4. requirements.txt を生成しました
5. pip install -r requirements.txt を実行しました
...
準備が整いました。'uvicorn main:app --reload' で起動できます。
```

Claude Codeの凄いところは、コードを書くだけでなく、依存ライブラリが足りなければ自ら `pip install` を提案し、実行まで行う点です。
私は以前、これと同じことを手動でやっていましたが、ボイラープレート（定型コード）を書くだけで15分は使っていました。
Claude Codeなら、私がコーヒーを一口飲んでいる間に、実働するサーバーが組み上がります。

## Step 4: 実用レベルにする

ここからがCursorの出番です。
Claude Codeが作ったバックエンドに対して、Cursorの「Composer（Ctrl+I または Cmd+I）」を使って、フロントエンドのHTML/JavaScriptを追加します。

1. Cursorで現在のフォルダを開きます。
2. `Ctrl+I` を押し、以下のプロンプトを入力します。
   「main.pyのAPIを叩く、モダンなTailwind CSSを使ったindex.htmlを作成して。完了後、main.pyを修正して、このindex.htmlを静的ファイルとして配信するように変更して。」

```python
# Cursorが修正するmain.pyの例
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Cursorが自動で追加する静的ファイルの配信設定
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')
```

なぜこの工程をCursorで行うのか。
それは、画面レイアウトの微調整は「プレビューを見ながら、特定の行を数ピクセル直す」という試行錯誤の連続だからです。
CLIのClaude Codeに「もっとボタンを右に」と頼むのは非効率ですが、Cursorならコードの横にチャットがあるため、直感的に指示を出せます。

次に、Claude Codeに戻って「テストコード」を書かせます。
実務で最も面倒な「正常系・異常系のテスト」こそ、AIエージェントの得意分野です。

```bash
claude "pytestを使って、CRUD操作が全て正常に動作するか確認するテストコードを書いて実行して。もしエラーが出たら、コードを修正してパスさせて。"
```

ここが最大のポイントです。
Claude Codeは自分でテストを実行し、エラーメッセージを見て、自力で `main.py` のバグを修正します。
私の役割は、ターミナルに流れるログを眺めて、最後に「All tests passed」と表示されるのを確認するだけです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `command not found: claude` | パスが通っていない | `npm bin -g` でパスを確認し、`.zshrc`等に追加 |
| API Quota Exceeded | Anthropicの無料枠終了 | コンソールからクレジットをチャージ（最低$5〜） |
| ファイル書き込み権限エラー | OS側の制限 | 実行中のターミナルにフルディスクアクセスの権限を付与 |
| 依存関係の競合 | 既存のPython環境との衝突 | `python -m venv venv` で仮想環境を先に作り、activateした状態でClaude Codeを動かす |

## 次のステップ

このフローをマスターしたら、次は「MCP（Model Context Protocol）」の導入を検討してください。
MCPを使えば、Claude CodeにGoogleカレンダーやGitHubのIssue、さらにはローカルのデータベースの中身までを「知識」として与えることができます。
例えば、「DBにある昨日の売上データを集計して、グラフを描画するPythonコードを生成して実行し、結果をSlackに投げて」といった、コーディングの枠を超えた「業務自動化エージェント」へと進化させることが可能です。

また、Cursorの設定で「rules for AI（.cursorrules）」を書き込むことも忘れないでください。
「型ヒントを必ず入れる」「DocstringはGoogleスタイルで」といった自分好みのルールを定義しておけば、Claude CodeとCursorのどちらを使っても、統一感のある美しいコードが維持されます。
AIに丸投げするのではなく、AIが「私らしいコード」を書くためのレールを敷くこと。
それが、これからのエンジニアに求められる最も重要なスキルです。

## よくある質問

### Q1: Claude Codeを使うとAPI料金が跳ね上がりそうで怖いです。

Claude Codeはプロンプトのたびにプロジェクトのファイル構造を読み込むため、大規模プロジェクトでは1回数円〜数十円かかります。
対策として `claude ignore` ファイルを作成し、`node_modules` や `__pycache__`、巨大なデータファイルをAIの視界から外すことが不可欠です。

### Q2: CursorのComposerとClaude Codeの使い分けが分かりません。

「新しい機能の追加や、ファイルが5つ以上にまたがる修正」はClaude Code、「今開いているファイルのロジック修正やUIの微調整」はCursorと使い分けてください。
イメージとしては、Claude Codeが「設計もする敏腕若手プログラマー」、Cursorが「自分の手足となる超高性能な筆記用具」です。

### Q3: セキュリティ面で、会社のコードをClaude Codeに読み込ませても大丈夫ですか？

AnthropicのAPI利用規約では、API経由のデータはモデルの学習に利用されないと明記されています。
ただし、環境変数（.env）に生パスワードなどを書いていると、それをコンテキストとして送信してしまうため、`.env` は必ず `claude ignore` に追加する設定を徹底してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールとローカルサーバーを同時に動かすには32GB以上のメモリが実務上の最低ライン</p>
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
- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用する最強AIコーディング環境の使い方](/posts/2026-07-31-claude-code-cursor-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うとAPI料金が跳ね上がりそうで怖いです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeはプロンプトのたびにプロジェクトのファイル構造を読み込むため、大規模プロジェクトでは1回数円〜数十円かかります。 対策として claude ignore ファイルを作成し、nodemodules や pycache、巨大なデータファイルをAIの視界から外すことが不可欠です。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのComposerとClaude Codeの使い分けが分かりません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「新しい機能の追加や、ファイルが5つ以上にまたがる修正」はClaude Code、「今開いているファイルのロジック修正やUIの微調整」はCursorと使い分けてください。 イメージとしては、Claude Codeが「設計もする敏腕若手プログラマー」、Cursorが「自分の手足となる超高性能な筆記用具」です。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で、会社のコードをClaude Codeに読み込ませても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI利用規約では、API経由のデータはモデルの学習に利用されないと明記されています。 ただし、環境変数（.env）に生パスワードなどを書いていると、それをコンテキストとして送信してしまうため、.env は必ず claude ignore に追加する設定を徹底してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">複数のAIツールとローカルサーバーを同時に動かすには32GB以上のメモリが実務上の最低ライン</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

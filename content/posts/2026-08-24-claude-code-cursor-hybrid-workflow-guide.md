---
title: "Claude CodeとCursorを使い分ける最強のAIコーディング環境構築ガイド"
date: 2026-08-24T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-08-24-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI 開発"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude Code（CLI）でバックエンドのロジックを高速生成し、Cursor（IDE）でフロントエンドと全体の構成を微調整する、ハイブリッドなAI開発ワークフローを構築します。
最終的に、FastAPIを使用した「AI要約機能付きタスク管理ツール」を、コードを一行も手書きせずに完成させます。

- 前提知識：ターミナルの基本操作ができる、Pythonの環境構築（venv等）を知っている。
- 必要なもの：Anthropic APIキー（Tier 1以上推奨）、Cursor Proプラン、Node.js環境（Claude Code用）。

## 先に確認するスペック・料金

AIコーディングを本格化するなら、ツールの料金とAPIコストの把握は必須です。
まず、Cursorは月額$20のProプランを契約してください。無料枠ではコンテキスト制限ですぐに手が止まります。
次にClaude Codeですが、これはCursorのようにサブスク型ではなく、AnthropicのAPI（Claude 3.5 Sonnet）を直接消費します。
中規模なアプリ開発を1日行うと、トークン消費で$5〜10程度かかることも珍しくありません。

ハードウェアについては、AIが生成したコードを即座にビルド・テストするため、メモリ32GB以上のMac（M2/M3以上）か、WSL2が動くWindows機を推奨します。
私はRTX 4090を積んだ自作機でローカルLLMも併用していますが、今回の構成はクラウドAPIがメインなので、ブラウザとエディタが快適に動けば問題ありません。
ただし、APIキーの「Usage Limit」を事前に設定しておかないと、バグで無限ループが発生した際に数万円溶かすリスクがあるため注意してください。

## なぜこの方法を選ぶのか

Cursorだけでも開発は可能ですが、なぜわざわざClaude Codeを併用するのか。
結論、Claude Codeは「ターミナルとファイル操作の権限」がCursorより強力だからです。
CursorのComposer機能は画面上のUIとして優れていますが、複雑なリファクタリングや依存関係の解決において、CLI（コマンドライン）で動作するClaude Codeの方が圧倒的に成功率が高い。

Claude Codeは、自身の判断でテストを実行し、エラーが出たらその場で修正して再度実行するという「自律的なループ」を回せます。
一方で、UIの微調整や複数ファイルにまたがるコードの視認性はCursorに軍配が上がります。
「ロジック構築とデバッグはClaude Code」、「全体の構成把握とフロントエンドの微調整はCursor」という役割分担が、2024年末時点での開発効率を最大化するベストプラクティスだと断言します。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはnpmパッケージとして提供されています。

```bash
# Node.js 18以上が必要です
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

次に、AnthropicのダッシュボードからAPIキーを取得し、環境変数に設定します。
毎回入力するのは手間なので、`.zshrc`や`.bashrc`に書き込んでおきましょう。

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

その後、プロジェクト用のディレクトリを作成し、Claude Codeを初期化します。

```bash
mkdir ai-app-project
cd ai-app-project
claude init
```

`claude init`を実行すると、`.claude`という設定ディレクトリが作られ、プロジェクトのコンテキストを管理できるようになります。

⚠️ **落とし穴:**
Claude Codeを初めて動かす際、ターミナルでのコマンド実行許可を求められます。
ここで「許可（Allow）」を選択しないと、AIがテストを実行したりパッケージをインストールしたりできず、ただのチャットツールに成り下がります。
「Always allow for this session」を選択して、AIに「手足」を与えるのが使いこなすコツです。

## Step 2: 基本の設定

次に、Pythonの仮想環境を作成し、FastAPIをベースにしたプロジェクトの骨組みをClaude Codeに作らせます。
以下の指示をターミナルに入力してください。

```bash
claude "FastAPIを使って、SQLiteをデータベースにしたシンプルなTODO管理APIを作成してください。Pydantic v2を使い、ディレクトリ構成はモダンな構成（app/以下にmain.pyやmodels.pyを分ける）にしてください。必要なライブラリをrequirements.txtにまとめ、venvを作成してインストールするスクリプトも用意してください。"
```

Claude Codeは、まずディレクトリ構成を考え、ファイルを一つずつ作成し、最後に`pip install`まで実行しようとします。
ここで重要なのは、**「なぜこの構成にするのか」をClaudeが説明しているか**を確認することです。
もし全てのファイルを1ファイルにまとめようとしたら、「保守性を高めるためにモジュール分割して」と追加で指示してください。

## Step 3: 動かしてみる

骨組みができたら、実際にAPIが動くかテストします。これもClaude Code内で完結させます。

```bash
claude "サーバーを起動して、curlコマンドでタスクの追加と取得ができるかテストしてください。エラーが出たら修正して。"
```

### 期待される出力

```text
> Running: uvicorn app.main:app --reload
> Running: curl -X POST http://localhost:8000/todos -d '{"title": "AI記事を書く"}'
{ "id": 1, "title": "AI記事を書く", "status": "pending" }
> Test passed!
```

Claude Codeはバックグラウンドでサーバーを立ち上げ、ポートが開くのを待ってからテストコマンドを叩きます。
この「待ち」の処理をAIが自動で行うのが、従来のAIチャットにはなかった強みです。

## Step 4: 実用レベルにする（Cursorとの連携）

ここからはCursorに切り替えます。
ターミナルで `cursor .` と入力してエディタを開いてください。
Claude Codeが作成したコードが反映されているはずです。

次に、このTODOアプリに「AIによるタスク要約機能」を追加します。
Cursorの「Composer（Cmd+I）」を開き、以下のように依頼します。

```text
app/services/summarizer.py を新規作成して、Anthropic APIを使ってタスクの内容を1行で要約するロジックを追加してください。
app/main.py のPOSTエンドポイントで、この要約機能を呼び出すように変更してください。
UIとして index.html を作成し、JavaScriptでAPIを叩いてタスク一覧を表示できるようにしてください。
```

Cursorを使う理由は、**「フロントエンドのコードとバックエンドの連携を、差分表示（Diff）で確認しながら進めたいから」**です。
Claude CodeはCLI上で一気にファイルを書き換えますが、UIが絡む部分は人間の目でプレビューを確認しながら進める方が事故が少ない。

ここで、APIキーの管理について補足します。
`app/services/summarizer.py`内でAPIキーを直書きしないよう、`.env`ファイルを使うようにCursorに命じてください。

```python
# app/services/summarizer.py の例
import os
from anthropic import Anthropic

# 環境変数から読み込む（セキュリティ上の理由で必須）
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def summarize_task(text: str):
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": f"要約して: {text}"}]
    )
    return response.content[0].text
```

最後に、再度Claude Codeに戻り、全体のテストを依頼します。
「UIはブラウザで開くので、バックエンドの単体テストコードをpytestで書いて実行して」と指示すれば、テストカバレッジの高い堅牢なコードが完成します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | npmのパスが通っていない | `npm list -g`で場所を確認し、PATHを通す |
| APIの402エラー | クレジット残高不足 | Anthropic Consoleで$5以上チャージする |
| ファイル上書き競合 | CursorとClaude Codeが同時に編集 | 保存を確実に行い、片方の処理が終わるまで待つ |

## 次のステップ

このワークフローをマスターしたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
Claude CodeはMCPサーバーと連携することで、Google検索の結果を取り込んだり、GitHubのIssueを直接読み取ったりすることが可能になります。

具体的には、プロジェクト内に`.claudecode.config.json`を作成し、自分がよく使う外部ツールと連携させる設定を書き込みます。
これにより、AIは「コードを書く」だけでなく、「外部ドキュメントを読みに行って最新の仕様を反映させる」というエンジニア顔負けの動きができるようになります。
私の環境では、自作のSQLite用MCPサーバーを接続し、ローカルにある過去のナレッジをClaude Codeに直接参照させています。
次は「AIに仕様書を渡して、全自動でプルリクを作成させる」までを自動化してみてください。

## よくある質問

### Q1: Claude CodeとCursor、結局どっちがメインですか？

開発の8割はClaude Codeで進めるのが私のスタイルです。特に「新しい機能の追加」「バグ修正」はCLIの方が速い。Cursorは「コードの全体像を眺める」「UIのデザインを確認する」「AIが提案した差分を1箇所ずつレビューする」ためのブラウザのような存在として使っています。

### Q2: API代が高くなりそうで怖いのですが、節約術はありますか？

Claude Codeには「Compact」機能があります。長いやり取りが続くとトークンを消費するので、定期的に `compact` と打って文脈を要約させてください。また、不要な大きなファイルを `.claudeignore` に追加して、AIが読み込む情報を制限するのも有効です。

### Q3: 日本語での指示は通じますか？

全く問題ありません。むしろ日本語の方が細かいニュアンスが伝わることもあります。ただし、エラーログなどは英語のまま渡した方が、AIが解決策を検索しやすいため、状況に応じて使い分けるのがベストです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini M4</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIの高速ビルドや複数ツール立ち上げに32GBメモリは必須環境</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M4%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAI開発環境の作り方](/posts/2026-07-27-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeとCursor、結局どっちがメインですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "開発の8割はClaude Codeで進めるのが私のスタイルです。特に「新しい機能の追加」「バグ修正」はCLIの方が速い。Cursorは「コードの全体像を眺める」「UIのデザインを確認する」「AIが提案した差分を1箇所ずつレビューする」ためのブラウザのような存在として使っています。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が高くなりそうで怖いのですが、節約術はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeには「Compact」機能があります。長いやり取りが続くとトークンを消費するので、定期的に compact と打って文脈を要約させてください。また、不要な大きなファイルを .claudeignore に追加して、AIが読み込む情報を制限するのも有効です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示は通じますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。むしろ日本語の方が細かいニュアンスが伝わることもあります。ただし、エラーログなどは英語のまま渡した方が、AIが解決策を検索しやすいため、状況に応じて使い分けるのがベストです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac mini M4</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIの高速ビルドや複数ツール立ち上げに32GBメモリは必須環境</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20mini%20M4%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

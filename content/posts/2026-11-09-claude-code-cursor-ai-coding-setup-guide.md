---
title: "Claude CodeとCursorを併用して開発効率を3倍に引き上げるAIコーディング環境構築ガイド"
date: 2026-11-09T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-setup-guide"
cover:
  image: "/images/posts/2026-11-09-claude-code-cursor-ai-coding-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング"
  - "Anthropic API"
  - "エージェント開発"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- GitHubのトレンドリポジトリを自動収集し、Claude 3.5 Sonnetで要約したレポートをSlackに毎日通知する自動化エージェントを構築します。
- 前提知識: 基本的なターミナル操作ができること、PythonまたはJavaScriptの読み書きができること。
- 必要なもの: Anthropic APIキー（クレジット課金が必要）、Cursor Proアカウント、Node.js（v18以上）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorを同時起動し、ブラウザとDockerを併用する開発環境にはメモリ32GB以上が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIコーディングを本気で実務に投入するなら、ツール選びで妥協すると逆に高くつきます。
まず、Claude Codeを利用するにはAnthropicのAPIコンソールで「Tier 2（合計50ドル以上の入金）」以上であることが望ましいです。
Tier 1だとレートリミット（1分あたりのリクエスト制限）が厳しく、Claude Codeのような自律型エージェントはすぐに制限に引っかかり、作業が中断してストレスが溜まります。

Cursorは無料枠でも使えますが、本気で書くなら月額20ドルのProプラン一択です。
「Cursor Prediction（コード予測）」の快適さは、無料枠のモデルでは体験できません。
ハードウェアについては、MacBook Air（M2/M3）のメモリ16GB以上を推奨します。
私はRTX 4090を2枚挿した自作機でローカルLLM（Qwen2.5-Coderなど）も併用していますが、こと「エージェントによるファイル操作」に関しては、現状Claude Code + Claude 3.5 Sonnetの組み合わせが最強です。

## なぜこの方法を選ぶのか

巷では「CursorがあればClaude Codeはいらない」あるいはその逆の意見も見かけますが、私は「併用」が正解だと確信しています。
CursorはエディタとしてのUIが完成されており、コードの微調整やリアルタイムの補完、インラインでのチャットには無類の強さを誇ります。
しかし、プロジェクト全体の構成を考えたり、複数のファイルを一括生成・修正したり、テストを回してエラーを自動修正する「エージェント的挙動」は、Claude Codeの方が圧倒的に洗練されています。

Claude Codeはターミナル内で動作し、OSのコマンドを直接実行できるため、ライブラリのインストールからデバッグまでを自律的に完結させられます。
「設計と大きな骨組みはClaude Codeで一気に作り、細部のロジックやUIの微調整はCursorで行う」という使い分けが、現時点での開発スピードを最大化させる最適解です。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはnpmパッケージとして提供されています。

```bash
# Node.jsがインストールされていることを確認
node -v

# Claude Codeをグローバルにインストール
npm install -g @anthropic-ai/claude-code

# 初期設定とログイン
claude auth login
```

`npm install -g` でインストールすることで、どのプロジェクトディレクトリからでも `claude` コマンドを呼び出せるようになります。
`claude auth login` を実行するとブラウザが開くので、Anthropicアカウントで認証を済ませてください。
このとき、APIキーを直接環境変数に書き込む必要がないため、セキュリティ的にも扱いやすいのが特徴です。

⚠️ **落とし穴:** Node.jsのバージョンが古いとインストール時にエラーが出ることがあります。v18未満を使っている場合は、nvmなどを使って最新のLTS（Long Term Support）版にアップデートしてから実行してください。

## Step 2: 基本の設定

プロジェクト用のディレクトリを作成し、Claude Codeに「開発のルール」を教え込みます。
AIに勝手なコードを書かせないために、`.clauderules` ファイルを作成するのがコツです。

```bash
mkdir ai-trend-agent
cd ai-trend-agent
touch .clauderules
```

`.clauderules` には以下のように記述してください。

```text
- Python 3.11以上を使用すること
- 外部APIとの通信には `httpx` ライブラリを使用すること
- 型ヒントを必ず付けること
- 日本語でコメントを書くこと
- 実行エラーが出た場合は、まずログを確認し、原因を特定してから修正案を提示すること
```

なぜこのファイルを作るかというと、Claude Codeは実行時にカレントディレクトリのファイルを読み取る性質があるからです。
あらかじめルールを明文化しておくことで、「そんな書き方をしてほしくなかった」という手戻りを30%以上削減できます。

次に、Cursorでこのディレクトリを開きます。
Cursorの設定画面（Cmd + Shift + J）で、モデルが `claude-3-5-sonnet` になっていることを確認してください。

## Step 3: 動かしてみる

いよいよClaude Codeを使って、エージェントの骨組みを生成させます。
ターミナルで `claude` と打ち込み、対話モードに入ります。

```bash
claude
```

Claude Codeのプロンプトに、以下の指示を投げてください。

```text
GitHubのトレンド（Python）をスクレイピングして、上位3つのリポジトリ名、URL、概要を取得するスクリプト `github_spy.py` を作成してください。
その後、その内容をClaude APIを使って日本語で要約する関数を追加してください。
最後に、要約した内容をSlackのWebhook URLに送信する機能を実装してください。
必要なライブラリのインストールも自動で行ってください。
```

### 期待される出力

Claude Codeは指示を受けると、以下のようなステップを自動で実行します。

1.  `pip install httpx beautifulsoup4` などのコマンドを提案し、実行する。
2.  `github_spy.py` を作成し、コードを書き込む。
3.  `.env` ファイルを作成し、APIキーの変数を定義するよう促す。

ここで重要なのは、Claude Codeが「自分でコマンドを叩いて環境を整える」点です。
従来のチャットAIのように「このコマンドを打ってください」と指示されるのを待つ必要はありません。

## Step 4: 実用レベルにする

Claude Codeが生成したコードを、Cursorで開いてブラッシュアップします。
AIが生成したコードには、しばしば「エラーハンドリングの不足」や「型定義の曖昧さ」が残ります。

Cursorの「Composer」（Cmd + I）を開き、生成された `github_spy.py` を参照しながらこう指示します。

```text
# Cursor Composerへの指示例
このコードにリトライ処理を追加して。
GitHubのAPI制限に引っかかった場合に1分待機してから再試行するように。
また、Slackへの投稿が成功したかどうかをログに残すようにして。
```

Cursorはエディタ上のコードをリアルタイムで書き換えてくれます。
この「Claude Codeで一気に土台を作り、Cursorで細部を詰め、補完機能でコードを完成させる」という流れが、実務で最もミスの少ない手法です。

最後に、完成したスクリプトをClaude Codeから実行してテストします。

```bash
# Claude Codeのターミナルに戻って
python github_spy.py
```

エラーが出た場合、そのエラー文をコピーしてClaude Codeに投げれば、「あ、ライブラリのインポートが漏れていましたね」といった具合に、即座に修正コードを適用してくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | Anthropic APIのTierが低い | クレジットを50ドル以上チャージしてTier 2に上げる |
| Command not found: claude | パスが通っていない | `npm list -g` で場所を確認し、PATHを通す |
| Permission denied | ファイル書き込み権限がない | `sudo` は使わず、ディレクトリの所有権を確認する |

## 次のステップ

この環境が構築できたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
Claude CodeはMCPサーバーと連携することで、Googleカレンダーの予定を読み取ったり、ローカルのデータベースに直接クエリを投げたりといった、さらに高度な自律動作が可能になります。

また、作成したスクリプトをGitHub Actionsで定期実行するように設定すれば、自分専用のAIニュースレター配信システムの完成です。
AIにコードを書かせる時代から、AIと一緒にプロジェクトを「運用」する段階へシフトしましょう。
私のブログでは、RTX 4090を活用したローカルLLMとのハイブリッド構成についても発信しているので、興味があればチェックしてみてください。

## よくある質問

### Q1: Cursorだけで十分ではないでしょうか？

CursorのComposerも優秀ですが、ターミナルの実行結果をAIが直接読み取り、それに基づいてファイルを自動修正するループの速さはClaude Codeが勝ります。特に「環境構築」や「大規模なリファクタリング」では、Claude Codeの方が迷いが少ない印象です。

### Q2: API代が怖いです。節約する方法はありますか？

Claude Codeには `--cost` オプションはありませんが、作業が終わるごとに `exit` で抜ける癖をつけてください。また、大きなファイルを読み込ませすぎないよう、`.gitignore` で不要なデータディレクトリを除外しておくのが有効な対策です。

### Q3: Windowsでも動きますか？

WSL2（Windows Subsystem for Linux）上での動作を強く推奨します。PowerShellでも動きますが、Claude Codeが提案するシェルコマンドの多くがUNIX系を想定しているため、WSL2の方がトラブルが圧倒的に少なくなります。

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境構築ガイド](/posts/2026-10-30-claude-code-cursor-setup-guide-2025/)
- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-10-19-claude-code-cursor-ai-coding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorだけで十分ではないでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも優秀ですが、ターミナルの実行結果をAIが直接読み取り、それに基づいてファイルを自動修正するループの速さはClaude Codeが勝ります。特に「環境構築」や「大規模なリファクタリング」では、Claude Codeの方が迷いが少ない印象です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeには --cost オプションはありませんが、作業が終わるごとに exit で抜ける癖をつけてください。また、大きなファイルを読み込ませすぎないよう、.gitignore で不要なデータディレクトリを除外しておくのが有効な対策です。"
      }
    },
    {
      "@type": "Question",
      "name": "Windowsでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "WSL2（Windows Subsystem for Linux）上での動作を強く推奨します。PowerShellでも動きますが、Claude Codeが提案するシェルコマンドの多くがUNIX系を想定しているため、WSL2の方がトラブルが圧倒的に少なくなります。 ---"
      }
    }
  ]
}
</script>

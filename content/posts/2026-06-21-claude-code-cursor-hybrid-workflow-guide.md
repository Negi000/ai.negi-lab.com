---
title: "Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法"
date: 2026-06-21T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "Python API 自動化"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

GitHubの特定リポジトリのスター数を監視し、前日からの増減をSlackに通知するPythonスクリプトを作成します。
この記事を読み終える頃には、Claude Code（CLI）に「自律的な実装とテスト」を任せ、Cursor（エディタ）で「コードの品質管理と細かな調整」を行うハイブリッド開発環境が手に入ります。

- GitHubとSlackのAPIを連携させた実用的なツール
- Pythonの基礎（pipインストールや環境変数の概念）があれば完結
- 必要なもの：Claude APIキー（Tier 2以上推奨）、Cursor、GitHubアカウント、Slackワークスペース

## 先に確認するスペック・料金

この環境を構築する前に、APIの「Tier（ティア）」を確認してください。
Claude Codeを実務で使うなら、Anthropic APIのクレジットを累計40ドル以上購入した「Tier 2」以上が理想的です。
Tier 1でも動きますが、レートリミット（1分あたりのリクエスト制限）が厳しく、大きなプロジェクトでは頻繁に止まります。

Cursorは月額20ドルのProプランを推奨します。
無料枠でも動かせますが、Claude 3.5 Sonnetを無制限に近い感覚で叩けないと、AIコーディングの恩恵を最大化できません。
ハードウェアに関しては、MacBook Air（M2/M3、メモリ16GB以上）あれば十分快適です。
私のRTX 4090 2枚挿し自作サーバーはローカルLLM用ですが、API利用が主体の今回は、安定したインターネット回線の方が重要になります。

## なぜこの方法を選ぶのか

Cursorの「Composer」機能だけでも開発は可能ですが、あえてCLIツールのClaude Codeを併用します。
理由は「ターミナルでの自律性」の差です。
Cursorはあくまでエディタ上での提案が主ですが、Claude Codeは「テストを実行し、エラーが出たら勝手に修正し、またテストする」というループを自律して回せます。

一方で、Claude Codeは自律性が高すぎて、勝手にファイルを書き換えすぎるリスクがあります。
そこで、CursorのGUIで変更差分（Diff）を確認しながら、複雑なロジックはClaude Codeに丸投げするという「分業」が、現時点で最もミスが少なく速いアプローチです。
実際に私が機械学習のパイプラインを組む際も、この組み合わせで開発時間が半分以下になりました。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorでプロジェクトを開く準備をします。

```bash
# Claude Codeのインストール（Node.js 18以上が必要）
npm install -g @anthropic-ai/claude-code

# 作業ディレクトリの作成
mkdir github-star-notifier
cd github-star-notifier

# Cursorで現在のディレクトリを開く
cursor .
```

`@anthropic-ai/claude-code`をグローバルインストールすることで、ターミナルから`claude`コマンドが使えるようになります。
このコマンドは、Anthropicが公式に提供している「エージェント型」のCLIツールです。

⚠️ **落とし穴:**
Node.jsのバージョンが古いとインストールでエラーが出ます。`node -v`で18以上であることを確認してください。
また、はじめて`claude`コマンドを叩くときは、ブラウザが立ち上がりAnthropicアカウントとの連携を求められます。APIキーを直接入力するのではなく、ブラウザ認証を通す形になるので注意してください。

## Step 2: 基本の設定

API連携には機密情報（トークン）が必要です。
`.env`ファイルに情報をまとめ、Claude Codeに読み込ませる準備をします。

```python
# .env（これは手動で作成するか、Claude Codeに作らせます）
GITHUB_TOKEN=ghp_your_token_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
REPO_NAME=anthropics/claude-code
```

ここでは直接コードを書かずに、Cursorのターミナルで以下のコマンドを打ち、Claude Codeを起動します。

```bash
claude
```

起動したら、Claudeに対して次のように指示を出してください。
「GitHubのスター数を取得してSlackに送るツールを作りたい。まずは必要なライブラリをリストアップして、requirements.txtを作って。その後、.envのテンプレートを作成して」

この指示により、Claude Codeはプロジェクト構成を把握し、必要なファイルを作成します。
なぜこの手順を踏むかというと、Claude Codeに「プロジェクトの初期状態」を定義させることで、その後のコード生成の精度が劇的に上がるからです。

## Step 3: 動かしてみる

環境が整ったら、一気にメインロジックを生成させます。
Claude Codeのプロンプトに以下を入力してください。

```text
/edit main.py を作成して、以下の仕様を実装してください。
1. .envから環境変数を読み込む
2. GitHub APIを使ってリポジトリのスター数を取得する
3. 取得したスター数を slack_notifier.py（新規作成）経由でSlackに投稿する
4. 実行後、実際にテスト走行を行い、エラーがあれば修正してください
```

### 期待される出力

Claude Codeが自律的に動き出し、以下のようなログが流れます。

```
Creating main.py...
Creating slack_notifier.py...
Installing dependencies: requests, python-dotenv...
Running: python3 main.py
Error: Missing SLACK_WEBHOOK_URL
Attempting fix...
```

Claude Codeは、コードを書いて終わりではありません。
「実行してエラーが出たら、そのエラーログを読み取り、自分でコードを修正して再実行する」というプロセスを自動で行います。
これがCursorのComposerとの決定的な違いです。

## Step 4: 実用レベルにする

単にスター数を送るだけでは実務では使えません。
「前回のスター数をローカルのJSONファイルに保存しておき、増分があった時だけ通知する」というロジックを追加します。

```python
# Claude Codeに追加で指示する内容
"""
main.pyを改良して、前回のスター数を 'stats.json' に保存するようにしてください。
前回の値と比較して、増加していた場合のみ『昨日のスター数から +5 増えました！』のようにSlackへ通知するようにしてください。
"""
```

このように「状態を持つ（Statefulな）」処理を指示する際、Claude Codeは既存のファイル構成を汚さずに、最適なリファクタリングを提案してくれます。
コードが書き換わったら、Cursorのエディタ画面に戻り、左側のGit管理画面で「何が変わったのか」を必ず確認してください。
AIは時として、エラーハンドリングを簡略化しすぎることがあります。
「ここはtry-exceptで囲ってほしい」という微調整は、Cursor上のエディタで直接書き込むのが一番効率的です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Rate limit reached` | APIの使用制限に達した | クレジットを追加してTierを上げるか、少し待つ |
| `Permission denied (GitHub API)` | トークンの権限不足 | GitHubでPersonal Access Tokenの`repo`権限を確認 |
| `ModuleNotFoundError` | 仮想環境にインストールされていない | Claude Codeに `pip installして` と指示する |

## 次のステップ

ここまでで「AIに自律的に作らせ、人間がエディタで監査する」という最強のワークフローが体験できたはずです。
次のステップとしては、以下のカスタマイズに挑戦してみてください。

1. **MCP（Model Context Protocol）の導入**: Claude CodeにGoogle検索やメモ帳などの外部ツールを連結させます。
2. **GitHub Actionsでの自動化**: 今回作ったスクリプトを、毎朝9時に自動実行されるように設定します。
3. **複数リポジトリへの対応**: 競合製品のリポジトリも監視対象に入れ、比較レポートを作らせます。

私はこれまで20件以上の機械学習案件をこなしてきましたが、最近は「コードを1行ずつ書くこと」をやめました。
「AIに仕様を伝え、動くものを出させ、それをレビューして直す」というスタイルにシフトしたことで、開発スピードは物理的に数倍になりました。
まずはこの小さなスクリプトを、自分専用のツールとして育ててみてください。

## よくある質問

### Q1: Claude CodeはAPI料金が高いと聞きますが、実際どうですか？

実務で数時間使い倒すと、1日で数ドル（500〜1000円程度）消費することもあります。しかし、エンジニアの時給を考えれば、3時間の作業が15分で終わる対価としては破格です。トークン節約のために、不要なファイルは`.claudeignore`で読み込ませないようにしましょう。

### Q2: CursorのComposer機能があるのに、Claude Codeを使う意味は？

Cursorは「今開いているファイル」の編集に強いですが、Claude Codeは「ターミナルでコマンドを実行し、その結果を見てコードを直す」というデバッグループが得意です。テストコードを走らせながら開発するスタイルなら、Claude Codeの方が圧倒的に楽です。

### Q3: 会社の機密コードに使っても大丈夫ですか？

AnthropicのAPI経由のデータは、モデルの学習には使用されないと明記されています。ただし、会社の規定で外部AIへのコード送信が禁止されている場合は、まずは個人開発のプロジェクトで試して、その生産性を上司にデモで見せるのが賢い戦略です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ターミナルとCursorを横に並べてAIの挙動を監視するのに、広大な4K画面は必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [CursorとClaude Codeを併用して爆速でPythonツールを開発する方法](/posts/2026-06-14-claude-code-cursor-hybrid-workflow-guide/)
- [Spotlight by Backplanes：Claude Codeの「思考の軌跡」を可視化して開発効率を最大化する](/posts/2026-06-10-spotlight-backplanes-claude-code-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeはAPI料金が高いと聞きますが、実際どうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実務で数時間使い倒すと、1日で数ドル（500〜1000円程度）消費することもあります。しかし、エンジニアの時給を考えれば、3時間の作業が15分で終わる対価としては破格です。トークン節約のために、不要なファイルは.claudeignoreで読み込ませないようにしましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのComposer機能があるのに、Claude Codeを使う意味は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Cursorは「今開いているファイル」の編集に強いですが、Claude Codeは「ターミナルでコマンドを実行し、その結果を見てコードを直す」というデバッグループが得意です。テストコードを走らせながら開発するスタイルなら、Claude Codeの方が圧倒的に楽です。"
      }
    },
    {
      "@type": "Question",
      "name": "会社の機密コードに使っても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI経由のデータは、モデルの学習には使用されないと明記されています。ただし、会社の規定で外部AIへのコード送信が禁止されている場合は、まずは個人開発のプロジェクトで試して、その生産性を上司にデモで見せるのが賢い戦略です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Dell U2723QE</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ターミナルとCursorを横に並べてAIの挙動を監視するのに、広大な4K画面は必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

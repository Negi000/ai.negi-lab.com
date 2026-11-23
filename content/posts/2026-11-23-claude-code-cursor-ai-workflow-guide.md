---
title: "Claude CodeとCursor併用で爆速AI開発環境を作る方法"
date: 2026-11-23T00:00:00+09:00
slug: "claude-code-cursor-ai-workflow-guide"
cover:
  image: "/images/posts/2026-11-23-claude-code-cursor-ai-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI 自動開発"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude CodeとCursorを組み合わせ、FastAPIを使用した「AIが自動でデバッグ・テストまで完結させるTODO管理API」を作成します。
Pythonの基本的な文法がわかり、ターミナルでコマンドを叩くことに抵抗がない方を対象としています。
単にコードを書くだけでなく、Claude Codeにブラウザ操作やテスト実行まで任せる「自律型開発」のワークフローを構築するのがゴールです。

- **使用技術:** Python, FastAPI, SQLite, Claude Code, Cursor
- **前提条件:** Node.js v18以上がインストールされていること、Anthropic APIキーを持っていること

## 先に確認するスペック・料金

AI開発をストレスなく行うには、道具選びがすべてです。
CursorのProプラン（月額$20）は必須と言っても過言ではありませんが、今回導入するClaude CodeはAnthropicのAPI（Claude 3.5 Sonnet等）を直接消費します。
開発規模によりますが、1時間の集中した開発で$1〜$5程度のAPI費用がかかる点は覚悟してください。

ハードウェア面では、MacBook Air（M2/M3）のメモリ16GB以上があれば十分快適に動きます。
私は自宅のRTX 4090搭載PCでローカルLLMも回しますが、Claude Codeのようなエージェントツールは、結局のところ推論速度とコンテキスト窓の広さが命です。
API経由で最新モデルを叩く方が、現時点ではローカルで完結させるよりも圧倒的に開発体験が良いと感じています。

## なぜこの方法を選ぶのか

Cursorだけでも十分強力ですが、CursorのComposerモード（Ctrl+I）は「エディタ内の書き換え」に特化しています。
一方でClaude Codeは、ターミナル上で動作するエージェントであり、ファイル操作だけでなく「テストコマンドの実行」「エラーログの読み取り」「ブラウザでの表示確認」を自律的に繰り返します。
つまり、Cursorを「設計とコードの微調整」に使い、Claude Codeを「泥臭い実装とデバッグの自動化」に割り当てるのが、2024年現在の最適解です。

実際に私が試したところ、Cursorだけで修正を繰り返すと「直したはずの別の場所が壊れる」というデグレードが頻発しました。
しかし、Claude Codeに「テストが通るまでループして修正しろ」と命令を投げておけば、私がお茶を飲んでいる間にバグが消えています。
この「手離れの良さ」こそが、両者を併用する最大のメリットです。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorでプロジェクトを開く準備をします。

```bash
# Claude Codeをグローバルにインストール
npm install -g @anthropic-ai/claude-code

# プロジェクト用ディレクトリの作成
mkdir ai-fastapi-app
cd ai-fastapi-app

# Cursorで現在のディレクトリを開く
cursor .
```

Claude CodeはNode.jsで動くCLIツールです。
最新のAnthropic製モデルをターミナルから直接操作できるため、`cd`や`ls`といったコマンドをAIが自分で発行して状況を把握してくれます。
インストールが終わったら、一度`claude`コマンドを叩いて初期設定を済ませましょう。

⚠️ **落とし穴:** Node.jsのバージョンが古いとインストール時にエラーが出ます。`node -v`で18.x以上であることを確認してください。また、Windows環境の場合はPowerShellよりもWSL2やGit Bashを使う方が、パスの解釈ミスが少なく安定します。

## Step 2: 基本の設定

Claude Codeを動かすには、AnthropicのAPIキーを環境変数に設定する必要があります。
`.env`ファイルに書く方法もありますが、CLIツールとして使う場合はシェル設定ファイル（`.zshrc`や`.bashrc`）に記述するのがスムーズです。

```bash
# APIキーの設定（一時的な設定）
export ANTHROPIC_API_KEY='sk-ant-api03-xxxx'

# Claude Codeの起動
claude
```

起動すると、まず認証を求められます。
ブラウザが開くので、Anthropicのアカウントでログインして許可してください。
設定が完了すると、ターミナルがClaudeとの対話モードに切り替わります。

ここで重要なのが「コスト制限」の設定です。
Claude Codeは放っておくと際限なくAPIを叩き続けるリスクがあるため、初回起動時の設定や`/config`コマンドで「1リクエストあたりの最大トークン数」などを意識しておくと安心です。
私は「自動実行の許可」をファイル読み取りのみにし、書き込みやコマンド実行は毎回確認を求める設定にしています。

## Step 3: 動かしてみる

それでは、実際にTODOアプリの土台をClaude Codeに作らせてみましょう。
ターミナルのClaude Codeに対して、以下のプロンプトを投げます。

```text
FastAPIとSQLiteを使って、TODO管理ができるAPIの最小構成を作成してください。
以下の要件を満たすこと。
1. Pydanticモデルによるバリデーション
2. sqliteを使用したデータの永続化
3. 全件取得、作成、削除の3つのエンドポイント
4. 仮想環境(venv)の作成と依存ライブラリのインストール
```

### 期待される出力

```text
[Claude Code]
1. venvを作成し、fastapi, uvicorn, sqlalchemyをインストールします。
2. main.py, database.py, models.py を作成します。
3. サーバーを起動して動作確認を行います。
... (中略) ...
Done! サーバーを起動するには 'source venv/bin/activate && uvicorn main:app --reload' を実行してください。
```

Claude Codeは、単にコードを提案するだけでなく、実際に`python -m venv venv`を実行し、`pip install`を行い、ファイルを作成します。
これがCursorのComposerとの決定的な違いです。
Cursorでは「ターミナルに貼り付けて実行する」という手間が発生しますが、Claude Codeはそのプロセス自体を代行します。

## Step 4: 実用レベルにする

土台ができたら、ここからはCursorとClaude Codeの「いいとこ取り」をします。
まずはCursor（IDE）で作成された`main.py`を開き、コードの全体像を眺めてみてください。
「エンドポイントをもう一つ増やしたい」「バリデーションを厳しくしたい」といった設計に関わる部分は、Cursorの右サイドバー（Chat）で対話しながら進めるのが直感的です。

しかし、ここから「ユニットテストを20ケース書き、すべてパスするまでデバッグする」という作業が発生したとき、Claude Codeの本領が発揮されます。
ターミナルのClaude Codeに以下のように指示してください。

```text
/test pytestを使って、現在のAPIのすべてのエンドポイントをテストするスクリプトを作成してください。
テストを実行し、エラーが出た場合は原因を特定してコードを修正してください。
すべてのテストがパスするまで繰り返してください。
```

Claude Codeは自動的に`test_main.py`を作成し、`pytest`コマンドを実行します。
もしデータベースの接続エラーや型不一致でテストが落ちれば、そのエラーメッセージを自分で読み取り、`main.py`を修正し、再度テストを回します。
この「自律デバッグループ」は、人間のエンジニアがやる作業と全く同じです。

さらに実務レベルに引き上げるために、以下のコマンドも活用しましょう。
`/compact`：会話履歴が長くなりすぎてAPI料金が高騰するのを防ぐため、コンテキストを要約して整理してくれます。
`/review`：書いたコードにセキュリティリスクやパフォーマンスの懸念がないか、AIの視点でレビューを依頼できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | npmのパスが通っていない | `npm bin -g`でパスを確認し、PATHに追加する |
| APIのタイムアウト | コンテキストが大きすぎる | `/compact`で履歴をリセットするか、不要なファイルを`.gitignore`に追加 |
| テストが無限ループする | AIが修正と破壊を繰り返している | 一旦停止し、Cursorで手動で構造を整理してから再度指示 |

## 次のステップ

ここまでで、AIにコードを書かせ、実行させ、テストをパスさせるという「エージェント型開発」の基礎ができました。
次に挑戦すべきは「MCP（Model Context Protocol）」の活用です。
Claude CodeはMCPサーバーと連携することで、Googleドキュメントを読み取ったり、GitHubのIssueを直接操作したりすることが可能になります。

例えば、「GitHubのIssueを読み取って、その内容に基づいた新機能を実装し、プルリクエストまで作成する」といったワークフローを構築してみてください。
もはや「コーディング」という作業は、キーボードを叩くことから、AIへの「タスク委譲」へと完全にシフトしています。
このスピード感に慣れてしまうと、手動で一行ずつコードを書いていた頃にはもう戻れません。

## よくある質問

### Q1: CursorのComposer機能があるのに、なぜわざわざClaude Codeを使うのですか？

Cursorは「UIを通じたコード編集」には優れていますが、シェルコマンドの実行やテストの反復、外部ツールとの連携（MCP）に関してはClaude Codeの方が圧倒的に自由度が高く、自律的だからです。

### Q2: API料金が怖いです。節約する方法はありますか？

`.gitignore`を適切に設定し、AIに読み込ませるファイル数を絞ってください。また、`/compact`をこまめに実行してコンテキストトークンを節約し、一度に大量の指示をせず、小さなステップでタスクを分割するのがコツです。

### Q3: Python以外の言語でも同じように使えますか？

もちろんです。TypeScript, Rust, Goなど、ターミナルでビルドやテストができる言語であれば、Claude Codeの恩恵をフルに受けられます。特にコンパイルエラーが厳しい言語ほど、AIによる自動修正が威力を発揮します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Air M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GB以上のメモリがあればAIツールを並列で動かしても快適です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-10-26-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用した最強のAIコーディング環境構築と実践ガイド](/posts/2026-08-22-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能があるのに、なぜわざわざClaude Codeを使うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Cursorは「UIを通じたコード編集」には優れていますが、シェルコマンドの実行やテストの反復、外部ツールとの連携（MCP）に関してはClaude Codeの方が圧倒的に自由度が高く、自律的だからです。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ".gitignoreを適切に設定し、AIに読み込ませるファイル数を絞ってください。また、/compactをこまめに実行してコンテキストトークンを節約し、一度に大量の指示をせず、小さなステップでタスクを分割するのがコツです。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じように使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScript, Rust, Goなど、ターミナルでビルドやテストができる言語であれば、Claude Codeの恩恵をフルに受けられます。特にコンパイルエラーが厳しい言語ほど、AIによる自動修正が威力を発揮します。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Air M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">16GB以上のメモリがあればAIツールを並列で動かしても快適です</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

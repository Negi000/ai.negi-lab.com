---
title: "Claude CodeとCursorを併用！爆速AIコーディング環境構築ガイド"
date: 2026-07-11T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-07-11-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIコーディング"
  - "FastAPI React 入門"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

ターミナルから直接コードを書き換え、テストまで自律実行する「Claude Code」と、視覚的なコード編集に強い「Cursor」を同期させ、API連携型のフルスタックWebアプリ（FastAPI + React）をゼロから構築します。

- 構築するもの：SQLiteを使用したタスク管理API（FastAPI）と、それを操作するフロントエンド（Vite + React）
- 前提知識：ターミナルの基本操作、PythonまたはJavaScriptの基礎的な読み書きができること
- 必要なもの：Anthropic APIキー（クレジットがチャージされていること）、Cursor（Proプラン推奨）

## 先に確認するスペック・料金

この環境を快適に動かすには、マシンスペックよりも「APIへの投資」が重要になります。

1.  **Anthropic APIクレジット:** Claude CodeはAPI経由で動作するため、月額プランではなく「従量課金」のクレジットが必要です。まずは $20 程度チャージしておくことをおすすめします。1回のプロジェクト構築で、経験上 $2〜$5 程度は消費します。
2.  **Cursor Proプラン:** 月額 $20 です。無料枠でも動かせますが、Claude 3.5 Sonnetを制限なく使うためにはProが必須です。
3.  **推奨ハードウェア:** M1以降のMacBook（メモリ16GB以上）またはWSL2が動くWindows環境。Claude Code自体は軽量ですが、ローカルでDockerや複数のサーバーを立ち上げるため、メモリ8GBだと厳しい場面が多いです。
4.  **Node.js & Python:** Node.js v18以上、Python 3.10以上がインストールされていることを確認してください。

## なぜこの方法を選ぶのか

「CursorがあるならClaude Codeはいらないのでは？」と考えるかもしれませんが、実際に20以上の案件をAIでこなした私の結論は「併用が最強」です。

CursorはエディタとしてのUIが完成されており、コードの全体像を把握したり、細かいスタイル調整をしたりするのに向いています。
一方でClaude Codeは「ターミナルとOSに直結している」のが最大の強みです。
「テストを実行して、エラーが出たら勝手に直して、直ったらgit commitして」という一連のワークフローを丸投げできるのはClaude Codeにしかできません。

UI操作（Cursor）とコマンドライン操作（Claude Code）を使い分けることで、人間が「指示出し」に専念できる環境を作ります。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはAnthropicが公式に提供しているCLIツールです。

```bash
# Claude Codeのインストール
npm i -g @anthropic-ai/claude-code

# 認証（ブラウザが開くのでAnthropicアカウントでログイン）
claude auth
```

次に、プロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-build-project
cd ai-build-project
cursor .
```

Cursorを開いたら、ターミナル（Ctrl + `）を表示させ、そこでClaude Codeを起動します。

```bash
claude
```

⚠️ **落とし穴:** 初回起動時に「ファイルの読み取り権限」を求められます。ここで全てを許可しないと、Claude Codeがプロジェクト構造を理解できず、的外れな修正を連発します。また、`.gitignore`が適切に設定されていないと、`node_modules`などの巨大なディレクトリを読み込もうとして、トークンを一瞬で溶かす（＝数千円が消える）ので注意してください。

## Step 2: 基本の設定

Claude Codeをプロジェクトに最適化させます。最初に「このプロジェクトのルール」を教え込むのが、AIを暴走させないコツです。

Claude Codeのプロンプト（ターミナル）に以下を入力してください。

```text
/config set --global theme dark
/config set --global verbose true
```

次に、プロジェクトのルートに `.clauderules` というファイルを作成するよう指示します。これが「AIの指示書」になります。

```text
以下のルールを .clauderules に保存して。
1. バックエンドは FastAPI を使用し、ポート 8000 で動作させる。
2. フロントエンドは Vite + React + Tailwind CSS を使用し、ポート 5173 で動作させる。
3. 常に型定義（TypeScript / Pydantic）を優先すること。
4. ファイルを変更する前に、必ず現在のディレクトリ構造を確認すること。
```

このように「技術スタック」と「ポート番号」を明示するのは、Claude Codeが勝手に異なるフレームワークを使ったり、ポート競合を起こしたりするのを防ぐためです。

## Step 3: 動かしてみる

いよいよ、フルスタックアプリの土台を1回の指示で作らせます。

```text
FastAPIのバックエンド（sqlite使用）と、Vite+React+Tailwindのフロントエンドを構築して。
Todoアプリで、追加・削除・完了フラグの更新ができるようにして。
作成したら、それぞれの依存関係をインストールして、実際にサーバーを起動して動作確認まで行って。
```

### 期待される出力

Claude Codeが以下のような動作を自動で開始します。
1. `backend/` ディレクトリを作成し、`main.py` を記述。
2. `frontend/` ディレクトリを作成し、Viteプロジェクトを初期化。
3. `pip install` と `npm install` を実行。
4. サーバーをバックグラウンドで起動し、curl等で疎通確認を行う。

私の環境で試した際、Claude Codeは「フロントエンドからバックエンドへのCORS設定が漏れている」ことに自分で気づき、即座に `main.py` を修正して解決しました。この「自律的なデバッグ」こそが、Cursor Composeとの決定的な違いです。

## Step 4: 実用レベルにする

単に動くだけでなく、実際の開発現場で使える「品質」まで高めます。ここでCursorの出番です。

Claude Codeが作ったコードをCursorのエディタで眺めると、デザインが素っ気ないことに気づくはずです。そこで、Cursorの「Composer（Ctrl + I）」を開き、UIのブラッシュアップを依頼します。

1. Cursorで `App.tsx` を開く。
2. Composerに「今のTodoリストを、もっとモダンなダッシュボード風のデザインにして。Lucide-reactのアイコンを使って、アニメーション（framer-motion）も追加して」と入力。

なぜここでCursorを使うのか。それは、UIの微調整は「プレビューを見ながら何度もやり直す」作業であり、ターミナル完結のClaude Codeよりも、エディタ一体型のCursorの方が、人間が変更箇所を確認しやすいからです。

さらに、Claude Codeに戻って「テストコード」を書かせます。

```text
/compact
バックエンドの各エンドポイントに対して、pytestを使ったユニットテストを作成して実行して。
全てのテストが通るまで、コードを修正して。
```

`/compact` コマンドは、会話の履歴を要約してトークンを節約するコマンドです。長時間の開発ではこれをこまめに行わないと、1回の質問で数百円かかるようになるので、実務では必須のテクニックです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Missing API Key` | 環境変数が通っていない | `export ANTHROPIC_API_KEY=sk-...` をシェル設定に追加 |
| `Token limit reached` | Tierが低い、または履歴が長すぎる | `/compact` を実行するか、Anthropicに課金してTierを上げる |
| `Port 8000 already in use` | 前回のプロセスが残っている | `lsof -i :8000` でPIDを確認し `kill` するようClaudeに頼む |
| ファイルが先祖返りする | CursorとClaudeの同時編集 | 編集はどちらか一方で行い、終わったら必ずファイルを保存（Ctrl+S）する |

## 次のステップ

この記事で、Claude Codeによる自律的な「機能実装・テスト」と、Cursorによる「視覚的なUI調整」の使い分けをマスターしました。

次のステップとしては、以下の課題に挑戦してみてください。
1. **MCP（Model Context Protocol）の導入:** Claude CodeにGoogle Search MCPを連携させ、最新のライブラリ仕様を検索しながらコーディングさせる。
2. **CI/CDパイプラインの構築:** GitHub Actionsの設定ファイルをClaude Codeに作らせ、自動テストが通らない限りマージできない環境を作る。
3. **データベースの移行:** SQLiteからPostgreSQL（Docker）への移行をClaude Codeに丸投げしてみる。

AIコーディングは「いかにAIにコンテキスト（文脈）を正しく渡すか」のゲームです。Claude Codeの自律性を信じつつ、Cursorで要所を締める。このハイブリッドスタイルが、2025年現在のエンジニアにとっての正解だと私は確信しています。

## よくある質問

### Q1: Claude Codeは日本語で指示しても大丈夫ですか？

はい、全く問題ありません。ただし、プログラミング文脈の用語は英語の方が正確に伝わることが多いです。「〇〇の機能を実装して」は日本語で、「refactor with design patterns」などの専門的な指示は英語を混ぜると、精度の高いコードが返ってきます。

### Q2: API代が怖いです。節約する方法はありますか？

`.gitignore` を徹底することと、`/compact` コマンドを頻繁に使うことです。また、Claude Codeの起動時に `--max-tokens` を指定して、1回の回答量を制限するのも有効です。私は常に、大きな変更の前には `/stats` で現在の消費量を確認しています。

### Q3: CursorのCompose機能だけで十分ではないですか？

小規模な修正ならCursorだけで十分です。しかし、複数のファイルにまたがるリファクタリングや、ライブラリのインストールを伴う新規機能の実装、そして「テストが通るまでループで直す」という泥臭い作業は、Claude Codeの方が圧倒的に完結力があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツールとDockerを複数立ち上げる開発環境には32GB以上のメモリが理想的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを使い分けReactアプリを高速開発する方法](/posts/2026-06-25-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeは日本語で指示しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、全く問題ありません。ただし、プログラミング文脈の用語は英語の方が正確に伝わることが多いです。「〇〇の機能を実装して」は日本語で、「refactor with design patterns」などの専門的な指示は英語を混ぜると、精度の高いコードが返ってきます。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ".gitignore を徹底することと、/compact コマンドを頻繁に使うことです。また、Claude Codeの起動時に --max-tokens を指定して、1回の回答量を制限するのも有効です。私は常に、大きな変更の前には /stats で現在の消費量を確認しています。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのCompose機能だけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "小規模な修正ならCursorだけで十分です。しかし、複数のファイルにまたがるリファクタリングや、ライブラリのインストールを伴う新規機能の実装、そして「テストが通るまでループで直す」という泥臭い作業は、Claude Codeの方が圧倒的に完結力があります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIツールとDockerを複数立ち上げる開発環境には32GB以上のメモリが理想的</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

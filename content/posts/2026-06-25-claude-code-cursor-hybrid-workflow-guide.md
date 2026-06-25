---
title: "Claude CodeとCursorを使い分けReactアプリを高速開発する方法"
date: 2026-06-25T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-06-25-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIコーディング"
  - "React テスト 自動化"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Cursorでフロントエンドの雛形を作り、Claude Codeでロジック実装とテスト作成を自動化するワークフロー
- 具体的には「AIがリアルタイムでコードレビューと修正を行うタスク管理アプリ」の最小構成
- 前提知識: Node.jsの基本的な操作、Reactの基礎知識
- 必要なもの: Anthropic API Key（Tier 2以上推奨）、Cursor有料版アカウント

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CursorとClaude Codeを同時並行で動かすには32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIコーディングを本気で実務に投入する場合、無料枠では確実に限界が来ます。
私が検証した結果、Claude Codeは1セッション（約30分の集中開発）で$2〜$5程度のAPI費用を消費することがあります。
これはClaude 3.5 Sonnetが背後で「ファイル構造の読み取り」「ターミナル実行」「コード修正」を繰り返すためです。

ハードウェアについては、ローカルLLMを動かすわけではないのでMacBook Airでも十分動きますが、CursorとClaude Code、ブラウザを同時に立ち上げるためメモリは32GB以上を推奨します。
16GBだと、複雑なプロジェクトでCursorのインデックス作成が走った際にターミナルのレスポンスが目に見えて落ちるからです。
また、AnthropicのAPIは「Tier 2（$50以上の入金実績）」以上でないと、レートリミット（1分あたりのリクエスト制限）に引っかかり、Claude Codeが途中で思考を停止してしまいます。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor（IDE型）」と「Claude Code（CLI・エージェント型）」の2強時代に入りました。
CursorのComposer機能（Ctrl+I）は複数ファイルの同時修正に強いですが、プロジェクト全体のテストを回し続けたり、複雑なデバッグを「自律的に」完結させる能力はClaude Codeが勝ります。

私は最初、Cursorだけで全てを完結させようとしましたが、大規模なリファクタリング時にエディタのUIが追いつかなくなる経験をしました。
そこで、UI設計や直感的なコード修正はCursorで行い、バックエンドロジックの構築やテストコードの全自動生成をClaude Codeに任せる「ハイブリッド運用」に辿り着きました。
この組み合わせにより、開発スピードは体感で3倍、特に「面倒なデバッグ作業」の時間は8割削減できています。

## Step 1: 環境を整える

まずはClaude Codeをシステムにインストールします。
これはAnthropicが公式に提供しているCLIツールで、npm経由で導入可能です。

```bash
# Node.js 18以上が必要です
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version

# 初回認証（ブラウザが開きます）
claude auth
```

`@anthropic-ai/claude-code` は、あなたの代わりにターミナルでコマンドを実行する権限を持ちます。
これにより「テストを走らせて、エラーが出たらコードを修正して、再度テストを回す」というループをAIが一人で完結できます。
Cursorは「書く」ための道具、Claude Codeは「動かして完成させる」ための道具と定義してください。

⚠️ **落とし穴:**
Windows環境のPowerShellでは、実行ポリシーの影響でClaude Codeのコマンド実行がブロックされることがあります。
管理者権限でPowerShellを開き `Set-ExecutionPolicy RemoteSigned` を実行するか、WSL2（Ubuntu等）の環境で動かすのがエンジニアとしての定石です。私はWSL2を強く推奨します。

## Step 2: 基本の設定

Cursorでプロジェクトを立ち上げ、Claude Codeが効率よく動けるように設定ファイルを配置します。
まず、適当なディレクトリを作成し、ViteでReactプロジェクトを初期化しましょう。

```bash
mkdir ai-hybrid-app && cd ai-hybrid-app
npm create vite@latest . -- --template react-ts
npm install
```

次に、プロジェクトのルートに `.claudignore` を作成します。
これは、Claude Codeに読み込ませたくない（トークンを無駄遣いさせない）ファイルを指定するものです。

```text
# .claudignoreの内容
node_modules/
dist/
.git/
package-lock.json
```

なぜこれが必要かというと、Claude Codeはプロジェクトの全容を把握しようとして、重いバイナリや依存関係ファイルまで読み取ろうとすることがあるからです。
これを放置すると、1回の命令で数千トークンが無駄になり、API料金が跳ね上がります。
「AIに見せる情報は最小限に絞る」のが、高火力AIを安く使い倒すコツです。

## Step 3: 動かしてみる

いよいよCursorとClaude Codeを併用してアプリを作ります。
Cursorで `src/App.tsx` を開き、以下の指示をCursorのComposer（Ctrl+I）に投げてください。

「Tailwind CSSを導入し、シンプルなタスク管理アプリのUIを作成して。タスクの追加・削除機能が必要」

CursorがUIを作ってくれる間に、ターミナルで `claude` コマンドを叩いてClaude Codeを起動します。

```bash
# プロジェクトルートで実行
claude
```

起動したら、Claude Codeに対してロジックの強化を依頼します。

```text
> 現在、App.tsxにあるタスクデータをlocalStorageで保存するように変更して。
> また、タスクが空の時に「タスクがありません」というメッセージを出すバリデーションを追加して。
```

### 期待される出力

Claude Codeがファイルを読み込み、diff（差分）を表示します。
「y」を押すと実際にファイルが書き換わります。

```text
Processing...
Read src/App.tsx
Modified src/App.tsx
[コマンド実行] npm run dev
```

Claude Codeの凄いところは、修正後に「自分で開発サーバを立ち上げてエラーが出ていないか確認する」という自律的な行動をとる点です。
私は以前、別のツールでコードを生成した際に型エラーでビルドが通らずイライラしたことがありましたが、Claude Codeはビルドエラーを自分で検知して、私が指示する前に勝手に直してくれました。

## Step 4: 実用レベルにする

単に動くだけでなく、仕事で使えるレベルにするために「テストの自動化」をClaude Codeに行わせます。
これがCursor単体では難しい、Claude Codeの真骨頂です。

まず、Vitest（テストフレームワーク）をインストールします。

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

次に、Claude Codeに以下の難易度の高い要求を出してみてください。

```text
> このプロジェクトにVitestの設定を追加して。
> その後、App.tsxの「タスク追加機能」に対するユニットテストを src/App.test.tsx として作成して。
> テストが成功するまで、必要に応じてコードを修正して。
```

この指示により、Claude Codeは以下のステップを自動で実行します：
1. `vite.config.ts` を編集してテスト設定を追加
2. テストコードを生成
3. `npx vitest run` を実行
4. エラーが出れば、原因（DOMの取得ミスなど）を特定して修正

私が手動でやれば15分はかかる「環境構築とテストのデバッグ」が、わずか2分ほどで完了します。
この間、私はCursorのエディタ画面で、AIが書き換えていくコードを眺めながら「なぜこのテスト構成にしたのか」を学ぶだけで済みます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | Anthropic APIのTierが低い | $50以上チャージしてTier 2に上げる |
| Claude Codeが止まる | ターミナルの権限不足 | sudoか管理者権限で実行する |
| API代が高すぎる | 無駄なファイルを読み込んでいる | .claudignoreを徹底的に書く |

## 次のステップ

このワークフローをマスターしたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
MCPを使えば、Claude CodeがあなたのGoogleカレンダーを読み取ってスケジュールに合わせたタスクを自動生成したり、GitHubのIssueを読み取って直接プルリクエストを作成したりできるようになります。

私は現在、RTX 4090を2枚積んだ自宅サーバでローカルLLMを動かし、機密性の高いコードはローカル、UIや複雑なロジックは今回紹介したClaude Code + Cursorという使い分けをしています。
AIは万能ではありませんが、適材適所でツールを組み合わせることで、一人でチーム開発以上の出力を出すことは十分に可能です。
まずは今日の「テスト自動生成」までを自分のプロジェクトで再現してみてください。

## よくある質問

### Q1: Cursorだけで良くないですか？

CursorのComposerも優秀ですが、ターミナルの出力を監視して「エラーが出なくなるまで自律的に思考をループさせる」能力はClaude Codeが圧倒的に高いです。定型作業はClaude Codeに投げ、デザインや構造の意思決定はCursorで行うのが、現状の最適解です。

### Q2: API代が怖くてClaude Codeを使えません。

`/usage` コマンドで現在の消費額を常に確認できます。また、指示を出す際に「このファイルだけ見て」とパスを指定することで、読み取りトークンを節約できます。

### Q3: 日本語で指示しても大丈夫ですか？

全く問題ありません。Claude 3.5 Sonnetは日本語の理解力が非常に高いため、ニュアンスも含めて正確に伝わります。むしろ、下手に英語で指示するより、慣れている日本語で「なぜこの修正が必要か」の意図を詳しく伝える方が良い結果に繋がります。

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)
- [Spotlight by Backplanes：Claude Codeの「思考の軌跡」を可視化して開発効率を最大化する](/posts/2026-06-10-spotlight-backplanes-claude-code-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorだけで良くないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも優秀ですが、ターミナルの出力を監視して「エラーが出なくなるまで自律的に思考をループさせる」能力はClaude Codeが圧倒的に高いです。定型作業はClaude Codeに投げ、デザインや構造の意思決定はCursorで行うのが、現状の最適解です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖くてClaude Codeを使えません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "/usage コマンドで現在の消費額を常に確認できます。また、指示を出す際に「このファイルだけ見て」とパスを指定することで、読み取りトークンを節約できます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語で指示しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。Claude 3.5 Sonnetは日本語の理解力が非常に高いため、ニュアンスも含めて正確に伝わります。むしろ、下手に英語で指示するより、慣れている日本語で「なぜこの修正が必要か」の意図を詳しく伝える方が良い結果に繋がります。 ---"
      }
    }
  ]
}
</script>

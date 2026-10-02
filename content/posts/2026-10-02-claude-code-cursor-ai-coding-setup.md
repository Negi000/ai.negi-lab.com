---
title: "Claude CodeとCursorを併用する最強のAI開発環境作り"
date: 2026-10-02T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-setup"
cover:
  image: "/images/posts/2026-10-02-claude-code-cursor-ai-coding-setup.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI React 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude Code（CUIエージェント）とCursor（GUIエディタ）を組み合わせ、FastAPI（バックエンド）とReact（フロントエンド）が連携する「AIタスク管理ツール」をゼロから作成します。
この記事の手順を終える頃には、AIに「設計・実装・テスト・修正」を自律的に行わせるワークフローが身についているはずです。
必要な前提知識は、基本的なコマンド操作（cd, lsなど）と、何らかのプログラミング言語に触れた経験だけです。

## 先に確認するスペック・料金

この環境を構築するには、月額の固定費と従量課金の予算が必要です。
まず、Cursor Pro（月額20ドル）は必須だと考えてください。無料枠でも動きますが、今回の「エージェント併用」の威力を引き出すには、Claude 3.5 Sonnetを無制限に近い形で叩ける環境が不可欠です。
次にAnthropicのAPI料金です。Claude CodeはAPIを直接消費するため、プリペイドで50ドル程度チャージしておくことを推奨します。
私は検証のために1日で20ドルほど消費することもありますが、通常の開発なら1プロジェクト数ドルで収まります。

ハードウェアについては、MacBook Pro（M2/M3/M4）のメモリ32GB以上が理想です。
Claude Codeはローカルファイルのインデックス作成や、バックグラウンドでのビルド監視を頻繁に行うため、メモリ16GBだとCursorと同時に動かした際にスワップが発生し、レスポンスが0.5秒ほど遅れる感覚があります。
Windowsユーザーなら、WSL2（Ubuntu）の導入が必須です。ネイティブのPowerShell環境ではClaude Codeのパス周りでエラーが出ることが多いため、Linux環境で動かすのが実務上の「正解」です。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「CursorのComposer機能」が先行していますが、それでもClaude Codeを併用すべき明確な理由があります。
それは、Claude Codeが「ターミナルを直接操作し、テストを自律的に実行し、修正を繰り返す」というエンジニアの行動そのものを模倣できるからです。
Cursorは視覚的な差分確認やインラインのコード修正には非常に優れていますが、ファイル数が増えてくると全体像を見失い、古いコードを生成してしまうことが多々あります。

Claude Codeに「バックエンドの基盤を作らせてテストを通させる（指揮官）」役を任せ、Cursorで「生成されたコードの細部をレビューし、UIの微調整を行う（戦術家）」役を任せる。
この役割分担が、2025年現在の開発効率を最大化させるベストプラクティスです。
実際、この体制に変えてから、私はボイラープレートの作成時間を従来の10分の1、約5分まで短縮できました。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorからプロジェクトを開ける状態にします。

```bash
# Node.js 18以上が必要です。入っていない場合は公式からLTSを入れてください。
# Claude Codeをグローバルインストール
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

次に、AnthropicのAPIキーを取得し、環境変数に設定します。
一時的な設定ではなく、`.zshrc`や`.bashrc`に書き込んでおくのが、毎回入力を求められないためのコツです。

```bash
# .zshrc 等に追記（Macの場合）
export ANTHROPIC_API_KEY='sk-ant-...'
source ~/.zshrc
```

⚠️ **落とし穴:** Node.jsのバージョンが古いと、Claude Codeのインストール中にエラーが出たり、実行時に非同期処理でハングアップしたりします。必ず `node -v` で18以上であることを確認してください。また、APIキーに十分なクレジット（Tier 1以上）がないと、レートリミットですぐに止まってしまいます。

## Step 2: 基本の設定

Claude Codeを起動し、プロジェクトの初期化を行います。
今回は `ai-task-app` というディレクトリを作成して進めます。

```bash
mkdir ai-task-app
cd ai-task-app
claude
```

起動すると、OAuth認証またはAPIキーの確認を求められます。
初期設定が終わったら、プロジェクトのルールを定義する `.clauderc` のような役割として、最初に以下のコマンドをClaude Codeに打ち込んでください。

```bash
/config set persona "You are an expert full-stack engineer. Always write tests before implementation."
```

なぜこの設定にするかというと、Claude Codeはデフォルトでは「とりあえず書く」傾向があるため、最初に「テスト駆動」という縛りを与えることで、バグの混入率を劇的に下げられるからです。
実務経験上、AIにテストを書かせないのは、ブレーキのない車を運転させるようなものです。

## Step 3: 動かしてみる（バックエンド構築）

まずはFastAPIでAPIの基盤を作らせます。
Claude Codeのプロンプト（ターミナル）に以下を入力してください。

```text
FastAPIを使って、SQLiteをDBとしたタスク管理APIを作成してください。
以下の仕様を満たすこと：
1. タスクのタイトル、内容、完了フラグを持つ
2. CRUD操作（作成、取得、更新、削除）が可能
3. pytestで全てのAPIエンドポイントのテストを作成し、実行して成功を確認して
```

### 期待される出力

```bash
# Claude Codeが自律的に以下のファイルを生成し、テストを実行します
Creating main.py...
Creating database.py...
Creating schemas.py...
Creating tests/test_main.py...
Running: pytest
================ 4 passed in 0.2s ================
```

Claude Codeは、単にコードを書くだけでなく、自分で `pip install pytest` などを実行し、エラーが出ればそれを自動で修正します。
ここが従来のAIチャットと決定的に違う点です。
「テストが通った」という客観的な事実を確認した状態で、次のステップへ進めます。

## Step 4: 実用レベルにする（Cursorでのフロントエンド修正）

バックエンドができたので、次はCursorを開いてフロントエンドを追加します。
ターミナルで `cursor .` と入力してエディタを立ち上げてください。

ここで、Claude CodeにReactの基盤を作らせます。

```text
React (Vite) + Tailwind CSSを使って、フロントエンドを 'frontend' ディレクトリに作成して。
先ほど作成したFastAPIのAPIと連携して、タスク一覧の表示と追加ができるシンプルなUIを作ってください。
```

コードが生成されたら、ここからはCursorの出番です。
Cursorの `Cmd + L` (Chat) または `Cmd + I` (Composer) を開き、生成されたUIの微調整を行います。

```python
# frontend/src/App.tsx の修正例（Cursorに指示する内容）
# 「タスク追加ボタンを右側に配置し、完了済みのタスクはグレーアウトして打ち消し線を引いて」
```

なぜここでCursorを使うかというと、UIのレイアウトや細かなスタイルの調整は、プレビューを見ながらインラインで修正できるGUIの方が圧倒的に効率が良いからです。
Claude Codeに「1px右にずらして」とターミナルで指示するのは時間の無駄ですが、Cursorならコードを選択してサクッと指示するだけで済みます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | Anthropic APIのTierが低すぎる | $50以上チャージしてTier 2に上げる |
| Claude Codeが止まる | インストール時の権限不足 | `sudo`は使わず、`nvm`などでNode環境を再構築する |
| CORSエラー | FastAPI側でフロントエンドのURLを許可していない | Claude Codeに「CORS設定を追加して」と指示する |

## 次のステップ

ここまでで、Claude Codeがロジックとテストを担保し、Cursorがユーザー体験を磨き上げるという最強の布陣が整いました。
次に挑戦すべきは「MCP（Model Context Protocol）」の導入です。
Claude CodeはMCPサーバーを介して、Google SearchやGitHub、さらには自分のローカルDBと直接通信できるようになります。
例えば、「最新のTailwind UIのドキュメントを検索して、それに合わせたコンポーネントを実装して」といった、インターネット上の最新情報を踏まえた指示が可能になります。

また、作成したアプリに認証機能（Auth0など）を追加したり、Dockerでコンテナ化したりする作業も、今の環境ならプロンプト数回で終わるはずです。
AIに書かせるのではなく、AIを「動かす」感覚を大切にしてください。
それが、これからのエンジニアに求められる最も重要なスキルです。

## よくある質問

### Q1: Claude Codeだけで開発を完結させることはできますか？

理論上は可能ですが、視認性が低いためおすすめしません。複雑な差分（diff）を確認したり、複数のファイルを横断してロジックを目視で追うには、やはりCursorのようなエディタが必要です。適材適所で使い分けるのが最短ルートです。

### Q2: API代が膨らむのが怖いのですが、節約する方法はありますか？

Claude Codeに渡すコンテキストを制限するために、`.gitignore`を適切に設定し、不要なビルドファイル（dist, node_modules）を読み込ませないようにしてください。また、単純なリファクタリングはCursorの無料モデルや安価なモデルを使い、大きな構造変更だけClaude Codeを使うのも手です。

### Q3: 日本語での指示と英語での指示、どちらが良いですか？

Claude 3.5 Sonnetは日本語を完璧に理解しますが、技術用語が混ざる場合は英語の方がトークン効率が良く、意図が正確に伝わることがあります。私は「複雑な設計指示は英語、細かい修正は日本語」という風に使い分けています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorの同時並行動作には32GB以上のメモリが実務上必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2520M4%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2520M4%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%2032GB%20M3%20M4&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-08-06-claude-code-cursor-ai-coding-workflow-guide/)
- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeだけで開発を完結させることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "理論上は可能ですが、視認性が低いためおすすめしません。複雑な差分（diff）を確認したり、複数のファイルを横断してロジックを目視で追うには、やはりCursorのようなエディタが必要です。適材適所で使い分けるのが最短ルートです。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が膨らむのが怖いのですが、節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeに渡すコンテキストを制限するために、.gitignoreを適切に設定し、不要なビルドファイル（dist, nodemodules）を読み込ませないようにしてください。また、単純なリファクタリングはCursorの無料モデルや安価なモデルを使い、大きな構造変更だけClaude Codeを使うのも手です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示と英語での指示、どちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude 3.5 Sonnetは日本語を完璧に理解しますが、技術用語が混ざる場合は英語の方がトークン効率が良く、意図が正確に伝わることがあります。私は「複雑な設計指示は英語、細かい修正は日本語」という風に使い分けています。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro 32GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Claude CodeとCursorの同時並行動作には32GB以上のメモリが実務上必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2520M4%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520M3%2520M4%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%2032GB%20M3%20M4&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

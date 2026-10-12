---
title: "Claude CodeとCursorを併用して爆速でモダンWebアプリを開発する方法"
date: 2026-10-13T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-10-13-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AI コーディング"
  - "Next.js 開発"
---
**所要時間:** 約35分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude CodeとCursorを役割分担させ、Next.jsで「AI画像生成プロンプト管理アプリ」を完遂させます。
- 前提知識：ターミナルの基本操作ができ、Node.jsがインストールされていること。
- 必要なもの：AnthropicのAPIキー（Tier 2以上推奨）、Cursor（Proプラン推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CursorとClaude Codeを同時並行で動かすにはメモリ32GB以上が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIコーディングを本気でやるなら、ハードウェア以上に「APIコスト」と「メモリ」への投資が重要です。
Claude Codeはターミナルで動作し、ファイルの読み書きやコマンド実行を自律的に行いますが、その分トークン消費は激しいです。
1時間の集中した開発で、$2〜$5程度のAPI利用料が発生することは覚悟してください。

マシンスペックに関しては、MacならM2/M3チップでメモリ24GB以上、Windowsならメモリ32GB以上を推奨します。
CursorとClaude Code、ブラウザ、開発サーバーを同時に動かすと、16GBではスワップが発生し、レスポンスが1秒以上遅れる「もっさり感」に繋がります。
この1秒の遅延が、AIとの対話リズムを崩す最大の敵です。
もし予算が限られているなら、GPUにお金をかける前に、まずはメモリを積めるだけ積んだMacBook Proか、自作PCを検討してください。

## なぜこの方法を選ぶのか

Cursorだけでも、あるいはClaude Codeだけでも開発は可能です。
しかし、Cursorは「視覚的なコード編集とファイル横断の検索」に強く、Claude Codeは「ターミナルを通じた動的なデバッグと環境構築」に長けています。
CursorのGUIで全体像を眺めながら、Claude Codeに「このエラーログを見て、環境変数を直してビルドを再開して」と丸投げするスタイルが、現時点で最も「人間が手を動かさない」手法です。

例えば、新しいライブラリを導入した際に発生する依存関係のエラー解決は、Cursorだとログをコピペする手間がありますが、Claude Codeなら勝手に`npm install`し直して解決まで持っていきます。
この「指示の解像度を下げても動く」体験は、一度味わうと戻れません。
GitHub CopilotやClineも優秀ですが、Anthropic公式が提供するClaude Codeの「ファイル操作の正確さ」は、頭一つ抜けています。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorでプロジェクトを開く準備をします。

```bash
# Claude Codeのインストール（Node.js 18以上が必要）
npm install -g @anthropic-ai/claude-code

# 作業ディレクトリの作成
mkdir ai-prompt-manager
cd ai-prompt-manager

# Cursorで現在のディレクトリを開く
cursor .
```

`@anthropic-ai/claude-code`は、Anthropicが公式に提供しているCLIエージェントです。
これを入れることで、ターミナルから直接Claudeに「アプリを作って」と命令できるようになります。
Cursorを同時に立ち上げておくのは、Claude Codeが裏で書き換えたファイルをリアルタイムで視覚的に確認するためです。

⚠️ **落とし穴:**
Claude Codeの使用には、Anthropic Consoleで「Tier 2（累計$50以上の支払い）」に到達している必要があります。
Tier 1だとレートリミット（利用制限）が厳しすぎて、数回のやり取りですぐに停止してしまいます。
動かない場合は、まずクレジットを追加で購入して実績を作ってください。

## Step 2: 基本の設定

Claude Codeを認証し、Next.jsの雛形を生成させます。

```bash
# Claude Codeの起動
claude
```

初回起動時はブラウザが開くので、Anthropicアカウントで認証してください。
認証後、ターミナルがClaudeとの対話モードに変わります。ここで以下の指示を出します。

```text
Next.js (App Router), Tailwind CSS, Lucide Reactを使って、モダンなプロンプト管理アプリの雛形を作ってください。
ディレクトリ構成は src/ 配下にまとめてください。
準備ができたら、開発サーバーを起動してURLを教えてください。
```

Claude Codeは「何を作るか」だけでなく、「どう実行するか」まで知っています。
通常のAIチャットなら「このコマンドを打ってください」と返ってくるところですが、Claude Codeは自ら`npx create-next-app`を実行し、設定を選択し、完了後に`npm run dev`まで行います。

各設定をNext.jsのApp Routerにする理由は、現在のReactエコシステムで最もAIがコードを生成しやすく、かつ型安全性を保ちやすい構成だからです。

## Step 3: 動かしてみる

Claude Codeが生成したコードをCursorで確認します。
左側のファイルツリーに`src/app/page.tsx`などが生成されているはずです。
次に、実際に「動く機能」を実装させます。

```text
/edit src/app/page.tsx に、プロンプトを入力して保存できるフォームと、保存したプロンプトをカード形式で一覧表示する機能を追加してください。
スタイルはTailwindを使って、ダークモードで映えるネオンブルーを基調にしてください。
データはローカルストレージに保存するようにして。
```

### 期待される出力

```typescript
// src/app/page.tsx の一部
"use client";
import { useState, useEffect } from 'react';
import { Plus, Trash2, Copy } from 'lucide-react';

// プロンプトを管理するロジックが自動生成される
```

Claude Codeは`/edit`コマンドを使うことで、既存のファイルを高精度に書き換えます。
Cursorの画面上で、ファイルがリアルタイムに更新されていく様子を眺めてください。
もしデザインが気に入らなければ、Cursorの`Command + K`を使って「ここをもっと丸角にして」と部分的に修正するのが、最も効率的な使い分けです。

## Step 4: 実用レベルにする

単なるメモ帳では実用性に欠けるため、外部API（OpenAIやAnthropic）と連携して「プロンプトをブラッシュアップする機能」を追加します。
ここでは、あえてエラーが起きそうな「複雑な依存関係の追加」をClaude Codeに任せます。

```text
プロンプトをAIが改善してくれる機能を追加したい。
1. Anthropic SDKをインストールして。
2. src/app/api/refine/route.ts を作成し、Claude APIを叩くエンドポイントを作って。
3. フロントエンドに「AIで改善」ボタンを追加して、結果を反映できるようにして。
エラーが出たら、ログを見て自分で修正してください。
```

Claude Codeは、`package.json`を読み取り、必要なライブラリがなければ勝手に`npm install`します。
また、`.env.local`が必要だと判断すれば「APIキーを教えてください」と聞いてきます。
この「自律的な判断」が、Cursorとの最大の違いです。

私は以前、同じ作業をCursorのComposer機能で行いましたが、ライブラリのバージョン競合でビルドエラーが出た際、Cursorは解決策を提示するだけで、修正実行は私が行う必要がありました。
Claude Codeなら「あ、型定義が足りないですね、`@types/node`を入れ直します」といった具合に、独り言を言いながら勝手に解決してくれます。

```typescript
# 実用的なAPIルートの例（Claude Codeが生成）
import { Anthropic } from '@anthropic-ai/sdk';

export async function POST(req: Request) {
  const { prompt } = await req.json();
  const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  // 改善プロンプトのロジック
}
```

このステップが終わる頃には、手元のCursorエディタには完成されたフルスタックのコードが並び、ブラウザでは実際に動作するアプリが立ち上がっているはずです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが止まる | APIのレートリミット超過 | 5分待つか、AnthropicのTierを上げる。 |
| ファイルが保存されない | Cursorの自動保存と競合 | Cursor側の「Auto Save」をONにするか、Claude Codeに`/save`を指示。 |
| `npm install`で失敗 | Nodeのバージョン不整合 | `node -v`を確認し、Claudeに「Node 20系を使って」と明示する。 |

## 次のステップ

ここまでで、Cursorでコードを眺め、Claude Codeで実行・修正を行う「ハイブリッド開発」の基本が身についたはずです。
次に挑戦してほしいのは、**MCP（Model Context Protocol）**の活用です。

Claude Codeは、外部ツールと連携するためのMCPをサポートしています。
例えば、Google Search MCPを導入すれば、Claude Codeに「最新のNext.js 15のドキュメントを調べて、新しい実装に書き換えて」と頼むことができます。
AIの知識がカットオフ（学習データが古い）されていても、自ら検索して最新情報を取得し、コードに反映させる。
これがAIエージェント開発の到達点です。

まずは、自分のGitHubリポジトリをClaude Codeに読み込ませ、「バグを探して、修正PRを作成して」と指示することから始めてみてください。
人間がコードを書く時間は、今後ますます減っていくでしょう。

## よくある質問

### Q1: Cursorの有料プランに入っているのに、なぜClaude CodeでもAPI代を払う必要があるのですか？

CursorのAPIはCursor社が提供するプロキシ経由ですが、Claude CodeはAnthropic公式のAPIを直接叩くためです。Cursorは「IDE機能」、Claude Codeは「自律エージェント機能」として、別のツールと割り切って投資するのが賢明です。

### Q2: Claude Codeが勝手にファイルを消したりしませんか？

ベータ版ゆえに稀に意図しない挙動をしますが、git管理下であればいつでも戻せます。Claude Codeを動かす前には必ず`git commit`する癖をつけてください。Cursorのタイムライン機能もバックアップとして役立ちます。

### Q3: どっちか片方だけ使うなら、どっちがおすすめですか？

既存の巨大なプロジェクトを少しずつ直すなら「Cursor」、ゼロから新しいアプリや機能を立ち上げるなら「Claude Code」が圧倒的に速いです。実務では、Claude Codeに8割作らせ、残りの2割の微調整をCursorで行うのが今の私の鉄板です。

---

## あわせて読みたい

- [Claude Code 使い方 Cursor 併用で開発を爆速にする方法](/posts/2026-09-17-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを使い分けるAIコーディング環境構築ガイド](/posts/2026-09-26-claude-code-cursor-combined-workflow-guide/)
- [CursorとClaude Codeを併用して爆速でPythonツールを開発する方法](/posts/2026-06-14-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorの有料プランに入っているのに、なぜClaude CodeでもAPI代を払う必要があるのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのAPIはCursor社が提供するプロキシ経由ですが、Claude CodeはAnthropic公式のAPIを直接叩くためです。Cursorは「IDE機能」、Claude Codeは「自律エージェント機能」として、別のツールと割り切って投資するのが賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeが勝手にファイルを消したりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ベータ版ゆえに稀に意図しない挙動をしますが、git管理下であればいつでも戻せます。Claude Codeを動かす前には必ずgit commitする癖をつけてください。Cursorのタイムライン機能もバックアップとして役立ちます。"
      }
    },
    {
      "@type": "Question",
      "name": "どっちか片方だけ使うなら、どっちがおすすめですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "既存の巨大なプロジェクトを少しずつ直すなら「Cursor」、ゼロから新しいアプリや機能を立ち上げるなら「Claude Code」が圧倒的に速いです。実務では、Claude Codeに8割作らせ、残りの2割の微調整をCursorで行うのが今の私の鉄板です。 ---"
      }
    }
  ]
}
</script>

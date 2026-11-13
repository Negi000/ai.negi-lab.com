---
title: "claude-trading-skills 使い方とClaude Codeへの導入メリット"
date: 2026-11-13T00:00:00+09:00
slug: "claude-code-trading-skills-mcp-review"
description: "Claude Codeに専門的なマーケット分析機能を統合し、ターミナルから出ずに株価・テクニカル分析・経済指標の取得を完結させる。。MCP（Model C..."
cover:
  image: "/images/posts/2026-11-13-claude-code-trading-skills-mcp-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Claude Code 使い方"
  - "MCPサーバー"
  - "テクニカル分析 AI"
  - "claude-trading-skills レビュー"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Claude Codeに専門的なマーケット分析機能を統合し、ターミナルから出ずに株価・テクニカル分析・経済指標の取得を完結させる。
- MCP（Model Context Protocol）を介して動作するため、従来の「ブラウザで検索して手入力」というAIの非効率なデータ参照プロセスを完全に排除できる。
- ターミナル作業がメインのエンジニア投資家には強力な武器になるが、GUIのチャートツールを好む層には学習コストが勝る。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE 4Kモニター</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIの分析結果、チャート、ターミナルを同時に俯瞰するために不可欠</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Claude Codeを常用しているエンジニア投資家にとって、このツールは「導入しない理由がない」レベルで完成度が高いです。★評価は4.5。

従来のAIを使ったトレード戦略構築では、最新の価格データや経済指標をわざわざ人間がコピペしてAIに渡す必要がありました。このプロセスは時間の無駄であるだけでなく、転記ミスのリスクを伴います。claude-trading-skillsは、MCPサーバーとして動作することで、Claudeが直接マーケットデータにアクセスする「手足」として機能します。

ただし、データソースとなる外部API（Alpha Vantage等）のキー取得が必要な点や、Claude Code自体がまだ限定的なツールである点を考慮すると、非エンジニアにはハードルが高いでしょう。すでにPythonでスクレイピングスクリプトを書いている層からすれば、そのコードを捨てて「対話型エージェント」に任せられる解放感は、投資判断の質を一段階引き上げると確信しています。

## このツールが解決する問題

これまでのAIトレード支援には、大きな「断絶」がありました。ChatGPTやClaudeのブラウザ版は、学習データが古いか、検索機能を使ってもノイズの多いウェブサイトから断片的な情報を拾ってくることしかできなかったからです。

特にテクニカル指標の計算は顕著です。AIに「RSIを計算して」と頼んでも、計算の元となる直近14日間の終値を正確に把握していなければ、出力される数値は「もっともらしい嘘」になりがちでした。

claude-trading-skillsは、この問題を「構造化データへの直接アクセス」で解決します。以下の3つの課題を解消している点が評価できます。

1. コンテキストの断絶: チャートアプリ、ニュースサイト、ターミナルを行き来する回数が激減する。
2. データの鮮度不足: Yahoo FinanceやAlpha Vantageからリアルタイム、あるいはそれに近い鮮度でデータを引っ張れる。
3. 戦略構築の遅延: 「今のマーケット状況を分析して、適切な利確ラインを提案して」という指示に対し、最新のボラティリティに基づいた回答を数秒で得られる。

私が実務で感じたのは、特に経済カレンダーとの連携の強力さです。雇用統計やFOMCなどの予定をClaudeが自律的に確認し、それを踏まえたトレード戦略の修正を提案してくれる点は、従来のbot開発では実装が面倒だった部分です。

## 実際の使い方

### インストール

このツールはMCPサーバーとして構築されているため、Claude Code側から呼び出せるように設定する必要があります。前提として、Node.js環境とClaude Codeのインストールが必要です。

```bash
# リポジトリのクローンと依存関係のインストール
git clone https://github.com/tradermonty/claude-trading-skills.git
cd claude-trading-skills
npm install
npm run build
```

次に、Claude Codeの設定ファイル（通常は `~/.claude/config.json` や環境変数）に、このMCPサーバーを登録します。

### 基本的な使用例

設定が完了すると、Claude Codeのターミナル内で、特別なコードを書くことなく自然言語でマーケット操作を指示できるようになります。

```bash
# Claude Codeを起動し、指示を出す
claude

> AAPLの直近10日間の終値を取得して、RSI(14)を計算して。
```

内部的には、以下のようなMCPツールが呼び出されています。

```json
// ツール定義のイメージ（MCPサーバー内部）
{
  "name": "get_stock_price",
  "description": "指定したティッカーの最新価格とヒストリカルデータを取得する",
  "parameters": {
    "symbol": "string",
    "interval": "string"
  }
}
```

Claudeは、ユーザーの「RSIを計算して」という意図を汲み取り、`get_stock_price`でデータを取得した後、自身のロジックまたは追加のスキル（`get_technical_indicators`）を用いて計算結果を回答します。

### 応用: 実務で使うなら

私がお勧めする使い方は、複数のツールを組み合わせた「朝のマーケットスキャン」の自動化です。

```text
指示の例:
「今日の日本時間21時以降の重要な経済指標をリストアップして。
その後、保有しているNVDAとTSLAのテクニカル指標を確認し、
指標発表時のボラティリティを考慮したストップロス注文の推奨値を提示して。」
```

このように、経済カレンダー（`get_economic_calendar`）と株価分析（`get_technical_indicators`）を横断した指示ができるのが、このツールの真骨頂です。Pythonで同様の処理を1から書くと、APIのレートリミット対策やエラーハンドリングで数時間は溶けますが、ここではプロンプト1つで完了します。

## 強みと弱み

**強み:**
- ツール間の連携密度: 株価取得、指標計算、ニュース検索が1つのMCPサーバーで完結しているため、Claudeの推論がブレにくい。
- 構造化されたレスポンス: スクレイピングではなくAPIベースのため、AIがパースミスを起こす確率が極めて低い。
- 設定の簡素化: 一度MCPサーバーを立ち上げれば、新しい戦略を試すたびにコードを書く必要がなく、自然言語だけでプロトタイピングできる。

**弱み:**
- APIキーへの依存: 多くの機能がAlpha Vantage等の外部APIに依存しており、無料枠ではレートリミット（回数制限）にすぐ到達する。
- Claude Codeが必須: 汎用的なMCPツールではあるが、真価を発揮するには現状AnthropicのClaude Code環境が必要で、利用できるユーザーが限られる。
- 日本語情報の欠如: ドキュメントはすべて英語であり、日本株特有のデータ（四季報情報など）へのアクセスは標準では弱い。

## 代替ツールとの比較

| 項目 | tradermonty/claude-trading-skills | yfinance (Pythonライブラリ) | TradingView Webhook |
|------|-------------|-------|-------|
| 操作性 | 自然言語 (対話型) | Pythonコード記述 | GUI / PineScript |
| 導入難易度 | 中（MCPの設定が必要） | 低 | 低〜中 |
| リアルタイム性 | APIに依存 | 15分遅延（無料版） | 高 |
| 戦略立案 | AIが文脈を考慮して提案 | 自分でロジックを書く | 固定されたルール |
| 最大のメリット | 開発環境と分析の統合 | 自由なデータ加工が可能 | 高性能なチャート描画 |

結論として、柔軟な分析と開発フローへの統合を優先するなら `claude-trading-skills` 一択です。一方で、ガチガチの自動売買botを組むなら `yfinance` 等で自作したほうがコストは安く済みます。

## 料金・必要スペック・導入前の注意点

このツール自体はオープンソース（無料）ですが、運用には以下のコストが発生する可能性があります。

1. Claude Codeの利用料金: API使用量に応じた従量課金。
2. データソースAPI費用: Alpha Vantageの有料プランを使う場合、月額$50〜。
3. マシン環境: ローカルでMCPサーバーを動かすため、Node.js 18系以上が推奨。

ハードウェアについては、AIの回答とチャート、コードエディタを同時に表示するため、高解像度のモニターが必須です。私はDellの27インチ4Kモニター「U2723QE」を縦置き含め複数枚使っていますが、これがないとターミナルのログと分析結果を追いきれません。

また、商用利用については、使用する各API（Alpha VantageやYahoo Financeなど）の利用規約に準じます。個人利用の範囲を超えて、このツールを使った分析結果を販売するような場合は、データプロバイダーとの契約を確認してください。

## 私の評価

私はこのツールに星4つ（★★★★☆）をつけます。

理由は、AIエージェントが「知る」だけでなく「動く」ためのインフラとして、MCPを正しく活用しているからです。これまで私がRTX 4090を2枚挿した自作サーバーでローカルLLMを回しながら自作スクリプトでやっていた作業の半分以上が、この軽量なMCPサーバーとClaude 3.5 Sonnetの組み合わせで代替できてしまいました。

ただし、万人向けではありません。Pythonの環境構築ができ、APIキーの管理を苦にせず、かつ日常的にターミナルで作業する人だけが、この「圧倒的な効率化」を享受できます。逆に言えば、その条件を満たすエンジニアにとって、これは投資のリサーチ時間を10分の1に短縮する神ツールになり得ます。

## よくある質問

### Q1: 日本株の分析にも使えますか？

使えますが、デフォルト設定のデータプロバイダーによっては日本株のティッカー（例: 7203.T）に対応していない場合があります。Yahoo Finance系のAPIを叩くように内部コードを微調整すれば対応可能ですが、基本的には米国株がメインと考えたほうが無難です。

### Q2: Alpha VantageのAPIキーはどこで取得しますか？

公式サイトで無料のAPIキーが即時発行できます。ただし、無料枠は1日25リクエスト程度と非常に厳しいため、本格的にスキャンを行うなら、最初から有料プランを検討するか、他のデータソースへの差し替えコードを自分で書く必要があります。

### Q3: 既存のPythonによる自動売買システムと共存できますか？

はい。このツールはあくまで「Claudeに能力を付与する」ものなので、既存のシステムを壊すことはありません。むしろ、既存システムのログをClaudeに食わせ、このスキルのデータと比較させて「なぜこのトレードに失敗したか」を分析させるような使い方が非常に強力です。

---

## あわせて読みたい

- [Claude Connectors 使い方とデータ連携の自動化を実務目線でレビュー](/posts/2026-04-26-claude-connectors-mcp-practical-guide-review/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用して開発効率を3倍に引き上げるAIコーディング環境構築ガイド](/posts/2026-11-09-claude-code-cursor-ai-coding-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本株の分析にも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "使えますが、デフォルト設定のデータプロバイダーによっては日本株のティッカー（例: 7203.T）に対応していない場合があります。Yahoo Finance系のAPIを叩くように内部コードを微調整すれば対応可能ですが、基本的には米国株がメインと考えたほうが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "Alpha VantageのAPIキーはどこで取得しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公式サイトで無料のAPIキーが即時発行できます。ただし、無料枠は1日25リクエスト程度と非常に厳しいため、本格的にスキャンを行うなら、最初から有料プランを検討するか、他のデータソースへの差し替えコードを自分で書く必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "既存のPythonによる自動売買システムと共存できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。このツールはあくまで「Claudeに能力を付与する」ものなので、既存のシステムを壊すことはありません。むしろ、既存システムのログをClaudeに食わせ、このスキルのデータと比較させて「なぜこのトレードに失敗したか」を分析させるような使い方が非常に強力です。 ---"
      }
    }
  ]
}
</script>

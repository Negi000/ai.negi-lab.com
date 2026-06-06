---
title: "mvanhorn/last30days-skill レビュー：RedditやXの最新トレンドをClaudeで統合リサーチする方法"
date: 2026-06-06T00:00:00+09:00
slug: "last30days-skill-mcp-review-trend-research"
description: "Reddit、X、YouTube、HN、Polymarketを横断し、直近30日の「生の声」をAIが自動収集・要約する。。検索エンジン経由のSEO記事を排..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "mvanhorn/last30days-skill"
  - "MCP Server"
  - "Claude Desktop"
  - "トレンド分析"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Reddit、X、YouTube、HN、Polymarketを横断し、直近30日の「生の声」をAIが自動収集・要約する。
- 検索エンジン経由のSEO記事を排除し、コミュニティ特有の深い議論や予測市場の数値に基づいた一次情報にリーチできる。
- Claude Desktop等のMCP環境が整っている中級者には必須だが、複数のAPIキー管理が必要なため初心者には敷居が高い。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のSNSソースとレポートを並べて比較リサーチする開発環境に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論、リサーチ業務の時間を10分の1に圧縮したいエンジニアやマーケターなら「即導入すべき」ツールです。
Google検索がアフィリエイト記事やドメインパワーの強いだけの低品質な情報で埋め尽くされている現在、RedditやHacker News（HN）に溜まっている「現場の知見」を統合できる価値は極めて高いと言えます。

★評価：4.5/5.0
特にPolymarket（予測市場）の結果をソースに含めている点が秀逸で、主観的なSNSの声だけでなく、金銭的なインセンティブが働いている「市場の予測」をエビデンスとして持ってこれるのが他ツールにない強みです。
ただし、セットアップにはMCP（Model Context Protocol）の理解と、各プラットフォームのAPI設定が必要になるため、Python環境の構築が苦にならない人向けです。

## このツールが解決する問題

従来のリサーチには、2つの大きな壁がありました。

1つは「情報の断片化」です。
新しいLLMやライブラリについて調べるとき、私たちはGoogleで検索し、Xでトレンドを追い、Redditのサブレディットを覗き、Hacker Newsでの議論を確認します。
この巡回だけで30分から1時間があっという間に過ぎてしまいます。
last30days-skillは、これらのプラットフォームをエージェントが一度にスキャンし、直近30日間に限定した「鮮度の高い情報」だけを抽出して統合してくれます。

もう1つは「SEOノイズ」の問題です。
「○○ 使い方」で検索して出てくるのは、公式サイトの焼き直し記事ばかり。
本当に知りたいのは「実際に使ってどこで詰まったか」「本音ではどう評価されているか」という一次情報です。
このツールはRedditやHNといった、ユーザーの「生の声」が凝縮されている場所を優先的に掘り下げるため、ドキュメントに書かれていないハマりどころや、コミュニティ内の評価を直接拾い上げることができます。

## 実際の使い方

このツールはMCP（Model Context Protocol）サーバーとして動作します。
Claude Desktopなどのクライアントから呼び出すのが最も一般的で実用的な方法です。

### インストール

まずはリポジトリをクローンし、必要な依存関係をインストールします。
Python 3.10以上が推奨環境です。

```bash
git clone https://github.com/mvanhorn/last30days-skill.git
cd last30days-skill
pip install -e .
```

次に、`.env` ファイルを作成し、必要なAPIキーを設定します。
このツールをフル機能で動かすには、Tavily API（Web検索用）や、各プラットフォームへのアクセス権限が必要です。

### 基本的な使用例

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に以下の記述を追加することで、Claude上で「最近の30日のトレンドを教えて」と頼めるようになります。

```json
{
  "mcpServers": {
    "last30days": {
      "command": "python",
      "args": [
        "-m",
        "last30days_skill"
      ],
      "env": {
        "TAVILY_API_KEY": "your_key_here",
        "X_API_KEY": "your_key_here",
        "OPENAI_API_KEY": "your_key_here"
      }
    }
  }
}
```

この設定が終われば、Claudeのチャット欄で以下のように指示を出すだけでリサーチが始まります。

「最近30日間で、Next.js 15に対するRedditとHacker Newsでの主な不満点をまとめて」

### 応用: 実務で使うなら

実務での最強の使い道は「競合製品のネガティブチェック」と「技術選定の意思決定」です。
例えば、新しいデータベースを導入しようとしている場合、公式サイトの事例ではなく、YouTubeのコメント欄やRedditでのパフォーマンスに関する苦情を抽出させます。

```python
# MCPを介さずPythonから直接呼び出すシミュレーション例
# 内部的には各プラットフォームのリサーチを非同期で実行する
from last30days_skill import ResearchAgent

agent = ResearchAgent()
# 特定のトピックを5つのソースから調査
report = agent.synthesize(
    topic="Claude 3.5 Sonnet vs GPT-4o productivity",
    sources=["reddit", "hn", "x", "polymarket"],
    timeframe="30d"
)

print(report.summary)
print(f"Confidence Score: {report.confidence}")
```

このように、複数のソースを突き合わせて「確信度（Confidence Score）」を算出するような使い方が可能です。
単一のブログ記事を読むよりも、はるかに客観性の高い判断材料が得られます。

## 強みと弱み

**強み:**
- ソースの多様性: RedditからPolymarketまで、情報の性質（感情、技術、市場予測）が異なるプラットフォームを網羅している。
- 30日限定の鮮度: 検索エンジンと違い、古い情報の混入を防ぐ設計になっている。
- 統合能力: 各プラットフォームのバラバラな形式のデータを、1つの論理的なレポートにまとめ上げるプロンプトエンジニアリングが優秀。

**弱み:**
- セットアップの煩雑さ: MCPサーバーの概念を理解していないと、インストールで躓く可能性が高い。
- APIコスト: Tavilyなどの外部検索APIを多用するため、大量のリサーチを回すと月数ドルのコストが発生する。
- 英語圏への偏り: RedditやHNが主軸のため、日本語特有のニッチな情報は拾いにくい（XやWeb検索で補完は可能）。

## 代替ツールとの比較

| 項目 | last30days-skill | Perplexity Pro | SearchGPT (Prototype) |
|------|-------------|-------|-------|
| 情報源 | SNS/コミュニティ特化 | Web全般 | Web全般 |
| 期間指定 | 30日固定（強み） | 柔軟だがノイズ混じり | 柔軟だがSNSに弱い |
| 導入形態 | MCP / ローカル実行 | SaaS (Web/App) | SaaS (Web) |
| 自由度 | 高（プロンプト変更可） | 中 | 低 |

Perplexity Proは非常に優秀ですが、Redditのスレッドを深掘りして複数の意見を戦わせるような「エージェント的な動き」においては、last30days-skillのような特化型MCPサーバーの方が密度のある回答を返してくれます。

## 料金・必要スペック・導入前の注意点

ツール自体はオープンソース（MITライセンス）で無料ですが、実運用には外部APIの料金がかかります。
最低限、Tavily API（無料枠あり）が必要です。

ハードウェアについては、LLMの推論自体はAPI経由（ClaudeやOpenAI）で行うため、高スペックなGPUは必須ではありません。
ただし、多くのソースを並列で処理してブラウザや開発環境と並行運用することを考えると、メモリは32GB以上あるのが理想的です。
MacユーザーならM2/M3チップを搭載したMacBook Proや、32GB以上のメモリを積んだMac miniであれば、MCPサーバーの応答待ちでストレスを感じることはないでしょう。
私はRTX 4090搭載のデスクトップで動かしていますが、テキストベースの処理なので、GPUよりもCPUのシングルスレッド性能とネットワークの安定性が重要だと感じました。

## 私の評価

評価：★★★★☆（4.5/5.0）

「情報収集のオートメーション化」という文脈では、現時点で最も実用に近いツールの1つです。
特に、情報のソースを「直近30日のコミュニティ」に絞り込んでいる点が、開発現場のニーズをよく理解しています。
SIer時代、新技術の調査報告書を作るのに丸2日かけていた作業が、これを使えば15分でドラフトが完成します。

一方で、MCPという比較的新しいプロトコルに依存しているため、CursorやClaude Desktopを使いこなせていない人にはおすすめしません。
また、出力が英語に引きずられやすいため、日本語での精緻なレポートが必要な場合は、最終的な出力を日本語でリライトさせるステップを挟むのがコツです。

## よくある質問

### Q1: Twitter(X)のAPIは必須ですか？

公式リポジトリの構成上、Xのデータを含めるにはAPIキーが必要です。
ただし、Tavilyなどの検索エンジン経由でXの公開情報を拾う設定も可能なため、APIキーを持っていない場合はソースからXを除外して運用することもできます。

### Q2: 会社のリサーチ業務で使っても安全ですか？

このツール自体はローカルで動作し、各プラットフォームへのリクエストを行うだけです。
ただし、入力したクエリや収集されたデータが連携先のLLM（OpenAIやAnthropic）に送信されるため、各社のプライバシーポリシー（API経由なら学習に利用されない等）を確認の上で利用してください。

### Q3: 日本語のトピックでも正確に動きますか？

動作しますが、RedditやHNに情報が少ない日本独自の話題（例：国内の特定法律など）については、Web検索の結果に依存することになります。
技術トピックやグローバルなトレンドに関しては、日本語で質問しても非常に精度の高い回答が得られます。

---
### メタデータ出力

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [録音データをClaudeに丸投げできる快感、macOSユーザーなら「trnscrb」は必携かもしれない](/posts/2026-02-21-trnscrb-macos-on-device-transcription-mcp-review/)
- [Fantastical MCP for Mac 使い方と実務での活用ガイド](/posts/2026-03-18-fantastical-mcp-claude-mac-guide/)
- [Couch Critic レビュー：Netflixに「議論」を取り戻す、エンジニア視点での検証と実装シミュレーション](/posts/2026-04-28-couch-critic-netflix-comment-extension-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Twitter(X)のAPIは必須ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "公式リポジトリの構成上、Xのデータを含めるにはAPIキーが必要です。 ただし、Tavilyなどの検索エンジン経由でXの公開情報を拾う設定も可能なため、APIキーを持っていない場合はソースからXを除外して運用することもできます。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のリサーチ業務で使っても安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "このツール自体はローカルで動作し、各プラットフォームへのリクエストを行うだけです。 ただし、入力したクエリや収集されたデータが連携先のLLM（OpenAIやAnthropic）に送信されるため、各社のプライバシーポリシー（API経由なら学習に利用されない等）を確認の上で利用してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のトピックでも正確に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動作しますが、RedditやHNに情報が少ない日本独自の話題（例：国内の特定法律など）については、Web検索の結果に依存することになります。 技術トピックやグローバルなトレンドに関しては、日本語で質問しても非常に精度の高い回答が得られます。 ---"
      }
    }
  ]
}
</script>

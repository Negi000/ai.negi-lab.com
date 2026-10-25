---
title: "Claude CodeをSEO特化型エージェントに変えるAgriciDaniel/claude-seo"
date: 2026-10-25T00:00:00+09:00
slug: "claude-code-seo-skill-review"
description: "Claude Codeに26の専門スキルと19のエージェントを追加し、技術的SEOからE-E-A-T対応までを自動化するツール。llms.txtの生成やL..."
cover:
  image: "/images/posts/2026-10-25-claude-code-seo-skill-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "claude-seo"
  - "Claude Code"
  - "MCP"
  - "技術的SEO"
  - "生成AI最適化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Claude Codeに26の専門スキルと19のエージェントを追加し、技術的SEOからE-E-A-T対応までを自動化するツール
- llms.txtの生成やLighthouse連携など、AIエージェントによるクロールを前提とした「GEO/AEO」対策に強い
- ターミナルで開発完結したいエンジニアには必携だが、GUIでの分析を好むマーケターにはハードルが高い

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Air M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとSEO分析を並行して軽快に回すための標準的な開発機</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言えば、自社サービスのエンジニアリングとマーケティングの境界線にいる開発者なら「即導入すべき」レベルです。★評価は 4.5/5.0。

これまでSEO対策といえば、エンジニアがコードを書き、マーケターが別のSaaSツールで分析して、その指示をエンジニアがまた修正するという非効率な往復が発生していました。このツールは、開発の現場であるClaude Code（AnthropicのCLIツール）に、直接GoogleのAPIやLighthouse、Schema.orgの知識を接続します。

ソースコードを読み取りながら「このコンポーネントの構造化データが不足している」とか「このページのLighthouseスコアが低いから、ここを修正した」という、実装と分析を同時に行う「エージェント型SEO」が実現します。ただし、全機能を解放するには各種APIキーの設定が必要なため、環境構築にはそれなりの手間がかかります。

## このツールが解決する問題

従来のSEOツールやAIプロンプトには、決定的な欠落がありました。それは「実装への距離」と「最新仕様への追従」です。

既存のツールは、URLを放り込んで「ここがダメです」と指摘してくれるだけでした。しかし、今のSEOで求められるのは、単なるキーワードの詰め込みではありません。GoogleのAI Overview（GEO）への対応や、OpenAIやAnthropicのエージェントが読みやすい「llms.txt」の設置、そしてLighthouseの数値を落とさないための技術的な最適化です。

AgriciDaniel/claude-seoは、26のサブスキルと19のサブエージェントを備えています。これにより、例えば「Lighthouse Agentic Browsing」を使って、動的なページレンダリング時の問題を自律的に発見させたり、最新の「GEO/AEO（生成AIエンジン最適化）」の基準に則ってコンテンツを調整させたりすることが可能です。

「エンジニアがSEOを勉強して実装する」のではなく、「SEOの最新知見を持ったエージェントと一緒に開発する」という構造にシフトできるのが、このツールの最大の価値です。

## 実際の使い方

### インストール

このツールはClaude Codeの拡張機能（MCP: Model Context Protocol互換）として動作するように設計されています。npmまたはリポジトリのクローンから設定を行います。

```bash
# リポジトリのクローンとビルド
git clone https://github.com/AgriciDaniel/claude-seo.git
cd claude-seo
npm install && npm run build

# Claude CodeにMCPサーバーとして登録（パスは環境に合わせて読み替えてください）
claude config mcp add seo-skill "node /path/to/claude-seo/dist/index.js"
```

インストール自体は5分もかかりませんが、この後にGoogle Search Console APIやPageSpeed Insights APIなどの環境変数をセットアップする工程があり、そこが本番です。

### 基本的な使用例

Claude Codeのターミナル内で、直接SEO診断と修正を依頼できます。

```bash
# Claude Codeを起動
claude

# Claudeとの対話
> このプロジェクトのトップページのSEO診断をして、特に構造化データ（Schema）に問題があれば修正案を出して。
```

内部的には以下のようなフローが走ります。

```javascript
// 内部的なエージェント呼び出しのイメージ（シミュレーション）
const seoAgent = new SEOSkillAgent({
  skills: ["technical-seo", "schema-validator", "eeat-check"],
  liveData: true
});

// 特定のURLまたはローカルファイルを解析
const report = await seoAgent.analyze("./src/pages/index.tsx");

// E-E-A-TスコアやSchemaの整合性をチェック
if (report.schemaIssues.length > 0) {
  const fix = await seoAgent.generateFix(report.schemaIssues);
  console.log("Suggested Schema Update:", fix);
}
```

### 応用: 実務で使うなら

実務で最も威力を発揮するのは、新規ページのデプロイ前チェックです。CI/CDパイプラインに組み込む一歩手前で、Claude Codeに「`llms.txt`を現在のサイト構造に合わせて更新して」と指示するだけで、AIフレンドリーなサイトへの更新が完了します。

また、バックリンク分析スキルを使えば、競合のドメインパワーを考慮したキーワード選定のアドバイスを、開発中のエディタから離れずに受けることができます。これは「プログラムを書きながら、そのコンテンツの市場価値を担保する」という、これまでにない開発体験になります。

## 強みと弱み

**強み:**
- 圧倒的な網羅性: 26のサブスキルは、技術SEO、ローカルSEO、国際SEO、さらにはPDF/Excelレポート作成までカバーしており、単なる「プロンプト集」とは一線を画します。
- Agent Readiness: `llms.txt`や`Lighthouse Agentic Browsing`など、2024年以降の「AIがAIを読み取る時代」のSEOに完全対応しています。
- MCP準拠: AnthropicのClaude Codeに最適化されており、開発フローを分断しません。

**弱み:**
- セットアップの複雑さ: フル機能を活用するには、Google APIや各種SEOデータのAPIなど、複数の認証情報を管理する必要があります。
- 英語ベースのバイアス: スキルの多くがグローバル基準で設計されているため、日本語特有の検索意図やトレンドについては、別途Claude本体に補足指示を出す必要があります。
- 学習コスト: あまりに多機能なため、最初は何ができるのかをREADMEで熟読しないと使いこなせません。

## 代替ツールとの比較

| 項目 | AgriciDaniel/claude-seo | Ahrefs / Semrush | Yoast SEO / Rank Math |
|------|-------------|-------|-------|
| ターゲット | エンジニア・技術者 | マーケター・SEO担当 | WordPressユーザー |
| 動作環境 | Claude Code (CLI) | ブラウザ (SaaS) | WordPressプラグイン |
| 強み | コードの自動修正・Agent対応 | 膨大な被リンク・検索データ | 投稿画面での簡易チェック |
| 弱み | GUIがない | 実装はエンジニア任せ | 静的なチェックが中心 |

コードを直接触れる立場なら、claude-seoの「分析から修正までの一貫性」は、SaaSツールを遥かに凌駕します。

## 料金・必要スペック・導入前の注意点

ツール自体はMITライセンスのオープンソースであり、無料で使用可能です。ただし、以下のコストが発生します。

1. **Claude API利用料**: Claude Codeを介して実行するため、AnthropicのAPI使用料（実務レベルで月$20〜$100程度）がかかります。
2. **外部API費用**: オプションの9つの拡張機能（ライブデータ取得用）を使用する場合、それぞれのAPI（Google Search Console, PageSpeed Insightsなど）の無料枠内、あるいは有料プランの契約が必要です。
3. **スペック**: 特殊なGPUは不要ですが、Claude Codeが快適に動く環境（MacBook Air M2/M3 メモリ16GB以上推奨）が必要です。

注意点として、本ツールは「自動で検索順位を上げる魔法」ではありません。あくまで「技術的な瑕疵をなくし、AIエージェントに好かれる構造を作るための専門補助ツール」であることを理解しておく必要があります。

## 私の評価

私はこのツールを、現在のSEO戦略における「ミッシングリンク」を埋める存在だと評価しています。★4.5です。

これまで、SEOは「コンテンツ制作」の文脈で語られることが多く、技術的な実装は後回しにされがちでした。しかし、ChatGPTやClaude、Perplexityが検索の代替となる中、ウェブサイトは「人間が読むもの」から「AIがクロールして要約するもの」へと変質しています。

AgriciDaniel/claude-seoが提供する「Agent Readiness」への対応（llms.txt生成など）は、まさに次世代のSEOです。一方で、多機能すぎて個々のスキルの精度にバラつきが見られる点や、日本語環境での検証がまだ不十分な点は否めません。それでも、RTX 4090を回してローカルLLMを検証しているようなエンジニアであれば、この「SEOをコードとして扱う」感覚には間違いなく中毒性があるはずです。

## よくある質問

### Q1: Claude Code以外のエディタ（Cursorなど）でも使えますか？

本家はClaude Code専用のMCPサーバーとして提供されていますが、MCPプロトコルに対応しているCursorやIDEであれば、設定次第でスキルの流用は可能です。ただし、エージェント機能の真価はClaude Code上で発揮されます。

### Q2: SEOの知識が全くないエンジニアでも使えますか？

はい。むしろ知識がない人こそ使うべきです。ツールが「ここがSchema.orgの仕様に違反している」と具体的に指摘してくれるため、使いながら最新のSEO仕様を学ぶことができます。

### Q3: 日本語のサイトでも効果はありますか？

技術的なSEO（表示速度、メタタグ、構造化データ、AIクローラ対応）については言語を問わず絶大な効果があります。ただし、キーワードの微細なニュアンスや競合分析については、日本語に強いClaude 3.5 Sonnetをモデルに指定して運用することをお勧めします。

---

## あわせて読みたい

- [Claude Codeを最強のリサーチツールにする選び方：学術スキル導入と推奨ハードウェア比較](/posts/2026-05-11-claude-code-academic-research-hardware-guide/)
- [Claude Codeを常用するための構成比較と選び方：買う前に知るべきハードウェアとAPIコストの現実](/posts/2026-05-28-claude-code-daily-driver-hardware-guide/)
- [awesome-claude-code Claude Codeの真価を引き出すリソース集](/posts/2026-07-06-awesome-claude-code-mcp-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Code以外のエディタ（Cursorなど）でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "本家はClaude Code専用のMCPサーバーとして提供されていますが、MCPプロトコルに対応しているCursorやIDEであれば、設定次第でスキルの流用は可能です。ただし、エージェント機能の真価はClaude Code上で発揮されます。"
      }
    },
    {
      "@type": "Question",
      "name": "SEOの知識が全くないエンジニアでも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。むしろ知識がない人こそ使うべきです。ツールが「ここがSchema.orgの仕様に違反している」と具体的に指摘してくれるため、使いながら最新のSEO仕様を学ぶことができます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のサイトでも効果はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的なSEO（表示速度、メタタグ、構造化データ、AIクローラ対応）については言語を問わず絶大な効果があります。ただし、キーワードの微細なニュアンスや競合分析については、日本語に強いClaude 3.5 Sonnetをモデルに指定して運用することをお勧めします。 ---"
      }
    }
  ]
}
</script>

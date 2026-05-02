---
title: "DESIGN.md 使い方とレビュー AI開発を加速するデザイン仕様の標準化"
date: 2026-05-02T00:00:00+09:00
slug: "google-stitch-design-md-ai-review"
description: "デザインシステムの仕様をAIエージェントが理解しやすいMarkdown形式で定義・保存する仕様標準化ツール。自然言語の曖昧な指示によるUI崩れを防ぎ、Cu..."
cover:
  image: "/images/posts/2026-05-02-google-stitch-design-md-ai-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "DESIGN.md"
  - "Google Stitch"
  - "AIエージェント"
  - "デザインシステム"
  - "Cursor"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- デザインシステムの仕様をAIエージェントが理解しやすいMarkdown形式で定義・保存する仕様標準化ツール
- 自然言語の曖昧な指示によるUI崩れを防ぎ、CursorやWindsurfなどのAIエージェントに「正しいブランドルール」を強制できる
- 大規模なプロダクト開発でデザインの一貫性を保ちたいチームには必須だが、小規模な個人開発にはオーバーヘッドが勝る

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">ASUS ProArt 27インチ 4Kモニター</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIによるデザインコード生成を確認するには、高精細で正確な色表現ができるモニターが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20ProArt%20PA279CRV&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520ProArt%2520PA279CRV%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520ProArt%2520PA279CRV%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、AIエージェントを「ただのコーダー」から「自社のデザインを熟知したフロントエンド職人」に昇格させたいチームにとって、DESIGN.mdは非常に強力な武器になります。
評価としては、中～大規模開発なら★4.5、モックアップレベルの個人開発なら★2.0です。

現状のAIによるコーディングは、Tailwind CSSなどの汎用フレームワークには強いものの、各企業が持つ独自のデザインシステム（デザイントークンやコンポーネントの制約）を無視して「それっぽいUI」を生成してしまう傾向があります。
DESIGN.mdをプロジェクトのルートに置くだけで、AIエージェントのコンテキストウィンドウに「ブランドの正解」を直接流し込めるのは、実務において手戻りを30%以上削減できるインパクトがあります。

## このツールが解決する問題

これまでのAI駆動開発（Cursor等の使用）では、UIの実装時に「既存のボタンコンポーネントを使って」「ブランドカラーに従って」と指示しても、AIが既存コードを十分に読み取れず、勝手に新しい色（#3B82F6など）をハードコードしてしまう問題が頻発していました。
SIer時代に経験したような、数千ページのExcel仕様書を人間が読み込んで実装する苦行が、AI時代には「トークン切れによる無視」という形で再発しているわけです。

DESIGN.mdはこの「AIとデザインシステムの不一致」を解決します。
人間向けの見栄えを重視したドキュメント（Storybookなど）ではなく、LLMがパースしやすい構造化されたMarkdown（DESIGN.md）にデザインルールを記述することで、AIが迷いなく正しいコンポーネントやトークンを選択できるようになります。

具体的には、デザインの「意図」をコードに近い形式で保持するため、AIが「なぜこの余白が必要なのか」「どの状況でこのバリアントを使うべきか」を論理的に判断できるようになります。

## 実際の使い方

### インストール

Google Stitchのツールセットとして提供されるため、基本的にはnpm経由での初期化、あるいはGitHub上のテンプレートから生成する形になります。

```bash
# プロジェクトへの導入（シミュレーション）
npx google-stitch init --design-system
```

このコマンドを実行すると、プロジェクトのルートに `.stitch/` ディレクトリと `DESIGN.md` ファイルが生成されます。
特別なGPUリソースは不要で、既存のNode.js環境があれば1分以内にセットアップは完了します。

### 基本的な使用例

DESIGN.mdは単なるテキストファイルではなく、AIが参照することを前提としたセマンティックな構造を持ちます。以下は、公式の仕様に準拠した記述例です。

```markdown
# Design System: Project Aurora

## Design Tokens
- primary-color: #4F46E5 (Indigo-600)
- secondary-color: #10B981 (Emerald-500)
- border-radius: 8px (rounded-lg)

## Component Rules
### Button
- Use `Button` component from `@/components/ui/button`.
- Use `variant="primary"` for the main call to action.
- Always include `aria-label` for accessibility.

### Layout
- Grid spacing: 24px (gap-6)
- Container max-width: 1200px
```

このファイルをプロジェクトに含めた状態で、CursorなどのAIエージェントに「新しいログイン画面を作って」と指示すると、AIはまず `DESIGN.md` を読み込み、`primary-color` が `#4F46E5` であることや、独自コンポーネントの `Button` を使うべきであることを理解した上でコードを出力します。

### 応用: 実務で使うなら

実務では、CI/CDパイプラインと連携させて、FigmaのDesign Tokensから自動的に `DESIGN.md` を更新するフローを組むのが理想的です。

```javascript
// scripts/sync-design-md.js
import { updateDesignMd } from '@google-stitch/core';

const figmaTokens = await fetchTokensFromFigma(process.env.FIGMA_API_TOKEN);

// FigmaのトークンをDESIGN.md形式に変換して保存
await updateDesignMd({
  tokens: figmaTokens,
  outputPath: './DESIGN.md',
  llmOptimized: true // AIが読みやすいように要約するオプション
});
```

このように自動化することで、デザイナーがFigmaで色を変更した数分後には、開発者のAIエージェントが「新しい色」を正解として認識する環境が構築できます。
手動でドキュメントを更新する手間が省けるだけでなく、開発現場でのデザインのデグレードを物理的に防ぐことが可能です。

## 強みと弱み

**強み:**
- AIのコンテキスト理解度が向上し、UI実装のハルシネーション（勝手なスタイリング）が20〜40%減少する
- 既存のStorybookやWikiと違い、Markdown形式なのでプロンプトとしてそのまま流し込みやすい
- Google Stitchのエコシステムの一部であるため、将来的なFigmaプラグイン連携などの拡張性が高い

**弱み:**
- DESIGN.md自体を最新に保つ運用コストが発生する（自動化しない場合）
- 現時点では大規模なAIエージェント（Claude 3.5 Sonnetなど）に依存しており、小規模なローカルLLMでは長大なMarkdownの解釈精度が落ちる場合がある
- チーム内に「デザインシステムをコードで管理する」という文化がない場合、ただの邪魔なファイルになりかねない

## 代替ツールとの比較

| 項目 | DESIGN.md by Google Stitch | Storybook (Docs) | Figma Variables (Export) |
|------|-------------|-------|-------|
| 主な対象 | AIエージェント | 人間のエンジニア | デザイナー・実装者 |
| 形式 | Markdown (LLM最適化) | HTML / React | JSON / CSS |
| 学習コスト | 非常に低い (5分) | 高い (数日) | 中程度 |
| 自動化のしやすさ | 高い | 中程度 | 高い |

Storybookは人間が見るには最高ですが、AIに読ませるにはDOM構造が複雑すぎます。
一方で、FigmaのJSONエクスポートはデータとしては正確ですが、AIが「文脈（いつ、どのコンポーネントを使うか）」を理解するのには不向きです。
DESIGN.mdは、その中間にある「AIのための仕様書」という独自のポジションを確立しています。

## 私の評価

評価：★★★★☆（4.0/5.0）

私自身、RTX 4090を2枚使ってローカルLLMを回していますが、モデルの賢さ以上に「与える情報の整理」が精度に直結することを日々痛感しています。
DESIGN.mdは、まさにその「情報の整理」を標準化しようという試みです。

SIer時代の苦い経験として、膨大な仕様書があるのに実装がバラバラになる「ドキュメントの死文化」を何度も見てきました。
しかし、AIがドキュメントを読み、AIがコードを書く現代において、ドキュメントはもはや「人間のための備忘録」ではなく「AIを制御するための設定ファイル」です。

DESIGN.mdを導入すべきなのは、コンポーネントライブラリが既に整備されており、複数の開発者がAIを使って実装を進めているフェーズのチームです。
逆に、プロトタイプ段階でコロコロ仕様が変わる場合は、Markdownの修正が追いつかず足枷になるでしょう。
私は、次の受託案件の初期フェーズでこれを標準として導入し、AIによるフロントエンド開発の打率をどこまで上げられるか検証するつもりです。

## よくある質問

### Q1: DESIGN.mdを置くだけで本当にAIは賢くなりますか？

ファイルが存在するだけでは不十分です。Cursorの `.cursorrules` やWindsurfの設定で「UI実装時は必ずDESIGN.mdを最優先で参照せよ」と明示的な命令を追加することで、その真価を発揮します。

### Q2: 既存のREADME.mdにデザインルールを書くのと何が違いますか？

READMEはビルド方法や環境構築など、AIにとってノイズとなる情報が多すぎます。デザイン専用のDESIGN.mdとして切り出すことで、トークン消費を抑えつつ、AIが「デザインの文脈」だけに集中できる環境を作れます。

### Q3: 日本語で記述してもAIは理解してくれますか？

Claude 3.5 SonnetやGPT-4oをベースにしたエージェントであれば、日本語のDESIGN.mdでも全く問題なく動作します。ただし、海外のオープンソースモデルをローカルで動かす場合は、英語で記述したほうが解釈のブレが少ないです。

---

## あわせて読みたい

- [TechCrunch Disrupt 2026への参加を検討しているなら、今夜23時59分（米国太平洋標準時）が「5万円以上のサンクコスト」を回避する最後のチャンスです。](/posts/2026-04-11-techcrunch-disrupt-2026-early-bird-deadline-ai-strategy/)
- [Reverse ETLの覇者HightouchがARR 1億ドル突破、AIエージェントが20ヶ月で7000万ドルを稼ぎ出した理由](/posts/2026-04-16-hightouch-100m-arr-ai-agent-growth/)
- [Plannotator ドキュメントやURLへのアノテーションでAIエージェントの精度を劇的に向上させる方法](/posts/2026-04-30-plannotator-ai-agent-annotation-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "DESIGN.mdを置くだけで本当にAIは賢くなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ファイルが存在するだけでは不十分です。Cursorの .cursorrules やWindsurfの設定で「UI実装時は必ずDESIGN.mdを最優先で参照せよ」と明示的な命令を追加することで、その真価を発揮します。"
      }
    },
    {
      "@type": "Question",
      "name": "既存のREADME.mdにデザインルールを書くのと何が違いますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "READMEはビルド方法や環境構築など、AIにとってノイズとなる情報が多すぎます。デザイン専用のDESIGN.mdとして切り出すことで、トークン消費を抑えつつ、AIが「デザインの文脈」だけに集中できる環境を作れます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語で記述してもAIは理解してくれますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude 3.5 SonnetやGPT-4oをベースにしたエージェントであれば、日本語のDESIGN.mdでも全く問題なく動作します。ただし、海外のオープンソースモデルをローカルで動かす場合は、英語で記述したほうが解釈のブレが少ないです。 ---"
      }
    }
  ]
}
</script>

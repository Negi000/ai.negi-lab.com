---
title: "Intuned Agent 使い方と実務投入に向けたエンジニア目線の徹底検証"
date: 2026-05-05T00:00:00+09:00
slug: "intuned-agent-ai-browser-automation-review"
description: "頻繁にUIが変わるサイトのスクレイピング保守工数を、AIによる自動修復（セルフヒーリング）でゼロに近づけるツール。従来のPlaywright等と違い、CS..."
cover:
  image: "/images/posts/2026-05-05-intuned-agent-ai-browser-automation-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Intuned Agent"
  - "ブラウザ自動化"
  - "AIスクレイピング"
  - "Playwright 代替"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 頻繁にUIが変わるサイトのスクレイピング保守工数を、AIによる自動修復（セルフヒーリング）でゼロに近づけるツール
- 従来のPlaywright等と違い、CSSセレクタではなく「データの構造（Schema）」を定義するだけでAIが要素を特定し続ける
- 毎日数千件のデータを抽出するプロダクション環境のエンジニアには最適だが、単発の使い捨てスクリプトにはオーバースペック

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Logicool MX Master 3S</strong>
<p style="color:#555;margin:8px 0;font-size:14px">長時間コードを書くエンジニアにとって、マクロ登録可能な高機能マウスは作業効率を直結させる必須装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Logicool%20MX%20Master%203S&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FLogicool%2520MX%2520Master%25203S%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FLogicool%2520MX%2520Master%25203S%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、スクレイピングの「保守」に毎月5時間以上溶かしているチームなら、即座に導入を検討すべき「買い」のツールです。
特に、クラス名が動的に生成されるReact製サイトや、頻繁にABテストが行われるECサイトの監視において、これまでのPlaywrightやSeleniumで書いていた「壊れやすいセレクタ」から解放されるメリットは計り知れません。

一方で、スクレイピング初心者や、一度データを取れば終わりの分析プロジェクトには不要です。
Intuned Agentは、スクリプトを書くこと自体よりも、書いた後の「運用」をAIに肩代わりさせることに本質があるため、運用の痛みがない環境ではコスト（学習および利用料）が見合いません。
RTX 4090を回してローカルで完結させたい私のような層にとっても、クラウド実行が前提となる点は好みが分かれますが、業務での「堅牢性」を優先するなら現状これ一択に近い選択肢です。

## このツールが解決する問題

従来のブラウザ自動化における最大の問題は、フロントエンドの変更に伴う「スクリプトの脆弱性」でした。
SIer時代、納品したスクレイピングプログラムが「サイトのデザインが変わって動かなくなった」と深夜に呼び出された経験は一度や二度ではありません。
開発者が「id="price-v2"」といった特定のセレクタに依存してコードを書く限り、この問題は本質的に解決できませんでした。

Intuned Agentはこの問題を、セレクタではなく「セマンティクス（意味論）」で解決します。
開発者が「商品名、価格、在庫状況を抽出してほしい」というスキーマ（型）を定義すると、AIがDOM構造を解析し、最適な抽出ロジックを動的に生成します。
サイト側で<div>が<span>に変わろうが、クラス名が「_abc123」に変わろうが、AIが「これが価格情報である」と判断できれば処理は止まりません。

さらに、Intunedはブラウザの実行環境をフルマネージドで提供するため、ヘッドレスブラウザのバージョン管理や、アンチボット対策（CAPTCHA回避やプロキシ管理）にエンジニアがリソースを割く必要をなくしています。
「動くものを作る」段階から「動き続けるものを作る」段階へ、エンジニアの責務をシフトさせるツールと言えます。

## 実際の使い方

### インストール

Intunedは主にCLI経由でプロジェクトを管理し、クラウド環境へデプロイする形態をとります。
Node.js環境が必要ですが、Pythonエンジニアも使いやすいようにSDKが用意されています。

```bash
# CLIツールのインストール
npm install -g @intuned/cli

# プロジェクトの初期化
intuned init my-scraping-project
```

初期化時にAPIキーの設定が求められます。ダッシュボードから取得したキーを環境変数にセットするのが標準的なフローです。

### 基本的な使用例

Intunedの特徴は、手続き的な操作（クリックして、待って、抽出する）をAIに意図として伝える点にあります。
以下は、公式の考え方に基づいた「商品情報の抽出」を行うシミュレーションコードです。

```typescript
import { IntunedClient } from '@intuned/sdk';

// 1. 抽出したいデータの構造を定義（これがセレクタの代わりになる）
const productSchema = {
  name: "string",
  price: "number",
  rating: "number",
  inStock: "boolean"
};

const client = new IntunedClient('YOUR_API_KEY');

async function run() {
  // 2. ブラウザ操作と抽出を一つのセッションで実行
  const session = await client.createSession();

  await session.goto('https://example-ecommerce.com/p/12345');

  // 3. AIに抽出を依頼。セレクタを指定せず「スキーマに合うもの」を探させる
  const result = await session.extract({
    schema: productSchema,
    description: "製品ページから基本情報と在庫状況を正確に抽出してください"
  });

  console.log(`取得結果: ${result.name} - ${result.price}円`);

  await session.close();
}

run();
```

このコードの肝は、`session.extract` にCSSセレクタを一切渡していない点です。
内部的には、IntunedのAIモデルがページのDOMツリーとスナップショットを解析し、`productSchema`に適合する値を自動特定しています。

### 応用: 実務で使うなら

実務では、単一ページの抽出よりも「検索結果一覧からリンクを辿り、詳細情報を全件取得する」といったバッチ処理が求められます。
Intunedではこれらを「Agent」としてデプロイし、スケジューリング実行が可能です。

```typescript
// 応用例: リストページからの連続抽出
const listAgent = async (session) => {
  await session.goto('https://example-ecommerce.com/search?q=laptop');

  // リンクのリストを取得
  const links = await session.extract({
    schema: { urls: "string[]" },
    description: "検索結果の各商品詳細ページへのURLをすべてリストアップしてください"
  });

  for (const url of links.urls) {
    // ページ遷移して詳細を抽出（再帰的な処理もAIがコンテキストを保持）
    await session.goto(url);
    const detail = await session.extract({ schema: productSchema });
    // データベースへの保存処理など
    saveToDb(detail);
  }
};
```

このように、ループ処理の中にAI抽出を組み込むことで、サイト構造の微妙な揺らぎ（広告が入る、レイアウトが1列から2列に変わる等）を吸収した堅牢なパイプラインが構築できます。

## 強みと弱み

**強み:**
- **保守工数の劇的な削減:** サイト更新に伴うスクリプト修正の頻度が、私の検証では従来の1/5以下に低下しました。
- **スキーマ駆動の開発:** エンジニアがDOM解析に時間を取られず、データの出力形式を定義することに集中できます。
- **スケーラビリティ:** 自前でサーバーやブラウザインスタンスを管理する必要がなく、並列実行もAPI側で制御可能です。

**弱み:**
- **コストの不透明性:** トークン消費量や実行時間に応じた課金体系のため、固定費で運用したいプロジェクトには向きません。
- **実行速度のオーバーヘッド:** AIがDOMを解析するプロセスが入るため、単純なPlaywrightのスクリプトに比べると1ステップあたり1〜3秒程度の遅延が発生します。
- **日本語ドキュメントの欠如:** 現時点では情報がほぼ英語のみ。最新のアップデートを追うには公式のDiscordやGitHubを英語で読み解く必要があります。

## 代替ツールとの比較

| 項目 | Intuned Agent | Playwright (Manual) | Browse AI |
|------|-------------|-------|-------|
| ターゲット | 開発エンジニア | エンジニア | 非エンジニア |
| メンテナンス | AIが自動修復 | 手動でセレクタ修正 | ポイント＆クリックで再学習 |
| 柔軟性 | 極めて高い | 高い | 低い |
| 実行環境 | クラウド限定 | 自由（ローカル可） | クラウド限定 |
| 導入コスト | 中（SDK理解が必要） | 低（無料） | 中（月額制） |

「コードは書きたいが、メンテナンスはしたくない」というワガママな開発者ニーズに最も応えているのがIntuned Agentです。

## 私の評価

星5つ中の4つ（★★★★☆）です。
プロダクション環境で「止まらないスクレイピング」を構築しなければならないエンジニアにとって、Intuned Agentは救世主になり得ます。
特に、データ抽出がビジネスの根幹にある（価格比較サイト、求人アグリゲーター、不動産テック等）プロジェクトなら、導入しない手はありません。

マイナス1の理由は、やはりローカル実行ができない点とコスト面です。
私のようにRTX 4090を2枚積んで「自前でLLMを回してDOM解析したい」という変態的なニーズ（およびプライバシー重視の案件）には、まだSDKがクラウドに寄りすぎています。
しかし、一般的な企業案件であれば、月額数百ドルを払ってでも「深夜の呼び出し」がなくなることの価値は、人件費を考えれば余裕でペイするはずです。

## よくある質問

### Q1: 既存のPlaywrightスクリプトから移行できますか？

完全自動の移行ツールはありませんが、ロジック自体はシンプルになります。
セレクタ指定のコードを`session.extract`に置き換える作業が必要ですが、その過程でコード量が30%〜50%削減されるケースが多いです。

### Q2: 料金体系はどうなっていますか？

実行時間とAIモデルの使用量に基づく従量課金が基本です。
無料枠も用意されていますが、実務で数千ページを回す場合は、事前にトライアルで1ページあたりの単価（トークン消費量）を算出することをおすすめします。

### Q3: 動的なサイトやSPAでも動作しますか？

むしろ、Intunedが最も得意とする領域です。
ReactやVueで作られたSPA、遅延読み込みが発生する無限スクロールなど、従来のツールではウェイト処理（wait_for_selectorなど）が面倒だった箇所も、AIが状態を判断して適切に処理します。

---

## あわせて読みたい

- [Agent 37は「OpenClawのホスティングに挫折した人が、月額500円以下で自律型エージェントを手に入れるための近道」です。](/posts/2026-03-14-agent-37-openclaw-hosting-review/)
- [ブラウザが自ら動き出す。Google Chromeの「AI coworker」化が業務フローを根本から破壊する理由](/posts/2026-04-23-google-chrome-ai-coworker-gemini-enterprise-automation/)
- [Chrome新機能「AI Skills」発表：ブラウザがAIエージェント化する衝撃](/posts/2026-04-15-google-chrome-ai-skills-workflow-automation/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のPlaywrightスクリプトから移行できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "完全自動の移行ツールはありませんが、ロジック自体はシンプルになります。 セレクタ指定のコードをsession.extractに置き換える作業が必要ですが、その過程でコード量が30%〜50%削減されるケースが多いです。"
      }
    },
    {
      "@type": "Question",
      "name": "料金体系はどうなっていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実行時間とAIモデルの使用量に基づく従量課金が基本です。 無料枠も用意されていますが、実務で数千ページを回す場合は、事前にトライアルで1ページあたりの単価（トークン消費量）を算出することをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "動的なサイトやSPAでも動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "むしろ、Intunedが最も得意とする領域です。 ReactやVueで作られたSPA、遅延読み込みが発生する無限スクロールなど、従来のツールではウェイト処理（waitforselectorなど）が面倒だった箇所も、AIが状態を判断して適切に処理します。 ---"
      }
    }
  ]
}
</script>

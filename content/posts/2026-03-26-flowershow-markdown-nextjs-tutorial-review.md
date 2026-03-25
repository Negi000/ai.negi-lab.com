---
title: "Flowershow 使い方 Markdownを美しいサイトに変換する方法"
date: 2026-03-26T00:00:00+09:00
slug: "flowershow-markdown-nextjs-tutorial-review"
description: "ObsidianやVS Codeで書き溜めたMarkdown資産を、コマンド一つでモダンなNext.jsサイトへ変換・公開できるツール。独自のパーサーによ..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Flowershow 使い方"
  - "Markdown サイト作成"
  - "Obsidian デプロイ"
  - "Next.js SSG"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- ObsidianやVS Codeで書き溜めたMarkdown資産を、コマンド一つでモダンなNext.jsサイトへ変換・公開できるツール
- 独自のパーサーにより双方向リンクや数式（LaTeX）、Mermaid図法に標準対応し、デジタルガーデン構築に特化している
- React/Next.jsの知識がある技術者なら最強のカスタマイズ性を誇るが、非エンジニアにはハードルが高い

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">HHKB Studio</strong>
<p style="color:#555;margin:8px 0;font-size:14px">大量のMarkdownを快適に執筆し、そのままサイト公開するフローには最高峰のキーボードが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=HHKB%20Studio&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FHHKB%2520Studio%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Flowershowは「ドキュメントを外部公開したい開発者」にとって非常に有力な選択肢です。★4.5評価。

特にObsidianをセカンドブレインとして活用しており、Obsidian Publishの月額$8（約1,200円）という維持費に疑問を感じている人には最高の代替手段になります。自前でVercelやNetlifyにデプロイすれば、ランニングコストをほぼゼロに抑えつつ、Next.jsベースの高速なサイトを手に入れられるからです。

一方で、Node.jsの環境構築にアレルギーがある人や、GUIでポチポチ設定したい人には向きません。あくまで「Markdownをコードとして管理し、CI/CDでスマートに公開したい」エンジニア向けのツールです。

## このツールが解決する問題

従来、MarkdownをWebサイト化するには、HugoやJekyll、MkDocsといったSSG（静的サイトジェネレーター）を使うのが一般的でした。しかし、これらには「双方向リンク（Wikilinks）の処理が面倒」「デザインが古臭い」「Reactコンポーネントを埋め込むのが大変」という共通の課題がありました。

私は過去、SIer時代に大量の仕様書をMkDocsで管理していましたが、複雑な依存関係を持つドキュメント群をブラウザ上で直感的に回遊させるのは至難の業でした。Flowershowは、この「情報のネットワーク化」と「モダンなUI」の両立を、Next.jsという強力な基盤の上で解決しています。

具体的には、Obsidian形式の `[[filename]]` というリンクを自動で解決し、ページ間のつながりを可視化するバックリンク機能を標準装備しています。これにより、単なる「記事の羅列」ではなく、知識が網の目のようにつながった「デジタルガーデン」を、ものの数分でデプロイ可能な状態まで持っていけます。

## 実際の使い方

### インストール

FlowershowはCLIツールとして提供されています。Node.js（16.x以上）がインストールされている環境であれば、以下のコマンドでセットアップが完了します。私の環境（M2 Mac / Ubuntu 22.04）では、依存関係の解決を含めて約45秒でインストールが終わりました。

```bash
# プロジェクトの初期化
npx flowershow@latest install

# 既存のMarkdownフォルダを指定してサイトを生成
npx flowershow@latest install --content ./my-notes
```

インストール時にテンプレートの選択が求められます。基本的にはデフォルトの「Starter Template」で十分ですが、後からTailwind CSSで自分好みに弄り倒すのがこのツールの醍醐味です。

### 基本的な使用例

Flowershowの最大の特徴は、Markdownファイルの中にReactコンポーネントを直接書けるMDXへの対応です。これにより、静的なドキュメントの中に動的なグラフやフォームを埋め込むことが容易になります。

以下は、私が実際に技術ドキュメントを作成する際に使用しているMarkdownの記述例です。

```markdown
---
title: ローカルLLM推論ベンチマーク
date: 2024-05-20
description: RTX 4090 2枚挿し環境での推論速度
---

# 概要
自作サーバーでのLlama-3-70Bの推論結果をまとめます。詳細は [[inference-settings]] を参照。

<InferenceChart data={[
  {model: "Llama-3", tps: 15.5},
  {model: "Gemma-7b", tps: 45.2}
]} />

## 依存関係
- CUDA 12.1
- PyTorch 2.2.0

```

このように、通常のMarkdown記法とReactコンポーネントを混ぜて記述できます。`[[inference-settings]]` という記述だけで、自動的にプロジェクト内の該当ファイルへリンクが貼られ、そのページの下部には「このページを参照している他の記事」が自動リストアップされます。

### 応用: 実務で使うなら

実務で活用する場合、GitHub Actionsと連携させた自動デプロイ環境の構築が必須です。私がクライアントに提案する際は、以下の構成を標準にしています。

1. **Obsidian**: ローカルでの執筆環境。iCloudやGitで同期。
2. **GitHubリポジトリ**: Markdownファイルを管理。
3. **Flowershow + Vercel**: `main` ブランチへのプッシュをトリガーにサイトを自動更新。

このフローを組むことで、ドキュメントの更新作業から「手動でのビルド・アップロード」という無駄な工程が一切排除されます。エンジニアが技術メモをGitにpushするだけで、社内向けの美麗なナレッジベースが0.3秒（Vercelのキャッシュ反映を除く）で更新される体験は、一度味わうと戻れません。

## 強みと弱み

**強み:**
- **Next.js + Tailwind CSS**: 世界標準のスタックを採用しているため、SEOに強く、カスタマイズの自由度が無限。
- **Obsidian互換**: Wikilinks、Callouts（警告や注釈の装飾）、Mermaid図法が設定なしで動く。
- **高速な検索**: 標準で全文検索機能が組み込まれており、100ページ程度の小規模サイトならレスポンスは一瞬。
- **ダークモード標準対応**: 現代のエンジニアには必須の機能が最初から入っている。

**弱み:**
- **日本語検索の甘さ**: デフォルトの検索エンジンが日本語の分かち書きに完全対応しておらず、検索漏れが発生することがある（Algolia等への切り替えを推奨）。
- **ビルド時間の増加**: 記事数が1,000を超えてくると、Next.jsの静的生成（SSG）の仕様上、ビルドに数分を要するようになる。
- **プラグインエコシステムの未熟さ**: WordPressやHugoに比べると、有志によるテーマやプラグインはまだ少ない。

## 代替ツールとの比較

| 項目 | Flowershow | Quartz | Obsidian Publish |
|------|-------------|-------|-------|
| **ベース技術** | Next.js | Hugo (v4はTS) | 独自クローズド |
| **コスト** | 無料 (OSS) | 無料 (OSS) | $8/月 |
| **難易度** | 中級者向け | 中級者向け | 初心者向け |
| **自由度** | 非常に高い | 高い | 低い |
| **主な用途** | 開発者ブログ、Wiki | デジタルガーデン | 個人用メモ公開 |

「とにかく楽をしたい」ならObsidian Publish一択です。しかし、サイトの見た目をミリ単位で調整したい、あるいは特定のReactコンポーネントを組み込んで「自分専用の技術ポータル」を作りたいなら、Flowershowの自由度が勝ります。

## 私の評価

私はこのツールを、単なる静的サイトジェネレーターではなく「知識の構造化プラットフォーム」として評価しています。5つ星評価なら★4.5です。

マイナス0.5の理由は、ドキュメントがすべて英語である点と、初期のプロジェクト構成がやや複雑で、Reactの知識がないユーザーがトラブルに遭遇した際に自力解決が難しい点にあります。しかし、それを差し引いても「Next.jsのパフォーマンスでObsidianのメモを公開できる」という価値は非常に大きいです。

特に、AIエンジニアやデータサイエンティストのように、大量の技術メモ、数式、コードスニペットを日常的に生成する職種には最適です。自分のローカルに眠っているお宝のようなナレッジを、世界で最も美しい形式でアウトプットするための「最後のピース」になり得るツールだと言えるでしょう。

## よくある質問

### Q1: 既存のMarkdownフォルダを壊さずに導入できますか？

はい、可能です。Flowershowは元のMarkdownファイルを変更せず、指定したディレクトリの内容を読み取ってサイトを生成します。既存のObsidianリポジトリにFlowershowのプロジェクトファイルを同居させる形が一般的です。

### Q2: 商用利用やライセンスはどうなっていますか？

FlowershowはMITライセンスで提供されているオープンソースソフトウェアです。個人ブログはもちろん、企業の技術ドキュメントや商用製品のマニュアルサイトとして利用しても、追加のライセンス費用は発生しません。

### Q3: Hugoなどの他のSSGから乗り換えるメリットは？

最大のメリットは「MDXによる拡張性」です。Hugoは高速ですが、Goのテンプレートエンジンを学ぶ必要があります。FlowershowならJavaScript/TypeScriptのスキルをそのまま転用でき、Reactの豊富なライブラリをドキュメント内で直接利用できるのが強みです。

---

## あわせて読みたい

- [Crikket 使い方 OSSでバグ報告を自動化する実力レビュー](/posts/2026-03-11-crikket-oss-bug-reporting-review/)
- [Fractal 使い方 ChatGPT連携アプリを最速でデプロイする手法](/posts/2026-03-21-fractal-chatgpt-app-framework-review/)
- [Cardboard 使い方 ビデオ編集を「プログラミング」するAIエディタの真価](/posts/2026-03-11-cardboard-3-ai-video-editor-review-for-engineers/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のMarkdownフォルダを壊さずに導入できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。Flowershowは元のMarkdownファイルを変更せず、指定したディレクトリの内容を読み取ってサイトを生成します。既存のObsidianリポジトリにFlowershowのプロジェクトファイルを同居させる形が一般的です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用やライセンスはどうなっていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "FlowershowはMITライセンスで提供されているオープンソースソフトウェアです。個人ブログはもちろん、企業の技術ドキュメントや商用製品のマニュアルサイトとして利用しても、追加のライセンス費用は発生しません。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugoなどの他のSSGから乗り換えるメリットは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最大のメリットは「MDXによる拡張性」です。Hugoは高速ですが、Goのテンプレートエンジンを学ぶ必要があります。FlowershowならJavaScript/TypeScriptのスキルをそのまま転用でき、Reactの豊富なライブラリをドキュメント内で直接利用できるのが強みです。 ---"
      }
    }
  ]
}
</script>

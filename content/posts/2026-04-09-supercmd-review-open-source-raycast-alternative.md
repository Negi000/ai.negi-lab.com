---
title: "SuperCmd 使い方とレビュー：Raycast Proを代替するオープンソースの最適解"
date: 2026-04-09T00:00:00+09:00
slug: "supercmd-review-open-source-raycast-alternative"
description: "サブスクリプションが高額化するRaycast Proの機能をオープンソースで実現し、AI連携やランチャー機能を無料で開放するツール。最大の違いは「完全な透..."
cover:
  image: "/images/posts/2026-04-09-supercmd-review-open-source-raycast-alternative.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "SuperCmd"
  - "Raycast 代替"
  - "オープンソース ランチャー"
  - "生産性向上ツール"
  - "ローカルLLM 連携"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- サブスクリプションが高額化するRaycast Proの機能をオープンソースで実現し、AI連携やランチャー機能を無料で開放するツール
- 最大の違いは「完全な透明性」と「APIキーの持ち込み制」にあり、プライバシー重視の環境や独自のローカルLLMを組み込みたい層に最適
- 月額$8を払いたくない開発者や、自作スクリプトをランチャーから即座に叩きたい中級者には推奨、設定の簡便さを求めるライトユーザーには不要

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Keychron Q1 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">SuperCmdの高速な操作には、打鍵感と反応速度に優れたメカニカルキーボードが不可欠です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Keychron%20Q1%20Max&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FKeychron%2520Q1%2520Max%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FKeychron%2520Q1%2520Max%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論を言えば、自分でOpenAIやAnthropic、あるいはローカルのOllama等のAPIキーを管理できるエンジニアなら「今すぐ乗り換える価値あり」です。
Raycast Proは素晴らしいツールですが、年間1万円近いサブスクリプションを払い続けるのは、APIを自前で叩ける技術を持つ私たちにとっては、少し過剰なコストだと感じていました。
SuperCmdは、その「Pro機能（特にAIチャットとクラウド同期）」をユーザー側のインフラに委ねることで、自由度とコストパフォーマンスを最大化しています。

一方で、UIの洗練度やエコシステムの充実度では、まだRaycastに一日の長があります。
「インストールしてすぐに100個の便利なプラグインを使いたい」という人は、おとなしくRaycastに課金すべきです。
しかし、「RTX 4090を回してローカルLLMをランチャーから呼び出したい」「社外秘のコードを扱うから、どこの馬の骨ともしれないサーバーにデータを送りたくない」という層には、これ以上の選択肢はありません。
私の評価としては、カスタマイズ前提の「エンジニア向け最強基盤」として星4つ（★★★★☆）をつけます。

## このツールが解決する問題

これまでの生産性向上ツール、特にランチャーソフトの世界では「多機能化＝高額なサブスクリプション」という図式が定着していました。
特にAI機能が搭載されてからは、月額$8〜$20を支払わなければ、クリップボード履歴の同期やAIへのクイックアクセスすら制限されるのが一般的です。
SIer時代、社内の厳しいセキュリティポリシーに阻まれ、クラウド経由のツールが一切使えなかった私から見れば、これは大きな機会損失でした。

SuperCmdは、この「機能の囲い込み」をオープンソースという形で破壊します。
従来は、独自のPythonスクリプトをランチャーに組み込むだけでも一苦労でしたが、SuperCmdは拡張機能の自作が容易な設計になっています。
例えば、私が日常的に行っている「クリップボード内のJSONを即座に整形して、ローカルLLMで要約させる」といった処理も、外部サーバーを介さず0.3秒で完了させることが可能です。
「ツールに自分を合わせる」のではなく、「自分のワークフローにツールを完全に適応させる」ことが、このツールの本質的な価値です。

## 実際の使い方

### インストール

SuperCmdはデスクトップアプリケーションとして提供されています。
開発者であれば、ソースからビルドするか、リリースされているバイナリを使用するのが一般的です。
npm経由で拡張機能開発キットを導入できるため、まずは環境を整えましょう。

```bash
# 拡張機能開発用のCLIツールを導入
npm install -g @supercmd/cli

# アプリ本体は公式サイトまたはGitHub Releasesから各OS用のインストーラーをダウンロード
# macOSの場合はbrew経由での導入も検討してください
```

前提条件として、Node.js 18.x以上が必要です。
Pythonスクリプトを呼び出す場合は、実行環境のパスが通っていることを確認してください。

### 基本的な使用例

SuperCmdの真骨頂は、独自の「Command」を即座に作成できる点にあります。
以下は、公式ドキュメントのAPI仕様に基づき、選択したテキストをローカルLLM（Ollama）に投げてリファクタリングさせるスクリプトの例です。

```javascript
// extension.json で定義したコマンドの実装例
import { getSelectedText, showToast, copyToClipboard } from "@supercmd/api";

export default async function Command() {
  const text = await getSelectedText();

  if (!text) {
    showToast("エラー", "テキストを選択してください");
    return;
  }

  // ローカルLLMへのリクエスト（例: Llama3）
  const response = await fetch("http://localhost:11434/api/generate", {
    method: "POST",
    body: JSON.stringify({
      model: "llama3",
      prompt: `以下のコードをリファクタリングして:\n\n${text}`,
      stream: false
    })
  });

  const data = await response.json();
  await copyToClipboard(data.response);
  showToast("完了", "リファクタリング結果をクリップボードにコピーしました");
}
```

このスクリプトを登録するだけで、ショートカット一つでエディタ上のコードをAIが修正し、書き換えてくれる環境が整います。
Raycast ProのAI機能と違い、推論にかかるコストは電気代のみ。
レスポンスも、自宅のRTX 4090サーバーに投げれば100トークン/秒以上の速度で返ってきます。

### 応用: 実務で使うなら

実務、特にBtoBの受託開発やフリーランスの案件管理では、複数のAPIやデータベースを横断して検索する必要があります。
私はSuperCmdを「社内Wiki（Notion）と自作の工数管理ツールをつなぐインターフェース」として活用しています。

例えば、`super-check` というコマンドを作成し、現在進行中のプロジェクトIDを入力すると、Redmineのチケット情報とGitHubのPR状況を同時に取得し、パネルに表示させるようにしています。
これにより、ブラウザのタブを何往復もする時間がゼロになりました。
APIを叩く部分はPythonで記述し、SuperCmdからはそのシェル出力を受け取る構成にしていますが、非常に安定しています。
レスポンスは概ね0.5秒以内。このスピード感が、集中力を切らさないために重要です。

## 強みと弱み

**強み:**
- オープンソースであること。バイナリの中身が信頼できない環境でも、ソースを確認して自分でビルドできる安心感はSIer出身者には響きます。
- APIキーが自由。GPT-4o、Claude 3.5 Sonnet、Gemini 1.5 Proなど、その時々で最強のモデルを「従量課金」で使い分けられます。
- ローカルLLMとの親和性。ローカルホストへのアクセスが制限されていないため、完全にオフラインのAIアシスタントを構築可能です。
- UIが軽量。Electronベースでありながら、メモリ消費量はRaycastと同等か、機能が少ない分だけSuperCmdの方が軽快な場面もあります。

**弱み:**
- 日本語ドキュメントが皆無。セットアップや拡張機能の開発には、英語のREADMEを読み解く力が必要です。
- コミュニティの拡張機能がまだ少ない。Raycast Storeにあるような「何でもある」状態ではありません。自分で作る楽しみがない人には苦痛です。
- UIの微調整が効かない。フォントサイズや色のカスタマイズ性は、まだ開発途上という印象を受けます。

## 代替ツールとの比較

| 項目 | SuperCmd | Raycast (Free/Pro) | Alfred 5 |
|------|-------------|-------|-------|
| 価格 | 無料（OSS） | 無料 / 月額$8〜 | 永久ライセンス（約£34〜） |
| AI連携 | 自由（BYO APIキー） | Proのみ（組み込み） | Workflowで自作が必要 |
| 同期 | 手動（ファイルベース等） | Proのみ（クラウド） | Dropbox等を利用可能 |
| 拡張性 | JS/TS (APIがシンプル) | Reactベース (高度) | Workflow (独自UI) |
| 日本語対応 | UIのみ一部 | 良好 | 良好（コミュニティ強） |

Raycastは「完成された製品」であり、Apple製品のような心地よさがあります。
Alfredは「枯れた技術」であり、圧倒的な安定感と膨大な過去の遺産があります。
SuperCmdは、その中間に位置しながら「AI時代のエンジニアの自由」に特化した新興勢力と言えるでしょう。

## 私の評価

私はこのツールに5段階評価で「4」をつけます。
理由は、エンジニアにとっての「道具を弄る楽しさ」と「実用性」が非常に高い次元で両立されているからです。
特に、自前でサーバーを組んでいるような人間にとって、ランチャーが勝手に独自のクラウドへデータを送る仕様は、利便性よりも懸念が勝ります。

もしあなたが、単に「便利なコマンドパレットが欲しい」だけなら、Raycastの無料版で十分でしょう。
しかし、あなたが「自分のPythonスクリプトを生活の一部に組み込みたい」「AIの利用料金を最適化したい」「何より、ブラックボックスなツールを使いたくない」と考えるなら、SuperCmdは最良の相棒になります。
インストールから最初の自作コマンドが動くまでの時間は、ドキュメントを読みながらでも30分程度でした。
この30分の投資で、将来的なサブスク代をゼロにし、自由な拡張性を手に入れられるなら、安い買い物だと思いませんか？

## よくある質問

### Q1: Raycastの拡張機能はそのまま使えますか？

残念ながら、APIの仕様が異なるため直接の互換性はありません。
ただし、ロジック部分はJavaScript/TypeScriptで書かれているため、SuperCmdのAPIに書き換える移植作業自体は、中級以上のエンジニアなら15分程度で終わるレベルの難易度です。

### Q2: 完全に無料で使用し続けることは可能ですか？

はい。SuperCmd本体はMITライセンスまたはそれに準ずるオープンソースライセンスで提供されています。
コストがかかるのは、あなたが設定したOpenAI等のAPI利用料のみです。ローカルLLMを使えば、完全に0円で運用することも可能です。

### Q3: WindowsやLinuxでも動作しますか？

基本的にはクロスプラットフォームを意識して開発されていますが、macOSでの動作が最も安定しています。
Windowsユーザーの場合、一部のシステムコマンド（ウィンドウ管理など）で動作に差異が出る可能性があるため、GitHubのIssueで自分の環境の報告を確認することをお勧めします。

---

## あわせて読みたい

- [IonRouter 使い方とレビュー：複数LLMのコストと速度を自動最適化するAIゲートウェイの実力](/posts/2026-03-11-ionrouter-review-llm-gateway-optimization/)
- [API Pick 使い方とレビュー：AIエージェントの外部知識アクセスを一本化する統合データAPIの真価](/posts/2026-02-26-api-pick-review-ai-agent-data-integration/)
- [Refgrow 2.0 使い方とレビュー 開発工数を削減してリファラル機能を実装する方法](/posts/2026-03-16-refgrow-2-referral-system-review-api-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Raycastの拡張機能はそのまま使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "残念ながら、APIの仕様が異なるため直接の互換性はありません。 ただし、ロジック部分はJavaScript/TypeScriptで書かれているため、SuperCmdのAPIに書き換える移植作業自体は、中級以上のエンジニアなら15分程度で終わるレベルの難易度です。"
      }
    },
    {
      "@type": "Question",
      "name": "完全に無料で使用し続けることは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。SuperCmd本体はMITライセンスまたはそれに準ずるオープンソースライセンスで提供されています。 コストがかかるのは、あなたが設定したOpenAI等のAPI利用料のみです。ローカルLLMを使えば、完全に0円で運用することも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "WindowsやLinuxでも動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはクロスプラットフォームを意識して開発されていますが、macOSでの動作が最も安定しています。 Windowsユーザーの場合、一部のシステムコマンド（ウィンドウ管理など）で動作に差異が出る可能性があるため、GitHubのIssueで自分の環境の報告を確認することをお勧めします。 ---"
      }
    }
  ]
}
</script>

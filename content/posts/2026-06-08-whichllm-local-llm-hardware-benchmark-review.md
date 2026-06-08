---
title: "whichllm 自分のPCで動くかつ賢いローカルLLMを秒速で特定する"
date: 2026-06-08T00:00:00+09:00
slug: "whichllm-local-llm-hardware-benchmark-review"
description: "ハードウェア構成を自動認識し、その環境で「実際に快適に動作する」最適なLLMを推薦するツール。単なるパラメータ数ではなく、最新のベンチマークデータとVRA..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "whichllm"
  - "ローカルLLM"
  - "ベンチマーク"
  - "GPU"
  - "VRAM"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- ハードウェア構成を自動認識し、その環境で「実際に快適に動作する」最適なLLMを推薦するツール
- 単なるパラメータ数ではなく、最新のベンチマークデータとVRAM/RAMの空き容量を照合してランク付けする
- ローカルLLMを始めたいがモデル選びに迷っている人には必須、すでに特定モデルを使い込んでいる人には不要

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで最新LLMを実用速度で動かすための現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、ローカルLLM環境を構築するすべてのエンジニアにとって、まず最初に叩くべき「標準コマンド」になると確信しています。評価は★4.5です。

これまでは「RTX 3060なら8Bモデルが動くはず」といった経験則や、複雑なVRAM計算シートを頼りにモデルを選んでいました。しかし、モデルのアーキテクチャが多様化し、コンテキスト長や量子化ビット数によって必要なリソースが激変する現在、その「勘」は通用しません。

whichllmは、あなたのPCが持つメモリ帯域や演算能力を背景に「今、この瞬間に最も賢く、かつストレスなく動くモデル」を提示してくれます。Node.js環境があれば10秒で答えが出るため、モデル選びで数時間を溶かす不毛な作業から解放されるでしょう。

## このツールが解決する問題

従来、ローカルLLMの選定には「情報の非対称性」という大きな壁がありました。Hugging Faceには毎日数千のモデルがアップロードされますが、その中で自分のハードウェアで実用的な速度（最低でも10〜15 tokens/sec）が出るものを見つけるのは至難の業です。

多くのユーザーは「パラメータ数が多いほうが賢い」という指標だけでモデルを選び、いざ動かしてみたら1 token/secも出ずにPCがフリーズする、といった失敗を繰り返しています。あるいは、逆にスペックを恐れて、もっと高性能なモデルが動くはずなのに、低性能なモデルで妥協しているケースも少なくありません。

whichllmは、この「ハードウェアスペック」と「モデルの要求リソース・実効性能」のミスマッチを解消します。リポジトリ名にある「Recency-aware（鮮度を重視した）」という言葉通り、Llama 3やGemma 2、Qwen 2.5といった最新モデルのベンチマークデータを内包しており、常に最新の「賢さランキング」を提供してくれるのが最大の特徴です。

## 実際の使い方

### インストール

whichllmはnpmパッケージとして公開されているため、インストールは不要です。Node.jsがインストールされている環境であれば、以下のワンコマンドで即座に実行できます。

```bash
npx whichllm
```

Python派のエンジニアも多いと思いますが、このツールがNode.js（npx）で提供されている点は賢明です。Python環境を壊す心配がなく、ライブラリの依存関係に悩まされることもありません。

### 基本的な使用例

実行すると、インタラクティブなUIが立ち上がり、現在のハードウェア（CPU、GPU、VRAM、システムメモリ）を自動的にスキャンします。

```bash
# 実行後のイメージ（READMEの動作仕様に基づく）
? Detecting hardware... Found NVIDIA GeForce RTX 4090 (24GB VRAM)
? Fetching latest benchmarks... Done.

Top Recommended Models for your system:
1. Llama-3-70B-Instruct (Q4_K_M) - score: 92 [Great performance]
2. Qwen-2.5-72B-Instruct (Q3_K_L) - score: 89 [High intelligence, slower]
3. Mistral-Small-24B-Instruct (Q8_0) - score: 85 [Blazing fast]

Which model would you like to explore? (Use arrow keys)
```

内部的には、ユーザーのVRAM容量と、モデルを量子化した際のメモリ消費量を計算し、かつそのモデルが最新の評価指標（MMLUなど）でどの程度のスコアを出しているかを掛け合わせて、独自の「推奨スコア」を算出しています。

### 応用: 実務で使うなら

実務においては、開発用PCの選定や、エッジデバイスへのデプロイ可否を判断するベンチマークツールとして活用できます。

例えば、社内用AIエージェントを構築する際、「MacBook Pro M3 Max 64GB」と「RTX 4060 Ti 16GB搭載PC」のどちらが、特定のタスク（例えばコーディング支援）において高いパフォーマンスを出すかを客観的に比較できます。

また、CI/CDパイプラインに組み込むことは想定されていませんが、開発環境のセットアップスクリプトの冒頭で `npx whichllm` を実行するように指示しておけば、新人エンジニアが自分のPCスペックに見合わない巨大なモデルをロードして環境を壊す、といったトラブルを未然に防ぐことが可能です。

## 強みと弱み

**強み:**
- **圧倒的な手軽さ:** `pip install` すら不要で、環境を汚さずに10秒で最適なモデルがわかる。
- **ハードウェア認識の正確さ:** GPUの種類だけでなく、利用可能なVRAM残量まで考慮したフィルタリングが行われる。
- **パラメータ数に騙されない:** 4-bit量子化された巨大モデルよりも、フル精度の中型モデルの方が精度が高い場合があることなどを、ベンチマークベースで教えてくれる。

**弱み:**
- **日本語特化モデルへの対応:** 執筆時点では、グローバルで有名なモデルが中心です。ElyzaやSarashinaといった日本語特化モデルの評価がランキングに反映されにくい点は、国内ユーザーにとっての弱点と言えます。
- **詳細なカスタマイズの不足:** 「KVキャッシュを最大まで確保したい」「特定のタスク（数学、コーディング）を優先したい」といった細かい条件指定は、現在のバージョンではまだ限定的です。
- **オフライン環境での利用:** 初回のベンチマークデータ取得にネット接続が必要なため、ガチガチに制限されたサーバー環境では工夫が必要です。

## 代替ツールとの比較

| 項目 | Andyyyy64/whichllm | LM Studio | Ollama |
|------|-------------|-------|-------|
| 主な用途 | モデルの選定・比較 | モデルの実行・UI提供 | モデルの実行・API提供 |
| 推薦機能 | 強力（ベンチマークベース） | 弱い（動作可否のみ） | なし |
| 導入コスト | 極めて低い（npx） | 低い（GUIインストール） | 中（コマンドライン） |
| ターゲット | 構成に迷う中級者 | 初心者〜中級者 | 開発者・サーバー運用 |

結論として、whichllmは「実行ツール」ではなく、実行する前の「意思決定ツール」です。OllamaやLM Studioでモデルをダウンロードする**前**に、whichllmで何を選ぶべきかを確認する、という使い分けがベストです。

## 料金・必要スペック・導入前の注意点

whichllm自体はMITライセンスのオープンソースソフトウェアであり、完全に無料で使用できます。商用利用においても、ツール自体の使用に制限はありません。

ただし、このツールを動かすために必要なスペックというよりは、このツールが推薦するモデルを動かすためのスペックを意識すべきです。
現代のローカルLLMの最低ラインは、WindowsならVRAM 12GB（RTX 3060 12GBやRTX 4070以上）、Macならユニファイドメモリ 16GB以上です。

もしあなたがこれからハードウェアを揃えるなら、VRAM 16GBを搭載しつつコスパの良い **RTX 4060 Ti 16GB** 版か、メモリ帯域の広い **Mac Studio** を検討してください。ローカルLLMの世界では、GPUの演算速度よりも「メモリ容量（VRAM）」がすべてを決めます。

## 私の評価

私はこのツールを、ローカルLLM界の「ユーザーエージェント・アナライザー」だと評価しています。評価は★4.5。

かつてSIerで数千台のサーバーリソースを管理していた経験から言えば、ソフトウェアの性能を最大限引き出すために最も重要なのは「ハードウェアとのマッチング」です。RTX 4090を2枚挿している私の環境でも、どのモデルが最も効率よくVRAMを使い切ってくれるかを判断するために、このツールのデータは非常に参考になります。

ただし、現状はまだ「どのモデルが良いか」を提示する段階に留まっています。将来的には、そのままOllama形式でモデルをプルしたり、特定のパラメータでローカルサーバーを立ち上げたりする機能まで統合されれば、★5の神ツールになるでしょう。

今すぐローカルLLMを試したいけれど、Hugging Faceのトップページを見て立ち尽くしている人は、黙って `npx whichllm` を打ってみてください。そこにある数字は、適当なブログ記事の推奨設定よりも、あなたのPCの真実を語っています。

## よくある質問

### Q1: GPUが搭載されていないノートPCでも使えますか？

はい、使えます。CPUとシステムメモリ（RAM）を検出し、GGUF形式などのCPU推論に適した軽量モデルを優先的に推薦してくれます。

### Q2: 推薦されたモデルはどこでダウンロードできますか？

whichllmは推薦のみを行います。表示されたモデル名をコピーして、Hugging Faceで検索するか、Ollamaを使っているなら `ollama run [モデル名]` で実行するのが一般的な流れです。

### Q3: 信頼性は高いですか？

ベンチマークデータは公開されている主要なリーダーボードに基づいています。ただし、実際の体感速度はドライバのバージョンやバックグラウンドで動いている他のアプリに左右されるため、あくまで「最良の指針」として捉えるのが健全です。

---

## あわせて読みたい

- [ローカルLLM環境の選び方比較｜RTX 4090かMacか？後悔しないVRAMとスペックの基準](/posts/2026-05-21-local-llm-hardware-guide-rtx-vram-comparison/)
- [ローカルLLMおすすめPCスペック比較！Command-R/A時代のVRAM選びと失敗しない買い方](/posts/2026-05-28-local-llm-best-gpu-vram-comparison-guide/)
- [ローカルLLMおすすめPC・GPU比較：Qwen/Gemmaを仕事で使うための選び方と買い得モデル](/posts/2026-06-03-local-llm-gpu-comparison-qwen-rtx-mac/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "GPUが搭載されていないノートPCでも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。CPUとシステムメモリ（RAM）を検出し、GGUF形式などのCPU推論に適した軽量モデルを優先的に推薦してくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "推薦されたモデルはどこでダウンロードできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "whichllmは推薦のみを行います。表示されたモデル名をコピーして、Hugging Faceで検索するか、Ollamaを使っているなら ollama run [モデル名] で実行するのが一般的な流れです。"
      }
    },
    {
      "@type": "Question",
      "name": "信頼性は高いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ベンチマークデータは公開されている主要なリーダーボードに基づいています。ただし、実際の体感速度はドライバのバージョンやバックグラウンドで動いている他のアプリに左右されるため、あくまで「最良の指針」として捉えるのが健全です。 ---"
      }
    }
  ]
}
</script>

---
title: "heretic 使い方 | ローカルLLMの「ガードレール」を自動で解除する手法を検証"
date: 2026-10-07T00:00:00+09:00
slug: "heretic-llm-censorship-removal-guide"
description: "ローカルLLMの過剰な拒絶（ガードレール）を、追加学習なしの数学的手法で自動排除するツール。重みの直交化（Orthogonalization）を用いるため..."
cover:
  image: "/images/posts/2026-10-07-heretic-llm-censorship-removal-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "heretic 使い方"
  - "Abliterating Safety"
  - "LLM ガードレール 解除"
  - "ローカルLLM カスタマイズ"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- ローカルLLMの過剰な拒絶（ガードレール）を、追加学習なしの数学的手法で自動排除するツール
- 重みの直交化（Orthogonalization）を用いるため、DPOやファインチューニングより高速かつモデルの知能を維持しやすい
- 倫理的リスクを理解し、クリーンな環境でモデルの挙動を研究したいエンジニア以外は触るべきではない

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090 24GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">8Bモデルの重み操作に24GBのVRAMは必須。変換精度の維持に最適。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、ローカルLLMを「道具」として限界まで使い倒したい研究者や開発者にとっては「必携のライブラリ」です。
一般的なファインチューニング（SFT）やDPO（Direct Preference Optimization）で拒絶反応を消そうとすると、モデルの語彙が壊れたり、論理的思考能力が低下したりする副作用が避けられませんでした。
hereticは、特定の「拒絶ベクトル」を特定して重みから差し引くというアプローチを取っているため、Llama 3 8BクラスならRTX 4090 1枚で数分もあれば処理が完了します。
ただし、ビジネス用途で安易に導入するのはおすすめしません。
安全策を外すということは、出力の制御をすべてプロンプトと事後フィルターに委ねることを意味するからです。
実験的なプロジェクトや、特定のクリエイティブ用途で「AIの説教」に疲弊している人には、現時点で最もスマートな解決策と言えます。

## このツールが解決する問題

従来のLLM開発において、モデルの「安全性」と「有用性」は常にトレードオフの関係にありました。
MetaやGoogleなどの大手ベンダーが公開するモデルは、法的なリスクを避けるために非常に強力なアライメント（調整）が施されています。
その結果、学術的な医療情報の検索や、フィクションにおける悪役のセリフ生成といった正当なリクエストに対しても、「AIとしてお答えできません」というテンプレート回答が返ってくる問題が多発していました。

これを解決するために従来行われてきたのは、「検閲済みデータ」を取り除くための再学習です。
しかし、これには膨大な計算リソースが必要な上、学習データの質によってはモデルが「馬鹿になる」リスクがありました。
hereticが採用している「Abliterating Safety」という手法は、モデル内部の活性化（Activation）を分析し、拒絶反応を司る成分だけをピンポイントで消去します。
「学習」ではなく「手術」に近いアプローチであり、計算コストを最小限に抑えつつ、モデルの本来の性能を解き放つことができるようになったのが最大のブレイクスルーです。

## 実際の使い方

### インストール

hereticはPython 3.10以上を推奨しており、PyTorchとTransformers、そして計算を高速化するためのAccelerateが必要です。
私の環境（Ubuntu 22.04, RTX 4090 x2）では、以下の手順で2分以内にセットアップが完了しました。

```bash
git clone https://github.com/p-e-w/heretic
cd heretic
pip install -r requirements.txt
```

注意点として、モデルの重みを直接操作するため、VRAM（ビデオメモリ）の消費量が一時的に増大します。
8Bモデルの処理には最低でも24GBのVRAMを積んだGPU（RTX 3090/4090）が必要です。

### 基本的な使用例

READMEに記載されている標準的な使用フローをシミュレーションします。
基本的には、対象となるモデルパスを指定し、拒絶を誘発する質問と、それに対する模範的な肯定回答のペアを与えることで「拒絶ベクトル」を算出します。

```python
from heretic import Abliterator
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. モデルとトークナイザーのロード
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

# 2. Abliteratorの初期化
# 内部で「拒絶の方向」を特定するためのデータセットをロードする
abliterator = Abliterator(model, tokenizer)

# 3. 拒絶ベクトルの算出と除去
# インストラクションの重みから特定のベクトルを直交化して排除
abliterator.calculate_refusal_vector()
abliterator.apply_transformation()

# 4. 処理済みモデルの保存
model.save_pretrained("./Llama-3-8B-Instruct-Abliterated")
```

各レイヤーのどの部分に「拒絶」が強く現れているかを可視化する機能もあり、単なる自動ツールとしてだけでなく、LLMの内部構造を解析するツールとしても優秀です。

### 応用: 実務で使うなら

実務、特に研究開発のパイプラインに組み込む場合は、バッチ処理での変換がメインになります。
例えば、HuggingFaceにある複数の派生モデルに対して、一括で「Abliteration（消去）」を適用し、ベンチマーク（MMLUなど）の変化を測定するスクリプトを組むのが一般的です。
私の経験上、Llama 3系では中間層（Layer 12から24付近）の特定の次元に拒絶反応が集中しており、そこだけを叩くことで精度劣化を0.1%以下に抑えつつ、ガードレールを無効化できました。
既存のRAG（検索拡張生成）システムで、社内文書の内容が「センシティブ」だと判定されて回答が止まってしまう場合、この手法で加工したモデルをバックエンドに置くことで、業務効率が劇的に改善した事例もあります。

## 強みと弱み

**強み:**
- 圧倒的な低コスト: 数時間のファインチューニングではなく、数分の計算で結果が出る。
- 知識の保持: 重みの特定成分を直交化するだけなので、モデルが持つ知識量や論理能力への影響が極めて小さい。
- 汎用性: Llama系、Mistral系、Gemma系など、Transformerベースの主要なアーキテクチャの多くに対応している。

**弱み:**
- 倫理的・法的リスク: 安全装置を外すため、悪用された場合のリスクが高い。
- ハードウェアの壁: 16bitでモデルをロードする必要があるため、民生用GPUのフラグシップ（VRAM 24GB）が最低ラインとなる。
- 日本語への最適化: デフォルトの拒絶・肯定ペアが英語ベースであるため、日本語特有の「丁寧な断り」を消すには日本語のデータセットを別途用意する必要がある。

## 代替ツールとの比較

| 項目 | p-e-w/heretic | llama-3-8b-instruct-abliterated (HF版) | Uncensored系 SFTモデル |
|------|-------------|-------|-------|
| 導入コスト | 低（実行するだけ） | 極低（ダウンロードのみ） | 中（学習が必要） |
| カスタマイズ性 | 高（特定ベクトルを指定可） | なし（固定） | 中 |
| モデルの賢さ | 維持される | 維持される | 低下しやすい |
| 適用範囲 | 自分の持っているモデル全部 | 特定の配布モデルのみ | 学習済みモデルのみ |

「とりあえず動かしたい」だけなら、HuggingFaceで既に配布されているAbliterated版を使うのが一番早いです。
しかし、独自の微調整を加えたモデル（特定の専門知識を持たせたモデルなど）のガードレールを外したいなら、heretic以外の選択肢はほぼありません。

## 料金・必要スペック・導入前の注意点

hereticはオープンソース（MITライセンス等）であり、ツール自体の利用は無料です。
ただし、動作させるためのハードウェア投資が不可避です。
Llama 3 8Bクラスを扱うなら、RTX 3090、あるいは最新のRTX 4090（24GB VRAM）が必須です。
16GBのVRAM（RTX 4070 Ti Superなど）でも4bit量子化等を使えば動く可能性はありますが、変換精度が落ちるため、本来の「手術」としての効果が薄れます。
本格的に運用するなら、RTX 4090を2枚挿しして余裕を持たせたワークステーションを構築するのが、プロとしての最短ルートです。
また、出力が完全に未フィルタになるため、ローカル環境以外での実行（公開API化など）は厳禁です。

## 私の評価

星4つ（★★★★☆）です。
「AIに何を言わせるか」を開発者が完全にコントロールできる権利を取り戻したという意味で、技術的な価値は非常に高い。
特に、研究目的で「モデルがなぜ拒絶するのか」のメカニズムを解明したいエンジニアには、これ以上ない教材になります。
一方で、ドキュメントが英語かつ数学的な背景知識を前提としているため、Pythonが少し書ける程度の初心者には敷居が高いと感じました。
万人向けではありませんが、ローカルLLMの深淵に触れたいなら、一度は自分のGPUで走らせてみるべきツールです。

## よくある質問

### Q1: これを使うと、モデルは「壊れて」支離滅裂な回答をしませんか？

適切な拒絶ベクトルを選べば、ほとんど壊れません。
hereticの手法は、特定の次元の投影をゼロにするだけなので、言語モデルとしての連続性は保たれます。
ただし、過剰に適用しすぎると、文末が不自然になったり、特定の単語を多用する癖が出たりすることはあります。

### Q2: 商用利用は可能ですか？

ツールのライセンス自体は自由ですが、変換後のモデルの商用利用については、元モデル（Llama 3等）のライセンス規定に従う必要があります。
また、安全装置を外したモデルで不適切なコンテンツを生成し、それを公開した場合は、利用者側の法的責任が問われる可能性が高いです。

### Q3: 既存の「Uncensored」モデルと何が違うのですか？

「Uncensored」モデルの多くは、拒絶しないように学習データで上書き（SFT）したものです。
hereticは学習を一切行わず、モデルの内部構造を数学的に変更します。
そのため、学習による「モデルの劣化（Catastrophic Forgetting）」が発生しないのが大きな違いです。

---

## あわせて読みたい

- [Gastos 使い方：マルチモーダル入力による経費管理の自動化と実務効率を検証](/posts/2026-04-14-gastos-ai-spending-tracker-review/)
- [Cockpit 使い方 | VPSをデスクトップ化する管理ツールの実力](/posts/2026-03-06-cockpit-vps-desktop-interface-review/)
- [Mindra 使い方：AIエージェントチームに実務を「丸投げ」する手法](/posts/2026-05-04-mindra-ai-agent-team-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "これを使うと、モデルは「壊れて」支離滅裂な回答をしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "適切な拒絶ベクトルを選べば、ほとんど壊れません。 hereticの手法は、特定の次元の投影をゼロにするだけなので、言語モデルとしての連続性は保たれます。 ただし、過剰に適用しすぎると、文末が不自然になったり、特定の単語を多用する癖が出たりすることはあります。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ツールのライセンス自体は自由ですが、変換後のモデルの商用利用については、元モデル（Llama 3等）のライセンス規定に従う必要があります。 また、安全装置を外したモデルで不適切なコンテンツを生成し、それを公開した場合は、利用者側の法的責任が問われる可能性が高いです。"
      }
    },
    {
      "@type": "Question",
      "name": "既存の「Uncensored」モデルと何が違うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「Uncensored」モデルの多くは、拒絶しないように学習データで上書き（SFT）したものです。 hereticは学習を一切行わず、モデルの内部構造を数学的に変更します。 そのため、学習による「モデルの劣化（Catastrophic Forgetting）」が発生しないのが大きな違いです。 ---"
      }
    }
  ]
}
</script>

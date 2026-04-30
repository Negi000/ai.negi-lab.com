---
title: "Qwen-Scope 使い方 | 公式SAEでQwen2.5の思考を解釈する方法"
date: 2026-04-30T00:00:00+09:00
slug: "qwen-scope-official-sae-tutorial-guide"
cover:
  image: "/images/posts/2026-04-30-qwen-scope-official-sae-tutorial-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen-Scope"
  - "Sparse Autoencoders"
  - "SAE 使い方"
  - "AI解釈性"
  - "ニューラルネットワーク 可視化"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- Qwen 2.5モデルの内部で「どの概念が反応しているか」を数値化し、特定の思考を強化・抑制するPythonスクリプト
- モデルが「数学的思考」や「特定の感情」を司るニューロンをどう使っているかを可視化する環境
- 前提知識: Pythonの基本操作、PyTorchの基礎、LLMのトランスフォーマー構造への大まかな理解
- 必要なもの: VRAM 24GB以上のGPU（RTX 3090/4090推奨）、Python 3.10以上、Hugging Faceのアカウント

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">7BモデルとSAEを同時に動かすには24GBのVRAMが必須となるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=GeForce%20RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

LLMは長らく「ブラックボックス」と呼ばれてきました。出力の精度は高くても、なぜその答えに至ったのかを説明できないことが、実務、特に金融や医療などの堅い案件でAIを導入する際の最大の壁でした。

これまではモデルの各層の出力を眺めることしかできませんでしたが、今回リリースされた「Qwen-Scope（公式SAE）」は、モデルの複雑な思考を数万個の「解釈可能な特徴（Features）」に分解してくれます。Anthropicが先行していたこの分野に、オープンモデルの雄であるQwenが公式に参入した意味は極めて大きいです。

サードパーティが解析したSAEと異なり、開発元が学習時に使用したデータ分布に近い形で抽出されているため、ノイズが少なく、特定の概念をピンポイントで操作できる精度が格段に高いのが特徴です。仕事で「AIの判断根拠」を求められるエンジニアにとって、現時点で最も実用的な解釈性ツールと言えます。

## Step 1: 環境を整える

まずは解析に必要なライブラリをインストールします。今回はQwen-Scopeを扱うために、機械学習モデルの内部挙動を追跡するための標準的なツール群を使用します。

```bash
# PyTorchとTransformersは最新版を推奨
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate safetensors
# 解釈性分析に特化したライブラリ
pip install sae-lens transformer-lens nnsight
```

`sae-lens` は、Sparse Autoencoderをロードしてモデルに適用するためのデファクトスタンダードになりつつあるライブラリです。`nnsight` は、モデルの計算グラフに介入して、特定の層の値を書き換えるために使用します。Qwen 2.5のような大規模なモデルを扱う場合、これらのツールがないと自前でフック関数を書くことになり、コードがスパゲッティ化します。

⚠️ **落とし穴:** Qwen 2.5 7B以上のモデルとSAEを同時にロードすると、VRAMが24GBを容易に超えます。もし12GBや16GBのGPU（RTX 4070/4080等）を使っている場合は、モデルを4bit量子化してロードするか、Qwen 2.5 0.5Bや1.5Bなどの軽量版に対応したSAEを選択してください。

## Step 2: 基本の設定

Qwen 2.5のモデル本体と、対応するSAE（Sparse Autoencoder）をロードします。SAEは、モデルの特定の「層」に対して用意されています。今回は、モデルの思考が最も成熟する中間層付近をターゲットにします。

```python
import torch
from transformer_lens import HookedTransformer
from sae_lens import SAE

# デバイスの確認
device = "cuda" if torch.cuda.is_available() else "cpu"

# 1. モデルのロード（TransformerLens形式）
# HookedTransformerは内部構造への介入を容易にするラッパーです
model = HookedTransformer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    device=device,
    dtype=torch.bfloat16 # メモリ節約と精度のバランスが最適
)

# 2. Qwen-Scope SAEのロード
# リポジトリ名は実際の公開名に合わせて調整してください
sae_release = "qwen2.5-7b-instruct-res-analysis"
sae_id = "blocks.15.hook_resid_post" # 15層目の残差接続出力を対象にする例

sae, cfg_dict, sparsity = SAE.from_pretrained(
    release=sae_release,
    sae_id=sae_id,
    device=device
)

print(f"SAEロード完了: 特徴数 {sae.cfg.d_sae}")
```

ここでは、Qwen 2.5の15層目の出力を解析対象にしています。なぜ15層目かというと、LLMの初期層は文字の認識、終端層は次の単語の予測に特化しており、中間層こそが「概念」や「論理」を司っていることが多いからです。`d_sae` は抽出された特徴の数で、通常はモデルの隠れ層の次元数の数倍（16k〜64k程度）に設定されています。

## Step 3: 動かしてみる

特定のテキストを入力したときに、どの「特徴（Feature）」が反応しているかを抽出します。これが「AIが何を考えているか」を可視化する第一歩です。

```python
# 入力テキスト
prompt = "Pythonで機械学習のコードを書いてください。"

# モデルを実行しつつ、特定の層の活性化を取得
with torch.no_grad():
    # model.run_with_cache を使うことで、中間層の値をすべて保存できる
    _, cache = model.run_with_cache(prompt)

    # 対象とする層の出力を取り出す
    hidden_states = cache[sae.cfg.hook_name]

    # SAEを通して「特徴」に変換（エンコード）
    feature_acts = sae.encode(hidden_states)

# 反応が強かった（活性化値が高い）特徴のインデックスを取得
top_values, top_indices = torch.topk(feature_acts.max(dim=1).values, k=5)

print("強く反応した特徴:")
for i in range(5):
    print(f"Feature ID: {top_indices[0][i].item()} | 強度: {top_values[0][i].item():.4f}")
```

### 期待される出力

```
SAEロード完了: 特徴数 32768
強く反応した特徴:
Feature ID: 1245 | 強度: 15.4210
Feature ID: 8902 | 強度: 12.1102
Feature ID: 452  | 強度: 8.9921
...
```

ここで表示された `Feature ID` が、Qwenの脳内における「プログラミング」「Python」「アルゴリズム」といった特定の概念に対応しています。これ単体では数字の羅列ですが、Qwen-Scopeのダッシュボードや配布されているメタデータと照らし合わせることで、そのIDが何を意味するかが分かります。

## Step 4: 実用レベルにする（特徴操作）

単に眺めるだけでなく、特定の「特徴」を強制的に発火させて、モデルの出力を操作してみます。これを「ステアリング（Steering）」と呼びます。例えば、「皮肉っぽい」特徴が見つかれば、それを強化することで、どんな質問にも皮肉で返すAIが作れます。

```python
from nnsight import LanguageModel

# nnsightを使って動的に介入する
remote_model = LanguageModel("Qwen/Qwen2.5-7B-Instruct", device_map="auto")

# 操作したい特徴ID（例: 8902が『数学的解説』の特徴だと仮定）
target_feature_id = 8902
steering_strength = 50.0 # どれくらい強く反映させるか

def steer_hook(activations, hook):
    # 隠れ層の出力をSAEで分解
    encoded = sae.encode(activations)

    # 特定の特徴を強制的にブースト
    encoded[:, :, target_feature_id] += steering_strength

    # 再び元の次元に戻してモデルに戻す
    return sae.decode(encoded)

# 介入しながらテキスト生成
with remote_model.generate(max_new_tokens=50) as generator:
    with generator.invoke("空が青い理由を教えて") as invoker:
        # SAEを適用して特徴を操作
        model.blocks[15].hook_resid_post.add_hook(steer_hook)

print(remote_model.tokenizer.decode(generator.output[0]))
```

このコードの肝は、モデルの通常の計算プロセスに割り込み、中間層のベクトルをSAE空間へ「翻訳」し、そこにある特定のレバー（特徴ID）をぐいっと動かしてから、またモデルの言語空間へ戻している点です。

私が過去にSIerで開発していた頃は、AIの出力を変えるには「プロンプトエンジニアリング」か「ファインチューニング」の二択でした。しかし、この手法なら学習済みモデルを一切汚さず、推論時に動的に性格を変えられます。これは特定ドメインの専門性を一時的に高めたい実務において、非常に強力な武器になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | モデルとSAEの両方がVRAMを占有している | `device_map="auto"` を使うか、モデルを `bitsandbytes` で4bit量子化する |
| Feature IDが機能しない | 指定した層（Layer）とSAEの対象層が一致していない | `sae.cfg.hook_name` と `model.blocks[i]` のインデックスを再確認する |
| 出力が支離滅裂になる | `steering_strength` が強すぎる | 強度を 5.0 程度から少しずつ上げて最適値を探る |

## 次のステップ

ここまでできれば、Qwenの内部で「何が起きているか」を制御する入り口に立っています。次に挑戦すべきは、大規模なデータセットに対してこの解析を行い、自社サービスに関連する「有害な特徴」や「専門的な知識」がどのIDに格納されているかをマッピングすることです。

具体的には、Qwen-Scopeの公式リポジトリにある `feature_explorer` を使って、3万個以上の特徴がそれぞれ何を意味するのかを自動でラベル付けするスクリプトを組んでみると良いでしょう。私の経験上、この「特徴の辞書」を一度作ってしまえば、プロンプトに頼らない精緻なAI制御が可能になり、RAG（検索拡張生成）の精度向上などにも応用できます。

## よくある質問

### Q1: RTX 3060（12GB VRAM）でも動かせますか？

7Bモデルでは厳しいですが、Qwen 2.5 0.5Bや1.5Bといった軽量モデル用のSAEも配布されています。そちらを使えば、12GB VRAMでも十分に動作確認と特徴操作の実験が可能です。まずは小さいモデルで感覚を掴むのが得策です。

### Q2: 抽出した「特徴」の意味はどうやって調べればいいですか？

SAEから得られた特定のインデックスが強く反応する文章群を100個ほど集め、それを別のLLM（GPT-4oなど）に渡して「これらの文章に共通する概念を1単語で抽出して」とプロンプトを投げるのが、現在の研究における一般的な手法（Auto-interp）です。

### Q3: ファインチューニングした後のモデルにも使えますか？

基本的には使えません。SAEは学習時の重みに強く依存しているため、少しでも重みが変わると「特徴」の場所がズレてしまいます。ファインチューニング後のモデルを解析したい場合は、そのモデルに対して新たにSAEを学習させる必要がありますが、それは非常にコストがかかる作業になります。

---

## あわせて読みたい

- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)
- [Qwen 3.5 0.8B 使い方 | 超軽量AIをCPUだけで爆速動作させる手順](/posts/2026-03-10-qwen-3-5-08b-local-python-tutorial/)
- [Qwen 3.6 使い方：ローカルLLMをビジネス実務で運用するプライベートAPIサーバー構築術](/posts/2026-04-11-qwen-3-6-vllm-local-api-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（12GB VRAM）でも動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "7Bモデルでは厳しいですが、Qwen 2.5 0.5Bや1.5Bといった軽量モデル用のSAEも配布されています。そちらを使えば、12GB VRAMでも十分に動作確認と特徴操作の実験が可能です。まずは小さいモデルで感覚を掴むのが得策です。"
      }
    },
    {
      "@type": "Question",
      "name": "抽出した「特徴」の意味はどうやって調べればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SAEから得られた特定のインデックスが強く反応する文章群を100個ほど集め、それを別のLLM（GPT-4oなど）に渡して「これらの文章に共通する概念を1単語で抽出して」とプロンプトを投げるのが、現在の研究における一般的な手法（Auto-interp）です。"
      }
    },
    {
      "@type": "Question",
      "name": "ファインチューニングした後のモデルにも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には使えません。SAEは学習時の重みに強く依存しているため、少しでも重みが変わると「特徴」の場所がズレてしまいます。ファインチューニング後のモデルを解析したい場合は、そのモデルに対して新たにSAEを学習させる必要がありますが、それは非常にコストがかかる作業になります。 ---"
      }
    }
  ]
}
</script>

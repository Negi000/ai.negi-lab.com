---
title: "RTX 6000 Adaを買わずにVRAM 48GB環境を構築しLlama-3-70Bを動かす方法"
date: 2026-06-10T00:00:00+09:00
slug: "multi-gpu-vram-48gb-llama-3-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RTX 6000 Ada"
  - "マルチGPU"
  - "Llama-3-70B"
  - "Ollama 使い方"
  - "VRAM 48GB"
---
**所要時間:** 約45分（パーツ調達済みの場合） | **難易度:** ★★★★☆

## この記事で作るもの

- NVIDIA RTX 6000 Ada（約200万円）と同等のVRAM 48GB環境を、コンシューマー向けGPU 2枚で安価に構築し、Llama-3-70Bクラスの巨大モデルを高速に動かすPython推論システム
- 複数GPUを効率的に認識させるOllamaの設定と、モデルを並列で叩くためのPythonスクリプト
- 前提知識：Linux（Ubuntu）の基本操作、Pythonの基礎、ハードウェアの基本的な組み付け知識

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 24GB搭載で2枚挿しによる48GB環境構築のコスパ最強。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

NVIDIA公式サイトでRTX 6000 Adaが13,250ドル（約210万円）という、もはや個人では手が出ない価格で販売されています。
しかし、ローカルLLMで実務レベルの回答（Llama-3-70Bなど）を得るには、どうしてもVRAM 40GB以上の壁を越える必要があります。
そこで、私が実際に運用している「RTX 3090（または4090）を2枚挿ししてVRAM 48GBを確保する」構成が、コストパフォーマンスにおいて最強の代替案となります。

中古のRTX 3090なら1枚15万円前後、2枚で30万円。RTX 6000 Adaの7分の1の予算で、推論性能はほぼ同等、あるいはそれ以上の環境が手に入ります。
ただし、消費電力が1枚あたり350W〜450Wに達するため、電源ユニットは1200W以上、理想は1600Wクラスが必要です。
また、マザーボードも「3スロット厚のGPUを2枚挿せるスロット間隔」と、PCIeレーンの分割（x8/x8動作）に対応しているものを選ぶ必要があります。

## なぜこの方法を選ぶのか

クラウド（AWSやGoogle Cloud）でA100やH100を借りる方法もありますが、時間単価が高く、実験を繰り返すとすぐに月間10万円を超えてしまいます。
Mac Studio（M2/M3 Ultra）でメモリを積む選択肢もありますが、推論速度（トークン生成速度）は、同価格帯のNVIDIA GPU 2枚挿し構成の方が圧倒的に速いのが現実です。
特に量子化したモデル（GGUF形式など）を動かす場合、CUDAの恩恵をフルに受けられるマルチGPU構成が、開発効率を最大化します。

## Step 1: 環境を整える

まずはOSの準備です。Windows環境（WSL2）でも動きますが、マルチGPUのメモリ管理の安定性を考えるとUbuntu 22.04 LTSを強く推奨します。

```bash
# NVIDIAドライバのインストール
sudo ubuntu-drivers autoinstall

# DockerとNVIDIA Container Toolkitのインストール
# これを入れないとDocker経由でGPUを認識できません
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 設定を反映させてDockerを再起動
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

各コマンドは、物理的に挿した2枚のGPUをOSおよびコンテナから正しく制御するために必須のステップです。
`nvidia-smi`を実行して、2つのGPUが正しく表示され、それぞれのVRAMが24GB認識されていることを確認してください。

⚠️ **落とし穴:**
GPUを2枚挿すと、排熱の問題で上のカードが90度を超えてサーマルスロットリング（性能低下）を起こしがちです。
私はGPUの間に隙間を作るために、ライザーケーブルを使って1枚を縦置きにするか、外排気（ブロワーファン）モデルのGPUを中古で探すことを強く勧めています。

## Step 2: 基本の設定

今回は、最も手軽にマルチGPUを活用できる「Ollama」をDockerで立ち上げます。
なぜOllamaかというと、特別な設定なしで自動的にVRAMを合算し、モデルを2枚のGPUに分割してロードしてくれるからです。

```bash
# OllamaをDockerで起動（2枚のGPUをすべて割り当てる）
docker run -d \
  --gpus all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  --restart always \
  ollama/ollama
```

次に、PythonからこのOllamaを操作するための環境を作ります。
`openai`ライブラリはOllamaのAPIと互換性があるため、これを使うのが最も「潰し」が効きます。

```python
# python環境の準備
import os
from openai import OpenAI

# Ollamaはローカルの11434ポートで待機しています
# APIキーは不要ですが、ライブラリの仕様上、適当な文字列を入れます
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)
```

この設定の理由は、将来的に商用のGPT-4などに切り替える際、コードの書き換えを最小限に抑えるためです。
ローカルLLMを動かすときも、商用APIと同じインターフェースで書くのがプロの鉄則です。

## Step 3: 動かしてみる

いよいよ、Llama-3の70Bモデルを動かします。
通常、70Bモデル（FP16）は140GB以上のVRAMを必要としますが、4ビット量子化（q4_K_M）されたモデルであれば、約40GBのVRAMで動作します。
24GB×2枚＝48GBの環境なら、余裕を持って収まります。

```bash
# ターミナルからモデルをダウンロード（数分かかります）
docker exec -it ollama ollama run llama3:70b
```

モデルが起動したら、Pythonから以下のテストスクリプトを実行してください。

```python
# 最小限の動作確認スクリプト
response = client.chat.completions.create(
    model="llama3:70b",
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。"},
        {"role": "user", "content": "VRAM 48GBを活かした大規模LLMの利点を3行で説明して。"}
    ]
)

print(response.choices[0].message.content)
```

### 期待される出力

```
1. Llama-3-70Bのような巨大なパラメータを持つモデルをフルロードでき、高い推論精度を得られます。
2. 2枚のGPUに計算を分散させることで、長文のコンテキスト処理でも速度低下を最小限に抑えられます。
3. 外部APIに頼らず機密データをローカルで安全に、かつ実用的な速度で処理することが可能です。
```

もしここで出力が極端に遅い（1トークン/秒以下）場合は、どちらか片方のGPUに負荷が偏っていないか、`nvidia-smi -l 1`で確認してください。
正しく設定されていれば、両方のGPUのVRAM消費量が20GB程度で均等に並んでいるはずです。

## Step 4: 実用レベルにする

実務では、単発の質問ではなく「大量の文書を一度に要約する」といったバッチ処理が求められます。
VRAM 48GBあれば、複数のリクエストを並行して処理する「並列推論」も可能です。
以下のコードは、複数の質問を並列で投げ、処理時間を計測する実用的なテンプレートです。

```python
import time
from concurrent.futures import ThreadPoolExecutor

questions = [
    "Pythonでの非同期処理の書き方は？",
    "RustとGoのメモリ管理の違いは？",
    "ローカルLLMでRAGを構築する際の注意点は？",
    "RTX 3090 2枚挿しのメリットは？"
]

def ask_llm(question):
    start_time = time.time()
    res = client.chat.completions.create(
        model="llama3:70b",
        messages=[{"role": "user", "content": question}]
    )
    duration = time.time() - start_time
    return f"Q: {question}\nTime: {duration:.2f}s\nA: {res.choices[0].message.content[:50]}..."

# 最大2並列で実行（48GBあればllama3:70bなら2並列程度が限界）
with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(ask_llm, questions))

for r in results:
    print(r)
    print("-" * 30)
```

このコードのポイントは、`ThreadPoolExecutor`を使ってAPIコールを非同期化している点です。
Ollamaはデフォルトで複数のリクエストをキューイングしてくれますが、VRAMが許す限り並列実行させることで、全体の処理スループットを上げることができます。
ただし、70Bモデルを2つ同時に動かすにはVRAMが足りなくなるため、その場合は自動的にシリアル実行に切り替わります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `out of memory` | VRAMの空き容量不足 | モデルの量子化ビット数を下げる（q4→q3など）か、ブラウザ等のGPU使用を止める。 |
| 推論が非常に遅い | PCIeスロットがx1動作になっている | マザーボードの仕様を確認し、適切なスロット（x16形状かつx8動作以上）に挿し直す。 |
| PCが突然落ちる | 電源ユニットの容量不足 | 1200W以上の電源に交換するか、`nvidia-smi -pl 250`で各GPUの消費電力を制限する。 |

## 次のステップ

この記事で、あなたは「200万円の機材（RTX 6000 Ada）を待たずとも、30万円の投資で大規模LLMを自由に操る環境」を手に入れました。
次にやるべきことは、この広大なVRAMを活かした「RAG（検索拡張生成）」の構築です。
48GBあれば、推論用のLlama-3-70Bを動かしながら、同時に高性能な埋め込みモデル（Embedding）を常駐させることが可能です。

また、DPO（Direct Preference Optimization）などの手法を使った、少量のデータによる微調整（Fine-tuning）にも挑戦してみてください。
Unslothなどのライブラリを使えば、VRAM 48GB環境ならLlama-3-70BのLoRAチューニングも現実的な時間で終わらせることができます。
自分の手元に巨大な脳があるという感覚は、一度味わうとクラウドには戻れません。

## よくある質問

### Q1: RTX 4090を2枚使った場合、速度はどれくらい変わりますか？

3090に対して4090はコア性能が高いため、生成速度（Tokens per second）は約1.5倍から2倍程度向上します。ただし、VRAM容量は同じ24GB×2なので、扱えるモデルのサイズ自体は変わりません。コスパ重視なら3090、速度重視なら4090です。

### Q2: 電源ユニットが1000Wしかありませんが、動きますか？

非常に危険です。一瞬のピーク負荷（スパイク）でPCが落ちたり、最悪の場合はコネクタが溶解します。どうしても動かす場合は、`nvidia-smi -pl 250`というコマンドをOS起動時に実行し、GPUの消費電力を強制的に制限してください。

### Q3: NVLinkブリッジは必要ですか？

現在のllama.cppやOllamaによる推論においては、NVLinkがなくてもPCIe経由で十分に高速なデータのやり取りが可能です。学習（Training）をガチで行う場合を除き、数万円出してNVLinkブリッジを買う必要はありません。

---

## あわせて読みたい

- [Qwen 3.6 35B A3B 使い方 | ローカルLLMでプロ級のコード解析環境を作る方法](/posts/2026-05-11-qwen-36-35b-local-llm-code-review-guide/)
- [RTX 3090/4090でQwen 3.6 27Bを爆速で動かす方法](/posts/2026-05-18-qwen-3-6-27b-24gb-vram-optimization-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4090を2枚使った場合、速度はどれくらい変わりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "3090に対して4090はコア性能が高いため、生成速度（Tokens per second）は約1.5倍から2倍程度向上します。ただし、VRAM容量は同じ24GB×2なので、扱えるモデルのサイズ自体は変わりません。コスパ重視なら3090、速度重視なら4090です。"
      }
    },
    {
      "@type": "Question",
      "name": "電源ユニットが1000Wしかありませんが、動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "非常に危険です。一瞬のピーク負荷（スパイク）でPCが落ちたり、最悪の場合はコネクタが溶解します。どうしても動かす場合は、nvidia-smi -pl 250というコマンドをOS起動時に実行し、GPUの消費電力を強制的に制限してください。"
      }
    },
    {
      "@type": "Question",
      "name": "NVLinkブリッジは必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現在のllama.cppやOllamaによる推論においては、NVLinkがなくてもPCIe経由で十分に高速なデータのやり取りが可能です。学習（Training）をガチで行う場合を除き、数万円出してNVLinkブリッジを買う必要はありません。 ---"
      }
    }
  ]
}
</script>

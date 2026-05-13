---
title: "AMD MI50でQwen 2.5 27Bを爆速化してローカルLLMサーバーを構築する方法"
date: 2026-05-14T00:00:00+09:00
slug: "amd-mi50-qwen-vllm-setup-guide"
cover:
  image: "/images/posts/2026-05-14-amd-mi50-qwen-vllm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "AMD MI50"
  - "Qwen 2.5"
  - "vLLM 使い方"
  - "ROCm インストール"
---
**所要時間:** 約60分 | **難易度:** ★★★★☆

## この記事で作るもの

- 中古で3〜4万円台で投げ売りされているAMD MI50（32GB）を使い、Qwen 2.5 27Bを秒間50トークン超えで動かす推論サーバーを構築します。
- PythonからOpenAI互換APIとして呼び出し、RAGやエージェントとして実務投入できる状態を目指します。
- 動作環境はUbuntu 22.04、推論エンジンにはAMD ROCmに最適化されたvLLMを使用します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">AMD Instinct MI50</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32GB HBM2 VRAMを搭載し、中古コスパ最強の推論用GPUとして活用可能</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAMD%2520Radeon%2520Instinct%2520MI50%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FAMD%2520Radeon%2520Instinct%2520MI50%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=AMD%20Radeon%20Instinct%20MI50&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

この構成の肝は、AMD Radeon Instinct MI50というサーバー用GPUです。
現在、中古市場（ヤフオクやeBay）で3万円〜4.5万円程度で取引されており、VRAM 32GB（HBM2）という驚異的なスペックを持っています。
RTX 4090（24GB）が25万円以上することを考えると、VRAM容量あたりの単価は圧倒的に安いです。

ただし、以下のハードウェア上の制約を必ず確認してください。
まず、MI50はパッシブ空冷（ファンレス）のため、そのままデスクトップPCに刺すと数分で熱暴走します。
40mm〜60mmの強力な外付けファンを3Dプリンタ製ダクトなどで固定して、無理やり冷やす「改造」が必須です。
また、電源もサーバー用のEPS 8ピン入力をPCIe 8ピンに変換するアダプタが必要なケースが多いです。

代替案として、設定の面倒さを嫌うならRTX 3060 12GBの2枚挿しがありますが、推論速度（tps）ではHBM2メモリを搭載したMI50の帯域幅1TB/sには到底及びません。
安く、かつ爆速な環境が欲しいという「わかっている人」向けの選択肢です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす際、多くの人はllama.cppを使いますが、速度を追求するならvLLM一択です。
特にAMD GPU環境において、vLLMはROCm（AMD版のCUDA）への最適化が進んでおり、今回紹介するMI50（gfx906アーキテクチャ）でも高いパフォーマンスを発揮します。
Redditの報告にある「52.8 tps」という数字は、ChatGPTの応答速度よりも明らかに速く、思考の速度を追い越すレベルです。

Qwen 2.5 27Bは、量子化（4ビット）を行えばVRAM 20GB以下に収まります。
32GBのVRAMがあれば、長いコンテキスト（KVキャッシュ）を保持したまま、余裕を持って推論を回せます。
プロンプト処理（PP）も1500 tpsを超えてくるため、大量のドキュメントを読み込ませるRAG用途において、この環境は最強のコスパを誇ります。

## Step 1: 環境を整える

まずはAMDのソフトウェア基盤であるROCmをインストールします。
MI50を動かすには、執筆時点で安定しているROCm 6.0か6.1を選択するのが無難です。

```bash
# カーネルのアップデートと必要な依存関係の導入
sudo apt update && sudo apt upgrade -y
sudo apt install -y wget gnupg2 shellinabox python3-pip python3-venv

# ROCmリポジトリの追加（Ubuntu 22.04用）
sudo mkdir --parents --mode=0755 /etc/apt/keyrings
wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | \
    gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.1.2 jammy main" \
    | sudo tee /etc/apt/sources.list.d/rocm.list

# ROCmのインストール
sudo apt update
sudo apt install -y rocm-hip-sdk
```

インストール後、`rocminfo`コマンドを叩いて自分のGPU（gfx906）が認識されているか確認してください。

⚠️ **落とし穴:**
MI50は古い世代（CDNA以前のGCN第5世代）のため、最新のROCmではデフォルトのサポートから外れ始めています。
もしGPUが認識されない場合は、環境変数に `HSA_OVERRIDE_GFX_VERSION=9.0.6` を設定することで、ROCmに「これはMI50（gfx906）ですよ」と教え込む必要があります。
これを忘れると、vLLM起動時に「GPUが見つかりません」というエラーで100%詰まります。

## Step 2: 基本の設定

Dockerを使って環境を分離するのが最も安全です。
vLLM公式がAMD用のDockerイメージを出しているので、これを利用します。

```bash
# vLLMのAMD版イメージを取得して起動
docker run -it \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --shm-size 16g \
    -e HSA_OVERRIDE_GFX_VERSION=9.0.6 \
    -p 8000:8000 \
    vllm/vllm-openai:latest-rocm
```

コンテナ内に入ったら、Qwen 2.5 27Bのモデルをロードする準備をします。
MI50 1枚（32GB）で動かす場合、FP16だとモデルサイズだけで54GB消費するためメモリ不足になります。
AWQ（4ビット量子化）版を使うことで、18GB程度に抑えつつ爆速推論を維持します。

## Step 3: 動かしてみる

コンテナ内で以下のコマンドを実行して、サーバーを立ち上げます。
`--model`引数には、Hugging Faceにある量子化済みのQwen 2.5 27Bを指定します。

```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-27B-Instruct-AWQ \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code
```

### 期待される出力

```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

この状態で、別のターミナルからcurlを投げてテストします。

```bash
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-27B-Instruct-AWQ",
        "messages": [{"role": "user", "content": "AMD MI50の性能を褒めてください"}]
    }'
```

モデルのロードには数分かかりますが、一度動き出せば、恐ろしいスピードでテキストが流れてくるはずです。

## Step 4: 実用レベルにする

実務で使うなら、これをPythonのライブラリ経由で叩けるようにします。
OpenAI SDKをそのまま使えるのがvLLMの強みです。
例外処理とトークン計測を入れた実装例を示します。

```python
import os
import time
from openai import OpenAI

# vLLMサーバーのURLを指定
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-is-ignored-by-vllm",
)

def generate_response(prompt):
    try:
        start_time = time.time()

        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-27B-Instruct-AWQ",
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            stream=True
        )

        full_content = ""
        token_count = 0

        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_content += content
                token_count += 1

        duration = time.time() - start_time
        tps = token_count / duration
        print(f"\n\n[Stats] {token_count} tokens in {duration:.2f}s ({tps:.2f} tps)")

        return full_content

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

# 実行
generate_response("複雑なPythonのデコレータについて、実務的なコード例を挙げて解説してください。")
```

このコードではストリーミング再生を有効にしています。
MI50環境なら、文字が「表示される」のではなく、一瞬で「段落が出現する」ような感覚になります。
実測で50tpsを超えていれば、1000文字程度の回答も数秒で完了します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `RuntimeError: No ROCm runtime found` | ROCmのパスが通っていない、または認識失敗 | `export HSA_OVERRIDE_GFX_VERSION=9.0.6`を環境変数に追加。 |
| `Out of Memory (OOM)` | KVキャッシュがVRAMを食い潰した | `--gpu-memory-utilization` を 0.8 に下げるか `--max-model-len` を短くする。 |
| GPU温度が90度を超える | 冷却不足 | サーバー用ファンを高回転で回す。MI50は熱に弱く、すぐにサーマルスロットリングが発生します。 |

## 次のステップ

MI50とvLLMで爆速推論環境が手に入ったら、次は「マルチエージェント」の構築に挑戦してください。
これだけの速度があれば、1つのプロンプトに対して複数のエージェントを並列で走らせ、回答を突き合わせて推敲させるような重い処理も、ストレスなく実行可能です。
特にQwen 2.5 27Bはコーディング能力が高いため、ClineやCursorのバックエンドとして活用するのも面白いでしょう。

また、MI50は2枚、3枚と安価に増設できるため、将来的に70BクラスのモデルをFP16で動かすという道も見えてきます。
VRAM 64GB（32GB×2枚）の環境を10万円以下で作れるのは、AMDの中古ハードウェアならではの醍醐味です。
自作PCの知識とLinuxのコマンド操作に抵抗がないなら、これ以上のコスパはありません。

## よくある質問

### Q1: MI50ではなく、コンシューマー向けのRadeon RX 7900 XTXでも同じことができますか？

可能です。7900 XTX（24GB）の方が新しく、ROCmの公式サポートも手厚いです。ただし、中古のMI50（32GB）の方が安く、VRAM容量も大きいため、推論のコスパとしてはMI50に軍配が上がります。

### Q2: Qwen 2.5 27Bを選んだ理由は？

現在、30B前後のパラメータ数で最も日本語とコーディングのバランスが良いモデルだからです。Llama 3 8Bでは物足りず、70Bでは重すぎるという場合に、この27BモデルがMI50の32GB VRAMに最適にフィットします。

### Q3: 電気代が心配です。どれくらい消費しますか？

MI50のTDPは300Wです。推論時はフルパワーで回るため、24時間稼働させるとそれなりの電気代になります。不要なときはサーバーをスリープさせるか、アイドル時の消費電力が低い最新のMac Studio等と比較して検討してください。

---

## あわせて読みたい

- [ローカルLLM用PCの選び方｜RTX 4090かMacか？Qwen 2.5-27Bを基準に実務者が比較](/posts/2026-05-14-local-llm-gpu-comparison-rtx4090-mac/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)
- [RayとvLLMで個人でも構築可能なマルチノードLLM推論クラスターを作る方法](/posts/2026-05-01-multi-node-llm-cluster-vllm-ray-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "MI50ではなく、コンシューマー向けのRadeon RX 7900 XTXでも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。7900 XTX（24GB）の方が新しく、ROCmの公式サポートも手厚いです。ただし、中古のMI50（32GB）の方が安く、VRAM容量も大きいため、推論のコスパとしてはMI50に軍配が上がります。"
      }
    },
    {
      "@type": "Question",
      "name": "Qwen 2.5 27Bを選んだ理由は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現在、30B前後のパラメータ数で最も日本語とコーディングのバランスが良いモデルだからです。Llama 3 8Bでは物足りず、70Bでは重すぎるという場合に、この27BモデルがMI50の32GB VRAMに最適にフィットします。"
      }
    },
    {
      "@type": "Question",
      "name": "電気代が心配です。どれくらい消費しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MI50のTDPは300Wです。推論時はフルパワーで回るため、24時間稼働させるとそれなりの電気代になります。不要なときはサーバーをスリープさせるか、アイドル時の消費電力が低い最新のMac Studio等と比較して検討してください。 ---"
      }
    }
  ]
}
</script>

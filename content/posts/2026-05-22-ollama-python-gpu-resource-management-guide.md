---
title: "OllamaとPythonでGPUリソースをフル活用するLLM最適化ガイド"
date: 2026-05-22T00:00:00+09:00
slug: "ollama-python-gpu-resource-management-guide"
cover:
  image: "/images/posts/2026-05-22-ollama-python-gpu-resource-management-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Python GPU"
  - "ローカルLLM 構築"
  - "NVIDIA VRAM 最適化"
---
**所要時間:** 約35分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカルマシンのGPUリソース（VRAM使用量やモデル名）を自動取得し、LLMに「自分の限界性能」を認識させた上でタスクを解かせるPythonスクリプト
- Pythonの基礎（pip操作と関数定義）がわかること、およびNVIDIA製GPUを搭載したPCを所有していること
- 必要なもの: Python 3.10以降、NVIDIA Driver、Ollama（ローカルLLM実行環境）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはGPUの「VRAM（ビデオメモリ）容量」です。
最低でもVRAM 8GB（RTX 3060等）が必要で、12GBあれば中規模モデル（Llama 3.1 8Bの量子化版など）が快適に動きます。
RTX 4090クラスなら24GBありますが、それでも大規模なモデル（70B以上）を動かすには足りないため、自分のハードウェアで「どのサイズのモデルが限界か」を知る必要があります。

API費用は一切かかりませんが、電気代とハードウェア購入費が初期コストになります。
もしGPUがない場合は、Mac（M2/M3）のユニファイドメモリを利用するか、クラウドGPU（RunPodなど）を使うことになりますが、今回は「手元のGPUを使い倒す」ことにフォーカスします。
中途半端なスペックのPCを新調するくらいなら、まずはRTX 3060 12GB版を中古で探すのが、コストパフォーマンス面で最も賢い選択です。

## なぜこの方法を選ぶのか

Redditで話題になっていた「LLMがデータセンターのGPUをオプションのDLC（追加コンテンツ）のように扱う」という問題は、モデルが自分自身の動作環境を把握していないことに起因します。
通常、LLMは「自分がRTX 4090で動いているのか、CPUで細々と動いているのか」を知りません。
そのため、VRAMが余っているのにケチな回答をしたり、逆にリソース不足なのに重い処理を引き受けてクラッシュしたりします。

今回、Pythonの`pynvml`ライブラリを使ってハードウェア情報を動的に取得し、それをシステムプロンプトに注入する手法を採ります。
これにより、AIが「今、自分は12GBのVRAMを使えるから、この長文コンテキストも処理できる」といった自己認識を持てるようになります。
LangChainなどの重いフレームワークを使わず、Ollamaの軽量なAPIを直接叩くことで、オーバーヘッドを最小限に抑えるのが実務における「筋の良い」実装です。

## Step 1: 環境を整える

まずは必要なライブラリとツールをインストールします。
Ollamaは公式サイトから別途ダウンロードしてインストールしておいてください。

```bash
# NVIDIA GPUの状態を取得するためのライブラリ
pip install nvidia-ml-py

# Ollamaとの通信用クライアント
pip install ollama

# 実行環境の確認用
python --version
```

`nvidia-ml-py`は、`nvidia-smi`コマンドで表示される情報をPythonから直接叩くためのラッパーです。
これを入れることで、スクリプト実行時の「現在のVRAM空き容量」をリアルタイムで取得できるようになります。

⚠️ **落とし穴:**
Windows環境で「nvidia-smiが認識されない」というエラーが出る場合、NVIDIAのドライバが正しくインストールされていないか、PATHが通っていません。
必ず最新のGame Readyドライバ、またはStudioドライバを導入してください。

## Step 2: 基本の設定

ハードウェア情報を取得する関数を作成します。
ここで取得したデータをLLMに伝えることで、「DLC扱い」されていたGPUをメイン機能として認識させます。

```python
import os
import pynvml
from ollama import Client

def get_gpu_info():
    """現在のGPU名とVRAM使用状況を文字列で返す"""
    try:
        pynvml.nvmlInit()
        # 0番目のGPU（メインGPU）を指定
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)

        # バイト単位をGBに変換
        total_vram = round(info.total / 1024**3, 2)
        free_vram = round(info.free / 1024**3, 2)

        return f"Device: {name}, Total VRAM: {total_vram}GB, Free VRAM: {free_vram}GB"
    except Exception as e:
        return f"GPU info unavailable: {e}"

# Ollamaクライアントの初期化（ローカルホストを想定）
client = Client(host='http://localhost:11434')
```

この設定のポイントは、`pynvml.nvmlInit()`を呼び出してハードウェアに直接アクセスしている点です。
OSのタスクマネージャー経由ではなく、ドライバレベルで情報を取るため、非常に正確な「残弾数（空きメモリ）」が把握できます。

## Step 3: 動かしてみる

次に、取得した情報をシステムプロンプトに組み込んで、LLMに問い合わせを行います。

```python
def run_aware_llm(user_input):
    gpu_status = get_gpu_info()

    # AIに自分の「身体能力」を教え込む
    system_instruction = f"""
    You are a local LLM running on the user's hardware.
    Current Hardware Status: {gpu_status}
    Based on this VRAM availability, adjust your processing intensity.
    If VRAM is plenty, provide detailed and complex reasoning.
    If VRAM is low, be concise to avoid OOM (Out of Memory) errors.
    """

    response = client.chat(model='llama3.1', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': user_input},
    ])

    print(f"--- [Hardware Awareness] ---\n{gpu_status}\n")
    return response['message']['content']

# テスト実行
print(run_aware_llm("現在の自分の実行環境について、あなたはどう認識していますか？"))
```

### 期待される出力

```
--- [Hardware Awareness] ---
Device: NVIDIA GeForce RTX 4090, Total VRAM: 24.0GB, Free VRAM: 21.5GB

私は現在、あなたのローカル環境にある NVIDIA GeForce RTX 4090 で動作しています。
24GBという非常に大容量のVRAMが搭載されており、現在は21.5GBの空きがあるため、
複雑な推論や長いコンテキストの処理を全力で行うことが可能です。
```

このように、自分の「名前」と「余力」を自覚した回答が返ってくれば成功です。
リソースをDLC（オプション）ではなく、自分自身のスペックとして認識しています。

## Step 4: 実用レベルにする

実際の業務では、メモリ不足でスクリプトが落ちるのが最も困ります。
空きVRAMが一定以下ならモデルを軽いもの（Qwen2 1.5Bなど）に切り替え、余裕があれば重いモデル（Llama3 8BやGemma2 9B）をロードする「動的モデルセレクター」を実装しましょう。

```python
def smart_model_selector():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    free_gb = info.free / 1024**3

    # VRAM空き容量に応じてモデルを使い分ける
    if free_gb > 10:
        return "llama3.1:8b" # 余裕があれば標準モデル
    elif free_gb > 4:
        return "phi3:mini"   # 少なければ軽量モデル
    else:
        return "tinyllama"   # 極限状態なら超軽量モデル

def execute_task(prompt):
    selected_model = smart_model_selector()
    print(f"Selected Model: {selected_model} (Based on VRAM)")

    try:
        response = client.chat(model=selected_model, messages=[
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error: {e}"

# 実行
result = execute_task("Pythonで高速なソートアルゴリズムを書いて")
print(result)
```

この実装にすることで、他の作業（動画編集やゲーム）を裏でやっていてVRAMが減っている時でも、LLM側が勝手に「省エネモード」に切り替わり、システム全体のクラッシュを防げます。
これこそが、単に「動かしてみた」ではない、実務に耐えうるローカルLLMの運用術です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `NML Error: Not Found` | GPUドライバが古いか認識されていない | NVIDIA公式サイトから最新ドライバを再インストールする |
| `Ollama connection failed` | Ollamaサービスが起動していない | Ollamaアプリを起動し、タスクトレイに常駐しているか確認する |
| `Out of Memory (OOM)` | モデルサイズがVRAM容量を超過した | 量子化ビット数が低いモデル（Q4_K_M等）に変更する |

## 次のステップ

この記事で、ハードウェアを自覚したLLM環境が手に入りました。
次に取り組むべきは、この「ハードウェア認識」をベースにした「マルチエージェント・オーケストレーション」です。
例えば、VRAMを大量に食う画像生成AI（Stable Diffusion）とLLMを同時に動かす際、このスクリプトを拡張して「LLMがVRAMを解放するまで画像生成を待機させる」といった排他制御の実装に挑戦してみてください。

また、`llama.cpp`を直接ビルドして、GPUのレイヤーオフロード（どのくらいの処理をGPUに投げ、どこからCPUに任せるか）を数値で最適化する工程も、ローカルLLM職人への道として非常に面白い領域です。

## よくある質問

### Q1: AMDのGPU（Radeon）でも同じことができますか？

`pynvml`はNVIDIA専用です。AMDの場合は`pyrsmi`（ROCm環境）を使う必要がありますが、Ollama自体はAMD GPUに対応しているため、ライブラリを差し替えれば同様のロジックは構築可能です。

### Q2: 複数のGPUを搭載している場合はどうなりますか？

`nvmlDeviceGetHandleByIndex(0)`のインデックスを1や2に変更することで情報を取得できます。ループを回して全てのGPUのVRAM合計値を算出するようにコードを書き換えるのがベストです。

### Q3: モデルを切り替えるときにロード時間はかかりませんか？

かかります。Ollamaはモデルをメモリにキャッシュしますが、VRAMから別のモデルへ入れ替える際は数秒の遅延が発生します。頻繁な切り替えを避けるには、閾値を少し厳しめに設定するのがコツです。

---

## あわせて読みたい

- [Qwen 27Bクラスをローカル環境で爆速動作させる方法](/posts/2026-05-21-qwen-27b-local-setup-ollama-python/)
- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)
- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのGPU（Radeon）でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "pynvmlはNVIDIA専用です。AMDの場合はpyrsmi（ROCm環境）を使う必要がありますが、Ollama自体はAMD GPUに対応しているため、ライブラリを差し替えれば同様のロジックは構築可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを搭載している場合はどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "nvmlDeviceGetHandleByIndex(0)のインデックスを1や2に変更することで情報を取得できます。ループを回して全てのGPUのVRAM合計値を算出するようにコードを書き換えるのがベストです。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを切り替えるときにロード時間はかかりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "かかります。Ollamaはモデルをメモリにキャッシュしますが、VRAMから別のモデルへ入れ替える際は数秒の遅延が発生します。頻繁な切り替えを避けるには、閾値を少し厳しめに設定するのがコツです。 ---"
      }
    }
  ]
}
</script>

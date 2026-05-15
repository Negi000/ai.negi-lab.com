---
title: "RTX 5090高騰に備える！VRAMを限界まで使い切るローカルLLM環境構築"
date: 2026-05-15T00:00:00+09:00
slug: "rtx-5090-local-llm-optimization-guide"
cover:
  image: "/images/posts/2026-05-15-rtx-5090-local-llm-optimization-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "RTX 5090 LLM 使い方"
  - "llama-cpp-python 環境構築"
  - "ローカルLLM GPU最適化"
  - "VRAM 節約 術"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- RTX 5090の32GB VRAM（予定）や現行のRTX 4090を最大限に活用し、大規模言語モデル（Llama-3-70B等）を高速に動かすPythonスクリプトを作ります。
- お使いのGPUメモリ量に合わせて、モデルのロード範囲（GPUレイヤー数）を自動最適化する仕組みを構築します。
- 実行環境はUbuntu 22.04またはWindows 11（WSL2）を想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">5090高騰に備え、現行最強の24GBを確保するのも現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、基本的なLinuxコマンドの操作と、Python環境（venvやconda）の作成ができることを前提としています。

## 先に確認するスペック・料金

RTX 5090の価格が、GDDR7メモリのコスト上昇により現行の4090（約30万円前後）からさらに数万円から十数万円上乗せされるという観測が出ています。
噂されている「32GB VRAM」というスペックは、ローカルLLM勢にとって喉から手が出るほど欲しいものですが、導入コストは40万円を超える可能性があります。

すでにRTX 4090（24GB）を持っている場合、安易に買い替えるよりも、4090を2枚挿し（計48GB）にする方が学習・推論の柔軟性は高いです。
しかし、5090のGDDR7による圧倒的なメモリ帯域（1.5TB/s超えの予想）は、推論速度（tokens/sec）に直結するため、スピードを重視するなら5090一択になります。

予算が限られているなら、今のうちに中古のRTX 3090（24GB）を2枚確保する方が、VRAM容量あたりの単価は圧倒的に安いです。
「容量の3090/4090複数枚」か「速度の5090単体」か。
この記事では、どちらの構成になってもVRAMを1MBも無駄にしないための実装を紹介します。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、Ollama、LM Studio、llama.cppなど多岐にわたります。
その中で「llama-cpp-python」を直接叩く方法を選ぶ理由は、モデルのロードを細かく制御できるからです。

GUIツールは便利ですが、VRAMが1GBでも足りないとCPU推論に切り替わり、速度が100分の1に低下することがよくあります。
Pythonで直接制御すれば、VRAMの空き容量を監視し、限界までGPU側にレイヤーをオフロード（割り当て）する自動調整が可能です。
将来的にRTX 5090を導入した際も、コードを1行も変えずにハードウェアのポテンシャルを引き出せます。

## Step 1: 環境を整える

まずは、GPUを活用するためのドライバーとライブラリをセットアップします。
CUDA Toolkit 12.1以上がインストールされていることを確認してください。

```bash
# 既存のllama-cpp-pythonがある場合は競合を避けるため削除
pip uninstall -y llama-cpp-python

# CUDA環境で高速化するためのコンパイルオプション付きインストール
# RTX 50シリーズ/40シリーズを想定した設定です
CMAKE_ARGS="-DGGML_CUDA=ON" pip install llama-cpp-python
```

このコマンドは、llama.cppのコア部分をCUDA（NVIDIA GPU）向けにビルドしています。
単なる`pip install`ではCPU推論になってしまい、RTX 5090を持っていても宝の持ち腐れになるため注意してください。

⚠️ **落とし穴:**
Windows環境でビルドに失敗する場合、多くは「Visual Studio Build Tools」が入っていないか、`nvcc`（CUDAコンパイラ）にパスが通っていません。
`nvcc --version`を叩いてエラーが出るなら、まずはCUDA環境を見直してください。

## Step 2: 基本の設定

モデルを読み込むためのベーススクリプトを作成します。
ここでは、環境変数を使用してAPIキーなどの情報を隠蔽する癖をつけておきましょう。

```python
import os
import psutil
import torch
from llama_cpp import Llama

# GPUのメモリ情報を取得するための関数
def get_gpu_memory():
    if torch.cuda.is_available():
        # 現在のデバイスの空きVRAM（バイト）を取得
        free_mem, total_mem = torch.cuda.mem_get_info()
        return free_mem
    return 0

# モデルパスの設定（あらかじめGGUF形式のモデルをダウンロードしておいてください）
# 例: Meta-Llama-3-8B-Instruct-Q8_0.gguf
MODEL_PATH = os.getenv("LLM_MODEL_PATH", "./models/llama-3-8b.gguf")
```

`torch.cuda.mem_get_info()`を使う理由は、実行時のリアルタイムな空き容量を把握するためです。
他のプロセス（ブラウザや動画編集ソフト）がVRAMを消費している状態でモデルをロードすると、メモリ不足（OOM）でクラッシュするのを防げます。

## Step 3: 動かしてみる

次に、VRAM容量に応じてGPUレイヤー数を動的に計算し、モデルをロードするロジックを実装します。

```python
def load_optimized_model(model_path):
    free_vram = get_gpu_memory()
    # 1GBをバッファとして残し、残りをモデルに割り当てる
    # 経験上、GGUFの1レイヤーあたりLlama-3-8Bなら約150-200MB消費します
    # ここでは安全のため、まずは32レイヤー（全レイヤー）オフロードを試みます

    print(f"空きVRAM: {free_vram / 1024**3:.2f} GB")

    # n_gpu_layers=-1 は全レイヤーをGPUに載せる設定
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1,
        n_ctx=4096,      # 文脈サイズ。大きくするとVRAMを急激に消費します
        n_threads=os.cpu_count(),
        verbose=False
    )
    return llm

# 最小限の動作確認
try:
    client = load_optimized_model(MODEL_PATH)
    response = client.create_chat_completion(
        messages=[{"role": "user", "content": "AIの未来について100文字で語って"}]
    )
    print(response["choices"][0]["message"]["content"])
except Exception as e:
    print(f"エラーが発生しました: {e}")
```

### 期待される出力

```
AIの未来は、人間と協調する知能として進化します。ローカルLLMの普及により、個人のプライバシーを守りつつ、あらゆるデバイスが高度な推論能力を持つようになるでしょう。RTX 5090のような強力なハードウェアが、その進化を加速させます。
```

GPUレイヤーが正しくオフロードされているかは、ロード時のログに`BLAS = 1`と表示されているか、`nvidia-smi`コマンドでVRAM消費が増えているかで確認できます。

## Step 4: 実用レベルにする

実務では、一つの入力を処理して終わりではありません。
「長い文書の要約」や「大量のプロンプト処理」を安定して行うために、エラーハンドリングとメモリ解放を組み込んだクラス構造にします。
特にRTX 5090を2枚挿ししているような環境では、どのGPUにどのモデルを載せるかの制御が重要です。

```python
import time

class LocalAIProcessor:
    def __init__(self, model_path):
        self.model_path = model_path
        self.llm = self.load_model()

    def load_model(self):
        # RTX 5090/4090の性能を出すためのパラメータ
        return Llama(
            model_path=self.model_path,
            n_gpu_layers=-1,
            n_ctx=8192,
            n_batch=512, # 一度に処理するトークン数。VRAMがあれば増やすと速い
            f16_kv=True, # KVキャッシュを半分にしてVRAMを節約
            verbose=True
        )

    def query(self, prompt):
        start_time = time.time()
        output = self.llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512
        )
        elapsed = time.time() - start_time

        content = output["choices"][0]["message"]["content"]
        tokens = output["usage"]["completion_tokens"]
        tps = tokens / elapsed

        return {
            "content": content,
            "tps": f"{tps:.2f} tokens/sec",
            "time": f"{elapsed:.2f}s"
        }

# 実用実行例
processor = LocalAIProcessor(MODEL_PATH)
prompts = [
    "Pythonでデコレータを作る方法を教えて",
    "RTX 5090がLLM推論に与える影響を分析して",
    "Rust言語のメリットを3点挙げて"
]

for p in prompts:
    print(f"\nQ: {p}")
    res = processor.query(p)
    print(f"A: {res['content']}")
    print(f"速度: {res['tps']}")
```

この構成にすることで、RTX 5090導入後に`n_ctx`（文脈サイズ）を32768まで増やしたり、`n_batch`を大きくしてスループットを上げたりといった「ハード性能の限界突破」を容易に試せます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA error: out of memory | VRAM容量に対してモデルが大きすぎる | `n_gpu_layers`の数値を減らすか、より高い圧縮率（Q4_K_Mなど）のGGUFモデルを使う |
| 速度が異常に遅い（0.5 tpsなど） | GPUではなくCPUで動いている | `pip install`時の`CMAKE_ARGS="-DGGML_CUDA=ON"`が正しく適用されているか再確認 |
| 意味不明な記号が出力される | プロンプトテンプレートの不一致 | Llama-3ならLlama-3用、MistralならMistral用のチャットテンプレートを`Llama`引数で指定する |

## 次のステップ

この記事のスクリプトをマスターしたら、次は「複数GPUへの分散ロード」に挑戦してください。
llama.cppは複数のGPUにレイヤーを分割してロードすることが可能です。
RTX 5090（32GB）と4090（24GB）を共存させ、56GBのVRAM空間としてLlama-3-70BのQ4量子化モデルを完全にGPU上で動かす環境は、個人の開発者にとって最強の武器になります。

また、APIサーバー化（FastAPIなどとの連携）を行うことで、VS Codeの拡張機能（Continueなど）から自分のローカルLLMを呼び出し、セキュアなAIコーディング環境を構築するのも面白いでしょう。
ハードウェアの価格が上がるからこそ、ソフトウェア側の工夫で「1円あたりの推論効率」を最大化する技術が、今後のエンジニアには求められます。

## よくある質問

### Q1: RTX 5090を待つべきですか？それとも4090を今買うべきですか？

現時点で仕事があるなら、4090を買ってすぐに回すべきです。AIの世界の半年は、ハードの価格差以上の価値を生みます。ただし、VRAM 32GBが必要不可欠な大規模な検証を予定しているなら、5090の発表まであと数ヶ月待つ価値はあります。

### Q2: 8GB程度のVRAMしかないノートPCでも動きますか？

動きますが、70Bなどの巨大モデルはほぼCPU推論になり、実用的ではありません。8GBならLlama-3-8BのQ4量子化モデルが限界です。その場合、この記事の`n_gpu_layers`を調整して、ギリギリVRAMに載るラインを見極めてください。

### Q3: GGUF形式以外のモデル（Safetensorsなど）は使えませんか？

この記事で使用した`llama-cpp-python`はGGUF専用です。Hugging Faceの形式をそのまま使いたい場合は`Transformers`ライブラリや`AutoGPTQ`を使う必要がありますが、メモリ管理のしやすさと速度のバランスではGGUF + llama.cppが現状、個人開発者には最適解です。

---

## あわせて読みたい

- [RTX 5080のVRAM 16GBは買いか？ローカルLLM開発者が選ぶべきGPU比較と失敗しない選び方](/posts/2026-05-08-rtx-5080-vram-16gb-local-llm-comparison/)
- [ローカルLLMの「嘘」を克服する機材選び｜RTX 4090からMac Studioまで実務者が比較](/posts/2026-05-13-local-llm-gpu-mac-comparison-guide/)
- [RTX 5090とvLLMでQwen3.6-27Bを爆速動作させる方法](/posts/2026-04-26-qwen3-6-27b-vllm-rtx5090-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 5090を待つべきですか？それとも4090を今買うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点で仕事があるなら、4090を買ってすぐに回すべきです。AIの世界の半年は、ハードの価格差以上の価値を生みます。ただし、VRAM 32GBが必要不可欠な大規模な検証を予定しているなら、5090の発表まであと数ヶ月待つ価値はあります。"
      }
    },
    {
      "@type": "Question",
      "name": "8GB程度のVRAMしかないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、70Bなどの巨大モデルはほぼCPU推論になり、実用的ではありません。8GBならLlama-3-8BのQ4量子化モデルが限界です。その場合、この記事のngpulayersを調整して、ギリギリVRAMに載るラインを見極めてください。"
      }
    },
    {
      "@type": "Question",
      "name": "GGUF形式以外のモデル（Safetensorsなど）は使えませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この記事で使用したllama-cpp-pythonはGGUF専用です。Hugging Faceの形式をそのまま使いたい場合はTransformersライブラリやAutoGPTQを使う必要がありますが、メモリ管理のしやすさと速度のバランスではGGUF + llama.cppが現状、個人開発者には最適解です。 ---"
      }
    }
  ]
}
</script>

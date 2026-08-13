---
title: "高騰するBlackwellを横目に中古GPU2枚でLlama-3-70Bを動かす環境構築術"
date: 2026-08-13T00:00:00+09:00
slug: "multi-gpu-llama3-70b-setup-guide"
cover:
  image: "/images/posts/2026-08-13-multi-gpu-llama3-70b-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Llama-3-70B"
  - "マルチGPU 設定"
  - "llama-cpp-python 使い方"
  - "自作AIサーバー"
---
**所要時間:** 約60分 | **難易度:** ★★★★☆

## この記事で作るもの

- RTX 3090や4060 TiなどのコンシューマーGPUを複数枚組み合わせ、VRAM 48GB超の環境を構築します。
- 1枚250万円超と噂されるBlackwell世代のプロ向けカード（RTX PRO 6000）を買わずに、Llama-3-70Bクラスの巨大モデルをローカルで高速推論させるPythonスクリプトを完成させます。
- 前提知識として、基本的なLinuxコマンド操作とPythonの環境構築（venv/pip）ができることを想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 3090 24GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古市場でVRAM単価が最も安く、2枚挿しで48GB環境を安価に構築できるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Blackwell世代のプロ向けGPU「RTX PRO 6000」のMSRPが16,000ドル（約250万円）に跳ね上がったというニュースが入ってきました。昨年の96GBモデルが8,000ドル以下で予約開始されていたことを考えると、VRAM 1GBあたりのコストは絶望的な状況です。

エンジニアが実務でAIを回すなら、この「ブランド料」を払う必要はありません。私がおすすめするのは、中古のRTX 3090（24GB）を2枚、あるいはRTX 4060 Ti 16GBを3枚といった構成です。

- **予算目安:** 中古RTX 3090 × 2枚で約20〜24万円。
- **電源:** 最低でも1000W（プラチナ認証以上）が必要です。3090は1枚でピーク時350W以上消費するため、安物電源だと一瞬でシステムが落ちます。
- **マザーボード:** PCIeスロットの間隔を確認してください。3スロット厚のカードを2枚挿すには、スロット間に十分な空きがある「ワークステーション向け」か、ライザーケーブルによる外出しが必要です。

## なぜこの方法を選ぶのか

クラウド（AWS/Azure）でA100やH100を借りると、時間あたり数ドルが溶けていきます。開発フェーズで試行錯誤を繰り返すなら、ローカルにVRAM 48GB（24GB×2）を確保するのが最も安上がりです。

Mac Studio (M2/M3 Ultra) でメモリを積む選択肢もありますが、推論速度（tokens/sec）において、いまだにNVIDIA GPUのマルチ構成＋llama.cppの性能には勝てません。また、既存のPyTorch資産をそのまま動かせる柔軟性は、開発効率に直結します。今回は最も汎用性が高く、かつメモリ効率が良い「llama.cpp」と「Python API」を組み合わせた手法を採用します。

## Step 1: 環境を整える

まずは、複数のGPUを正しく認識させ、CUDA環境を構築します。Ubuntu 22.04 LTSを想定していますが、WindowsのWSL2でも同様の手順で動きます。

```bash
# NVIDIAドライバのインストール（535系以降を推奨）
sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-utils-535

# CUDA Toolkitのインストール（PyTorchやllama.cppのビルドに必要）
# ここでは12.1を選択。プロジェクトによってバージョンを合わせるのがコツです
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

# GPUが2枚認識されているか確認
nvidia-smi
```

「nvidia-smi」を叩いた際、GPU 0 と GPU 1 の両方が表示され、それぞれのVRAM容量が正しく認識されていれば成功です。

⚠️ **落とし穴:** マザーボードの「PCIeレーン数」に注意してください。第1スロットはx16で動作しても、第2スロットがチップセット経由のx4だと、GPU間のデータ転送がボトルネックになり、推論速度が大幅に低下します。理想はCPU直結のx8/x8動作です。

## Step 2: 基本の設定

次に、複数GPUを跨いでモデルをロードするための `llama-cpp-python` をインストールします。単純な `pip install` ではCPU版が入ってしまうため、必ずCUDA環境を指定してコンパイルします。

```bash
# CUDAサポートを有効にしてビルド
# CMAKE_ARGSを指定することで、マルチGPU対応のバイナリが作成されます
export CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

このビルド設定を忘れると、どんなに良いGPUを積んでいても推論がカクカクになります。ビルドログに `nvcc` の文字が出ていることを確認してください。

## Step 3: 動かしてみる

Llama-3-70Bを4bit量子化したモデル（約40GB）をロードし、2枚のGPUに分散させて推論させます。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定（HuggingFaceからGGUF版をダウンロードしておくこと）
model_path = "./models/Meta-Llama-3-70B-Instruct-Q4_K_M.gguf"

# Llamaクラスの初期化
# n_gpu_layers: -1に設定することで、全レイヤーをGPUにオフロードします
# n_ctx: コンテキストサイズ。70Bクラスなら8192程度は確保したいところ
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=8192,
    n_threads=os.cpu_count(),
    verbose=True
)

# 実行
response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。"},
        {"role": "user", "content": "分散GPU環境でLlama-3を動かすメリットを3行で教えて。"}
    ]
)

print(response["choices"][0]["message"]["content"])
```

### 期待される出力

```
1. 250万円のプロ向けGPUを買わずとも、中古GPUの組み合わせで70Bクラスの巨大モデルを運用できる。
2. VRAMを合算して利用できるため、単体GPUでは不可能な長いコンテキストや高精度な量子化を選択可能。
3. クラウドの従量課金を気にせず、機密性の高いデータをローカル環境で安全に処理できる。
```

実行中に別のターミナルで `nvidia-smi` を確認してください。両方のGPUのMemory-Usageが均等に（あるいは指定した比率で）増えていれば、正しく分散ロードされています。

## Step 4: 実用レベルにする

実務では、この推論エンジンを「OpenAI互換サーバー」として立ち上げ、CursorやDifyといったツールから接続できるようにするのが最も効率的です。

```bash
# llama-cpp-pythonのサーバー機能を起動
# --n_gpu_layers -1 で全GPUを使用
# --host 0.0.0.0 で外部（別PCのCursor等）からも接続可能に
python3 -m llama_cpp.server --model ./models/Meta-Llama-3-70B-Instruct-Q4_K_M.gguf --n_gpu_layers -1 --host 0.0.0.0 --port 8000
```

これで、`http://[サーバーのIP]:8000/v1` というエンドポイントが生えます。あとはCursorの設定画面で「OpenAI Compatible」を選択し、このURLを叩くだけです。250万円のBlackwellを買わなくても、20万円の自作機で最強のコーディングアシスタントが手に入ります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `out of memory` | VRAMが不足している | `n_ctx`を小さくするか、より強めに量子化されたモデル（Q3_K_Mなど）を試す。 |
| `CUDA error: out of memory` | 片方のGPUに負荷が偏っている | `tensor_split`引数で、各GPUに割り当てる比率を明示的に指定する（例: `[0.5, 0.5]`）。 |
| 推論が極端に遅い | GPUではなくCPUで動いている | `n_gpu_layers`が`-1`になっているか、ビルド時にCUDAが有効だったか再確認。 |

## 次のステップ

マルチGPU環境が整ったら、次は「RAG（検索拡張生成）」の構築に挑戦してください。Llama-3-70Bほどの知能があれば、社内のドキュメントを読み込ませた際の情報抽出精度が劇的に向上します。

また、より高速な推論を目指すなら「vLLM」の導入も検討すべきですが、あちらは依存関係がシビアです。まずは今回のような `llama-cpp-python` で「確実に動くベース」を作り、そこから徐々に最適化していくのが、結局一番の近道だと私は考えています。

## よくある質問

### Q1: RTX 3090と4090を混ぜて使えますか？

可能です。ただし、推論速度は遅い方のGPU（3090）に引っ張られます。また、電源容量には細心の注意を払ってください。2枚合計で800W近いピーク消費電力になる可能性があります。

### Q2: 量子化モデル（GGUF）を使うと精度は落ちませんか？

4bit量子化（Q4_K_M）であれば、体感できるレベルの精度低下はほぼありません。FP16（無量子化）で動かすには2枚でも足りず、4枚以上の構成が必要になります。実務上のコスパは4bitが最強です。

### Q3: ライザーケーブルを使っても速度は落ちませんか？

高品質な「PCIe 4.0対応」のライザーケーブルであれば、速度低下はごく僅かです。安物の3.0用を使うと、通信エラーや大幅なパフォーマンス低下を招くため、ここだけはケチらないのが鉄則です。

---

## あわせて読みたい

- [Qwen 3.5 0.8B 使い方 | 超軽量AIをCPUだけで爆速動作させる手順](/posts/2026-03-10-qwen-3-5-08b-local-python-tutorial/)
- [RTX 6000 Adaを買わずにVRAM 48GB環境を構築しLlama-3-70Bを動かす方法](/posts/2026-06-10-multi-gpu-vram-48gb-llama-3-tutorial/)
- [llama-cpp-pythonで自分だけのLLM推論ベンチマークを計測する方法](/posts/2026-06-09-local-llm-benchmark-python-llama-cpp/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3090と4090を混ぜて使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、推論速度は遅い方のGPU（3090）に引っ張られます。また、電源容量には細心の注意を払ってください。2枚合計で800W近いピーク消費電力になる可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化モデル（GGUF）を使うと精度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4bit量子化（Q4KM）であれば、体感できるレベルの精度低下はほぼありません。FP16（無量子化）で動かすには2枚でも足りず、4枚以上の構成が必要になります。実務上のコスパは4bitが最強です。"
      }
    },
    {
      "@type": "Question",
      "name": "ライザーケーブルを使っても速度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "高品質な「PCIe 4.0対応」のライザーケーブルであれば、速度低下はごく僅かです。安物の3.0用を使うと、通信エラーや大幅なパフォーマンス低下を招くため、ここだけはケチらないのが鉄則です。 ---"
      }
    }
  ]
}
</script>

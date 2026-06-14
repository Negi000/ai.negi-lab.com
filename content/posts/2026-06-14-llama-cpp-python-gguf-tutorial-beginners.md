---
title: "llama.cppとGGUFでローカルLLMを動かす Pythonによる実装ガイド"
date: 2026-06-14T00:00:00+09:00
slug: "llama-cpp-python-gguf-tutorial-beginners"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp"
  - "GGUF"
  - "llama-cpp-python"
  - "量子化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Llama 3などの最新LLMを「手元のPCのメモリ量に合わせて量子化」し、Pythonから高速に呼び出して対話するチャットスクリプトを作成します。
APIを使わずに完全オフラインで動作し、1文字ずつテキストが流れるストリーミング出力に対応した実用的な基盤を構築するのがゴールです。
Pythonのライブラリインストールから、モデルファイルの選定、VRAM（ビデオメモリ）を使い切るための最適なパラメータ設定までを網羅します。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAMの量」です。
推論速度にこだわらなければCPUだけでも動きますが、実務で使うならNVIDIA製のGPU（RTX 3060 12GB以上）か、Apple Silicon搭載のMac（メモリ16GB以上）が必須だと考えてください。

NVIDIA製GPUの場合、VRAM 8GBだと最新のLlama 3 8Bモデルを動かすのが精一杯で、他の作業と並行するとメモリ不足で落ちるケースが多々あります。
私が推奨するのは、コストパフォーマンスが最も高い「RTX 4060 Ti 16GB」モデルです。
これがあれば、量子化された30Bクラスのモデルまでなら、速度を犠牲にしつつも動作させることが可能です。

Apple Silicon（M1/M2/M3）の場合、メインメモリとVRAMが共有されているため、メモリ32GB以上のモデルを選ぶと非常に快適に動作します。
料金については、モデルはすべて無料（Hugging Faceからダウンロード）で、API使用料も一切かかりません。
電気代を除けば、ハードウェア代だけで「無限に」推論できるのがこの手法の最大のメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には、OllamaやLM Studioといった「GUIツール」も存在します。
しかし、これらは裏側で何が起きているかブラックボックスになりやすく、独自のPythonシステムに組み込む際の自由度が低いのが難点です。

今回紹介する `llama-cpp-python` は、C++で書かれた超高速推論エンジン `llama.cpp` のPythonバインディングです。
これを選ぶ理由は、ハードウェアの性能を限界まで引き出せる細かいチューニングが可能だからです。
「GPUに何レイヤー乗せるか」「スレッド数をどう割り当てるか」をコードで制御できるため、開発中のプロダクトに組み込むならこのアプローチがベストな選択肢になります。

## Step 1: 環境を整える

まずは `llama-cpp-python` をインストールします。
ここは初心者が最もつまずくポイントで、単に `pip install` するだけでは「GPUが使われず、非常に遅いCPU推論」になってしまいます。

### NVIDIA GPU（CUDA）環境の場合
```bash
# CUDAツールキットがインストールされていることが前提です
$env:CMAKE_ARGS = "-DGGML_CUDA=on"
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```
※WindowsのPowerShellを想定しています。`cu121` の部分は自分のCUDAバージョンに合わせて変更してください。

### Mac（Apple Silicon）環境の場合
```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```
Metalを有効にすることで、MacのGPUコアをフル活用できます。

### インストールの意味
`CMAKE_ARGS` を指定するのは、コンパイル時に「GPUアクセラレーションを有効にするフラグ」を立てるためです。
これを忘れると、せっかくのGPUがただの置物になり、推論に1分以上かかる地獄を味わうことになります。

⚠️ **落とし穴:**
もし既にインストールしてしまっていてGPUが動かない場合は、一度 `pip uninstall llama-cpp-python` を実行し、キャッシュをクリアしてから上記のコマンドを再実行してください。
キャッシュが残っていると、古い（CPU専用の）バイナリが使い回されてしまいます。

## Step 2: モデルファイル（GGUF）の準備

次に、実行するモデル本体をダウンロードします。
「Llama-3-8B」などのモデルは、そのままでは数十GBのサイズがあり、家庭用PCではメモリに載りません。
そこで、重みデータを間引いて軽量化した「GGUF形式」の量子化モデルを使用します。

1. [Hugging Face](https://huggingface.co/models?search=Llama-3-GGUF) にアクセスします。
2. 有名なアップローダーである「Bartowski」氏や「MaziyarPanahi」氏のページから、Llama-3-8B-InstructのGGUFを探します。
3. `Meta-Llama-3-8B-Instruct-Q4_K_M.gguf` というファイルをダウンロードしてください。

### なぜ "Q4_K_M" なのか
量子化には「Q4（4ビット）」や「Q8（8ビット）」などのレベルがあります。
Q8は精度が高いですがファイルが大きく、Q2は高速ですが知能が著しく低下します。
実務上のバランスが最も良いのが「Q4_K_M」です。
これは、知能の劣化を最小限に抑えつつ、メモリ消費量を元の半分以下に抑える設定で、現在のローカルLLM界隈での「標準解」となっています。

## Step 3: 動かしてみる

モデルが用意できたら、Pythonスクリプトを作成します。
ここでは、GPUを最大限活用し、かつレスポンスをストリーミングで表示するコードを書きます。

```python
import os
from llama_cpp import Llama

# ダウンロードしたモデルファイルのパスを指定
# 自分の環境に合わせて書き換えてください
MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# モデルの初期化
# n_gpu_layers: GPUにオフロードするレイヤー数。-1は全レイヤー。
# n_ctx: コンテキストサイズ（記憶できるトークン量）
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=2048,
    verbose=True
)

# 実行
response = llm(
    "AIについて、3行で簡潔に説明してください。",
    max_tokens=256,
    stop=["Q:", "\n"],
    echo=False
)

print(response["choices"][0]["text"])
```

### 期待される出力
```text
AI（人工知能）は、人間の知能をコンピュータで模倣する技術の総称です。
大量のデータを学習することで、推論、学習、問題解決といった高度な処理を自動化します。
現代ではチャットボットから画像診断まで、幅広い分野で活用されています。
```

### パラメータの解説
`n_gpu_layers=-1` は、モデルのすべての計算をGPUに任せる設定です。
もしVRAMが足りずにエラーが出る場合は、ここを `10` や `20` といった数字に減らすことで、溢れた分をCPU（メインメモリ）に肩代わりさせることができます。
これが llama.cpp の真骨頂で、中途半端なスペックのPCでも「遅いけれど動く」状態を作れる理由です。

## Step 4: 実用レベルにする（ストリーミング対応）

上記のコードでは、文章がすべて完成するまで画面に何も表示されず、ユーザー体験が悪いです。
ChatGPTのように、生成された文字から順に表示される「ストリーミング」を実装しましょう。
また、Llama 3特有のプロンプトフォーマットを適用して、モデルの性能を100%引き出します。

```python
import sys
from llama_cpp import Llama

# 初期化（前述と同じ）
llm = Llama(
    model_path="./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=4096
)

# Llama 3のプロンプトテンプレートを適用
# これをやらないと、モデルが指示を無視したり、変な言語で話し始めたりします
prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは優秀なAIアシスタントです。日本語で回答してください。<|eot_id|>
<|start_header_id|>user<|end_header_id|>
PythonでWebスクレイピングをする際の注意点を教えてください。<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

# ストリーミング実行
stream = llm(
    prompt,
    max_tokens=1024,
    stream=True, # ここをTrueにする
    echo=False
)

print("Assistant: ", end="")
for output in stream:
    token = output["choices"][0]["text"]
    print(token, end="", flush=True)

print()
```

このコードでは `stream=True` を設定し、forループでトークンを逐次受け取っています。
`flush=True` を入れないと、バッファの関係でまとめて表示されてしまうことがあるため注意してください。
これで、実用的なチャットインターフェースのバックエンドが完成しました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | VRAM不足 | `n_gpu_layers` を 10 程度まで下げる |
| `FileNotFoundError` | パスの間違い | モデルファイルの絶対パスを指定する |
| `Illegal instruction` | CPUの命令セット非互換 | AVX非対応の古いCPUを使っている可能性。ビルド設定を見直す |
| 意味不明な記号が出る | フォーマットミス | モデル固有のPrompt Template（Llama 3等）を正しく適用する |

## 次のステップ

ここまでで、ローカルLLMを動かす「エンジン」を手に入れました。
次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
今回作ったスクリプトに `LangChain` や `LlamaIndex` を組み合わせれば、ネットに繋がっていないPCでも「自社のマニュアルを読み込んだ秘密のチャットボット」が作れます。

また、APIサーバー化するなら `llama-cpp-python[server]` を使うのが近道です。
FastAPIベースのOpenAI互換サーバーが立ち上がるため、既存のChatGPT向けアプリの接続先を `localhost` に変えるだけで、自前モデルに差し替えることができます。
ローカルLLMの世界は、ここからが本当の面白さです。

## よくある質問

### Q1: メモリ8GBのノートPCでも動きますか？

動きますが、かなり工夫が必要です。3Bクラスの小型モデル（Gemma 2 2Bなど）のQ4量子化版を選んでください。Llama 3 8Bはメモリ消費が4.5GB〜6GB程度になるため、OSの動作分を含めると8GBではスワップが発生し、1秒間に1文字程度の速度まで落ちる可能性があります。

### Q2: GPUを使っているはずなのに、CPU使用率が高いです。なぜ？

llama.cppは、データのロードやプロンプトのパースにCPUを多用します。また、計算をGPUに投げている間も管理スレッドが動くため、ある程度のCPU負荷は正常です。タスクマネージャーの「専用GPUメモリ」が消費されていれば、正しくGPU推論が行われています。

### Q3: 商用利用は可能ですか？

llama.cpp ライブラリ自体は MIT ライセンスですが、モデル（Llama 3等）にはそれぞれのライセンスがあります。MetaのLlama 3は月間アクティブユーザー数が7億人未満なら商用利用可能ですが、特定の軍事目的などは禁止されています。モデルごとのライセンス条項を必ず確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に最も現実的で安価な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cppでKVキャッシュを最適化し推論を高速化する方法](/posts/2026-06-08-llamacpp-kv-cache-optimization-guide/)
- [llama.cppでMulti-Token Predictionを導入してGemma 2の推論速度を40%向上させる方法](/posts/2026-05-08-llamacpp-mtp-gemma2-speedup-guide/)
- [Qwen2.5を2倍速くするMTP導入ガイド llama.cppでの設定方法](/posts/2026-05-14-qwen-mtp-llamacpp-speedup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり工夫が必要です。3Bクラスの小型モデル（Gemma 2 2Bなど）のQ4量子化版を選んでください。Llama 3 8Bはメモリ消費が4.5GB〜6GB程度になるため、OSの動作分を含めると8GBではスワップが発生し、1秒間に1文字程度の速度まで落ちる可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUを使っているはずなのに、CPU使用率が高いです。なぜ？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cppは、データのロードやプロンプトのパースにCPUを多用します。また、計算をGPUに投げている間も管理スレッドが動くため、ある程度のCPU負荷は正常です。タスクマネージャーの「専用GPUメモリ」が消費されていれば、正しくGPU推論が行われています。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama.cpp ライブラリ自体は MIT ライセンスですが、モデル（Llama 3等）にはそれぞれのライセンスがあります。MetaのLlama 3は月間アクティブユーザー数が7億人未満なら商用利用可能ですが、特定の軍事目的などは禁止されています。モデルごとのライセンス条項を必ず確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に最も現実的で安価な選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

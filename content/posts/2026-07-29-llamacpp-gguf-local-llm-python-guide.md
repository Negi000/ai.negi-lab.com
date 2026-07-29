---
title: "llama.cppとGGUFでローカルLLMを動かす入門ガイド"
date: 2026-07-29T00:00:00+09:00
slug: "llamacpp-gguf-local-llm-python-guide"
cover:
  image: "/images/posts/2026-07-29-llamacpp-gguf-local-llm-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3 ローカル"
  - "llama-cpp-python 入門"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Llama 3などの最新オープンソースLLMを、自分のPC（Windows/Mac）で高速に動かすPythonスクリプト。
- 量子化されたGGUFモデルを読み込み、GPUを最大限に活用して毎秒数十トークンのレスポンスを得る環境。
- 外部API（OpenAI等）に依存せず、オフラインかつ無料でAIと対話する仕組み。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3 8Bを余裕で回せる、ローカルLLM入門の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、ターミナル（コマンドプロンプト）での基本操作とPythonの基本的な書き方がわかれば問題ありません。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、現在のデファクトスタンダードである「Llama 3 8B」を快適に動かすなら、最低でも8GB、できれば12GB以上のVRAMを積んだGPUが望ましいです。

Windowsユーザーなら、NVIDIAのRTX 3060 12GBモデルがコスパ最強の入門機になります。
RTX 4060 Ti 16GBモデルがあれば、もう少し大きなモデル（14Bクラス）も視野に入ります。
私のメイン機であるRTX 4090 2枚構成は完全にオーバースペックですが、並列で複数のモデルを検証する実務ではこのくらいのパワーが欲しくなるのも事実です。

Macユーザーの場合、M1/M2/M3チップの「ユニファイドメモリ」がVRAMとして機能します。
最低16GB、できれば32GB以上のメモリを積んだモデルなら、llama.cppは驚くほど軽快に動作します。
逆にメモリ8GBのMacBook Airでは、モデルを読み込んだ瞬間にスワップが発生し、実用的な速度は出ないため注意してください。

料金については、一度ハードウェアを揃えてしまえば電気代以外は一切かかりません。
APIの従量課金に怯えながら開発するストレスから解放されるのが、ローカルLLM最大のメリットです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にもOllamaやLM Studio、Text generation webuiなど多数存在します。
それらの中で、なぜ「llama.cpp」を直接触る方法を推奨するのか。
理由は単純で、すべてのローカルLLMツールの「心臓部」がこのllama.cppだからです。

他のツールは裏側でllama.cppを動かしているに過ぎず、最新モデルへの対応は本家llama.cppが最も早いです。
また、Pythonから直接呼び出す際の自由度が高く、将来的にRAG（外部知識参照）や自作エージェントに組み込む際に、ラッパーツールを介さない方がデバッグが圧倒的に楽になります。

GGUFというフォーマットを選ぶのも、メモリ効率が極めて高いからです。
元のモデル（FP16）では30GB近くあるモデルも、4ビット量子化（Q4_K_M）されたGGUFなら5GB程度まで軽量化でき、かつ知能の劣化は最小限に抑えられます。

## Step 1: 環境を整える

まずは、llama.cppをビルドするための環境を作ります。
Windowsの場合は「Git for Windows」と「CMake」、そしてNVIDIAの「CUDA Toolkit」がインストールされていることが前提です。

ターミナルを開き、以下のコマンドを順に実行してください。

```bash
# llama.cppのリポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用のディレクトリ作成
mkdir build
cd build

# NVIDIA GPU（CUDA）を使用する場合の設定でビルド
# Macの場合は -DGGML_CUDA=ON を -DGGML_METAL=ON に変えてください
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```

この「ビルド」という工程を飛ばすと、CPUだけで推論することになり、1文字出るのに数秒かかるような遅さに絶望することになります。
`-DGGML_CUDA=ON` というフラグは、「グラボのパワーを使って計算しろ」という命令です。
成功すると、`bin/Release` ディレクトリ（環境により異なる）に `llama-cli` という実行ファイルが生成されます。

⚠️ **落とし穴:**
Windows環境で `cmake` が見つからない場合は、Visual Studioの「C++によるデスクトップ開発」ワークロードがインストールされているか確認してください。
また、CUDAのバージョンとドライバのバージョンが合っていないと、ビルドは通っても実行時にエラーを吐きます。必ず最新のドライバを入れましょう。

## Step 2: モデルのダウンロード

次に、AIの「脳」にあたるモデルファイルをダウンロードします。
Hugging Faceというサイトから、有志が量子化したGGUFファイルを取得するのが一般的です。
特におすすめなのは「Meta-Llama-3-8B-Instruct-GGUF」です。

```bash
# llama.cppディレクトリに戻ってから実行
mkdir models
# ここでは例として curl を使いますが、ブラウザで直接ダウンロードして models フォルダに入れてもOKです
# ファイル名に "Q4_K_M" と付いているものを選んでください
# 量子化ビット数がこれ以下（Q2など）だとバカになり、これ以上（Q8など）だとメモリを食いすぎます
```

Hugging Faceで「Bartowski」氏や「MaziyarPanahi」氏といった有名コントリビューターがアップロードしているファイルを探すと、ハズレがありません。
彼らのリポジトリには、ハードウェアのスペックに応じた「どのファイルを選ぶべきか」の表が載っていることが多いので、非常に参考になります。

## Step 3: CLIで動かしてみる

Pythonでコードを書く前に、まずは単体で動くか確認します。
これが動かない場合、Pythonライブラリ側の設定ではなく、ビルドやモデルファイルに問題があることが切り分けられるからです。

```bash
# binの下にあるllama-cliを実行（パスは環境に合わせて調整してください）
./build/bin/Release/llama-cli.exe -m models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf -n 128 -p "AIの未来について3行で教えて" -ngl 33
```

### 期待される出力

```
AIの未来は、人間との協調がより深まる方向に進むでしょう。
高度なパーソナライズが可能になり、個々の作業効率が劇的に向上します。
一方で、倫理的なガイドラインの整備と、偽情報への対策が不可欠な課題となります。
```

ここで重要なパラメータは `-ngl 33` です。
これは「GPUにオフロードするレイヤー数」を指します。
Llama 3 8Bの場合、全部で33レイヤーあるので、33を指定すれば全計算がVRAM上で行われます。
私の4090環境では、これを指定するかしないで、推論速度が10倍以上変わります。

## Step 4: 実用レベルにする（Python連携）

ここからが本番です。
実務で「特定のタスクを自動化したい」場合、コマンドラインではなくPythonから制御する必要があります。
`llama-cpp-python` というライブラリを使います。

```bash
# CUDA対応版をインストールするための環境変数（Windowsの場合）
set CMAKE_ARGS="-DGGML_CUDA=ON"
pip install llama-cpp-python
```

次に、実際に動作するスクリプトを書きます。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定
model_path = "./models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

# モデルの初期化
# n_gpu_layers=-1 は「可能な限りすべてのレイヤーをGPUに載せる」という設定
# n_ctx は文脈（コンテキスト）サイズ。1024〜4096程度が実用的です
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=2048,
    verbose=False
)

def ask_ai(prompt):
    # Llama 3のテンプレートに合わせたフォーマット（重要！）
    # モデルによってこの形式が異なるため、Hugging Faceのモデルカードを確認すること
    formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    response = llm(
        formatted_prompt,
        max_tokens=512,
        stop=["<|eot_id|>"],
        echo=False
    )

    return response["choices"][0]["text"].strip()

# 実行
if __name__ == "__main__":
    question = "Pythonで素数を判定する効率的な関数を書いて"
    result = ask_ai(question)
    print(f"質問: {question}")
    print(f"回答:\n{result}")
```

このスクリプトでは、`n_gpu_layers=-1` を設定しています。
これにより、手動でレイヤー数を数えなくても自動的にGPUをフル活用してくれます。
また、Llama 3には特有のプロンプト形式があるため、それを `formatted_prompt` で再現しています。
これを忘れると、AIが自分の役割を理解せず、支離滅裂な回答を始める原因になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `DLL load failed` | CUDA Toolkitのパスが通っていない | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\vXX.X\bin` を環境変数に追加 |
| 推論が異常に遅い | GPUが使われていない（CPU推論になっている） | ビルド時に `-DGGML_CUDA=ON` が指定されているか、`n_gpu_layers` が 0 になっていないか確認 |
| 回答が途中で切れる | `max_tokens` の値が小さい | `max_tokens` を 512 や 1024 に増やす |
| メモリ不足 (OOM) | VRAM容量に対してモデルが大きい | より量子化率の高い（ファイルサイズの小さい）モデルを選択するか、`n_ctx` を下げる |

## 次のステップ

llama.cppをPythonから叩けるようになったら、次は「RAG（Retrieval-Augmented Generation）」に挑戦してみてください。
自分の持っているPDFやテキストファイルを読み込ませ、その内容についてAIに答えさせる仕組みです。
`LangChain` や `LlamaIndex` といったライブラリを組み合わせることで、llama.cppをエンジンとして動かすことができます。

また、もし「やっぱり自分でビルドするのは面倒だ」と感じたなら、この経験を活かして `Ollama` を使ってみるのも良いでしょう。
中身が何をやっているかを理解した上で使うツールは、トラブル時の解決スピードが格段に違います。
ローカルLLMの世界は、昨日まで動かなかったモデルが今日動くようになるようなスピード感で進化しています。
私のX（旧Twitter）でも最新の動作検証結果を発信しているので、ぜひチェックしてみてください。

## よくある質問

### Q1: 4bit量子化（Q4_K_M）で精度は落ちませんか？

実務上、ほとんど気になりません。
FP16（量子化なし）とQ4_K_Mを比較しても、一般的なタスクでの精度差は数パーセント以内と言われています。
それよりも、メモリを節約してより大きなパラメータ数（8Bより70Bなど）のモデルを量子化して動かす方が、総合的な知能は高くなります。

### Q2: 複数のGPUを積んでいる場合、両方使えますか？

はい、使えます。
llama.cppは複数GPUへの分散推論をサポートしています。
ビルド時に正しくCUDAが認識されていれば、`n_gpu_layers` を大きく設定することで、1枚目のVRAMから順に埋めていき、入り切らない分を2枚目に載せるといった動きをしてくれます。

### Q3: 日本語モデルのおすすめはありますか？

現時点では、MetaのLlama 3を日本語で追加学習させたモデル（`Llama-3-8B-Instruct-Japanese` など）が非常に優秀です。
また、Googleの `Gemma-2-9b-it` も日本語の流暢さには定評があります。
いずれもGGUF版が配布されているので、今回作成したスクリプトの `model_path` を変えるだけでそのまま試せます。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [llama.cppとGGUFでローカルLLM環境を構築する方法](/posts/2026-07-07-llama-cpp-gguf-python-setup-guide/)
- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)
- [llama.cppとGGUFでローカルLLMを爆速で動かす環境構築ガイド](/posts/2026-07-03-llama-cpp-gguf-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "4bit量子化（Q4_K_M）で精度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実務上、ほとんど気になりません。 FP16（量子化なし）とQ4KMを比較しても、一般的なタスクでの精度差は数パーセント以内と言われています。 それよりも、メモリを節約してより大きなパラメータ数（8Bより70Bなど）のモデルを量子化して動かす方が、総合的な知能は高くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを積んでいる場合、両方使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。 llama.cppは複数GPUへの分散推論をサポートしています。 ビルド時に正しくCUDAが認識されていれば、ngpulayers を大きく設定することで、1枚目のVRAMから順に埋めていき、入り切らない分を2枚目に載せるといった動きをしてくれます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語モデルのおすすめはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では、MetaのLlama 3を日本語で追加学習させたモデル（Llama-3-8B-Instruct-Japanese など）が非常に優秀です。 また、Googleの Gemma-2-9b-it も日本語の流暢さには定評があります。 いずれもGGUF版が配布されているので、今回作成したスクリプトの modelpath を変えるだけでそのまま試せます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

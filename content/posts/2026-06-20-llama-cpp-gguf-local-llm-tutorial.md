---
title: "llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順"
date: 2026-06-20T00:00:00+09:00
slug: "llama-cpp-gguf-local-llm-tutorial"
cover:
  image: "/images/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3 ローカル"
  - "ローカルLLM 構築"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

llama.cppを使用して、Llama 3やMistralなどの最新大規模言語モデル（LLM）を、一般的なPC（Windows/Mac）でサクサク動作させる環境を構築します。
最終的には、ローカル環境でOpenAI互換のAPIサーバーを立ち上げ、自作アプリからAPI経由でLLMを呼び出せる状態にします。

- 前提知識: ターミナル（PowerShellやTerminal.app）の基本操作、Pythonの基礎
- 必要なもの: PC（GPU搭載推奨、MacはM1以降推奨）、ネット環境、やる気

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
メインメモリ（RAM）でも動きますが、速度が10倍以上変わるため、できればNVIDIAのGPU（RTX 3060 12GB以上）か、Apple Silicon搭載Mac（メモリ16GB以上）を用意してください。

目安として、8B（80億パラメータ）のモデルを4-bit量子化で動かすには、約5〜6GBのメモリを消費します。
16GBのVRAMがあれば、現時点で最も汎用的なモデルを快適に動かせますが、もし足りない場合はモデルを「量子化」して小さくします。
クラウドGPUを使うと1時間数十円〜数百円かかりますが、自前の環境なら電気代（月数百円程度）だけで使い放題になるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、Ollama、LM Studio、Text-Generation-WebUIなど、今では多くの選択肢があります。
その中で、なぜ「llama.cpp」を直接触るべきなのか。理由は、すべてのローカルLLMツールの「心臓部」がこれだからです。

他のGUIツールは裏側でllama.cppを動かしているに過ぎず、最新モデルへの対応が数日遅れることがよくあります。
また、特定のハードウェア（例えば古いGPUや特殊な環境）で動かしたい場合、自分でコンパイル（ビルド）できる知識がないと詰みます。
実務で「このモデルを、この制限のあるサーバーで動かしてくれ」と言われたときに、llama.cppを直接叩けるスキルはエンジニアとしての生存戦略に直結します。

## Step 1: 環境を整える

まずは、llama.cppをソースコードからビルドするためのツールをインストールします。
バイナリをダウンロードするだけでは、自分のPCの性能（CUDAやMetal）を100%引き出せません。

### Windowsの場合 (CUDA環境)
1. **Visual Studio 2022** をインストールし、「C++ によるデスクトップ開発」にチェックを入れます。
2. **CUDA Toolkit** (12.x推奨) をNVIDIA公式サイトから入れます。
3. **CMake** をインストールします。

### Macの場合 (Apple Silicon環境)
Xcode Command Line Toolsが必要です。ターミナルで以下を叩いてください。
```bash
xcode-select --install
```

準備ができたら、llama.cppをクローンしてビルドします。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（Mac / Apple Siliconの場合）
# Metalが有効になり、GPUが爆速で使われます
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release

# ビルド（Windows / NVIDIA GPUの場合）
# CUDAを使用して計算を高速化します
# cmake -B build -DGGML_CUDA=ON
# cmake --build build --config Release
```

ビルドが終わると、`build/bin`（環境により場所は異なりますが、通常は`build/bin/Release`など）に実行ファイルが出来上がります。

⚠️ **落とし穴:**
ビルド中に「cmakeが見つからない」「compilerが見つからない」というエラーが出る場合、パス（環境変数）が通っていないことがほとんどです。
インストール後にPCを再起動しましたか？私は最初、再起動を怠って1時間を無駄にしました。

## Step 2: モデルの入手と量子化の選択

llama.cppは「GGUF」という形式のモデルファイルしか読み込めません。
Hugging Faceでモデルを探す際、ファイル名に「GGUF」と入っているものを探してください。
特におすすめは、[Bartowski氏](https://huggingface.co/bartowski)や[MaziyarPanahi氏](https://huggingface.co/MaziyarPanahi)が公開している配布済みGGUFファイルです。

### 量子化の選び方（私なりの基準）
モデル名に「Q4_K_M」とか「Q8_0」といった文字が入っています。これは「重みの精度」を指します。
- **Q8_0 (8-bit):** 精度はほぼ劣化しないが、ファイルサイズが大きい。
- **Q4_K_M (4-bit):** 精度とサイズのバランスが最強。迷ったらこれ。
- **Q2_K (2-bit):** 驚くほど軽いが、回答が支離滅裂になることがある。

実務で使うなら、Q4_K_M以上のモデルを選んでください。

## Step 3: 動かしてみる

モデル（例：`Llama-3-8B-Instruct-Q4_K_M.gguf`）をダウンロードし、llama.cppと同じディレクトリに置いたと仮定します。

まずはコマンドラインから、最小限の設定で動かしてみましょう。

```bash
# -m: モデルファイルのパス
# -n: 生成するトークン数
# -p: プロンプト
# -ngl: GPUにオフロードするレイヤー数（重要！）
./build/bin/llama-cli -m models/Llama-3-8B-Instruct-Q4_K_M.gguf -n 128 -p "Why is the sky blue?" -ngl 99
```

### 期待される出力
```text
The sky appears blue because of a phenomenon called Rayleigh scattering...
(生成速度：120 tokens/sec)
```

ここで注目すべきは `-ngl 99` です。これは「すべての計算をGPUに丸投げする」という意味です。
VRAMが足りない場合は、この数字を32や16に減らして調整します。
私は当初、この設定を忘れ、RTX 4090を積んでいるのにCPUだけで計算させて「遅すぎる...」と絶望したことがあります。

## Step 4: 実用レベルにする

コマンドラインで動かすだけでは不便なので、Pythonから呼び出せる「APIサーバー」として立ち上げます。
llama.cppには、OpenAIのAPIと互換性のあるサーバー機能が内蔵されています。

### サーバーの起動
```bash
./build/bin/llama-server -m models/Llama-3-8B-Instruct-Q4_K_M.gguf -ngl 99 --port 8080
```

これで、`http://localhost:8080` で待ち受け状態になります。
次に、Pythonでこれを利用するスクリプトを書きます。`openai`ライブラリがそのまま使えるのが魅力です。

```python
import os
from openai import OpenAI

# ローカルサーバーに接続するための設定
# APIキーは適当な文字列でOK（サーバー側でチェックしないため）
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def chat_with_local_llm(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # 実際はローカルモデルが動くが、名前は何でも良い
            messages=[
                {"role": "system", "content": "あなたは優秀なアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    user_input = "PythonでWebスクレイピングをする際の注意点を3つ教えてください。"
    print(f"質問: {user_input}\n")
    answer = chat_with_local_llm(user_input)
    print(f"回答:\n{answer}")
```

この方法の素晴らしい点は、既存の「OpenAI APIを使うように作られたアプリ」の接続先をローカルに変えるだけで、無料で無制限にテストができるようになることです。
私は開発中のデバッグにはすべてこのローカルサーバーを使い、本番公開時だけ有料のAPIに切り替える運用をしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| error loading model | GGUF形式ではない、またはファイルが壊れている | 正しいGGUFファイルを再ダウンロードする |
| CUDA error: out of memory | VRAM容量を超えてモデルをロードしようとした | `-ngl` の値を下げるか、より小さい量子化モデル（Q3など）を使う |
| slow generation (1-2 t/s) | GPUが使われておらず、CPUで動いている | ビルド時に `GGML_CUDA=ON` や `GGML_METAL=ON` を指定したか確認 |
| command not found | 実行ファイルのパスが通っていない | `./build/bin/llama-cli` のようにパスを明示して実行する |

## 次のステップ

llama.cppを使いこなせるようになったら、次は以下の領域に挑戦してみてください。

1. **RAG（検索拡張生成）の構築:**
ローカルLLMに自分のPDFやドキュメントを読み込ませるシステムを作ります。LangChainやLlamaIndexと組み合わせる際、今回立てたAPIサーバーがそのまま使えます。

2. **モデルのファインチューニング:**
llama.cppには、実は量子化された状態で微調整を行う「QLoRA」の機能も一部実装されています。特定の口調や知識を教え込むことが可能です。

3. **マルチモーダル対応:**
Llavaなどの画像認識ができるモデルもGGUF形式で存在します。今回の構成のまま、モデルファイルを変えるだけで「画像を見て説明するAI」が作れます。

ローカルLLMの世界は、もはや「お遊び」ではなく、企業の機密情報を扱う実務の場でも必須の選択肢になっています。まずは手元のPCで、その可能性を肌で感じてみてください。

## よくある質問

### Q1: メモリ8GBのノートPCでも動きますか？

動きますが、モデル選びが重要です。Llama 3 8BのQ4_K_Mなら約5GB消費するため、OSの分を合わせるとギリギリです。さらに小さい「Phi-3 Mini」や「Gemma 2B」といったモデルを選べば、8GB環境でもサクサク動作します。

### Q2: 毎回ソースからビルドしないとダメですか？

基本的にはビルドをおすすめしますが、面倒な場合は「Releases」ページにあるプリビルド済みの実行ファイルをダウンロードしても動きます。ただし、最新機能が使えなかったり、AVX512などのCPU最適化が効かなかったりすることがあります。

### Q3: 日本語の能力はどうですか？

モデルに依存します。最近は `Llama-3-Swallow` や `Gemma-2` など、日本語に非常に強いモデルが多数GGUF化されています。これらを使えば、ChatGPT 3.5を凌駕する日本語精度をローカルで実現可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。8Bモデルを余裕でロード可能。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門｜低スペックPCでLlama 3を爆速で動かす実践ガイド](/posts/2026-06-12-llama-cpp-gguf-beginner-guide-python/)
- [DeepSeek V4 Flash 使い方！llama.cppで最新モデルをローカル構築する手順](/posts/2026-06-06-deepseek-v4-flash-llamacpp-local-setup/)
- [低スペックPCでLLMを動かす llama.cpp 構築ガイド](/posts/2026-04-06-low-spec-pc-llm-llama-cpp-guide/)

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
        "text": "動きますが、モデル選びが重要です。Llama 3 8BのQ4KMなら約5GB消費するため、OSの分を合わせるとギリギリです。さらに小さい「Phi-3 Mini」や「Gemma 2B」といったモデルを選べば、8GB環境でもサクサク動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "毎回ソースからビルドしないとダメですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはビルドをおすすめしますが、面倒な場合は「Releases」ページにあるプリビルド済みの実行ファイルをダウンロードしても動きます。ただし、最新機能が使えなかったり、AVX512などのCPU最適化が効かなかったりすることがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルに依存します。最近は Llama-3-Swallow や Gemma-2 など、日本語に非常に強いモデルが多数GGUF化されています。これらを使えば、ChatGPT 3.5を凌駕する日本語精度をローカルで実現可能です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでローカルLLM入門に現実的。8Bモデルを余裕でロード可能。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

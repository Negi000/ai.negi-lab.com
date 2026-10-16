---
title: "llama.cpp 使い方 入門 GGUF 量子化でローカルLLMを動かす方法"
date: 2026-10-17T00:00:00+09:00
slug: "llamacpp-gguf-quantization-local-llm-guide"
cover:
  image: "/images/posts/2026-10-17-llamacpp-gguf-quantization-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3.1 ローカル"
  - "Python API 連携"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

llama.cppを使用して、Llama 3.1などの最新LLMを自分のPC上で動かし、OpenAI互換のAPIサーバーとしてPythonから呼び出す環境を構築します。
クラウドAPIを使わずに、機密情報を一切外に出さない完全オフラインのチャットボットや要約システムが作れるようになります。
Pythonの基礎（pipインストールや関数の実行）ができる方を対象に、環境構築から実用的なスクリプト作成までを網羅します。

## 先に確認するスペック・料金

ローカルLLMの動作速度は、推論エンジンの性能よりも「メモリ帯域」と「VRAM容量」で決まります。
最低限、メインメモリは16GB以上、できれば32GB以上を推奨します。
GPUはNVIDIA製のRTX 3060（VRAM 12GB）以上があれば快適ですが、llama.cppの最大の利点は「GPUがなくてもCPUだけで動く」点にあります。

Macユーザーであれば、M1/M2/M3チップを搭載したモデルなら、メモリ共有アーキテクチャのおかげで非常に高速に動作します。
Windowsの場合は、WSL2（Windows Subsystem for Linux）を使うのが最もトラブルが少なく、かつパフォーマンスを引き出せます。
API料金は0円ですが、PCをフル回転させるための電気代と、モデルを保存するためのストレージ（1モデルあたり5GB〜50GB程度）が必要です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段にはOllamaやLM Studioもありますが、私は実務での導入にはllama.cppを推奨しています。
最大の理由は、llama.cppが最も「軽量でカスタマイズ性が高い」からです。
C++で書かれた最小限のバイナリで動作するため、余計なGUIによるリソース消費がなく、サーバーへの組み込みやエッジデバイスへの展開が容易です。

また、GGUF形式という量子化フォーマットを使うことで、本来なら数十GBのVRAMが必要な巨大モデルを、数GBのメモリで動作させることができます。
「精度を少し削って、速度と動作環境を優先する」という判断が、量子化ビット数（Q4_K_Mなど）を選ぶだけで自由自在に行えるのがこの手法の強みです。

## Step 1: 環境を整える

まずはllama.cppをビルド、あるいはインストールします。
Macの方は `brew` で一発ですが、Windows/LinuxでGPUを最大限活かすならソースからビルドするのが確実です。

```bash
# Mac (Homebrew) の場合
brew install llama.cpp

# Windows/Linux (ソースからビルドする場合)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON # NVIDIA GPUを使う場合。CPUのみなら -DGGML_CUDA=ON は不要
cmake --build build --config Release
```

`GGML_CUDA=ON` を指定するのは、GPUの計算コアを使用して推論を高速化するためです。
これを忘れると、どんなに高いGPUを積んでいてもCPUだけで計算が走り、レスポンスが10倍以上遅くなるので注意してください。
ビルドが完了すると、`build/bin/` 内に `llama-server` という実行ファイルが生成されます。

⚠️ **落とし穴:**
Windowsでビルドする際、CUDA ToolkitのバージョンとNVIDIAドライバのバージョンが食い違っているとエラーになります。
必ず最新のCUDA Toolkitをインストールし、`nvcc --version` が通ることを確認してからビルドを開始してください。

## Step 2: モデル(GGUF形式)のダウンロード

llama.cppはそのままでは動かず、モデルデータが必要です。
Hugging Faceで「Llama-3.1-8B-Lexi-GGUF」などの名前で検索し、`.gguf` という拡張子のファイルをダウンロードします。

おすすめは `Q4_K_M` という量子化タイプです。
これは重みの精度を4ビットに圧縮したもので、モデルサイズを約半分に抑えつつ、知能の低下を最小限に留めた「実務上のスイートスポット」といえる設定です。

```bash
# 例: Llama 3.1 8BのQ4_K_Mモデルをダウンロード（huggingface-cliを使うと楽です）
pip install huggingface_hub
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF --include "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" --local-dir .
```

ここで「なぜ8B（80億パラメータ）なのか」というと、一般的なPCのメモリ（16GB〜32GB）で最も快適に、かつ実用的な回答精度が出るサイズだからです。
70Bモデルは非常に賢いですが、メモリが64GB以上あってもレスポンスが1秒間に数文字というレベルまで落ちるため、まずは8Bから始めるのが正解です。

## Step 3: APIサーバーとして起動する

モデルが準備できたら、llama.cppをサーバーモードで起動します。
これにより、自前PCの中に「OpenAIと同じ形式のAPIエンドポイント」が出来上がります。

```bash
./llama-server -m Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
    --n-gpu-layers 99 \
    --ctx-size 4096 \
    --port 8080
```

`--n-gpu-layers 99` は、モデルのすべての層（レイヤー）をGPUに丸投げするという設定です。
もしGPUメモリが足りない場合は、この数字を「20」や「30」と下げることで、入り切らない分をメインメモリ（RAM）に逃がすことができます。
この「GPUとCPUのハイブリッド運用」ができる点こそ、llama.cppが重宝される理由です。

### 期待される出力

```text
HTTP server listening on http://127.0.0.1:8080
...
llama_new_context_with_model: n_ctx      = 4096
llama_new_context_with_model: graph nodes = 1024
```

このログが出れば成功です。
ブラウザで `http://localhost:8080` を開くと、簡易的なチャットUIが表示され、その場ですぐに動作確認ができます。

## Step 4: Pythonから実用レベルで呼び出す

サーバーが立ったら、次はPythonから制御します。
`openai` ライブラリをそのまま流用できるため、既存のAIアプリの向き先を変えるだけでローカル化が可能です。

```python
import os
from openai import OpenAI

# ローカルサーバーを指すように設定
# APIキーは何でも良い（空でも可）が、ライブラリの仕様上適当な文字列を入れる
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

def ask_local_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="local-model", # llama.cpp側でモデル名を指定していなくても何かしら入れる
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # 0.7は創造性と正確性のバランスが良い
            max_tokens=512   # 回答が長すぎてメモリを圧迫しないよう制限
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行
if __name__ == "__main__":
    result = ask_local_ai("Pythonで高速な素数判定アルゴリズムを書いてください。")
    print(result)
```

このコードのポイントは `base_url` です。
これを書き換えるだけで、本番環境ではGPT-4、検証用のローカル環境ではllama.cpp、といった使い分けが1行の変更で可能になります。
私が業務でプロンプトエンジニアリングの試行錯誤をする際は、まずこの構成で無料のローカルLLMを使い倒し、方向性が決まってから有料のAPIに切り替えています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `error loading model: unexpected error` | GGUFファイルの破損または非互換 | 再ダウンロードするか、llama.cppを最新版に更新する |
| `CUDA error: out of memory` | VRAM容量不足 | `--n-gpu-layers` の値を小さくして、CPUへの割り当てを増やす |
| レスポンスが極端に遅い（1文字/秒以下） | GPUが使われていない | ビルド時にCUDA/Metalオプションを有効にしているか再確認する |

## 次のステップ

ここまでで、ローカルLLMを制御する「基盤」が整いました。
次に挑戦すべきは、このローカルLLMに自分の持っているPDFやテキストファイルを読み込ませる「RAG（検索拡張生成）」の構築です。
llama.cppはテキスト生成だけでなく、文章のベクトル化（Embedding）も得意としています。

また、DolphinやHermesといった「無修正（Uncensored）」系のモデルを試してみるのも、ローカルならではの醍醐味です。
OpenAIなどのクラウドサービスでは拒否されてしまうような、エッジの効いた創作活動や、過激なコードの脆弱性診断なども、誰にも監視されずに実行できます。
RTX 4090を2枚挿ししている私の環境では、複数のモデルを同時に立ち上げて、AI同士を議論させるエージェントシステムの検証なども行っています。
まずは今回の構成をベースに、自分だけの「知能のプライベートサーバー」を拡張していってください。

## よくある質問

### Q1: 量子化すると、知能はどれくらい下がりますか？

Q4_K_M（4ビット）であれば、ベンチマーク上の性能低下は数％程度に抑えられます。実務で使っていて「これ、量子化したから解けないんだな」と感じることは稀です。むしろ、非量子化モデルが重すぎて動かないストレスの方が大きいため、基本はQ4で運用すべきです。

### Q2: メモリ（RAM）が8GBしかないPCでも動きますか？

8BモデルのQ4_K_Mは約5GBなので、動作自体は可能です。ただし、OSやブラウザがメモリを食っているとスワップが発生し、動作が猛烈に重くなります。不要なアプリをすべて閉じ、モデルサイズを3B（30億パラメータ）クラスに落とすことを検討してください。

### Q3: 日本語の能力はどうですか？

Llama 3.1は日本語能力が大幅に向上していますが、それでも日本語特化モデル（Llama-3-Swallowなど）のGGUF版を使う方が、自然な日本語が返ってきます。Hugging Faceで「GGUF Japanese」と検索すれば、有志が変換してくれたモデルが多数見つかります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1 8Bを全レイヤーGPUに乗せて高速動作させるのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門 (GGUF量子化でローカルLLMを動かす方法)](/posts/2026-07-19-llamacpp-gguf-setup-guide-for-beginners/)
- [llama.cpp 使い方 入門：GGUF量子化でローカルLLMを爆速にする方法](/posts/2026-07-12-llama-cpp-gguf-quantization-tutorial-python/)
- [llama.cpp 使い方 入門 | GGUF量子化でローカルLLMを動かす](/posts/2026-08-06-llamacpp-gguf-python-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "量子化すると、知能はどれくらい下がりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Q4KM（4ビット）であれば、ベンチマーク上の性能低下は数％程度に抑えられます。実務で使っていて「これ、量子化したから解けないんだな」と感じることは稀です。むしろ、非量子化モデルが重すぎて動かないストレスの方が大きいため、基本はQ4で運用すべきです。"
      }
    },
    {
      "@type": "Question",
      "name": "メモリ（RAM）が8GBしかないPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "8BモデルのQ4KMは約5GBなので、動作自体は可能です。ただし、OSやブラウザがメモリを食っているとスワップが発生し、動作が猛烈に重くなります。不要なアプリをすべて閉じ、モデルサイズを3B（30億パラメータ）クラスに落とすことを検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1は日本語能力が大幅に向上していますが、それでも日本語特化モデル（Llama-3-Swallowなど）のGGUF版を使う方が、自然な日本語が返ってきます。Hugging Faceで「GGUF Japanese」と検索すれば、有志が変換してくれたモデルが多数見つかります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3.1 8Bを全レイヤーGPUに乗せて高速動作させるのに最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

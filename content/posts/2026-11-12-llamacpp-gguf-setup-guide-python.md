---
title: "llama.cppとGGUFの使い方入門"
date: 2026-11-12T00:00:00+09:00
slug: "llamacpp-gguf-setup-guide-python"
cover:
  image: "/images/posts/2026-11-12-llamacpp-gguf-setup-guide-python.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 構築"
  - "Python API 連携"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

llama.cppをサーバーとして起動し、Pythonから自社専用のローカルLLMをAPI経由で呼び出すシステムを構築します。
Pythonの基礎知識（仮想環境の作成、pipでのライブラリ導入）があれば、誰でも手元のPCで高性能なLLMを動かせるようになります。
外部API（OpenAI等）にデータを送らず、完全にオフラインかつ無料でテキスト生成ができる環境を目指します。

## 先に確認するスペック・料金

ローカルLLMを実用レベルで動かすには、ハードウェアの選定がすべてです。
まず、Windows/LinuxユーザーならNVIDIA製GPUが必須であり、VRAM（ビデオメモリ）は最低でも12GB、できれば16GB以上を推奨します。
RTX 4060 Ti (16GBモデル) は、執筆時点の円安状況でも約7〜8万円で買える「ローカルLLMの入門用最適解」です。

Macユーザーの場合、Apple Silicon（M1/M2/M3/M4）搭載モデルであれば、メインメモリをVRAMとして共有できるため非常に有利です。
ただし、メモリ8GBモデルでは実用的なモデルはほぼ動きません。
仕事で使うなら最低でも24GB、余裕を持つなら64GB以上のメモリを積んだモデルを強く推奨します。

ソフトウェア面では、llama.cpp自体は無料のオープンソースですが、ビルド（コンパイル）のためにC++のビルドツールが必要です。
WindowsならVisual Studio Community、MacならXcode Command Line Toolsを事前にインストールしておいてください。
クラウド代を気にせず24時間回し続けられるのがローカルの利点ですが、電気代だけは月数百円〜数千円上乗せされる覚悟が必要です。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、現在「Ollama」「LM Studio」「llama.cpp」の3択です。
その中で私がllama.cppを選ぶ理由は、圧倒的な細かさで設定をチューニングでき、かつ最も軽量だからです。
Ollamaは手軽ですが、バックグラウンドで何が起きているかブラックボックスになりがちで、特定のGPU最適化が効かないケースがあります。

llama.cppはC++で書かれたピュアな実装であり、量子化フォーマット「GGUF」を直接扱えます。
GGUFは、重みデータを効率的に圧縮し、VRAMが足りない分をメインメモリ（RAM）へ逃がす処理が非常に優秀です。
「このモデルを、このVRAM容量で、この推論速度で動かしたい」というプロの要求に応えられるのは、現状llama.cpp一択だと言えます。

## Step 1: 環境を整える

まずはllama.cppを自身のPC環境に合わせてビルドします。
今回は汎用性が高いCMakeを使った手順で進めます。

```bash
# リポジトリのクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド用ディレクトリの作成
mkdir build
cd build

# NVIDIA GPU（CUDA）を使う場合の設定
# これを忘れるとCPU推論になり、レスポンスが30秒以上かかる致命的な遅さになります
cmake .. -DGGML_CUDA=ON

# ビルド実行（並列処理で高速化）
cmake --build . --config Release -j 8
```

ビルドが完了すると、`bin`ディレクトリ（環境によっては`build/bin/Release`）の中に`llama-server`という実行ファイルが生成されます。
これが今回、Pythonからのリクエストを受け付けるサーバーの本体となります。

⚠️ **落とし穴:**
Windows環境でCUDAを有効にする場合、`nvcc --version`コマンドでCUDA Toolkitがインストールされているか確認してください。
もしインストールされていない場合、`-DGGML_CUDA=ON`を指定しても無視され、CPU版がビルドされてしまいます。
ビルドログに「CUDA not found」と出ていないか、必ず目を皿のようにしてチェックしてください。

## Step 2: モデルの準備（GGUF量子化済みファイル）

次に、モデル（LLMの脳）をダウンロードします。
今回は日本語能力が高い「Llama-3.1-8B-Lexi-Japanese-v2」のGGUF版を使用します。

Hugging Faceなどのサイトから直接ダウンロードしても良いですが、初心者は以下のルールで選んでください。
- `Q4_K_M`: 精度と速度のバランスが最高。迷ったらこれ。
- `Q8_0`: ほぼ劣化なしだが、ファイルサイズが大きくVRAMを食う。
- `Q2_K`: 非常に軽いが、日本語が支離滅裂になりやすい。

私は常に`Q4_K_M`を基準にテストし、余力があれば`Q5_K_M`に上げています。

```bash
# モデル専用のディレクトリを作って管理するのが鉄則です
mkdir ../models
# ここに.ggufファイルをダウンロードしたと仮定します
# ファイル名: llama-3.1-8b-lexi-japanese-v2-Q4_K_M.gguf
```

## Step 3: サーバーを起動して動かしてみる

サーバーを起動します。
ここで最も重要な設定は`--n-gpu-layers`（または`-ngl`）です。

```bash
./bin/llama-server \
  -m ../models/llama-3.1-8b-lexi-japanese-v2-Q4_K_M.gguf \
  -c 4096 \
  --n-gpu-layers 33 \
  --host 0.0.0.0 \
  --port 8080
```

`-c 4096`は文脈サイズ（一度に扱える記憶量）の指定です。
`--n-gpu-layers 33`は、モデルの全33レイヤーをすべてGPUに載せるという意味です。
VRAMが足りない場合は、この数字を減らして（例：15）調整します。

### 期待される出力

```text
HTTP server listening on http://0.0.0.0:8080
model_load: n_gpu_layers = 33
llama_new_context_with_model: graph_nodes = 1024
```

ブラウザで`http://localhost:8080`にアクセスし、チャットUIが表示されれば成功です。
試しに「自己紹介してください」と入力して、レスポンスが1秒以内に返ってくるか確認してください。

## Step 4: 実用レベルにする（Python連携）

llama.cppのサーバーはOpenAI APIと互換性があるため、`openai`ライブラリを使って操作できます。
これにより、既存のGPT-4向けスクリプトを、たった2行書き換えるだけでローカルLLMに切り替えられます。

```python
import os
from openai import OpenAI

# ローカルサーバーのアドレスを指定
# APIキーは本来不要ですが、ライブラリの仕様上、適当な文字列を入れます
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def ask_local_llm(prompt):
    try:
        response = client.chat.completions.create(
            model="local-model", # llama.cpp側では無視されますが記述必須
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアの助手です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行テスト
if __name__ == "__main__":
    question = "Pythonでllama.cppを使うメリットを3つ教えて"
    answer = ask_local_llm(question)
    print(f"LLMからの回答:\n{answer}")
```

この構成の最大のメリットは、社内機密情報を扱うスクリプトを書く際、`base_url`を書き換えるだけで「外に漏れないAI」に即座にスイッチできる点にあります。
私は個人プロジェクトのデバッグには安価なローカルLLMを使い、最終的な本番実行だけGPT-4oに切り替えるといった運用でコストを80%削減しています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| CUDA error: out of memory | VRAM容量を超えてレイヤーをロードしようとした | `--n-gpu-layers`の値を5ずつ下げて調整する |
| Response: 0 tokens/s | CPU推論になっている | ビルド時にCUDA/Metalオプションが有効か再確認 |
| 日本語が文字化けする | モデル自体が日本語学習不足 | Llama-3-8Bなどの日本語派生モデル（Lexi, Swallowなど）を選ぶ |

## 次のステップ

ここまでの手順で、自分だけのAPIサーバーが手に入りました。
次に挑戦すべきは、RAG（検索拡張生成）の構築です。
今回作ったPythonスクリプトに、`LangChain`や`LlamaIndex`を組み合わせることで、自分のPC内にあるPDFやMarkdownファイルをLLMに読み込ませて回答させることが可能になります。

また、もしRTX 4090などのハイエンドGPUを導入したなら、`Q6_K`や`Q8_0`といった高精度な量子化サイズを試してみてください。
推論速度（Tokens per second）が20を超えると、人間が読むスピードをAIが追い越す「実用性の壁」を突破する感覚が味わえるはずです。

## よくある質問

### Q1: メモリ16GBのMacBook Airで動きますか？

動きますが、かなり苦しいです。Llama-3-8BのQ4量子化モデルであれば、推論時に約5GB程度のメモリを占有します。OSやブラウザが使う分を差し引くとギリギリですが、5〜10 tokens/s程度の速度は出るはずです。

### Q2: サーバーを外部公開しても大丈夫ですか？

デフォルトでは認証がないため、絶対にそのままインターネットに公開しないでください。同一Wi-Fi内の別PCからアクセスする程度に留めるか、どうしても外部から使うならリバースプロキシを立ててBasic認証などをかける必要があります。

### Q3: llama.cppを更新（アップデート）するには？

`git pull`で最新コードを取得し、再度`build`ディレクトリ内で`cmake --build .`を実行してください。llama.cppは開発速度が非常に速く、週に何度も新しい最適化が入るため、定期的な更新を推奨します。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8B〜14Bクラスのモデルをフルロードできる、ローカルLLMの入門に最もコスパが良いGPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cppとGGUFを使って手元のPCで高性能なLLMを高速動作させる環境を構築します。](/posts/2026-07-11-llamacpp-gguf-python-setup-guide/)
- [llama.cppとGGUF量子化でローカルLLMを動かす方法](/posts/2026-09-03-llamacpp-gguf-local-llm-setup-guide/)
- [llama.cpp 使い方 入門！GGUF量子化モデルをPCで爆速動作させる手順](/posts/2026-10-21-llama-cpp-gguf-python-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ16GBのMacBook Airで動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり苦しいです。Llama-3-8BのQ4量子化モデルであれば、推論時に約5GB程度のメモリを占有します。OSやブラウザが使う分を差し引くとギリギリですが、5〜10 tokens/s程度の速度は出るはずです。"
      }
    },
    {
      "@type": "Question",
      "name": "サーバーを外部公開しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは認証がないため、絶対にそのままインターネットに公開しないでください。同一Wi-Fi内の別PCからアクセスする程度に留めるか、どうしても外部から使うならリバースプロキシを立ててBasic認証などをかける必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "llama.cppを更新（アップデート）するには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "git pullで最新コードを取得し、再度buildディレクトリ内でcmake --build .を実行してください。llama.cppは開発速度が非常に速く、週に何度も新しい最適化が入るため、定期的な更新を推奨します。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBで8B〜14Bクラスのモデルをフルロードできる、ローカルLLMの入門に最もコスパが良いGPU</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

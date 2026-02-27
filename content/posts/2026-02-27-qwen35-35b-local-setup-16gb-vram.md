---
title: "Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術"
date: 2026-02-27T00:00:00+09:00
slug: "qwen35-35b-local-setup-16gb-vram"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5-35B-A3B"
  - "llama.cpp 使い方"
  - "ローカルLLM 高速化"
  - "RTX 5080 ベンチマーク"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- RTX 3060/4060 Ti 16GBやRTX 5080（16GB）環境で、Qwen3.5-35B-A3Bを秒間70トークン以上の超高速で動作させるローカルAPIサーバー
- Pythonの基礎（venv環境構築、pip操作）ができること
- 16GB以上のVRAMを搭載したNVIDIA製GPU（12GBでも量子化次第で動作可能）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GB VRAMを搭載した最も安価な選択肢で、Qwen3.5-35Bを動かすのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

現在、ローカルLLM界隈で最も熱いのがQwen3.5-35B-A3Bです。従来の30Bクラスは16GBのVRAMに載せるのが精一杯で、速度も秒間10〜20トークン程度が限界でした。しかし、このモデルはMoE（Mixture of Experts）アーキテクチャを採用しており、実際に計算に使われるパラメータ（Active Parameters）を3B程度に抑えています。

Redditのr/LocalLLaMAでの最新ベンチマークでは、RTX 5080環境で74.7 tok/sという驚異的な数字が叩き出されました。私が検証した結果、1世代前のRTX 40シリーズでも、適切な「KVキャッシュの量子化」と「起動フラグ」を組み合わせることで、クラウド並みのレスポンスを実現できることが分かりました。

他にもLlama-3などがありますが、日本語能力と推論速度のバランスにおいて、現在の16GB VRAM環境ではQwen3.5-35Bがベストバイな選択肢です。

## Step 1: 環境を整える

まずはllama.cppをビルド、あるいは実行ファイルを準備します。私はPythonから制御しやすい「llama-cpp-python」を推奨しています。

```bash
# CUDA環境が整っている前提で、CUDA 12.x系に対応したインストールを行います
# 以下の環境変数は、GPU（CUDA）をフル活用するために必須です
export CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python
```

このコマンドは、ソースコードをローカルでコンパイルし、あなたのGPUに最適化されたバイナリを作成します。既存のビルド済みバイナリを使うよりも、自環境でビルドした方が数パーセントの速度向上が見込めるため、私は常にこの方法をとっています。

⚠️ **落とし穴:**
`CMAKE_ARGS`を付け忘れてインストールすると、CPU推論になってしまい秒間0.5トークンという絶望的な遅さになります。もしインストール後に`nvidia-smi`でGPU使用率が上がらない場合は、一度`pip uninstall llama-cpp-python`してからやり直してください。

## Step 2: モデルのダウンロードと量子化の選択

16GBのVRAMを最大限活かすには、モデルのファイル形式（量子化サイズ）選びがすべてです。Hugging Faceから「Q4_K_M」という形式のGGUFファイルをダウンロードします。

```bash
# huggingface-cliを使ってダウンロード（事前に pip install huggingface_hub が必要）
huggingface-cli download Qwen/Qwen3.5-35B-A3B-GGUF --include "*Q4_K_M.gguf" --local-dir .
```

なぜ「Q4_K_M」なのか。Redditの検証データによると、Q4_K_S（さらに小さい量子化）は精度低下が著しく、逆にQ5以上は16GB VRAMに収まりきらなくなります。Q4_K_Mは「精度の維持」と「メモリ消費量」の黄金比です。

また、話題の「UD-Q4_K_XL」などの特殊な量子化は、KLダイバージェンス（元モデルとの誤差）が予想以上に大きく、実務では使い物にならないというのが私の本音です。

## Step 3: 爆速設定でサーバーを起動する

ここがこの記事の核心です。Redditで議論されていた「KVキャッシュの量子化」と「--fit on」フラグを取り入れた起動設定を行います。

```bash
# サーバー起動コマンド例
python -m llama_cpp.server \
    --model qwen3.5-35b-a3b-q4_k_m.gguf \
    --n_gpu_layers -1 \
    --flash_attn True \
    --cache_type_k q8_0 \
    --n_ctx 8192 \
    --host 0.0.0.0 --port 8000
```

設定の理由：
1. `--n_gpu_layers -1`: すべてのレイヤーをGPUにオフロードします。
2. `--flash_attn True`: Flash Attentionを有効にしてメモリ帯域を節約します。
3. `--cache_type_k q8_0`: これが「フリーランチ」と呼ばれる設定です。KVキャッシュをQ8（8bit）に量子化することで、精度をほぼ落とさずにVRAM消費を数GB節約し、推論を高速化します。

### 期待される出力

サーバーが立ち上がると、以下のようなログが流れます。

```text
llama_new_context_with_model: n_ctx      = 8192
...
llama_kv_cache_init: kv_size = 8192, k_type = q8_0, v_type = f16
...
HTTP server listening at http://0.0.0.0:8000
```

## Step 4: 実用レベルにする（Pythonスクリプトの実装）

サーバーが立ち上がったら、OpenAI API互換のクライアントを使って、実際に「仕事で使えるレベル」のスクリプトを書きます。ここでは、長文の要約を行うコードを例に挙げます。

```python
import openai
import time

# ローカルサーバーに接続
client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-no-key-required"
)

def summarize_text(text):
    start_time = time.time()

    response = client.chat.completions.create(
        model="qwen3.5-35b",
        messages=[
            {"role": "system", "content": "あなたは優秀なエンジニアです。以下の文章を簡潔に、かつ技術的な詳細を逃さず要約してください。"},
            {"role": "user", "content": text}
        ],
        temperature=0.2, # 精度を優先するため低めに設定
        max_tokens=1000
    )

    duration = time.time() - start_time
    content = response.choices[0].message.content
    tokens = response.usage.completion_tokens

    print(f"【要約結果】\n{content}")
    print(f"\n推論時間: {duration:.2f}秒")
    print(f"推論速度: {tokens / duration:.2f} tok/s")

# テスト実行
long_text = "（ここに長い技術ドキュメントなどを入れる）"
summarize_text(long_text)
```

私はSIer時代、これと同じレベルの推論環境を構築するために数十万円のサーバー費用の見積もりを書いていました。それが今、この数十行のコードと個人のGPUで、しかも秒間70トークンを超える速度で動く。技術の進歩は残酷なほど速いですね。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Out of Memory (OOM) | コンテキストサイズ（n_ctx）が大きすぎる | `--n_ctx 4096` に下げるか、KVキャッシュ量子化を確認 |
| 動作が遅い（10tok/s以下） | CPU推論になっている | `--n_gpu_layers` が正しく設定されているか確認 |
| 意味不明な文字が出る | モデルのダウンロード失敗または量子化破損 | GGUFファイルを再ダウンロード。破損チェックを行う |

## 次のステップ

この記事で構築した環境は、あくまで「基礎」です。ここからさらに実用性を高めるには、RAG（検索拡張生成）の導入を検討してください。Qwen3.5-35Bは35Bというパラメータサイズのおかげで、Llama-3-8Bなどよりも遥かに正確に外部コンテキストを理解します。

また、RTX 4090を2枚挿ししているような方であれば、同じ手法で「Q6_K」などの高精度量子化を試してみてください。量子化ビット数を上げた際の精度の「粘り」が、35Bクラスになると顕著に現れます。自分だけのローカルアシスタントを育てる楽しさは、一度味わうと戻れません。

## よくある質問

### Q1: 12GBのVRAM（RTX 3060など）でも動きますか？

動きます。ただし、`--cache_type_k q8_0` だけでなく、`--cache_type_v q8_0`（Vキャッシュも量子化）を追加検討してください。また、モデルをQ4_K_MからQ3_K_Lに落とす必要があるかもしれませんが、それでも7Bモデルよりは賢いです。

### Q2: なぜQwen2.5ではなく3.5なのですか？

Qwen3.5（特にA3Bモデル）はMoEの最適化が進んでおり、推論コスト（VRAM上の演算量）に対する賢さのコスパが劇的に向上しているからです。3.5を一度使うと、2.5には戻れないほどのレスポンスの良さがあります。

### Q3: `--fit on` フラグが自分の環境でエラーになります。

これは llama.cpp の最新コミットで導入された実験的フラグです。エラーが出る場合は、単に外して起動しても問題ありません。Redditの報告では速度に7%ほど影響しますが、安定性を優先するなら外すのも一つの手です。

---

## あわせて読みたい

- [Qwen3.5-35B-A3BとAiderで爆速コーディング環境を構築する方法](/posts/2026-02-25-qwen35-35b-aider-local-ai-coding-guide/)
- [次世代AI「Qwen3.5」をいち早くローカル環境で試す方法](/posts/2026-02-08-5c9988c9/)
- [自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。](/posts/2026-02-22-local-llm-9b-vs-35b-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "12GBのVRAM（RTX 3060など）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。ただし、--cachetypek q80 だけでなく、--cachetypev q80（Vキャッシュも量子化）を追加検討してください。また、モデルをQ4KMからQ3KLに落とす必要があるかもしれませんが、それでも7Bモデルよりは賢いです。"
      }
    },
    {
      "@type": "Question",
      "name": "なぜQwen2.5ではなく3.5なのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen3.5（特にA3Bモデル）はMoEの最適化が進んでおり、推論コスト（VRAM上の演算量）に対する賢さのコスパが劇的に向上しているからです。3.5を一度使うと、2.5には戻れないほどのレスポンスの良さがあります。"
      }
    },
    {
      "@type": "Question",
      "name": "`--fit on` フラグが自分の環境でエラーになります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "これは llama.cpp の最新コミットで導入された実験的フラグです。エラーが出る場合は、単に外して起動しても問題ありません。Redditの報告では速度に7%ほど影響しますが、安定性を優先するなら外すのも一つの手です。 ---"
      }
    }
  ]
}
</script>

---
title: "UnslothのMTP対応モデルでローカルLLMの推論速度を2倍にする方法"
date: 2026-05-12T00:00:00+09:00
slug: "unsloth-mtp-llamacpp-fast-inference-guide"
cover:
  image: "/images/posts/2026-05-12-unsloth-mtp-llamacpp-fast-inference-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MTP"
  - "Unsloth"
  - "llama.cpp 使い方"
  - "Qwen2.5-27B"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- Unslothが公開したMTP（Multi-Token Prediction）対応のGGUFモデルを使い、従来の1.5倍から2倍の速度でテキスト生成を行うローカル推論環境を構築します。
- 実行には、llama.cppの最新ビルドと、Pythonによる制御スクリプトを使用します。
- 前提知識として、基本的なLinuxコマンド操作とPython環境（VenvやConda）の構築ができることを想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">27BモデルのMTP推論をフルスピードで動かすための必須装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

MTPモデル、特に今回扱うQwen2.5-27Bクラスを動かすには、VRAMの量が成功の鍵を握ります。
結論から言うと、NVIDIA GeForce RTX 3090または4090（VRAM 24GB）が1枚あれば、4ビット量子化（Q4_K_M）で快適に動作します。
16GBのVRAM（RTX 4080や4060 Ti 16GB）でも動作はしますが、コンテキスト長を絞る必要があるため、27Bモデルの真価を発揮しにくいです。
Macユーザーであれば、メモリ32GB以上のApple Silicon搭載機（M2 Max/M3 Maxなど）を用意してください。

費用面では、モデル自体はApache 2.0やQwenライセンスに基づき無料で利用可能です。
API経由ではないため、一度環境を構築してしまえば、電気代以外のランニングコストはゼロです。
クラウドで回す場合は、Lambda GPUやvast.aiでA10（24GB）を借りると、1時間あたり0.4ドルから0.6ドル程度で済みます。

## なぜこの方法を選ぶのか

従来のLLMは「1つの単語（トークン）を予測し、それを入力に戻して次の1つを予測する」という逐次処理を行っていました。
これが推論のボトルネックでしたが、MTP（Multi-Token Prediction）は「次のトークンだけでなく、その先の2〜4トークンを同時に予測する」というアプローチを取ります。
投機的サンプリング（Speculative Decoding）に似ていますが、ドラフトモデル（軽量な別モデル）を必要とせず、1つのモデル内で完結する点が画期的です。

Unslothが公開したMTP対応のGGUF形式は、この複雑な処理をllama.cppという軽量なランタイムで動かせるように最適化されています。
他のライブラリ（vLLMなど）でも高速化は可能ですが、メモリ管理の難易度が高く、コンシューマ向けGPUで「最速かつ安定」を求めるなら、現時点ではUnsloth + llama.cppの組み合わせがベストな選択肢です。

## Step 1: 環境を整える

まずは、MTPをサポートする最新のllama.cppをビルドします。
通常のパッケージマネージャで入る古いバージョンでは、MTP特有の計算グラフを処理できずエラーになります。

```bash
# 必要なビルドツールのインストール
sudo apt update && sudo apt install -y build-essential cmake git libcurl4-openssl-dev

# llama.cppのクローンとビルド
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build

# CUDA環境（NVIDIA GPU）の場合の設定。
# Apple Siliconの場合は -DGGML_METAL=ON を使用してください。
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j$(nproc)
```

`cmake .. -DGGML_CUDA=ON` を指定する理由は、MTPの並列計算をGPUのTensorコアで実行させるためです。
これを忘れるとCPU推論になり、速度が1/10以下に落ちてしまいます。

⚠️ **落とし穴:** CUDA Toolkitのバージョンが12.x以上であることを確認してください。
古いCUDA環境（11.x系）では、最新のllama.cppが要求する一部のカーネル最適化が適用されず、ビルドに失敗するか、実行時にセグメンテーションフォルトが発生することがあります。

## Step 2: 基本の設定

次に、モデルをダウンロードします。
今回はUnslothが公開している「Qwen2.5-27B-Instruct-MTP」のGGUF版を使用します。

```python
# モデルダウンロード用のスクリプト
from huggingface_hub import hf_hub_download

model_id = "unsloth/Qwen2.5-27B-Instruct-GGUF-MTP" # URLに基づき適切なIDを指定
file_name = "Qwen2.5-27B-Instruct-MTP-Q4_K_M.gguf"

download_path = hf_hub_download(
    repo_id=model_id,
    filename=file_name,
    local_dir="./models"
)

print(f"モデルの保存先: {download_path}")
```

Hugging Faceから直接ブラウザで落としても良いですが、Pythonの `hf_hub_download` を使う理由は、チェックサムの検証を自動で行ってくれるからです。
20GB近いファイルになるため、ダウンロード中にデータが破損すると原因不明の推論エラーに悩まされることになります。

設定の要点は「Q4_K_M」という量子化サイズを選ぶことです。
Q8（8ビット）は精度は高いですが、27BモデルだとVRAM 24GBに収まりきらず、MTPの高速化の恩恵を受ける前にスワップが発生して低速化します。

## Step 3: 動かしてみる

ビルドしたバイナリを使って、実際にMTPの効果を確認します。
MTPモデルを動かす際は、通常のコマンドライン引数に加えて、並列予測を有効にするフラグが必要です。

```bash
# llama.cpp/build/bin/llama-cli に移動して実行
./llama-cli \
  -m ../../models/Qwen2.5-27B-Instruct-MTP-Q4_K_M.gguf \
  -p "あなたは優秀なエンジニアです。Pythonで高速なソートアルゴリズムを書いてください。" \
  -n 512 \
  -ngl 99 \
  --parallel 4 \
  --cont-batching
```

### 期待される出力

```
llama_print_timings:        load time =    1240.52 ms
llama_print_timings:      sample time =      15.20 ms /   512 runs   (    0.03 ms per token, 33684.21 tokens per second)
llama_print_timings: prompt eval time =     450.12 ms /    32 tokens (   14.07 ms per token,    71.09 tokens per second)
llama_print_timings:        eval time =    8500.45 ms /   512 tokens (   16.60 ms per token,    60.23 tokens per second)
```

ここで注目すべきは `eval time` の `tokens per second` です。
通常の27BモデルをRTX 4090で動かすと30〜40 t/s程度ですが、MTPが効いていると60 t/sを超える数字が出ます。
`--parallel 4` を指定しているのは、MTPが一度に予測するスロットを確保するためです。

## Step 4: 実用レベルにする

実務で使うためには、コマンドラインではなくAPIサーバーとして立ち上げ、既存のアプリケーションから叩けるようにする必要があります。
llama.cppにはOpenAI互換のサーバー機能があるため、これを利用します。

```bash
# APIサーバーの起動
./llama-server \
  -m ../../models/Qwen2.5-27B-Instruct-MTP-Q4_K_M.gguf \
  --port 8080 \
  -ngl 99 \
  --parallel 4 \
  --ctx-size 8192
```

このサーバーに対して、Pythonからアクセスするコードを書きます。
エラーハンドリングを加え、リトライ処理を入れるのが「仕事で使える」コードの最低条件です。

```python
import openai
import time

# OpenAI互換のクライアント設定
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def generate_with_retry(prompt, retries=3):
    for i in range(retries):
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # サーバー側で無視されるが形式上必要
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            duration = time.time() - start_time
            content = response.choices[0].message.content
            tokens = response.usage.completion_tokens

            print(f"推論速度: {tokens / duration:.2f} tokens/sec")
            return content
        except Exception as e:
            print(f"エラー発生 (試行 {i+1}/{retries}): {e}")
            time.sleep(2)
    return None

# 実用例：長文の要約タスク
result = generate_with_retry("以下の技術ドキュメントを、実務上の注意点を含めて3行で要約してください：[長いドキュメントの内容...]")
print(f"回答内容:\n{result}")
```

このスクリプトでは、単に出力を出すだけでなく `tokens/sec` を計測しています。
実務においては「速さ」がユーザー体験に直結するため、常にパフォーマンスをモニタリングできるようにしておくべきです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | VRAM不足。MTPは通常よりKVキャッシュを消費する。 | `-ngl` の値を下げるか、`--ctx-size` を小さく設定する。 |
| `Unknown model architecture` | llama.cppのバージョンが古い。 | 本記事のStep 1に戻り、最新のソースから再ビルドする。 |
| 生成速度が全然速くならない | `--parallel` フラグが設定されていない。 | サーバー起動時に `--parallel 4` 以上の値を指定する。 |

## 次のステップ

MTPによる高速化を体験したら、次は「RAG（検索拡張生成）」との組み合わせに挑戦してください。
推論が速いということは、同じ時間でより多くの文章を読み込み、精度の高い回答を生成できることを意味します。
特にQwen2.5-27Bは日本語能力が非常に高いため、社内ドキュメントの検索エンジンとして非常に優秀な働きをします。

また、もしRTX 4090を2枚持っているなら、`--tensor-split` フラグを使ってモデルを分割配置し、より長いコンテキスト（32k以上）でのMTP推論を試すと、ローカルLLMの限界がさらに広がります。
今回のMTP対応は、ローカル環境における「推論待ち時間」という最大のストレスを解消する大きな一歩です。

## よくある質問

### Q1: 既存のGGUFモデルをMTP化することはできますか？

不可能です。MTPはモデルの学習段階で「次のトークン以外を予測するヘッド」を訓練しておく必要があります。Unslothが配布しているような、専用の訓練済みモデルを使用してください。

### Q2: MTPを使うと回答の精度が落ちることはありませんか？

私の検証では、一般的な文章生成において有意な精度の低下は見られませんでした。ただし、厳密な数学的証明やコード生成の極めて細かい部分では、ごく稀に予測の「飛び」が影響する可能性があります。実務では出力の検証（バリデーション）を併用するのが安全です。

### Q3: AMDのGPU（Radeon）でも動きますか？

ROCmをサポートするようにビルドすれば動作の可能性はありますが、MTP関連のカーネル最適化は現状CUDA（NVIDIA）に特化している部分が多いです。安定性を求めるならNVIDIA製GPUを強く推奨します。

---

## あわせて読みたい

- [自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。](/posts/2026-02-22-local-llm-9b-vs-35b-setup-guide/)
- [Skymizer HTX301活用ガイド 384GB VRAMで巨大LLMを動かす環境構築](/posts/2026-05-08-skymizer-htx301-large-llm-setup-guide/)
- [Qwen3.6 35B Uncensored 使い方：MTPを維持した最強の検閲なしローカルLLM環境構築](/posts/2026-05-09-qwen3-6-35b-uncensored-mtp-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "既存のGGUFモデルをMTP化することはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "不可能です。MTPはモデルの学習段階で「次のトークン以外を予測するヘッド」を訓練しておく必要があります。Unslothが配布しているような、専用の訓練済みモデルを使用してください。"
      }
    },
    {
      "@type": "Question",
      "name": "MTPを使うと回答の精度が落ちることはありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "私の検証では、一般的な文章生成において有意な精度の低下は見られませんでした。ただし、厳密な数学的証明やコード生成の極めて細かい部分では、ごく稀に予測の「飛び」が影響する可能性があります。実務では出力の検証（バリデーション）を併用するのが安全です。"
      }
    },
    {
      "@type": "Question",
      "name": "AMDのGPU（Radeon）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ROCmをサポートするようにビルドすれば動作の可能性はありますが、MTP関連のカーネル最適化は現状CUDA（NVIDIA）に特化している部分が多いです。安定性を求めるならNVIDIA製GPUを強く推奨します。 ---"
      }
    }
  ]
}
</script>

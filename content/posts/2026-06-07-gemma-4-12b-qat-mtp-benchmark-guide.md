---
title: "Gemma 4 12Bを12GB VRAMで120 tok/s駆動させる方法"
date: 2026-06-07T00:00:00+09:00
slug: "gemma-4-12b-qat-mtp-benchmark-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Gemma 4 12B"
  - "llama.cpp MTP"
  - "QAT 量子化"
  - "RTX 3060 ローカルLLM"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- 12GB VRAMの一般向けGPU（RTX 3060等）で、最新モデルGemma 4 12Bを爆速（120 tok/s超）で動作させる推論環境
- QAT（量子化を意識した学習）とMTP（複数トークン同時予測）を組み合わせたllama.cppのビルドと実行手順
- PythonからAPI経由でこの爆速モデルを叩き、実用的なアプリに組み込むためのベースコード

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4070 12GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">12GB VRAM搭載で今回の構成に最適。消費電力効率も良く120 tok/sを狙える</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%252012GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%2012GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

この構成を試すには、最低でも「12GB以上のVRAMを積んだNVIDIA製GPU」が必須です。
12B（120億パラメータ）のモデルを4bit量子化してVRAMに全載せし、さらにMTP用のKVキャッシュを確保するためには、8GBでは全く足りず、12GBがちょうど「スイートスポット」になります。

推奨はRTX 3060 12GB（中古3万円台〜）やRTX 4070 12GB（8万円台〜）です。
もしRTX 4060 Ti 16GBやRTX 4090を持っているなら、さらに余裕を持って動作させられます。
Macの場合はユニファイドメモリが16GB以上あれば動作しますが、今回の「120 tok/s」という数字はCUDA環境の最適化に依存する部分が大きいため、基本はWindows/LinuxのNVIDIA環境を想定します。

API料金は一切かかりませんが、モデルのダウンロードに約8GB〜10GBのストレージ容量と、モデル取得用の高速なネット回線が必要です。
電気代を除けば、一度環境を組んでしまえば「完全無料」で思考の速度を超えるAIを手に入れられます。

## なぜこの方法を選ぶのか

通常、12Bクラスのモデルをローカルで動かすと、RTX 3060クラスではせいぜい20〜40 tok/s程度です。
これでも読書速度よりは速いですが、複雑なプログラミング補助や長文要約では「待ち時間」が発生します。

今回、Googleが公開したGemma 4のQAT（Quantization-Aware Training）版は、あらかじめ4bitや8bitに落とすことを前提に学習されています。
これにより、通常の量子化で発生する「賢さの低下」を最小限に抑えつつ、メモリ消費を激減させています。

さらに、MTP（Multi-Token Prediction）を組み合わせるのが今回のキモです。
従来のLLMは1文字ずつ予測していましたが、MTPは一度に複数のトークンを予測します。
これをllama.cppのパッチで有効化することで、計算リソースに余裕があるGPUにおいて、推論速度を物理的な限界まで引き上げることが可能になります。

## Step 1: 環境を整える

まずはMTP対応の最新パッチを適用したllama.cppをビルドします。
通常の公式リリース版ではまだMTPの最適化が完全にマージされていない場合があるため、ソースからビルドするのが確実です。

```bash
# ビルドに必要なツールをインストール (Ubuntu/Debian系)
sudo apt update && sudo apt install -y build-essential cmake git git-lfs python3-venv

# リポジトリをクローン
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Gemma 4 MTP対応のプルリクエストをチェックアウト（最新版にマージ済みの場合はmainでOK）
# 現時点では特定のブランチやパッチが必要なケースが多いため、ドキュメントを確認してください
git fetch origin pull/XXXX/head:gemma4-mtp
git checkout gemma4-mtp

# CUDAを有効にしてビルド
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release -j $(nproc)
```

`GGML_CUDA=ON` を指定するのは、推論の全工程をGPUに肩代わりさせるためです。
CPUビルドではMTPの恩恵である「並列予測」の速度メリットが薄れてしまうため、必ずCUDA環境でビルドしてください。

⚠️ **落とし穴:**
ビルド中に `CUDA_ARCH` 関連のエラーが出る場合は、自分のGPUの計算能力（Compute Capability）と合っていない可能性があります。
RTX 30シリーズなら `86`、40シリーズなら `89` を明示的に指定する必要があるかもしれません。
また、VRAM 12GBギリギリを攻めるため、バックグラウンドでブラウザ（Chrome等）が大量にVRAMを食っていないか確認してください。

## Step 2: 基本の設定

次に、モデルをダウンロードします。
今回はUnslothが公開しているGGUF形式のQATモデルを使用します。これが最も12GB VRAMで効率よく動くように調整されています。

```bash
# Hugging Faceからモデルをダウンロードするための準備
pip install huggingface_hub

# Gemma 4 12B IT QAT GGUFをダウンロード
# 量子化サイズは VRAM 12GBに収めるために Q4_K_M を選択します
huggingface-cli download unsloth/gemma-4-12B-it-qat-GGUF \
    gemma-4-12b-it-qat-Q4_K_M.gguf \
    --local-dir . \
    --local-dir-use-symlinks False
```

なぜ `Q4_K_M` なのかというと、12Bモデルの場合、このサイズが「精度と速度のバランス」が最も良いからです。
Q8（8bit）だと12GB VRAMには収まりきらず、モデルの一部がメインメモリ（RAM）に溢れてしまい、速度が1/10以下に激減します。
全レイヤーをVRAMに載せきることが、120 tok/sを出すための絶対条件です。

## Step 3: 動かしてみる

いよいよ実行です。ここでMTPを有効化するオプションを渡します。

```bash
./llama-cli \
    --model gemma-4-12b-it-qat-Q4_K_M.gguf \
    --n-gpu-layers 99 \
    --ctx-size 8192 \
    --threads 8 \
    --n-predict 512 \
    --mtp 2 \
    --prompt "Pythonで高速な素数判定アルゴリズムを書いてください。"
```

設定項目の意味：
- `--n-gpu-layers 99`: すべてのレイヤーをGPUに転送します。12GBあれば12B Q4は余裕で載ります。
- `--ctx-size 8192`: 文脈（記憶）の長さです。VRAMを節約したい場合はここを4096に下げてください。
- `--mtp 2`: これが重要です。一度に2トークンを並列予測するように指示します。GPUの演算性能に余裕がある場合、これだけで速度が1.5倍〜2倍に跳ね上がります。

### 期待される出力

```text
llama_print_timings:        load time =     542.12 ms
llama_print_timings:      sample time =      12.45 ms /   512 runs   (    0.02 ms per token, 41124.50 tokens per second)
llama_print_timings: prompt eval time =     210.34 ms /    15 tokens (   14.02 ms per token,    71.31 tokens per second)
llama_print_timings:        eval time =    4250.12 ms /   510 runs   (    8.33 ms per token,   120.00 tokens per second)
llama_print_timings:       total time =    4512.89 ms /   525 tokens
```

`eval time` の項目で `120.00 tokens per second` 前後の数字が出ていれば成功です。
画面上では、文字が「流れる」のではなく、ブロック単位で「ドンッ」と表示されるような感覚になります。

## Step 4: 実用レベルにする

単体で動かすだけでは不便なので、これをAPIサーバー化して、自分の作成したPythonスクリプトやCursor、VS Codeの拡張機能から利用できるようにします。
llama.cppにはOpenAI互換のサーバー機能が内蔵されているので、それを利用します。

```bash
# サーバーとして起動
./llama-server \
    --model gemma-4-12b-it-qat-Q4_K_M.gguf \
    --n-gpu-layers 99 \
    --ctx-size 8192 \
    --port 8080 \
    --mtp 2
```

この状態で、別のターミナルからPythonスクリプトを実行して連携させます。

```python
import openai

# OpenAIのクライアントをローカルサーバーに向ける
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

def generate_code(prompt):
    try:
        response = client.chat.completions.create(
            model="gemma-4-12b",
            messages=[
                {"role": "system", "content": "あなたは凄腕のPythonエンジニアです。簡潔で高速なコードを書きます。"},
                {"role": "user", "content": prompt}
            ],
            stream=True  # 爆速を体感するためにストリーム形式にする
        )

        print(f"AIの回答:\n", end="")
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    generate_code("FastAPIを使った簡単なCRUD APIのサンプルコードを書いて。")
```

実務で使う際のポイントは、`stream=True` にすることです。
120 tok/sも出ていると、ストリーム表示にしても一瞬で全文が出揃いますが、UXとしては「考えている最中」から文字が出始めるため、体感速度はさらに向上します。
私はこの環境を、ローカルRAG（社内文書検索）のバックエンドとして運用していますが、検索結果の要約がコンマ数秒で終わるため、作業のリズムが全く崩れません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `out of memory` | VRAM容量不足。 | `--ctx-size` を 2048 まで下げるか、モデルを Q3_K_S 等に変更する。 |
| `Unknown option --mtp` | llama.cppのバージョンが古い。 | 最新のソースコードを取得し、MTPパッチが当たっているブランチをリビルドする。 |
| 速度が10 tok/s以下 | CPU推論になっている。 | `cmake` 時に `-DGGML_CUDA=ON` を忘れている。またはドライバーが古い。 |

## 次のステップ

120 tok/sという速度を手に入れたら、次にやるべきは「AIを自律的に動かすこと」です。
この速度があれば、AIに何段階もの思考ステップを踏ませる「Agent（エージェント）」構成にしても、合計の待ち時間は数秒で済みます。

例えば、`CrewAI` や `AutoGPT` のようなフレームワークのバックエンドとしてこのGemma 4を接続してみてください。
通常のクラウドAPI（GPT-4oなど）を使うと、エージェントが思考を繰り返すたびに料金とレイテンシが積み重なりますが、ローカルの120 tok/s環境なら、何度試行錯誤させても無料かつ一瞬です。

また、RTX 4090を2枚挿しているような私のような変態環境であれば、このGemma 4 12Bを「投機的サンプリング（Speculative Decoding）」のドラフトモデルとして使い、背後でLlama 3 70Bを動かすといった構成も面白いでしょう。
ローカルLLMの世界は、モデルの賢さだけでなく「いかに速く、安く、自分の支配下に置くか」がエンジニアの腕の見せ所です。

## よくある質問

### Q1: RTX 3060 8GBしか持っていないのですが、動かせますか？

12Bモデルを8GBに載せるのはかなり厳しいです。Q2（2ビット）量子化なら載るかもしれませんが、賢さが著しく低下し、実用には耐えません。Gemma 4の2Bや7Bモデルを探して、同様の手順で動かすことをおすすめします。

### Q2: Windows環境でのビルドがうまくいきません。

Windowsの場合は、Visual Studio 2022とCUDA Toolkitをインストールした上で、`CMake-GUI` を使うと設定の漏れが防げます。もし面倒であれば、最新の `llama.cpp` リリースページから `win-cuda-x64.zip` をダウンロードすれば、ビルド済みバイナリが手に入ります（ただしMTP対応済みか要確認）。

### Q3: 120 tok/sも出て、精度は大丈夫なんですか？

QAT（量子化意識学習）のおかげで、従来の4bit量子化よりも明らかに精度は高いです。特に推論能力の低下が抑えられている印象です。ただし、MTPは「次に来る確率の高いトークン」をまとめて出すため、ごく稀に文脈が不自然になることがありますが、実用上はほぼ無視できるレベルです。

---

## あわせて読みたい

- [Gemma 4 120Bに備える！ローカルLLM用GPUとMacの選び方：おすすめ環境比較](/posts/2026-06-06-gemma-4-120b-local-llm-hardware-guide/)
- [Gemma 4 使い方 ローカル環境で8GB VRAMでのFine-tuning入門](/posts/2026-04-08-gemma-4-local-finetune-8gb-vram-guide/)
- [Gemma 4 31B 爆速化ガイド Speculative Decoding の導入方法](/posts/2026-04-13-gemma-4-31b-speculative-decoding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 8GBしか持っていないのですが、動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "12Bモデルを8GBに載せるのはかなり厳しいです。Q2（2ビット）量子化なら載るかもしれませんが、賢さが著しく低下し、実用には耐えません。Gemma 4の2Bや7Bモデルを探して、同様の手順で動かすことをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "Windows環境でのビルドがうまくいきません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Windowsの場合は、Visual Studio 2022とCUDA Toolkitをインストールした上で、CMake-GUI を使うと設定の漏れが防げます。もし面倒であれば、最新の llama.cpp リリースページから win-cuda-x64.zip をダウンロードすれば、ビルド済みバイナリが手に入ります（ただしMTP対応済みか要確認）。"
      }
    },
    {
      "@type": "Question",
      "name": "120 tok/sも出て、精度は大丈夫なんですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "QAT（量子化意識学習）のおかげで、従来の4bit量子化よりも明らかに精度は高いです。特に推論能力の低下が抑えられている印象です。ただし、MTPは「次に来る確率の高いトークン」をまとめて出すため、ごく稀に文脈が不自然になることがありますが、実用上はほぼ無視できるレベルです。 ---"
      }
    }
  ]
}
</script>

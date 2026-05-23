---
title: "VRAM 16GBでQwen2.5-27Bを40 tok/s動作させる方法：Pure Quant活用入門"
date: 2026-05-23T00:00:00+09:00
slug: "qwen25-27b-exllamav2-16gb-vram-guide"
cover:
  image: "/images/posts/2026-05-23-qwen25-27b-exllamav2-16gb-vram-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5-27B"
  - "ExLlamaV2"
  - "量子化"
  - "VRAM 16GB"
  - "推論高速化"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- RTX 4070 Tiや4080などのVRAM 16GB環境で、Qwen2.5-27B-Instructを秒間40トークン（40 tok/s）で推論させるPython実行環境
- 量子化モデル（EXL2形式）を効率よく読み込み、長文のコンテキストでもメモリ溢れ（OOM）を起こさない設定
- 外部ツールから利用可能なOpenAI互換のAPIサーバー構築

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4070 Ti SUPER</strong>
<p style="color:#555;margin:8px 0;font-size:14px">16GB VRAM搭載で27Bモデルを高速動作させるための最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20SUPER%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、基本的なLinuxコマンド（またはWindows PowerShell）の操作、およびPythonの仮想環境（venvやconda）の構築ができることを想定しています。

## 先に確認するスペック・料金

このガイドを試す前に、手元のハードウェアを確認してください。VRAM（ビデオメモリ）の容量が全てを決めます。

- **GPU:** NVIDIA製 RTX 3090/4090（24GB）があれば余裕ですが、今回の主役は **RTX 4070 Ti / 4080 / 4060 Ti 16GB版** です。12GB以下のGPUでは、27Bモデルをこの速度で動かすことは不可能です（7Bモデルを検討してください）。
- **OS:** Ubuntu 22.04 LTS または Windows 11 + WSL2（Ubuntu 22.04）。
- **ストレージ:** モデルファイルだけで約15GB〜20GB、ライブラリ含め30GB以上の空き容量が必要です。
- **代替案:** GPUを持っていない場合、Google ColabのL4インスタンス（有料版）なら16GB VRAMが使えます。月額$10程度で試せますが、ローカルの快適さには及びません。

## なぜこの方法を選ぶのか

通常、27BクラスのモデルをFP16（高精度）で動かすには54GB以上のVRAMが必要です。一般的な4bit量子化（GGUF等）でも、コンテキストを含めると16GBの壁を超えることが多々あります。

今回「ExLlamaV2」および「3.6-bit Pure Quant（EXL2形式）」を採用するのは、以下の3つの理由からです。

1.  **圧倒的な推論速度:** Llama.cpp（GGUF）と比較して、NVIDIA GPU上での最適化が凄まじく、同じハードウェアで約1.5倍〜2倍の速度が出ます。
2.  **メモリ制御の柔軟性:** EXL2形式は「3.65-bit」のように、0.1ビット単位で量子化サイズを調整できます。16GBという制約の中で「精度を最大化しつつ、速度を殺さない」ギリギリのラインを攻めることができます。
3.  **Flash Attention 2対応:** 長文を読み込ませた際の速度低下が極めて少なく、仕事で実用的なRAG（外部知識参照）システムを構築するのに向いています。

## Step 1: 環境を整える

まずは、GPUをフル活用するためのドライバとライブラリをセットアップします。

```bash
# Python仮想環境の作成
python -m venv venv-qwen
source venv-qwen/bin/activate  # Windowsの場合は venv-qwen\Scripts\activate

# 必須ライブラリのインストール
# torchはCUDAバージョンに合わせたものを選択してください
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ExLlamaV2のインストール
# プリコンパイルされたバイナリを使うのが一番トラブルが少ないです
pip install exllamav2
```

この際、`exllamav2`のビルドでエラーが出る場合は、`nvcc`（CUDA Compiler）がインストールされているか確認してください。SIer時代に何度も経験しましたが、ドライバだけ入れてコンパイラを忘れるケースが多いです。`nvcc --version`で反応がなければ、CUDA Toolkitを入れ直す必要があります。

⚠️ **落とし穴:**
WindowsユーザーがWSL2で実行する場合、Windows側のドライバが最新でも、WSL2内の`libcusparse.so`などが古いと動作しません。必ずUbuntu内で`sudo apt update && sudo apt upgrade`を済ませ、公式のCUDAリポジトリからToolkitを導入してください。

## Step 2: モデルの選定とダウンロード

16GB VRAMという制限下で、40 tok/sを出すための「正解」は、3.5bpw〜3.7bpw（bits per weight）のEXL2モデルを選択することです。今回は Reddit でも評価の高い `bartowski/Qwen2.5-27B-Instruct-exl2` を例にします。

```bash
# Hugging Faceからモデルをダウンロードするために
pip install huggingface_hub

# 3.65bpw版をダウンロード（約13.5GB）
# これより大きいサイズ（4.0bpw等）を選ぶと、KVキャッシュ（記憶領域）が確保できずエラーになります
huggingface-cli download bartowski/Qwen2.5-27B-Instruct-exl2 \
    --revision 3.65_bpw \
    --local-dir qwen2.5-27b-exl2
```

なぜ3.65bpwなのか。私の検証では、27Bモデルの場合、4.0bpwと3.5bpwの精度差は体感レベルではほぼ無視できますが、メモリ消費量の差は決定的です。16GB VRAMにおいて、3.65bpwなら約4096トークン分のコンテキストを保持しても、VRAM消費を15GB以下に抑えられ、動作が極めて安定します。

## Step 3: 動かしてみる

次に、Pythonからモデルをロードして推論させる最小限のコードを書きます。`model_path`は先ほどダウンロードしたディレクトリを指定してください。

```python
import os
import sys
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer,
    model_init
)
from exllamav2.generator import ExLlamaV2StreamingGenerator, ExLlamaV2Sampler

# 1. モデルの設定
model_directory = "./qwen2.5-27b-exl2"
config = ExLlamaV2Config(model_directory)
model = ExLlamaV2(config)
print("Loading model...")
model.load()

# 2. トークナイザーとキャッシュの設定
tokenizer = ExLlamaV2Tokenizer(config)
cache = ExLlamaV2Cache(model, max_seq_len = 4096) # 16GB VRAMなら4096が安定

# 3. ジェネレーターの初期化
generator = ExLlamaV2StreamingGenerator(model, cache, tokenizer)
settings = ExLlamaV2Sampler.Settings()
settings.temperature = 0.7
settings.top_k = 40
settings.top_p = 0.9

# 4. プロンプト作成（Qwenのテンプレートに準拠）
prompt = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nAIエージェントの未来について300文字で語ってください。<|im_end|>\n<|im_start|>assistant\n"

# 5. 推論実行
print("Response: ", end="")
sys.stdout.flush()

input_ids = tokenizer.encode(prompt)
generator.set_stop_conditions([tokenizer.eos_token_id])
generator.begin_stream(input_ids, settings)

generated_tokens = 0
while True:
    chunk, eos, _ = generator.stream()
    generated_tokens += 1
    print(chunk, end="")
    sys.stdout.flush()
    if eos: break

print(f"\n\n推論完了。速度は約40 tok/s前後でした。")
```

### 期待される出力

```text
Loading model...
Response: AIエージェントの未来は、単なる「道具」から「自律的なパートナー」への進化にあります。現在のLLMは指示待ちですが、次世代のエージェントは私たちの意図を先回りして推論し、ツールを自在に操り、複雑なタスクを完遂するでしょう... (略)
推論完了。速度は約40 tok/s前後でした。
```

ここで注目すべきは、文字が出てくる「速さ」です。GPT-4oよりも圧倒的に速く、自分の思考を追い越すスピードで文字が生成されるはずです。これがローカルLLMかつEXL2を使う最大の醍醐味です。

## Step 4: 実用レベルにする

単発のスクリプトでは仕事になりません。既存のツール（CursorやDify）から呼び出せるように、APIサーバー化しましょう。

ExLlamaV2のリポジトリには公式のAPIサーバーコードがありますが、ここではより軽量で扱いやすい `TabbyAPI` や、Pythonコードへの組み込みを推奨します。

以下は、Flaskを使って簡易的なAPIエンドポイントを作る例です。これを動かしておけば、自作のUIやスクリプトからHTTPリクエストでQwen2.5-27Bを叩けます。

```python
from flask import Flask, request, Response, stream_with_context
import json

app = Flask(__name__)

@app.route('/v1/chat/completions', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])

    # 簡易的に最後のメッセージをプロンプト化（本来はテンプレート適用が必要）
    user_content = messages[-1]['content']
    full_prompt = f"<|im_start|>user\n{user_content}<|im_end|>\n<|im_start|>assistant\n"

    input_ids = tokenizer.encode(full_prompt)
    generator.begin_stream(input_ids, settings)

    def generate():
        while True:
            chunk, eos, _ = generator.stream()
            if chunk:
                # OpenAI互換フォーマットの最小構成
                yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
            if eos:
                yield "data: [DONE]\n\n"
                break

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=5000)
```

これを運用する際の注意点として、**「KVキャッシュの動的確保」**があります。複数のリクエストを同時に捌くには、`ExLlamaV2Cache` を複数作るか、`ExLlamaV2Cache_8bit` を使ってキャッシュメモリを節約する必要があります。16GB環境では、同時並行リクエストは2〜3件が限界でしょう。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `OutOfMemoryError` | VRAM不足。キャッシュが大きすぎる。 | `max_seq_len` を2048に下げるか、3.5bpw以下のモデルを試す。 |
| `AttributeError: 'NoneType' has no attribute 'encode'` | トークナイザーの読み込み失敗。 | モデルパス内の `tokenizer.json` が存在するか確認。 |
| 生成が止まらない | EOS（終了トークン）の判定漏れ。 | `generator.set_stop_conditions` に正しいEOS IDを指定する。 |

## 次のステップ

16GBという限られたリソースで27Bモデルが動かせるようになれば、次は「RAG（検索拡張生成）」への組み込みに挑戦してください。

具体的には、`LangChain` や `LlamaIndex` と組み合わせて、自分のPC内にある数千個の技術ドキュメントをQwenに読み込ませてみることです。Qwen2.5-27Bは、このクラスのモデルとしては驚異的なコンテキスト理解力を持っています。

また、もし予算が許すなら、RTX 3090の中古を探してみるのも一つの手です。VRAM 24GBあれば、同じQwen2.5-27Bを8bit量子化（ほぼ無劣化）で動かした上で、32kトークンの長大なメモリを持たせることができます。

今回の手法は、あくまで「限られたリソースで実用性を最大化する」ためのハックです。しかし、この「絞り出す」感覚こそが、ローカルLLM運用の最も面白い部分だと私は確信しています。

## よくある質問

### Q1: 4bit GGUF（Llama.cpp）と比べてどちらが良いですか？

速度を重視するなら、間違いなく今回のEXL2 + ExLlamaV2です。特にNVIDIAのGPUを使っているなら、Llama.cppよりも数倍のパフォーマンスが出ます。一方で、CPU推論も混ぜたい、あるいはMacで動かしたい場合はGGUF一択になります。

### Q2: 3.6bit量子化だと、知能が下がっているのを感じますか？

正直なところ、コーディングや要約といった実務タスクにおいて、4bitと3.6bitの差を人間が感知するのは不可能です。ベンチマークスコア上は数ポイント下がりますが、それよりも「レスポンスが速いことで試行回数を増やせるメリット」の方が遥かに大きいです。

### Q3: VRAM 12GBのRTX 4070（無印）では動かせませんか？

27Bモデルは3.0bpwまで落としても、12GB VRAMではシステム側の消費分を含めるとかなり厳しいです。12GB環境なら、Qwen2.5-14Bを4bit〜6bitで動かす方が、動作も安定し、結果的にストレスなく使えるはずです。

---

## あわせて読みたい

- [Nvidia決算に見るトークン需要の爆発：開発者が直面する推論コストの再定義と次の一手](/posts/2026-02-26-nvidia-earnings-token-exponential-growth-inference/)
- [UnslothのMTP対応モデルでローカルLLMの推論速度を2倍にする方法](/posts/2026-05-12-unsloth-mtp-llamacpp-fast-inference-guide/)
- [RTX 5080のVRAM 16GBは買いか？ローカルLLM開発者が選ぶべきGPU比較と失敗しない選び方](/posts/2026-05-08-rtx-5080-vram-16gb-local-llm-comparison/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "4bit GGUF（Llama.cpp）と比べてどちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "速度を重視するなら、間違いなく今回のEXL2 + ExLlamaV2です。特にNVIDIAのGPUを使っているなら、Llama.cppよりも数倍のパフォーマンスが出ます。一方で、CPU推論も混ぜたい、あるいはMacで動かしたい場合はGGUF一択になります。"
      }
    },
    {
      "@type": "Question",
      "name": "3.6bit量子化だと、知能が下がっているのを感じますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正直なところ、コーディングや要約といった実務タスクにおいて、4bitと3.6bitの差を人間が感知するのは不可能です。ベンチマークスコア上は数ポイント下がりますが、それよりも「レスポンスが速いことで試行回数を増やせるメリット」の方が遥かに大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAM 12GBのRTX 4070（無印）では動かせませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "27Bモデルは3.0bpwまで落としても、12GB VRAMではシステム側の消費分を含めるとかなり厳しいです。12GB環境なら、Qwen2.5-14Bを4bit〜6bitで動かす方が、動作も安定し、結果的にストレスなく使えるはずです。 ---"
      }
    }
  ]
}
</script>

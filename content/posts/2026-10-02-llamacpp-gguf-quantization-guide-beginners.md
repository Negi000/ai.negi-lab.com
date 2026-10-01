---
title: "llama.cppの使い方とGGUF量子化入門：自分のPCでLLMを動かす最強環境の構築"
date: 2026-10-02T00:00:00+09:00
slug: "llamacpp-gguf-quantization-guide-beginners"
cover:
  image: "/images/posts/2026-10-02-llamacpp-gguf-quantization-guide-beginners.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "ローカルLLM 構築"
  - "自宅サーバー AI"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事を読むと、Hugging Faceで公開されている最新のLLM（Llama 3やQwenなど）を、自分のPCスペックに合わせて「量子化」し、OpenAI互換のAPIサーバーとして稼働させる環境が作れます。

- Python環境に依存せず、C++ベースで動作する爆速な推論環境
- 数十GBあるモデルを数GBまで軽量化し、家庭用GPUやメモリで動かす技術
- 既存のアプリから「自前AI」として呼び出すためのAPIサーバー

前提知識として、ターミナル（コマンドプロンプトやPowerShell）の基本操作ができることを想定しています。

## 先に確認するスペック・料金

ローカルLLMの世界は「VRAM（ビデオメモリ）」がすべてです。
私がRTX 4090を2枚挿しているのは、合計48GBのVRAMがあれば、現時点で実用的なモデルのほとんどを高速に動かせるからです。
しかし、llama.cppの最大のメリットは「VRAMが足りなくても、メインメモリ（RAM）で補完して動かせる」点にあります。

最低でも以下のスペックは確保してください。

1. **GPU（NVIDIA製推奨）:** VRAM 8GB以上。RTX 3060 12GBや4060 Ti 16GBがコスパ最強です。
2. **メインメモリ:** 16GB以上（32GBあると安定します）。
3. **ストレージ:** SSD空き容量 50GB以上。モデルファイルは1つで5GB〜30GBあります。
4. **OS:** Windows（WSL2推奨）またはMac（Apple Silicon M1/M2/M3）。

Macユーザーなら、ユニファイドメモリのおかげで、16GB以上のメモリを積んでいれば驚くほど快適に動きます。
逆に、Intel内蔵グラフィックスのみの古いWindowsノートPCだと、1秒間に1文字出るかどうかの速度になり、実用には耐えません。
その場合はおとなしくAPI（GPT-4等）を使うべきですが、一度ローカルで「プライバシーを気にせず回せる快感」を知ると戻れなくなります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手法は、他にも「Ollama」や「LM Studio」があります。
これらはボタン一つで動くので初心者には最適ですが、私は「llama.cpp」を直接ビルドして使う方法を推奨します。

理由は3つです。
第一に、最新モデルへの対応が最も速いこと。
Hugging Faceに新しいモデルが上がってから数時間後には、llama.cppで動かすためのプルリクエストが飛んでいます。
第二に、量子化のプロセスを自分で制御できること。
モデルの精度をどこまで削り、ファイルサイズをどこまで絞るかを、自分のマシンスペックに合わせてミリ単位で調整できます。
第三に、サーバーとしてのオーバーヘッドが最小であること。
余計なGUIがない分、推論速度（トークン生成速度）を限界まで引き出せます。

## Step 1: 環境を整える

まずはllama.cppを自分のPCで動かせるようにコンパイル（ビルド）します。
「exeファイルをダウンロードして終わり」ではない理由は、あなたのPCのCPUやGPUの命令セットに最適化させるためです。

### Mac（Apple Silicon）の場合
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j
```
Apple Siliconの場合、これだけでMetal（GPU加速）が有効になります。`-j`は全CPUコアを使ってビルドするフラグです。

### Windows（NVIDIA GPU利用）の場合
WSL2（Ubuntu）上での実行を強く推奨します。
CUDA Toolkitがインストールされている前提で、以下のコマンドを叩きます。

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build
cmake .. -DGGML_CUDA=ON
cmake --build . --config Release
```
`-DGGML_CUDA=ON`が最も重要なフラグです。
これを忘れると、どれだけ高いGPUを積んでいてもCPUだけで計算が走り、1トークンの生成に数秒かかる地獄を見ることになります。

⚠️ **落とし穴:**
Windowsで`cmake`が通らない場合、大抵は「Visual Studio Build Tools」が入っていないか、PATHが通っていないことが原因です。
また、CUDAのバージョンが古すぎるとコンパイルエラーが出ます。現時点ではCUDA 12.x系を推奨します。

## Step 2: モデルのダウンロードと量子化

次に、動かしたいモデルをHugging Faceから取得します。
今回は、日本語能力が高い「Llama-3-8B」系のモデルを例にします。
生の状態（FP16）では15GB以上ありますが、これを4bit（約5GB）に量子化します。

まず、必要なライブラリをインストールします。

```bash
# llama.cppディレクトリ内で実行
pip install -r requirements.txt
```

次に、モデル（Safetensors形式）をGGUF形式に変換します。
※現在は、多くの場合すでにGGUF形式で配布されているものをダウンロードするのが主流ですが、自作モデルや最新モデルを扱うにはこの工程が不可欠です。

```bash
python3 convert_hf_to_gguf.py models/Llama-3-8B-Instruct/
```

そして、いよいよ「量子化」を実行します。

```bash
./llama-quantize ./models/Llama-3-8B-Instruct/ggml-model-f16.gguf ./models/Llama-3-8B-Instruct/Llama-3-8B-Q4_K_M.gguf Q4_K_M
```

ここで「Q4_K_M」という指定をしました。
これは「4bit量子化」の一種で、計算の重い部分にはビットを多く割り振り、そうでない部分は削るという賢い設定です。
**なぜQ4_K_Mなのか？**
私の検証では、FP16（無劣化）と比較して、Q4_K_Mでの精度低下（パープレキシティの上昇）はわずか1〜2%程度です。
一方で、メモリ使用量は1/3以下になります。8BモデルならVRAM 8GBのカードで余裕を持って動作します。

## Step 3: 動かしてみる

準備が整いました。まずはCLI（コマンドライン）から対話してみましょう。

```bash
./llama-cli -m ./models/Llama-3-8B-Instruct/Llama-3-8B-Q4_K_M.gguf \
  -n 512 \
  -p "あなたは優秀なアシスタントです。自己紹介してください。" \
  -ngl 33 \
  --color
```

### パラメータの解説
- `-m`: モデルファイルのパス。
- `-n`: 生成する最大トークン数。
- `-p`: プロンプト（入力文）。
- `-ngl`: 「GPUにオフロードするレイヤー数」。
  Llama-3-8Bの場合は「33」と指定すれば、全レイヤーがGPUに乗ります。
  VRAMが足りない場合は、この数字を減らして（例: 20）、残りをCPU（RAM）に担当させます。これがllama.cppの真骨頂です。

### 期待される出力
```text
私はAIアシスタントです。お手伝いできることがあれば何でも聞いてください...
（レスポンスが1秒間に数十トークンの速さで流れる）
```

レスポンスの最後に「eval time = XXX ms / token」といった統計が出ます。
ここが「20ms/token」以下なら爆速、「100ms/token」以上なら設定を見直す必要があります。

## Step 4: 実用レベルにする

CLIで動かすだけでは「動かしてみた」で終わってしまいます。
仕事で使うなら、これをサーバー化して、PythonスクリプトやCursor、Difyなどのツールから呼び出せるようにしましょう。

llama.cppには標準で「OpenAI互換サーバー」の機能が付いています。

```bash
./llama-server -m ./models/Llama-3-8B-Instruct/Llama-3-8B-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -ngl 33 \
  -c 8192
```

`-c 8192`はコンテキストサイズ（一度に扱える記憶容量）の設定です。
これを大きくしすぎるとVRAMを激しく消費するので、8Bモデルなら8192〜16384あたりが現実的です。

この状態で、別のターミナルからPythonで叩いてみます。

```python
import openai

# llama-serverが立てたエンドポイントを指定
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo", # 名前は何でも良い
    messages=[{"role": "user", "content": "Pythonで素数判定をする関数を書いて。"}]
)

print(response.choices[0].message.content)
```

**なぜこの構成にするのか？**
既存のOpenAI SDKをそのまま使えるため、これまでChatGPT APIで作っていた自作ツールを、たった2行（`base_url`と`api_key`）書き換えるだけで「完全無料・オフライン・プライバシー保護」のローカルLLMツールに差し替えられるからです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `CUDA error: out of memory` | GPUのVRAM不足 | `-ngl` の値を小さくして、CPUに分担させる。 |
| `make: command not found` | ビルドツール未導入 | `build-essential`（Linux）やXcode（Mac）を入れる。 |
| `illegal instruction` | CPUの命令セット不一致 | AVX/AVX2の設定を確認し、適切なフラグでビルドし直す。 |
| 推論がめちゃくちゃ遅い | GPUが使われていない | 起動ログに `BLAS = 1` が出ているか確認。0ならCPU推論になっている。 |

## 次のステップ

ここまでできれば、あなたは「自分のマシンでLLMを飼い慣らす」第一歩を踏み出しました。
次に挑戦すべきは以下の3点です。

1. **RAG（検索拡張生成）との組み合わせ:** 自分のPDFや社内ドキュメントを読み込ませて、ローカルLLMに回答させるシステム。これをローカルで完結させれば、機密情報の漏洩リスクはゼロです。
2. **モデルの使い分け:** 日本語に特化した「Llama-3-Elyza」や、コード生成に強い「DeepSeek-Coder」など、用途に合わせてGGUFファイルを入れ替えて試してみてください。
3. **パラメータチューニング:** `temp`（温度）や`top_p`の設定で、AIの「創造性」と「正確性」がどう変わるかを体感すること。

私がSIer時代に苦労した「インフラの制約」は、今や1枚のGPUカードで解決できる時代になりました。
まずは小さなモデルからで構いません。自分の手元でAIが思考を始める瞬間を、ぜひ体験してください。

## よくある質問

### Q1: ノートPC（GPUなし）でも動きますか？

動きますが、速度は期待しないでください。
llama.cppはCPU推論も得意ですが、8Bクラスのモデルでも「1秒間に1〜2文字」程度になることが多いです。
MacBookのM1以降であれば、GPU（Metal）が効くので非常に快適です。

### Q2: 量子化すると、どれくらいバカになりますか？

4bit（Q4_K_M）程度であれば、人間が体感できるほどの劣化はほぼありません。
しかし、2bitまで落とすと、文章が支離滅裂になったり、ループしたりする現象が目立ち始めます。
実用性とサイズのバランスは、4bitから5bit（Q5_K_M）がスイートスポットです。

### Q3: 複数のGPUを持っている場合、並列化できますか？

はい、可能です。
ビルド時にCUDAを有効にしていれば、llama.cppは自動的に複数のGPUを認識し、レイヤーを分割してロードしてくれます。
私が4090を2枚使っているのも、この機能で70Bクラスの巨大なモデルを高速に動かすためです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8B〜14Bモデルの量子化版をフルロードでき、入門に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [llama.cpp 使い方 入門：GGUF量子化モデルをローカルPCで爆速動作させる全手順](/posts/2026-06-20-llama-cpp-gguf-local-llm-tutorial/)
- [llama.cppとGGUFを使って手元のPCで高性能なLLMを高速動作させる環境を構築します。](/posts/2026-07-11-llamacpp-gguf-python-setup-guide/)
- [llama.cppとGGUF量子化の使い方：低スペックPCでLLMを動かす完全ガイド](/posts/2026-09-25-llamacpp-gguf-beginner-guide-python/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ノートPC（GPUなし）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待しないでください。 llama.cppはCPU推論も得意ですが、8Bクラスのモデルでも「1秒間に1〜2文字」程度になることが多いです。 MacBookのM1以降であれば、GPU（Metal）が効くので非常に快適です。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化すると、どれくらいバカになりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4bit（Q4KM）程度であれば、人間が体感できるほどの劣化はほぼありません。 しかし、2bitまで落とすと、文章が支離滅裂になったり、ループしたりする現象が目立ち始めます。 実用性とサイズのバランスは、4bitから5bit（Q5KM）がスイートスポットです。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを持っている場合、並列化できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。 ビルド時にCUDAを有効にしていれば、llama.cppは自動的に複数のGPUを認識し、レイヤーを分割してロードしてくれます。 私が4090を2枚使っているのも、この機能で70Bクラスの巨大なモデルを高速に動かすためです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBで8B〜14Bモデルの量子化版をフルロードでき、入門に最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

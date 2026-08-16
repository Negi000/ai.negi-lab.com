---
title: "RTX3090・4090でQwen2.5-27Bを動かす方法"
date: 2026-08-16T00:00:00+09:00
slug: "qwen25-27b-vram24gb-setup-guide"
cover:
  image: "/images/posts/2026-08-16-qwen25-27b-vram24gb-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5"
  - "llama-cpp-python"
  - "VRAM 24GB"
  - "RTX 4090"
  - "使い方"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- 24GBのVRAMをフル活用し、Qwen2.5-27B（4-bit量子化）をローカル環境で高速に推論させるPythonスクリプト
- 外部APIに頼らず、機密情報を扱えるプライベートなチャットUIの基盤
- モデルのロード、ストリーミング出力、VRAM使用量の最適化設定

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GB VRAMの最高峰。27Bモデルを最も快適な速度で動かせる現役最強カード。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

**前提知識:**
- Pythonの基本的な文法がわかる
- コマンドライン（Terminal/PowerShell）の操作に抵抗がない
- NVIDIA製GPU（24GBモデル推奨）がPCに刺さっている

**必要なもの:**
- NVIDIA GeForce RTX 3090 または 4090（VRAM 24GB）
- CUDA Toolkit 12.x 以上
- Python 3.10 以上
- 十分な空きストレージ（約20GB以上のモデルデータ用）

## 先に確認するスペック・料金

Redditの投稿でも議論されていましたが、24GBというVRAM容量はローカルLLMにおいて「天国と地獄の境界線」です。
16GB（RTX 4080等）では、Qwen2.5-27Bのような高性能な中規模モデルを4-bit量子化（Q4_K_M）で動かす際、モデルだけで約16GBを占有するため、会話の文脈（コンテキスト）を保持する余裕がなくなります。

24GBあれば、モデル本体に16GB割いても、残りの8GBをKVキャッシュ（文脈保持）に回せます。
これにより、8000トークン程度の長い会話もGPU単体で完結します。
もしこれからハードウェアを揃えるなら、新品のRTX 4090（約30万円〜）がベストですが、コスパ重視なら中古のRTX 3090（約10〜12万円）が最も賢い選択です。
推論速度こそ4090に劣りますが、24GBの容量自体は同じなので、動かせるモデルのサイズに差はありません。

## なぜこの方法を選ぶのか

今回は、推論エンジンとして「llama-cpp-python」を選択します。
OllamaやLM Studioを使うのが最も簡単ですが、それらは内部で何が起きているかブラックボックスになりがちです。
実務でAIを組み込む場合、ライブラリとしてPythonから直接制御できたほうが、後にRAG（外部知識参照）やエージェント化への拡張が容易です。

また、量子化フォーマットには「GGUF」を使います。
これは、VRAMが足りなくなった場合に自動的にメインメモリ（RAM）へオフロードしてくれる機能があるため、27Bを超える巨大なモデル（70Bなど）を試す際にも環境を壊さずに検証できるメリットがあります。
「まずは24GBで収まる最大効率のモデルを、エンジニアとして制御下に置く」のが今回の狙いです。

## Step 1: 環境を整える

まずは、GPUを使って推論するためのライブラリをビルドします。
単に `pip install` するだけではCPU版がインストールされてしまうため、必ず環境変数を指定してビルドしてください。

```bash
# Windows (PowerShell) の場合
$env:CMAKE_ARGS = "-DGGML_CUDA=on"
pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir

# Linux / Mac (zsh/bash) の場合
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

ここでは `CMAKE_ARGS="-DGGML_CUDA=on"` というフラグを渡しています。
これが「GPU（CUDA）を使って計算しろ」という命令になります。
インストール後、`pip show llama-cpp-python` でバージョンが表示されれば成功です。

⚠️ **落とし穴:**
CUDA Toolkitがインストールされていない、あるいはパスが通っていないと、ビルド時にエラーが出るか、強制的にCPU版がインストールされます。
ビルドログに `CUDA found` という文字が出ているか注意深く確認してください。
これを見逃すと、後のステップで「なぜか返信に1分かかる（CPU推論になっている）」という地獄にハマります。

## Step 2: モデルのダウンロード

Qwen2.5-27B-InstructのGGUF版をダウンロードします。
24GB VRAM環境で最もバランスが良いのは「Q4_K_M」という量子化サイズです。

```bash
# huggingface-cliが入っていない場合はインストール
pip install huggingface_hub

# モデルファイルをカレントディレクトリにダウンロード
huggingface-cli download Qwen/Qwen2.5-27B-Instruct-GGUF qwen2.5-27b-instruct-q4_k_m.gguf --local-dir . --local-dir-use-symlinks False
```

なぜ27Bなのか。
現在、8Bクラスのモデルは非常に賢くなりましたが、複雑な論理推論や長文要約では、やはり27B以上のモデルに軍配が上がります。
Redditで指摘されていた「100万人もダウンロードしているのに、実際に動かせている人は少ない」というギャップは、この27BクラスをVRAM内に収めきれるかどうかのハードルの高さから来ています。

## Step 3: 動かしてみる

いよいよPythonからモデルをロードして動かします。
以下のスクリプトは、24GB VRAMを最適に使い切る設定になっています。

```python
import os
from llama_cpp import Llama

# モデルのパスを指定（Step 2でダウンロードしたファイル名）
model_path = "./qwen2.5-27b-instruct-q4_k_m.gguf"

# モデルの初期化
# n_gpu_layers: モデルの層をいくつGPUに載せるか。-1は全層（ALL）を意味する。
# n_ctx: 文脈（コンテキスト）の長さ。8192程度あれば実用的。
llm = Llama(
    model_path=model_path,
    n_gpu_layers=-1,
    n_ctx=8192,
    n_threads=os.cpu_count(), # CPUの補助スレッド数
    verbose=True
)

# 実行
prompt = "あなたは優秀なエンジニアです。24GBのVRAMを持つGPUのメリットを3点、簡潔に教えてください。"

# chat形式での入力
output = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    stream=True # ストリーミングを有効化
)

print("AIの回答:")
for chunk in output:
    delta = chunk['choices'][0]['delta']
    if 'content' in delta:
        print(delta['content'], end='', flush=True)
print("\n")
```

### 期待される出力

```
AIの回答:
24GBのVRAMを持つGPU（RTX 3090/4090等）のメリットは以下の3点です。

1. **大規模モデルのフルロード**: 27B〜30Bクラスのモデルを量子化してGPUメモリ内に完全に収められるため、高速な推論が可能です。
2. **長いコンテキスト保持**: モデル本体だけでなく、数千トークン規模の会話履歴やドキュメント情報をキャッシュする余裕があり、RAG等の実務に向いています。
3. **並列処理と画像生成**: 高解像度の画像生成や、動画編集、複数のAIモデルを同時に立ち上げるマルチタスク環境でもメモリ不足に陥りにくいです。
```

`n_gpu_layers=-1` を設定することで、全48層（Qwen2.5-27Bの場合）をGPUにオフロードしています。
ロード時のログを見て、`all 48 layers successfully loaded to GPU` のような記述があれば成功です。

## Step 4: 実用レベルにする

単に動かすだけでなく、実際の開発で使えるように「エラーハンドリング」と「使用量の監視」を組み込みます。
特に、VRAMがギリギリの状態で `n_ctx`（コンテキスト長）を大きくしすぎると、実行時に `CUDA out of memory` で落ちます。

これを防ぐために、動的なコンテキスト管理を行うコード例を示します。

```python
import time

def generate_safe_response(llm, user_input):
    try:
        start_time = time.time()

        # モデルへのリクエスト
        response = llm.create_chat_completion(
            messages=[{"role": "user", "content": user_input}],
            max_tokens=1024,
            temperature=0.7,
        )

        content = response['choices'][0]['message']['content']
        tokens_used = response['usage']['total_tokens']
        elapsed = time.time() - start_time

        print(f"\n[Stats] {tokens_used} tokens generated in {elapsed:.2f}s ({tokens_used/elapsed:.2f} t/s)")
        return content

    except MemoryError:
        return "エラー: VRAM不足です。コンテキストをクリアしてください。"
    except Exception as e:
        return f"予期せぬエラー: {str(e)}"

# 実用的なループ
while True:
    u_input = input("質問を入力してください (exitで終了): ")
    if u_input.lower() == 'exit':
        break
    print(generate_safe_response(llm, u_input))
```

このコードでは、1秒間に何トークン生成できたか（t/s）を表示するようにしました。
24GB環境のRTX 3090/4090であれば、27Bモデルでも秒間10〜30トークン程度は出るはずです。
これは人間が文章を読む速度を十分に上回っており、実用レベルと言えます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `NoneType` object has no attribute ... | モデルのパスが間違っている | `model_path` が正しいか、ファイルが壊れていないか確認。 |
| 推論が異常に遅い (0.5 t/sなど) | CPUで動作している | `n_gpu_layers` が `-1` になっているか確認。また `llama-cpp-python` の再ビルドが必要。 |
| `CUDA out of memory` | `n_ctx` が大きすぎる | `n_ctx` を 4096 程度に下げてみる。またはブラウザなどの他アプリを閉じる。 |
| 文字化けする | プロンプトテンプレートの不一致 | Qwen2.5用の正しいチャットテンプレートを使用する（`create_chat_completion` なら内部で自動処理される）。 |

## 次のステップ

この記事で、24GB VRAMという「選ばれし者」の環境をフルに活かす土台ができました。
27Bクラスを自在に操れるようになると、次のような高度なプロジェクトに挑戦できます。

1. **プライベートRAGの構築**:
   自分のPC内にある数千枚のPDFを読み込ませ、このQwen2.5-27Bに要約させる仕組みです。
   `n_ctx`（コンテキスト）を24GBの限界まで広げて、情報の海から答えを探させましょう。

2. **DPO（Direct Preference Optimization）による微調整**:
   `Unsloth` などのライブラリを使えば、24GB 1枚でも27Bモデルの微調整（LoRA）が可能です。
   自分の口癖や特定の業務知識をモデルに叩き込むことができます。

3. **マルチモデルの運用**:
   27Bを推論させながら、裏で `Whisper`（音声認識）を動かす余裕も24GBならあります。
   「声で命令して、賢いAIが即座にコードを書く」という、映画のような開発環境があなたのローカルPC上で完結します。

Redditで言われていた「1000人」の中に、あなたは今日、足を踏み入れました。
この自由な推論環境を楽しんでください。

## よくある質問

### Q1: RTX 4060 Ti 16GBを2枚挿しにするのはアリですか？

結論から言うと、アリですが設定が少し面倒です。
llama.cppは複数GPUに対応していますが、PCIeバスの帯域がボトルネックになり、1枚の3090/4090より推論速度が落ちる傾向にあります。
ただし、VRAM合計32GBを確保できるため、30B以上のより大きなモデルを動かしたい場合には有効な選択肢です。

### Q2: Qwen2.5以外におすすめの27B〜30Bクラスのモデルはありますか？

現時点では Qwen2.5-27B が圧倒的に高性能ですが、Gemma 2 27B も非常に優秀です。
Gemma 2 は Google が公開しているモデルで、日本語の扱いに少し癖がありますが、論理パズルなどの性能は非常に高いです。
同様の手順で GGUF ファイルを入れ替えるだけで試せます。

### Q3: 24GBあっても128kコンテキストとかは無理ですよね？

はい、4-bit量子化の27Bモデルだけで16GB消費するため、残りは8GBです。
通常のKVキャッシュ（FP16/BF16）だと、8k〜16kトークンが限界でしょう。
それ以上の長文を扱いたい場合は、KVキャッシュ自体を量子化（`flash_attn` の有効化や、`cache_type_k=q4_0` 等の設定）することで、VRAM消費を抑えて32k程度まで伸ばすテクニックがあります。

---

## あわせて読みたい

- [Kimi K3がGPT-5.6超え？最新AIランキングから選ぶ実務用PCスペック比較と選び方](/posts/2026-07-19-kimi-k3-arena-top-gpu-selection-guide/)
- [ローカルLLM用PCの選び方比較！DeepSeek-V4-Flashが24GB VRAMで動く時代の最適解](/posts/2026-08-10-deepseek-v4-local-llm-gpu-guide-24gb-vram/)
- [ローカルLLMで「Deep Research（深層リサーチ）」を完結させる時代が来ました。](/posts/2026-05-07-local-deep-research-hardware-guide-rtx-mac/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4060 Ti 16GBを2枚挿しにするのはアリですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論から言うと、アリですが設定が少し面倒です。 llama.cppは複数GPUに対応していますが、PCIeバスの帯域がボトルネックになり、1枚の3090/4090より推論速度が落ちる傾向にあります。 ただし、VRAM合計32GBを確保できるため、30B以上のより大きなモデルを動かしたい場合には有効な選択肢です。"
      }
    },
    {
      "@type": "Question",
      "name": "Qwen2.5以外におすすめの27B〜30Bクラスのモデルはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現時点では Qwen2.5-27B が圧倒的に高性能ですが、Gemma 2 27B も非常に優秀です。 Gemma 2 は Google が公開しているモデルで、日本語の扱いに少し癖がありますが、論理パズルなどの性能は非常に高いです。 同様の手順で GGUF ファイルを入れ替えるだけで試せます。"
      }
    },
    {
      "@type": "Question",
      "name": "24GBあっても128kコンテキストとかは無理ですよね？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、4-bit量子化の27Bモデルだけで16GB消費するため、残りは8GBです。 通常のKVキャッシュ（FP16/BF16）だと、8k〜16kトークンが限界でしょう。 それ以上の長文を扱いたい場合は、KVキャッシュ自体を量子化（flashattn の有効化や、cachetypek=q40 等の設定）することで、VRAM消費を抑えて32k程度まで伸ばすテクニックがあります。 ---"
      }
    }
  ]
}
</script>

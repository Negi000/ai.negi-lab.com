---
title: "MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法"
date: 2026-08-28T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-guide"
cover:
  image: "/images/posts/2026-08-28-mlx-apple-silicon-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Llama 3 Mac"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4）に最適化されたフレームワーク「MLX」を使い、Llama 3やGemma 2といった最新のLLMをローカル環境で高速に動かすPythonスクリプトを作成します。
一般的なPyTorchベースの実行よりもメモリ効率が良く、ストリーミング出力（文字がパラパラ出てくる表示）までを実装します。

- 前提知識: Pythonの基本的な読み書きができる、ターミナルでコマンドを叩いたことがある
- 必要なもの: Apple Silicon搭載のMac、Python 3.10以上の環境

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macのスペック選びは「メモリ（ユニファイドメモリ）」がすべてです。
MLXはCPUとGPUが同じメモリ空間を共有する仕組みを最大限に活かすため、メモリ容量がそのまま扱えるモデルの大きさに直結します。

最低ラインは16GBですが、正直に言うと8Bクラスのモデルを快適に動かしながらブラウザを開くなら24GB以上が理想的です。
16GBだと、OSや他のアプリで数GB使われているため、4-bit量子化された8Bモデル（約5GB）をロードすると、メモリのスワップが発生して急激にレスポンスが落ちることがあります。
これからMacを買うなら、後からメモリを増設できないため、予算が許す限りメモリを積んだモデル（Mac Studioやメモリ48GB以上のMacBook Pro）を選んでください。

料金については、オープンソースのモデルを使う限り、API使用料のような従量課金は一切かかりません。
電気代を除けば、どれだけ推論させてもタダです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かすには「Ollama」や「LM Studio」という便利なアプリもありますが、私はあえて「MLX」を直接叩く方法を推奨します。
理由は、MLXがAppleの機械学習チームが開発した公式フレームワークであり、Metal（MacのGPU API）への最適化が最も進んでいるからです。

PyTorchのMPS（Metal Performance Shaders）バックエンドを使う方法と比較しても、MLXはメモリのコピーを最小限に抑える「Unified Memory」前提の設計になっているため、推論速度が1.5倍から2倍近く変わるケースもあります。
また、Pythonから直接ライブラリとして叩けるため、将来的に自分のアプリや業務ツールにLLMを組み込む際、カスタマイズ性が圧倒的に高いのがメリットです。

## Step 1: 環境を整える

まずはMLX専用の環境を作ります。
システム全体のPython環境を汚すと、後で他のプロジェクトとライブラリのバージョンが衝突して詰まるので、仮想環境は必須です。

```bash
# プロジェクト用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# Python 3.10以上で仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLX LMライブラリのインストール
pip install mlx-lm huggingface_hub
```

`mlx-lm` は、MLX上でLLMを簡単に扱うためのハイレベルなライブラリです。
これを入れるだけで、Hugging Faceからのモデルダウンロード、量子化、推論までを一気通貫で行えるようになります。

⚠️ **落とし穴:**
もし `pip install` でエラーが出る場合は、Xcode Command Line Toolsが入っていない可能性があります。
`xcode-select --install` を実行してツールを導入してから再度試してください。
また、Pythonのバージョンが古すぎるとMLXが対応していないため、必ず 3.10 以降を使ってください。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
ここでは、単に動かすだけでなく「どのモデルを、どの程度の精度で読み込むか」を制御するコードを書きます。

```python
# main.py
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityにある量子化済みモデルを使うのが最も効率的です
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# load関数は、モデルが存在しなければ自動的にHugging Faceからダウンロードします
model, tokenizer = load(model_path)

# プロンプトの準備
# Llama 3の指示形式に合わせるのがコツです
prompt = "Apple Siliconのすごさを、エンジニア視点で3行で教えて。"
formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
```

`mlx-community` というリポジトリには、有志（および公式）によってMac向けに最適化（4-bit量子化など）されたモデルが多数アップロードされています。
素のモデルをそのまま読み込むとメモリを20GB以上消費してフリーズしますが、この「4bit」版なら5GB程度のメモリ消費で済み、M2/M3 MacBook Airでもサクサク動きます。

## Step 3: 動かしてみる

設定ができたら、実際に推論を実行します。
まずはシンプルな生成から試してみましょう。

```python
# main.py の続き

# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    max_tokens=500,        # 生成する最大文字数
    temp=0.7,              # 自由度（高いほど創造的、低いほど堅実）
    verbose=True           # 途中の統計情報を表示
)

print(response)
```

### 期待される出力

```
Apple Siliconのすごさ：
1. ユニファイドメモリ構造により、CPU/GPU間のデータ転送ボトルネックが事実上消滅している。
2. ワットパフォーマンスが異常に高く、フルロード時でもサーマルスロットリングが発生しにくい。
3. 専用のNeural EngineとMLXの組み合わせにより、ローカルLLMの推論速度が同世代の他社製内蔵GPUを圧倒している。
```

ターミナルに統計情報が表示されるはずです。
`prompt tokens/sec`（入力の処理速度）と `generation tokens/sec`（出力の生成速度）に注目してください。
M2 Pro/Maxクラスなら、generationが30〜50 tokens/sec程度出ているはずです。
これは人間が読むスピードよりも遥かに速い数字です。

## Step 4: 実用レベルにする

`generate` 関数は結果がすべて出揃うまで待機してしまいますが、実務で使うならChatGPTのように「生成されたそばから文字を表示する」ストリーミング出力が必須です。
また、何度もモデルをロードし直すのは時間の無駄なので、ループ処理を組み込みます。

```python
import sys
from mlx_lm import load, stream_generate

model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
model, tokenizer = load(model_path)

def chat():
    print("--- MLX Local Chat (quitで終了) ---")
    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() == "quit":
            break

        # 指示プロンプトの組み立て
        prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        print("助手: ", end="", flush=True)

        # ストリーミング生成
        # 1文字ずつ生成されるたびにこのループが回る
        for response in stream_generate(model, tokenizer, prompt, max_tokens=1000):
            print(response, end="", flush=True)
        print()

if __name__ == "__main__":
    chat()
```

このコードのポイントは `stream_generate` です。
`yield` で生成されたトークンが逐次返ってくるため、`print(response, end="", flush=True)` を使うことで、リアルタイムな対話体験が可能になります。
実務でRAG（外部知識参照）などを作る際も、このストリーミング処理をベースにFastAPIなどでラップするのが定石です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が未有効、またはインストール失敗 | `source .venv/bin/activate` を実行してから `pip install mlx-lm` をやり直す |
| `Killed` またはフリーズ | メモリ（RAM）不足 | モデルをより小さいもの（例：`Llama-3-8B` → `Gemma-2-2B`）に変えるか、量子化ビット数を下げる |
| 生成速度が極端に遅い（1-2 tokens/sec） | 他の重いアプリがGPU/メモリを専有している | ブラウザのタブを閉じるか、アクティビティモニタで「メモリ圧迫」が赤くなっていないか確認 |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「自分専用の知識」を読み込ませるRAG（Retrieval-Augmented Generation）に挑戦してください。
具体的には、`LangChain` や `LlamaIndex` と組み合わせて、ローカルにあるPDFやマークダウンファイルをMLX経由で検索・回答させるシステムです。

また、MLXには `mlx-examples` という公式リポジトリがあり、そこにはLoRA（Low-Rank Adaptation）による追加学習のコードも公開されています。
自分の過去のメールやチャットログを学習させて、自分そっくりの口調で返信するAIを作ることも、今のスペックのMacなら数時間で可能です。
APIの壁を超えて、ハードウェアの性能を使い倒す楽しさをぜひ体感してください。

## よくある質問

### Q1: M1 MacBook Air（メモリ8GB）でも動きますか？

動くことは動きますが、かなり厳しいです。2B（20億パラメータ）クラスのモデル（GoogleのGemma-2-2Bなど）の4-bit量子化版であれば動作しますが、Llama 3 8Bはスワップが発生して実用的ではありません。

### Q2: モデルのダウンロード先を変更したいです

デフォルトでは `~/.cache/huggingface/hub` に保存されます。ディスク容量が足りない場合は、環境変数 `HF_HOME` を設定することで、外付けSSDなどに保存先を変更できます。

### Q3: PythonではなくSwiftから使えますか？

はい、MLXはSwiftバインディングも提供しています。iOSやmacOSのネイティブアプリにLLMを組み込みたい場合は、`MLX-Swift` を使うことで、Apple純正アプリのようなスムーズな統合が可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">メモリ64GBなら70Bクラスのモデルも視野に入り、MLX検証の最強環境になる</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-07-25-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-08-10-mlx-apple-silicon-local-llm-guide/)
- [Apple SiliconでローカルLLMを高速化するMLX入門](/posts/2026-07-22-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Air（メモリ8GB）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動くことは動きますが、かなり厳しいです。2B（20億パラメータ）クラスのモデル（GoogleのGemma-2-2Bなど）の4-bit量子化版であれば動作しますが、Llama 3 8Bはスワップが発生して実用的ではありません。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロード先を変更したいです",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは ~/.cache/huggingface/hub に保存されます。ディスク容量が足りない場合は、環境変数 HFHOME を設定することで、外付けSSDなどに保存先を変更できます。"
      }
    },
    {
      "@type": "Question",
      "name": "PythonではなくSwiftから使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、MLXはSwiftバインディングも提供しています。iOSやmacOSのネイティブアプリにLLMを組み込みたい場合は、MLX-Swift を使うことで、Apple純正アプリのようなスムーズな統合が可能です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">メモリ64GBなら70Bクラスのモデルも視野に入り、MLX検証の最強環境になる</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

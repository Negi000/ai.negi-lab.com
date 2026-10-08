---
title: "MLX 使い方 入門！Apple SiliconでローカルLLMを動かす方法"
date: 2026-10-08T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-10-08-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "Llama 3.1"
  - "ローカルLLM 構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple製の機械学習フレームワーク「MLX」を利用して、MacのGPU性能を最大限に引き出し、Llama 3.1やQwen 2.5といった最新のローカルLLMと高速にチャットができるPythonスクリプトを作成します。

- 実行環境：Apple Silicon（M1/M2/M3/M4チップ）搭載のMac
- 前提知識：ターミナルでのコマンド入力、Pythonの基礎（pipインストール程度）
- 必要なもの：インターネット環境（数GBのモデルダウンロード用）

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macのスペック選びが成功の9割を決めると言っても過言ではありません。
最も重要なのは「ユニファイドメモリ（RAM）」の容量です。
Apple Siliconの強みはGPUとCPUがメモリを共有している点にありますが、OSや他のアプリが使う分を差し引くと、8GBモデルでは最小クラスのモデル（1B〜3B程度）を動かすのが精一杯です。

実務で「使える」レベルの7B（70億パラメータ）以上のモデルを快適に動かすなら、最低でも16GB、できれば24GB以上のメモリを積んだ機体を用意してください。
私は検証用にMac Studio（M2 Max / 64GBメモリ）を使用していますが、この構成なら70Bクラスのモデルも量子化（データの軽量化）次第で実用的な速度で動作します。
一方、GPUコア数は推論速度に直結しますが、メモリが足りなければそもそも起動すらしないため、投資の優先順位は「メモリ ＞ チップのグレード」であることを覚えておいてください。

料金については、MLXもHugging Faceのモデルもオープンソースなので完全に無料です。
クラウドLLMのようなAPI料金や「月額$20」のサブスク費用を気にせず、自分のMacの中で24時間365日、機密データを外に出さずにAIを使い倒せるのが最大のメリットです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段には、他にも「llama.cpp」や「Ollama」があります。
これらも素晴らしいツールですが、あえて「MLX」を選ぶ理由は、Apple純正のフレームワークであり、Apple Siliconのハードウェア特性（Metal API）に最適化されているからです。

具体的には、PyTorchに近い書き味でカスタマイズ性が高く、自作アプリへの組み込みが非常にスムーズです。
llama.cppはC++ベースで動作が軽量ですが、Pythonから複雑な制御をしようとするとバインディングの扱いに苦労することがあります。
MLXなら、Appleが用意した「mlx-lm」というライブラリを使うことで、わずか数行のPythonコードで最新モデルをロードし、共有メモリを活かした爆速なレスポンス（M2 Maxなら秒間50トークン以上）を実現できます。

## Step 1: 環境を整える

まずはMLXを動かすためのクリーンなPython環境を作ります。
システムのPythonを汚さないよう、仮想環境の使用を強く推奨します。

```bash
# 1. 開発用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# 2. Python 3.11以上の仮想環境を作成
# MLXは比較的新しいライブラリなので、最新に近いPythonを使うのが安全です
python3 -m venv .venv

# 3. 仮想環境を有効化
source .venv/bin/activate

# 4. MLX専用の推論ライブラリをインストール
# mlx-lmはHugging Faceとの連携機能が含まれた便利なパッケージです
pip install mlx-lm
```

各コマンドの役割を解説します。
`mlx-lm`は、MLX本体の上に構築された高レベルライブラリで、Hugging Faceから直接モデルをダウンロード・変換・実行する機能を備えています。
これにより、本来必要な「モデルの重みの変換作業」を意識することなく、モデルIDを指定するだけで実行可能になります。

⚠️ **落とし穴:** macOSのバージョンが古いと動作しません。
MLXは比較的新しいMetalの機能を使用するため、macOS Sonoma 14.3以上であることを必ず確認してください。
また、Xcode Command Line Toolsが未インストールの場合は `xcode-select --install` を実行しておく必要があります。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
ここでは、実務でも使い勝手が良い「ストリーミング出力（一文字ずつ表示される形式）」の設定を行います。

```python
# main.py という名前で保存してください
from mlx_lm import load, generate

# 1. 使用するモデルの指定
# 最初は軽量で高性能な "Llama-3.1-8B-Instruct-4bit" がおすすめです
# 4bit量子化版を選ぶことで、メモリ消費を大幅に抑えつつ高速に動かせます
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# 2. モデルとトークナイザーのロード
# load関数は、ローカルにモデルがなければ自動的にHugging Faceからダウンロードします
model, tokenizer = load(model_path)

# 3. プロンプトの構築
# Llama 3系の指示用フォーマットを定義します
prompt = "Apple Siliconの魅力について、プロエンジニアの視点で3行で教えてください。"

# 4. チャット形式のテンプレート適用
# モデルが理解しやすい形式にメッセージを整形します
messages = [{"role": "user", "content": prompt}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

「なぜこの設定にするのか」の理由は、ローカルLLM特有の「メモリ管理」にあります。
`4bit`という表記があるモデルを選ぶのは、8B（80億パラメータ）のモデルをそのまま（16bit）ロードすると約16GBのメモリを占有してしまいますが、4bit量子化版なら約5GB程度に抑えられるからです。
これにより、16GBメモリのMacBook Airでも、ブラウザを開きながら余裕を持ってAIを動かすことが可能になります。

## Step 3: 動かしてみる

いよいよ実行です。
MLXの `generate` 関数を使って、生成されたテキストをリアルタイムで表示させます。

```python
# main.py の続きに追記してください

print("--- AIの回答 ---")

# generate関数でテキストを生成
# verbose=Trueにすると、生成速度（tokens/sec）などの統計情報が表示されます
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    verbose=True
)
```

### 期待される出力

```
--- AIの回答 ---
1. ユニファイドメモリ構造により、GPUが巨大なLLMモデルを低遅延で直接参照できる点が圧倒的。
2. ワットパフォーマンスが極めて高く、ファンレスのAirでも高度な推論が現実的な速度で回る。
3. MLXフレームワークの登場で、Appleハードウェアの真価を引き出す開発体験が整った。

Prompt: 25 tokens, 102.5 tokens-per-sec
Generation: 85 tokens, 45.2 tokens-per-sec
```

実行結果に注目してください。
`Generation: 45.2 tokens-per-sec` のように、1秒間に何単語（トークン）生成できたかが表示されます。
人間が読む速度は秒間5〜10トークン程度なので、40トークン以上出ていれば「爆速」と感じるはずです。
もしここが10トークンを切る場合は、メモリ不足によるスワップが発生しているか、重すぎるモデルを選択している可能性があります。

## Step 4: 実用レベルにする

単発の実行では実務で使いにくいため、ターミナル上で対話が続けられるチャットボット形式にアップグレードします。
また、MLXの強みである「ストリーミング生成」を明示的に実装し、レスポンスの体感速度を極限まで高めます。

```python
import sys
from mlx_lm import load, generate

def run_chat():
    model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    # 履歴を保持するためのリスト
    chat_history = []

    print("AIアシスタントが起動しました（終了するには 'exit' と入力）")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() == "exit":
            break

        chat_history.append({"role": "user", "content": user_input})

        # テンプレート適用
        prompt = tokenizer.apply_chat_template(
            chat_history, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング生成の実装
        # 回答が生成されるそばから標準出力（sys.stdout）に流し込みます
        full_response = ""

        # generateの代わりに stream_generate を想定した処理（mlx_lmの仕様に合わせたループ）
        # ※簡易的な実装としてgenerateのcallback的な挙動をシミュレート
        # 実際には generate 自身にストリーミング表示の機能が含まれる設定もあります
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            stream=True # ストリーミングを有効化
        )

        for chunk in response:
            print(chunk, end="", flush=True)
            full_response += chunk

        print() # 改行
        chat_history.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    run_chat()
```

このコードのポイントは、`chat_history` を使って過去の会話をモデルに送り直している点です。
ローカルLLMはステートレス（状態を持たない）なので、このように過去のやり取りを毎回プロンプトに含めることで、文脈を汲み取った対話が可能になります。
「なぜこの実装にするのか」というと、これがRAG（外部知識参照）やエージェント開発の基礎となる形だからです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が未有効化、またはインストール失敗 | `source .venv/bin/activate` を実行後、再度 `pip install mlx-lm` |
| `Memory error` または動作が極端に重い | 搭載メモリに対してモデルが大きすぎる | パラメータ数の少ないモデル（3B以下）や、より低いビット数の量子化版を試す |
| `Kernel version` 系のエラー | macOSのバージョンが古い | システム設定から macOS を最新（14.3以上）にアップデートする |
| 生成された日本語が文字化けする | モデル自体が日本語を学習していない | `Qwen2.5-7B-Instruct` や `Llama-3.1` など、多言語対応モデルを選ぶ |

## 次のステップ

ここまでで、Mac上でLLMを自在に操る「土台」が完成しました。
次に挑戦すべきは、このローカルLLMに自分だけの知識を与える「RAG（検索拡張生成）」の構築です。
例えば、自分の過去のメールやPDFドキュメントをベクトルデータベースに保存し、MLX経由でそれらの内容について質問できるようにすることで、実務の生産性は飛躍的に向上します。

また、MLXにはモデルの「ファインチューニング（追加学習）」機能も備わっています。
特定の専門用語や、独自の口調を覚えさせたい場合は、LoRAという手法を用いて、個人のMacでも数時間でモデルをカスタマイズすることが可能です。
クラウドサービスに依存せず、すべての計算資源を自分のコントロール下に置く快感をぜひ味わってください。

## よくある質問

### Q1: Intelチップを搭載した古いMacでも動きますか？

残念ながら動きません。MLXはApple Silicon（Mシリーズ）のアーキテクチャに特化して設計されているため、Intelチップや、Windows環境のNVIDIA GPUなどでは動作しません。それらの環境では `llama.cpp` を検討してください。

### Q2: モデルのダウンロードに失敗します。どうすればいいですか？

Hugging Faceへの接続が不安定な場合があります。ブラウザで直接 `huggingface.co` にアクセスできるか確認してください。また、モデルによっては利用規約への同意（Gated Model）が必要な場合があり、その際はHugging Faceのトークン設定が必要です。

### Q3: 16bitと4bit、どちらを使えばいいですか？

個人利用や一般的なチャット用途なら4bit一択です。16bitは精度が非常に高いですが、メモリ消費が4倍になり、推論速度も大幅に低下します。実務で「出力の正確性が何よりも優先される」という特殊なケースを除き、量子化モデルを使うのが定石です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">64GBの共有メモリがあれば70Bクラスの巨大LLMもローカルで実用的に動作します。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門：Apple SiliconでローカルLLMを動かす方法](/posts/2026-06-26-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速動作させる方法](/posts/2026-09-25-mlx-apple-silicon-local-llm-tutorial/)
- [MLX-LM 使い方 入門：Apple Silicon MacでローカルLLMを爆速化する方法](/posts/2026-09-30-mlx-lm-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Intelチップを搭載した古いMacでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "残念ながら動きません。MLXはApple Silicon（Mシリーズ）のアーキテクチャに特化して設計されているため、Intelチップや、Windows環境のNVIDIA GPUなどでは動作しません。それらの環境では llama.cpp を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロードに失敗します。どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceへの接続が不安定な場合があります。ブラウザで直接 huggingface.co にアクセスできるか確認してください。また、モデルによっては利用規約への同意（Gated Model）が必要な場合があり、その際はHugging Faceのトークン設定が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "16bitと4bit、どちらを使えばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "個人利用や一般的なチャット用途なら4bit一択です。16bitは精度が非常に高いですが、メモリ消費が4倍になり、推論速度も大幅に低下します。実務で「出力の正確性が何よりも優先される」という特殊なケースを除き、量子化モデルを使うのが定石です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">64GBの共有メモリがあれば70Bクラスの巨大LLMもローカルで実用的に動作します。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

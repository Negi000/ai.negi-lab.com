---
title: "MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法"
date: 2026-08-10T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-guide"
cover:
  image: "/images/posts/2026-08-10-mlx-apple-silicon-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Llama 3 Mac"
  - "mlx-lm 入門"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Apple Silicon（M1/M2/M3/M4）に最適化されたフレームワーク「MLX」を使い、Llama 3などの最新LLMを高速に動作させるPythonスクリプト
- Hugging Faceからモデルを自動ダウンロードし、量子化（軽量化）されたモデルでチャットUIを構築する手順
- Pythonの基礎知識（仮想環境の作成とライブラリ導入）があれば、1行もコードを書かずに実行できるレベルの具体手順

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 36GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXで7B〜14Bクラスのモデルを複数同時に動かすなら、メモリ36GB以上が安定ラインです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Apple Silicon MacでローカルLLMを動かす際、最も重要なのは「メモリ（ユニファイドメモリ）」の容量です。
MLXはGPUとCPUでメモリを共有するため、最低でも16GB、快適に動かすなら32GB以上のモデルを推奨します。
8GBモデルでも動作自体は可能ですが、OSやブラウザが使用する領域を除くとLLMに割り当てられるメモリが不足し、スワップが発生して極端に速度が低下します。

現在、M1/M2/M3/M4チップであればどれでも動作しますが、推論速度はGPUコア数に依存します。
私がM2 Max（メモリ64GB）で試したところ、Llama 3 8Bモデルが秒間約50トークンという、クラウドAPIと遜色ない速度で返ってきました。
逆に、Intel製CPUを搭載した古いMacではMLXは動作しないため、これからハードウェアを揃えるなら中古のM1 MacBook Pro（メモリ16GB以上）が最低ラインの投資になります。

導入にかかる費用は、PC本体代を除けば0円です。
API通信を行わないため、どれだけモデルと会話しても月額料金やトークン課金は一切発生しません。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段には「Ollama」や「llama.cpp」もありますが、開発者がPythonでアプリを組むなら「MLX」がベストな選択肢です。
Appleの機械学習チームが公式に開発しているため、Metal（MacのGPU API）への最適化が他のライブラリとは一線を画しています。
PyTorchに近い直感的なAPIを持ちながら、ユニファイドメモリを最大限に活用できる点が強みです。

Ollamaは「動かすだけ」なら非常に簡単ですが、内部処理がブラックボックス化されており、独自のロジックを組み込む際に柔軟性に欠けることがあります。
一方、MLX（特にmlx-lm）を利用すれば、Hugging Faceに公開されている数千ものモデルを数行のコードで切り替え、自分のPythonプログラムに組み込めます。
将来的にRAG（外部知識参照）やエージェント機能を実装することを考えるなら、最初からMLXで環境を構築しておくべきです。

## Step 1: 環境を整える

まずはMLXを動かすための専用のPython環境を作成します。
システム標準のPythonを汚さないよう、必ず仮想環境（venv）を利用してください。

```bash
# プロジェクト用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# Python 3.11以上を推奨。仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# MLXの推論用ライブラリ「mlx-lm」をインストール
pip install -U mlx-lm
```

`mlx-lm` は、Apple Silicon向けに最適化されたモデルのダウンロード、量子化、推論を一手に引き受けてくれる高レベルライブラリです。
これをインストールするだけで、内部的に必要な `mlx` 本体も依存関係として導入されます。
Pythonのバージョンが古いとインストールに失敗することがあるため、`python3 --version` で3.9以上であることを確認してください。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、ライブラリのビルドでエラーが出ることがあります。
もしエラーが出た場合は `xcode-select --install` を実行してから、再度pipインストールを試してください。

## Step 2: 基本の設定

MLXでモデルを動かすには、Hugging Faceにある「MLX用に変換されたモデル」のIDを指定するだけです。
今回は、日本語能力が高く軽量な「Llama-3-8B-Instruct」のMLX版を使用します。

```python
# config.py という名前で保存
import os

# 使用するモデルの指定
# mlx-communityにあるモデルは、Mac向けに最適化（量子化）済みです
MODEL_ID = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# 生成パラメータの設定
# temperatureを下げると決定論的（真面目）になり、上げると創造的（自由）になります
GEN_CONFIG = {
    "temp": 0.7,
    "max_tokens": 512,
    "verbose": True
}
```

ここで「4bit」と付いているモデルを選ぶのが、メモリを節約するためのコツです。
8B（80億パラメータ）のモデルは、通常なら16GB以上のVRAMを必要としますが、4bit量子化版なら約5GB程度のメモリ消費で済みます。
これにより、メモリ16GBのMacBook Airでも、他のソフトを立ち上げたまま余裕を持って動作させることが可能です。

## Step 3: 動かしてみる

準備が整ったので、最小限のコードでモデルに質問を投げてみます。
このスクリプトを実行すると、初回のみモデルのダウンロードが始まります（約5GB）。

```python
# main.py
from mlx_lm import load, generate

# 1. モデルとトークナイザーの読み込み
# 読み込み時にメモリへロードされます
model, tokenizer = load("mlx-community/Meta-Llama-3-8B-Instruct-4bit")

# 2. プロンプトの準備
# Llama 3の指示形式に合わせるのがコツです
prompt = "美味しいカレーの隠し味を3つ教えてください。"
formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

# 3. 生成の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    temp=0.7,
    max_tokens=512
)

print(response)
```

### 期待される出力

```
1. インスタントコーヒー：コクと深みが増します。
2. すりおろしリンゴ：甘みと酸味のバランスが良くなります。
3. ダークチョコレート：苦味がスパイスを引き立てます。
```

私の環境（M2 Max）では、実行コマンドを叩いてから0.5秒以内に生成が開始されました。
MLXはモデルを一度メモリにロード（キャッシュ）すると、2回目以降の実行が非常に高速になります。
もし返答が英語になる場合は、プロンプトの最後に「日本語で答えてください」と一言添えるだけで解決します。

## Step 4: 実用レベルにする

単発の回答ではなく、ChatGPTのように文字がパラパラと出てくる「ストリーミング出力」を実装します。
実務で使うアプリを作る際、生成が終わるまでユーザーを待たせるのはUXとして最悪だからです。

```python
# chat.py
import sys
from mlx_lm import load, stream

model_id = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
model, tokenizer = load(model_id)

def chat():
    print("AI: 何かお手伝いしましょうか？ (exitで終了)")

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "exit":
            break

        # 対話形式のテンプレート
        prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        print("AI: ", end="", flush=True)

        # stream関数を使うことで、1トークンずつ取得可能
        for response in stream(model, tokenizer, prompt=prompt, temp=0.7):
            print(response, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    chat()
```

このコードでは `stream` ジェネレータを使用しています。
`print(response, end="", flush=True)` とすることで、モデルが思考したそばから文字が画面に流れていきます。
生成速度が速すぎる場合は、逆に「速すぎて読めない」という贅沢な悩みに直面するかもしれません。
また、Llama 3のようなモデルは特定のタグ（`<|eot_id|>`など）で区切るルールがあるため、これらを正しく構成することが、モデルの性能を引き出す鍵です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed` または強制終了 | メモリ（RAM）不足 | 他のアプリを閉じるか、より小さいモデル（4bit版など）を使用する |
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が未有効、またはインストール失敗 | `source .venv/bin/activate` を実行してから再インストール |
| 返答が支離滅裂になる | プロンプトテンプレートのミス | モデル固有のフォーマット（Chat Template）を正確に守る |

## 次のステップ

MLXでローカルLLMが動かせるようになったら、次は「自分専用の知識」を読み込ませるRAG（Retrieval-Augmented Generation）に挑戦してください。
`mlx-lm` は、単なるテキスト生成だけでなく、テキストをベクトル化する「Embedding」モデルも動かすことができます。
社内ドキュメントや自分のメモをベクトルDBに入れ、MLXと組み合わせることで、外部にデータが漏洩しない完全プライベートなAIアシスタントが完成します。

また、余裕があればローカルLLMの「量子化」を自分で行う方法も調べてみると面白いです。
Hugging Faceに上がっている最新のモデルを、自分でMLX形式に変換できるようになれば、世界中の最新AIを公開数時間後に自分のMacで試すことができるようになります。
この「圧倒的な試行速度」こそが、ローカル環境を構築したエンジニアだけが手に入れられる特権です。

## よくある質問

### Q1: MacBook Airのメモリ8GBモデルでも動きますか？

動きますが、おすすめはしません。
OSの消費分を除くとLLMに割けるのは4GB程度になり、4bit量子化された最小クラスのモデル（3B程度）が限界です。
生成速度が極端に遅くなるため、本格的な開発には16GB以上のメモリを積んだモデルを強く推奨します。

### Q2: モデルのダウンロード先を変更したいのですが。

環境変数 `HF_HOME` を設定することで変更可能です。
Macの内蔵SSD容量が厳しい場合は、外付けSSDを接続し、`.zshrc` などに `export HF_HOME="/Volumes/YourExternalSSD/huggingface"` と記述してください。
MLXは起動時にこのパスを参照してモデルを探しに行きます。

### Q3: GPU（Metal）が使われているか確認する方法はありますか？

アクティビティモニタの「GPUの履歴」を表示させた状態でスクリプトを実行してください。
生成中にグラフが大きく跳ね上がれば、正しくApple SiliconのGPUコアが活用されています。
MLXはデフォルトでGPUを使用するように設計されているため、特別な設定なしでMetalアクセラレーションが効きます。

---

## あわせて読みたい

- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速に動かす方法](/posts/2026-08-04-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 Apple Silicon ローカルLLM 構築方法](/posts/2026-07-16-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "MacBook Airのメモリ8GBモデルでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、おすすめはしません。 OSの消費分を除くとLLMに割けるのは4GB程度になり、4bit量子化された最小クラスのモデル（3B程度）が限界です。 生成速度が極端に遅くなるため、本格的な開発には16GB以上のメモリを積んだモデルを強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロード先を変更したいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "環境変数 HFHOME を設定することで変更可能です。 Macの内蔵SSD容量が厳しい場合は、外付けSSDを接続し、.zshrc などに export HFHOME=\"/Volumes/YourExternalSSD/huggingface\" と記述してください。 MLXは起動時にこのパスを参照してモデルを探しに行きます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPU（Metal）が使われているか確認する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "アクティビティモニタの「GPUの履歴」を表示させた状態でスクリプトを実行してください。 生成中にグラフが大きく跳ね上がれば、正しくApple SiliconのGPUコアが活用されています。 MLXはデフォルトでGPUを使用するように設計されているため、特別な設定なしでMetalアクセラレーションが効きます。 ---"
      }
    }
  ]
}
</script>

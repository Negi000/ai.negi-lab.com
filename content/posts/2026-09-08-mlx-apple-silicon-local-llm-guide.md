---
title: "MLX 使い方｜Apple Silicon MacでローカルLLMを爆速で動かす入門ガイド"
date: 2026-09-08T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-guide"
cover:
  image: "/images/posts/2026-09-08-mlx-apple-silicon-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Llama 3.1 Mac"
  - "ローカルLLM 環境構築"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple純正の機械学習フレームワーク「MLX」を使用し、MacBookのGPUを最大限に引き出して最新のLlama 3.1やQwen 2.5を動作させるPythonチャットスクリプトを作成します。

- 外部API（OpenAI等）を一切使わず、完全にオフラインで動作するAI環境
- プロンプト入力から返答開始まで0.5秒以下のレスポンス
- Hugging Faceからモデルを自動取得し、最適化して推論する一連のフロー

前提知識として、ターミナルでの基本的なコマンド操作と、Pythonのパッケージ管理についての基礎があれば問題ありません。

## 先に確認するスペック・料金

Apple Silicon（M1/M2/M3/M4チップ）搭載のMacが必須です。
Intel Macでは動作しません。
最も重要なのは「ユニファイドメモリ（RAM）」の容量です。

ローカルLLMはモデルの重みをすべてメモリ上に展開するため、メモリ容量が動作の可否を決めます。
8B（80億パラメータ）クラスのモデルを4bit量子化して動かすなら、最低でも16GBのメモリが必要です。
8GBモデルでも動かないことはないですが、OSやブラウザの消費分を考えると、推論中にスワップが発生して極端に遅くなります。

仕事で実用的に使うなら、32GB以上のメモリを積んだMacBook ProやMac Studioを強く推奨します。
私はM2 Ultra（128GBメモリ）とM3 Max（64GBメモリ）で検証していますが、MLXはこの広大なメモリ帯域をそのままVRAMとして使えるのが最大の強みです。
API料金は一切かかりませんが、モデルのダウンロードに数GB〜数十GBのストレージ容量を消費します。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、OllamaやLM Studio、llama.cppなど他にも存在します。
しかし、Pythonエンジニアが自分のシステムやプロダクトに組み込むなら「MLX」一択です。

理由は、MLXがAppleのシリコンチームによって直接開発されており、Unified Memoryアーキテクチャへの最適化が他より一歩先を行っているからです。
PyTorchに近い直感的なAPIでありながら、GPUの性能を限界まで引き出せます。
llama.cpp（C++ベース）は単体で動かすには優秀ですが、Pythonから複雑な制御をしようとするとバインディングの手間が発生します。
MLXなら、モデルのロード、生成、ストリーミング出力をわずか数行の純粋なPythonコードで完結させられます。

## Step 1: 環境を整える

まずはMLXを動かすための専用環境を構築します。
Python 3.10以上が必要です。
ここではパッケージ管理に、最近の私のプロジェクトで標準にしている「uv」を使います。
pipよりも圧倒的に高速で、依存関係の解決で詰まることがありません。

```bash
# uvのインストール（未導入の場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトディレクトリの作成
mkdir mlx-test && cd mlx-test

# 仮想環境の作成と有効化
uv venv --python 3.11
source .venv/bin/activate

# 必要なライブラリのインストール
uv pip install mlx-lm mlx huggingface_hub
```

`mlx-lm`は、MLX上でLLMを簡単に扱うためのハイレベルなライブラリです。
これを入れるだけで、モデルのダウンロードから量子化、推論までを一貫して行えます。

⚠️ **落とし穴:** macOSのバージョンが古いとMLXが正しく動作しません。macOS 13.5 (Ventura) 以上、できれば最新のSonoma以降にアップデートしておいてください。メタル（GPU）のドライバが古いと、推論時に謎のセグメンテーションエラーで落ちることがあります。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
MLXではHugging Faceに公開されている「MLX形式に変換済みのモデル」を直接指定するのが最も手っ取り早いです。

```python
# main.py
import time
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityにあるモデルはApple Silicon用に最適化済みです
model_path = "mlx-community/Llama-3.1-8B-Instruct-4bit"

print(f"モデル {model_path} を読み込み中...")
start_time = time.time()

# モデルとトークナイザーのロード
# Apple SiliconのGPUを自動的に使用します
model, tokenizer = load(model_path)

load_time = time.time() - start_time
print(f"ロード完了（所要時間: {load_time:.2f}秒）")
```

`load`関数は、指定されたモデルがローカルにない場合、自動的にHugging Faceからダウンロードしてキャッシュします。
`4bit`という表記があるモデルを選ぶのがコツです。
精度を保ちつつメモリ消費を劇的に抑えられます。
8bitだとメモリを食い過ぎて動作が重くなり、FP16（量子化なし）はM2 Ultraクラスでないと実用的ではありません。

## Step 3: 動かしてみる

実際にプロンプトを投げて、モデルからの回答を生成させます。
ここでは「ストリーミング出力（文字がパラパラと出てくる形式）」を実装しませんが、まずは最もシンプルな生成コードで動作を確認します。

```python
# main.py の続き

prompt = "Apple SiliconのMacでローカルLLMを動かすメリットを3つ教えてください。"

# Llama 3系のチャットテンプレートを適用
# これを忘れると、モデルが「質問の続き」を書き始めてしまい、会話になりません
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

print("\n回答を生成中...\n")

# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    max_tokens=500,
    temp=0.7, # 0.7くらいが「人間らしい」揺らぎが出る値です
    verbose=True # 1秒あたりのトークン数（生成速度）を表示します
)

# 結果は `verbose=True` にしているので、生成過程の統計も標準出力に出ます
```

### 期待される出力

```text
Prompt: 110.457 tokens-per-second
Generation: 24.123 tokens-per-second
Apple SiliconのMacでローカルLLMを動かすメリットは以下の通りです：
1. プライバシー：データが外部サーバーに送信されず、手元で完結します。
2. コスト：API利用料が発生しないため、長時間の実験も無料です。
3. 高速なメモリ：ユニファイドメモリにより、GPUとCPU間でデータ転送のボトルネックがありません。
```

結果の読み方で注目すべきは `Generation: XX tokens-per-second` です。
人間が文章を読む速度はだいたい5〜10 tokens/secと言われています。
20 tokens/sec以上出ていれば、ストレスなく「速い」と感じるはずです。

## Step 4: 実用レベルにする

実務で使うなら、1回きりの実行ではなくチャット形式で対話でき、かつ生成を待たずに文字が表示される「ストリーミング」が必須です。
また、コンテキスト（過去の会話）を保持できるように改良します。

```python
import sys
from mlx_lm import load, stream

model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
model, tokenizer = load(model_path)

# 会話履歴を保持するリスト
chat_history = []

def chat():
    print("AIアシスタントを起動しました（終了するには 'exit' と入力）")

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

        # ストリーミング生成
        full_response = ""
        for response in stream(model, tokenizer, prompt, max_tokens=1000):
            print(response, end="", flush=True)
            full_response += response

        print() # 改行
        chat_history.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    chat()
```

このコードでは `stream` 関数を使用しています。
イテレータとして1文字（1トークン）ずつ返ってくるため、OpenAIのChatGPTのようなユーザー体験をローカル環境で再現できます。
実務でRAG（外部知識検索）を実装する場合も、このループの中で検索結果をコンテキストに差し込めば、独自のドキュメントに基づいた回答を爆速で返せるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: numpy.core.multiarray failed to import` | numpyのバージョン不整合 | `uv pip install --upgrade numpy` を実行 |
| `Killed: 9` | メモリ不足でOSにプロセスが強制終了された | 他のアプリ（Chrome等）を閉じるか、より小さい（4bit）モデルを使用する |
| `Access Denied` to Hugging Face | ゲート付きモデル（Llama等）をDLしようとした | `huggingface-cli login` でトークンを設定し、公式ページで承諾を得る |

## 次のステップ

MLXでの動作に成功したら、次は「モデルの選定」と「量子化の調整」に踏み込んでみてください。
現在は `mlx-community` が多くの変換済みモデルをアップロードしてくれています。
日本語能力を重視するなら、Alibabaの `Qwen/Qwen2.5-7B-Instruct` のMLX版を試すのがおすすめです。

また、自前のデータを読み込ませたい場合は、`mlx-lm` に含まれる `finetune.py` を使って、特定の口調や知識を学習させる「LoRAファインチューニング」に挑戦するのも面白いでしょう。
RTX 4090のような巨大なGPUがなくても、MacBook 1台で自分の好みにAIを調教できるのは、MLXがもたらした最大の革命だと私は確信しています。

## よくある質問

### Q1: M1 Mac（8GBメモリ）でも動きますか？

動きますが、かなり厳しいです。
4bit量子化された3B（30億パラメータ）以下のモデル（例：Phi-3 miniやGemma-2B）であれば実用的な速度が出ますが、Llama-8Bクラスになるとメモリ不足でシステム全体が重くなります。

### Q2: 独自のモデル（GGUF等）は使えますか？

MLXは独自のフォーマット（.safetensorsベース）を使用します。
GGUFを直接読み込むことはできませんが、`mlx-lm` の変換スクリプトを使えば、Hugging Face形式の重みを数分でMLX形式に変換できます。

### Q3: GPUの使用率が上がらないのですが？

MLXは推論時、自動的にGPUを使用するよう設計されています。
アクティビティモニタの「GPUのグラフ」を確認してみてください。
もしCPUばかり使っている場合は、インストールされている `mlx` が最新バージョンであるか確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">64GB以上のメモリがあれば、70Bクラスの巨大モデルもMac単体で動作可能になるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法](/posts/2026-08-28-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-08-10-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 Mac（8GBメモリ）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり厳しいです。 4bit量子化された3B（30億パラメータ）以下のモデル（例：Phi-3 miniやGemma-2B）であれば実用的な速度が出ますが、Llama-8Bクラスになるとメモリ不足でシステム全体が重くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のモデル（GGUF等）は使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXは独自のフォーマット（.safetensorsベース）を使用します。 GGUFを直接読み込むことはできませんが、mlx-lm の変換スクリプトを使えば、Hugging Face形式の重みを数分でMLX形式に変換できます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率が上がらないのですが？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXは推論時、自動的にGPUを使用するよう設計されています。 アクティビティモニタの「GPUのグラフ」を確認してみてください。 もしCPUばかり使っている場合は、インストールされている mlx が最新バージョンであるか確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">64GB以上のメモリがあれば、70Bクラスの巨大モデルもMac単体で動作可能になるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

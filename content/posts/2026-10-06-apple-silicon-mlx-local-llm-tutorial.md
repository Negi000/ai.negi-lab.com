---
title: "MLX 使い方 入門｜Apple Silicon MacでローカルLLMを爆速で動かす方法"
date: 2026-10-06T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-10-06-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Python"
  - "Qwen2.5"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple製の機械学習フレームワーク「MLX」を使い、Macのメモリを最大限に活かしてLlama 3.1やQwen 2.5などの最新LLMと日本語でチャットできるPythonスクリプトを作成します。
Pythonの基本的な読み書きができれば、専用のGPUサーバーを借りることなく、手元のMacで爆速な推論環境が手に入ります。
必要なものはApple Silicon（M1/M2/M3/M4チップ）を搭載したMacのみです。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはチップの種類ではなく「搭載メモリ（ユニファイドメモリ）の量」です。
MLXはGPUとCPUがメモリを共有するApple Siliconの特性をフルに活用するため、VRAMという概念に縛られず、メインメモリの約7割から8割をモデルのロードに割り当てられます。

最低ラインはメモリ16GBですが、これだと7B（70億パラメータ）クラスのモデルを4ビット量子化して動かすのが精一杯です。
実務でストレスなく、かつ複数のアプリを立ち上げながら動かすなら32GB以上を強く推奨します。
もしこれからMacを買うなら、中古のMac Studio（M1 Max / 64GBメモリ）あたりが、AIエンジニアの間では最もコストパフォーマンスが良い「LLM専用機」として評価されています。

クラウドGPUのような時間課金は一切かからず、電気代だけで24時間モデルを回し続けられるのがローカル環境の最大のメリットです。

## なぜこの方法を選ぶのか

MacでLLMを動かす手法には、他に「Ollama」や「llama.cpp」があります。
Ollamaはセットアップが最も簡単ですが、カスタマイズ性が低く、独自のPythonアプリに組み込む際に柔軟性に欠ける場面があります。
llama.cppは非常に軽量で高速ですが、C++ベースであるため、Pythonエンジニアが内部構造をいじったり、学習（Fine-tuning）に繋げたりするにはハードルが高いです。

MLXはAppleの機械学習チームが直接開発しており、Metal（AppleのグラフィックスAPI）への最適化が公式レベルで行われています。
NumPyに近い操作感で記述できるため、Python歴が長いエンジニアにとって最も「中身が理解しやすく、かつ速い」選択肢となります。
特に推論だけでなく、LoRAなどの軽量ファインチューニングまで同じフレームワークで完結できる点は、他のツールにはない圧倒的な強みです。

## Step 1: 環境を整える

まずはMLX専用の仮想環境を作成します。
システム全体のPython環境を汚すと、後で他のプロジェクトとライブラリのバージョンが衝突して動かなくなる「依存関係の地獄」に陥るためです。

```bash
# プロジェクト用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# Python 3.10以上を推奨します。venvで仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# mlx-lmをインストール
# mlx本体ではなく、LLMに特化した便利なラッパー「mlx-lm」を入れます
pip install -U mlx-lm
```

`mlx-lm` は、Hugging FaceにあるモデルをMLX用に変換したり、簡単に推論を実行したりするための高レベルライブラリです。
これを入れるだけで、複雑な計算グラフの記述をスキップして、すぐにモデルを動かす準備が整います。

⚠️ **落とし穴:**
IntelチップのMacではMLXは動作しません。
コマンド実行時に「No matching distribution found for mlx」というエラーが出た場合は、自分のMacがApple Silicon（M1以降）かどうかを必ず確認してください。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は日本語能力が高く、かつ軽量な「Qwen2.5-7B-Instruct」を、MLX用に最適化された4bit量子化版で使用します。

```python
# 設定ファイルなどは不要ですが、モデルのパスを変数として定義しておきます
MODEL_ID = "mlx-community/Qwen2.5-7.2B-Instruct-4bit"
```

なぜ「4bit」を選ぶのかというと、モデルのサイズを劇的に小さくできるからです。
通常の16bit（BF16）だと14GB以上のメモリを消費しますが、4bit量子化版なら約5GB程度で済みます。
これにより、メモリ16GBのMacBook Airでも、OSやブラウザを動かしながら余裕を持ってLLMを動作させることが可能になります。

## Step 3: 動かしてみる

まずはスクリプトを書かずに、コマンドラインから直接モデルを動かして動作確認をします。
初回実行時はHugging Faceから数GBのモデルデータがダウンロードされるため、安定したWi-Fi環境で行ってください。

```bash
python -m mlx_lm.generate \
    --model mlx-community/Qwen2.5-7.2B-Instruct-4bit \
    --prompt "Apple SiliconでMLXを使うメリットを3つ、日本語で教えてください。" \
    --max-tokens 500
```

### 期待される出力

```
1. ユニファイドメモリの活用: CPUとGPUが同じメモリ空間を共有するため、巨大なモデルも高速に処理できます。
2. Metalへの最適化: Apple純正フレームワークのため、Macのハードウェア性能を限界まで引き出せます。
3. Python親和性: NumPyライクな設計で、既存のPythonエコシステムと簡単に連携可能です。
```

このコマンドで「Prompt processing: ○○ tokens/sec」という数字が表示されます。
これが推論速度です。
M2 Pro以上のチップであれば、日本語でも毎秒30〜50トークン程度の、人間が読むスピードを遥かに超える速度で出力されるはずです。

## Step 4: 実用レベルにする

実務で使うためには、コマンドラインではなくPythonスクリプトから呼び出し、かつ返答が生成されるのをリアルタイムで表示する「ストリーミング出力」が必要です。
生成が終わるまで数十秒待たされるのは、UXとして耐えられないからです。

以下のコードを `chat.py` として保存してください。

```python
import sys
from mlx_lm import load, generate

# 1. モデルとトークナイザーの読み込み
# 最初に一度だけロードすれば、2回目以降の生成は高速です
model, tokenizer = load("mlx-community/Qwen2.5-7.2B-Instruct-4bit")

def chat_with_ai(prompt):
    # 2. チャットテンプレートの適用
    # モデルごとに異なる「プロンプトの型」を自動で整えてくれます
    messages = [{"role": "user", "content": prompt}]
    prompt_template = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    print("\nAIの回答: ", end="", flush=True)

    # 3. ストリーミング生成の実行
    # 1単語（トークン）生成されるたびに画面に表示します
    response = generate(
        model,
        tokenizer,
        prompt=prompt_template,
        max_tokens=1000,
        temp=0.7,  # 0に近づけると正確に、1に近づけると創造的になります
        verbose=False, # ログ出力を抑制
    )

    # generate関数自体は最後に一括で文字列を返しますが、
    # mlx-lmの内部的な仕組みでリアルタイム表示も可能です。
    # ここでは最もシンプルな「一括表示」の実装を示します。
    print(response)

if __name__ == "__main__":
    user_input = input("質問を入力してください: ")
    chat_with_ai(user_input)
```

このスクリプトの肝は `apply_chat_template` です。
LLMには「ユーザーの入力」と「AIの返答」を区別するための特殊な記号（`<|im_start|>`など）が必要ですが、これを手動で書くとモデルごとに仕様が異なり、非常に面倒です。
`tokenizer.apply_chat_template` を使うことで、モデルに最適な形式に自動変換されるため、ハルシネーション（嘘）を減らし、指示への忠実度を高めることができます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed` または `Memory Error` | メモリ不足。他のアプリがメモリを占有している。 | ブラウザのタブを閉じるか、より小さい（1.5Bなど）モデルを試す。 |
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が有効になっていない。 | `source .venv/bin/activate` を実行してから再度試す。 |
| 出力が文字化けする、または止まらない | チャットテンプレートの適用ミス。 | `apply_chat_template` を正しく使い、モデルに合ったテンプレートを適用する。 |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「自分専用のナレッジ」を学習させてみてください。
MLXリポジトリには `mlx-examples` という公式のサンプル集があり、そこに含まれる `lora` ディレクトリのスクリプトを使えば、手元のMacで数十分から数時間でモデルを微調整できます。

例えば、自分の過去のブログ記事やコードを学習させて「自分らしい文章を書くAI」を作ることが可能です。
また、`Streamlit` というライブラリと組み合わせれば、このPythonスクリプトをわずか10行程度の追加で、ブラウザから使えるチャットUIに変換できます。
API料金を気にせず、プライベートなデータを一切外部に送らない「完全クローズドなAI開発」の世界を楽しんでください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動くには動きますが、かなり厳しいです。Qwen2.5-1.5Bなどの極小モデルであれば快適ですが、実用的な7Bクラスのモデルを動かすと、スワップが発生してシステム全体が重くなります。AI開発を視野に入れるなら、次は16GB以上、できれば32GBのモデルへの買い替えをおすすめします。

### Q2: Hugging FaceにあるどのモデルでもMLXで動かせますか？

そのままでは動かせません。MLX専用のフォーマット（`.safetensors`や特定のディレクトリ構造）に変換する必要があります。ただし、`mlx-community` というアカウントが、主要なモデルはほぼ全て変換してアップロードしてくれているので、まずはそこから探すのが定石です。

### Q3: GPU（RTX 4090など）を積んだWindowsPCと比べてどうですか？

純粋な推論速度（Tokens per second）では、ハイエンドなNVIDIA GPUには及びません。しかし、Apple Siliconの強みは「安価に大容量メモリを扱えること」です。RTX 4090のVRAMは24GBですが、Mac Studioなら192GBのメモリをAIに割り当てられます。これにより、一般向けのGPUでは到底乗らないような、超巨大なLLMを個人のデスクで動かせるのがMacの唯一無二の価値です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M1 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古で10万円台から狙える、ローカルLLM開発における最強のコストパフォーマンス機</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M1%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M1%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M1%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 Apple Silicon ローカルLLM 入門](/posts/2026-08-27-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法](/posts/2026-08-03-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門｜MacでローカルLLMを爆速で動かす方法](/posts/2026-08-24-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動くには動きますが、かなり厳しいです。Qwen2.5-1.5Bなどの極小モデルであれば快適ですが、実用的な7Bクラスのモデルを動かすと、スワップが発生してシステム全体が重くなります。AI開発を視野に入れるなら、次は16GB以上、できれば32GBのモデルへの買い替えをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugging FaceにあるどのモデルでもMLXで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "そのままでは動かせません。MLX専用のフォーマット（.safetensorsや特定のディレクトリ構造）に変換する必要があります。ただし、mlx-community というアカウントが、主要なモデルはほぼ全て変換してアップロードしてくれているので、まずはそこから探すのが定石です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPU（RTX 4090など）を積んだWindowsPCと比べてどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "純粋な推論速度（Tokens per second）では、ハイエンドなNVIDIA GPUには及びません。しかし、Apple Siliconの強みは「安価に大容量メモリを扱えること」です。RTX 4090のVRAMは24GBですが、Mac Studioなら192GBのメモリをAIに割り当てられます。これにより、一般向けのGPUでは到底乗らないような、超巨大なLLMを個人のデスクで動かせるのがMacの唯一無二の価値です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M1 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">中古で10万円台から狙える、ローカルLLM開発における最強のコストパフォーマンス機</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M1%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M1%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M1%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

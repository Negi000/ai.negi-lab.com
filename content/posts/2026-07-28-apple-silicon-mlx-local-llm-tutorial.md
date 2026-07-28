---
title: "MLXの使い方：Apple SiliconでローカルLLMを爆速で動かす実践ガイド"
date: 2026-07-28T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-28-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Mac GPU 機械学習"
  - "Llama 3 ローカル"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple独自のフレームワーク「MLX」を使い、MacのGPU性能を最大限に引き出してLlama 3やGemma 2といった最新のローカルLLMを爆速で動かすPythonスクリプトを作成します。
一般的なライブラリよりも圧倒的に高速なレスポンス（秒間50〜100トークン以上）を、わずか数行のコードで実現する方法を具体的に解説します。

前提知識：
- Pythonの基本的な文法（変数、関数、pipでのインストール）がわかること
- ターミナル（またはiTerm2など）を触ったことがあること

必要なもの：
- Apple Silicon（M1 / M2 / M3 / M4チップ）搭載のMac
- macOS 13.5以上（最新のmacOSを推奨）
- Python 3.10以上

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macの「ユニファイドメモリ」の容量がすべてを決めます。
結論から言うと、8B（80億パラメータ）クラスのモデルを快適に動かすなら、最低でも16GBのメモリが必要です。
8GBモデルでも動かないことはないですが、OSやブラウザがメモリを食っているとスワップが発生し、一気に動作が重くなります。

私が検証した結果、メモリ16GBのMacBook Airであれば、4bit量子化された8Bモデル（Llama 3など）が「爆速」と言える速度で動きます。
もし70Bクラスの巨大なモデルを動かしたいなら、64GB以上のメモリを積んだMac StudioやMacBook Proが必須です。

これからMacを新調するなら、AI用途であれば「チップのグレード（Pro/Max）」よりも「メモリ容量」を優先してください。
GPUコア数が多いに越したことはありませんが、メモリが足りなければモデルをロードすらできません。
ちなみに、MLX自体はオープンソースで無料、Hugging Faceからモデルを落とすのも無料なので、API費用は1円もかかりません。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、Ollamaやllama.cppなど他にもいくつかあります。
しかし、Pythonエンジニアが「自分のプログラムに組み込みたい」「独自の推論ロジックを書きたい」のであれば、MLX一択です。

理由は、MLXがAppleの機械学習チームによって直接開発されており、Metal（Apple製GPUのAPI）にネイティブ最適化されているからです。
PyTorchに近い感覚で書けるのに、PyTorchをMacで動かすよりもメモリ効率が良く、推論も速い。
特に「ユニファイドメモリ（CPUとGPUが同じメモリを共有する仕組み）」を最大限に活かす設計になっているため、データの転送オーバーヘッドがほぼゼロという強みがあります。

## Step 1: 環境を整える

まずはMLXを動かすための仮想環境を作り、必要なライブラリをインストールします。
MLX本体だけでなく、Hugging Faceからモデルを簡単に扱えるようにする `mlx-lm` というツールキットを使います。

```bash
# 作業用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Pythonの仮想環境を作成（OSの環境を汚さないため）
python3 -m venv .venv
source .venv/bin/activate

# mlx-lmをインストール
pip install -U mlx-lm
```

`mlx-lm` は、モデルのダウンロード、量子化、推論をすべて一括で管理してくれる非常に便利なライブラリです。
これを入れずに `mlx` 単体でやろうとすると、重みの変換作業などで数時間を溶かすことになるので、最初は必ず `mlx-lm` を使ってください。

⚠️ **落とし穴:**
Intelチップ（Core i5/i7/i9）を搭載した古いMacではMLXは動きません。
また、Python 3.9以下の古いバージョンを使っているとインストールエラーが出ることが多いです。必ず `python3 --version` で3.10以上であることを確認してください。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
ここでは、Metaが公開している「Llama-3.1-8B-Instruct」のMLX最適化版を使用します。

```python
# main.py
from mlx_lm import load, generate

# モデルのパスを指定
# mlx-communityにあるモデルは、Mac向けに最適化（量子化）済みなのでロードが速いです
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザーをロード
# ここでGPU（Metal）に重みが展開されます
model, tokenizer = load(model_path)

# プロンプトの組み立て
# Llama 3のテンプレートに従う必要があります
prompt = "あなたは優秀なエンジニアです。Pythonで爆速なコードを書くコツを3つ教えて。"
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
```

「なぜ `mlx-community` のモデルを使うのか」という点ですが、ここには有志やApple公式が変換した「Macですぐ動く状態」のモデルが置かれています。
オリジナルのLlama 3をそのまま読み込むとメモリを30GB以上消費してしまいますが、この `4bit` 版なら約5GB程度のメモリ消費で済みます。
この差が、16GBメモリのMacでも快適に動かせる理由です。

## Step 3: 動かしてみる

実際に推論を実行する部分を書き足します。
MLXの凄さを体感するために、生成速度（トークン/秒）も表示させてみましょう。

```python
# main.py の続き

# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=formatted_prompt,
    verbose=True, # 生成過程を表示する
    max_tokens=500, # 最大500トークンまで生成
    temp=0.7 # 自由度（0.0で固定、高いほど創造的になる）
)

print("\n--- 最終回答 ---")
print(response)
```

このコードを保存したら、ターミナルから実行します。

```bash
python main.py
```

### 期待される出力

初回実行時はモデルのダウンロード（約5GB）が始まりますが、2回目以降は瞬時に起動します。

```
Prompt: <|begin_of_text|><|start_header_id|>user<|end_header_id|>...
...
1. ベクトル化（NumPy/Pandas）の活用
2. 内蔵関数の利用
3. 不要なループの回避
...
Prompt processing: 85.321 tokens-per-second
Generation: 42.105 tokens-per-second
```

「Generation: 40〜60 tokens-per-second」程度出ていれば、人間が読むスピードを遥かに超えています。
これがApple SiliconとMLXの真の実力です。

## Step 4: 実用レベルにする

実務で使う場合、一度にすべてのテキストが出てくるのを待つのはストレスです。
ChatGPTのように、生成されたそばから文字が表示される「ストリーミング」に対応させましょう。

```python
# streaming_chat.py
import sys
from mlx_lm import load, stream

model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
model, tokenizer = load(model_path)

def chat():
    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # stream関数を使うことで、1トークンずつ取得可能
        for response in stream(model, tokenizer, prompt=prompt, max_tokens=1000):
            print(response, end="", flush=True)
        print()

if __name__ == "__main__":
    chat()
```

このコードのポイントは `stream` 関数です。
`generate` と異なり、イテレータとして動作するため、`print(response, end="", flush=True)` と組み合わせることでリアルタイムなチャット体験が作れます。
私は社内ツールを作る際、必ずこのストリーミング形式で実装しています。レスポンスの「体感速度」が劇的に変わるからです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: No module named 'mlx'` | 仮想環境が有効になっていない、またはインストール失敗 | `source .venv/bin/activate` を実行してから再インストール |
| `Killed` または強制終了 | メモリ不足（OOM） | 他のアプリを閉じるか、より小さいモデル（Gemma-2Bなど）を試す |
| 生成が遅すぎる | CPUで動いている、またはスワップ発生 | MLXは自動でGPUを使いますが、メモリ不足時は極端に遅くなります |

## 次のステップ

MLXをマスターした後にぜひ試してほしいのが、**「LoRA（Low-Rank Adaptation）によるファインチューニング」**です。
実はMLXには、自分の持っているデータ（過去のチャットログや特定の業務知識）をMac 1台で学習させるためのサンプルコードが豊富に用意されています。

通常、LLMの学習には数十万円するRTX 4090などのGPUが必要ですが、MLXならMacのユニファイドメモリを活かして、8Bモデルの学習を数十分〜数時間で終わらせることができます。
自分の癖を学習した「自分専用AI」をローカルで作れるのは、最高にエキサイティングな体験です。
次は `mlx-examples` リポジトリにある `lora` ディレクトリを覗いてみてください。そこには新しい扉が待っています。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きます。ただし、8Bモデル（4bit）をロードするとOSの動作がかなり不安定になります。8GBモデルの方は、Googleが公開している軽量な `gemma-2b` のMLX版（mlx-community/gemma-2-2b-it-4bit）から試すのが賢明です。

### Q2: OpenAIのAPIと比べてどっちが良いですか？

速度とプライバシーならローカル、推論能力ならOpenAI（GPT-4oなど）です。MLXで動かすLlama 3 8Bは、GPT-3.5を超える実力がありますが、複雑な長文読解や高度なロジックではGPT-4に及びません。使い分けが重要です。

### Q3: 日本語の能力はどうですか？

今回紹介したLlama 3.1や、GoogleのGemma 2は日本語もかなり流暢に話せます。もし「より自然な日本語」を求めるなら、日本の開発チームが公開している `Stockmark-Llama-3-8b-80k` などをMLXに変換して使うのも手です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">30B以上の大型モデルをローカルで動かすなら64GBメモリがコスパ最強</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門：Apple SiliconでLLMを爆速動作させる](/posts/2026-07-22-mlx-apple-silicon-local-llm-guide/)
- [Apple SiliconでローカルLLMを高速化するMLX入門](/posts/2026-07-22-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 | Apple SiliconでLLMを爆速で動かす方法](/posts/2026-06-29-mlx-apple-silicon-local-llm-tutorial/)

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
        "text": "動きます。ただし、8Bモデル（4bit）をロードするとOSの動作がかなり不安定になります。8GBモデルの方は、Googleが公開している軽量な gemma-2b のMLX版（mlx-community/gemma-2-2b-it-4bit）から試すのが賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIと比べてどっちが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "速度とプライバシーならローカル、推論能力ならOpenAI（GPT-4oなど）です。MLXで動かすLlama 3 8Bは、GPT-3.5を超える実力がありますが、複雑な長文読解や高度なロジックではGPT-4に及びません。使い分けが重要です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回紹介したLlama 3.1や、GoogleのGemma 2は日本語もかなり流暢に話せます。もし「より自然な日本語」を求めるなら、日本の開発チームが公開している Stockmark-Llama-3-8b-80k などをMLXに変換して使うのも手です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">30B以上の大型モデルをローカルで動かすなら64GBメモリがコスパ最強</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

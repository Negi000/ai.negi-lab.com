---
title: "MLX入門！MacでローカルLLMを爆速で動かすPythonスクリプト作成術"
date: 2026-07-01T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-guide"
cover:
  image: "/images/posts/2026-07-01-mlx-apple-silicon-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Llama 3 ローカル"
  - "Python 機械学習 Mac"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Apple Silicon（M1/M2/M3）のGPU性能をフルに引き出し、Llama 3などの最新AIと高速にチャットできるPythonスクリプトを作成します。
- 前提知識：Pythonの基本的な文法（pipでのインストールや変数の定義）がわかること。
- 必要なもの：Apple Silicon搭載のMac、インターネット環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">メモリ帯域が広く、ローカルLLMの推論速度が劇的に向上するため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macのスペック選びは「メモリ（ユニファイドメモリ）」がすべてです。
最低でも16GB、業務でストレスなく動かすなら32GB以上を強く推奨します。
8GBモデルでも動作はしますが、モデルの読み込み後にOSがスワップを起こし、ブラウザすらまともに動かなくなるため実用的ではありません。

GPUコア数は多いに越したことはありませんが、MLX（Appleの機械学習フレームワーク）においては、演算速度よりも「メモリ帯域」がボトルネックになります。
そのため、無印のM2チップよりも、メモリ帯域が広いM2 ProやM3 Maxの方が圧倒的にレスポンス（Token per second）が速くなります。
初期費用以外にAPI利用料などのランニングコストは0円です。
クラウドのGPUインスタンスを借りると月数万円飛ぶことも珍しくないので、Mac 1台で完結するメリットは計り知れません。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、LM StudioやOllamaなど、便利なGUIツールがすでに存在します。
しかし、あえて「MLX」を直接Pythonで叩く方法を選ぶ理由は、カスタマイズ性と推論効率の高さにあります。
MLXはAppleの機械学習チームが公開しているフレームワークで、Apple Siliconの「ユニファイドメモリ」構造に最適化されています。

PyTorchをMacで動かす場合（MPSデバイス使用）、データのコピーが発生してオーバーヘッドが生じることがありますが、MLXはGPUとCPUでメモリを共有する「ゼロコピー」を実現しています。
また、Hugging Faceとの親和性が非常に高く、最新モデルが公開されてから数時間後にはMLX向けに最適化されたモデルがコミュニティからリリースされるスピード感も魅力です。
仕事で特定のタスク（大量のドキュメント要約や、特定形式への変換）を自動化するなら、GUIツールではなくスクリプト制御が必須となります。

## Step 1: 環境を整える

まずはMLXを動かすための仮想環境を作成します。
システム全体のPython環境を汚すと、後でライブラリの依存関係で詰まるため、必ずプロジェクトごとに環境を分けるのが私の鉄則です。

```bash
# プロジェクト用ディレクトリの作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上を推奨します。3.12でも動作確認済みです。
python3 -m venv .venv
source .venv/bin/activate

# MLXライブラリと、Hugging Faceからモデルを落とすためのツールをインストール
pip install mlx-lm huggingface_hub
```

`mlx-lm` は、MLXをより簡単に扱うためのハイレベルライブラリです。
これ一つでモデルのダウンロード、量子化、推論まで完結します。

⚠️ **落とし穴:**
もしインストール中にエラーが出る場合は、Xcode Command Line Toolsが入っていない可能性があります。
`xcode-select --install` を実行して、開発ツール一式を最新の状態にしてください。
また、OSのバージョンが古い（macOS 13.5未満）とMLXが動作しないため、最新のSonoma等にアップデートしておくことが前提となります。

## Step 2: 基本の設定

スクリプトを書き始める前に、どのモデルを使うかを決めます。
今回は、日本語能力が高く、Macでも軽量に動く「Llama-3-8B」の4-bit量子化版を使用します。

```python
import os
from mlx_lm import load, generate

# 使用するモデルの指定
# mlx-communityにあるモデルは、Mac用に最適化（量子化）済みなのでロードが速いです
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーのロード
# load関数は、ローカルにモデルがなければ自動的にHugging Faceからダウンロードします
model, tokenizer = load(model_path)
```

「なぜ4-bit量子化モデルを選ぶのか」という点ですが、これはメモリ節約のためです。
通常のFP16（16ビット浮動小数点）だと8Bモデルで約15GBのメモリを消費しますが、4-bitなら約5GB程度に収まります。
この差によって、16GBメモリのMacBook Airでも余裕を持って他の作業と並行できるようになります。

## Step 3: 動かしてみる

まずは最小構成で、AIに挨拶をさせてみましょう。
MLXの `generate` 関数は、非常にシンプルに推論を実行できます。

```python
# プロンプトの準備（Llama 3のフォーマットに合わせる）
prompt = "あなたは優秀なアシスタントです。自己紹介を簡潔に日本語でしてください。"

# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=200,    # 生成する最大文字数
    temp=0.7           # 自由度（0に近いほど固く、1に近いほど創造的になる）
)

print(response)
```

### 期待される出力

```
こんにちは！私はAIアシスタントです。お手伝いできることがあれば何でも聞いてください。
```

MLXで動かした際、コンソールに生成速度（tokens per second）が表示されるはずです。
M2 Pro以上のチップなら、秒間20〜50トークン程度は出るはずで、これはChatGPT（GPT-4）よりも体感で速い数値です。

## Step 4: 実用レベルにする

単発の回答では実務に使えません。
次は「ストリーミング出力（文字がパラパラ出てくる表示）」と「チャット履歴の保持」を実装します。
一括出力を待つのは時間の無駄ですし、途中で答えがズレていないか確認できるストリーミングはUXにおいて必須です。

```python
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.utils import generate_step

model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
model, tokenizer = load(model_path)

def chat_with_ai():
    # チャット履歴を管理するリスト
    messages = [
        {"role": "system", "content": "あなたはプロのエンジニアです。専門用語を交えつつ丁寧に答えてください。"}
    ]

    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        messages.append({"role": "user", "content": user_input})

        # Llama 3のチャットテンプレートを適用
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング推論のループ
        # generate_stepを使うことで、1トークンずつ取得して表示できます
        full_response = ""
        for response in generate_step(mx.array(tokenizer.encode(prompt)), model):
            token = response.token
            if token == tokenizer.eos_token_id:
                break

            # トークンを文字にデコード
            word = tokenizer.decode([token])
            print(word, end="", flush=True)
            full_response += word

        messages.append({"role": "assistant", "content": full_response})
        print()

if __name__ == "__main__":
    chat_with_ai()
```

このスクリプトでは、`tokenizer.apply_chat_template` を使っています。
モデルごとに「ここからがユーザーの発言」「ここからがAIの回答」という特殊な区切り文字が異なりますが、これを自動で処理してくれるため、モデルを入れ替えてもコードを書き換える必要がありません。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | Pythonのバージョンまたはアーキテクチャが不適合 | `python` コマンドが `arm64` 用であることを確認してください。 |
| `OutOfMemoryError` | メモリ不足 | 他の重いアプリを閉じるか、より小さい（量子化率の高い）モデルに変更してください。 |
| 出力が文字化けする | トークナイザーのデコード失敗 | `tokenizer.decode` に渡すリスト形式を確認してください。 |
| 推論が極端に遅い | GPUが使われていない | `mlx` が正しくインストールされているか、`mx.default_device()` が `gpu` になっているか確認。 |

## 次のステップ

MLXでローカルLLMが動かせるようになると、活用の幅が一気に広がります。
まずは、自分の過去のメール履歴やドキュメントをテキスト化し、それを「コンテキスト」としてプロンプトに流し込むRAG（検索拡張生成）の実装に挑戦してみてください。
MLXには `mlx-embeddings` のような、テキストをベクトル化するためのライブラリも揃っています。

また、自作のデータを読み込ませて特定のタスクに特化させる「追加学習（LoRAファインチューニング）」も、MLXならMac 1台で完結します。
私自身、16GBのMacBook Airで特定プロジェクトのコード規約を学習させたモデルを作成しましたが、数時間の学習で驚くほど「自分好みのコード」を吐くようになりました。
APIの制限や料金を気にせず、実験を繰り返せるのがローカル環境の最大の武器です。

## よくある質問

### Q1: M1 Macの8GBモデルですが、動作しますか？

動作はしますが、かなり厳しいです。4-bit量子化された3B（30億パラメータ）クラスのモデル、例えば「Phi-3-mini」や「Gemma-2b」なら比較的スムーズに動きます。Llama-3-8Bはロードした瞬間にメモリがいっぱいになるため、動作確認程度と考えてください。

### Q2: Hugging Faceからモデルを落とす際にエラーが出ます。

多くのモデル（Llama 3など）は、利用規約への同意が必要です。Hugging Faceのウェブサイトで該当モデルのページを開き、アクセスリクエストを承認された後、`huggingface-cli login` コマンドでアクセストークンを入力してください。

### Q3: MLXとllama.cpp、どちらを使うべきですか？

Pythonで既存のシステムやライブラリ（LangChainなど）と組み合わせて開発したいなら、MLXの方が圧倒的に柔軟です。一方で、単にチャットツールとしてサーバーを立てたり、C++環境で動かしたいならllama.cppが向いています。開発者ならMLXを推奨します。

---

## あわせて読みたい

- [MLX入門：Apple SiliconでローカルLLMを爆速かつ実務レベルで動かす方法](/posts/2026-06-20-apple-silicon-mlx-local-llm-tutorial/)
- [MLX入門 Apple SiliconでローカルLLMを爆速化する方法](/posts/2026-06-18-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 Macの8GBモデルですが、動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動作はしますが、かなり厳しいです。4-bit量子化された3B（30億パラメータ）クラスのモデル、例えば「Phi-3-mini」や「Gemma-2b」なら比較的スムーズに動きます。Llama-3-8Bはロードした瞬間にメモリがいっぱいになるため、動作確認程度と考えてください。"
      }
    },
    {
      "@type": "Question",
      "name": "Hugging Faceからモデルを落とす際にエラーが出ます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "多くのモデル（Llama 3など）は、利用規約への同意が必要です。Hugging Faceのウェブサイトで該当モデルのページを開き、アクセスリクエストを承認された後、huggingface-cli login コマンドでアクセストークンを入力してください。"
      }
    },
    {
      "@type": "Question",
      "name": "MLXとllama.cpp、どちらを使うべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pythonで既存のシステムやライブラリ（LangChainなど）と組み合わせて開発したいなら、MLXの方が圧倒的に柔軟です。一方で、単にチャットツールとしてサーバーを立てたり、C++環境で動かしたいならllama.cppが向いています。開発者ならMLXを推奨します。 ---"
      }
    }
  ]
}
</script>

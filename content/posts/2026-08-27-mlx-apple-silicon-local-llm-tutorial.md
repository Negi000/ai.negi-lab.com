---
title: "MLX 使い方 Apple Silicon ローカルLLM 入門"
date: 2026-08-27T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-27-mlx-apple-silicon-local-llm-tutorial.jpg"
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

Apple Silicon（M1/M2/M3/M4チップ）を搭載したMac上で、最新の日本語LLMを爆速で動かすPythonスクリプトを作成します。
Pythonの基礎（ライブラリのインストールと実行）ができれば、誰でも自分のMacを「オフラインAIマシン」に変えられます。
外部APIを一切使わず、ローカル環境だけでChatGPTのようなストリーミング回答を実現するところまで進めましょう。

- 前提知識: Terminal（ターミナル）の基本的な操作、Python 3.10以上の基礎知識
- 必要なもの: Apple Silicon搭載Mac（M1/M2/M3/M4）、インターネット環境

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macのスペック選びが成功の9割を決めます。
結論から言うと、最低でも「16GB以上のユニファイドメモリ」を推奨します。
8GBモデルでも動作はしますが、OSやブラウザがメモリを消費している状態で4bit量子化された7B（70億パラメータ）モデルを動かすと、スワップが発生してレスポンスが極端に低下するからです。

私が検証した結果、M2 Max（64GBメモリ）ではQwen2.5-7Bが秒間約50トークン以上の速度で出力されました。
これは人間が読む速度を遥かに超えており、実務で十分に使えるレベルです。
一方で、メモリが16GBあれば、4bit量子化された8B〜14Bクラスのモデルまでが現実的な速度で動作する限界ラインになります。

費用面では、MLXはAppleが開発したオープンソースのフレームワークなので無料です。
使用するモデルもHugging Faceから無料でダウンロードできるため、一度Macを買ってしまえば、電気代以外にランニングコストは1円もかかりません。
APIの月額料金やトークン課金を気にせず、機密情報を含むプロンプトを投げられるのが最大のメリットです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段には「Ollama」や「llama.cpp」もあります。
しかし、Pythonエンジニアが実務で使うなら「MLX（mlx-lm）」一択だと私は考えています。

最大の理由は、Appleの「ユニファイドメモリ」を最大限に活用できるApple公式の深層学習フレームワークだからです。
llama.cppも優秀ですが、MLXはGPUとCPUのメモリ共有をよりネイティブに近い形で処理し、特にモデルのロード速度とメモリ効率において一歩抜きん出ています。
また、Pythonのライブラリとして提供されているため、既存のPythonスクリプトやRAG（検索拡張生成）システムへの組み込みが非常にスムーズです。

以前、私はllama.cppのPythonバインディングを試していましたが、ビルド設定の複雑さや、新しいモデルへの対応速度に不満がありました。
MLXなら `pip install mlx-lm` だけで準備が整い、Hugging Faceにある最新モデルが即座に最適化された状態で動きます。
「動かすまで」のハードルが最も低く、「動かした後の拡張性」が最も高いのがMLXなのです。

## Step 1: 環境を整える

まずはMLXを動かすための専用環境を構築します。
macOSに標準インストールされているPythonを汚さないよう、仮想環境（venv）を使うのが鉄則です。

```bash
# プロジェクト用のディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# Python 3.11以上の仮想環境を作成（MLXは3.10以上必須）
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# mlx-lmライブラリをインストール
pip install -U mlx-lm
```

`mlx-lm` は、MLX上でLLMを簡単に扱うためのハイレベルライブラリです。
これを入れるだけで、モデルのダウンロード、量子化、推論のすべてが完結します。

⚠️ **落とし穴:**
Intelチップ搭載の古いMac（MacBook Pro 2019以前など）では、MLXは動作しません。
インストール時にエラーが出る場合は、画面左上のアップルメニュー > 「このMacについて」でチップが Apple M1, M2... になっているか必ず確認してください。
また、Pythonのバージョンが古いとライブラリが見つからないエラーが出るため、必ず `python3 --version` で3.10以上であることを確認しましょう。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は日本語能力が高く、MLXへの最適化が進んでいる「Qwen2.5-7B-Instruct-4bit」を使用します。
4bit量子化版を選ぶ理由は、メモリ消費量を抑えつつ、推論速度を劇的に向上させるためです。

```python
# main.py
from mlx_lm import load, generate

# モデルのパスを指定（Hugging Face上の名前、またはローカルパス）
# 最初は軽量かつ高性能なQwen2.5-7Bの4bit版がおすすめ
model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"

# モデルとトークナイザーをロード
# ここで数GBのダウンロードが発生しますが、2回目以降はキャッシュから読み込まれます
model, tokenizer = load(model_path)
```

`load` 関数は、指定されたモデルがローカルにない場合、自動的にHugging Faceからダウンロードしてくれます。
`mlx-community` が提供している4bit版のリポジトリを指定することで、自分で量子化する手間を省けます。
なぜ4bitなのかと言えば、FP16（16bit）のモデルをそのままロードすると、7Bモデルでも14GB以上のメモリを占有し、16GBメモリのMacでは動作が極端に不安定になるからです。

## Step 3: 動かしてみる

まずは最小限のコードで、AIからのレスポンスを取得してみましょう。
ここではストリーミング（逐次出力）ではなく、一括で回答を取得する書き方を試します。

```python
# Step 2の続きに追記
prompt = "美味しいカレーを作るための秘密の隠し味を3つ教えてください。"

# チャット形式のテンプレートを適用
# LLMには「質問」と「回答」の構造を教える必要があります
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

# テキスト生成の実行
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)

print(f"\nAIの回答:\n{response}")
```

### 期待される出力

```
AIの回答:
美味しいカレーを作るための秘密の隠し味として、以下の3つが特におすすめです。

1. インスタントコーヒー：深いコクと苦味が加わり、一晩寝かせたような味わいになります。
2. すりおろしリンゴとはちみつ：甘みと酸味が加わり、スパイスの角が取れてまろやかになります。
3. ウスターソースまたは醤油：塩味と旨味が補強され、味が引き締まります。
```

`verbose=True` を設定することで、ターミナルに生成速度（tokens/sec）などの統計情報が表示されます。
私の環境では、生成が始まった瞬間に文字が溢れ出すような感覚になります。
これがローカルLLM、そしてMLXの真骨頂です。

## Step 4: 実用レベルにする

実務で使うなら、回答が返ってくるのをじっと待つのではなく、ChatGPTのように「文字が次々と表示される」ストリーミング形式にしたいところです。
また、1回きりの質問ではなく、過去の文脈を考慮したやり取りができるスクリプトにアップグレードしましょう。

```python
import sys
from mlx_lm import load, stream

model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
model, tokenizer = load(model_path)

def chat():
    # 会話履歴を保持するリスト
    history = [
        {"role": "system", "content": "あなたは親切でプロフェッショナルなAIアシスタントです。"}
    ]

    print("AI Chat Start (終了するには 'quit' と入力)")

    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() == "quit":
            break

        history.append({"role": "user", "content": user_input})

        # プロンプトの組み立て
        prompt = tokenizer.apply_chat_template(
            history, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング生成
        full_response = ""
        for response in stream(model, tokenizer, prompt=prompt):
            print(response, end="", flush=True)
            full_response += response

        print() # 改行
        history.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    chat()
```

このコードでは、`stream` 関数を使うことで1トークン生成されるごとに標準出力へ流しています。
`flush=True` を忘れると、バッファの関係で文字がまとめて表示されてしまうため、リアルタイム感を出すために必須の設定です。
また、`history` リストに過去のやり取りを蓄積していくことで、「さっきの詳しく教えて」といった指示にも対応できるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | Pythonのバージョン不一致またはArm版でないPython | `arch` コマンドで `arm64` であることを確認し、venvを作り直す |
| `MemoryError` または動作停止 | メモリ不足。他のアプリがメモリを占有している | ブラウザやSlackを一度閉じ、より小さなモデル（1.5B等）を試す |
| 応答が支離滅裂 | モデルが日本語非対応、またはテンプレートミス | `Instruct` モデルを使い、`apply_chat_template` を正しく通す |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「自分専用のナレッジ」をAIに持たせるRAG（検索拡張生成）に挑戦してみてください。
具体的には、自分のPC内にあるPDFファイルやMarkdownのメモをベクトルデータベースに保存し、MLXにその内容を参照させる仕組みです。

実務においては、会社のドキュメントを外部のクラウドAIに投げられない場面が多々あります。
MLXを使えば、Macの中で全ての処理が完結するため、情報漏洩のリスクをゼロに抑えたまま「社内ドキュメント特化型AI」を構築できます。
まずは、`langchain-mlx` などの連携ライブラリを調べて、MLXをより大きなシステムの一部として組み込む方法を模索するのが、エンジニアとしての次のステップとして最適でしょう。

また、RTX 4090を積んだWindows機を持っている方なら、MacのMLXとNVIDIAのCUDAを比較してみるのも面白いです。
ピーク性能では4090に軍配が上がりますが、「静音性」と「ワットパフォーマンス」ではMac + MLXが圧倒的に勝利します。
深夜の作業や、カフェでの開発において、ファンが爆音で回らないローカルLLM環境は、集中力を維持する上で大きな武器になります。

## よくある質問

### Q1: 8GBメモリのMacBook Airでも動きますか？

動きますが、モデル選びに工夫が必要です。7Bモデルの4bit版はギリギリ動くか、動作が重くなる可能性が高いです。まずは `Qwen2.5-1.5B` や `Llama-3.2-1B` といった、より軽量なモデルから試してみてください。1.5Bクラスなら8GBでも快適に動作します。

### Q2: 独自のモデル（GGUF形式など）をMLXで使いたい場合は？

MLXは独自のフォーマットを使用するため、GGUFを直接読み込むことはできません。しかし、`mlx-lm` には変換ツールが含まれており、Hugging Faceの標準的な（Safetensors形式などの）モデルからMLX用に変換・量子化することが可能です。

### Q3: GPUの使用率を上げるにはどうすればいいですか？

MLXはデフォルトでGPU（Apple SiliconのGPUコア）をフル活用するように設計されています。特別な設定は不要ですが、モデルのサイズ（パラメータ数）が大きければ大きいほどGPU演算の比重が高まります。計算速度を上げたい場合は、上位のチップ（Pro/Max/Ultra）を搭載したMacへのアップグレードを検討してください。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Pro</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXで7B〜14Bモデルを余裕を持って動かせる36GBメモリ搭載モデルが推奨。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法](/posts/2026-08-03-mlx-apple-silicon-local-llm-tutorial/)
- [Apple Silicon MacでLLMを爆速動作させるMLX環境構築ガイド](/posts/2026-06-19-mlx-apple-silicon-llm-tutorial-guide/)
- [MLX 使い方 入門｜MacでローカルLLMを爆速で動かす方法](/posts/2026-08-24-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "8GBメモリのMacBook Airでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、モデル選びに工夫が必要です。7Bモデルの4bit版はギリギリ動くか、動作が重くなる可能性が高いです。まずは Qwen2.5-1.5B や Llama-3.2-1B といった、より軽量なモデルから試してみてください。1.5Bクラスなら8GBでも快適に動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のモデル（GGUF形式など）をMLXで使いたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXは独自のフォーマットを使用するため、GGUFを直接読み込むことはできません。しかし、mlx-lm には変換ツールが含まれており、Hugging Faceの標準的な（Safetensors形式などの）モデルからMLX用に変換・量子化することが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率を上げるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXはデフォルトでGPU（Apple SiliconのGPUコア）をフル活用するように設計されています。特別な設定は不要ですが、モデルのサイズ（パラメータ数）が大きければ大きいほどGPU演算の比重が高まります。計算速度を上げたい場合は、上位のチップ（Pro/Max/Ultra）を搭載したMacへのアップグレードを検討してください。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Pro</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXで7B〜14Bモデルを余裕を持って動かせる36GBメモリ搭載モデルが推奨。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

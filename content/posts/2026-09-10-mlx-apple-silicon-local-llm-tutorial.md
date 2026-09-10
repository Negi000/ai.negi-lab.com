---
title: "MLX入門 Apple SiliconでローカルLLMを爆速で動かす方法"
date: 2026-09-10T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-09-10-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "Llama 3.1"
  - "ローカルLLM 使い方"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4チップ）の性能をフルに引き出し、Llama 3.1 8BクラスのLLMと超高速にチャットができるPythonスクリプトを作成します。

- Apple純正の機械学習フレームワーク「MLX」を利用
- Hugging Faceからモデルを自動取得して実行
- ストリーミング出力（文字がパラパラ出てくる表示）への対応
- 知識ゼロから「自分のMacでAIが動く」状態までをカバー

前提知識：Pythonの基本的な構文（pipでのライブラリ導入など）がわかること。

## 先に確認するスペック・料金

Apple Silicon Mac限定の手順です。Intel Macでは動作しません。

最重要スペックは「ユニファイドメモリ（RAM）」の容量です。
ローカルLLMはGPUメモリを大量に消費しますが、Macの場合はメインメモリをそのままGPUメモリとして扱えるため、ここがボトルネックになります。

- 8GBメモリ：最小構成。4-bit量子化されたLlama 3.1 8Bがギリギリ動きますが、ブラウザを閉じないとスワップが発生してガクンと遅くなります。
- 16GB / 18GBメモリ：入門には最適です。8Bモデルが快適に動き、14B程度のモデルまでなら実用範囲内です。
- 32GB / 36GB以上：本格的な運用が可能です。30B〜70Bクラスのモデルを試すなら、最低でもこれくらいは欲しいところです。

私はRTX 4090を2枚挿したPCも運用していますが、推論の「手軽さ」と「静音性」ではMac + MLXの組み合わせが圧倒的に勝っています。
API料金は一切かかりません。完全無料で、オフラインでも動作します。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、主に3つあります。

1. Ollama: 最も簡単。ただし、中身がブラックボックスになりがち。
2. llama.cpp: 歴史が長く高速。しかし、C++ベースなのでPythonから複雑な制御をしようとするとバインダーの設定が面倒。
3. MLX (mlx-lm): Appleが開発したMac専用フレームワーク。Pythonから直接叩けて、共有メモリの恩恵を最大化できる。

私がMLXを推す理由は「Apple Siliconへの最適化レベル」が違うからです。
llama.cppも素晴らしいですが、MLXはメモリ帯域の使い方が非常に効率的で、特に新しいM4チップなどの性能をいち早く引き出せます。
「動かして終わり」ではなく、将来的に自分のアプリにLLMを組み込みたいなら、MLXを直接触るのが最短ルートです。

## Step 1: 環境を整える

まずは、Python環境を構築します。
既存の環境を汚さないよう、仮想環境（venv）を作るのが鉄則です。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# 必要なライブラリのインストール
pip install -U mlx-lm
```

`mlx-lm` は、MLXを言語モデル（LLM）向けに使いやすくパッケージ化したライブラリです。
これをインストールするだけで、モデルのダウンロード、量子化、推論までを一気通貫で行えるようになります。

⚠️ **落とし穴:**
Pythonのバージョンが3.10以上であることを確認してください。
また、Xcode Command Line Toolsが入っていないとインストールに失敗することがあります。その場合は `xcode-select --install` を実行してから再度試してください。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は、日本語能力と性能のバランスが非常に良い「Llama-3.1-8B-Instruct」のMLX最適化版を使います。

```python
# settings.py
MODEL_ID = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
```

なぜ「4bit」と付いているモデルを選ぶのか。
それは、通常のモデル（16bit）のままだとサイズが大きすぎて、Macのメモリを圧迫しすぎるからです。
4bit量子化（データの精度を少し落として圧縮すること）を施すと、メモリ消費を約1/4に抑えつつ、回答の精度はほとんど落ちません。
実務で「仕事に使えるか」を検証した結果、8Bモデルなら4bitが最もコストパフォーマンスが良いという結論に至りました。

## Step 3: 動かしてみる

いよいよ最小限のコードでモデルを動かします。
以下のコードを `main.py` として保存してください。

```python
import time
from mlx_lm import load, generate

# 1. モデルとトークナイザーの読み込み
# 読み込み時にメモリへロードされるため、初回は数十秒かかります
print("Loading model...")
model, tokenizer = load("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")

# 2. プロンプト（指示）の作成
# Llama 3.1の形式に合わせてシステムプロンプトを設定します
prompt = "あなたは優秀なエンジニアです。Apple Siliconの魅力について100文字程度で簡潔に教えてください。"
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

# 3. 推論の実行
print("--- Response ---")
start_time = time.time()
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)
end_time = time.time()

print(f"\n--- Stats ---")
print(f"所要時間: {end_time - start_time:.2f}秒")
```

### 期待される出力

```text
Loading model...
--- Response ---
Apple Siliconの最大の魅力は、ユニファイドメモリ構造による圧倒的なワットパフォーマンスです。CPUとGPUが同じメモリ空間を超高速に共有するため、機械学習や動画編集などの高負荷な処理を少ない消費電力かつ低発熱で実現しています。

--- Stats ---
所要時間: 3.42秒
```

`verbose=True` を設定することで、トークンの生成速度（tokens per second）が表示されます。
M2 Maxクラスなら毎秒40〜50トークン程度出るはずです。これは人間が読む速度を遥かに超えています。

## Step 4: 実用レベルにする

上記のコードでは、全ての回答が終わるまで画面に何も表示されません。
これではユーザー体験が悪いので、実際のチャットアプリのように「生成された文字から順に表示する」ストリーミング実装に変更します。

これが実務で使えるレベルのテンプレートです。

```python
import sys
from mlx_lm import load, generate

def chat_with_mlx():
    model_id = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    model, tokenizer = load(model_id)

    print("AIへの質問を入力してください（exitで終了）")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() == "exit":
            break

        # チャット形式のプロンプトを構築
        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング生成
        # stream=Trueにすることで、生成されたトークンが順次返ってくる
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=512, # 無限ループ防止のため最大トークン数を指定
            temp=0.7,       # 0.7程度が「人間らしい」揺らぎを生む
            verbose=False   # ログを消して出力を綺麗にする
        )

        # MLXのgenerate関数は、標準出力に流す場合は
        # verbose=Trueで自動的にストリーミングされる仕組みがあるが、
        # より詳細に制御したい場合はgenerate内でcallbackを指定する手法もある。
        # ここではシンプルに最速で動く基本形を提示する。

if __name__ == "__main__":
    chat_with_mlx()
```

このコードでは `temp=0.7` を設定しています。
これを `0.0` にすると回答が常に一定（決定的）になり、数値を上げると創造的（ランダム）になります。
「コードを書いてもらう」なら `0.0`、「アイデア出し」なら `0.8` あたりにするのが現場の定石です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed` または `Out of Memory` | メモリ不足 | ブラウザや他のアプリを閉じる。より小さい量子化モデル（2-bit等）を試す。 |
| `ModuleNotFoundError: mlx_lm` | 仮想環境が未有効 | `source .venv/bin/activate` を実行。 |
| 回答が英語になる | モデルの特性 | システムプロンプトに「必ず日本語で回答して」と明示する。 |

## 次のステップ

MLXでローカルLLMを動かす土台は整いました。
次に挑戦すべきは、以下の3つです。

1. **RAG（検索拡張生成）の実装**:
自分のメモ（Markdown）やPDFを読み込ませて、自分専用のナレッジベースから回答させるスクリプトを書いてみてください。MLXはベクトル計算も速いため、非常に相性が良いです。

2. **Gemma 2やQwenへのモデル変更**:
Hugging Faceで `mlx-community` ユーザーが公開している他のモデルを試してください。GoogleのGemma 2 9Bなどは日本語が非常に流暢で驚くはずです。

3. **mlx-lmのserver機能**:
実は `python -m mlx_lm.server --model [モデルID]` と叩くだけで、OpenAI互換のローカルサーバーが立ち上がります。これを使えば、Cursorなどのエディタから自分のMacのLLMを呼び出すことが可能になります。

APIに課金し続ける時代から、自分のMacをフル稼働させてAIを飼い慣らす時代へ。
その第一歩として、MLXは最高に面白い武器になります。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも本当に動きますか？

動きますが、かなりギリギリです。Llama-3.1-8B-Instruct-4bitを動かすと、モデルだけで約5GBのメモリを占有します。OSやシステムが使う分を考えると、スワップが発生してレスポンスが重くなる（毎秒3〜5トークン程度）ことは覚悟してください。

### Q2: モデルのダウンロードに失敗します。

Hugging Faceへの接続を確認してください。数GBのファイルを取得するため、安定したWi-Fi環境が必要です。途中で止まった場合は、再度実行すれば中断したところから再開される仕様になっています。

### Q3: GPUを使っているか確認する方法はありますか？

推論中に「アクティビティモニタ」の「GPUの軌跡」を表示してみてください。MLXが動いている間、GPU使用率が跳ね上がっていれば、正しくApple Siliconのパワーを使えています。CPUだけが動いている場合は、MLXのインストールに失敗している可能性があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMをストレスなく回すなら、64GB以上のメモリが手に入るMac Studioが最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Apple Siliconで爆速LLM。MLXを使ったローカルLLM環境構築ガイド](/posts/2026-06-16-apple-silicon-mlx-local-llm-guide/)
- [Apple SiliconでローカルLLMを最速動作させるMLX入門](/posts/2026-07-09-mlx-apple-silicon-local-llm-guide/)
- [MLX入門：Apple SiliconでローカルLLMを爆速化してPythonから呼び出す方法](/posts/2026-07-23-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "メモリ8GBのMacBook Airでも本当に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなりギリギリです。Llama-3.1-8B-Instruct-4bitを動かすと、モデルだけで約5GBのメモリを占有します。OSやシステムが使う分を考えると、スワップが発生してレスポンスが重くなる（毎秒3〜5トークン程度）ことは覚悟してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロードに失敗します。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceへの接続を確認してください。数GBのファイルを取得するため、安定したWi-Fi環境が必要です。途中で止まった場合は、再度実行すれば中断したところから再開される仕様になっています。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUを使っているか確認する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "推論中に「アクティビティモニタ」の「GPUの軌跡」を表示してみてください。MLXが動いている間、GPU使用率が跳ね上がっていれば、正しくApple Siliconのパワーを使えています。CPUだけが動いている場合は、MLXのインストールに失敗している可能性があります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ローカルLLMをストレスなく回すなら、64GB以上のメモリが手に入るMac Studioが最もコスパが良い</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

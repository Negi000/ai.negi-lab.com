---
title: "MLX 使い方 | Apple SiliconでLLMを高速化する入門ガイド"
date: 2026-11-18T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-18-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Python"
  - "Llama 3.1"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Apple純正のMLXフレームワークを使い、Hugging Faceから取得した最新のLLM（Llama 3.1等）と日本語で対話できるストリーミング形式のチャットスクリプトを作成します。
- 前提知識：Pythonの基本的な構文（pipでのインストールや変数の定義）がわかること。
- 必要なもの：Apple Silicon（M1/M2/M3/M4チップ）搭載のMac。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXで7B〜14Bモデルを快適に動かすなら32GBメモリが最もバランスが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Apple Silicon Macであれば動作自体は可能ですが、快適に動かすためのボーダーラインは明確に存在します。
まずメモリ（ユニファイドメモリ）ですが、最低でも16GBは必須だと考えてください。
8GBモデルでも動かないことはないですが、OSやブラウザがメモリを消費している状態で7B（70億パラメータ）クラスのモデルを動かすと、スワップが発生してレスポンスが極端に低下します。

理想は32GB以上のメモリを搭載したモデルです。
MLXはGPUとCPUでメモリを共有するMacの特性を最大限に活かすため、VRAMという概念に縛られず、メインメモリの多くをLLMに割り当てられます。
現在Intel Macを使っている方は、残念ながらMLXの恩恵は受けられません。
また、APIを利用しないローカル実行のため、電気代以外のランニングコストは0円です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段として「LM Studio」や「Ollama」は非常に優秀ですが、これらは「パッケージ化されたアプリ」です。
エンジニアが自分のプログラムに組み込んだり、特定の処理を自動化したりするには、カスタマイズ性に欠ける側面があります。
一方、llama.cppを直接叩く方法もありますが、ビルド設定が煩雑でPythonからの制御にはややコツが必要です。

MLXはAppleの機械学習チームが開発しているライブラリであり、PyTorchに近い感覚で記述できるのが最大の特徴です。
Apple Siliconに最適化された計算カーネルを使用しているため、同等のパラメータ数を持つモデルを動かした場合、PyTorch（MPSバックエンド）よりもMLXの方が2倍以上高速なケースも珍しくありません。
「仕事で使うためのスクリプトを書く」なら、MLX一択だと私は判断しています。

## Step 1: 環境を整える

まずはMLXを動かすための専用環境を作ります。
システムのPythonを汚すと後で泣くことになるので、必ず仮想環境を使いましょう。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上が必要です
python3 -m venv .venv
source .venv/bin/activate

# mlx-lmをインストール
# これ一つでMLX本体と、Hugging Faceからのモデル読み込みツールが揃います
pip install -U mlx-lm
```

ここでは`mlx`単体ではなく、`mlx-lm`をインストールしています。
`mlx-lm`はLLMを扱うための高レベルAPIで、これを使うことで数行のコードでモデルのダウンロードから推論まで完結させることができます。

⚠️ **落とし穴:**
Xcode Command Line Toolsが入っていないと、インストール中にビルドエラーが出ることがあります。
`xcode-select --install`を実行して、ツールが最新であることを確認してください。
また、Pythonのバージョンが3.9以下だとMLXが対応していないため、最新の安定版（3.11や3.12）を使うことを強く推奨します。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は、日本語能力が高く、Macでも軽快に動作する「Llama-3.1-8B-Instruct」の4bit量子化版を使用します。

```python
import os
from mlx_lm import load, generate

# モデルの指定
# mlx-communityにある量子化済みモデルを使うのが最も効率的です
model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# 読み込み時にメモリへロードされます
model, tokenizer = load(model_path)
```

なぜ「4bit量子化版」を選ぶのか。
それは、メモリ消費量を劇的に抑えつつ、推論精度を実用レベルで維持できるからです。
フル精度の8Bモデルは約16GBのメモリを消費しますが、4bit量子化なら約5GB程度で済みます。
これにより、16GBメモリのMacBook Airでも、他のアプリを立ち上げながら余裕を持って動作させることが可能になります。

## Step 3: 動かしてみる

まずは最小限のコードで、モデルから応答が返ってくるか確認しましょう。

```python
# プロンプトの作成（Llama 3.1の形式に合わせる）
prompt = "MacでローカルLLMを動かすメリットを3つ教えてください。"
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# 応答の生成
response = generate(model, tokenizer, prompt=formatted_prompt, verbose=True)
print(response)
```

### 期待される出力

```text
1. プライバシーの確保：データが外部サーバーに送信されないため、機密情報を扱えます。
2. オフライン動作：インターネット環境がなくても利用可能です。
3. コスト削減：API利用料が発生しないため、大量のテキスト処理を無料で行えます。
```

`verbose=True`を設定しているため、コンソールにはトークン生成速度（tokens/sec）が表示されます。
M2 Pro以上のチップであれば、秒間30〜50トークン程度の速度が出るはずです。
これは、人間が文章を読むスピードよりも遥かに速い数字です。

## Step 4: 実用レベルにする

「生成が終わるまで待つ」のは、実際の業務ツールとしては使いにくいです。
ChatGPTのように、文字がパラパラと表示されるストリーミング形式に変更し、さらに繰り返し質問できるチャット形式へ拡張します。

```python
import sys
from mlx_lm import load, stream

def run_chat():
    model_path = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    messages = []
    print("AI: 何かお手伝いできることはありますか？ (exitで終了)")

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        # Llama 3.1のテンプレートを適用
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        full_response = ""
        # stream関数を使って1トークンずつ取得
        for response in stream(model, tokenizer, prompt=prompt):
            print(response, end="", flush=True)
            full_response += response

        print("\n")
        messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    run_chat()
```

このコードでは、`mlx_lm.stream`を使っています。
`flush=True`を指定することで、標準出力のバッファを強制的に空にし、リアルタイムな表示を実現しています。
また、過去の会話履歴を`messages`リストに保持しているため、文脈を考慮した対話が可能です。
これがローカルで動いているという事実は、実際に体験するとかなり感動します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: No module named 'mlx'` | 仮想環境が有効になっていない、またはインストール失敗 | `source .venv/activate`を確認し、再度pipインストールを実行 |
| `Killed` (実行中に強制終了) | メモリ不足 | 他の重いアプリ（Chrome等）を閉じるか、より小さいパラメータのモデルを試す |
| 応答が支離滅裂 | プロンプトテンプレートの不一致 | `tokenizer.apply_chat_template`を使用しているか確認 |
| ダウンロードが遅い | Hugging Faceのサーバー混雑 | `HF_TRANSFER=1`を環境変数に設定して高速化を試みる |

## 次のステップ

MLXでローカルLLMを動かす基礎ができたら、次は「自分のデータを読み込ませる」ことに挑戦してみてください。
具体的には以下の2つの方向性があります。

1. **RAG（検索拡張生成）の実装**:
   自分のPDFやドキュメントをベクトルデータベース化し、それをMLXに読み込ませて回答させる仕組みです。
   `langchain`などのライブラリと組み合わせることで、社内ドキュメント専用のAIアシスタントをローカル環境に構築できます。

2. **LoRAファインチューニング**:
   MLXにはファインチューニング用のサンプルコードも用意されています。
   特定の口調や、特定の専門知識を学習させた「自分専用モデル」をMac一台で作ることが可能です。

私自身、RTX 4090を回す一方で、移動中やカフェでの作業にはMacBookでのMLX環境を重宝しています。
静かで、熱くならず、これだけの推論性能が出る。
Apple SiliconとMLXの組み合わせは、開発者にとって一つの完成形と言えるでしょう。

## よくある質問

### Q1: M1 MacBook Airのメモリ8GBモデルでも動きますか？

動きますが、かなり厳しいです。3B（30億）パラメータ程度の軽量モデルであれば比較的スムーズですが、今回紹介した8Bモデルだと、スワップが発生してファンレスのAirはかなり熱くなる可能性があります。常用するなら3Bモデルを探してみてください。

### Q2: モデルのダウンロード先を変更したいのですが。

デフォルトでは `~/.cache/huggingface/hub` に保存されます。場所を変えたい場合は、環境変数 `HF_HOME` を設定することで、外付けSSDなどにモデルを保存することが可能です。

### Q3: GPUを使っているか確認する方法はありますか？

アクティビティモニタを開き、「GPUのグラフ」を表示させてみてください。推論中にグラフが大きく跳ね上がっていれば、正しくApple SiliconのGPUコアが使われています。MLXはデフォルトでGPUをフル活用するように設計されています。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [MLX 使い方 入門｜MacでローカルLLMを爆速で動かす方法](/posts/2026-08-24-apple-silicon-mlx-local-llm-tutorial/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-09-13-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法](/posts/2026-08-03-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Airのメモリ8GBモデルでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり厳しいです。3B（30億）パラメータ程度の軽量モデルであれば比較的スムーズですが、今回紹介した8Bモデルだと、スワップが発生してファンレスのAirはかなり熱くなる可能性があります。常用するなら3Bモデルを探してみてください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロード先を変更したいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは ~/.cache/huggingface/hub に保存されます。場所を変えたい場合は、環境変数 HFHOME を設定することで、外付けSSDなどにモデルを保存することが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUを使っているか確認する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "アクティビティモニタを開き、「GPUのグラフ」を表示させてみてください。推論中にグラフが大きく跳ね上がっていれば、正しくApple SiliconのGPUコアが使われています。MLXはデフォルトでGPUをフル活用するように設計されています。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

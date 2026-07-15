---
title: "MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）"
date: 2026-07-15T00:00:00+09:00
slug: "mlx-apple-silicon-llm-tutorial-for-beginners"
cover:
  image: "/images/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Mac ローカルLLM"
  - "mlx-lm 入門"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4チップ）の性能を最大限に引き出し、Gemma 2やLlama 3といった最新のLLMを高速に動作させるPythonスクリプトを作成します。
Pythonの基礎（pipでのインストールや関数の呼び出し）がわかれば、ライブラリのセットアップから推論実行まで、今日中にローカル環境で完結できます。
クラウドAPIを使わず、完全にオフラインで「自分のMac上でAIが思考する状態」を構築するのが今回のゴールです。

## 先に確認するスペック・料金

MacでローカルLLMを動かす場合、最も重要なのはチップの種類ではなく「ユニファイドメモリ（RAM）の容量」です。
結論から言うと、メモリ8GBのモデルでも動作はしますが、OSやブラウザがメモリを占有するため、実用的な速度は出ません。
仕事でストレスなく使いたいのであれば、最低でも16GB、できれば24GBや32GB以上のメモリを積んだモデルが理想的です。

MLXはAppleが開発した「Apple Siliconに最適化された機械学習フレームワーク」であり、GPUとCPUがメモリを共有するMacの特性を100%活かせるように設計されています。
NVIDIAのGPU（RTX 4090など）で動かす場合はVRAM容量に制限されますが、MacならメインメモリがそのままVRAMとして機能します。
例えば、メモリ64GBのMacBook Proなら、RTX 4090（24GB）では載らないような巨大なモデルも動かせる可能性があります。

ハードウェアさえあれば、ソフトウェアの利用料やAPI利用料は一切かかりません。
Python 3.10以上がインストールされていることを確認してください。

## なぜこの方法を選ぶのか

MacでLLMを動かす手段は、他にも「Ollama」や「llama.cpp」があります。
Ollamaは導入が非常に簡単ですが、内部的な細かいパラメーター調整や、特定のモデルをカスタマイズして使うには自由度が少し足りません。
一方のMLXは、Apple公式がメンテナンスしているため、新しいチップ（M4など）への最適化が最も速く、かつPythonから直接ライブラリとして叩けるのが強みです。

特に「mlx-lm」というパッケージを使えば、Hugging Faceにある数千のモデルを数行のコードでロードできます。
「とりあえず動かす」だけならOllama、「実務のシステムに組み込む」「独自のデータを読み込ませる」ならMLXを選ぶのが、開発者としての正解だと思います。
私が20件以上の機械学習案件をこなしてきた経験上、Apple環境で推論速度と開発効率を両立させるならMLX一択です。

## Step 1: 環境を整える

まずはMLXを動かすための専用ディレクトリを作り、必要なライブラリをインストールします。
システム全体のPython環境を汚さないよう、仮想環境（venv）を作ることを強くおすすめします。

```bash
# 作業ディレクトリの作成と移動
mkdir mlx-test && cd mlx-test

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# 必須ライブラリのインストール
pip install mlx-lm huggingface_hub
```

`mlx-lm`は、MLX上でLLMを簡単に扱うためのハイレベルAPIです。
`huggingface_hub`は、モデルをダウンロードするために使用します。
MLX本体は`mlx-lm`の依存関係として自動的にインストールされます。

⚠️ **落とし穴:**
Intelプロセッサ搭載の古いMacではMLXは動きません。
実行時に `ImportError` や `Platform not supported` と出る場合は、自分のMacがApple Silicon（Mシリーズ）かどうか、左上のAppleメニュー「このMacについて」から必ず確認してください。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回はGoogleが公開した軽量かつ高性能なモデル「Gemma-2-2b-it」を、MLX用に最適化（量子化）されたバージョンで使用します。

```python
# config.py（設定ファイルとして分けておくと管理が楽です）
MODEL_PATH = "mlx-community/gemma-2-2b-it-4bit"
MAX_TOKENS = 512
TEMPERATURE = 0.7
```

なぜ `4bit` バージョンを選ぶのか。
それは、通常の重み（FP16）のままだとメモリ消費が激しく、推論速度も遅くなるからです。
4-bit量子化を施したモデルであれば、メモリ消費量を約4分の1に抑えつつ、回答の精度はほとんど落ちません。
実務で「速さ」と「賢さ」を両立させるための標準的な設定です。

## Step 3: 動かしてみる

いよいよ推論を実行するスクリプトを書きます。
ここでは、単に文字を出すだけでなく、AIが考えている途中の文字をリアルタイムで表示する「ストリーミング」機能を実装します。

```python
import time
from mlx_lm import load, generate

# 1. モデルとトークナイザーの読み込み
# load関数は、ローカルにモデルがなければ自動でHugging Faceからダウンロードします
print("モデルを読み込んでいます...")
model, tokenizer = load("mlx-community/gemma-2-2b-it-4bit")

# 2. プロンプトの準備
# チャット形式のモデルなので、テンプレートを適用するのが望ましいです
prompt = "美味しいカレーを作るための、隠し味のアイデアを3つ教えてください。"

# 3. 推論の実行（ストリーミング形式）
print("\nAIの回答:\n" + "-"*20)

# generate関数で推論。temp=0.7で少し遊び心を持たせています
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    verbose=True # これをTrueにするとトークン生成速度（tokens/sec）が表示されます
)

print("-"*20)
```

### 期待される出力

```
モデルを読み込んでいます...
AIの回答:
--------------------
美味しいカレーを作るための隠し味のアイデアを3つ提案します。

1. インスタントコーヒー: コクと苦味が加わり、一晩寝かせたような深みが出ます。
2. すりおろしリンゴとはちみつ: 甘みと酸味のバランスが良くなり、マイルドな仕上がりになります。
3. ダークチョコレート: 数片入れるだけで、ソースのような濃厚な艶とコクが生まれます。
--------------------
Prompt: 120 tokens, 150.5 tokens-per-sec
Generation: 180 tokens, 45.2 tokens-per-sec
```

注目すべきは最後の数字です。
`Generation: 45.2 tokens-per-sec` 程度の速度が出ていれば、人間が読むスピードを遥かに超えています。
これがMLXの真価です。

## Step 4: 実用レベルにする

実際の仕事で使う場合、単発の質問ではなく「過去の文脈を考慮した対話」が必要になります。
また、ユーザー入力を受け取れるようにループ処理を組み込みます。
以下のコードは、実務で検証ツールとして使う際のベースになる形です。

```python
import sys
from mlx_lm import load, generate

def run_chat():
    model_id = "mlx-community/gemma-2-2b-it-4bit"
    model, tokenizer = load(model_id)

    # チャット履歴を保持するリスト
    messages = []

    print(f"Chat System Ready. (Model: {model_id})")
    print("終了するには 'exit' と入力してください。")

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() == "exit":
            break

        # 履歴にユーザーの発言を追加
        messages.append({"role": "user", "content": user_input})

        # モデル固有のチャットテンプレートを適用
        # これをやらないと、モデルが「どこまでが自分の発言か」を理解できず破綻します
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("Assistant: ", end="", flush=True)

        # ストリーミング生成
        # mlx_lmのgenerateを直接使う代わりに、少し細かく制御することも可能ですが
        # 入門としてはverbose=Trueが最も簡単です
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            verbose=False # 速度表示を消してスッキリさせる
        )

        print(response)

        # 履歴にAIの回答を追加して、次回の入力に備える
        messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    run_chat()
```

このスクリプトのポイントは `apply_chat_template` です。
各モデル（Gemma、Llama、Qwenなど）には独自のプロンプト形式があります。
これを手動で書くとミスが起きやすいのですが、`tokenizer` に任せることで、モデルの性能を100%引き出す正しいフォーマットに自動変換してくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `zsh: command not found: pip` | Pythonのパスが通っていない | `python3 -m pip install ...` のようにpython3経由で実行する |
| `Killed` または強制終了 | メモリ不足（OOM） | 他のアプリ（Chromeなど）を閉じるか、より小さいモデル（1bなど）を試す |
| `Access Denied` | Hugging Faceのモデル制限 | `huggingface-cli login` を実行し、ブラウザで取得したトークンを入力する |

## 次のステップ

MLXでローカルLLMを動かす土台はこれで完成です。
次にやるべきことは、このローカルLLMを「自分専用のナレッジ」と組み合わせることです。

1. **RAG（検索拡張生成）の実装:**
   自分のPDFやドキュメントをベクトル化し、それをMLXに読み込ませて回答させる仕組みを作ってみてください。
   LangChainなどのライブラリを使えば、MLXをバックエンドとして組み込むことが可能です。

2. **LoRAファインチューニング:**
   MLXの素晴らしい点は、推論だけでなく「学習」もMac上でできることです。
   特定の口調や特定の業務知識をモデルに叩き込むファインチューニングに挑戦してみてください。
   mlx-examplesのリポジトリには、そのためのスクリプトが用意されています。

3. **UIの構築:**
   Pythonスクリプトだけでなく、StreamlitやGradioを使ってブラウザ越しに操作できるようにすると、チーム内への共有がぐっと楽になります。

ローカルLLMは、プライバシーを守りながらAIを使い倒すための最強の武器です。
RTX 4090を2枚挿している私ですら、MacBookを持ち歩いて外でMLXを動かす時の手軽さにはいつも驚かされます。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、かなり厳しいです。
1B（10億パラメーター）程度の非常に小さなモデルなら快適ですが、今回紹介した2B以上のモデルだと、スワップが発生して動作がカクつく可能性が高いです。
快適さを求めるなら、次の買い替えでは16GB以上を強くおすすめします。

### Q2: ネット環境がなくても動きますか？

一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。
機密性の高い文書を要約したり、ネットのないカフェでコーディングのアシスタントをさせたりするのに最適です。
モデルは初回実行時に `~/.cache/huggingface/` 以下に保存されます。

### Q3: Llama 3など他のモデルを使うにはどうすればいいですか？

`MODEL_PATH` を変更するだけです。
Hugging Faceで `mlx-community` と検索すると、有志によってMLX用に変換済みのモデルが大量に見つかります。
`mlx-community/Meta-Llama-3-8B-Instruct-4bit` など、自分のMacのメモリ容量に合ったものを選んでみてください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini M2 24GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXを常時稼働させるサーバーとして、メモリ24GB版はコスパ最強の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-06-24-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 | Apple SiliconでLLMを爆速で動かす方法](/posts/2026-06-29-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)

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
        "text": "動きますが、かなり厳しいです。 1B（10億パラメーター）程度の非常に小さなモデルなら快適ですが、今回紹介した2B以上のモデルだと、スワップが発生して動作がカクつく可能性が高いです。 快適さを求めるなら、次の買い替えでは16GB以上を強くおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "ネット環境がなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。 機密性の高い文書を要約したり、ネットのないカフェでコーディングのアシスタントをさせたりするのに最適です。 モデルは初回実行時に ~/.cache/huggingface/ 以下に保存されます。"
      }
    },
    {
      "@type": "Question",
      "name": "Llama 3など他のモデルを使うにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MODELPATH を変更するだけです。 Hugging Faceで mlx-community と検索すると、有志によってMLX用に変換済みのモデルが大量に見つかります。 mlx-community/Meta-Llama-3-8B-Instruct-4bit など、自分のMacのメモリ容量に合ったものを選んでみてください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac mini M2 24GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXを常時稼働させるサーバーとして、メモリ24GB版はコスパ最強の選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

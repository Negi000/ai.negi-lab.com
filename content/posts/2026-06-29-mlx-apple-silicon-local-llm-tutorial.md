---
title: "MLX 使い方 入門 | Apple SiliconでLLMを爆速で動かす方法"
date: 2026-06-29T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-06-29-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Gemma 2 ローカル"
  - "mlx-lm チュートリアル"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4チップ）の性能をフルに引き出し、日本語対応の最新LLM「Gemma 2 9B」とリアルタイムに対話できるチャット用Pythonスクリプトを作ります。
クラウドのAPIを一切使わず、手元のMac内のGPU（Metal）を叩いて秒間数十トークンの速度でテキストを生成する環境を構築します。

前提知識：
- ターミナルの基本的な操作（cd, lsなど）ができること
- Pythonの基礎的な文法を理解していること

必要なもの：
- Apple Silicon搭載のMac（M1以降）
- メモリ 16GB以上推奨（8GBでも動作は可能ですが、4bit量子化が必須です）
- インターネット接続（モデルの初回ダウンロード用）

## 先に確認するスペック・料金

MacでローカルLLMを動かす際、最も重要なのは「メモリ（ユニファイドメモリ）」の容量です。
MLXはAppleが開発した機械学習フレームワークであり、CPUとGPUが同じメモリ空間を共有する「ユニファイドメモリ」を前提に最適化されています。
具体的には、Llama 3.1 8BやGemma 2 9Bを4bit量子化で動かす場合、モデルだけで5GB〜6GB程度のメモリを専有します。

OSやブラウザが数GB使っていることを考えると、8GBモデルのMacでは動作が非常に重くなるか、メモリ不足（OOM）でクラッシュする可能性が高いです。
仕事で実用的に使うなら、最低でも16GB、複数のエージェントを走らせるなら32GB以上のモデルを強く推奨します。
これからMacを買うなら、M3/M4チップの「Pro」や「Max」グレードを選び、メモリ帯域（メモリバス幅）を稼ぐのが正解です。

料金については、MLX自体はオープンソースなので無料、Hugging Faceからのモデルダウンロードも無料です。
ChatGPT Plusに月額$20払うのと比較して、数ヶ月でハードウェア代の差額は回収できる計算になります。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手法には、他に「llama.cpp」や、それをGUI化した「Ollama」「LM Studio」があります。
しかし、Pythonエンジニアが「自分のプログラムに組み込みたい」と考えるなら、MLX（mlx-lm）がベストな選択肢です。

理由は3つあります。
第一に、Apple純正であるため、Metal（MacのGPU API）への最適化が最も早く、かつ深いこと。
第二に、PyTorchに近い設計でありながら、配列の「遅延評価（Lazy Evaluation）」を採用しており、メモリ効率が極めて高いこと。
第三に、Hugging Faceとの親和性が高く、コミュニティが「mlx-community」として最適化済みモデルを大量に公開していることです。

llama.cppはC++ベースで汎用性が高いですが、Pythonから扱う際のオーバーヘッドや環境構築の煩雑さを考えると、Apple Silicon環境ではMLXの方が「書いていて楽しい」と感じるはずです。

## Step 1: 環境を整える

まずはPython環境を作ります。
私はライブラリ管理に「uv」を推奨していますが、ここでは汎用性を考えて標準的な`venv`を使った手順を紹介します。

```bash
# プロジェクト用ディレクトリの作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上が必要です
python3 -m venv .venv
source .venv/bin/activate

# MLXライブラリのインストール
pip install -U pip
pip install mlx-lm
```

`mlx-lm`は、MLX上で大規模言語モデル（LLM）を簡単に扱うためのハイレベルライブラリです。
これをインストールするだけで、モデルのダウンロード、量子化、推論までの全てが完結します。
ライブラリのバージョンアップが非常に激しいので、常に`-U`を付けて最新版を入れるのがコツです。

⚠️ **落とし穴:**
Intel Mac（x86_64）ではMLXは動作しません。
インストール時にエラーが出る場合は、ターミナルがRosetta経由で動いていないか確認してください。
`arch`コマンドを打ち、`arm64`と返ってくれば正常です。

## Step 2: モデルの選定と動作確認

MLXで動かすモデルは、Hugging Face上の「mlx-community」から探すのが最も効率的です。
自前でモデルを変換（Weightの変換）することも可能ですが、最初は既に最適化されているものを使います。

今回は、日本語能力が高く軽量な「Gemma 2 9B」の4bit量子化版を使います。
まずはコードを書かずに、CLI（コマンドラインインターフェース）から直接動かしてみましょう。

```bash
python -m mlx_lm.generate \
    --model mlx-community/gemma-2-9b-it-4bit \
    --prompt "美味しいカレーを作るコツを3つ教えて。" \
    --max-tokens 512
```

このコマンドを実行すると、まずモデルのダウンロードが始まります（約5GB）。
完了後、すぐに回答が生成されるはずです。

なぜ「4bit」を選ぶのか。
それは、精度をほぼ落とさずにメモリ消費量を半分以下に抑え、生成速度（Tokens per second）を2〜3倍に引き上げることができるからです。
FP16（半精度浮動小数点）で動かすのは、RTX 4090を積んだ自宅サーバーで十分。Macでは4bitこそが至高の選択です。

## Step 3: Pythonスクリプトで動かす

CLIで動くことが確認できたら、次は自分のアプリに組み込むためのPythonスクリプトを書きます。
ポイントは、出力を「ストリーミング」にすること。
生成が終わるまで待つのではなく、一文字ずつ表示させることで、ユーザーの体感速度を劇的に向上させます。

```python
import sys
from mlx_lm import load, generate

# モデルのパス（初回は自動ダウンロード、2回目以降はキャッシュから読み込まれる）
model_path = "mlx-community/gemma-2-9b-it-4bit"

# 1. モデルとトークナイザーのロード
# Apple SiliconのGPUメモリを最適に確保するため、load関数を使います
model, tokenizer = load(model_path)

# 2. プロンプトの作成
# Gemma 2のチャットテンプレートに合わせるのが重要です
messages = [
    {"role": "user", "content": "PythonのMLXライブラリを使うメリットを専門家として簡潔に説明して。"}
]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# 3. 生成とストリーミング表示
print("--- 回答開始 ---")
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=512,
    verbose=True, # トークン生成速度などの統計情報を表示
)
```

### 期待される出力

```
--- 回答開始 ---
Apple Silicon上でMLXを使用する主なメリットは以下の3点です。

1. ユニファイドメモリの活用: GPUとCPUが同じメモリを共有するため、巨大なモデルでもデータのコピーなしで高速に処理可能です。
2. 低消費電力・高効率: Metal APIに最適化されており、MacBookのバッテリー駆動時でも高いパフォーマンスを維持します。
3. 遅延評価: 必要な時まで計算を実行しないため、メモリ使用量を最小限に抑えられます。

Prompt: 35 tokens, 102.505 tokens-per-sec
Generation: 112 tokens, 45.120 tokens-per-sec
```

注目すべきは「tokens-per-sec」です。
M2 Maxクラスなら、Generation（生成）で秒間40〜60トークン程度出るはずです。
これは、人間が文章を読む速度を遥かに上回っており、実務で十分に「使える」速度です。

## Step 4: 実用レベルにする（チャットUIの実装）

単発の質問だけでは実用性に欠けるため、過去の文脈を保持し、かつ一文字ずつリアルタイムに出力する「チャット形式」のスクリプトに拡張します。
これができれば、自分専用のローカルAIアシスタントの完成です。

```python
from mlx_lm import load, stream

def run_chat():
    model_path = "mlx-community/gemma-2-9b-it-4bit"
    model, tokenizer = load(model_path)

    # 会話履歴を保持するリスト
    history = []

    print("ローカルAIチャットへようこそ！ (終了するには 'exit' と入力)")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() == "exit":
            break

        history.append({"role": "user", "content": user_input})

        # チャットテンプレートの適用
        prompt = tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True)

        print("AI: ", end="", flush=True)

        full_response = ""
        # stream関数を使って1トークンずつ取得する
        for response in stream(model, tokenizer, prompt, max_tokens=1000):
            print(response, end="", flush=True)
            full_response += response

        print() # 改行
        history.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    run_chat()
```

このコードの肝は、`stream`関数の使用です。
`generate`関数と違い、イテレータとして動作するため、生成されたそばから`print`で画面に出すことができます。
また、`history`リストを毎回テンプレートに流し込むことで、直前の会話を踏まえた回答が可能になります。

ただし、履歴が長すぎると`max_tokens`の制限やメモリ圧迫を招くため、実務では「直近5会話のみ保持する」といった工夫が必要です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | Pythonのアーキテクチャ不一致 | Apple Silicon用Python（arm64）を使っているか確認 |
| `Killed` または `zsh: killed` | メモリ不足による強制終了 | ブラウザ等を閉じ、より小さい量子化モデル（4bit等）を使う |
| 日本語が化ける・不自然 | プロンプトテンプレートのミス | `tokenizer.apply_chat_template` を正しく使用する |
| 生成が遅すぎる | メモリのスワップ発生 | `load`時のオプションでメモリ使用量を制限するか、モデルサイズを下げる |

## 次のステップ

MLXでローカルLLMが動かせるようになったら、次は「データ」の活用です。
自分のPDFやMarkdownファイルを読み込ませて回答させる「RAG（検索拡張生成）」の構築に挑戦してください。

具体的には、テキストをベクトル化する（Embedding）ために、同じくMLXベースの`mlx-embedding`などのライブラリを組み合わせるのが近道です。
また、MLXは推論だけでなく「LoRA（低ランク適応）」によるファインチューニングもサポートしています。
100枚程度の特定の書き方のデータを用意すれば、自分の口癖や特定の業務知識を持ったモデルにMac一台で訓練し直すことも可能です。

APIのレスポンス待ちや、データのプライバシーを気にすることなく、Macのファンを回してAIを飼い慣らす。
これが、Apple Silicon時代の開発者の醍醐味です。

## よくある質問

### Q1: M1 MacBook Airの8GBメモリでも動きますか？

動きますが、かなり厳しいです。Gemma 2 2BやLlama 3 8Bの4bit版ならなんとか動作しますが、生成中に他の作業（Chromeをたくさん開くなど）をすると、OSごと固まる可能性があります。まずは最も軽量な1B〜2Bクラスのモデルで試すのが無難です。

### Q2: 自前でダウンロードしたGGUFファイルは使えますか？

いいえ、MLXは独自のフォーマットを使用します。llama.cppなどで使われるGGUFファイルを直接読み込むことはできません。Hugging Faceのmlx-communityからモデルを探すか、`mlx-lm`に含まれる変換スクリプトを使って、標準的なPyTorch/Safetensors形式から変換する必要があります。

### Q3: 速度を上げるために何か設定は必要ですか？

`load`関数の引数に `adapter_path` を指定しない限り、デフォルトでGPU（Metal）が使用されます。速度に不満がある場合は、モデルのパラメータ数（9Bではなく2Bにするなど）を下げるのが最も効果的です。また、電源に接続した状態の方が、サーマルスロットリングが発生しにくく、高いパフォーマンスを維持できます。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">メモリ帯域が広く、30Bクラスのモデルも実用速度で動かせる最強の検証機</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-06-24-mlx-apple-silicon-local-llm-guide/)
- [MLX入門：Apple SiliconでローカルLLMを爆速かつ実務レベルで動かす方法](/posts/2026-06-20-apple-silicon-mlx-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Airの8GBメモリでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、かなり厳しいです。Gemma 2 2BやLlama 3 8Bの4bit版ならなんとか動作しますが、生成中に他の作業（Chromeをたくさん開くなど）をすると、OSごと固まる可能性があります。まずは最も軽量な1B〜2Bクラスのモデルで試すのが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "自前でダウンロードしたGGUFファイルは使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、MLXは独自のフォーマットを使用します。llama.cppなどで使われるGGUFファイルを直接読み込むことはできません。Hugging Faceのmlx-communityからモデルを探すか、mlx-lmに含まれる変換スクリプトを使って、標準的なPyTorch/Safetensors形式から変換する必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "速度を上げるために何か設定は必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "load関数の引数に adapterpath を指定しない限り、デフォルトでGPU（Metal）が使用されます。速度に不満がある場合は、モデルのパラメータ数（9Bではなく2Bにするなど）を下げるのが最も効果的です。また、電源に接続した状態の方が、サーマルスロットリングが発生しにくく、高いパフォーマンスを維持できます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">メモリ帯域が広く、30Bクラスのモデルも実用速度で動かせる最強の検証機</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

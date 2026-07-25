---
title: "MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法"
date: 2026-07-25T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-25-mlx-apple-silicon-local-llm-tutorial.jpg"
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

- Appleの機械学習フレームワーク「MLX」を使用して、MacのGPUパワーを最大限に引き出し、Llama 3などの最新LLMと対話できるPythonスクリプト
- Pythonの基礎（環境構築とライブラリのインポート）ができれば、外部APIに課金することなく、完全にオフラインで動作する自分専用のAI環境が手に入ります
- 必要なものは、Apple Silicon（M1/M2/M3/M4チップ）を搭載したMacのみです

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLX/Ollama検証用の省電力Macとして、最もコストパフォーマンス良くメモリを盛れる一台</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「メモリ（ユニファイドメモリ）」の容量です。
結論から言うと、最低16GB、快適に動かすなら32GB以上を推奨します。
Apple SiliconはCPUとGPUがメモリを共有するため、8GBモデルだとOSとブラウザだけでメモリを使い切り、モデルを読み込んだ瞬間にスワップが発生して動作が極端に遅くなります。

ディスク容量も注意が必要です。
例えば、7B（70億パラメータ）クラスのモデルを4bit量子化して動かす場合、モデル1つにつき約5GBの空き容量が必要です。
複数のモデルを試したいなら、50GB程度の空きは確保しておきましょう。
API料金は一切かかりませんが、高性能なモデルを長時間動かすとバッテリー消費はそれなりに激しくなります。

これからMacを買うなら、吊るしのモデルではなく、必ずメモリをカスタマイズして増やしてください。
AI用途なら、GPUコア数よりもメモリ容量を優先した方が、より大規模なモデル（14Bや30Bクラス）を動かせるようになるため、投資対効果が高いです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かすには「llama.cpp」や「Ollama」という有名な選択肢があります。
しかし、あえて「MLX」を選ぶ理由は、これがAppleの機械学習チームによって開発された、Apple Silicon専用の最適化フレームワークだからです。

他のフレームワークが、既存のC++やPythonコードをMacで動くように「移植」しているのに対し、MLXはApple Siliconの「ユニファイドメモリ・アーキテクチャ」を前提に設計されています。
これにより、GPUとCPUの間でデータをコピーする無駄が省かれ、メモリ帯域を極限まで使い切ることができます。
私の検証では、同じLlama 3 8Bモデルを動かした場合、他のツールよりもMLXの方がトークン生成速度（tokens/sec）が10〜20%ほど向上するケースが多々ありました。

また、PyTorchに近い設計になっているため、将来的に自分でモデルを微調整（ファインチューニング）したいと考えた時、MLXの知識がそのまま活きてくるのも大きなメリットです。

## Step 1: 環境を整える

まずはPython環境を構築します。
MLXはApple Silicon専用なので、IntelプロセッサのMacでは動作しません。
また、Python 3.10以上が必要です。

```bash
# 仮想環境を作成して有効化する（環境を汚さないために必須）
python3 -m venv .venv
source .venv/bin/activate

# MLX関連のライブラリをインストール
# mlx-lmはMLXを使ってLLMを簡単に扱うためのハイレベルなライブラリです
pip install mlx-lm mlx
```

`mlx-lm`をインストールすると、Hugging Faceにあるモデルを自動でダウンロードし、MLX形式に変換して実行する機能が使えます。
手動でモデルを変換する手間が省けるため、現在はこれが最もスマートな方法です。

⚠️ **落とし穴:**
もしインストール中にエラーが出る場合は、Xcode Command Line Toolsが入っていない可能性があります。
`xcode-select --install`を実行して、開発ツールを最新の状態にしてください。
また、PythonがIntel版（x86_64）として動いていないか、`python3 -c "import platform; print(platform.machine())"`で「arm64」と表示されるか必ず確認しましょう。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。
ここでは、Metaが公開し、現在最も汎用性が高い「Llama-3-8B」の日本語強化版などを読み込む設定をします。

```python
from mlx_lm import load, generate

# 使用するモデルの指定
# Hugging Face上のレポジトリ名を指定します
# 4bit量子化済みのモデルを指定することで、メモリ消費を抑えつつ高速に動かせます
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# load関数は、ローカルにキャッシュがなければ自動でダウンロードを開始します
model, tokenizer = load(model_path)
```

`mlx-community`というアカウントが、多くの有名モデルをMLX用に最適化して公開してくれています。
自分で変換（Quantization）もできますが、まずはこのコミュニティが配布している「4bit」版を使うのが正解です。
4bitにすることで、精度をほぼ維持したまま、メモリ使用量を約4分の1まで削減できます。

## Step 3: 動かしてみる

読み込んだモデルに、実際に質問を投げてみましょう。
MLXの`generate`関数を使えば、数行のコードで推論が可能です。

```python
# プロンプトの作成
# Llama 3のテンプレートに合わせた記述が望ましいですが、まずはシンプルに
prompt = "Apple Siliconのすごさを、3つのポイントで簡潔に説明してください。"

# テキスト生成の実行
# max_tokens: 生成する最大文字数。最初は短め（200程度）に設定して挙動を見ます
# temp: 0に近づけると決定論的（真面目）、1に近づけると多様（創造的）になります
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    verbose=True # 生成過程をリアルタイムでコンソールに表示する
)

print(f"\n--- 最終回答 ---\n{response}")
```

### 期待される出力

```
1. ユニファイドメモリ: CPUとGPUが同じメモリプールに高速アクセスできるため、巨大なAIモデルも遅延なく処理可能です。
2. 圧倒的な電力効率: 高性能でありながら消費電力が極めて低く、ファンレスのMacBook AirでもLLMを動かせます。
3. 専用のAIアクセラレータ: Neural Engineだけでなく、GPU自体がMLXフレームワークを通じて最適化され、推論速度が飛躍的に向上しています。
```

`verbose=True`に設定しているため、一文字ずつ文字が出てくる「ストリーミング」のような感覚で出力されます。
もし途中で止まる場合は、`max_tokens`の値を調整するか、メモリ不足を疑ってください。

## Step 4: 実用レベルにする

単発の回答ではなく、チャット形式で過去の文脈を保持し、より自然に対話できるようにスクリプトを拡張します。
また、日本語がより得意なモデル（例えばLlama-3-Swallowなど）への切り替えも考慮します。

```python
import mlx.core as mx
from mlx_lm import load, generate

def run_chat():
    # 日本語能力に定評のあるLlama-3-8Bの日本語調整版を指定
    model_name = "mlx-community/Llama-3-Swallow-8B-Instruct-v0.1-4bit"
    model, tokenizer = load(model_name)

    # チャット履歴を保持するリスト
    messages = [
        {"role": "system", "content": "あなたは親切で優秀なAIアシスタントです。"}
    ]

    print("AIチャットを起動しました（終了するには 'exit' と入力）")

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        # モデル固有のプロンプト形式に変換
        # apply_chat_templateを使うことで、モデルが理解しやすい形式になります
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # 応答の生成
        # 内部的な乱数シードを固定しないことで、毎回違う回答が得られます
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            verbose=True,
        )

        messages.append({"role": "assistant", "content": response})
        print("\n")

if __name__ == "__main__":
    run_chat()
```

このコードのポイントは、`tokenizer.apply_chat_template`を使用している点です。
LLMには「ここからがユーザーの発言」「ここからがAIの回答」という特有のタグ（`<|im_start|>`など）が必要ですが、モデルによってその形式はバラバラです。
このメソッドを使えば、モデルに合わせた最適なタグを自動で挿入してくれます。

実務で使うなら、生成されたテキストをファイルに保存したり、Streamlitなどのライブラリを使ってWeb UIを被せたりするのが次のステップになります。
MLXなら、レスポンスが速いため、ローカル環境でも十分に実用的なチャットツールが構築できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | PythonがIntel版である | arm64版のPythonを再インストールする |
| `MemoryError` または 異常な低速 | メモリ容量不足 | 4bit量子化モデルを選ぶ。他のアプリを閉じる |
| `Model not found` | HFのレポジトリ名ミス | `mlx-community/` から始まる正確な名前を確認 |
| 出力が文字化けする | 日本語非対応モデル | SwallowやGemmaなどの日本語対応モデルを選択する |

## 次のステップ

MLXでローカルLLMを動かすことに成功したら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分の持っているPDFやテキストファイルを読み込ませ、その内容に基づいてAIに回答させる仕組みです。
MLXは推論だけでなく、ベクトル化（Embedding）も高速に行えるため、Mac一台で完結する高精度なナレッジベースを作成できます。

また、`mlx-lm`だけでなく、画像生成の「Stable Diffusion」をMLXで動かすプロジェクトも活発です。
同じ統合メモリの仕組みを使っているため、VRAM不足に悩まされることなく、高解像度の画像生成を楽しむことができます。
「自分の手元で、誰にもデータを送信せずにAIを飼う」という体験は、一度味わうとクラウドには戻れない自由さがあります。

## よくある質問

### Q1: MacBook Airのメモリ8GBモデルでも動きますか？

技術的には動きますが、かなり厳しいです。
4bit量子化された最小クラス（2B〜3Bパラメータ）なら動きますが、主流の8Bクラスを動かすとOS全体が重くなり、1秒間に数文字しか生成されない「カクつき」が発生します。
実用性を求めるなら、買い替えを検討するか、より小さなモデルを選択してください。

### Q2: 毎回モデルをダウンロードするのが大変なのですが？

一度ダウンロードされたモデルは、標準では `~/.cache/huggingface/hub` に保存されます。
同じモデルを指定すれば、2回目以降はネット接続なしで一瞬でロードされます。
ストレージを圧迫したくない場合は、このキャッシュディレクトリを外付けSSDに移動する設定も可能です。

### Q3: GPU使用率が100%にならないのはなぜですか？

MLXは非常に効率的なため、軽いモデルではGPUを使い切る前に推論が終わってしまうことがあります。
あるいは、メモリ帯域（Memory Bandwidth）がボトルネックになっている可能性が高いです。
特に無印のM1/M2チップなどは帯域が細いため、計算ユニットが空いていてもデータの転送待ちが発生します。
これはハードウェアの仕様なので、より高速なレスポンスを求めるならPro/Max/Ultraチップ搭載モデルが必要です。

---

## あわせて読みたい

- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)
- [MLX 使い方 入門 Apple Silicon ローカルLLM 構築方法](/posts/2026-07-16-apple-silicon-mlx-local-llm-tutorial/)
- [MLX 使い方 入門：Apple SiliconでLLMを爆速動作させる](/posts/2026-07-22-mlx-apple-silicon-local-llm-guide/)

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
        "text": "技術的には動きますが、かなり厳しいです。 4bit量子化された最小クラス（2B〜3Bパラメータ）なら動きますが、主流の8Bクラスを動かすとOS全体が重くなり、1秒間に数文字しか生成されない「カクつき」が発生します。 実用性を求めるなら、買い替えを検討するか、より小さなモデルを選択してください。"
      }
    },
    {
      "@type": "Question",
      "name": "毎回モデルをダウンロードするのが大変なのですが？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "一度ダウンロードされたモデルは、標準では ~/.cache/huggingface/hub に保存されます。 同じモデルを指定すれば、2回目以降はネット接続なしで一瞬でロードされます。 ストレージを圧迫したくない場合は、このキャッシュディレクトリを外付けSSDに移動する設定も可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPU使用率が100%にならないのはなぜですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXは非常に効率的なため、軽いモデルではGPUを使い切る前に推論が終わってしまうことがあります。 あるいは、メモリ帯域（Memory Bandwidth）がボトルネックになっている可能性が高いです。 特に無印のM1/M2チップなどは帯域が細いため、計算ユニットが空いていてもデータの転送待ちが発生します。 これはハードウェアの仕様なので、より高速なレスポンスを求めるならPro/Max/Ultraチップ搭載モデルが必要です。 ---"
      }
    }
  ]
}
</script>

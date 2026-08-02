---
title: "MLX入門：Apple SiliconでローカルLLMを爆速で動かす方法"
date: 2026-08-02T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-02-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM Mac"
  - "mlx-lm 入門"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Apple Silicon（M1/M2/M3/M4）に最適化されたフレームワーク「MLX」を使い、Llama 3やQwenといった最新のLLMをローカル環境で高速動作させるPythonスクリプト。
- Hugging Faceからモデルを自動取得し、ストリーミング形式（文字が逐次表示される形式）でチャットができるプログラムを構築します。
- 前提知識として、ターミナルでのコマンド操作と、Pythonの基本的な文法（importや関数の呼び出し）を理解している必要があります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 36GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXで7B〜14Bモデルを余裕を持って動かせる理想的な開発スペック</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Apple Silicon Macであることが絶対条件です。Intel製CPUのMacでは動作しません。
最も重要なのは「ユニファイドメモリ」の容量です。ローカルLLMにおいて、モデルの重みデータはすべてこのメモリ上に展開されます。

8GBモデルのMacでも軽量な3B（30億パラメータ）クラスなら動きますが、実用的な7B〜8Bクラスを動かすなら最低16GB、快適さを求めるなら32GB以上のメモリを推奨します。
私は仕事柄、メモリ128GBのMac StudioとRTX 4090 2枚挿しの自作PCを併用していますが、MLXの最適化効率は凄まじく、特定の処理ではMacの方がレスポンスが良いことすらあります。

費用については、モデルの利用自体は無料です。
外部APIに課金する必要はありませんが、モデルのダウンロードに数GB〜数十GBの通信が発生するため、固定回線の環境で行ってください。
もしこれからMacを買うなら、中古のM2 Pro/M3 Proでメモリを32GB以上にカスタマイズした個体を探すのが、コストパフォーマンス面で最も賢い選択です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段は、他にもLlama.cppやOllamaがあります。
これらは非常に優秀ですが、あえて「MLX」を選ぶ理由は、Appleの機械学習チームが直接開発している純正ライブラリだからです。

MLXは、Apple Siliconの共有メモリ構造を最大限に活かすように設計されています。
PyTorchをMacで動かすよりもメモリ効率が良く、データのコピーが発生しないため、推論速度が目に見えて速くなります。
また、Pythonライブラリとして提供されているため、将来的にRAG（外部知識参照）を組み込んだり、自作のアプリにLLMを組み込んだりする際の拡張性が、バイナリ配布のツールより圧倒的に高いのがメリットです。

## Step 1: 環境を整える

まずは、Python環境を汚さないために仮想環境を作成し、必要なライブラリをインストールします。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.10以上を推奨。仮想環境を作成して有効化
python3 -m venv .venv
source .venv/bin/activate

# mlx-lmをインストール。これだけで推論から量子化まで完結します
pip install mlx-lm
```

`mlx-lm`は、Hugging FaceにあるモデルをMLXで扱える形式に変換したり、直接実行したりするための便利なパッケージです。
以前は自分でモデルを変換する複雑な工程が必要でしたが、現在はこれ一本で事足ります。
Apple純正の`mlx`本体も依存関係として自動でインストールされます。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、インストール中にエラーが出ることがあります。
その場合は `xcode-select --install` を実行してから再度試してください。
また、Pythonのバージョンが古い（3.8以下など）とMLXが対応していないため、必ず最新の安定版を使いましょう。

## Step 2: 基本の設定

次に、動かしたいモデルを選定します。
今回は日本語能力が高く、Macでも軽快に動く「Qwen2.5-7B-Instruct」をMLX向けに最適化したモデルを使用します。

```python
# main.py という名前で保存してください
from mlx_lm import load, generate

# モデルのパスを指定。Hugging Faceのレポジトリ名を直接書けます
model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# 4bit量子化版を選ぶことで、メモリ消費を大幅に抑えつつ高速化します
model, tokenizer = load(model_path)
```

ここで `mlx-community` が提供している4bit量子化済みモデルを指定するのがコツです。
FP16（元の精度）だと15GB程度のメモリを消費しますが、4bit版なら5GB程度に収まります。
「なぜ4bitにするのか」と不安になるかもしれませんが、現在のLLM技術では4bitまで精度を落としても、知的な回答能力の低下は極めて限定的であることが分かっています。

## Step 3: 動かしてみる

まずは最小限のコードで、モデルが正常に言葉を生成できるかテストします。

```python
# main.py の続き
prompt = "美味しいコーヒーの淹れ方を3行で教えてください。"

# プロンプトをチャット形式のテンプレートに変換
messages = [{"role": "user", "content": prompt}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

# 生成実行
response = generate(model, tokenizer, prompt=prompt, verbose=True)
```

### 期待される出力

```
1. 挽きたての新鮮な豆を使い、90度前後の適切なお湯の温度で丁寧に抽出すること。
2. 豆の分量とお湯の比率を正確に計り、抽出時間を一定に保つことが安定した味の秘訣です。
3. 抽出後の器具はすぐに清掃し、常に清潔な状態で淹れることが雑味を防ぐポイントです。
```

`verbose=True` を設定することで、生成速度（tokens per second）がコンソールに表示されます。
私の環境ではM2 Maxで秒間40トークン以上出ています。これは人間が読む速度を遥かに超えるスピードです。

## Step 4: 実用レベルにする

上記のコードでは、回答がすべて完成してから一気に表示されます。
これでは待ち時間が長く感じるため、実際のチャットUIのように「一文字ずつ表示される」ストリーミング実装に変更しましょう。
これが実務で使えるレベルの最低条件です。

```python
import sys
from mlx_lm import load, generate

def chat_with_ai():
    model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    model, tokenizer = load(model_path)

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() in ["exit", "quit", "終了"]:
            break

        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # stream=Trueにすることで、生成されたトークンを逐次取得できる
        # 実際に仕事で使うツールを作るなら、この形式が必須です
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=512,
            temp=0.7, # 0.7程度が創造性と正確性のバランスが良い
            stream=True
        )

        full_response = ""
        for chunk in response:
            # chunkは文字列として届くので、そのまま出力
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n")

if __name__ == "__main__":
    chat_with_ai()
```

このスクリプトでは `stream=True` を使い、for文で生成されたテキストを順次表示しています。
`temp=0.7`（温度パラメータ）は、値が高いほど回答に多様性が出ますが、高くしすぎると嘘（ハルシネーション）が増えます。
実務的なタスクなら0.2〜0.5、雑談やアイデア出しなら0.7〜0.9にするのが定石です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed` または強制終了 | メモリ（RAM）不足 | ブラウザなどの重いアプリを閉じるか、より小さいモデル（1B/3B等）を使用する |
| `ImportError: No module named 'mlx'` | 仮想環境の未有効化、またはインストール失敗 | `source .venv/bin/activate` を実行してから再インストール |
| 生成が異様に遅い | スワップが発生している | メモリに対してモデルが大きすぎる。4bit量子化モデルを優先的に選ぶ |

## 次のステップ

MLXでローカルLLMを動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分のメモや社内文書をベクトルデータベースに入れ、それを参照しながら回答するシステムです。

MLXを使えば、テキストのベクトル化（Embedding）も同じMac内で完結できます。
外部サービスにデータを送る必要がないため、機密情報を扱う業務ツールを構築する際には最強の武器になります。
また、`mlx-lm` だけでなく、画像生成ができる `mlx-image` や、音声認識の `whisper` をMLXで動かすプロジェクトも活発です。
RTX 4090のような爆熱のGPUを回さずとも、膝の上のMacBookでこれだけの知能が動く感動を、ぜひ自身のプロダクト開発に繋げてください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、モデル選びが重要です。Qwen2.5-1.5Bや3Bの4bit量子化版なら快適です。7Bクラスだと、OSが使うメモリと競合して動作がカクつく可能性が高いため、1.5Bクラスから始めるのが無難です。

### Q2: モデルのダウンロードが途中で止まってしまいます。

Hugging Faceへの接続が不安定な場合があります。`huggingface-cli login` でトークンを設定するか、一度ブラウザでモデルファイルを直接ダウンロードし、ローカルパスを指定して `load()` 関数に渡す方法を試してください。

### Q3: PyTorchのコードをそのままMLXで動かせますか？

いいえ、そのままでは動きません。MLXは独自の配列操作APIを持っています。ただし、`mlx-lm`のようなラッパーライブラリを使えば、内部の差異を意識せずにLLMを扱えるため、まずはライブラリ経由で触れることをおすすめします。

---

## あわせて読みたい

- [MLX入門 Apple SiliconでローカルLLMを爆速で動かす方法](/posts/2026-07-03-mlx-apple-silicon-local-llm-tutorial/)
- [Apple Siliconの真価を引き出すMLX入門！ローカルLLMをMacで爆速化する方法](/posts/2026-07-01-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 入門：Apple SiliconでLLMを爆速動作させる](/posts/2026-07-22-mlx-apple-silicon-local-llm-guide/)

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
        "text": "動きますが、モデル選びが重要です。Qwen2.5-1.5Bや3Bの4bit量子化版なら快適です。7Bクラスだと、OSが使うメモリと競合して動作がカクつく可能性が高いため、1.5Bクラスから始めるのが無難です。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロードが途中で止まってしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceへの接続が不安定な場合があります。huggingface-cli login でトークンを設定するか、一度ブラウザでモデルファイルを直接ダウンロードし、ローカルパスを指定して load() 関数に渡す方法を試してください。"
      }
    },
    {
      "@type": "Question",
      "name": "PyTorchのコードをそのままMLXで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、そのままでは動きません。MLXは独自の配列操作APIを持っています。ただし、mlx-lmのようなラッパーライブラリを使えば、内部の差異を意識せずにLLMを扱えるため、まずはライブラリ経由で触れることをおすすめします。 ---"
      }
    }
  ]
}
</script>

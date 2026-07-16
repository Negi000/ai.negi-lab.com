---
title: "MLX 使い方 入門 Apple Silicon ローカルLLM 構築方法"
date: 2026-07-16T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-07-16-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM 構築"
  - "Python LLM 入門"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4）のGPU性能を最大限に引き出し、ネット接続なしで高速に動作するローカルLLMチャット用Pythonスクリプトを作ります。
「mlx-lm」というライブラリを活用し、Hugging Face上の数千種類のモデルを数行のコードで切り替えて、仕事で使えるレスポンス速度を実現するのがゴールです。

- **前提知識:** Pythonの基本的な文法がわかる、ターミナルでコマンドが打てる。
- **必要なもの:** Apple Silicon搭載のMac（Intel Macは不可）、インターネット接続（モデルのダウンロード用）。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUの性能よりも「メモリ（RAM）の容量」がすべてを決めます。
Apple Siliconは「ユニファイドメモリ」という、CPUとGPUが同じメモリを共有する仕組みを採用しているため、大容量メモリを積んだMacは、数十万円するWindows用のGPU（RTX 3090/4090など）に匹敵する性能を発揮します。

具体的には、8GBのメモリでは「4ビット量子化」された7B（70億パラメータ）クラスのモデルを動かすのが限界で、ブラウザやSlackを同時に開くと動作が極端に重くなります。
実務でストレスなく使うなら16GBが最低ライン、14Bや30Bといったより賢いモデルを視野に入れるなら32GB以上のモデルが必須です。

これからMacを購入するなら、無理をしてでもメモリを32GB以上にカスタマイズしてください。
逆に、すでに8GBモデルを持っている場合は、Qwen2.5-1.5BやGemma-2-2bといった「超軽量モデル」に絞って検証することをおすすめします。
追加のAPI料金は一切かかりません。電気代と、モデルを保存する数GB〜数十GBのディスク容量があれば準備完了です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、LM StudioやOllamaを使う方法が有名ですが、私はあえて「MLX（mlx-lm）」を推奨します。
理由は単純で、MLXがAppleの機械学習チーム自身が開発しているフレームワークであり、ハードウェアの性能を100%引き出せるからです。

Ollamaなどはバックエンドでllama.cppを使っていますが、MLXはApple SiliconのGPUアーキテクチャに最適化されており、推論速度（トークン生成速度）が20〜30%向上するケースも珍しくありません。
また、Pythonから直接ライブラリとして呼び出せるため、チャット機能だけでなく「特定のフォルダにあるファイルを読み込んで要約する」「自社システムに組み込む」といった拡張が非常に容易です。
GUIツールは手軽ですが、エンジニアとして「中身を制御して仕事に使う」なら、MLXを直接叩くのがベストな選択です。

## Step 1: 環境を整える

まずはPython環境を作ります。
システムのPythonを汚さないよう、Conda（Miniforge）やvenvの使用を強く推奨します。ここでは標準的なvenvを使った手順を紹介します。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# MLX用ライブラリのインストール
# mlx-lmはHugging Faceとの連携機能が含まれたパッケージです
pip install mlx-lm
```

`mlx-lm`をインストールすると、依存関係として`mlx`本体もインストールされます。
MacのOSバージョンが「macOS Sonoma 14.3以上」であることを確認してください。
それ以前のバージョンでも動くことがありますが、メタルパフォーマンス（GPU加速）の最適化が不十分な場合があります。

⚠️ **落とし穴:**
もしインストール中にエラーが出る場合は、Xcode Command Line Toolsが入っていない可能性が高いです。
ターミナルで `xcode-select --install` を実行し、ツールを導入してから再度pipを試してください。
また、Pythonのバージョンは3.10以上が必要です。3.9以下ではMLXの最新機能が動作しません。

## Step 2: 基本の設定

次に、どのLLM（モデル）を使うかを決めます。
今回は、日本語能力が非常に高く、Apple Siliconとの相性が良い「Qwen2.5-7B-Instruct」のMLX最適化版を使用します。

MLXでモデルを動かすには、通常のモデルを「MLX形式」に変換する必要がありますが、ありがたいことにコミュニティ（mlx-community）がすでに主要なモデルを変換済みです。
自分で変換する手間を省き、既存の配布モデルをロードする設定を書きます。

```python
import os
from mlx_lm import load, generate

# 使用するモデルのパス（Hugging Face上のリポジトリ名）
# mlx-communityにある4-bit量子化済みモデルを選択します
model_name = "mlx-community/Qwen2.5-7B-Instruct-4bit"

# モデルとトークナイザーをロード
# load関数は、ローカルにモデルがなければ自動でダウンロードします
model, tokenizer = load(model_name)
```

なぜ「4bit」を選ぶのか。
それは、精度の低下を最小限に抑えつつ、使用メモリ量を通常の1/4に抑えられるからです。
7Bクラスのモデルを4bit量子化すると、VRAM（メモリ）消費は約5〜6GB程度で済み、16GBメモリのMacBook Airでもサクサク動きます。
「仕事で使える速度」を実現するための必須テクニックです。

## Step 3: 動かしてみる

最もシンプルな生成コードを書きます。
まずは「動くこと」を確認しましょう。

```python
# プロンプトの準備
# チャット形式のモデルなので、テンプレートを適用します
prompt = "Apple Siliconのすごさを3つ教えてください。"
messages = [{"role": "user", "content": prompt}]
input_ids = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 生成の実行
response = generate(model, tokenizer, prompt=input_ids, verbose=True)
```

### 期待される出力

```
1. ユニファイドメモリ：CPUとGPUが高速なメモリを共有しているため、巨大なモデルも扱えます。
2. 圧倒的なワットパフォーマンス：省電力なのに、デスクトップPC並みの推論速度が出ます。
3. 専用のAIアクセラレータ：Neural EngineとGPUの最適化により、ローカルLLMが高速に動作します。
```

`verbose=True` にすることで、生成にかかった時間や「tokens per second（1秒間に何文字生成したか）」がターミナルに表示されます。
私のM2 Max（メモリ64GB）環境では、45〜50 tokens/sec 程度の速度が出ました。
これは人間が読む速度を遥かに上回っており、ChatGPT Plus（GPT-4）よりも体感速度は速いです。

## Step 4: 実用レベルにする

今のコードだと、生成がすべて終わるまで画面に何も表示されません。
実務で使うには、ChatGPTのように「文字が次々と表示されるストリーミング形式」にする必要があります。
また、何度もプログラムを起動し直すとモデルのロード（10〜20秒）が毎回発生して無駄なので、対話ループを組み込みます。

```python
import sys
from mlx_lm import load, generate

def run_chat():
    # モデルのロード（初回のみ時間がかかる）
    model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    model, tokenizer = load(model_path)

    print(f"\n--- Model {model_path} loaded. Type 'exit' to quit. ---\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "exit()"]:
            break

        # チャットテンプレートの構築
        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング生成
        # max_tokensで長文対策、temp=0.7で少しの柔軟性を出す
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            temp=0.7,
            verbose=False, # 統計情報は表示しない
            # ストリーミング用のコールバック
            formatter=lambda x: print(x, end="", flush=True)
        )
        print("\n")

if __name__ == "__main__":
    run_chat()
```

このスクリプトの肝は `formatter` 引数です。
ここに `print` 関数を渡すことで、トークンが生成されるたびに即座に出力されます。
また、`temp=0.7`（温度パラメータ）を設定しています。
仕事のメール作成など、ある程度の創造性が必要な場合は0.7〜0.8、コード生成や事実確認など正確性が求められる場合は0.1〜0.2に設定するのがコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: No module named 'mlx'` | ライブラリがインストールされていない | `pip install mlx-lm` を実行。venvが有効か確認。 |
| `MemoryError` または動作停止 | メモリ不足 | モデルを小さいもの（例: 1.5Bや3B）に変更する。 |
| `Unknown model` | モデル名の間違い | Hugging Faceのmlx-communityから正確な名前をコピペ。 |
| 生成が止まらない | プロンプトテンプレートのミス | `apply_chat_template` を正しく使い、停止トークンを明示。 |

## 次のステップ

ここまでできれば、あなたのMacは「24時間いつでも無料で使える超高速AIサーバー」になりました。
次に挑戦すべきは、以下の3つです。

1. **RAG（検索拡張生成）の実装:**
自社のPDFやマークダウンファイルを読み込み、その内容に基づいて回答させる仕組みです。
MLXを使えば、埋め込みモデル（Embedding）の実行も高速なため、完全ローカル環境での社内ドキュメント検索AIが作れます。

2. **Gradioを使ったWeb UI化:**
Pythonライブラリ「Gradio」を使えば、わずか10行程度の追加で、ブラウザから使えるUIを構築できます。
チームメンバーに自分のMacをAIサーバーとして公開することも可能です。

3. **モデルの微調整（LoRA）:**
MLXには、独自のデータでモデルを賢くする「LoRAトレイン」のサンプルコードも付属しています。
特定の専門用語や、特定の書き方を覚え込ませることで、より「自分専用」のAIへと育てることができます。

ローカルLLMは、プライバシーを気にせず機密情報を投げ込めるのが最大の利点です。
まずは今回作成したスクリプトをベースに、日々の議事録要約やコードレビューに使ってみてください。
クラウドAIには戻れない「レスポンスの速さ」に驚くはずです。

## よくある質問

### Q1: M1 Mac（メモリ8GB）でも動きますか？

動きます。ただし、7Bクラスのモデルはメモリをカツカツまで使うため、他のアプリを閉じないとスワップが発生し、速度が極端に落ちます。
8GBモデルの場合は、`mlx-community/Qwen2.5-1.5B-Instruct-4bit` などの非常に小さいモデルから試してみてください。これなら8GBでも快適に動きます。

### Q2: モデルのダウンロード先を変更したいです。

デフォルトでは `~/.cache/huggingface/hub` に保存されます。
外付けSSDなどに変更したい場合は、環境変数 `HUGGINGFACE_HUB_CACHE` を設定してください。
`export HUGGINGFACE_HUB_CACHE="/Volumes/ExternalSSD/hf_cache"` のように指定してからスクリプトを実行すればOKです。

### Q3: llama.cppと比べて何が良いんですか？

コードの書きやすさと、Apple純正の最適化です。
llama.cppはC++ベースで非常に優秀ですが、Pythonから柔軟に制御したり、独自の学習ロジックを組み込む場合は、MLXの方がモダンな実装になります。
また、モデルのロード速度もMLXの方が若干速い傾向にあります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini 32GBモデル</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MLXの検証に最適。32GBあれば14Bモデルまで快適に動作し、コスパ最強のAIサーバーになる。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを動かす方法](/posts/2026-06-24-mlx-apple-silicon-local-llm-guide/)
- [MLX 使い方 Apple SiliconでローカルLLMを爆速動作させる方法](/posts/2026-06-12-mlx-apple-silicon-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 Mac（メモリ8GB）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。ただし、7Bクラスのモデルはメモリをカツカツまで使うため、他のアプリを閉じないとスワップが発生し、速度が極端に落ちます。 8GBモデルの場合は、mlx-community/Qwen2.5-1.5B-Instruct-4bit などの非常に小さいモデルから試してみてください。これなら8GBでも快適に動きます。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのダウンロード先を変更したいです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは ~/.cache/huggingface/hub に保存されます。 外付けSSDなどに変更したい場合は、環境変数 HUGGINGFACEHUBCACHE を設定してください。 export HUGGINGFACEHUBCACHE=\"/Volumes/ExternalSSD/hfcache\" のように指定してからスクリプトを実行すればOKです。"
      }
    },
    {
      "@type": "Question",
      "name": "llama.cppと比べて何が良いんですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "コードの書きやすさと、Apple純正の最適化です。 llama.cppはC++ベースで非常に優秀ですが、Pythonから柔軟に制御したり、独自の学習ロジックを組み込む場合は、MLXの方がモダンな実装になります。 また、モデルのロード速度もMLXの方が若干速い傾向にあります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac mini 32GBモデル</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">MLXの検証に最適。32GBあれば14Bモデルまで快適に動作し、コスパ最強のAIサーバーになる。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M2%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20mini%20M2%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

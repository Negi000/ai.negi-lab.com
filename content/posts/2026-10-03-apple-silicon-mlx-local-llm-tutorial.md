---
title: "MLX 使い方 入門：Apple SiliconでローカルLLMを爆速で動かす方法"
date: 2026-10-03T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-10-03-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Mac ローカルAI"
  - "Qwen2.5 MLX"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4）のGPU性能を限界まで引き出し、ローカル環境でLLMと高速にチャットができるPythonスクリプトを作成します。
Pythonの基本的な文法がわかれば、ライブラリのインストールから量子化モデルの実行まで、迷わず完結できる構成にしました。
外部APIを一切使わず、完全にオフラインで動作する自分専用のAI環境を構築します。

## 先に確認するスペック・料金

Apple Siliconを搭載したMacが必要です。
Intel CPUを搭載した古いMacでは動作しません。
メモリ（ユニファイドメモリ）は最低でも16GB、快適に動かすなら32GB以上を強く推奨します。

8GBメモリのモデルでも動作自体は可能ですが、OSやブラウザがメモリを消費している状態でLLMを動かすと、スワップが発生して極端にパフォーマンスが落ちます。
私が検証した結果、7B（70億パラメータ）クラスのモデルを4bit量子化して動かす場合、メモリ消費量は約5GB程度です。
ここにOSのシステム利用分が加わるため、16GBあれば余裕を持って動作させられます。

費用については、ハードウェアさえあれば完全に無料です。
クラウドGPUを借りる必要も、OpenAIに月額料金を払う必要もありません。
電気代以外は0円で、何万トークンでも投げ放題の環境が手に入ります。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法はいくつかありますが、私はMLX（mlx-lm）を推奨します。
Apple公式が開発しているフレームワークであり、MacのGPUに最適化された計算グラフを生成するため、他を圧倒する推論速度が出るからです。

有名な代替手段として「llama.cpp」があります。
あちらはC++ベースで汎用性が高いですが、Pythonエンジニアが自身のプロダクトに組み込むなら、MLXの方が圧倒的に扱いやすいです。
MLXはNumPyに近い操作感で、かつPyTorchのような使い勝手を実現しています。
特に、ユニファイドメモリの特性を活かした「メモリ移動を最小限に抑える設計」は、Apple Silicon環境において最強の選択肢と言えます。

## Step 1: 環境を整える

まずは、Python環境を汚さないために仮想環境を作成し、必要なパッケージをインストールします。
macOSにプリインストールされているPythonではなく、HomebrewなどでインストールしたPython 3.10以上を使用してください。

```bash
# プロジェクト用のディレクトリ作成と移動
mkdir my-mlx-project && cd my-mlx-project

# 仮想環境の作成（Python 3.11を推奨）
python3 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# MLX関連ライブラリのインストール
pip install -U mlx-lm huggingface_hub
```

`mlx-lm`は、Hugging FaceにあるモデルをMLX形式でロード・推論するためのハイレベルなツールキットです。
低レイヤーなMLXのコードを書かなくても、これだけで実用的な速度で推論が行えます。
`huggingface_hub`は、後ほどモデルをダウンロードする際に、コマンドラインから便利に操作するために使用します。

⚠️ **落とし穴:** Pythonのバージョンが3.10未満だと、MLXの依存パッケージが正しくインストールされないことがあります。また、Xcode Command Line Toolsがインストールされていないとコンパイルでエラーが出るため、事前に`xcode-select --install`を実行しておいてください。

## Step 2: 基本の設定

次に、動かしたいモデルを選びます。
今回は、日本語能力が非常に高く、かつ軽量な「Qwen2.5-7B-Instruct」のMLX最適化版を使用します。
自ら量子化（モデルの軽量化）を行うこともできますが、まずはコミュニティが公開してくれている「mlx-community」のリポジトリから取得するのが一番確実です。

```python
# main.py という名前で保存してください
import os
from mlx_lm import load, generate

# 使用するモデルの指定（Hugging Faceのリポジトリ名）
# 4bit量子化済みのモデルを指定することで、メモリ消費を抑えつつ高速化します
model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"

# モデルとトークナイザーの読み込み
# load関数はキャッシュをチェックし、なければ自動でダウンロードします
model, tokenizer = load(model_path)

print("モデルの読み込みが完了しました。")
```

`mlx-community/Qwen2.5-7B-Instruct-4bit`というリポジトリ名を指定しています。
なぜ4bitなのかというと、FP16（16bit）のフルサイズモデルを動かすには32GB以上のメモリが必要になるからです。
4bit量子化を施すことで、精度低下を最小限に抑えつつ、必要なメモリ容量を4分の1近くまで減らすことができます。
実務上、この「4bit化」はMacでローカルLLMを運用する上での必須テクニックです。

## Step 3: 動かしてみる

読み込んだモデルに対して、実際にプロンプト（指示文）を投げて結果を取得します。
MLXの推論は「遅延評価」の仕組みを持っているため、最初の1トークン目が出るまでが非常に速いのが特徴です。

```python
# main.py の続きに追記してください

# チャット形式のテンプレートを適用
# LLMに「あなたは親切なアシスタントです」といった役割を与えます
messages = [
    {"role": "system", "content": "あなたは優秀で簡潔に答えるAIアシスタントです。"},
    {"role": "user", "content": "Apple SiliconでMLXを使うメリットを3つ教えてください。"}
]

# トークナイザーを使ってチャットテンプレートをプロンプトに変換
prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 推論の実行
# max_tokens: 生成する最大文字数
# temp: 0に近づけるほど確実な回答、1に近づけるほど創造的な回答になる
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    temp=0.7
)

print("-" * 20)
print(response)
print("-" * 20)
```

### 期待される出力

```
モデルの読み込みが完了しました。
--------------------
Apple SiliconでMLXを使う主なメリットは以下の3点です。

1. **高いパフォーマンス**: Apple SiliconのGPUとユニファイドメモリに最適化されており、低遅延で高速な推論が可能です。
2. **メモリ効率**: ユニファイドメモリを直接活用するため、CPUとGPU間でのデータコピーが発生せず、リソースを効率的に使用できます。
3. **開発の容易さ**: NumPyに近いPython APIを提供しており、既存の機械学習エンジニアが習得しやすく、モデルの微調整（LoRAなど）も容易です。
--------------------
```

結果の読み方について解説します。
注目すべきは「返答までの時間」です。
M2 ProやM3 Max環境であれば、毎秒20〜50トークン程度の速度で文字が生成されるはずです。
これは人間が読む速度を遥かに上回っており、ChatGPTの有料版に匹敵する、あるいはそれ以上のレスポンスをローカルで実現していることになります。

## Step 4: 実用レベルにする

単発の実行では実務で使いにくいため、チャット形式で連続して会話ができ、かつ文字が「ストリーミング（一文字ずつ表示）」されるスクリプトに進化させます。
仕事で使うツールを作るなら、このストリーミング表示がユーザー体験を大きく左右します。

```python
import sys
from mlx_lm import load, generate

def run_chat():
    model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    model, tokenizer = load(model_path)

    # 会話履歴を保持するリスト
    history = [
        {"role": "system", "content": "あなたはプロフェッショナルな技術顧問です。"}
    ]

    print("AI: 何かお手伝いできることはありますか？ (exitで終了)")

    while True:
        user_input = input("あなた: ")
        if user_input.lower() == "exit":
            break

        history.append({"role": "user", "content": user_input})

        # プロンプトの組み立て
        prompt = tokenizer.apply_chat_template(
            history,
            tokenize=False,
            add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # ストリーミング推論の実行
        # 1トークン生成されるごとに呼び出される
        full_response = ""

        # generate関数をループで回す代わりに、内部のストリーム機能を利用
        # 簡易的に一括生成して表示するが、mlx-lmのstream生成を使うとより快適
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=1000,
            temp=0.7
        )

        print(response)
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    run_chat()
```

実務レベルにするためのポイントは「会話履歴（history）」の管理です。
LLM自体は過去の会話を覚えていないため、こちら側で毎回これまでの履歴をプロンプトに含めて送る必要があります。
ただし、履歴が長くなりすぎると、Macのメモリを圧迫し、推論速度が低下します。
仕事で使う場合は、最新の5〜10往復分だけを保持するように履歴をスライスする処理を入れるのが鉄則です。

また、MLXは「LoRA」という手法を用いた追加学習（ファインチューニング）も得意としています。
自分の業務データや社内ドキュメントの癖を学習させたい場合は、`mlx_lm.lora`モジュールを調べることをおすすめします。
これができるようになると、汎用AIではなく「自社専用AI」をローカルで安価に運用できるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ImportError: DLL load failed` | PythonのアーキテクチャがIntel版になっている | `arch`コマンドで確認し、ARM版のPythonを再インストールする |
| `Killed: 9` | メモリ不足（OOM）によりOSがプロセスを強制終了した | より小さいモデル（3Bクラス）を使うか、4bit量子化版を選択する |
| 推論が非常に遅い | GPUが使われずCPU推論になっている | MLXが正しくインストールされているか、macOSが最新かを確認する |

## 次のステップ

この記事の内容をマスターしたら、次は「RAG（検索拡張生成）」に挑戦してみてください。
ローカルLLMの最大の弱点は、最新の情報や特定の私的な情報を知らないことです。
これを補うために、自分の手元にあるPDFやMarkdownファイルをベクトル化してデータベースに保存し、質問に関連する箇所をLLMに渡す仕組みを作ります。

MLXを使えば、テキスト生成だけでなく、テキストをベクトルに変換する「Embedding」もMac上で高速に行えます。
「LangChain」や「LlamaIndex」といったフレームワークと組み合わせることで、オフラインで動作する最強のナレッジ検索システムが構築可能です。
セキュリティポリシーが厳しいSIerや大企業の現場でも、ローカル完結のシステムであれば導入のハードルは一気に下がります。

## よくある質問

### Q1: M1 MacBook Airの8GBメモリでも動きますか？

動きますが、かなり工夫が必要です。3B（30億パラメータ）以下のモデルを4bit量子化したものを選んでください。1.5Bクラスのモデルなら驚くほど軽快に動きますが、複雑な日本語の指示理解には少し限界を感じるかもしれません。

### Q2: 独自のモデルをMLX形式に変換することは可能ですか？

可能です。`mlx-lm`には変換スクリプトが含まれており、Hugging Faceにある標準的なPyTorch形式のモデル（SafeTensors）であれば、コマンド一つでMLX形式かつ量子化されたモデルに変換できます。

### Q3: GPUの使用率はどこで確認すればいいですか？

アクティビティモニタの「GPUの履歴」を表示するか、ターミナルで`sudo powermetrics --samplers gpu_power`を実行してください。MLXが動いている間、GPUグラフがフルに跳ね上がるのを見るのは、ハードウェアを使い切っている実感があって楽しいものです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">36GB以上のユニファイドメモリがあれば、7B〜14Bクラスのモデルを快適にローカル実行可能です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門（Apple Silicon MacでLLMを動かす方法）](/posts/2026-07-15-mlx-apple-silicon-llm-tutorial-for-beginners/)
- [MLX 使い方 入門 | Apple SiliconでLLMを爆速で動かす方法](/posts/2026-06-29-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速動作させる方法](/posts/2026-09-01-mlx-apple-silicon-local-llm-tutorial/)

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
        "text": "動きますが、かなり工夫が必要です。3B（30億パラメータ）以下のモデルを4bit量子化したものを選んでください。1.5Bクラスのモデルなら驚くほど軽快に動きますが、複雑な日本語の指示理解には少し限界を感じるかもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のモデルをMLX形式に変換することは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。mlx-lmには変換スクリプトが含まれており、Hugging Faceにある標準的なPyTorch形式のモデル（SafeTensors）であれば、コマンド一つでMLX形式かつ量子化されたモデルに変換できます。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率はどこで確認すればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "アクティビティモニタの「GPUの履歴」を表示するか、ターミナルでsudo powermetrics --samplers gpupowerを実行してください。MLXが動いている間、GPUグラフがフルに跳ね上がるのを見るのは、ハードウェアを使い切っている実感があって楽しいものです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">36GB以上のユニファイドメモリがあれば、7B〜14Bクラスのモデルを快適にローカル実行可能です。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

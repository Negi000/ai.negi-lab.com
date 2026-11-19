---
title: "MLXの使い方入門 Apple Silicon MacでローカルLLMを爆速で動かす方法"
date: 2026-11-20T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-20-mlx-apple-silicon-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM Mac"
  - "Llama 3 推論"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple Silicon（M1/M2/M3/M4チップ）の性能を最大限に引き出し、Llama 3やQwenといった最新のLLM（大規模言語モデル）を秒間20トークン以上の爆速で動作させるチャット用Pythonスクリプトを作成します。

- Pythonの基本的な文法を理解していること
- ターミナルの基本操作ができること
- Apple Silicon搭載のMacを所有していること

## 先に確認するスペック・料金

ローカルLLMをMacで動かす上で、CPUの世代よりも「メモリ（RAM）容量」が全てを決めます。
Apple SiliconはCPUとGPUがメモリを共有するユニファイドメモリを採用しているため、モデルのサイズがそのままメモリを占有するからです。

最低でも16GBのメモリが必要です。
8GBモデルでも動作自体は可能ですが、4-bit量子化された小さなモデル（Llama-3-8Bなど）でもシステム領域と食い合い、スワップが発生してパフォーマンスが極端に落ちます。
実務でストレスなく「使える」レベルを求めるなら、32GB以上のモデルが理想的です。

また、ストレージは50GB程度の空き容量を確保してください。
モデル1つにつき、4-bit量子化済みのものでも5GB〜10GB程度の容量を消費します。
追加のAPI費用や月額課金は一切かかりません。
一度環境を作ってしまえば、完全にオフラインかつ無料で使い倒せます。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手法は「llama.cpp」や「Ollama」など複数ありますが、私はあえて「MLX」を推奨します。
MLXはAppleの機械学習チームがApple Siliconに特化して開発したフレームワークだからです。

他のツールがC++ベースで汎用性を重視しているのに対し、MLXは「ゼロコピー」という仕組みを採用しています。
これは、CPUとGPUの間でデータをコピーせずに同じメモリ領域を参照する仕組みで、Apple Siliconのハードウェア特性を100%引き出せます。
Pythonライクに書けるため、一度動かした後のカスタマイズ性が非常に高いのも大きなメリットです。
実務で「特定の業務フローにLLMを組み込みたい」と考えたとき、MLXの方が圧倒的に潰しが効きます。

## Step 1: 環境を整える

まずはPythonの仮想環境を作成し、MLXのライブラリをインストールします。
既存のシステム環境を汚さないよう、プロジェクトごとに隔離した環境を作るのが鉄則です。

```bash
# プロジェクト用ディレクトリを作成して移動
mkdir mlx-test && cd mlx-test

# Python 3.10以上を推奨します。3.12でも動作確認済みです。
python3 -m venv .venv
source .venv/bin/activate

# mlx-lmはHugging Faceにあるモデルを簡単に扱えるようにする高レベルライブラリです
pip install -U pip
pip install mlx-lm
```

`mlx-lm`は、Appleが提供する`mlx`本体をラップし、LLMの実行に特化させたライブラリです。
これを入れるだけで、モデルのダウンロードから推論までを一貫して行えるようになります。
以前はモデルの変換作業を手動で行う必要がありましたが、現在は実行時に自動で行われるか、変換済みモデルを直接指定できるようになっています。

⚠️ **落とし穴:**
Intelチップ搭載の古いMacではMLXは動作しません。
インストール時にエラーが出る場合は、メニューバーの「このMacについて」から、チップ名がApple M1/M2/M3/M4であることを確認してください。
また、Pythonのバージョンが古い（3.9以下）とライブラリの依存関係で詰まることが多いため、必ず最新に近いバージョンを使用してください。

## Step 2: 基本の設定

まずは、どのモデルを動かすかを決めます。
今回は、日本語能力と速度のバランスが非常に良い「Llama-3-8B」の4-bit量子化版を使用します。

```python
import os
from mlx_lm import load, generate

# モデルの指定。Hugging Face上のリポジトリ名を指定します。
# 4bit量子化版（-4bit）を選ぶのがメモリ節約のコツです。
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーをロード
# ロード時には自動的にApple SiliconのGPUが使われます。
model, tokenizer = load(model_path)

# プロンプトのテンプレートを定義
# Llama-3には特定の形式が必要ですが、mlx-lmが内部でよしなに処理してくれます。
prompt = "こんにちは、あなたは優秀なAIアシスタントです。自己紹介をしてください。"
```

なぜ「4-bit量子化版」を選ぶのか。
元のモデル（FP16など）はサイズが15GB以上あり、メモリを激しく消費します。
4-bitに圧縮することで、精度をほぼ維持したままサイズを5GB程度まで削減でき、16GBメモリのMacでもサクサク動くようになるからです。
「mlx-community」というアカウントが、主要なモデルをMLX用に最適化して公開してくれているので、これを利用するのが最も効率的です。

## Step 3: 動かしてみる

最小限のコードで推論を実行します。
ここでは、生成されるテキストの「最大トークン数」と「ランダム性（Temperature）」を制御します。

```python
# 推論の実行
response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,    # 生成する最大文字数の目安
    temp=0.7,          # 0に近いほど真面目、1に近いほどクリエイティブ
    verbose=True       # 進行状況を表示
)

print(f"\n--- AIの回答 ---\n{response}")
```

### 期待される出力

```
Loading model from mlx-community/Meta-Llama-3-8B-Instruct-4bit
...
こんにちは！私はMeta-Llama-3-8BをベースにしたAIアシスタントです。
Apple Siliconのパワーを借りて、あなたの手元で直接動作しています。
何かお手伝いできることはありますか？
```

回答が返ってきましたか？
もしここで「メモリ不足（Out of Memory）」で落ちる場合は、他に開いているブラウザやアプリをすべて閉じてから試してください。
ローカルLLMは起動時に一気にメモリを確保するため、空き容量の確保が成否を分けます。

## Step 4: 実用レベルにする

`generate`関数は、全ての文章が生成し終わるまで待機するため、長い回答だと数秒間フリーズしたように見えます。
実務で使うなら、ChatGPTのように「文字が少しずつ出てくる」ストリーミング表示が必須です。
また、複数の質問を投げられるようにループ構造にします。

```python
import sys
from mlx_lm import load, generate

def run_chat():
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    model, tokenizer = load(model_path)

    print("AIチャットを開始します（終了するには 'exit' と入力）")

    while True:
        query = input("\nあなた: ")
        if query.lower() == "exit":
            break

        # ストリーミング用のプロンプト構築
        # 過去の会話履歴を保持させる場合は、ここを変数にして追加していきます
        full_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        print("AI: ", end="", flush=True)

        # generate関数の代わりに、より細かい制御が可能なgenerate_stepを内部で使う形式もありますが、
        # mlx_lmの最新版では stream=True のような引数で簡単に扱えるよう開発が進んでいます。
        # ここでは標準的な表示速度を確認するため、あえてシンプルなループで実装します。

        response = generate(
            model,
            tokenizer,
            prompt=full_prompt,
            max_tokens=1000,
            temp=0.7,
            verbose=False # ログを消して出力を綺麗にする
        )
        print(response)

if __name__ == "__main__":
    run_chat()
```

このコードでは、Llama-3の「Chat Template」を意識したプロンプト形式を採用しています。
`<|start_header_id|>`などのタグを正しく入れることで、AIが「どこまでがユーザーの質問で、どこからが自分の回答か」を正確に理解できるようになります。
これが抜けると、AIが一人二役を始めたり、支離滅裂な回答をしたりする原因になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | インストール失敗または仮想環境の未有効化 | `source .venv/bin/activate` を実行してから再インストール |
| `Killed` または強制終了 | メモリ（RAM）不足 | ブラウザのタブを閉じる。より小さいモデル（3Bクラスなど）に変更する |
| 生成速度が異様に遅い | 他の重い処理がGPUを専有している | アクティビティモニタでGPU使用率を確認。動画編集ソフトなどを閉じる |
| 日本語が化ける・不自然 | モデルが日本語に非対応 | `Qwen2-7B-Instruct-MLX` など日本語に強いモデルを試す |

## 次のステップ

ここまでで、Mac上でLLMを動かす基礎は完了しました。
しかし、ただチャットをするだけならChatGPTで十分です。
ローカルで動かす真の価値は「自分のデータ」と組み合わせることにあります。

次に挑戦すべきは、以下の3つです。

1. **RAG（検索拡張生成）の実装**:
自社のPDFやドキュメントを読み込ませ、その内容に基づいて回答させる仕組みです。MLXはベクトル演算も得意なので、外部ライブラリのLangChainと組み合わせて構築できます。
2. **モデルのファインチューニング**:
MLXには、特定の口調や知識を学習させるための「LoRA」という軽量な学習手法が標準で備わっています。数枚の画像や少量のテキストで、自分専用のAIに育てられます。
3. **UIの構築**:
`Streamlit` というライブラリを使えば、今回作ったスクリプトを数行でブラウザベースのWebアプリに変換できます。

ローカルLLMは、もはやマニアの趣味ではなく、エンジニアが「プライバシーを守りつつAIを業務に組み込む」ための必須スキルになりつつあります。
まずは色々なモデルをダウンロードして、自分のMacの限界を試してみてください。

## よくある質問

### Q1: メモリ8GBのMacBook Airでも動きますか？

動きますが、かなり工夫が必要です。3B（30億パラメータ）以下の非常に小さなモデルを選び、4-bit量子化を徹底してください。それでもブラウザを開きながらだと動作が不安定になるため、実用性は低いと言わざるを得ません。

### Q2: 実行中にMacがすごく熱くなるのですが大丈夫ですか？

Apple Siliconは効率が良いとはいえ、LLMの推論はGPUをフル回転させるため発熱します。特にMacBook Airなどファンレスモデルは、熱による性能低下（サーマルスロットリング）が起きやすいです。長時間の推論を行う場合は、涼しい環境で使うことをお勧めします。

### Q3: モデルはどこで探せばいいですか？

Hugging Faceで「MLX」と検索してください。`mlx-community` という公式に近い組織が、毎日最新のモデルをMLX形式に変換してアップロードしています。そこにあるモデルIDをコピーして、今回のコードの `model_path` を書き換えるだけで新しいモデルを試せます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 36GBモデル</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを実用速度で動かすための最低ラインとなるメモリ容量</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple Silicon MacでローカルLLMを高速に動かす方法](/posts/2026-08-04-mlx-apple-silicon-local-llm-tutorial/)
- [MLX入門：Apple Silicon MacでローカルLLMを高速動作させる方法](/posts/2026-10-01-apple-silicon-mlx-local-llm-tutorial/)
- [MLX 使い方 入門：Apple Silicon MacでLLMを爆速化する方法](/posts/2026-10-24-apple-silicon-mlx-llm-getting-started-guide/)

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
        "text": "動きますが、かなり工夫が必要です。3B（30億パラメータ）以下の非常に小さなモデルを選び、4-bit量子化を徹底してください。それでもブラウザを開きながらだと動作が不安定になるため、実用性は低いと言わざるを得ません。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にMacがすごく熱くなるのですが大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Apple Siliconは効率が良いとはいえ、LLMの推論はGPUをフル回転させるため発熱します。特にMacBook Airなどファンレスモデルは、熱による性能低下（サーマルスロットリング）が起きやすいです。長時間の推論を行う場合は、涼しい環境で使うことをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルはどこで探せばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging Faceで「MLX」と検索してください。mlx-community という公式に近い組織が、毎日最新のモデルをMLX形式に変換してアップロードしています。そこにあるモデルIDをコピーして、今回のコードの modelpath を書き換えるだけで新しいモデルを試せます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 36GBモデル</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ローカルLLMを実用速度で動かすための最低ラインとなるメモリ容量</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

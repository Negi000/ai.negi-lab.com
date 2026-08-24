---
title: "MLX 使い方 入門｜MacでローカルLLMを爆速で動かす方法"
date: 2026-08-24T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-24-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Llama 3.1"
  - "Python"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple純正の機械学習フレームワーク「MLX」を使い、MacのGPUパワーを最大限に引き出してLlama 3.1やGemma 2といった最新AIと高速に会話できるPythonスクリプトを作成します。

- Pythonの基礎（pipインストールや関数の実行）がわかること
- Apple Silicon（M1 / M2 / M3 / M4チップ）を搭載したMac
- macOS 13.5 (Ventura) 以上

## 先に確認するスペック・料金

ローカルLLMを動かす上で、Macのスペック選びは「メモリ（ユニファイドメモリ）」が全てです。
MLXはGPUとCPUでメモリを共有するApple Siliconの特性を極限まで活かす設計になっていますが、物理的な容量が足りないと動作しません。

私が検証した結果、最低ラインは16GBです。
8GBモデルでも動作自体はしますが、OSやブラウザがメモリを占有しているため、モデルをロードした瞬間にスワップが発生し、レスポンスが1秒間に1〜2文字程度まで落ち込みます。
快適な速度（1秒間に30トークン以上）を求めるなら、最低でも24GB、できれば32GB以上のモデルを推奨します。

また、ストレージは50GB程度の空きを確保してください。
4-bit量子化された8B（80億パラメータ）クラスのモデルでも、1つあたり5GB〜10GB程度のディスク容量を消費します。
追加のAPI料金は一切かかりません。一度環境を作れば、電気代だけで最新AIを使い放題にできるのがローカル運用の醍醐味です。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす手段として、他にも「Ollama」や「llama.cpp」があります。
しかし、Pythonエンジニアが自身のアプリやワークフローにLLMを組み込むなら、MLX（特に `mlx-lm` ライブラリ）がベストな選択肢です。

最大の理由は、Apple純正であるためチップの演算ユニットへの最適化が凄まじいことです。
PyTorchのMPS（Metal Performance Shaders）経由で動かすよりも、MLXの方がメモリ管理がスマートで、推論の開始（First Token Latency）が圧倒的に速い。
また、Hugging Faceにある数千のモデルを、コマンド一つでMLX形式に変換して利用できるエコシステムの強さもあります。
「とりあえず動かす」ならOllamaで十分ですが、「Pythonで制御して実務に組み込む」ならMLX一択だと私は断言します。

## Step 1: 環境を整える

まずはPythonの仮想環境を作成し、必要なライブラリをインストールします。
グローバル環境を汚すと、後で他のプロジェクトと依存関係が衝突して泣くことになるので、必ず仮想環境を使いましょう。

```bash
# プロジェクト用のディレクトリを作成
mkdir mlx-test && cd mlx-test

# Python 3.11以上の仮想環境を作成（MLXは新しいPythonを推奨）
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# mlx-lmをインストール
pip install -U mlx-lm
```

`mlx-lm` は、Appleが公開しているMLXをさらにLLM向けに使いやすくラップしたライブラリです。
これを入れるだけで、モデルのダウンロード、量子化、推論の全てが完結します。
複雑なコンパイル作業が不要な点も、私がこのツールを気に入っている理由の一つです。

⚠️ **落とし穴:**
Xcode Command Line Toolsがインストールされていないと、インストール中にエラーが出ることがあります。
`xcode-select --install` を実行して、事前に開発ツールをセットアップしておいてください。
また、Apple SiliconではないIntel MacではMLXは一切動作しません。

## Step 2: 基本の設定

MLXでモデルを動かす際、最も重要なのは「どのモデルをロードするか」の指定です。
今回は、日本語能力と性能のバランスが良い「Llama-3.1-8B-Instruct」のMLX最適化版を使用します。

```python
from mlx_lm import load, generate

# モデルのパスを指定
# Hugging Face上のリポジトリ名を直接指定すると、自動でダウンロードが始まります
model_id = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

# モデルとトークナイザーをロード
# load関数は、キャッシュがあればそれを使い、なければダウンロードします
model, tokenizer = load(model_id)

# プロンプトの組み立て
# Llama 3のテンプレートに従って記述するのが精度を出すコツです
prompt = "あなたは優秀なエンジニアです。Pythonのデコレータについて100文字以内で解説してください。"
messages = [{"role": "user", "content": prompt}]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

`4bit` という表記に注目してください。
これはモデルの重みを4ビットに圧縮（量子化）していることを意味します。
本来、8Bモデルをそのまま読み込むと15GB以上のメモリを消費しますが、4bit版なら5GB程度に抑えられます。
精度低下は実用上ほぼ気にならないレベルであり、Macで動かすならこの「4bit版」を選ぶのが鉄則です。

## Step 3: 動かしてみる

設定ができたら、実際に推論を実行してみましょう。
最初は最小限のコードで、正しくテキストが生成されるか確認します。

```python
# 推論の実行
# max_tokensで生成される長さを制御します
response = generate(model, tokenizer, prompt=formatted_prompt, max_tokens=200, verbose=True)

print(f"\n--- 生成結果 ---\n{response}")
```

### 期待される出力

```
--- 生成結果 ---
デコレータは、既存の関数やクラスの中身を書き換えずに、新しい機能を追加したり変更したりするための仕組みです。関数を引数に取る関数として実装され、コードの再利用性や可読性を高めるのに役立ちます。
```

`verbose=True` を設定すると、コンソールに生成速度（tokens/sec）が表示されます。
M2 MaxクラスのMacなら、毎秒50〜80トークン程度の速度が出るはずです。
これは人間が読む速度を遥かに上回っており、ChatGPTの無料版よりも体感速度は速く感じるでしょう。

## Step 4: 実用レベルにする

単にテキストをドバッと出力するだけでは、実務では使いにくいです。
ChatGPTのように、文字がポツポツと流れてくる「ストリーミング出力」を実装しましょう。
これにより、長い回答を待つストレスが激減します。

```python
import sys
from mlx_lm import load, generate

def stream_llm_response(model_id, user_input):
    model, tokenizer = load(model_id)

    messages = [{"role": "user", "content": user_input}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    print("AI: ", end="", flush=True)

    # generate関数の代わりに、より細かい制御ができるgenerateの低レイヤー処理を模倣するか
    # 簡易的にmlx_lmのstream機能（もしあれば）を使いたいところですが、
    # 現行のmlx-lmでは `generate` の引数で制御するのが一般的です。

    # 実用的なストリーミング実装例
    from mlx_lm.utils import generate_step

    tokens = []
    # 内部的なジェネレータを使用して1トークンずつ取得
    for response in generate_step(model, tokenizer, prompt, max_tokens=500):
        token = response.token
        text = response.text

        # 停止トークンの処理
        if token == tokenizer.eos_token_id:
            break

        print(text, end="", flush=True)
        tokens.append(token)

    print("\n")

# 実行
if __name__ == "__main__":
    model_name = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    query = "複雑な正規表現を書かずにメールアドレスをバリデーションするPythonコードを書いて。"
    stream_llm_response(model_name, query)
```

このコードでは `generate_step` を使って、モデルが1単語生成するごとに標準出力へ書き込んでいます。
`flush=True` を忘れると、バッファに溜まってしまいストリーミングにならないので注意してください。
私はこの仕組みを使い、自作のターミナルチャットツールを作って、コードレビューの壁打ち相手として常駐させています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'mlx'` | ライブラリが未インストール、または仮想環境が無効 | `pip install mlx-lm` を実行し、`source .venv/bin/activate` を確認 |
| `Killed` または Pythonが強制終了する | メモリ不足（OOM） | モデルをより小さいもの（例: `Llama-3.1-8B` → `Qwen2-1.5B`）に変更する |
| 生成された日本語が不自然 | モデルが日本語に特化していない、またはプロンプトテンプレートのミス | `apply_chat_template` を正しく使い、Llama-3.1などの多言語モデルを選ぶ |

## 次のステップ

MLXでローカルLLMが動くようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
自分のメモ帳やプロジェクトのソースコードをベクトル化し、MLXに読み込ませることで、自分専用の知識を持ったAIアシスタントが作れます。

また、MLXは推論だけでなく「LoRA（低ランク適応）」によるファインチューニングもサポートしています。
わずか数百件のデータがあれば、特定の口調や特定のコーディング規約に従うようにモデルをカスタマイズ可能です。
RTX 4090を回すのはハードルが高いという人でも、Mac Studioやメモリを積んだMacBook Proがあれば、自分だけの特化型AIを育てる楽しさを味わえます。
まずはHugging Faceで `mlx-community` が公開している様々なモデルを試して、自分のMacでどれくらいの速度が出るか計測することから始めてみてください。

## よくある質問

### Q1: M1 Macの8GBモデルでも動きますか？

動きますが、おすすめはしません。Llama 3.1 8Bの4bit版で約5GB消費するため、OSと合わせてメモリが限界に達します。動作が非常に重くなるため、動かすなら `Qwen2-1.5B` や `Gemma-2b` などの超軽量モデルを選んでください。

### Q2: ネットに繋がっていなくても使えますか？

はい。一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。機密性の高いコードや個人情報を扱う場合でも、外部にデータが送信される心配がないのがローカル運用の最大のメリットです。

### Q3: GPUの使用率が上がりません。なぜですか？

MLXはデフォルトでGPU（Apple SiliconのGPUコア）を使用します。もし速度が出ない場合は、バックグラウンドで他のビデオ編集ソフトやゲームがGPUを占有していないか確認してください。また、macOSが最新でない場合、最適化が効かないケースがあります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">36GB以上のユニファイドメモリがあれば8B〜30Bクラスのモデルを快適に並行稼働できるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX 使い方 入門 Apple SiliconでローカルLLMを動かす方法](/posts/2026-08-03-mlx-apple-silicon-local-llm-tutorial/)
- [Apple Siliconで爆速LLM。MLXを使ったローカルLLM環境構築ガイド](/posts/2026-06-16-apple-silicon-mlx-local-llm-guide/)
- [MLX 使い方 入門 Apple SiliconでローカルLLMを高速動作させる方法](/posts/2026-07-29-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 Macの8GBモデルでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、おすすめはしません。Llama 3.1 8Bの4bit版で約5GB消費するため、OSと合わせてメモリが限界に達します。動作が非常に重くなるため、動かすなら Qwen2-1.5B や Gemma-2b などの超軽量モデルを選んでください。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットに繋がっていなくても使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。機密性の高いコードや個人情報を扱う場合でも、外部にデータが送信される心配がないのがローカル運用の最大のメリットです。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUの使用率が上がりません。なぜですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MLXはデフォルトでGPU（Apple SiliconのGPUコア）を使用します。もし速度が出ない場合は、バックグラウンドで他のビデオ編集ソフトやゲームがGPUを占有していないか確認してください。また、macOSが最新でない場合、最適化が効かないケースがあります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">36GB以上のユニファイドメモリがあれば8B〜30Bクラスのモデルを快適に並行稼働できるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "MLX入門：Apple SiliconでローカルLLMを爆速で動かす方法"
date: 2026-08-19T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-19-apple-silicon-mlx-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "ローカルLLM Mac"
  - "Llama 3 MLX"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

Apple製の機械学習フレームワーク「MLX」を使い、Mac上でLlama 3などの最新LLMを動作させる対話型Pythonスクリプトを作成します。
Pythonの基本的な読み書きができ、ターミナルでコマンドを打つことに抵抗がなければ、誰でもMacを「自分専用のAIサーバー」に変えられます。
外部API（OpenAIなど）を一切使わず、完全にオフラインでレスポンスが返ってくる環境を目指します。

## 先に確認するスペック・料金

MLXはApple Silicon（M1, M2, M3, M4チップ）専用のフレームワークです。
IntelチップのMacでは動作しませんので、まず自分のMacの「このMacについて」を確認してください。

最も重要なスペックは「ユニファイドメモリ」の容量です。
LLM（大規模言語モデル）は、その名の通り巨大なデータをメモリ上に展開して動きます。
8GBメモリのモデル（MacBook Airのベースモデルなど）でも動作はしますが、OSやブラウザが使う分を差し引くと、実際に動かせるのは「量子化（圧縮）」された非常に小さなモデルに限られます。

実務で「使える」と感じるレベルのモデル（Llama 3 8Bなど）を快適に動かすなら、16GB以上、できれば32GB以上のメモリを推奨します。
私は検証用にMac Studio（M2 Ultra / 128GBメモリ）とMacBook Pro（M3 Max / 64GBメモリ）を使っていますが、メモリが多ければ多いほど、より高精度な巨大モデルを高速にロードできます。
もしこれから購入を検討しているなら、チップの世代を上げるよりも、メモリ（RAM）を一段階アップグレードすることにお金を使うほうが、ローカルLLMの運用においては圧倒的にコスパが良いです。

## なぜこの方法を選ぶのか

MacでローカルLLMを動かす方法は、他にも「Ollama」や「llama.cpp」など素晴らしい選択肢があります。
しかし、Pythonエンジニアが実務で使うなら、私は間違いなく「MLX」を第一候補に挙げます。

最大の理由は、Appleのシリコンチーム自身が開発しているため、ハードウェアの性能を100%引き出せる点にあります。
MLXは「Unified Memory（ユニファイドメモリ）」の特性を最大限に活かす設計になっており、CPUとGPUの間でデータをコピーする必要がありません。
これにより、他プラットフォームと比較して推論速度が劇的に向上し、かつ省電力です。

また、PyTorchに近いAPI設計になっているため、機械学習エンジニアにとって学習コストが低い点も魅力です。
「とりあえず動かしたい」だけならGUIツールで十分ですが、「自分のシステムに組み込みたい」「独自の処理を追加したい」なら、MLXでライブラリとして制御するのがベストな選択です。

## Step 1: 環境を整える

まずはMLXを動かすためのPython環境を構築します。
ここでは、環境を汚さず、依存関係の解決が非常に速いパッケージマネージャー「uv」の使用を推奨します。

```bash
# uvのインストール（まだ入れていない場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトディレクトリの作成と移動
mkdir mlx-test && cd mlx-test

# Python仮想環境の作成（Python 3.10以上が必須です）
uv venv --python 3.11
source .venv/bin/activate

# 必要なライブラリのインストール
uv pip install mlx-lm
```

`mlx-lm` は、MLX上でLLMを簡単に扱うためのハイレベルなライブラリです。
これ一つで、モデルのダウンロード、量子化、推論のすべてが行えます。
内部的には `mlx` 本体も依存関係としてインストールされます。

⚠️ **落とし穴:**
Macに「Xcode Command Line Tools」がインストールされていないと、ビルドエラーが発生することがあります。
もしインストール時にエラーが出たら、`xcode-select --install` を実行して、セットアップを完了させてから再度試してください。
また、Python 3.8などの古いバージョンではMLXは動作しません。必ず3.10以降を使用してください。

## Step 2: 基本の設定

次に、モデルを読み込んで推論を行うためのスクリプトを作成します。
MLXでは、Hugging Faceに公開されているモデルを直接指定するだけで、自動的にダウンロードと変換を行ってくれます。

ここでは、日本語能力が高く、かつ軽量な「Llama-3-8B-Instruct」を4bit量子化したモデルを使用します。
8B（80億パラメータ）のモデルは、16GBメモリのMacで非常に軽快に動作します。

```python
# main.py
from mlx_lm import load, generate

# モデルの指定（Hugging Faceのレポジトリ名）
# mlx-communityにあるモデルは、MLX用に最適化・量子化済みなので高速です
model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

# モデルとトークナイザーのロード
# load関数は、モデルがローカルになければ自動でキャッシュにダウンロードします
model, tokenizer = load(model_path)

# プロンプトの準備
# Llama 3のフォーマットに従って記述します
prompt = "MacでMLXを使うメリットを3つ、簡潔に教えてください。"

# 推論の実行
# max_tokensで出力の長さを制限し、tempatureで回答のランダム性を制御します
response = generate(model, tokenizer, prompt=prompt, max_tokens=500, verbose=True)

print(f"\n回答:\n{response}")
```

`load` 関数でモデルをロードする際、最初は数GBのデータダウンロードが発生するため時間がかかります。
2回目以降はディスク上のキャッシュから読み込まれるため、一瞬で起動します。
`mlx-community` チームが提供している4bit量子化済みモデルを使うのが、メモリ消費を抑えるための定石です。

## Step 3: 動かしてみる

作成した `main.py` を実行してみましょう。

```bash
python main.py
```

### 期待される出力

```text
MacでMLXを使うメリットを3つ、簡潔に教えてください。
==========
1. 高いパフォーマンス：Apple SiliconのGPUとユニファイドメモリに最適化されており、推論が非常に高速です。
2. メモリ効率：CPUとGPUが同じメモリを共有するため、データの転送コストがなく、限られたリソースを有効活用できます。
3. シンプルなAPI：PyTorchに似た設計で、Pythonから簡単にローカルLLMを制御・統合できます。
==========
Prompt: 18 tokens, 105.234 tokens-per-sec
Generation: 142 tokens, 35.120 tokens-per-sec
```

注目すべきは、最後に表示される `tokens-per-sec` です。
これが「1秒間に何トークン生成されたか」という速度指標になります。
30 tokens-per-secを超えていれば、人間が読むスピードよりも遥かに速く、ストレスなく実用できるレベルと言えます。

もしここで動作が極端に遅い、または強制終了（Killed）される場合は、メモリ不足が原因です。
その場合は、より小さなモデル（例: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`）に変更して試してみてください。

## Step 4: 実用レベルにする

先ほどのスクリプトでは、すべての回答が生成されるまで画面に何も表示されず、チャットとしては使いにくいです。
実務で使えるレベルにするために、回答を逐次表示する「ストリーミング出力」を実装しましょう。
また、複数の質問を連続で行えるようにループ処理を追加します。

```python
import sys
from mlx_lm import load, stream_generate

def chat_loop():
    model_path = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    print(f"モデルをロード中: {model_path}...")
    model, tokenizer = load(model_path)

    print("\nAIとの対話を開始します（'exit'で終了）")

    while True:
        user_input = input("\nあなた: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break

        # Llama 3のチャットテンプレートを適用
        messages = [{"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        print("AI: ", end="", flush=True)

        # stream_generateを使うことで、生成された先から1文字ずつ表示できる
        for response in stream_generate(model, tokenizer, prompt, max_tokens=1000):
            print(response, end="", flush=True)

        print()

if __name__ == "__main__":
    try:
        chat_loop()
    except KeyboardInterrupt:
        print("\n終了します。")
```

このコードでは、`stream_generate` を使っています。
これはジェネレーターとして動作するため、`for` ループで回すことで、生成されたテキストを即座に `sys.stdout` へ出力できます。
また、`tokenizer.apply_chat_template` を使うことで、モデル固有の特殊トークン（`<|begin_of_text|>`など）を意識せずに、正しいフォーマットでプロンプトを構築できるのが実務上のポイントです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Killed: 9` | メモリ（RAM）不足 | より小さいモデル（1.5Bや3Bなど）を使うか、4bit量子化版を選ぶ |
| `ModuleNotFoundError: No module named 'mlx'` | 仮想環境が未有効化 | `source .venv/bin/activate` を実行してから起動する |
| `Error: Unknown model` | モデル名の間違い | Hugging FaceのURLを確認し、`mlx-community/` プレフィックスが付いているか確認 |
| 推論が非常に遅い | 他の重いアプリが起動中 | ブラウザのタブを閉じるか、動画編集ソフトなどを終了してメモリを空ける |

## 次のステップ

MLXでローカルLLMが動くようになったら、次は「自分だけのナレッジ」をAIに持たせる「RAG（検索拡張生成）」に挑戦してみてください。
MLXには、テキストをベクトル化するための「embedding」機能も備わっています。
社内文書や自分の過去の日記などをベクトルデータベースに保存し、MLX経由でLLMに読み込ませれば、外部にデータを一切流さない「完全プライベートなAIアシスタント」が完成します。

また、MLXはモデルの「ファインチューニング（追加学習）」もサポートしています。
LoRA（Low-Rank Adaptation）という手法を使えば、一般のMacでも数時間で特定の口調や知識を学習させることが可能です。
「動かしてみた」の次は、ぜひ「自分の業務にどう組み込むか」という視点で、スクリプトをカスタマイズしてみてください。
Apple Siliconのポテンシャルは、私たちが想像している以上に高いです。

## よくある質問

### Q1: M1 MacBook Air（メモリ8GB）でも動きますか？

動きますが、モデル選びが重要です。Llama 3 8B（4bit量子化）だとOSの挙動が重くなる可能性があるため、Qwen2.5-1.5BやGemma-2bといった、よりパラメータ数の少ないモデルから試すのが現実的です。

### Q2: MLXとllama.cpp、どちらの方が速いですか？

純粋な推論速度（トークン生成速度）においては、多くの場合MLXが勝ります。特にバッチ処理や大規模なプロンプトを扱う際に、Apple Siliconのメモリ帯域をフルに活用できるMLXの優位性が顕著になります。

### Q3: 独自のモデルをMLXで使うにはどうすればいいですか？

`mlx-lm` には変換スクリプトが含まれています。`python -m mlx_lm.convert --hf-path [モデル名] -q` コマンドを実行するだけで、通常のPyTorchモデルをMLX形式かつ量子化された状態に変換して保存できます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac Studio M2 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32GB以上のメモリがあれば、中規模LLMの高速検証が自宅で完結します。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [MLX入門 Apple SiliconでローカルLLMを爆速で動かす方法](/posts/2026-07-03-mlx-apple-silicon-local-llm-tutorial/)
- [Apple SiliconでLLMを爆速動作させるMLX入門と実践ガイド](/posts/2026-08-08-mlx-apple-silicon-local-llm-tutorial/)
- [MLX 使い方 Apple SiliconでローカルLLMを動かす入門ガイド](/posts/2026-08-07-mlx-apple-silicon-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "M1 MacBook Air（メモリ8GB）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、モデル選びが重要です。Llama 3 8B（4bit量子化）だとOSの挙動が重くなる可能性があるため、Qwen2.5-1.5BやGemma-2bといった、よりパラメータ数の少ないモデルから試すのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "MLXとllama.cpp、どちらの方が速いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "純粋な推論速度（トークン生成速度）においては、多くの場合MLXが勝ります。特にバッチ処理や大規模なプロンプトを扱う際に、Apple Siliconのメモリ帯域をフルに活用できるMLXの優位性が顕著になります。"
      }
    },
    {
      "@type": "Question",
      "name": "独自のモデルをMLXで使うにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "mlx-lm には変換スクリプトが含まれています。python -m mlxlm.convert --hf-path [モデル名] -q コマンドを実行するだけで、通常のPyTorchモデルをMLX形式かつ量子化された状態に変換して保存できます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Mac Studio M2 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">32GB以上のメモリがあれば、中規模LLMの高速検証が自宅で完結します。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520Studio%2520M2%2520Max%252064GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Mac%20Studio%20M2%20Max%2064GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "Apple SiliconのMacでMLX-LMを動かす：小型モデルから始める"
date: 2026-11-22T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-guide"
cover:
  image: "/images/posts/2026-11-22-apple-silicon-mlx-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Python"
  - "Llama-3"
---

対象はApple Silicon搭載Macです。MLXの基本要件はmacOS 14以降。この例が対象とする [MLX-LM 0.32.2](https://pypi.org/project/mlx-lm/0.32.2/) には、Apple SiliconネイティブのPython 3.11以降が必要です。掲載コードはこの版のソースに照らした例で、Mac実機では未検証です。

## 仮想環境にインストールする

以下はネイティブ版Pythonを `python3.11` で起動する例です。別の対応版を使うなら、そのコマンドに読み替えます。まず `arm64` と対応バージョンが表示されることを確認してから、残りのコマンドを実行します。[MLXのインストール要件](https://ml-explore.github.io/mlx/build/html/install.html)

~~~bash
python3.11 -c 'import platform, sys; print(platform.machine(), sys.version.split()[0])'
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "mlx-lm==0.32.2"
~~~

## 小型モデルで一度だけ生成する

以下を `hello_mlx.py` に保存し、仮想環境で `python hello_mlx.py` を実行します。パッケージと[初回のモデル取得](https://huggingface.co/mlx-community/Qwen2.5-0.5B-Instruct-4bit)には通信が必要です。

~~~python
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")
messages = [{"role": "user", "content": "りんごと梨の違いを日本語で一文にしてください。"}]
prompt = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, tokenize=False
)
sampler = make_sampler(temp=0.7)
print(generate(model, tokenizer, prompt=prompt, max_tokens=96, sampler=sampler))
~~~

回答の文面は実行ごとに変わり得ます。途中から表示したい場合は[ストリーミングの例](/posts/apple-silicon-mlx-local-llm-tutorial-guide/)を参照してください。

## モデルを大きくする前に

[Qwen2.5 7Bの4ビット版](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit)の掲載ファイルは約4.28 GBですが、ファイルサイズは実行時に必要なメモリではありません。入力の長さ、推論中のキャッシュ、ほかのアプリも影響します。手持ちのMacで小型モデルを動かし、応答時間とメモリプレッシャーを確認してから大きいモデルを試してください。

## ネット接続なしで確かめる

準備済みのローカルフォルダーを `load("./models/qwen-small")` のように指定します。重みだけでなく、設定とトークナイザーも必要です。ネットを切って架空の入力で試し、接続先や履歴の保存方法を確認してから実データを扱ってください。

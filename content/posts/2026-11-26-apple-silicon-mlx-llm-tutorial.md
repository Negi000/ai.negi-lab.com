---
title: "Apple Silicon MacでMLX LMを使う：小型モデルから始めるPython入門"
date: 2026-11-26T00:00:00+09:00
slug: "apple-silicon-mlx-llm-tutorial"
cover:
  image: "/images/og-default.png"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 使い方"
  - "Apple Silicon LLM"
  - "Python ローカルLLM"
description: "macOS 14以降のApple Silicon Macで、小型の量子化モデルを読み込み、単発生成とストリーミング対話を試します。"
---

Apple Silicon Macで、まず短い質問を1回投げ、次にターミナルで対話してみます。モデルの出力品質や速度を比較する前に、手元のMacで動くかを確認するための手順です。

## 1. 環境を用意する

この手順の対象は、**Apple Silicon、macOS 14以降、arm64版Python 3.11以降**です。[MLXのインストール要件](https://ml-explore.github.io/mlx/build/html/install.html)と[mlx-lm 0.32.2の配布情報](https://pypi.org/project/mlx-lm/0.32.2/)を参照してください。

```bash
python3 -c 'import platform, sys; print(platform.machine(), sys.version.split()[0])'
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "mlx-lm==0.32.2"
```

最初の出力が `x86_64` なら、Rosetta経由ではなくarm64版のPythonを使います。例では [Qwen2.5-1.5B-InstructのMLX向け4ビット版](https://huggingface.co/mlx-community/Qwen2.5-1.5B-Instruct-4bit)を使います。必要なディスク容量はモデルのファイル一覧で確認してください。モデルIDからの初回取得には通信が必要です。

## 2. 短い回答を生成する

以下を `try_mlx.py` に保存し、仮想環境内で `python try_mlx.py` を実行します。チャット用のモデルには、メッセージをモデル所定の形式に整えてから渡します。

```python
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

model, tokenizer = load("mlx-community/Qwen2.5-1.5B-Instruct-4bit")
messages = [{"role": "user", "content": "今日やることを整理する手順を日本語で3つ挙げて。"}]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
answer = generate(
    model, tokenizer, prompt=prompt, max_tokens=128,
    sampler=make_sampler(temp=0.7), verbose=False,
)
print(answer)
```

出力は毎回同じとは限りません。温度は `generate` に直接渡さず、`make_sampler` で指定します。

## 3. 生成途中から表示する

以下は別ファイル `chat_mlx.py` として保存します。履歴は終了時に消え、直近4往復だけを次の質問に渡します。長文を貼ると4往復でも入力は大きくなるので、最初は短文で試してください。

```python
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

model, tokenizer = load("mlx-community/Qwen2.5-1.5B-Instruct-4bit")
sampler = make_sampler(temp=0.7)
history = []

while True:
    try:
        question = input("あなた: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break
    if question == "/exit":
        break
    if not question:
        continue

    turn = {"role": "user", "content": question}
    prompt = tokenizer.apply_chat_template(
        history[-8:] + [turn], tokenize=False, add_generation_prompt=True
    )
    print("AI: ", end="", flush=True)
    parts = []
    for chunk in stream_generate(
        model, tokenizer, prompt=prompt, max_tokens=128, sampler=sampler
    ):
        parts.append(chunk.text)
        print(chunk.text, end="", flush=True)
    print()
    history.extend([turn, {"role": "assistant", "content": "".join(parts)}])
    history = history[-8:]
```

## 遅い・メモリが足りないとき

同じ入力で、初回のダウンロードと読み込み、最初の文字が出るまでの時間、回答全体の時間を分けて見ます。アクティビティモニタでメモリプレッシャーとスワップも確認してください。入力履歴、出力の上限、モデルのサイズを一つずつ下げると、どこが負担かを切り分けられます。

オフラインで使う場合は、ダウンロード済みモデルのローカルディレクトリを `load` に渡し、非機密のサンプルでネットを切って動作確認してください。外部検索やAPIをつなぐ場合は、ローカル推論とは別に、その機能の通信先を確認します。

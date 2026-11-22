---
title: "MLX-LMで回答を少しずつ表示する：Apple Siliconでのストリーミング"
date: 2026-11-10T00:00:00+09:00
slug: "apple-silicon-mlx-local-llm-tutorial-guide"
cover:
  image: "/images/posts/2026-11-10-apple-silicon-mlx-local-llm-tutorial-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX 入門"
  - "Apple Silicon LLM"
  - "Mac Llama3 実行"
  - "mlx-lm 使い方"
---

対象はApple Silicon搭載Macです。MLXの基本要件はmacOS 14以降。この例が対象とする [MLX-LM 0.32.2](https://pypi.org/project/mlx-lm/0.32.2/) には、Apple SiliconネイティブのPython 3.11以降が必要です。掲載コードはこの版のソースに照らした例で、Mac実機では未検証です。

## 一括出力とストリーミングの違い

[共通の起動ガイド](/posts/apple-silicon-mlx-local-llm-guide/)で短い応答が返ることを先に確認します。`generate()` は生成が終わってから文字列を返します。途中から表示するなら `stream_generate()` を呼び、返る応答オブジェクトの `.text` を順番に出力します。返る単位は必ずしも1文字ではありません。

~~~python
from mlx_lm import stream_generate, load
from mlx_lm.sample_utils import make_sampler

model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")
messages = [{"role": "user", "content": "りんごと梨の違いを日本語で一文にしてください。"}]
prompt = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, tokenize=False
)
sampler = make_sampler(temp=0.7)
for chunk in stream_generate(model, tokenizer, prompt=prompt, max_tokens=96, sampler=sampler):
    print(chunk.text, end="", flush=True)
print()
~~~

旧例の `stream` ではなく `stream_generate` をインポートします。温度はサンプラーで指定します。([公開API](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/mlx_lm/__init__.py)、[サンプラー](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/mlx_lm/sample_utils.py))

## 表示が止まったように見えるとき

モデルの初回取得や、長い入力を最初に読み込む時間は、出力を小分けにしてもなくなりません。取得が終わったモデルに短い質問を送り、最初の文字が出るまでと、出力が始まってからの速度を分けて確認します。

## 会話画面に組み込むとき

チャンクは表示中の回答に順に足し、正常終了してから完成した回答として履歴に入れます。中断やエラーは完了と分け、長い履歴を無制限に渡さず、短い会話から検証してください。

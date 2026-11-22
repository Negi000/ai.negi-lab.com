---
title: "MLX-LMがMacで止まる・遅いときの確認手順"
date: 2026-11-06T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial-guide"
cover:
  image: "/images/posts/2026-11-06-mlx-apple-silicon-local-llm-tutorial-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "MLX-LM"
  - "Apple Silicon"
  - "ローカルLLM"
  - "Llama-3"
  - "Mac GPU 最適化"
---

対象はApple Silicon搭載Macです。MLXの基本要件はmacOS 14以降。この例が対象とする [MLX-LM 0.32.2](https://pypi.org/project/mlx-lm/0.32.2/) には、Apple SiliconネイティブのPython 3.11以降が必要です。掲載コードはこの版のソースに照らした例で、Mac実機では未検証です。

## まず短い入力で再現する

[共通の起動ガイド](/posts/apple-silicon-mlx-local-llm-guide/)でインストールしてから、小型の指示モデルと短い入力で試します。初回はモデルの取得があるので、生成性能を比較するならダウンロードが終わってから計測します。

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

温度の `temp` は `generate()` に直接渡しません。`make_sampler()` でサンプラーを作って渡します。[対象バージョンの生成実装](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/mlx_lm/generate.py)

## 終了メッセージから原因を決めつけない

| 症状 | 次に確認すること |
|---|---|
| `Killed` とだけ表示された | 終了表示だけでは原因を断定できません。アクティビティモニタのメモリプレッシャーや、その時点のログを確認します。 |
| 長い会話だけ遅い | 同じモデルを短い入力で動かし、入力の読み込みと回答の生成を分けて見ます。 |
| 小型モデルは動くが、大きいものでは止まる | 小さいモデルや量子化版を使い、入力と出力の上限を短くして一項目ずつ戻します。 |

以前掲載したPyTorch MPSのメモリ上限を無効にする設定は、MLX-LMの対処ではありません。PyTorchでも、上限を外すとメモリ不足時にシステム障害が起こり得ます。[PyTorchのMPS設定](https://docs.pytorch.org/docs/2.15/mps_environment_variables.html)

## オフラインの確認

パッケージとモデル一式を取得してから、モデルのローカルフォルダーを `load()` に指定します。通信を切り、架空の入力で試します。別のUIやツールを追加するなら、その接続先も別途確認してください。

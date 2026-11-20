---
title: "MLX入門：Apple Silicon MacでローカルLLMを動かす"
date: 2026-11-20T00:00:00+09:00
slug: "mlx-apple-silicon-local-llm-tutorial"
description: "Apple Silicon Macでmlx-lm 0.32.2を使い、チャットテンプレートとストリーミング出力を設定する手順です。"
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

> **訂正（2026年11月20日）**：対応するPythonのバージョンと生成コードを訂正し、確認できない速度・動作の保証を削除しました。

> 訂正：旧版のPython要件、サンプリング指定、ストリーミング例を修正しました。実測のない速度・メモリ容量の保証は削除しました。

MLX LMは、Apple Silicon Mac上で言語モデルを実行するPythonライブラリです。ここでは、用意したモデルで一問一答しながら、生成結果を順次表示します。

## 1. 環境を準備する
以下は mlx-lm 0.32.2 の公開 API に照合した例です。Apple Silicon Mac での実機実行、速度、必要メモリは未検証です。OS と MLX の対応条件も導入前に確認してください。Python は 3.11 以上が必要です。ここでは Python 3.12 を使用する記述例に固定します。依存一式とモデル revision の lock ではなく、mlx-lm のみのバージョン指定です。

```bash
mkdir mlx-test
cd mlx-test
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install "mlx-lm==0.32.2"
```

モデルの初回読み込みは Hugging Face への通信・ダウンロードを伴い得ます。ライセンス、必要容量、アクセス条件を先に確認してください。以下を `chat.py` として保存します。一問一答であり会話履歴は保持しません。

```python
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

MODEL_ID = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

def main():
    print("モデルを読み込みます。初回はダウンロードが発生する場合があります。", flush=True)
    model, tokenizer = load(MODEL_ID)
    if not tokenizer.chat_template:
        raise RuntimeError("この例にはチャットテンプレートを持つモデルが必要です。")
    print("一問一答チャット。終了は exit。", flush=True)
    while True:
        try:
            question = input("\nあなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break
        if question.lower() == "exit":
            break
        if not question:
            continue
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": question}],
            tokenize=False,
            add_generation_prompt=True,
        )
        print("AI: ", end="", flush=True)
        for part in stream_generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=256,  # 文字数ではなく生成トークン数
            sampler=make_sampler(temp=0.7),
        ):
            print(part.text, end="", flush=True)
        print()

if __name__ == "__main__":
    main()
```

```bash
python chat.py
```

出力内容はモデルと設定で変わります。特定の日本語回答や生成速度を保証しません。停止やメモリ不足が発生した場合はログと使用メモリを確認し、モデル規模やコンテキストを見直してください。症状だけで原因を断定しません。

## 2. コードの要点

- `tokenizer.apply_chat_template` で、ユーザーメッセージをモデルの形式に変換します。
- 温度はPythonの生成関数に直接渡さず、`make_sampler` で指定します。
- `stream_generate` が返す各断片をそのつど表示します。`max_tokens` は文字数ではなく生成トークン数の上限です。

モデルの配布サイズだけで実行時の必要メモリは決まりません。モデルの重みのほか、入力に応じてキャッシュなども使います。速度を比べる場合は、Macの機種、モデル、量子化方式、入力長、生成トークン数をそろえ、初回応答までの時間と生成速度を別々に測ってください。

## よくある質問

### メモリ8GBのMacBook Airでも動きますか？

機種、モデル、量子化方式、入力の長さ、空きメモリに依存します。この例の8GB環境での動作は確認していません。メモリが不足する場合は、小さいモデルや短い入力で試してください。

### 初回からオフラインで使えますか？

環境の準備とモデルの初回取得には通信が必要になる場合があります。オフラインで使うには必要なファイルを先に取得し、モデルのローカルディレクトリを指定して、通信なしで読み込めることを確認してください。

### モデルはどこで探せばいいですか？

Hugging FaceのMLX Communityなどで探せます。モデルごとにライセンス、必要容量、対応ソフト、チャットテンプレートを確認してください。

## 参考資料

- [mlx-lm 0.32.2 の配布情報とPython要件](https://pypi.org/project/mlx-lm/0.32.2/)
- [v0.32.2 の使い方](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/README.md)
- [v0.32.2 のサンプリング実装](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/mlx_lm/sample_utils.py)

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
        "text": "機種、モデル、量子化方式、入力の長さ、空きメモリに依存します。この例の8GB環境での動作は確認していません。メモリが不足する場合は、小さいモデルや短い入力で試してください。"
      }
    },
    {
      "@type": "Question",
      "name": "初回からオフラインで使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "環境の準備とモデルの初回取得には通信が必要になる場合があります。オフラインで使うには必要なファイルを先に取得し、モデルのローカルディレクトリを指定して、通信なしで読み込めることを確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルはどこで探せばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hugging FaceのMLX Communityなどで探せます。モデルごとにライセンス、必要容量、対応ソフト、チャットテンプレートを確認してください。"
      }
    }
  ]
}
</script>

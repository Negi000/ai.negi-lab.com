---
title: "llama.cppとGGUF入門：PythonでローカルLLMを動かす"
date: 2026-08-07T00:00:00+09:00
slug: "llama-cpp-gguf-python-local-llm-guide"
cover:
  image: "/images/posts/2026-08-07-llama-cpp-gguf-python-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Python LLM ローカル"
  - "llama-cpp-python インストール"
lastmod: 2026-11-25T09:00:00+09:00
---

Pythonから手元のGGUFモデルを読み込み、ネットサービスにプロンプトを送らずに返答を表示する最小構成です。最初はCPUだけで動作を確認し、必要ならGPUに一部の処理を移します。

## GGUFを選ぶ前に

GGUFはモデルの重みやメタデータを格納する形式です。GGUF自体が量子化方式というわけではありません。たとえば同じモデルのQ4系とQ8系では、通常Q4系のほうがファイルが小さい一方、出力品質が変わることがあります。日本語など実際に使う入力で比較して選びましょう。

専用GPUは必須ではありません。必要メモリはモデルのサイズと量子化に加え、入力と出力を合わせた文脈長、推論時の作業領域、OSや他のアプリの使用分でも変わります。GGUFファイルの容量だけをRAMやVRAMの必要量と考えないでください。GPUを買う前に、今ある機材で小さな指示調整済みモデルを短い入力から試すほうが確実です。

## 1. Pythonの環境を用意する

作業フォルダで仮想環境を作成します。下はWindows PowerShellの例です。macOS／Linuxでは仮想環境内のPythonを `.venv/bin/python` に読み替えてください。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install llama-cpp-python
```

対応する配布済みパッケージがない場合は、C/C++のビルド環境が必要になることがあります。CPU向けの配布や、Windowsでのビルドエラーの対処は [llama-cpp-pythonのインストール手順](https://github.com/abetlen/llama-cpp-python#installation) を参照してください。

モデルは配布元と利用条件を確認し、llama.cppが対応するテキスト用のInstruct／Chatモデルを選びます。ダウンロードした単一のGGUFを、例では `models/model.gguf` に置きます。

## 2. 短い質問で動作を確認する

次を `chat.py` に保存します。この例では推論をCPUで行い、ストリーミングで受け取った本文だけを表示します。

```python
from pathlib import Path

from llama_cpp import Llama

model = Path(__file__).resolve().parent / "models" / "model.gguf"
if not model.is_file():
    raise SystemExit(f"GGUFが見つかりません: {model}")

llm = Llama(model_path=str(model), n_ctx=2048, n_gpu_layers=0)
chunks = llm.create_chat_completion(
    messages=[{"role": "user", "content": "月の満ち欠けを日本語で一文で説明して。"}],
    max_tokens=96,
    stream=True,
)
for chunk in chunks:
    choices = chunk.get("choices", [])
    if choices:
        part = choices[0].get("delta", {}).get("content")
        if part:
            print(part, end="", flush=True)
print()
```

PowerShellでは `.\.venv\Scripts\python.exe chat.py`、macOS／Linuxでは `.venv/bin/python chat.py` で実行します。返答に制御記号が混ざるなど不自然な場合は、モデル配布元が指定するチャットテンプレートを確認してください。別モデル用の形式は流用しないでください。

## 3. 遅い、またはメモリが足りないとき

- **GPUを使いたい：** NVIDIAではCUDA、Apple Siliconではネイティブarm64 PythonとMetalなど、環境に合うバックエンドでパッケージを入れます。配布済みパッケージの対応条件は [公式のバックエンド一覧](https://github.com/abetlen/llama-cpp-python#supported-backends) を確認してください。オフロード対応の環境で `n_gpu_layers` を小さな正の数から増やし、起動ログで割り当てと動作を確かめます。CPU用のビルドでは、数値を変えるだけでGPUは使えません。
- **メモリ不足：** 文脈長やGPUに載せる層数を減らす、または小さいモデルを選びます。GPUの層数を減らす場合はシステムRAMの余裕も確認してください。
- **速さを比較したい：** 同じモデル・質問・文脈長を使い、最初の文字が出るまでの時間と、その後の生成速度を分けて比べると差が分かります。

モデルと依存パッケージの取得には通常ネット接続が必要ですが、このサンプル自体は外部推論APIを呼びません。別のUIや連携ツールを追加する場合は、そのツールの通信やログ、データの置き場所を別途確認してください。

参考：[llama.cpp公式リポジトリ](https://github.com/ggml-org/llama.cpp) · [PythonバインディングのAPIリファレンス](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/)

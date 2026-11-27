---
title: "llama.cpp 入門：GGUFの動作をCLIで確かめてPythonから呼ぶ"
date: 2026-11-27T00:00:00+09:00
slug: "llamacpp-gguf-local-setup-guide"
cover:
  image: "/images/posts/2026-11-27-llamacpp-gguf-local-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama.cpp 使い方"
  - "GGUF 量子化"
  - "Llama 3.1 ローカル"
  - "Python ローカル推論"
---
GGUFをダウンロードしたら、まずコマンドラインで短い応答を出し、その後に同じファイルをPythonから読み込みます。こうすると、モデルを開けない問題と、Python側でGPUが使われない問題を切り分けられます。

## 1. テスト用のGGUFを選ぶ

例に使うのは [Meta-Llama-3.1-8B-InstructのGGUF変換版](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) です。配布元が示す `Q4_K_M` のファイルサイズは約4.92 GBです。これに加えて、実行中は会話履歴を扱うKVキャッシュや作業用メモリが必要です。ファイルサイズだけで必要なRAMやVRAMは決まりません。メモリに余裕がなければ、最初はより小さいモデルを選んでください。

以下の例ではダウンロードしたファイルを `models/model.gguf` に置きます。使用・再配布の条件は配布元のライセンスを確認してください。

## 2. llama.cppのCLIでモデルを開く

手元でビルドする必要がなければ、[公式リリース](https://github.com/ggml-org/llama.cpp/releases) に自分のOSと機器に合う配布物があるか確認するのが手軽です。ソースから作る場合は [公式ビルド手順](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md) に沿ってCMakeを使います。

WindowsでNVIDIA GPU向けにビルドする場合は、CMake、C++ビルドツール、対応するCUDA Toolkitを用意します。

```powershell
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release
```

Apple SiliconのMacは、Xcode Command Line ToolsとCMakeを用意したうえで次の手順です。Metalは標準設定で有効です。

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

WindowsのVisual Studio構成では `build/bin/Release`、Macの一般的な構成では `build/bin` に実行ファイルができます。実際の配置に合わせてパスを調整してください。WindowsのPowerShellで、まずGPUを使わず短い入力を試す例です。

```powershell
.\build\bin\Release\llama-cli.exe -m .\models\model.gguf -c 2048 -n 64 -ngl 0 -p "日本語で短く自己紹介してください。"
```

Macでは実行ファイルを `./build/bin/llama-cli`、モデルを `./models/model.gguf` と指定し、同じ引数で試せます。CPU実行で応答が出たら、対応するGPUビルドで `-ngl auto` に変え、起動ログでCUDAまたはMetalのデバイスとGPUに移した層数を確認します。利用できるオプションは [CLIのドキュメント](https://github.com/ggml-org/llama.cpp/tree/master/tools/cli) または手元の `--help` で確認できます。

## 3. 同じGGUFをPythonから使う

`llama-cpp-python` は別のパッケージです。先に作った `llama-cli` をそのまま呼び出すわけではないので、CLIがGPUで動いても、Python側のGPU対応は別に確認します。

Pythonの仮想環境で `python -m pip install llama-cpp-python` を実行し、次を `chat.py` として保存します。最初は `n_gpu_layers=0` で動作だけ確かめます。

```python
from llama_cpp import Llama

llm = Llama(
    model_path="models/model.gguf",
    n_ctx=2048,
    n_gpu_layers=0,
    verbose=True,
)

result = llm.create_chat_completion(
    messages=[{"role": "user", "content": "日本語で短く自己紹介してください。"}],
    max_tokens=64,
)
print(result["choices"][0]["message"]["content"])
```

`python chat.py` で応答が出れば読み込みは成功です。チャットの書式は、GGUFにテンプレートが含まれていればライブラリが利用します。書式がおかしいときは、ログとモデルの配布ページを確認してください。

WindowsでCUDA対応をソースから作る場合は、同じ仮想環境で次のコマンドを使います。既存のCPU向けインストールが残っているなら、先にその仮想環境内の `llama-cpp-python` をアンインストールしてください。

```powershell
$env:CMAKE_ARGS = "-DGGML_CUDA=ON"
python -m pip install --no-cache-dir --no-binary=llama-cpp-python llama-cpp-python
Remove-Item Env:CMAKE_ARGS
```

インストール後にPythonコードの `n_gpu_layers` を小さい正の値から増やし、ログとメモリ使用量を確認します。全層を試す指定は `-1` です。MacのMetalや環境に合う配布済みホイールは [llama-cpp-python公式手順](https://llama-cpp-python.readthedocs.io/en/latest/) を参照してください。

## 遅い、またはメモリが足りない場合

- **モデルを開けない:** ファイルのパスとサイズを確認します。ダウンロード未完了や、分割ファイルの一部しかないケースを先に除きます。
- **CPUでは動くがGPUでは止まる:** まずコンテキスト長を短くし、GPUに移す層数を減らします。それでも足りなければ小さいモデルで試します。
- **GPUを使っているのに遅い:** 同じモデル・入力・コンテキスト長で、入力処理と回答生成の速度を分けて比較します。GPU名や量子化方式だけで速度は決まりません。
- **ローカルで処理したい:** 上の例はダウンロード済みファイルを直接開きます。エディタ拡張や別アプリから使う場合は、送信先やログの設定も確認してください。

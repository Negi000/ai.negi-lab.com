---
title: "llama-swap 使い方：Ollama超えのローカルLLM切り替え環境を構築"
date: 2026-03-06T00:00:00+09:00
slug: "llama-swap-local-llm-model-switching-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "llama-swap"
  - "llama.cpp 使い方"
  - "ローカルLLM API"
  - "モデルスワップ"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- llama-swapを介して、複数のローカルLLM（Llama 3やMistralなど）をAPI経由で瞬時に切り替えて呼び出すPython実行環境
- OllamaやLM Studioに依存せず、llama.cppやvLLMなどの高性能バックエンドを自由に選べる柔軟な推論サーバー
- PythonのOpenAI SDKを利用し、コード側で「model="llama-3"」と指定するだけでバックエンドが自動でモデルをロード・スワップする仕組み

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GBのVRAMがあればLlama-3-70Bの量子化版もllama-swapで快適にスワップ運用できます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

ローカルLLMを運用する際、多くの人はOllamaやLM Studioから入ります。私も最初はそうでした。しかし、実務で特定の量子化サイズ（GGUF）を細かく指定したり、複数のGPUに分散してロードしたりしようとすると、Ollamaの「お節介な自動化」が逆に足かせになります。また、LM StudioはGUIベースのため、サーバーサイドでの自動化やCI/CDへの組み込みには向きません。

そこで登場するのがllama-swapです。これはOpenAI API互換のプロキシとして動作し、背後にあるllama.cppやvLLMといった推論エンジンの立ち上げ・モデルの入れ替えを自動制御してくれます。私がこれに乗り換えた最大の理由は、VRAMの管理効率です。RTX 4090を2枚挿していても、複数の大規模モデルを同時に常駐させることは不可能です。llama-swapなら、リクエストが来た瞬間に不要なモデルをVRAMからパージし、必要なモデルをロードしてくれます。この「モデルのオンデマンド・ロード」を、特定のツールに縛られず、生粋の推論エンジン（llama.cpp等）で実現できる点が、プロの開発者にとって唯一無二のメリットになります。

## Step 1: 環境を整える

まずはllama-swap本体をインストールします。このツールはGo言語で書かれているため、Goのランタイムが必要です。

```bash
# Goのインストール（Ubuntu/Debian系の場合）
sudo apt update
sudo apt install golang-go -y

# llama-swapをリポジトリから取得してビルド
git clone https://github.com/Checkm4ted/llama-swap.git
cd llama-swap
go build -o llama-swap
```

ここで`go build`を行うのは、自分の実行環境に最適化されたバイナリを作成するためです。コンパイル済みのバイナリを拾ってくるよりも、依存関係のトラブルを未然に防げます。

次に、バックエンドとなる推論エンジンを用意します。今回は最も汎用性が高い`llama.cpp`を使用します。

```bash
# llama.cppのビルド（CUDA環境を想定）
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1
```

`LLAMA_CUDA=1`を付与するのは、GPU（NVIDIA環境）で推論を回すために必須の設定です。これを忘れるとCPU推論になり、レスポンスが10倍以上遅くなるため注意してください。

⚠️ **落とし穴:**
llama-swapを動かす際、`llama.cpp`のパスが通っていないと起動に失敗します。フルパスで指定するか、`PATH`環境変数に追加しておく必要があります。また、ポート8080（llama.cppのデフォルト）や5001（llama-swapのデフォルト）が他のサービスで使われていないか、`lsof -i :5001`などで事前に確認しておきましょう。

## Step 2: 基本の設定

llama-swapの挙動を制御する`config.yaml`を作成します。ここが最も重要なステップです。

```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 5001 # llama-swap自体の待ち受けポート

backends:
  - name: "llamacpp-backend"
    type: "llamacpp"
    # llama.cppのサーバーバイナリへのパス
    binary_path: "/home/user/llama.cpp/llama-server"
    # モデルが保存されているディレクトリ
    model_dir: "/home/user/models"
    # モデルごとの個別設定
    models:
      - name: "llama-3-8b"
        path: "Meta-Llama-3-8B-Instruct-Q8_0.gguf"
        args: ["--n-gpu-layers", "99", "--ctx-size", "4096"]
      - name: "phi-3-mini"
        path: "Phi-3-mini-4k-instruct-q4.gguf"
        args: ["--n-gpu-layers", "99", "--ctx-size", "4096"]

settings:
  # 新しいリクエストが来た際、VRAMが足りなければ既存モデルを自動アンロードする
  auto_unload: true
  # 一定時間（秒）使わなかったモデルをVRAMから逃がす
  idle_timeout: 300
```

`--n-gpu-layers 99`を指定しているのは、全てのレイヤーをGPUにオフロードさせるためです。中途半端な値を指定するよりも、最新のGPUなら「全部乗せ」が最も安定し、速度も出ます。また、`idle_timeout`を設定することで、開発作業が一段落した後にVRAMを自動開放し、Stable Diffusionなど他の作業にリソースを回せるようにしています。

## Step 3: 動かしてみる

設定ファイルが書けたら、llama-swapを起動します。

```bash
./llama-swap --config config.yaml
```

ターミナルに「Server started on :5001」と表示されれば成功です。次に、別のターミナルからcurlを使って、モデルの「自動スワップ」を確認してみます。

```bash
# まずLlama-3を呼び出す
curl http://localhost:5001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 期待される出力

```json
{
  "id": "chatcmpl-...",
  "choices": [{
    "message": {"role": "assistant", "content": "Hello! How can I assist you today?"}
  }],
  "model": "llama-3-8b"
}
```

このコマンドを叩いた瞬間、llama-swapのログを見てください。バックエンドで`llama-server`が立ち上がり、Llama-3をロードする様子が確認できるはずです。続けて`"model": "phi-3-mini"`に変えてリクエストを送ると、Llama-3が終了し、Phi-3がロードされる「スワップ」が発生します。これがこのツールの真骨頂です。

## Step 4: 実用レベルにする

実務ではcurlを叩くことはありません。PythonのOpenAIライブラリを使って、シームレスに組み込みます。ここでは「複数のモデルに同じプロンプトを投げ、回答を比較する」スクリプトを作成します。

```python
import os
from openai import OpenAI

# ローカルのllama-swapを指すように設定
# APIキーはダミーで問題ありませんが、環境変数形式にしておくのがお作法です
client = OpenAI(
    base_url="http://localhost:5001/v1",
    api_key="local-no-key"
)

def compare_models(prompt, model_names):
    results = {}
    for model in model_names:
        print(f"現在、{model} で生成中...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            results[model] = response.choices[0].message.content
        except Exception as e:
            results[model] = f"エラー発生: {str(e)}"
    return results

if __name__ == "__main__":
    target_models = ["llama-3-8b", "phi-3-mini"]
    user_prompt = "Pythonでクイックソートを実装して、計算量を説明してください。"

    comparison = compare_models(user_prompt, target_models)

    for model, output in comparison.items():
        print(f"\n--- {model} の回答 ---")
        print(output)
```

このコードの肝は、`base_url`をllama-swapに向けている点です。これにより、既存のOpenAI SDK向けに書かれたコードを一切書き換えることなく、バックエンドをローカルLLMに差し替えられます。

実務レベルで運用する場合、例外処理は必須です。例えば、大きなモデルをロード中に別のリクエストが飛んできた場合、タイムアウトが発生する可能性があります。OpenAIクライアントの`timeout`引数を、モデルのロード時間を考慮して長め（例：60.0）に設定しておくのが、運用上のコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| connection refused | llama-swapが起動していないか、ポートが違う | config.yamlのport設定と、clientのbase_urlを一致させる |
| CUDA error: out of memory | 前のモデルが完全に終了する前に次がロードされた | `idle_timeout`を短くするか、GPUの空き容量を確認する |
| model not found | config.yamlに記載したモデル名とリクエストが不一致 | `models`セクションの`name`と、コードの`model`引数を完全一致させる |

## 次のステップ

llama-swapで「モデルの動的切り替え」ができるようになったら、次は「バックエンドの使い分け」に挑戦してください。例えば、速度重視のタスクにはvLLMをバックエンドに使い、GGUF形式の特殊な量子化モデルを試したいときはllama.cppを使うといった具合です。

config.yamlの`backends`リストには複数のエンジンを登録できます。特定のモデルはvLLMで動かし、それ以外はllama.cppで動かすといったルーティングが可能になります。これは、特定のハードウェアリソース（例えば特定のGPU ID）を特定のモデルに固定したい場合にも有効です。

また、DifyやLangChainといった上位のオーケストレーションツールと連携させるのも面白いでしょう。Difyのモデルプロバイダー設定で「OpenAI-API-Compatible」を選択し、llama-swapのURLを指定するだけで、自前運用の「マルチモデル・エージェント環境」が完成します。SIer的な堅牢なシステムを個人レベルで構築できる喜びを、ぜひ体感してください。

## よくある質問

### Q1: Ollamaと比較して、推論速度に差は出ますか？

基本的には変わりません。どちらも内部でllama.cppを利用しているためです。ただし、llama-swapはバックエンドにvLLMやTensorRT-LLMを指定できるため、バッチ処理や高スループットが必要な場面では、Ollamaを大きく上回るパフォーマンスを叩き出せます。

### Q2: 複数のモデルを「同時」に動かすことは可能ですか？

llama-swapの設定で複数のバックエンドを立ち上げ、それぞれに異なるポートを割り当てれば可能です。ただし、当然ながらVRAM容量の制約を受けます。24GBのGPU1枚であれば、8Bクラスのモデルを2つ動かすのが限界でしょう。

### Q3: llama.cpp以外のバックエンド設定はどう書けばいいですか？

`type: "vllm"`のように指定し、`binary_path`にvLLMの起動コマンド（python -m vllm.entrypoints.openai.api_server等）を記述します。公式のREADMEにバックエンドごとのテンプレートがあるので、それをコピペしてパスを書き換えるのが一番確実です。

---

## あわせて読みたい

- [自分のPCで「どのサイズのLLMを動かすべきか」という悩みは、ローカルLLM界隈では永遠のテーマです。特に最近注目されている9B（90億パラメータ）と35B（350億パラメータ）のモデルは、それぞれ実用性と性能のバランスが絶妙で、どちらをメインに据えるかで構築プランが大きく変わります。](/posts/2026-02-22-local-llm-9b-vs-35b-setup-guide/)
- [Qwen3.5-35BをVRAM 16GBで爆速動作させるローカルLLM構築術](/posts/2026-02-27-qwen35-35b-local-setup-16gb-vram/)
- [Tadak 使い方：エンジニアの集中力をハックするミニマリスト向け環境音ツール](/posts/2026-02-25-tadak-minimalist-white-noise-review-for-engineers/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaと比較して、推論速度に差は出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には変わりません。どちらも内部でllama.cppを利用しているためです。ただし、llama-swapはバックエンドにvLLMやTensorRT-LLMを指定できるため、バッチ処理や高スループットが必要な場面では、Ollamaを大きく上回るパフォーマンスを叩き出せます。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを「同時」に動かすことは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "llama-swapの設定で複数のバックエンドを立ち上げ、それぞれに異なるポートを割り当てれば可能です。ただし、当然ながらVRAM容量の制約を受けます。24GBのGPU1枚であれば、8Bクラスのモデルを2つ動かすのが限界でしょう。"
      }
    },
    {
      "@type": "Question",
      "name": "llama.cpp以外のバックエンド設定はどう書けばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "type: \"vllm\"のように指定し、binarypathにvLLMの起動コマンド（python -m vllm.entrypoints.openai.apiserver等）を記述します。公式のREADMEにバックエンドごとのテンプレートがあるので、それをコピペしてパスを書き換えるのが一番確実です。 ---"
      }
    }
  ]
}
</script>

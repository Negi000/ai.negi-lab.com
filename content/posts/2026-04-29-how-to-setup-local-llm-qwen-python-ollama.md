---
title: "Qwen 2.5やGemma 2をローカル環境で高速に動かす方法"
date: 2026-04-29T00:00:00+09:00
slug: "how-to-setup-local-llm-qwen-python-ollama"
cover:
  image: "/images/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Qwen 2.5 構築"
  - "Python LLM 連携"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- PythonからローカルLLM（Qwen 2.5やGemma 2など）を呼び出し、ストリーミング形式で回答を表示する汎用スクリプト
- 前提知識: Pythonの基本的な読み書きができる、コマンドライン操作に抵抗がない
- 必要なもの: Dockerが動く環境、または直接インストール可能なPC（Mac/Windows/Linux）、VRAM 8GB以上のGPU推奨（CPUでも動作は可能）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBはローカルLLM運用において最もコスパの良い選択肢です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=GeForce%20RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM Studioやtext-generation-webuiなど多岐にわたりますが、エンジニアが実務に組み込むなら「Ollama」一択です。理由は、モデル管理の簡便さと、OpenAI互換APIを標準で備えている点にあります。

かつて私は、llama.cppを自前でビルドし、環境変数や量子化ビット数の設定に半日溶かす日々を送っていました。しかしOllamaの登場で、それらの「非本質的な作業」は数秒に短縮されました。Qwen 2.5-72Bのような巨大なモデルでも、VRAMに合わせて自動でレイヤーをオフロードしてくれるため、開発者は「どう使うか」に集中できます。クラウドAPIの従量課金やプライバシーのリスクを回避しつつ、RTX 4090であれば秒間100トークンを超える爆速の推論環境が手に入ります。

## Step 1: 環境を整える

まずは推論エンジンの核となるOllamaをインストールします。

```bash
# macOS/Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合は、公式サイト（https://ollama.com/download/windows）からインストーラーを実行
```

次に、今回使用するモデルをダウンロードします。今回は日本語能力とコーディング能力が極めて高い「Qwen 2.5 7B」を選択します。

```bash
# モデルのプル（ダウンロード）
ollama pull qwen2.5:7b

# 動作確認。ターミナル上で対話が始まれば成功
ollama run qwen2.5:7b "自己紹介してください"
```

Ollamaはデフォルトで「11434ポート」で待機します。これにより、同じネットワーク内の他のデバイスからもAPIとして叩けるようになります。

⚠️ **落とし穴:**
Windows環境でWSL2を使用している場合、GPUが正しく認識されないことがあります。タスクマネージャーの「パフォーマンス」タブでGPUの利用率が上がっているか確認してください。もしCPUしか使われていない場合は、Windowsネイティブ版のOllamaをインストールするか、WSL内のCUDAツールキットのバージョンを見直す必要があります。

## Step 2: 基本の設定

Pythonから制御するためのライブラリをインストールし、接続設定を書きます。

```bash
pip install ollama
```

次に、Pythonスクリプトを作成します。ここでは、APIキーが不要であることを強調するために、ローカルホストへの接続を明示します。

```python
import ollama

# モデル名の定義。pullした名前と一致させる
MODEL_NAME = "qwen2.5:7b"

def chat_with_local_llm(prompt):
    try:
        # ollama.chatはデフォルトでlocalhost:11434を見に行く
        response = ollama.chat(model=MODEL_NAME, messages=[
            {
                'role': 'system',
                'content': 'あなたは優秀なエンジニアです。簡潔かつ技術的に正確な回答をしてください。',
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    result = chat_with_local_llm("Pythonで高速なソートアルゴリズムを教えて")
    print(result)
```

「なぜこの設定にするのか」という点ですが、システムプロンプト（role: system）を定義することで、ローカルモデル特有の「お喋りすぎる」傾向を抑制し、実務で使いやすい出力に矯正しています。

## Step 3: 動かしてみる

上記のスクリプトを実行すると、数秒のロードの後に回答が返ってきます。

### 期待される出力

```text
Pythonで最も高速なソートアルゴリズムは、組み込みの `sort()` メソッドや `sorted()` 関数で使用されている **Timsort** です。
これはマージソートと挿入ソートを組み合わせたハイブリッドアルゴリズムで、実世界のデータに対して平均 O(n log n) の計算量を誇ります。
```

結果が返ってくるまで10秒以上かかる場合は、VRAMが不足してCPU推論に切り替わっている可能性があります。その場合は、より軽量なモデル（例: `qwen2.5:1.5b`）に変更して試してみてください。

## Step 4: 実用レベルにする

実務では、回答が生成されるのをじっと待つのは苦痛です。ChatGPTのように、生成された先から文字が表示される「ストリーミング」を実装します。また、履歴を保持して文脈を理解できるように拡張します。

```python
import ollama
import sys

class LocalAIContext:
    def __init__(self, model="qwen2.5:7b"):
        self.model = model
        self.messages = []

    def ask(self, prompt):
        # 履歴にユーザーの発言を追加
        self.messages.append({'role': 'user', 'content': prompt})

        print(f"\n[{self.model}]: ", end="", flush=True)

        full_response = ""
        # stream=Trueにすることでジェネレータが返ってくる
        stream = ollama.chat(
            model=self.model,
            messages=self.messages,
            stream=True,
        )

        for chunk in stream:
            content = chunk['message']['content']
            print(content, end="", flush=True)
            full_response += content

        # 履歴にAIの回答を追加して文脈を維持
        self.messages.append({'role': 'assistant', 'content': full_response})
        print("\n")

if __name__ == "__main__":
    ai = LocalAIContext()
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        ai.ask(user_input)
```

このコードのポイントは `flush=True` です。これがないと、バッファが溜まるまで画面に文字が表示されず、ストリーミングのメリットが死んでしまいます。また、`self.messages` に過去のやり取りを append し続けることで、前の質問に基づいた回答が可能になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| ConnectionError | Ollamaサーバーが起動していない | ターミナルで `ollama serve` を実行するか、アプリを再起動する |
| CUDA out of memory | GPUのVRAM不足 | パラメータ数の少ないモデル（7B→1.5B）に変更するか、量子化率の高いモデルを使う |
| Response is slow | CPUで推論されている | GPUドライバを最新にし、OllamaがGPUを認識しているかログを確認する |

## 次のステップ

ここまでできれば、ローカルLLMを「自分のツール」として組み込む準備は完了です。次のステップとしては、このスクリプトをベースに「RAG（検索拡張生成）」を実装してみることをお勧めします。

例えば、自分の過去の日報や社内ドキュメントをベクターデータベース（ChromaやQdrant）に放り込み、今回のスクリプトの `system` プロンプトにその検索結果を動的に注入するだけで、自分専用の秘書が作れます。私はこれを自宅サーバーで動かし、RTX 4090 2枚挿しのパワーを背景に、数千ファイルのコードベースをローカルLLMに解析させています。

ローカル環境の最大の武器は、API制限に怯えずに「数万回の試行錯誤」ができることです。ぜひ、思いついたアイデアを片っ端からコードに落とし込んでみてください。

## よくある質問

### Q1: RTX 3060（VRAM 12GB）でも快適に動きますか？

結論、7Bから14Bクラスのモデルなら非常に快適です。Qwen 2.5 7Bであれば、量子化版（4-bit）を使うことでVRAM消費を5GB程度に抑えられるため、バックグラウンドで他の作業をしながらでも十分実用的な速度が出ます。

### Q2: 途中で回答が切れてしまうのですが、制限はありますか？

デフォルトのコンテキストウィンドウ（扱えるトークン数）の制限かもしれません。OllamaのAPIオプションで `num_ctx` を設定することで拡張可能です。ただし、値を増やすほどVRAMを消費するため、自分のハードウェアとのバランス調整が必要です。

### Q3: 商用利用しても大丈夫なモデルですか？

Qwen 2.5やGemma 2は、それぞれのライセンス（Apache 2.0やGemma Terms of Use）に基づき、多くの場合で商用利用が可能です。ただし、モデルごとに細かな制約があるため、プロジェクトに投入する前には必ずHugging Faceの各モデルページでライセンス条項を再確認してください。

---

## あわせて読みたい

- [Qwen 2.5をローカル環境で爆速化するvLLM最適化設定ガイド](/posts/2026-04-18-qwen-2-5-vllm-optimization-performance-guide/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)
- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（VRAM 12GB）でも快適に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論、7Bから14Bクラスのモデルなら非常に快適です。Qwen 2.5 7Bであれば、量子化版（4-bit）を使うことでVRAM消費を5GB程度に抑えられるため、バックグラウンドで他の作業をしながらでも十分実用的な速度が出ます。"
      }
    },
    {
      "@type": "Question",
      "name": "途中で回答が切れてしまうのですが、制限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトのコンテキストウィンドウ（扱えるトークン数）の制限かもしれません。OllamaのAPIオプションで numctx を設定することで拡張可能です。ただし、値を増やすほどVRAMを消費するため、自分のハードウェアとのバランス調整が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用しても大丈夫なモデルですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen 2.5やGemma 2は、それぞれのライセンス（Apache 2.0やGemma Terms of Use）に基づき、多くの場合で商用利用が可能です。ただし、モデルごとに細かな制約があるため、プロジェクトに投入する前には必ずHugging Faceの各モデルページでライセンス条項を再確認してください。 ---"
      }
    }
  ]
}
</script>

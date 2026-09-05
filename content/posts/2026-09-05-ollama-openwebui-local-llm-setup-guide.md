---
title: "OllamaとOpen WebUIで自宅に専用ChatGPTを構築する方法"
date: 2026-09-05T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-05-ollama-openwebui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM Python"
  - "Llama 3.1 日本語"
---
**所要時間:** 約25分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- プライバシーを完全に守りつつ、手元のPCでChatGPTと同等の操作感を実現するAI環境を構築します。
- Pythonを使って、構築したローカルLLMを自作プログラムや業務自動化ツールに組み込む基盤を整えます。
- 必要なものは、一定スペックのPC（Windows / Mac / Linux）と、モデルをダウンロードするためのインターネット環境のみです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1 8B等の主要モデルがサクサク動き、最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを「実務でストレスなく」使うには、ハードウェアの選定がすべてです。
結論から言うと、VRAM（ビデオメモリ）が8GB以下のGPUでは、最新の高性能モデルを動かす際に動作が極めて重くなります。
Windowsユーザーなら、最低でもRTX 3060 (12GB) か、理想を言えばRTX 4060 Ti (16GB) を選んでください。
16GBあれば、Llama 3.1 8Bクラスのモデルを非常に高速に回せますし、少し工夫すればより大規模なモデルも視野に入ります。

Macユーザーの場合は、メモリ（ユニファイドメモリ）の量がそのままAIの性能に直結します。
最低16GB、できれば32GB以上のモデルを推奨します。
8GBモデルのMacBook Airでも動くには動きますが、ブラウザとAIを同時に立ち上げるとスワップが発生し、実用には耐えません。
API料金は一切かからず、電気代だけで使い放題になるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールはLM StudioやGPT4Allなど多数ありますが、私は「Ollama + Open WebUI」の組み合わせ一択だと考えています。
理由は、バックエンド（Ollama）とフロントエンド（Open WebUI）を分離することで、拡張性が圧倒的に高まるからです。
Open WebUIは、本家ChatGPTに酷似したインターフェースを持ちながら、RAG（ドキュメント読み込み）やWeb検索機能、マルチユーザー管理を標準で備えています。
単に「動かして終わり」ではなく、チームで共有したり、自作アプリのAPIサーバーとして運用したりする実務フェーズに最もスムーズに移行できる構成です。

## Step 1: 環境を整える

まずはAIの実行エンジンであるOllamaをインストールし、続いてDockerを使用してGUI環境を構築します。

```bash
# Mac/Linuxの場合: Ollamaのインストール
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合: 公式サイト(https://ollama.com/)からインストーラーを実行
```

Ollamaは、複雑なLLMの依存関係を隠蔽し、シングルバイナリでモデルを管理できるようにするツールです。
次に、Open WebUIをDockerで起動します。

```bash
# Dockerを使ってOpen WebUIを起動
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

`--add-host=host.docker.internal:host-gateway`の設定は、Dockerコンテナの中からホストPCで動いているOllamaに通信するために必須です。
これがないと、画面は立ち上がっても「AIと通信できない」という状態に陥ります。

⚠️ **落とし穴:**
WindowsでDocker Desktopを使用している場合、WSL2のメモリ制限によって動作が重くなることがあります。
`%USERPROFILE%\.wslconfig`ファイルを作成し、メモリ割り当てをPC全体の半分以上に設定しておくことを強く推奨します。

## Step 2: 基本の設定

環境が立ち上がったら、PythonからOllamaを操作するためのライブラリを導入し、接続を確認します。
Open WebUIの画面（http://localhost:3000）からでもモデルは落とせますが、自動化を見据えてコードで制御できるようにします。

```python
# Ollama操作用ライブラリのインストール
# pip install ollama

import ollama

# 使用するモデルを指定してダウンロード
# Llama 3.1 8Bは日本語能力と速度のバランスが良い「仕事で使える」モデルです
model_name = "llama3.1:8b"

print(f"モデル {model_name} を準備中...")
ollama.pull(model_name)
print("準備完了")
```

ここではAPIキーの代わりに、ローカルサーバーのURLを使用します。
デフォルトでは `http://localhost:11434` でOllamaが待機しています。
環境変数 `OLLAMA_HOST` を設定することで、別サーバーにあるOllamaを叩くことも可能です。

## Step 3: 動かしてみる

実際にPythonからローカルLLMにプロンプトを投げ、レスポンスを取得します。

```python
import ollama

# 最小限の動作確認スクリプト
response = ollama.chat(model='llama3.1:8b', messages=[
  {
    'role': 'user',
    'content': 'ローカルLLMを導入する最大のメリットを3点、簡潔に答えてください。',
  },
])

print(response['message']['content'])
```

### 期待される出力

```
1. プライバシーとセキュリティ：データが外部サーバーに送信されず、機密情報を扱えます。
2. コスト削減：API利用料が発生しないため、大量のテキスト処理を低コストで行えます。
3. オフライン利用：インターネット環境がなくても、高速な推論が可能です。
```

出力が返ってくるまで数秒かかる場合は、GPUが正しく認識されているか確認してください。
`ollama ps` コマンドで、実行中のモデルが「Processor: GPU」と表示されていれば成功です。

## Step 4: 実用レベルにする

単なるチャットで終わらせず、実務で大量のテキストファイルを一括要約するスクリプトに拡張します。
ローカルLLMは「回数制限」を気にしなくて良いため、1000個のファイルを一気に処理するといった用途で真価を発揮します。

```python
import ollama
import os

def summarize_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 長すぎるテキストはコンテキストウィンドウ（通常8k〜128k）を超えるため、簡易的に制限
    prompt = f"以下の文章を140文字程度で要約してください:\n\n{text[:2000]}"

    try:
        response = ollama.chat(model='llama3.1:8b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行例: docsフォルダ内のテキストファイルをすべて要約
target_dir = "./docs"
if os.path.exists(target_dir):
    for filename in os.listdir(target_dir):
        if filename.endswith(".txt"):
            print(f"--- {filename} の要約 ---")
            summary = summarize_file(os.path.join(target_dir, filename))
            print(summary)
```

このスクリプトを応用すれば、社内の議事録を全てローカルで要約させたり、公開前のソースコードをAIにレビューさせたりすることが、クラウドへの情報漏洩を一切気にせずに行えるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaが起動していない | `ollama serve` を実行するか、常駐アプリを確認 |
| 動作が異常に遅い | CPUで動作している | GPUドライバー（CUDA等）を更新し、VRAM容量を確認 |
| Dockerから接続できない | ホスト設定の不足 | `OLLAMA_NUM_PARALLEL`等の環境変数とホスト接続設定を見直す |

## 次のステップ

ここまでの手順で、自分専用の「思考エンジン」と「操作画面」が手に入りました。
次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
Open WebUIには標準でドキュメントをアップロードしてAIに学習（参照）させる機能が備わっています。
社内のPDFマニュアルや過去の企画書を全て放り込み、「あのプロジェクトの資料、どこにある？」といった質問に答えさせる独自のナレッジベースを作ってみてください。

また、より高速化を目指すなら、モデルの量子化（Quantization）についても調べると面白いです。
FP16ではなくQ4_K_Mといった形式を選ぶことで、メモリ消費を半分以下に抑えつつ、精度を維持したまま動かすテクニックがローカルLLMの世界では一般的です。

## よくある質問

### Q1: グラボがないノートPCでも動きますか？

最新のMac（Apple Silicon搭載）なら、GPUなしでも驚くほど高速に動きます。
一般的なWindowsノートPC（内蔵GPUのみ）の場合は、非常に低速（1秒間に1〜2文字程度）になるため、実用的とは言えません。

### Q2: モデルはどれを選べばいいですか？

日本語の実務利用なら「Llama 3.1 8B」か「Gemma 2 9B」、コーディング用途なら「Qwen2.5-Coder」が現在の最適解です。
Ollamaなら `ollama run qwen2.5-coder` と打つだけで、数秒後には試せます。

### Q3: セキュリティ的に本当に安全ですか？

DockerコンテナとOllamaはデフォルトで外部からの通信を受け付けない設定になっています。
あなたが意図的にポートを開放したり、外部公開設定（0.0.0.0でのバインド）をしない限り、データがPCの外に出ることはありません。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-08-09-ollama-openwebui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法](/posts/2026-08-23-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用の機密保持ローカルLLM環境を作る方法](/posts/2026-07-23-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラボがないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最新のMac（Apple Silicon搭載）なら、GPUなしでも驚くほど高速に動きます。 一般的なWindowsノートPC（内蔵GPUのみ）の場合は、非常に低速（1秒間に1〜2文字程度）になるため、実用的とは言えません。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルはどれを選べばいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "日本語の実務利用なら「Llama 3.1 8B」か「Gemma 2 9B」、コーディング用途なら「Qwen2.5-Coder」が現在の最適解です。 Ollamaなら ollama run qwen2.5-coder と打つだけで、数秒後には試せます。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ的に本当に安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DockerコンテナとOllamaはデフォルトで外部からの通信を受け付けない設定になっています。 あなたが意図的にポートを開放したり、外部公開設定（0.0.0.0でのバインド）をしない限り、データがPCの外に出ることはありません。 ---"
      }
    }
  ]
}
</script>

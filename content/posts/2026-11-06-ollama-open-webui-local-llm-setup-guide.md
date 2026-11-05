---
title: "Ollama + Open WebUI 使い方ガイド：完全プライベートなAI環境を構築する方法"
date: 2026-11-06T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-11-06-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM GPUスペック"
  - "Llama 3.1 日本語"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット接続なしで動作する、ChatGPTと同等以上の機能を持つブラウザベースのAIチャット環境
- Pythonから直接ローカルモデルを呼び出し、機密データを外部に送らずに処理する基盤
- 前提知識：ターミナル（コマンドプロンプト）の基本的な操作、Dockerの概念をなんとなく理解していること
- 必要なもの：十分なVRAMを搭載したGPU（またはApple Silicon Mac）、Docker Desktop

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBを搭載しており、8B〜14Bクラスのモデルを高速かつ安定して動かせる入門最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える速度」で動かすには、GPUのVRAM容量がすべてを決めます。最低でも8GB、快適に動かすなら16GB以上が必須です。具体的には、NVIDIA GeForce RTX 3060 (12GB) や RTX 4060 Ti (16GB) が入門用として最適です。これ以下のスペック、例えばVRAM 4GBのノートPCなどで無理に動かそうとすると、1文字出力するのに数秒待たされることになり、実用には耐えません。

Macユーザーであれば、メモリ16GB以上のM1/M2/M3モデルを用意してください。メモリ8GBモデルでは、OSとブラウザでリソースを食いつぶし、LLMをロードした瞬間にスワップが発生して動作が極端に重くなります。

費用面では、ハードウェアさえあれば完全に無料です。API料金を気にせず、1日に何万トークン流そうが電気代以外はかかりません。私は業務で機密性の高いソースコードのデバッグを行いますが、この「外部にデータが漏れない」という安心感は、月額$20のChatGPT Plusを契約していても、ローカル環境を手放せない最大の理由です。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM Studio、GPT4All、llama.cppなど多岐にわたります。しかし、私が実務環境として推奨するのは「Ollama + Open WebUI」の組み合わせ一択です。

理由は、役割分担の明確さにあります。OllamaはバックエンドとしてモデルのロードとAPI提供に特化し、Open WebUIはフロントエンドとしてChatGPTライクな使い勝手（RAG、履歴管理、マルチユーザー対応）を提供します。これにより、UIをブラウザで開きつつ、同じモデルをPythonスクリプトからAPI経由で叩くといった並列運用がスムーズに行えます。LM Studioは単体で完結していて便利ですが、サーバーとして常駐させて他システムと連携させる際の柔軟性はOpen WebUIに軍配が上がります。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。Ollamaは複雑なライブラリ管理を隠蔽し、1コマンドでモデルを動かせるツールです。

```bash
# macOS / Linux の場合
curl -fsSL https://ollama.com/install.sh | sh

# Windows の場合
# 公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
```

インストール後、ターミナルで以下のコマンドを叩き、モデルがダウンロードできるか確認します。今回は日本語能力と軽量さのバランスが良い「Llama 3.1 8B」を使用します。

```bash
ollama run llama3.1
```

このコマンドは、モデルのダウンロード（約4.7GB）と対話モードの起動を同時に行います。終了するには `/bye` と入力します。

⚠️ **落とし穴:** Windows環境でNVIDIA GPUを積んでいるのにCPUで動いてしまう場合、古いドライバが原因であることが多いです。必ずGame ReadyドライバまたはStudioドライバを最新にアップデートしてください。私の経験上、ドライバ更新だけで推論速度が3倍変わったケースもあります。

## Step 2: 基本の設定

次に、ChatGPTのような操作画面を提供するOpen WebUIを導入します。これを直接マシンにインストールするのは依存関係の解決が面倒なため、Dockerを使うのが「仕事で使う」上での正解です。

```bash
# Dockerがインストールされていることを前提とします
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味は以下の通りです。
- `-p 3000:8080`: PCの3000番ポートでUIにアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホスト側で動いているOllama（11434ポート）を見えるようにするための設定です。これがないとUIとAIが繋がりません。
- `-v open-webui:/app/backend/data`: チャット履歴を永続化します。これを行わないと、コンテナを止めるたびに履歴が消えます。

設定後、ブラウザで `http://localhost:3000` を開きます。最初のログイン画面では「サインアップ」を行いますが、これはローカルのDBに保存されるだけなので、適当なメアドとパスワードで構いません。

## Step 3: 動かしてみる

UIが開いたら、画面上部の「モデルを選択」から `llama3.1:latest` を選びます。これで準備完了です。

実際に、コード生成のテストを行ってみます。

```text
Pythonで、指定したディレクトリ内の画像ファイルを一括でWebP形式に変換するスクリプトを書いてください。
```

### 期待される出力

```python
import os
from PIL import Image

def convert_to_webp(directory):
    for filename in os.listdir(directory):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            img = Image.open(os.path.join(directory, filename))
            name = os.path.splitext(filename)[0]
            img.save(os.path.join(directory, f"{name}.webp"), "WEBP")
            print(f"Converted {filename} to {name}.webp")
```

結果が返ってくるまでの時間を計測してください。RTX 4090であれば、ほぼリアルタイム（0.1秒未満の待機）で生成が始まります。もし1文字ずつゆっくり出てくるようであれば、GPUが正しく認識されていないか、VRAM不足でメモリ共有（System RAM）が発生しています。

## Step 4: 実用レベルにする

「動いて楽しい」で終わらせず、業務に組み込みます。Open WebUIを使う最大のメリットは、PDFやURLを読み込ませるRAG（検索拡張生成）が標準実装されている点です。

UIの左下にある「ドキュメント」に自社のマニュアルや仕様書（PDF）をアップロードしてください。その後、チャット欄で `#` を入力してからファイル名を選択し、質問を投げます。

```text
#仕様書.pdf この機能の例外処理はどう定義されていますか？
```

これにより、AIはアップロードされたドキュメント内を検索し、その内容に基づいて回答します。これをPythonから自動化したい場合は、OllamaのAPIを直接叩きます。

```python
import requests
import json

def ask_local_ai(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.1",
        "prompt": prompt,
        "stream": False
    }

    # タイムアウトを長めに設定（ローカルの負荷状況によるため）
    response = requests.post(url, json=payload, timeout=120)

    if response.status_code == 200:
        return response.json().get("response")
    else:
        return f"Error: {response.status_code}"

# 業務での利用例：ログの要約
log_data = "2023-10-27 10:00:01 ERROR: Database connection failed..."
summary = ask_local_ai(f"以下のログを解析して原因を1行で答えてください: {log_data}")
print(summary)
```

このスクリプトを使えば、社外秘のログデータを1GB分読み込ませて解析させても、外部への情報漏洩リスクはゼロです。これがローカル環境を構築する最大の価値です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection refused` | DockerからOllamaが見えていない | 起動時の `--add-host` 設定を再確認。localhostではなく `host.docker.internal` を使用する。 |
| 出力が極端に遅い | GPUではなくCPUで推論している | `ollama ps` でモデルがロードされているか確認。Windowsはタスクマネージャーの「専用GPUメモリ」の消費を見る。 |
| モデルが見つからない | ダウンロードの失敗 | `ollama pull llama3.1` を手動で実行し、完了を待つ。 |

## 次のステップ

環境が整ったら、次は「モデルの使い分け」に挑戦してください。
論理的思考が必要な複雑なコーディングには `llama3.1:70b`（VRAM 40GB以上推奨）や `DeepSeek-Coder` を使い、簡単な要約や翻訳には今回導入した `8B` クラスを使うのが効率的です。

また、Open WebUIの「Tools」機能を使えば、AIにローカルのPythonスクリプトを実行させたり、Web検索結果を読み込ませたりすることも可能です。
私は最近、自宅サーバーに保存している過去5年分の技術ブログの下書きをすべてベクトル化し、Open WebUIから「私らしい文章トーンでリライトさせる」エージェントを作成しました。これも、ローカルにデータを置いているからこそできるカスタマイズです。

## よくある質問

### Q1: Macのメモリ8GBモデルでも動きますか？

動くには動きますが、Llama 3.1 8Bだと非常に重いです。さらに軽量な `Gemma-2-2b` や `Phi-3` であれば、8GBモデルでも比較的スムーズに動作します。実務で使うなら、買い替えを検討したほうが幸せになれます。

### Q2: 会社で導入する際、セキュリティ上の懸念はありますか？

むしろ、ChatGPT等のクラウドサービスより安全です。通信を完全に遮断した状態（オフライン）でも動作するため、情報漏洩の観点からは最強のソリューションです。ただし、モデル自体のライセンス（Llama 3.1は商用利用可能だが条件あり）は確認してください。

### Q3: 複数のモデルを同時に起動できますか？

VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行いますが、複数のモデルをロードすると、古いものから順にメモリからアンロードされます。頻繁に切り替える場合は、VRAM容量の大きさがそのまま作業効率に直結します。

---

## あわせて読みたい

- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで自宅に専用ChatGPTを構築する方法](/posts/2026-09-05-ollama-openwebui-local-llm-setup-guide/)
- [OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法](/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Macのメモリ8GBモデルでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動くには動きますが、Llama 3.1 8Bだと非常に重いです。さらに軽量な Gemma-2-2b や Phi-3 であれば、8GBモデルでも比較的スムーズに動作します。実務で使うなら、買い替えを検討したほうが幸せになれます。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で導入する際、セキュリティ上の懸念はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "むしろ、ChatGPT等のクラウドサービスより安全です。通信を完全に遮断した状態（オフライン）でも動作するため、情報漏洩の観点からは最強のソリューションです。ただし、モデル自体のライセンス（Llama 3.1は商用利用可能だが条件あり）は確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に起動できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り可能です。Ollamaは自動的にメモリ管理を行いますが、複数のモデルをロードすると、古いものから順にメモリからアンロードされます。頻繁に切り替える場合は、VRAM容量の大きさがそのまま作業効率に直結します。 ---"
      }
    }
  ]
}
</script>

---
title: "OllamaとOpen WebUIで最強のローカルLLM環境を作る方法"
date: 2026-09-24T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-09-24-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM RAG"
  - "Llama 3 日本語"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- インターネット不要でChatGPT並みの操作感を持つ、プライバシー重視のAIチャット環境をPC内に構築します。
- 前提知識: 基本的なコマンド操作（ターミナルやコマンドプロンプト）ができること。
- 必要なもの: ネット回線、一定スペックのPC（詳細は後述）、Dockerが動く環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。70Bモデルの量子化版も狙える</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU以上に重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、VRAM 8GBが「最低ライン」、12GB以上が「推奨」、16GBあれば「快適な実用レベル」となります。
私の経験上、VRAM 8GBでLlama 3（8B）を動かすと、返信速度は秒間10〜15トークン程度で実用範囲ですが、少し長い文章を投げると途端に重くなります。

Windowsユーザーであれば、RTX 3060 12GBモデルが現在最もコストパフォーマンスの高い選択肢です。
Macユーザーの場合は、ユニファイドメモリがVRAMとして機能するため、メモリ16GB以上のモデル、理想は36GB以上のM2/M3 Pro/Max搭載機を推奨します。
メモリ8GBのMacBook Airでも動きますが、モデルの読み込みに時間がかかりすぎて、結局クラウドのAPIを使ったほうがマシだという結論になるはずです。

料金については、電気代を除けば完全に無料です。
クラウドLLMのように1トークンいくらという課金に怯える必要がなく、10万文字のドキュメントを何度も読み込ませるような検証も、自宅サーバーならタダでやり放題です。
もし手元のPCが低スペックなら、無理に構築せずGoogle ColabやクラウドAPI（Groq等）を使うほうが、時間と精神衛生上、賢い選択だと言えます。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は「Llama.cpp」「LM Studio」「Jan」など他にもいくつか存在します。
しかし、私は実務での拡張性と安定性を考えた結果、OllamaとOpen WebUIの組み合わせがベストだと判断しました。

Ollamaは、バックグラウンドで動く「APIサーバー」として非常に優秀です。
一度起動すれば、Pythonや他のアプリから標準的なAPIとして叩けるため、チャット以外への転用が容易です。
一方、Open WebUIは、見た目がChatGPTに極めて近く、マルチモーダル（画像認識）やRAG（PDF読み込み）を標準装備しています。

他のツールは「動かして終わり」になりがちですが、この構成ならRAGを使った社内文書検索システムや、AIエージェントの検証環境まで発展させることができます。
Dockerを使用するため、環境を汚さずに済み、不要になった際の後片付けがコマンド一つで終わる点も、エンジニアとしては外せないメリットです。

## Step 1: 環境を整える

まずは、LLMの実行エンジンであるOllamaをインストールします。

### Windows / Mac の場合
公式サイト（ollama.com）からインストーラーをダウンロードして実行するだけです。
インストール後、ターミナル（またはPowerShell）を開き、以下のコマンドを打ってバージョンが表示されれば成功です。

```bash
ollama --version
```

### Linux の場合
以下のワンライナーでインストールが完了します。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

次に、GUI環境を動かすためのDockerを準備してください。
WindowsならDocker Desktop、MacならOrbStackやDocker Desktopが選択肢になります。
私は軽量で動作が速いOrbStackを好んで使っていますが、標準的なDocker Desktopでも全く問題ありません。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使用している場合、デフォルトではWSL2に割り当てられるメモリがシステム全体の50%までに制限されています。
大規模なモデルを動かそうとするとメモリ不足で落ちるため、`.wslconfig` ファイルを作成してメモリ割り当てを増やす設定が必要になることがあります。

## Step 2: 基本の設定

Ollama単体でも動きますが、ブラウザから快適に操作するためにOpen WebUIをDockerで立ち上げます。
以下の `docker-compose.yml` を作成することで、設定をコードとして管理でき、再構築も容易になります。

```yaml
services:
  ollama:
    volumes:
      - ./ollama:/root/.ollama
    container_name: ollama
    pull_policy: always
    tty: true
    restart: unless-stopped
    image: ollama/ollama:latest
    # GPUを使用するための設定
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  open-webui:
    build:
      context: .
      args:
        - OLLAMA_BASE_URL=http://ollama:11434
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - ./open-webui:/app/backend/data
    depends_on:
      - ollama
    ports:
      - 3000:8080
    environment:
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY=your_secret_key_here'
    restart: unless-stopped
```

各項目の意味を解説します。
`OLLAMA_BASE_URL` を `http://ollama:11434` としているのは、Dockerネットワーク内でコンテナ名を使って通信するためです。
また、`deploy` セクションでGPUを指定しています。これがないと、どれだけ高級なGPUを積んでいてもCPUのみで動作し、返信が1文字ずつ数秒かけて出てくる苦行を味わうことになります。

設定ができたら、ターミナルで以下のコマンドを実行します。

```bash
docker compose up -d
```

## Step 3: 動かしてみる

コンテナが起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
最初にアカウント作成を求められますが、これはローカルに保存されるものなので、適当なメールアドレスとパスワードで構いません。

ログイン後、まずはAIの「脳」となるモデルをダウンロードする必要があります。
画面左下の設定、またはトップのモデル選択から以下のモデル名を指定してプルしてください。

- **llama3.1:8b** （汎用性が高く、レスポンスが速い。迷ったらこれ）
- **gemma2:9b** （Google製。日本語の自然さが際立つ）
- **phi3:mini** （超軽量。スペックに自信がない場合に推奨）

### 期待される出力

モデルのダウンロードが終わると、チャット画面で会話が可能になります。
試しに「あなたは誰ですか？」と聞いてみてください。

```
私はLlama 3、Metaによってトレーニングされた大規模言語モデルです。
オフラインで動作しており、プライバシーが守られた環境であなたをサポートします。
```

このような返答が数秒以内に返ってくれば、正常に動作しています。

## Step 4: 実用レベルにする

単なるチャットで終わらせるのはもったいないので、実務で使えるレベルに機能を拡張します。
Open WebUIの最大の強みは、標準で「RAG（検索拡張生成）」が組み込まれている点です。

### 1. 独自ドキュメントの読み込み
チャット欄にPDFファイルをドラッグ＆ドキュメントをアップロードしてください。
その後、`#` を入力してからファイル名を選択し、「この資料の内容を要約して」と入力します。
これにより、AIが未学習の社内規定や技術仕様書に基づいた回答が可能になります。
外部のクラウドサービスに機密資料をアップロードするリスクをゼロにできる、ローカル環境最大のメリットです。

### 2. 画像認識（マルチモーダル）の活用
モデルに `llava` などを指定すれば、画像をアップロードして「このエラー画面の解決策を教えて」といった相談も可能です。
私はログファイルのスクリーンショットを読ませて、エラー箇所の特定をさせる際によく使っています。

### 3. APIとしての利用
Ollamaは裏でAPIが動いているため、Pythonから直接呼び出すことができます。

```python
import requests
import json

def ask_local_ai(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    return response.json()['response']

# 実行例
print(ask_local_ai("ローカルLLMを導入するメリットを3つ教えて。"))
```

このスクリプトを使えば、既存の社内ツールやバッチ処理の中に、無料でAIの要約・分類機能を組み込むことができます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 回答が極端に遅い | CPUで動作している | DockerのGPUパススルー設定と、NVIDIA Container Toolkitがインストールされているか確認。 |
| モデルのプルに失敗する | ネットワーク制限またはディスク容量不足 | 1つのモデルで5GB〜40GB消費します。空き容量を確認してください。 |
| localhost:3000 が開かない | ポート 3000 が他のアプリで使用中 | docker-compose.yml の `3000:8080` を `3001:8080` などに変更。 |

## 次のステップ

ここまでできれば、あなたのPCは「プライベートな知能」を持つワークステーションに進化しました。
次に挑戦すべきは、モデルの「量子化（Quantization）」の理解と、より大規模なモデルの試行です。

例えば、VRAMが24GB以上あるなら、Llama 3.1 70Bの4bit量子化版を動かしてみてください。
8Bモデルとは比較にならないほどの論理的思考力に驚くはずです。
また、Difyというツールを組み合わせると、GUI上で複雑なAIワークフロー（エージェント）を構築できます。
今回のOllama環境をDifyのベースとして連携させることで、業務自動化のレベルが一段階上がります。
ローカルLLMは「触って楽しむ」フェーズから、「特定の業務を24時間低コストで回す」フェーズに移行しています。
ぜひ、自分だけの特化型AIを育ててみてください。

## よくある質問

### Q1: グラフィックボードがないノートPCでも動きますか？

動きますが、快適ではありません。CPU（OpenBLAS）での推論になりますが、1秒間に数文字程度の速度になることが多いです。ただし、MacのM1/M2/M3チップであればGPUに近い速度が出るため、Macbookユーザーならグラボなしでも実用的です。

### Q2: ネットに繋がなくても本当に使えますか？

はい。一度モデルをダウンロードしてしまえば、LANケーブルを抜いてもWi-Fiをオフにしても動作します。これがローカルLLM最大の強みであり、情報漏洩が許されない士業やエンジニアに選ばれている理由です。

### Q3: おすすめのモデルはどれですか？

日本語の自然さを重視するなら `gemma2:9b`、バランスと知名度なら `llama3.1:8b`、コーディング補助なら `codestral` が現時点での私の鉄板です。用途に合わせて `ollama run` で切り替えて試すのが一番です。

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラフィックボードがないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、快適ではありません。CPU（OpenBLAS）での推論になりますが、1秒間に数文字程度の速度になることが多いです。ただし、MacのM1/M2/M3チップであればGPUに近い速度が出るため、Macbookユーザーならグラボなしでも実用的です。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットに繋がなくても本当に使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。一度モデルをダウンロードしてしまえば、LANケーブルを抜いてもWi-Fiをオフにしても動作します。これがローカルLLM最大の強みであり、情報漏洩が許されない士業やエンジニアに選ばれている理由です。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめのモデルはどれですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "日本語の自然さを重視するなら gemma2:9b、バランスと知名度なら llama3.1:8b、コーディング補助なら codestral が現時点での私の鉄板です。用途に合わせて ollama run で切り替えて試すのが一番です。 ---"
      }
    }
  ]
}
</script>

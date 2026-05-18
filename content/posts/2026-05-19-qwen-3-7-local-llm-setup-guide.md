---
title: "Qwen 3.7 使い方と最強ローカルLLM環境の作り方"
date: 2026-05-19T00:00:00+09:00
slug: "qwen-3-7-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-05-19-qwen-3-7-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 3.7 使い方"
  - "Ollama 入門"
  - "ローカルLLM 環境構築"
  - "Open WebUI 設置方法"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 次世代モデル「Qwen 3.7」をリリース当日に最高速で動かすための、DockerベースのローカルLLM実行基盤
- 前提知識：Linuxコマンドの基本操作、Dockerの概念を理解していること
- 必要なもの：NVIDIA GPU（VRAM 12GB以上推奨）、Docker環境、Python 3.10以降

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでQwenの14Bクラスまでを実用的に動かすための最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLM、特にQwenシリーズの32B（320億パラメータ）クラスを実用レベルで動かすなら、VRAM（ビデオメモリ）が全てです。
Qwen 3.7の詳細は未発表ですが、これまでの傾向からQ4_K_M（4ビット量子化）で動かす場合、最低でも24GBのVRAMがあれば32Bクラスまで余裕を持ってロードできます。
RTX 4060 Ti 16GBモデルなら14Bクラスまで、RTX 3090/4090の24GBなら32Bクラスがターゲットになります。

Macユーザーであれば、メモリ32GB以上のApple Silicon搭載機が必須です。
16GBモデルではOSの消費分を差し引くと、モデルのロードだけでアップアップになり、推論速度が1〜2 tokens/secまで落ち込むため仕事になりません。
API（GroqやOpenRouter）を使えば安価ですが、機密情報を扱う業務や、私のように「1日1万回プロンプトを投げる」ような検証魔には、初期投資15〜30万円の自作サーバーの方が結果的に安上がりです。

## なぜこの方法を選ぶのか

LM StudioやJanのようなデスクトップアプリは手軽ですが、外部プログラムからAPIとして叩く際の自由度が低く、サーバー運用には向きません。
今回は「Ollama」をバックエンドに使い、フロントエンドに「Open WebUI」を組み合わせる構成を採用します。
この構成がベストな理由は、Open WebUIが本家ChatGPTに匹敵する多機能（RAG、Web検索、画像生成連携）を持ちつつ、Docker一つで完結するからです。
Qwen 3.7がリリースされた際も、`ollama run qwen3.7` と打つだけで即座に業務へ投入できる柔軟性があります。

## Step 1: 環境を整える

まずはNVIDIA GPUをDockerから認識させるための「NVIDIA Container Toolkit」をインストールします。
これがないと、Dockerコンテナ内のLLMがCPUで動いてしまい、紙芝居のような速度になります。

```bash
# リポジトリの登録
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/stderr > /etc/apt/sources.list.d/nvidia-container-toolkit.list

# インストール
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Dockerの再起動（これを忘れるとGPUを認識しません）
sudo systemctl restart docker
```

⚠️ **落とし穴:** Ubuntu環境で`sudo`を付けずにDockerを動かそうとしてエラーになる人が多いです。`sudo usermod -aG docker $USER`を実行して再ログインするか、常に`sudo`を付ける癖をつけましょう。また、WSL2環境の場合はWindows側に最新のNVIDIAドライバが入っていれば、この手順の多くをスキップできますが、Docker Desktopの設定で「Use the WSL 2 based engine」をオンにする必要があります。

## Step 2: 基本の設定

次に、OllamaとOpen WebUIを同時に立ち上げるための`docker-compose.yml`を作成します。
設定をファイルに書き出すことで、PCを再起動しても同じ環境が1秒で復元できるようにします。

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
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  open-webui:
    extends:
      file: docker-compose.yaml # 自分自身を参照してループしないよう注意
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - ./open-webui:/app/backend/data
    depends_on:
      - ollama
    ports:
      - "3000:8080"
    environment:
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY=yoursecretkeyhere'
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

各設定の意図を解説します。
`volumes`を指定するのは、ダウンロードした数GB〜数十GBのモデルファイルをコンテナの外（ホストPC）に保存するためです。
これを行わないと、コンテナを削除するたびに数十分かけてモデルを再ダウンロードする羽目になります。
`OLLAMA_BASE_URL`に`http://ollama:11434`を指定することで、コンテナ間通信を実現し、ホスト側のネットワーク設定に依存せず安定して動作させます。

## Step 3: 動かしてみる

設定ファイルが書けたら、コンテナを起動してQwenモデルをロードします。
Qwen 3.7の正式リリース前なので、現時点での最高傑作である`qwen2.5-coder:14b`（コーディング特化モデル）で動作確認を行います。

```bash
# コンテナの起動
docker compose up -d

# モデルのダウンロード（Qwen 2.5 Coder 14Bを指定）
docker exec -it ollama ollama run qwen2.5-coder:14b
```

コマンド実行後、ブラウザで `http://localhost:3000` にアクセスしてください。
最初のサインアップ画面が出ますが、これはローカル保存されるだけなので、好きなメールアドレスとパスワードで登録してログインします。

### 期待される出力

```text
>>> Pythonで高速な素数判定プログラムを書いて
...
(数秒でコードが生成される)
```

ブラウザ上のOpen WebUIで右上に「qwen2.5-coder:14b」と表示され、チャットがスムーズに返ってくれば成功です。
RTX 3060以上のGPUを使っていれば、毎秒50トークン以上の爆速レスポンスが体感できるはずです。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。ローカルで動かす最大のメリットは「自分のプログラムに組み込めること」にあります。
PythonからOllama APIを呼び出し、特定のフォルダにあるファイルを全て要約する「実務自動化スクリプト」を作成しましょう。

```python
import os
import requests
import json

class QwenAgent:
    def __init__(self, model="qwen2.5-coder:14b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def ask(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False # スクリプト処理の場合は一括取得が楽
        }

        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            return f"Error: {str(e)}"

# 実用例: カレントディレクトリのtxtファイルを要約する
agent = QwenAgent()
files = [f for f in os.listdir('.') if f.endswith('.txt')]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        summary = agent.ask(f"以下の内容を3行で要約してください:\n\n{content}")
        print(f"--- {file_path} の要約 ---\n{summary}\n")
```

このコードでは、`stream: False`を設定しています。
チャットUIでは1文字ずつ出るのが心地よいですが、自動化処理では「結果を全て受け取ってから次の処理へ行く」ほうがバグを防げます。
Qwenシリーズは特に「命令への忠実度」が高いため、プロンプトの最後に`JSON形式で返せ`と指示し、結果を`json.loads()`でパースするワークフローも非常に安定します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Error: nvidia-container-cli: initialization error | GPUドライバとToolkitの不整合 | `nvidia-smi`が出るか確認し、Toolkitを再インストール |
| コンテナは起動するがWebUIがOllamaに接続できない | ネットワーク設定ミス | `OLLAMA_BASE_URL`が`http://ollama:11434`になっているか確認 |
| 推論が極端に遅い（1〜2 tokens/sec） | CPUで動作している | Docker DesktopのGPU設定、または`deploy`セクションの記述を確認 |

## 次のステップ

無事に環境が構築できたら、次に取り組むべきは「RAG（検索拡張生成）」の構築です。
Open WebUIには標準でドキュメントアップロード機能があり、PDFやテキストファイルを読み込ませて「この資料に基づいて回答して」と指示できます。
Qwen 2.5/3.7はコンテキストウィンドウ（一度に扱える情報量）が非常に広いため、数冊の技術書を一度に参照させても精度が落ちにくいのが特徴です。

また、より高度な活用として「ComfyUI」と連携させ、Qwenに画像生成のプロンプトを書かせるのも面白いでしょう。
私自身、ブログのアイキャッチ画像はすべてローカルのQwenが生成したプロンプトを元に作成しています。
一度この「自分専用のAIサーバー」を手に入れると、クラウドの制限やプライバシーを気にしていた頃にはもう戻れません。

## よくある質問

### Q1: Qwen 3.7が出たら、また設定をやり直す必要がありますか？

いいえ。Ollama側がモデルを登録した瞬間に、`ollama pull qwen3.7`を実行するだけで今の環境がそのままアップグレードされます。Dockerベースで作る最大のメリットは、このメンテナンスの楽さにあります。

### Q2: 16GBのVRAMで32Bモデルを動かす裏技はありますか？

あります。量子化ビット数を下げる（Q3_K_Lなど）か、一部の層をCPUにオフロードします。ただし、推論速度は確実に落ちます。実用性を取るなら、14BクラスをQ8（8ビット）で動かす方が賢い選択だと思います。

### Q3: 外出先からこのローカルAIを使うには？

Tailscaleを使うのが最も安全で簡単です。VPNを張れば、スマホのブラウザから自宅サーバーのOpen WebUIにアクセスし、自分専用の最強AIをポケットに入れて持ち歩くことができます。

---

## あわせて読みたい

- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)
- [Minimax 2.7 使い方：ローカル環境で高性能MoEモデルを動かす実践ガイド](/posts/2026-04-05-minimax-2-7-local-llm-guide-python/)
- [Qwen 3.5 0.8B 使い方 | 超軽量AIをCPUだけで爆速動作させる手順](/posts/2026-03-10-qwen-3-5-08b-local-python-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Qwen 3.7が出たら、また設定をやり直す必要がありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。Ollama側がモデルを登録した瞬間に、ollama pull qwen3.7を実行するだけで今の環境がそのままアップグレードされます。Dockerベースで作る最大のメリットは、このメンテナンスの楽さにあります。"
      }
    },
    {
      "@type": "Question",
      "name": "16GBのVRAMで32Bモデルを動かす裏技はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。量子化ビット数を下げる（Q3KLなど）か、一部の層をCPUにオフロードします。ただし、推論速度は確実に落ちます。実用性を取るなら、14BクラスをQ8（8ビット）で動かす方が賢い選択だと思います。"
      }
    },
    {
      "@type": "Question",
      "name": "外出先からこのローカルAIを使うには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Tailscaleを使うのが最も安全で簡単です。VPNを張れば、スマホのブラウザから自宅サーバーのOpen WebUIにアクセスし、自分専用の最強AIをポケットに入れて持ち歩くことができます。 ---"
      }
    }
  ]
}
</script>

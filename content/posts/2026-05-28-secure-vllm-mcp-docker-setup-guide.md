---
title: "vLLMとMCPサーバーの脆弱性対策！Dockerで安全なAI実行環境を構築する方法"
date: 2026-05-28T00:00:00+09:00
slug: "secure-vllm-mcp-docker-setup-guide"
cover:
  image: "/images/posts/2026-05-28-secure-vllm-mcp-docker-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "vLLM 使い方"
  - "MCPサーバー セキュリティ"
  - "Docker AI環境"
  - "ローカルLLM 脆弱性対策"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

vLLMやMCPサーバーを外部攻撃から守るために、Dockerコンテナ内でネットワークと権限を完全に隔離した「セキュアAI推論・実行環境」を構築します。

この記事では、単にツールをインストールするだけでなく、万が一脆弱性を突かれてもホストOSや個人データにアクセスさせないための多層防御設定を組み込んだ環境を完成させます。

- 実行環境: Docker + NVIDIA Container Toolkit
- 対象ツール: vLLM (推論サーバー), MCP (Model Context Protocol) サーバー
- 前提知識: Linuxの基本コマンド操作、Dockerの基礎知識

## 先に確認するスペック・料金

AIサーバーを安全に運用するには、それなりのリソースが必要です。私の検証機（RTX 4090 2枚挿し）では余裕ですが、最低限以下のスペックを確保してください。

1. **GPU**: NVIDIA製 12GB以上のVRAM（RTX 3060 12GB以上）。vLLMはVRAM消費が激しいため、8GBだとモデルのロードすら厳しいです。
2. **メモリ**: 32GB以上を推奨。Dockerコンテナを複数立てると、ホスト側のメモリも食いつぶします。
3. **OS**: Ubuntu 22.04 LTS または 24.04 LTS。Windows + WSL2でも動きますが、セキュリティ上のネットワーク制御（UFW等）が複雑になるため、本気で運用するならLinuxネイティブがベストです。
4. **料金**: ソフトウェアはすべてオープンソースなので無料ですが、電気代は覚悟してください。4090をフル稼働させると月数千円単位で変わります。

もしこれからパーツを揃えるなら、VRAM 16GBの「RTX 4060 Ti 16GB」がコスパと安全性のバランスが取れています。安く済ませようとしてVRAM 8GBのカードを買うと、後で必ず後悔します。

## なぜこの方法を選ぶのか

vLLMやMCPサーバーで発見されたような脆弱性は、多くの場合「リモートからのコード実行（RCE）」に繋がります。これは、攻撃者があなたのPC上で任意のコマンドを実行できる状態を意味します。

「自分のPCなんて誰も狙わない」と思うのは、SIerの現場を知らない素人の考えです。インターネットにポートを公開した瞬間、数分以内にスキャナーが飛んできます。

ローカル環境で直接バイナリを叩くのではなく、Dockerによる隔離を選ぶ理由は3つあります。

1. **ファイルシステムの隔離**: 万が一乗っ取られても、コンテナ内の偽のルートディレクトリしか見えません。
2. **権限の最小化**: `non-root` ユーザーで実行することで、コンテナ脱出（Container Escape）のリスクを最小限に抑えます。
3. **ネットワークの制御**: Docker Bridgeネットワークを使い、コンテナが勝手に外部へ通信（リバースシェル等）するのを遮断できます。

他サイトでは「pip install vllm」だけで解説が終わっていますが、実務でそんな危ないことはできません。

## Step 1: 環境を整える

まずは、ホストOS側を最新の状態にし、GPUをDockerから扱えるようにします。

```bash
# OSのパッケージを最新にする（脆弱性対策の基本）
sudo apt update && sudo apt upgrade -y

# NVIDIA Container Toolkitのインストール
# これを入れないとDocker内でGPUが認識されません
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit

# 設定を反映してDocker再起動
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

⚠️ **落とし穴:**
`nvidia-smi` がホスト側で動いているのに、Docker内でGPUを認識しないことがよくあります。これは `nvidia-ctk runtime configure` の後のDocker再起動を忘れているか、後述する `compose.yaml` の `deploy` 設定が漏れている場合がほとんどです。

## Step 2: 基本の設定

次に、安全なDocker環境を定義します。ここでは、root権限を使わずにvLLMを動かすための設定を盛り込みます。

作業ディレクトリを作成し、`Dockerfile` と `docker-compose.yaml` を用意します。

```dockerfile
# Dockerfile
# セキュリティパッチが当たった最新のベースイメージを使用
FROM vllm/vllm-openai:latest

# rootでの実行を避けるため、専用ユーザーを作成
RUN useradd -m aiuser
USER aiuser
WORKDIR /home/aiuser

# モデルキャッシュ用のディレクトリを作成
RUN mkdir -p /home/aiuser/.cache/huggingface
```

次に、このDockerfileを呼び出す `docker-compose.yaml` を書きます。

```yaml
services:
  vllm:
    build: .
    container_name: secure-vllm
    # GPUの割り当て。ここが「落とし穴」になりやすい
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports:
      - "127.0.0.1:8000:8000" # 重要：localhost以外からの接続を遮断
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    volumes:
      - ./models:/home/aiuser/.cache/huggingface
    command: >
      --model facebook/opt-125m
      --enforce-eager
      --max-model-len 4096
    restart: unless-stopped
    # ネットワーク隔離：必要最小限の通信のみ許可
    networks:
      - ai-internal

networks:
  ai-internal:
    driver: bridge
```

（解説：`ports` の項目で `127.0.0.1:8000:8000` と書いているのがミソです。単に `8000:8000` と書くと、あなたのPCのIPアドレスを知っている外部の人間が、誰でもあなたのGPUを使って推論できてしまいます。）

## Step 3: 動かしてみる

設定ができたら起動します。Hugging Faceのトークンが必要なモデルを使う場合は、`.env` ファイルを作成しておいてください。

```bash
# 起動。ビルドを含めて実行します
docker compose up -d
```

### 期待される出力

```text
[+] Running 2/2
 ⠿ Network ai-secure_ai-internal  Created
 ⠿ Container secure-vllm          Started
```

サーバーが立ち上がるまで、`docker compose logs -f` でログを確認します。VRAMにモデルがロードされ、`Uvicorn running on http://0.0.0.0:8000` と出れば成功です。

次に、別のターミナルから動作確認のAPIリクエストを投げます。

```python
import requests
import json

# ローカルホスト経由でリクエストを送る
url = "http://127.0.0.1:8000/v1/completions"
payload = {
    "model": "facebook/opt-125m",
    "prompt": "The future of AI security is",
    "max_tokens": 50
}

try:
    response = requests.post(url, json=payload)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
```

（結果の読み方：`choices` の中にテキストが生成されていれば、コンテナ内での推論が正しく行われ、ネットワーク越しに結果が返ってきている証拠です。）

## Step 4: 実用レベルにする（MCPサーバーの連携）

vLLMが動いたら、次は最近話題のMCP（Model Context Protocol）サーバーを安全に動かします。MCPは「ClaudeなどのAIがあなたのPCのツールを叩く」ための仕組みですが、これが一番危険です。

信頼できないMCPサーバーを直接実行するのは、知らない人に家の鍵を渡すのと同じです。これもDockerで隔離しましょう。

以下は、`fetch`（Webサイトの中身を取得する）というMCPサーバーを、専用のコンテナで動かす例です。

```yaml
# docker-compose.yaml に追記
  mcp-fetch:
    image: node:20-slim
    container_name: secure-mcp-fetch
    working_dir: /app
    command: >
      npx -y @modelcontextprotocol/server-fetch
    networks:
      - ai-internal
    # ファイルシステムを読み取り専用にする（書き換え防止）
    read_only: true
    # 一時ファイルのみ書き込み許可
    tmpfs:
      - /tmp
      - /root/.npm
```

このように、MCPサーバーごとにコンテナを分け、`read_only: true` を設定することで、AIが勝手にあなたの設定ファイルを書き換えたり、マルウェアを設置したりするリスクを構造的に排除します。

実務では、この `ai-internal` ネットワーク内に、APIゲートウェイ（Nginxなど）を1つだけ置き、そこで認証（APIキーのチェック）を行うのがセオリーです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `NVIDIA-SMI has failed...` | ホストのドライバと不整合 | `sudo apt install nvidia-driver-xxx` でドライバを再インストール |
| `Permission denied` (Volume) | ホスト側のフォルダ権限不足 | `chmod -R 777 ./models` （検証用）または実行ユーザーのUIDを合わせる |
| `Connection refused` | 127.0.0.1で縛りすぎ | コンテナ間通信ならサービス名（`vllm:8000`）でアクセスする |

## 次のステップ

お疲れ様でした。これで「脆弱性が発表されても、すぐには致命傷にならない」強固なAI実行環境が手に入りました。

次にやるべきことは、この環境に「監視」を入れることです。
例えば、`Prometheus` と `Grafana` を使って、GPUの温度やVRAM使用率、そして「異常な回数のAPIリクエスト（総当たり攻撃の兆候）」を可視化してみてください。

また、今回は `docker-compose` でしたが、複数のGPUサーバーを束ねるなら `Kubernetes` (K8s) への移行も視野に入ります。SIer出身の私から言わせれば、ローカルLLMを「おもちゃ」で終わらせるか「仕事の武器」にするかの差は、こうしたインフラの堅牢性に現れます。

自分の身は自分で守りつつ、最新のAI技術を全力で使い倒していきましょう。

## よくある質問

### Q1: Dockerを通すと推論速度は落ちませんか？

ほとんど落ちません。NVIDIA Container Toolkitを使えば、GPUへのアクセスはネイティブに近いパフォーマンスが出ます。オーバーヘッドは無視できるレベル（1%未満）です。

### Q2: MCPサーバーをCursorで使いたいのですが、Dockerだと不便では？

CursorなどのIDEから使う場合は、Dockerのポートをホストにマッピング（`127.0.0.1:3000:3000`等）すれば、IDE側からはローカルで動いているように見えます。隔離のメリットを維持したまま使えます。

### Q3: VRAMが足りないというエラー（OOM）が出ます。

`--max-model-len` の値を小さくするか、`--gpu-memory-utilization` を `0.8` などに下げてみてください。また、同時に動かしている他のアプリ（ブラウザ等）がVRAMを食っていないか確認しましょう。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでvLLMを安全・安価に試すための現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [AMD MI50でQwen 2.5 27Bを爆速化してローカルLLMサーバーを構築する方法](/posts/2026-05-14-amd-mi50-qwen-vllm-setup-guide/)
- [RTX 5090とvLLMでQwen3.6-27Bを爆速動作させる方法](/posts/2026-04-26-qwen3-6-27b-vllm-rtx5090-setup-guide/)
- [Qwen2.5 27Bを爆速化 vLLMでスループットを極限まで高めるやり方](/posts/2026-05-25-qwen-27b-vllm-high-throughput-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerを通すと推論速度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ほとんど落ちません。NVIDIA Container Toolkitを使えば、GPUへのアクセスはネイティブに近いパフォーマンスが出ます。オーバーヘッドは無視できるレベル（1%未満）です。"
      }
    },
    {
      "@type": "Question",
      "name": "MCPサーバーをCursorで使いたいのですが、Dockerだと不便では？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorなどのIDEから使う場合は、Dockerのポートをホストにマッピング（127.0.0.1:3000:3000等）すれば、IDE側からはローカルで動いているように見えます。隔離のメリットを維持したまま使えます。"
      }
    },
    {
      "@type": "Question",
      "name": "VRAMが足りないというエラー（OOM）が出ます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "--max-model-len の値を小さくするか、--gpu-memory-utilization を 0.8 などに下げてみてください。また、同時に動かしている他のアプリ（ブラウザ等）がVRAMを食っていないか確認しましょう。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでvLLMを安全・安価に試すための現実的な選択肢</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

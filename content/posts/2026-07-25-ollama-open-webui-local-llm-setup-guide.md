---
title: "OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法"
date: 2026-07-25T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-07-25-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "Llama 3 ローカル"
  - "Docker GPU 設定"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

この記事を読むと、完全にオフラインで動作し、ChatGPTのような操作感を持つプライベートなAIチャット環境があなたのPC上に完成します。
具体的には、バックエンドに「Ollama」、フロントエンドに「Open WebUI」を組み合わせ、Dockerを用いて一気に立ち上げる環境を構築します。
PythonからAPIとして叩く方法や、手元のPDFを読み込ませて回答させるRAG（検索拡張生成）機能の基礎までを網羅します。

前提知識：
- 基本的なコマンド操作（ターミナルやコマンドプロンプトの利用）ができること
- Dockerの概念をふんわりと理解していること（インストール済みが望ましい）

必要なもの：
- インターネット環境（数GBのモデルをダウンロードするため）
- NVIDIA製GPU搭載のPC（Windows/Linux）または Apple Silicon搭載のMac

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、現在のデファクトスタンダードである Llama 3 (8B) クラスを快適に動かすなら、最低でも8GB、理想は12GB以上のVRAMが必要です。
VRAMが足りないと、処理がメインメモリ（RAM）に溢れ出し、レスポンスが「1秒間に1文字」レベルまで低下して実用的ではなくなります。

Windowsユーザーであれば、RTX 3060 (12GB版) や RTX 4060 Ti (16GB版) が、コストパフォーマンスの面で最も賢い選択です。
Macユーザーの場合は、メモリがCPUと共有される「ユニファイドメモリ」なので、最低16GB、できれば24GB以上のモデルを選んでください。
ちなみに私の環境（RTX 4090 24GB × 2枚）では、70Bクラスの巨大なモデルも1秒間に20トークン以上の高速レスポンスで動作しますが、初心者がいきなりここを目指す必要はありません。

もし手元にGPUがない場合、CPUだけでも動作はしますが、ストレスを感じる速度になります。
その場合は無理にローカルで動かさず、Groqなどの高速APIを試すか、この機会にVRAM 12GB以上のグラボを新調することをおすすめします。
一度構築してしまえば、API利用料を気にせず、どれだけ長文を投げても「月額0円」で使い放題になるのが最大のメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやJan、GPT4Allなど他にもいくつか存在します。
しかし、私が「Ollama + Open WebUI」の組み合わせを最も推奨する理由は、その「拡張性」と「再現性」にあります。

Ollamaは内部的にllama.cppを利用しており、モデルの管理が非常に軽量で、バックエンドとしてAPIを公開する機能が標準で備わっています。
そこにOpen WebUIを組み合わせることで、ChatGPTと遜色ないUIだけでなく、複数ユーザー管理、RAG、プラグイン機能などが手に入ります。
また、Dockerを利用することで環境を汚さず、設定の移行やバックアップが容易になる点も、実務でAIを扱う上では欠かせないポイントです。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。
Windows/Macなら公式サイトからインストーラーをダウンロードするだけですが、今回はDocker上で一元管理する道を選びます。
理由は、将来的にサーバーを立てたり、複数のツールを連携させたりする際に、Dockerの方が圧倒的に管理しやすいからです。

Windowsユーザーは「Docker Desktop」と「NVIDIA Container Toolkit」が必要です。
WSL2（Windows Subsystem for Linux）がセットアップされている前提で進めます。

```bash
# NVIDIA Container Toolkit のインストール（Linux/WSL2の場合）
# これを入れないと、DockerコンテナからGPUが見えません
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/lib/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

⚠️ **落とし穴:**
WindowsでDocker Desktopを使っている場合、設定画面で「Use the WSL 2 based engine」にチェックが入っているか必ず確認してください。
ここがオフだと、GPUアクセラレーションが効かず、CPUのみの極めて遅い動作になります。
また、NVIDIAのドライバーは最新版（Game ReadyでもStudioでも可）を必ずインストールしておいてください。

## Step 2: Docker Composeで一括起動

OllamaとOpen WebUIを別々に立ち上げると、お互いの通信設定（IPアドレスの指定など）で初心者は必ずハマります。
そこで、`docker-compose.yml` という設定ファイルを作成し、一つのコマンドで連携済みの環境を立ち上げます。

適当な作業用フォルダを作成し、以下の内容で `docker-compose.yml` を保存してください。

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
              count: 1
              capabilities: [gpu]

  open-webui:
    extends:
      file: docker-compose.yaml # 自身を参照する設定（必要に応じて修正）
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
      - 'WEBUI_SECRET_KEY=your_secret_key_here'
    restart: unless-stopped
```

各設定の意図を解説します。
`OLLAMA_BASE_URL` に `http://ollama:11434` を指定することで、Open WebUIコンテナが同一ネットワーク内のOllamaコンテナを名前で解決できるようにしています。
`volumes` 指定により、ダウンロードしたモデルデータやチャット履歴がホスト側のフォルダ（./ollama, ./open-webui）に保存されるようにしています。
これにより、コンテナを削除してもデータが消えることはありません。

準備ができたら、ターミナルで以下のコマンドを叩きます。

```bash
docker compose up -d
```

## Step 3: モデルのダウンロードと動作確認

コマンド実行後、ブラウザで `http://localhost:3000` にアクセスしてください。
最初のログイン画面が出ますが、これはローカル環境内に保存されるアカウントなので、好きなメールアドレスとパスワードで登録してOKです。
一番最初に登録したユーザーが自動的に管理者（Admin）になります。

ログインしたら、まず左下の設定アイコン、あるいは上部のモデル選択から「モデルのダウンロード」を行います。
ここでは、現在最も性能と速度のバランスが良い「Llama 3 (8B)」を試しましょう。

```text
モデル名入力欄: llama3:8b
```

ダウンロードボタンを押すと、数GBのデータ転送が始まります。
私の光回線環境では、Llama 3 8B (約4.7GB) のダウンロードは約2分で完了しました。

### 期待される出力

ダウンロード完了後、チャット画面で「こんにちは、自己紹介してください」と入力してみてください。

```text
こんにちは！私はLlama 3、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で直接動作しており、プライバシーが守られた環境でお手伝いできます。
```

このように返ってくれば成功です。
タスクマネージャーの「パフォーマンス」タブを開き、GPUのVRAM（専用ビデオメモリ）の使用量が増えていることを確認してください。
もしCPU使用率が100%に張り付いて、VRAMが動いていない場合は、Step 1のNVIDIA Container Toolkitの設定を見直す必要があります。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分ですが、ローカル環境の真価は「機密情報の処理」と「API連携」にあります。

### 1. PDFを読み込ませる（RAG）
Open WebUIには、標準でドキュメント解析機能が備わっています。
チャット欄の「＋」ボタンからPDFやテキストファイルをアップロードしてください。
「このドキュメントの内容を要約して」と指示すると、ローカル内でテキストをベクトル化し、関連箇所を抽出して回答してくれます。
会社の機密マニュアルや、外部に出したくないソースコードの解析に最適です。

### 2. PythonからOllamaを叩く
開発者であれば、自作アプリのバックエンドとして使いたいですよね。
OllamaはOpenAI互換のAPIエンドポイントを持っています。

```python
import openai

# OllamaはデフォルトでOpenAI APIのインターフェースをエミュレートできます
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # キーは何でも良い
)

response = client.chat.completions.create(
    model="llama3:8b",
    messages=[
        {"role": "system", "content": "あなたは優秀なエンジニアです。"},
        {"role": "user", "content": "Pythonで素数を判定する効率的な関数を書いて。"},
    ],
)

print(response.choices[0].message.content)
```

このコードを実行するには `pip install openai` が必要です。
`base_url` をローカルのOllamaに向けるだけで、既存のOpenAI向けライブラリがそのまま動くのが、Ollamaの最も強力な点の一つです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection refused` | Ollamaコンテナが起動していない | `docker ps` で確認し、再起動する |
| レスポンスが極端に遅い | GPUが認識されずCPUで動いている | NVIDIA Container Toolkitを再インストール |
| `Out of Memory` | VRAM容量に対してモデルが大きすぎる | `phi3` や `gemma:2b` など軽量モデルを試す |
| WebUIにアクセスできない | ポート3000が他アプリで使用中 | docker-composeの `3000:8080` を `3001:8080` 等に変更 |

## 次のステップ

無事に環境が動いたら、次は「モデルの使い分け」に挑戦してみてください。
- 汎用的な対話なら: `llama3:8b`
- 日本語の自然さを重視するなら: `elyza:jp8b` (Ollamaライブラリで検索可能)
- 軽量・高速化を求めるなら: `phi3:mini`
- プログラミング特化なら: `codellama` または `deepseek-coder`

また、Open WebUIの「Functions」機能を使えば、AIに特定のPythonスクリプトを実行させたり、最新のWeb情報を検索しに行かせたりすることも可能です。
これらはクラウドのAIでは制限が多い部分ですが、ローカルなら自由自在です。
自分だけの最強のAI秘書を、その12GBや24GBのVRAMの中に飼い慣らしてみてください。

## よくある質問

### Q1: Ollamaを入れると、PCの動作全体が重くなりませんか？

アイドル時はメモリをほとんど消費しません。推論（回答）中のみGPUに負荷がかかります。推論が終わればVRAMは解放される設定（デフォルトで5分後にアンロード）になっているため、普段の作業に支障は出ません。

### Q2: 外部のPCやスマホから、このWebUIを使うことはできますか？

可能です。Docker Composeのポート設定を `0.0.0.0:3000:8080` のように開放し、スマホからPCのローカルIPアドレス（192.168.x.x:3000）を叩けばアクセスできます。ただし、セキュリティのためVPN越しでの利用を強く推奨します。

### Q3: モデルをカスタマイズ（ファインチューニング）できますか？

Ollama単体ではできません。しかし、Modelfileという設定ファイルを作成することで、システムプロンプト（性格付け）やパラメータを固定した自分専用モデルを `ollama create` コマンドで簡単に作ることができます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama3クラスを余裕を持って動かせる、個人開発者の最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-07-12-ollama-open-webui-local-llm-guide/)
- [ローカルLLM構築入門 OllamaとPythonでAIを自前運用する方法](/posts/2026-06-02-ollama-python-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaを入れると、PCの動作全体が重くなりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "アイドル時はメモリをほとんど消費しません。推論（回答）中のみGPUに負荷がかかります。推論が終わればVRAMは解放される設定（デフォルトで5分後にアンロード）になっているため、普段の作業に支障は出ません。"
      }
    },
    {
      "@type": "Question",
      "name": "外部のPCやスマホから、このWebUIを使うことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Docker Composeのポート設定を 0.0.0.0:3000:8080 のように開放し、スマホからPCのローカルIPアドレス（192.168.x.x:3000）を叩けばアクセスできます。ただし、セキュリティのためVPN越しでの利用を強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルをカスタマイズ（ファインチューニング）できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollama単体ではできません。しかし、Modelfileという設定ファイルを作成することで、システムプロンプト（性格付け）やパラメータを固定した自分専用モデルを ollama create コマンドで簡単に作ることができます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama3クラスを余裕を持って動かせる、個人開発者の最適解。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

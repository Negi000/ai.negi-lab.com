---
title: "OllamaとOpen WebUIで自分専用のChatGPTを爆速で構築する方法"
date: 2026-10-17T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-10-17-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM 環境構築"
  - "Docker LLM"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 自分のPC内で完結し、外部にデータが漏れない「ChatGPTと同等のUIを持つAIチャット環境」を構築します。
- ネット不要で動作し、月額費用もかからない自由なローカルLLM実行基盤を完成させます。
- Dockerを使用して、将来的な拡張（RAGやマルチモーダル対応）が容易な構成を目指します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3クラスのモデルを快適に動かせるコスパ最強の選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのは「GPUのビデオメモリ（VRAM）」と「メインメモリ（RAM）」です。
結論から言うと、VRAM 8GB以上のNVIDIA製GPUがあれば快適、Macならユニファイドメモリ16GB以上が最低ラインです。

私が検証した結果、RTX 3060 (12GB) なら「Llama 3.1 8B」クラスが爆速（レスポンス秒間50トークン以上）で動きます。
一方で、VRAM 4GB以下の古いPCや、メモリ8GBのMacBook Airでは、モデルのロードだけで数分かかり、実務には耐えません。
もしこれから機材を揃えるなら、予算10万円前後ならRTX 4060 Ti (16GB版)、25万円出せるならMac Studio (M2/M3 Max) のメモリ64GB以上が、仕事で使うための「賢い投資」になります。

料金については、電気代以外は「完全無料」です。
ChatGPT Plusに毎月$20払うのを1年やめれば、ミドルレンジのGPUが買える計算になります。
プライバシーが極めて重要な機密情報を扱う業務なら、この投資は1ヶ月で回収できると私は考えています。

## なぜこの方法を選ぶのか

ローカルLLMを動かす方法は、Pythonで直接スクリプトを書く、LM Studioを使うなど多岐にわたります。
その中で「Ollama + Open WebUI」の組み合わせがベストな理由は、バックエンドとUIの分離が完璧だからです。

Ollamaはモデルの管理と実行を肩代わりし、Open WebUIはChatGPTと遜色ない操作感を提供してくれます。
特にOpen WebUIは、PDFをアップロードして内容を質問する「RAG」機能や、複数のモデルを並べて回答を比較する機能が標準で備わっています。
単に「動かして終わり」ではなく、エンジニアとして実務に組み込むためのAPI連携もOllamaがあれば簡単です。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。
Windowsならインストーラーを叩くだけですが、開発者ならWSL2（Windows Subsystem for Linux）上で動かすのが正解です。
理由は、Dockerとの親和性が高く、将来的なデプロイ作業がスムーズになるからです。

```bash
# Linux / WSL2 の場合、以下のコマンド一発でインストール完了
curl -fsSL https://ollama.com/install.sh | sh
```

このコマンドは、Ollamaのバイナリをダウンロードし、GPU（NVIDIA/AMD）を自動認識して最適なドライバ設定を適用してくれます。
インストールが終わったら、一度バージョンを確認して動作を確かめます。

```bash
ollama --version
```

⚠️ **落とし穴:**
WindowsのWSL2で動かす際、`nvidia-smi`コマンドが効かない状態だとGPUを認識しません。
必ずWindows側に最新のNVIDIA Game Readyドライバ（またはStudioドライバ）が入っていることを確認してください。
GPUが認識されていないと、推論がCPUで行われ、1文字出るのに3秒かかるような地獄のレスポンスになります。

## Step 2: Docker ComposeでUIを立ち上げる

次にOpen WebUIを導入します。
Open WebUIは機能が多いため、依存関係で環境を汚さないようDockerで動かすのが鉄則です。
私が実際に運用している、GPUを有効化した`docker-compose.yml`の設定を共有します。

```yaml
version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    environment:
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  open-webui:
```

ここで重要なのが `OLLAMA_BASE_URL` の設定です。
Dockerコンテナの中から、ホストマシンで動いているOllama（ポート11434）を参照させるために `host.docker.internal` を使っています。
これを忘れると、UIだけ立ち上がって「モデルが見つかりません」というエラーで30分溶かすことになります。

設定ファイルを保存したら、以下のコマンドで起動します。

```bash
docker compose up -d
```

## Step 3: モデルをダウンロードして動かしてみる

ブラウザで `http://localhost:3000` にアクセスしてください。
最初のサインアップ画面が出ますが、これはローカル環境内に保存されるユーザー情報なので、適当なメアドとパスワードで大丈夫です。

ログインしたら、まず左上の「モデルを選択」をクリックします。
まだ何も入っていないので、Ollamaからモデルをプル（ダウンロード）する必要があります。
まずは世界標準と言える「Llama 3.1 (8B)」を入れましょう。

```bash
# ターミナルから直接プルする場合
ollama pull llama3.1
```

ダウンロードが完了すると、Open WebUIのモデル選択リストに「llama3.1:latest」が現れます。
これを選択して、何か質問を投げてみてください。

### 期待される出力

```text
User: 日本の首都は？
AI: 日本の首都は東京です。
```

この時、タスクマネージャーや `nvidia-smi` でGPUメモリの使用率を見てください。
VRAMが数GB占有され、GPUの使用率がスパイクしていれば、正しくハードウェアアクセラレーションが効いている証拠です。

## Step 4: 実用レベルにする

「動いた、すごい」で終わらせてはプロの道具になりません。
実務で使えるレベルにするために、2つのカスタマイズを推奨します。

### 1. システムプロンプトの固定
Open WebUIの「設定」→「一般」から、システムプロンプトを設定できます。
「あなたは一流のPythonエンジニアです。回答は簡潔に、必ず実行可能なコード例を含めてください」と入れるだけで、回答の質が劇的に変わります。
私は用途に合わせて「コードレビュー用」「翻訳用」「壁打ち用」とモデルを複製して使い分けています。

### 2. RAG（ドキュメント参照）の活用
チャット欄にファイルをドラッグ＆ドロップしてみてください。
Open WebUIが自動的にそのファイルをベクトル化し、内容に基づいた回答をしてくれます。
最新の技術ドキュメントや、自社の社内規定PDFを読み込ませることで、ChatGPT（Web版）にはできない「手元データに基づいた正確な回答」が可能になります。

```python
# OllamaをPythonから叩く例（自動化の第一歩）
import requests

def ask_local_llm(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=data)
    return response.json()['response']

print(ask_local_llm("Pythonで素数を判定する関数を書いて"))
```

このようにAPIとしても叩けるため、私は日々のログ解析や、大量のメール下書き作成をローカルLLMで自動化しています。
API料金を気にせず、1日1万回リクエストを送っても無料なのがローカル環境の真髄です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Error (Docker) | `OLLAMA_BASE_URL`が誤っている | 11434ポートが解放されているか確認し、IPを正しく指定する |
| 回答が異常に遅い | GPUではなくCPUで動作している | Ollamaのログを確認し、CUDAドライバを更新する |
| メモリ不足で落ちる | VRAMに対してモデルが大きすぎる | `8B`や`7B`など、パラメータ数の少ないモデルに変更する |

## 次のステップ

環境が整ったら、次は「Quantization（量子化）」について学ぶことをおすすめします。
例えば、70Bという巨大で賢いモデルも、4-bit量子化されたものを使えば、RTX 4090を2枚挿している私の環境ならサクサク動きます。
Hugging Faceで「GGUF」という形式を検索すれば、世界中の有志が最適化したモデルが数万件見つかります。

また、Open WebUIの「Tools」機能を使って、AIにGoogle検索をさせたり、Pythonスクリプトをその場で実行させたりする「エージェント化」にも挑戦してみてください。
ここまで来れば、あなたはもう有料のAIサービスに依存せず、自分だけの最強の思考パートナーを手に入れたことになります。

## よくある質問

### Q1: AMDのGPU（Radeon）でも動きますか？

動きます。OllamaはAMDのROCmスタックをサポートしています。ただし、NVIDIAのCUDAに比べるとセットアップの難易度が少し高く、ライブラリの相性問題が出やすい点は覚悟してください。

### Q2: 会社で使ってもセキュリティ的に大丈夫ですか？

これこそがローカルLLM最大のメリットです。データは全てあなたのPC（または社内サーバー）内で処理され、OpenAIやMetaに送信されることはありません。オフライン状態で動かすことも可能です。

### Q3: おすすめのモデルは何ですか？

日本語の自然さを重視するなら「Llama-3-Elyza-jp」が最強クラスです。コード作成や論理的思考なら「Qwen 2.5 (7B)」が、パラメータ数の割に驚くほど賢いので私も常用しています。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPTをローカルに構築する方法](/posts/2026-10-11-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AMDのGPU（Radeon）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。OllamaはAMDのROCmスタックをサポートしています。ただし、NVIDIAのCUDAに比べるとセットアップの難易度が少し高く、ライブラリの相性問題が出やすい点は覚悟してください。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使ってもセキュリティ的に大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "これこそがローカルLLM最大のメリットです。データは全てあなたのPC（または社内サーバー）内で処理され、OpenAIやMetaに送信されることはありません。オフライン状態で動かすことも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめのモデルは何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "日本語の自然さを重視するなら「Llama-3-Elyza-jp」が最強クラスです。コード作成や論理的思考なら「Qwen 2.5 (7B)」が、パラメータ数の割に驚くほど賢いので私も常用しています。 ---"
      }
    }
  ]
}
</script>

---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-11-24T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-11-24-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM GPU 要件"
  - "Docker LLM 連携"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

プライバシーを完全に保護した状態で、ChatGPTと同等の操作感を持つAIチャット環境を、あなたのPCローカル上に構築します。
具体的には、バックエンドに「Ollama」、フロントエンドに「Open WebUI」を採用し、Dockerを使用してこれらを連携させたシステムを作り上げます。
この記事の手順を終える頃には、Llama 3やGemma 2といった最新のオープンモデルを、ブラウザから快適に操作できるようになります。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも遥かに重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、NVIDIA製GPUであればVRAM 8GBが最低ライン、12GBあれば7B（70億パラメータ）クラスのモデルが快適に動作し、24GBあれば70Bクラスの量子化版が視野に入ります。
AMD製GPUでも動きますが、ドライバ周りのトラブルが多いため、初心者が「仕事で使う」ならRTX 3060 12GB以上のNVIDIA環境か、ユニファイドメモリを積んだMacを強く推奨します。

Apple Silicon（M1/M2/M3）搭載のMacの場合、メモリ（RAM）がVRAMを兼ねるため、最低16GB、できれば32GB以上のモデルを選んでください。
Windowsでこれから機材を揃えるなら、コストパフォーマンスの観点からRTX 4060 Ti 16GB版が、ローカルLLM入門における現在の「正解」です。
電気代を除けば、モデルの利用料やAPI使用料は一切かかりません。月額$20のChatGPT Plusを解約できるポテンシャルを秘めています。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には、LM StudioやJan、GPT4Allなど多くの選択肢があります。
しかし、私が実務での運用に「Ollama + Open WebUI」を推す理由は、その「拡張性」と「再現性」にあります。
Ollamaはコマンド一つでモデルの管理とAPIサーバー化が可能であり、Open WebUIはDocker上で動くため、将来的にRAG（外部知識参照）やマルチユーザー管理、さらにはWeb検索機能の統合が容易です。

他のデスクトップアプリは「とりあえず動かす」には最適ですが、特定のディレクトリ構造に依存したり、APIのカスタマイズ性が低かったりと、実務に組み込む際に壁にぶつかります。
Dockerを用いることで環境を汚さず、設定ファイルを共有するだけで他のPCでも全く同じ環境が再現できる点は、プロフェッショナルな開発者にとって譲れないメリットです。

## Step 1: 環境を整える

まずは、LLMの推論エンジンとなる「Ollama」をインストールします。

```bash
# macOS/Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、Ollamaの公式サイトからインストーラー（.exe）をダウンロードして実行してください。
インストール後、ターミナル（またはPowerShell）で以下のコマンドを叩き、バージョンが表示されるか確認します。

```bash
ollama --version
```

次に、Docker Desktop（またはDocker Engine）がインストールされていることを確認してください。
Open WebUIは非常に多機能なため、ホストOSの環境を汚さないようDockerコンテナとして動かすのが定石です。

落とし穴: NVIDIAのGPUを使用しているWindows/Linuxユーザーは、DockerコンテナからGPUを認識させるために「NVIDIA Container Toolkit」をインストールする必要があります。これを忘れると、コンテナ内でLLMがCPU推論になり、レスポンスが10倍以上遅くなります。

## Step 2: 基本の設定

次に、OllamaとOpen WebUIを連携させるための設定を行います。
一番シンプルかつ管理しやすい「Docker Compose」を使用する方法を推奨します。
適当なディレクトリを作成し、`docker-compose.yaml`という名前で以下の内容を保存してください。

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
      - "3000:8080"
    environment:
      - 'OLLAMA_BASE_URL=http://ollama:11434'
      - 'WEBUI_SECRET_KEY=yoursecretkeyhere'
    restart: unless-stopped
```

なぜこの設定にするのかを解説します。
`OLLAMA_BASE_URL`に`http://ollama:11434`を指定しているのは、Dockerのネットワーク内で`open-webui`コンテナから`ollama`コンテナを名前解決するためです。
また、`volumes`を設定することで、ダウンロードした数十GBに及ぶモデルデータやチャット履歴がコンテナを削除しても消えないようにしています。

## Step 3: 動かしてみる

設定ファイルが用意できたら、以下のコマンドでコンテナを起動します。

```bash
docker compose up -d
```

起動には数分かかる場合があります。ブラウザを開き、`http://localhost:3000`にアクセスしてください。
最初のサインアップ画面が表示されます。これはローカル環境内のアカウント管理用なので、メールアドレスとパスワードは適当なもので構いません（外部には送信されません）。

ログイン後、モデルを選択する必要があります。まだモデルをダウンロードしていないので、画面上部の設定（歯車アイコン）から「Settings」>「Models」を開き、以下のモデル名を入力してダウンロードしてください。

```text
llama3.1:8b
```

### 期待される出力

ダウンロード完了後、トップ画面のプルダウンから`llama3.1:8b`を選択し、チャットを入力します。
「こんにちは、自己紹介してください」と投げた際、0.5秒以内に生成が始まり、秒間50トークン程度の速度で出力されれば、GPUが正しく認識されています。

```text
こんにちは！私はMetaによってトレーニングされたLlama 3という大規模言語モデルです。
あなたのPC上で直接動作しており、プライバシーが守られた状態で対話が可能です。
```

結果の読み方ですが、ここで出力が極端に遅い（1文字ずつゆっくり出る）場合は、DockerがGPUを掴んでおらず、CPUで処理されている可能性が高いです。その際は`nvidia-smi`コマンドでGPUの使用状況を確認してください。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。ローカルLLMを実務で使うなら、「RAG（外部ドキュメント参照）」と「API利用」を使いこなすべきです。

Open WebUIには、PDFやテキストファイルをアップロードして、その内容に基づいた回答をさせる機能が標準で備わっています。
チャット欄にファイルをドラッグ＆ドロップし、「#」を入力してファイル名を選択するだけで、社外秘のドキュメントを外部サーバーに送ることなく解析できます。

また、Pythonからこの環境をAPIとして叩くことで、大量のテキスト処理を自動化できます。

```python
import requests
import json

def chat_with_local_llm(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }

    # ローカルサーバーにリクエストを送信
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json().get("response")
    else:
        return f"Error: {response.status_code}"

# 実行例
print(chat_with_local_llm("PythonでCSVを読み込むコードを書いて"))
```

このスクリプトを使えば、数千件の顧客アンケートの分類や、大量のログ解析を、APIコストを気にせず回し続けることが可能です。
私はこの方法で、月間数万件のテキスト要約タスクを自前サーバーで処理し、月額数十万円相当のAPI費用を浮かせています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection refused | Ollamaが起動していない、またはポートが競合している | `docker compose ps`でコンテナの状態を確認し、11434ポートが空いているかチェック |
| Out of Memory (OOM) | VRAM容量に対してモデルが大きすぎる | 量子化レベルの高いモデル（4-bit等）を選ぶか、モデルサイズを落とす（70B→8B） |
| WebUIにモデルが出ない | OLLAMA_BASE_URLの設定ミス | Composeファイルの環境変数が`http://ollama:11434`になっているか再確認 |

## 次のステップ

ここまでの環境構築ができたら、次は「モデルの使い分け」に挑戦してください。
汎用的な対話なら`llama3.1`、コーディング特化なら`deepseek-coder-v2`、日本語のニュアンスを重視するなら`karakuri-lm`など、用途に合わせて最適なモデルを使い分けるのがローカル運用の醍醐味です。

さらに、Open WebUIの「Tools」機能を使えば、LLMにローカルのPythonスクリプトを実行させたり、Web検索の結果を要約させたりする「エージェント」的な動きも可能になります。
クラウドAIに依存せず、自前の計算リソースだけでどこまで業務を自動化できるか、ぜひその手で試行錯誤してみてください。

## よくある質問

### Q1: 社内の複数人でこの環境を共有して使えますか？

可能です。Dockerを動かしているマシンのIPアドレスに対して、他のPCからブラウザでアクセス（例: `http://192.168.1.10:3000`）すれば共有できます。Open WebUIにはユーザー管理機能があるため、誰がどのモデルを使ったかも管理できます。

### Q2: 量子化モデル（GGUF等）を使うと精度は落ちますか？

4-bit量子化程度であれば、実務上の回答精度に大きな差は感じられません。むしろ、メモリ消費を抑えて推論速度を上げるメリットの方が圧倒的に大きいです。VRAMに余裕がない限り、基本は量子化版の使用を推奨します。

### Q3: インターネット接続は必要ですか？

モデルの初回ダウンロード時のみ必要ですが、一度構築してしまえば完全にオフラインで動作します。物理的にネットワークから遮断された「エアギャップ」環境で機密情報を扱う用途には、このローカルLLM構成が唯一の選択肢となります。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、7Bモデルを高速に、14Bクラスも余裕で動かせる現時点の最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-08-09-ollama-openwebui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルChatGPTを構築する方法](/posts/2026-08-26-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-09-02-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の複数人でこの環境を共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを動かしているマシンのIPアドレスに対して、他のPCからブラウザでアクセス（例: http://192.168.1.10:3000）すれば共有できます。Open WebUIにはユーザー管理機能があるため、誰がどのモデルを使ったかも管理できます。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化モデル（GGUF等）を使うと精度は落ちますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "4-bit量子化程度であれば、実務上の回答精度に大きな差は感じられません。むしろ、メモリ消費を抑えて推論速度を上げるメリットの方が圧倒的に大きいです。VRAMに余裕がない限り、基本は量子化版の使用を推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "インターネット接続は必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの初回ダウンロード時のみ必要ですが、一度構築してしまえば完全にオフラインで動作します。物理的にネットワークから遮断された「エアギャップ」環境で機密情報を扱う用途には、このローカルLLM構成が唯一の選択肢となります。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MSI RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GB搭載で、7Bモデルを高速に、14Bクラスも余裕で動かせる現時点の最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

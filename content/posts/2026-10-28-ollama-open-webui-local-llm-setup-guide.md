---
title: "OllamaとOpen WebUIで自分専用のローカルChatGPTを構築する方法"
date: 2026-10-28T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM RAG"
  - "Llama 3.1 日本語"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

自分のPC内に、一切の外部通信を行わない「自分専用のChatGPT」を構築します。
具体的には、バックエンドにOllama、フロントエンドにOpen WebUIを使い、Dockerを用いて環境を汚さずにプロフェッショナルなチャットUIを立ち上げます。
Pythonなどのコードを書かずに、ドラッグ＆ドキュメント（RAG）や最新のLlama 3.1、Gemma 2といったモデルをGUIで自由に入れ替えて使える環境が手に入ります。

### 前提知識
- ターミナル（コマンドプロンプトやPowerShell）でコピペができること。
- Dockerの基本的な概念（「コンテナ」という使い捨ての環境があること）を知っていること。

### 必要なもの
- Windows 11 (WSL2導入済み) または macOS (Apple Silicon推奨)。
- Docker Desktop。
- NVIDIA製GPU（Windowsの場合。VRAM 8GB以上推奨）または Apple M1/M2/M3チップ。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも圧倒的に重要なのが「GPUのビデオメモリ（VRAM）」です。
結論から言うと、VRAMが8GBあれば「Llama 3.1 8B」などの軽量モデルが爆速（0.1秒〜0.3秒で生成開始）で動きます。
逆にVRAMが4GB以下だと、メインメモリ（RAM）へのスワップが発生し、1文字出すのに1秒以上かかる苦行になります。

Windowsユーザーでこれからハードを揃えるなら、RTX 4060 Tiの16GB版が最もコスパが良い選択肢です。
私はRTX 4090を2枚挿していますが、これは70B（700億パラメータ）クラスの巨大モデルを高速に回すための特殊な構成です。
一般的な業務補助やコーディング支援であれば、ミドルクラスのGPU1枚で十分実用レベルに達します。

Macユーザーの場合、メモリ（ユニファイドメモリ）がそのままVRAMとして機能するため、16GB以上のメモリを積んだモデルなら快適です。
8GBモデルのMacBook Airでも動きますが、OSやブラウザがメモリを食うため、大きなモデルを動かすとシステム全体が重くなる点に注意してください。
API料金は一切かかりません。電気代とPC購入代以外、完全に無料です。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには「LM Studio」や「GPT4All」など、より簡単にインストールできるものも存在します。
しかし、あえてOllamaとOpen WebUIを組み合わせる理由は、拡張性と実用性が段違いだからです。

Open WebUIは、本家ChatGPTに酷似した操作感に加え、RAG（ドキュメント読み込み）機能やウェブ検索連携が標準で備わっています。
また、Ollamaはバックエンドとして軽量で、複数のフロントエンドから同時にアクセスできるため、開発用サーバーとしても転用可能です。
「とりあえず動かす」ではなく「実務でChatGPTの代わりに使う」なら、現時点でこの構成がベストな解です。

## Step 1: Ollamaをインストールする

まずはLLMを制御するエンジンである「Ollama」をインストールします。

```bash
# Linuxの場合（WSL2上でも実行可能）
curl -fsSL https://ollama.com/install.sh | sh
```

WindowsやMacの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストール後、ターミナルで以下のコマンドを叩き、バージョンが表示されれば成功です。

```bash
ollama --version
```

次に、実際に使うモデルをダウンロードします。今回はMetaが開発した最高峰の軽量モデル「Llama 3.1 8B」を入れます。

```bash
ollama run llama3.1
```

ダウンロードが完了すると、そのままターミナル上で対話が始まります。
確認できたら `Ctrl + D` で終了してください。バックグラウンドでOllamaのサーバー機能は動き続けています。

⚠️ **落とし穴:**
Windowsの場合、Ollamaをインストールしただけでは「GPU」を認識しないことがあります。
タスクマネージャーの「パフォーマンス」タブで、モデル動作中にGPUの「専用ビデオメモリ」が消費されているか確認してください。
もしCPU使用率が100%になり、GPUが0%なら、NVIDIAのドライバが古いか、WSL2の設定が不完全な可能性があります。

## Step 2: DockerでOpen WebUIを構築する

次に、ブラウザで操作するためのUIを立ち上げます。
Open WebUIは依存関係が多いため、Dockerを使うのが最も安全で、環境を汚さない方法です。

以下の `docker-compose.yml` を作成してください。
なぜこれを作るかというと、コマンド一行で起動・停止を管理でき、ポート番号やデータの保存場所を明示的に固定できるからです。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'

volumes:
  open-webui:
```

### 設定の重要ポイント
- `ports: "3000:8080"`: ブラウザで `localhost:3000` にアクセスするための設定です。
- `OLLAMA_BASE_URL`: コンテナの中から、あなたのPC本体（Host）で動いているOllamaを見つけるための魔法の言葉です。これがないとUIだけ立ち上がってモデルが読み込めません。

ファイルを保存したディレクトリで、以下のコマンドを実行します。

```bash
docker compose up -d
```

画像（数GBあります）のダウンロードが始まるので、コーヒーを飲んで待ちましょう。

## Step 3: 初回ログインと動作確認

コンテナが起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
ログイン画面が表示されます。

「ローカルなのにメールアドレスが必要なの？」と思うかもしれませんが、これは複数のユーザーで使う場合の管理機能です。
データはすべてあなたのPC内に保存されるので、適当なメールアドレスとパスワードでアカウントを作成してください。
最初に作成したユーザーが管理者権限を持ちます。

ログイン後、画面上部の「モデルを選択」をクリックし、先ほどダウンロードした `llama3.1:latest` を選びます。

### 期待される出力

チャット欄に「こんにちは、自己紹介してください」と入力します。

```text
こんにちは！私はLlama 3.1、Metaによってトレーニングされた大規模言語モデルです。
あなたのPC上で直接動作しており、プライバシーを保ちながらお手伝いできます。
```

このように返ってくれば成功です。
レスポンス速度に注目してください。RTX 3060以上の環境なら、文字が流れるように出力されるはずです。

## Step 4: 実用レベルにする（RAG機能の活用）

Open WebUIの真骨頂は「ドキュメント連携」です。
左下のプラスアイコン、または「ドキュメント」メニューから、手持ちのPDFやテキストファイルをアップロードしてください。

例えば、会社の就業規則や、現在開発中のプロジェクトの仕様書（PDF）をアップロードします。
その後、チャット欄で `#` を入力すると、アップロードしたファイル名が出てきます。

```text
#仕様書.pdf この機能の仕様について、3行で要約して。
```

このように入力すると、LLMがファイルを読み込み、その内容に基づいた回答を生成します。
OpenAIにデータを送りたくない機密性の高い文書を扱う際に、このローカルRAG環境は最強の武器になります。

なぜこれが重要かというと、通常LLMは2023年頃までの知識しか持っていませんが、RAGを使うことで「今、目の前にあるデータ」を理解させることができるからです。
しかも、すべてローカルで完結するため、情報漏洩のリスクはゼロです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | UIがOllamaを見失っている | `docker-compose.yml` の `OLLAMA_BASE_URL` が正しいか確認 |
| 生成速度が異常に遅い | CPUで動作している | NVIDIA Container Toolkitをインストールし、DockerからGPUが見えるようにする |
| モデルが出てこない | Ollama側でpullしていない | ターミナルで `ollama pull llama3.1` を実行する |

## 次のステップ

この環境ができたら、次は「自分専用のエージェント」を作ってみるのが面白いです。
Open WebUIには「モデルファイル（Modelfile）」という機能があり、システムプロンプトを固定したカスタムモデルを作成できます。
「あなたは優秀なPythonエンジニアです。コード以外の説明は不要です」といった指示を固定しておけば、いつものチャットがより実用的なツールに変わります。

また、API経由でこのOllamaを呼び出すことも可能です。
Pythonで `requests` ライブラリを使い、 `http://localhost:11434/api/generate` にリクエストを送れば、自作のプログラムにローカルLLMを組み込めます。
私はこれを利用して、自宅サーバー内の大量のログファイルを深夜に自動で要約させるスクリプトを走らせています。

## よくある質問

### Q1: Macのメモリ8GBモデルでも動きますか？

動きますが、Llama 3.1 8B（約5GB）をロードすると、ブラウザや他のアプリがかなり重くなります。4ビット量子化版（デフォルト）ならギリギリ実用的ですが、ブラウザのタブは閉じておくことをお勧めします。

### Q2: 外部のPCからこのUIにアクセスできますか？

可能です。Dockerの `ports` 設定で `0.0.0.0:3000:8080` とし、ファイアウォールを開ければ、同じWi-Fi内のスマホなどからアクセスできます。自分だけのプライベートAIサーバーが簡単に作れますね。

### Q3: おすすめのモデルはありますか？

日本語の自然さを重視するなら、Alibabaの「Qwen2.5 7B」や、Googleの「Gemma 2 9B」が非常に優秀です。Ollamaなら `ollama run qwen2.5` と打つだけで、数分後には新しいモデルに切り替えられます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1などの8B〜14Bモデルを快適に動かせる最高コスパのGPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-06-28-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を作る方法](/posts/2026-09-24-ollama-open-webui-local-llm-setup-guide/)

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
        "text": "動きますが、Llama 3.1 8B（約5GB）をロードすると、ブラウザや他のアプリがかなり重くなります。4ビット量子化版（デフォルト）ならギリギリ実用的ですが、ブラウザのタブは閉じておくことをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "外部のPCからこのUIにアクセスできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerの ports 設定で 0.0.0.0:3000:8080 とし、ファイアウォールを開ければ、同じWi-Fi内のスマホなどからアクセスできます。自分だけのプライベートAIサーバーが簡単に作れますね。"
      }
    },
    {
      "@type": "Question",
      "name": "おすすめのモデルはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "日本語の自然さを重視するなら、Alibabaの「Qwen2.5 7B」や、Googleの「Gemma 2 9B」が非常に優秀です。Ollamaなら ollama run qwen2.5 と打つだけで、数分後には新しいモデルに切り替えられます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3.1などの8B〜14Bモデルを快適に動かせる最高コスパのGPU</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

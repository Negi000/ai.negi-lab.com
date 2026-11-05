---
title: "OllamaとOpen WebUIでプライベートなChatGPT環境を構築する方法"
date: 2026-11-05T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-11-05-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 環境構築"
  - "RAG 自作"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- インターネット接続不要で、機密情報を一切外部に送信しない「自分専用のChatGPT」環境
- 複数のLLM（Llama 3.1, Gemma 2, Phi-3等）をボタン一つで切り替えて、PDFやURLの内容を読み込ませるRAG環境
- Dockerを使用してPC環境を汚さず、コマンド一つで起動・停止ができる運用フロー

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのが「VRAM（ビデオメモリ）」の容量です。
結論から言うと、NVIDIAのGPUならVRAM 12GB以上、Macならメモリ（ユニファイドメモリ）16GB以上が最低ラインです。
VRAM 8GBでも動きますが、モデルの量子化（圧縮）を強める必要があり、回答の質が目に見えて落ちます。

WindowsユーザーならRTX 3060 (12GB版) や RTX 4070 Ti Super (16GB) あたりがコスパの良い選択肢です。
私はRTX 4090 (24GB) を2枚挿していますが、Llama 3の70Bモデルを高速で動かすならこれくらいの投資は覚悟すべきですね。
Macの場合はM1/M2/M3チップの「メモリ容量」がVRAMとして機能するため、32GB以上のモデルを選ぶと中規模モデルが快適に動きます。

ソフトウェアはすべて無料のオープンソースを使用するため、電気代を除けば運用コストは0円です。
API料金を気にせず、1日に何万トークン投げても請求書は届きません。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は「LM Studio」や「GPT4All」など他にもありますが、私は「Ollama + Open WebUI」の組み合わせが最強だと確信しています。
理由は、Ollamaがバックエンドとして軽量かつモデル管理が非常に楽であること。
そしてOpen WebUIが、本家ChatGPTに匹敵する、あるいは超えるほどの多機能（RAG、Web検索、マルチユーザー対応）を備えているからです。

多くの人が「動かしてみた」で終わる中、実務で使うならドキュメントのアップロードやプロンプト管理ができるUIが欠かせません。
この構成なら、将来的に自作のPythonスクリプトからAPI経由でモデルを叩くことも容易です。

## Step 1: 環境を整える

まずは土台となるOllamaと、コンテナ環境のDockerを準備します。

```bash
# Windows/Macの場合: 公式サイトからインストーラーをダウンロード
# https://ollama.com/download

# Linuxの場合: 以下のコマンドで一発インストール
curl -fsSL https://ollama.com/install.sh | sh
```

Ollamaをインストールしたら、バックグラウンドで常駐していることを確認してください。
次に、NVIDIA GPUを使用するWindows/Linuxユーザーは「NVIDIA Container Toolkit」をインストールする必要があります。
これがないと、Dockerコンテナの中からGPUを見つけることができず、CPUだけで計算することになり、レスポンスが100倍遅くなります。

⚠️ **落とし穴:**
Windowsユーザーは、Docker Desktopの設定で「WSL 2 based engine」が有効になっていることを必ず確認してください。
また、BIOS設定で「Virtualization Technology (VT-x / AMD-V)」が有効になっていないと、Docker自体が起動しません。
PC起動時にF2やDelキーを連打して設定画面に入る必要がありますが、意外とここで詰まる初心者が多いです。

## Step 2: 基本の設定

次に、OllamaとOpen WebUIを連携させるための `docker-compose.yml` を作成します。
手動でコマンドを打つのは面倒ですし、設定を忘れるので、必ずファイルで管理すべきです。

適当な作業用フォルダを作成し、以下の内容で保存してください。

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - ./ollama:/root/.ollama
    ports:
      - "11434:11434"
    # NVIDIA GPUを使う場合のみ以下を有効化
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  open-webui:
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
      - 'WEBUI_SECRET_KEY=your_secret_key_here' # 適当な文字列に変更
    restart: always
```

この設定のポイントは `volumes` です。
ローカルのフォルダ（`./ollama` や `./open-webui`）をコンテナ内にマウントすることで、ダウンロードした巨大なモデルデータや、チャット履歴がコンテナを消しても消えないようにしています。
これをしていないと、Dockerを更新するたびに数GBのモデルを再ダウンロードする羽目になります。

## Step 3: 動かしてみる

設定ファイルができたら、ターミナル（PowerShellやTerminal.app）でそのフォルダに移動し、魔法の呪文を唱えます。

```bash
docker-compose up -d
```

このコマンドは「裏側（デタッチモード）でコンテナを起動せよ」という意味です。
初回はイメージのダウンロードに数分かかります。
起動が完了したら、ブラウザで `http://localhost:3000` を開いてください。

### 期待される出力

綺麗なログイン画面が表示されたら成功です。
最初のユーザー登録はローカルに保存されるだけなので、好きなメールアドレスとパスワードで作成してください。

次に、モデルをダウンロードします。
画面上部の設定（あるいはモデル選択）から、使いたいモデル名を指定します。
まずは `llama3.1:8b` あたりがバランスが良くておすすめです。

```text
llama3.1:8b
```

ダウンロードが完了すると、ついにチャットが始められます。
試しに「ローカルLLMを動かすメリットを教えて」と聞いてみてください。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。
ローカル環境の真髄は「自分のファイルを読み込ませる」ことにあります。

Open WebUIの画面左下にある「Documents」タブ、あるいはチャット欄にファイルをドラッグ＆ドロップしてください。
これにより、ローカルでRAG（検索拡張生成）が動きます。
例えば、社内の仕様書PDFや、自分が書いたコードのログをアップロードして、それに基づいた回答をさせることができます。

これをPythonから制御したい場合は、以下のようなスクリプトでOllamaのAPIを叩くことができます。

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

    # タイムアウトを長めに設定（初回起動時はモデルロードに時間がかかるため）
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実用例: 大量のテキストファイルを要約するバッチ処理
texts = ["文章1...", "文章2..."]
for i, text in enumerate(texts):
    print(f"Processing {i}...")
    result = chat_with_local_llm(f"以下の文章を3行で要約して:\n{text}")
    print(result)
```

このスクリプトを使えば、数千個のファイルを一括で処理しても「API破産」することはありません。
これこそが実務でローカルLLMを運用する最大のメリットです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Error: nvidia-container-cli: not found` | NVIDIA Toolkit未インストール | 公式ドキュメントに従ってToolkitを導入し、Dockerを再起動する。 |
| `localhost:3000` が開かない | ポート 3000 が既に使用されている | `docker-compose.yml` の `3000:8080` を `3001:8080` などに変更する。 |
| 回答が極端に遅い（1文字/秒以下） | GPUが認識されずCPUで動作している | Ollamaのログを確認。GPUレイヤーが0になっていないかチェック。 |
| モデルのダウンロードが止まる | ディスク容量不足 | ローカルLLMは1モデル4GB〜40GB消費する。空き容量を確保する。 |

## 次のステップ

無事に動くようになったら、次は「モデルの選定」にこだわってみてください。
日本語に特化したモデルを使いたいなら `elyza:jp8b`、コーディングを爆速にしたいなら `deepseek-coder-v2` など、用途に合わせて使い分けるのがプロのやり方です。

また、Open WebUIには「Functions」という機能があり、PythonコードをUI上で実行させたり、外部の検索エンジン（SearXNGなど）と連携して最新情報を取得させたりすることも可能です。
これらを組み合わせれば、特定業務に特化した「AIエージェント」を自前で構築できます。

最後に一つ。ローカルLLMの世界は進化が異常に速いです。
1ヶ月前の「最強」が今日は「並」になります。
常に新しいGGUF形式のモデルがアップロードされる「Hugging Face」をチェックする習慣をつけることをおすすめします。

## よくある質問

### Q1: グラボがないノートPCでも動きますか？

動きますが、快適とは言えません。CPUのみの場合、4-bit量子化された3B（30億パラメーター）クラスの軽量モデルなら実用的な速度で動く可能性があります。ただし、MacBookならM1以降であれば非常に快適です。

### Q2: 家族やチームで共有して使えますか？

はい、Open WebUIにはユーザー管理機能があります。サーバーとなるPCのIPアドレスを共有すれば、同じLAN内の他のPCやスマホのブラウザからアクセスして、1つのGPUリソースを共同利用することができます。

### Q3: データの機密性は本当に守られますか？

本記事の手順で構築し、外部API設定（OpenAI等）を入れない限り、データはあなたのPC内のDockerコンテナから一歩も外に出ません。完全にオフラインの環境でも、一度モデルさえダウンロードしてしまえば動作します。

---

## あわせて読みたい

- [OllamaとOpen WebUIを組み合わせて、データの外部流出を完全に防ぎながらChatGPTと同等の操作感を持つローカルLLM環境を構築します。](/posts/2026-08-02-ollama-openwebui-local-llm-tutorial/)
- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法](/posts/2026-08-10-ollama-open-webui-local-llm-tutorial/)

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
        "text": "動きますが、快適とは言えません。CPUのみの場合、4-bit量子化された3B（30億パラメーター）クラスの軽量モデルなら実用的な速度で動く可能性があります。ただし、MacBookならM1以降であれば非常に快適です。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームで共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Open WebUIにはユーザー管理機能があります。サーバーとなるPCのIPアドレスを共有すれば、同じLAN内の他のPCやスマホのブラウザからアクセスして、1つのGPUリソースを共同利用することができます。"
      }
    },
    {
      "@type": "Question",
      "name": "データの機密性は本当に守られますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "本記事の手順で構築し、外部API設定（OpenAI等）を入れない限り、データはあなたのPC内のDockerコンテナから一歩も外に出ません。完全にオフラインの環境でも、一度モデルさえダウンロードしてしまえば動作します。 ---"
      }
    }
  ]
}
</script>

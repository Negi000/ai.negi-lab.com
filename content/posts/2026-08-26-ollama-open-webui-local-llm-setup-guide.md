---
title: "OllamaとOpen WebUIで自分専用のローカルChatGPTを構築する方法"
date: 2026-08-26T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-08-26-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM 入門"
  - "Docker LLM 連携"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、自分のPC内で完結する「ChatGPTと同等の操作感を持つAIチャット環境」を構築します。
- 前提知識: 基本的なコマンド操作（PowerShellやTerminal）ができること。Dockerという単語を聞いたことがある程度でOK。
- 必要なもの: Windows、Mac、またはLinuxを搭載したPC。インターネット環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでこの価格は唯一無二。ローカルLLMを快適に動かすための最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、もっとも重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、NVIDIA製GPUならVRAM 8GB以上、Macならメモリ（ユニファイドメモリ）16GB以上が実用ラインになります。

VRAM 8GBあれば、現在主流の「Llama 3.1 8B」や「Gemma 2 9B」といった軽量かつ高性能なモデルが快適に動きます。
逆に、VRAM 4GB以下の古いPCや、内蔵グラフィックスのみの安価なWindowsノートPCでは、回答生成が1秒間に1文字程度になり、実務には耐えません。
その場合は、おとなしくChatGPT Plusに月額3,000円払う方がタイパ（タイムパフォーマンス）は圧倒的に高いです。

ストレージは、モデル1つにつき5GB〜10GB程度を消費します。
複数のモデルを試すなら、50GB程度の空き容量を確保しておいてください。
料金は、PCの電気代以外は完全に無料です。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールは、他にも「LM Studio」や「GPT4All」などがあります。
これらはインストールが簡単ですが、基本的には「1人で使うこと」に特化しています。

私が「Ollama + Open WebUI」の組み合わせを推す理由は、拡張性と実務適応力です。
Open WebUIは、PDFやテキストファイルを読み込ませるRAG（検索拡張生成）機能が標準で備わっており、UIもChatGPTに極めて近いため家族やチームでの共有も容易です。
また、Ollamaはバックエンドでサーバーとして常駐するため、PythonスクリプトからAPI経由で呼び出すといった「自動化」への発展が非常にスムーズです。
「ただチャットして終わり」ではなく、将来的に業務システムに組み込むことを見据えるなら、この構成一択だと断言します。

## Step 1: 環境を整える

まずはLLM（大規模言語モデル）を実行するエンジンである「Ollama」をインストールします。

1. [Ollama公式サイト](https://ollama.com/)にアクセスし、OSに合わせたインストーラーをダウンロードして実行します。
2. インストール完了後、ターミナル（WindowsならPowerShell）を開き、以下のコマンドを入力してバージョンが表示されれば成功です。

```bash
ollama --version
# ollama version is 0.3.x のように表示されればOK
```

次に、GUI（画面）となる「Open WebUI」を動かすためにDockerを導入します。
なぜDockerを使うのかというと、Open WebUIには多くの依存ライブラリがあり、直接PCにインストールすると環境を汚したり、設定で高確率で詰まるからです。
Docker Desktopを公式サイトからインストールし、起動しておいてください。

⚠️ **落とし穴:**
WindowsユーザーでWSL2（Windows Subsystem for Linux）が有効になっていない場合、Dockerが起動しません。
「Docker Desktop requires a newer WSL kernel version」というエラーが出たら、メッセージに従ってカーネルのアップデートを行ってください。

## Step 2: 基本の設定

OllamaとOpen WebUIを連携させて起動します。
ここでは、最もトラブルが少なく、かつGPUをしっかり認識させるための「Docker Compose」を使った設定を行います。

適当なフォルダ（例: `C:\ai-local`）を作成し、その中に `docker-compose.yaml` という名前で以下の内容を保存してください。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    # Ollamaが同じPCで動いている場合、ホスト側のネットワークを参照させる設定
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/data
    environment:
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'
    restart: always

volumes:
  open-webui: {}
```

この設定の肝は `OLLAMA_BASE_URL` です。
Dockerコンテナの中から見ると、自分のPC（ホスト）は `host.docker.internal` という名前で参照できます。
これを指定しないと、ブラウザの画面は出るのに「AIと通信できない」という状態に陥ります。

設定ファイルを保存したら、そのフォルダで以下のコマンドを実行します。

```bash
docker compose up -d
```

これで、ブラウザから `http://localhost:3000` にアクセスすれば、ログイン画面が表示されます。
最初の1人は管理者アカウントとして登録されます（メールアドレスとパスワードはローカル保存なので、何でも構いません）。

## Step 3: 動かしてみる

ログインできても、まだ「脳」となるモデルがありません。
まずは世界標準のモデルをダウンロード（プル）してみましょう。

1. Open WebUIの画面左下、設定アイコン（歯車）をクリックします。
2. 「Settings」>「Models」を開きます。
3. 「Pull a model from Ollama.com」の入力欄に `llama3.1` と入力し、ダウンロードボタンを押します。

ダウンロードが進まない場合は、ターミナルから直接以下のコマンドを打つ方が確実です。

```bash
ollama run llama3.1
```

### 期待される出力

ダウンロードが終わると、チャット画面上部のモデル選択から `llama3.1:latest` が選べるようになります。
試しに「ローカルLLMを構築するメリットを3つ教えて」と投げてみてください。

```
1. プライバシーの保護: データが外部サーバーに送信されません。
2. コスト削減: API利用料がかからず、無料で使い放題です。
3. オフライン利用: インターネットがない環境でも動作します。
```

レスポンスが返ってくれば成功です。
もし回答が異常に遅い場合は、GPUが使われずCPUだけで計算している可能性があります。
Windowsのタスクマネージャーで「専用GPUメモリ」の使用量が増えているか確認してください。

## Step 4: 実用レベルにする

単なるチャットで終わらせるのはもったいないです。
実務で使えるレベルに引き上げるため、「ドキュメント参照（RAG）」機能を試しましょう。

Open WebUIには、PDFやCSVをチャット欄にドラッグ＆ドロップするだけで、その内容に基づいた回答を生成する機能があります。
例えば、社内の仕様書PDFを読み込ませて「このシステムのデータベース構成を要約して」と指示を出すことができます。

この機能をさらに強力にするために、以下の設定変更をおすすめします。

1. **埋め込みモデルの変更:** デフォルトの埋め込みモデル（文章をベクトル化するモデル）よりも、日本語に強いモデルを指定することで、検索精度が劇的に上がります。
2. **Web検索の有効化:** 設定から「Web Search」を有効にし、SerperなどのAPIキーを入れることで、ローカルLLMが最新のニュースをネットで拾ってきて回答できるようになります。

また、エンジニアなら「Pythonからこのローカル環境を叩く」ことも検討してください。
以下のコードで、自分の構築したOllamaにプログラムからアクセスできます。

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

    # OllamaのAPIを叩く
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Error: {response.status_code}"

# 実用例：特定のテキストを要約させる
text = "ここに長い文章を入力します..."
result = ask_local_ai(f"以下の文章を100字以内で要約してください：\n\n{text}")
print(result)
```

このスクリプトを使えば、社内秘の大量のログファイルを一括で要約したり、特定の形式に整形したりする処理を、情報漏洩のリスクゼロで自動化できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Failed | Open WebUIがOllamaを見つけられていない | docker-composeの `OLLAMA_BASE_URL` が正しいか確認。 |
| 回答が壊滅的に遅い | GPUではなくCPUで動作している | NVIDIA Container Toolkitが未導入か、VRAM不足。 |
| モデルのプルが失敗する | ストレージ容量不足、またはネットワーク制限 | `Cドライブ` の空き容量を確認。プロキシ環境なら環境変数設定が必要。 |

## 次のステップ

無事に動いたら、次は「モデルの使い分け」をマスターしてください。
Llama 3.1は汎用性が高いですが、日本語の自然さなら「Gemma 2 9B」や、サイバーエージェントが公開しているモデルの方が優れた結果を出すことがあります。
Ollamaなら `ollama run gemma2` と打つだけで、数分後には新しい脳に入れ替えられます。

また、RTX 3090や4090のようなVRAM 24GBクラスのGPUを手に入れたら、さらに巨大な「70B（700億パラメータ）」モデルに挑戦してください。
70Bクラスになると、もはやGPT-4oと遜色ない推論能力をローカルで発揮できます。
ここまで来ると、独自の知識を学習させる「ファインチューニング」も視野に入ってきます。
まずは色々なモデルをプルして、自分のPCの限界性能を確かめることから始めてみましょう。

## よくある質問

### Q1: Dockerを使わずに構築できますか？

可能です。Open WebUIはPython環境（pip）で直接インストールもできます。
ただし、依存ライブラリの競合が非常に起きやすく、初心者が環境構築で挫折する原因の9割がこれです。
メンテナンス性やOS再インストール時の再現性を考えると、Dockerを強く推奨します。

### Q2: 家族や友人のPCからもアクセスできますか？

同じWi-Fi（LAN）内であれば可能です。
Open WebUIを動かしているPCのローカルIPアドレス（例: 192.168.1.10）を調べ、他のPCのブラウザから `http://192.168.1.10:3000` を叩けばアクセスできます。
もちろん、パスワード設定は忘れないようにしてください。

### Q3: ノートPCのバッテリー持ちへの影響は？

劇的に悪化します。
ローカルLLMの推論はGPUをフルパワーで回すため、ゲーミングノートなどの場合はACアダプタ接続が必須です。
逆に、MacBook（Apple Silicon）の場合は、専用の推論エンジンにより消費電力を抑えつつ高速に動作するため、モバイル環境での利用に向いています。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-08-09-ollama-openwebui-local-llm-tutorial/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-07-27-ollama-open-webui-local-llm-setup/)
- [OllamaとOpen WebUIの使い方！自分専用のローカルLLM環境を完全構築する方法](/posts/2026-06-26-ollama-open-webui-local-llm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerを使わずに構築できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Open WebUIはPython環境（pip）で直接インストールもできます。 ただし、依存ライブラリの競合が非常に起きやすく、初心者が環境構築で挫折する原因の9割がこれです。 メンテナンス性やOS再インストール時の再現性を考えると、Dockerを強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "家族や友人のPCからもアクセスできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "同じWi-Fi（LAN）内であれば可能です。 Open WebUIを動かしているPCのローカルIPアドレス（例: 192.168.1.10）を調べ、他のPCのブラウザから http://192.168.1.10:3000 を叩けばアクセスできます。 もちろん、パスワード設定は忘れないようにしてください。"
      }
    },
    {
      "@type": "Question",
      "name": "ノートPCのバッテリー持ちへの影響は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "劇的に悪化します。 ローカルLLMの推論はGPUをフルパワーで回すため、ゲーミングノートなどの場合はACアダプタ接続が必須です。 逆に、MacBook（Apple Silicon）の場合は、専用の推論エンジンにより消費電力を抑えつつ高速に動作するため、モバイル環境での利用に向いています。 ---"
      }
    }
  ]
}
</script>

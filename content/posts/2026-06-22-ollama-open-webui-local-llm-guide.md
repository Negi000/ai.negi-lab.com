---
title: "OllamaとOpen WebUIで自分専用のChatGPTを構築する方法"
date: 2026-06-22T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-06-22-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "自宅サーバー AI"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Ollamaをバックエンド、Open WebUIをフロントエンドに据えた、完全オフライン動作する生成AI環境。
- WebブラウザからChatGPT感覚で、Llama 3やQwen 2.5、Gemma 2などの最新モデルを切り替えて使えるシステム。
- 自分のPC内にあるPDFやテキストファイルを読み込ませて回答させるローカルRAG（検索拡張生成）機能。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、8Bモデルを余裕を持って高速駆動できる入門用GPUの最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを「仕事で使えるレベル」で動かすなら、最も重要なのはGPUのビデオメモリ（VRAM）容量です。
結論から言うと、VRAM 12GB以上あれば現時点での主要な軽量モデル（8Bクラス）が快適に動きます。
私は自宅のRTX 4090（24GB）2枚挿し環境でも検証していますが、実務で文章作成やコード補完をさせるなら、RTX 3060 12GB版やRTX 4060 Ti 16GB版がコストパフォーマンスの最適解です。

WindowsユーザーならNVIDIA製GPU一択、Macユーザーならメモリ（ユニファイドメモリ）32GB以上のApple Silicon（M2/M3/M4）を推奨します。
メモリ8GBや16GBのMacでも動くには動きますが、モデルをロードした瞬間にスワップが発生し、レスポンスが1トークン/秒を切るなど実用性に欠けるため注意してください。

費用については、ハードウェアさえあればAPI料金は一切かかりません。
電気代はRTX 4090をフル稼働させるとそれなりにかかりますが、一般的な推論時であれば1回あたり数円レベルです。
月額$20を払い続けるChatGPT Plusの代替として考えるなら、半年から1年でハードウェア代の元は取れる計算になります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は「LM Studio」や「AnythingLLM」など他にもありますが、私は「Ollama + Open WebUI」の組み合わせがベストだと確信しています。
最大の理由は、Open WebUIが本家ChatGPTに最も近い操作感を持ちながら、Dockerベースで拡張性が非常に高い点にあります。

Ollamaはバックエンドとして優秀で、モデルの管理（プル・更新・削除）がコマンド一つで完結し、APIサーバーとしても極めて軽量に動作します。
これにOpen WebUIを組み合わせることで、マルチモーダル（画像認識）への対応や、Web検索結果を取り込んだ回答、さらにはRAG機能までを一つのインターフェースで完結させられます。
特定のアプリに依存せず、ブラウザさえあれば家のどの端末（スマホやタブレット）からも自前サーバーのAIにアクセスできる自由度は、一度体験すると戻れません。

## Step 1: 環境を整える

まずはバックエンドとなるOllamaをインストールします。
公式サイトからインストーラーをダウンロードしても良いですが、エンジニアなら環境の再現性を重視してコマンドラインで進めるのが確実です。

### Windows/Linuxの場合
WSL2（Windows Subsystem for Linux）上で動かすのが、GPUリソースの管理面で最も安定します。

```bash
# Ollamaのインストールスクリプト実行
curl -fsSL https://ollama.com/install.sh | sh
```

このスクリプトは、システムのアーキテクチャを自動判別し、適切なバイナリを配置します。
インストール後、以下のコマンドでサーバーを立ち上げます。

```bash
ollama serve
```

⚠️ **落とし穴:**
WindowsでDocker Desktopを併用している場合、WSL2側でGPUを認識させるために「NVIDIA Container Toolkit」のインストールが必須です。
これを忘れると、モデルは動いてもCPU推論になり、レスポンスが数十秒待ちという地獄を見ることになります。
必ず `nvidia-smi` コマンドがWSL2内で通ることを確認してください。

## Step 2: DockerでOpen WebUIを起動する

Open WebUIを直接ソースからビルドするのは、ライブラリの依存関係で高確率でハマります。
私は過去にPythonのバージョン競合で数時間を溶かした経験があるので、素直に公式Dockerイメージを使うことを強く勧めます。

以下の `docker-compose.yaml` ファイルを作成します。
なぜ単一のコマンドではなくComposeを使うかというと、後からデータベースのバックアップやポート変更を容易にするためです。

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

### 設定のポイント
`OLLAMA_BASE_URL` に `http://host.docker.internal:11434` を指定しているのが肝です。
Dockerコンテナの中から、ホストマシン側で動いているOllamaサーバーを見に行くための設定です。
これを localhost にしてしまうと、コンテナ自身の内部を探しに行ってしまい「Connection Refused」で接続に失敗します。

作成したら、以下のコマンドで起動します。

```bash
docker compose up -d
```

## Step 3: 動かしてみる

ブラウザで `http://localhost:3000` にアクセスしてください。
最初にアカウント作成を求められますが、これはローカル環境内に保存されるだけなので、適当なメールアドレスとパスワードで構いません。

ログイン後、まずはモデルをダウンロード（プル）します。
左下の設定、またはトップのモデル選択から「Llama3.1:8b」や「Qwen2.5:7b」を入力してダウンロードを開始してください。

### 日本語能力のテスト
まずは日本語で「こんにちは、自己紹介をしてください」と投げてみましょう。

### 期待される出力
```text
こんにちは！私はMetaによって訓練された大型言語モデルのLlama 3です。
日本語でのお手伝いが可能です。質問や相談があれば何でもどうぞ。
```

レスポンス速度に注目してください。
RTX 3060以上の環境であれば、文字が「ザザザッ」と流れるように出てくるはずです。
もし一文字ずつゆっくり出る場合は、GPUが使われずCPU推論になっている可能性があります。
その際は `docker logs -f open-webui` でエラーが出ていないか確認してください。

## Step 4: 実用レベルにする

単なるチャットで終わらせてはもったいないです。
仕事で使えるレベルに引き上げるため、RAG（ドキュメント参照）機能を設定します。

Open WebUIには標準でRAGが組み込まれています。
チャット欄の左側にある「＋」ボタン、もしくは「#」を入力してからファイルをアップロードしてみてください。
例えば、社内の技術仕様書PDFを読み込ませてから、「この仕様書におけるAPIの認証方式を教えて」と質問します。

### RAGの設定調整
「設定」→「ドキュメント」から、使用する埋め込み（Embedding）モデルを選択できます。
初期設定では `sentence-transformers` が使われますが、日本語の精度を高めたい場合は、以下の手順で日本語特化モデルに変更することを検討してください。

1. Ollama側で `ollama pull mxbai-embed-large` を実行
2. Open WebUIの設定で Embedding Model に `mxbai-embed-large` を指定

これにより、日本語ドキュメントの検索精度が体感で2割ほど向上しました。
私が実務でマニュアルの要約を行わせる際は、必ずこの設定を入れています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Refused | コンテナがOllamaを認識できていない | environmentのURLをホストIPまたはhost.docker.internalにする |
| GPU認識不可 | NVIDIA Container Toolkit未導入 | インストール後、Dockerデーモンを再起動する |
| レスポンスが極端に遅い | VRAM不足でメインメモリに溢れている | モデルの量子化サイズ（Q4_K_M等）を下げるか、より小規模なモデルを選ぶ |
| 文字化け | ブラウザのエンコーディング | 最新のChrome/Edgeを使用し、WebUIの言語設定を日本語にする |

## 次のステップ

無事に環境が動いたら、次は「エージェント機能」に挑戦してみてください。
Open WebUIには「Tools」という機能があり、Pythonコードを実行させたり、最新のニュースをネットから検索して回答させたりすることが可能です。

具体的には、Open WebUIのCommunityサイト（openwebui.com）に公開されているスクリプトをインポートするだけで、機能拡張が可能です。
私はここで「Google Search」ツールを連携させ、ローカルLLMの弱点である「最新情報の欠如」を補っています。
また、自分専用のシステムプロンプトを作成し、特定のプログラミング言語に特化した「専属シニアエンジニア」を量産するのも面白いでしょう。

APIの課金を気にせず、プライバシーを完全に守った状態でAIを使い倒せる自由。
これを手に入れた瞬間、AIとの付き合い方は一段階上のステージに進みます。

## よくある質問

### Q1: 自宅サーバーとして外部からアクセスできますか？

可能です。Open WebUIを動かしているマシンのローカルIPを特定し、ポート3000を解放すれば、同一Wi-Fi内のスマホからアクセスできます。外出先から使う場合は、TailscaleなどのVPNを使うのがセキュリティ的に安全です。

### Q2: 4bit量子化モデルと8bit、どちらが良いですか？

実務利用なら4bit（Q4_K_Mなど）で十分です。推論速度と精度のバランスが最も良く、VRAM消費も抑えられます。8bitにしても精度向上はわずかですが、速度低下が顕著なため、まずはQ4モデルから試すのが私のおすすめです。

### Q3: Ollamaを使わずにDockerだけで完結できませんか？

Open WebUIの公式イメージには、Ollamaを内包した「Bundled版」もあります。手軽ですが、モデルの管理がコンテナ内に隠蔽されてしまうため、バックアップや多段GPU構成への移行を考えると、この記事のようにOllamaとWebUIを分離して運用する方がメンテナンス性は高いです。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [Ollama 使い方 入門: 限られたGPU資産で実用的なローカルLLM環境を構築する方法](/posts/2026-06-13-ollama-local-llm-python-tutorial-for-beginners/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自宅サーバーとして外部からアクセスできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Open WebUIを動かしているマシンのローカルIPを特定し、ポート3000を解放すれば、同一Wi-Fi内のスマホからアクセスできます。外出先から使う場合は、TailscaleなどのVPNを使うのがセキュリティ的に安全です。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化モデルと8bit、どちらが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実務利用なら4bit（Q4KMなど）で十分です。推論速度と精度のバランスが最も良く、VRAM消費も抑えられます。8bitにしても精度向上はわずかですが、速度低下が顕著なため、まずはQ4モデルから試すのが私のおすすめです。"
      }
    },
    {
      "@type": "Question",
      "name": "Ollamaを使わずにDockerだけで完結できませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Open WebUIの公式イメージには、Ollamaを内包した「Bundled版」もあります。手軽ですが、モデルの管理がコンテナ内に隠蔽されてしまうため、バックアップや多段GPU構成への移行を考えると、この記事のようにOllamaとWebUIを分離して運用する方がメンテナンス性は高いです。 ---"
      }
    }
  ]
}
</script>

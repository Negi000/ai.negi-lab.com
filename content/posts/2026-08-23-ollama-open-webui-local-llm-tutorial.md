---
title: "OllamaとOpen WebUIで自分専用のセキュアなローカルLLM環境を構築する方法"
date: 2026-08-23T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-23-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "Docker GPU設定"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Dockerを使用して、ブラウザからChatGPT感覚で操作できる「Open WebUI」と、バックエンドで推論を担う「Ollama」を連携させた環境を構築します。
- 外部API（OpenAIなど）にデータを送ることなく、完全オフラインかつ無料でLLM（大規模言語モデル）を動かせる仕組みを作ります。
- 必要なものは、DockerがインストールされたPCと、それなりのGPU（またはMac）だけです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。7Bクラスのモデルが快適に動きます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのはCPUではなく「VRAM（ビデオメモリ）」の容量です。
私がRTX 4090の2枚挿し（VRAM 48GB）にこだわっているのは、量子化されていない大型モデルを動かすためですが、入門ならそこまで必要ありません。

最低ラインはVRAM 8GB（RTX 3060 8GB等）ですが、これだとLlama 3.1 8Bクラスを動かすのが精一杯で、少し複雑なことをさせるとレスポンスが1秒間に数単語という速度まで落ち込みます。
ストレスなく実務で使うなら、VRAM 12GB以上のグラフィックボードを推奨します。
具体的にはRTX 3060 12GB版や、RTX 4070 Ti Super（VRAM 16GB）がコストパフォーマンスの面で賢い選択ですね。

Macユーザーであれば、メモリ16GB以上のApple Silicon（M1/M2/M3）なら十分実用圏内です。
MacはシステムメモリをVRAMとして共有できるため、32GB以上のメモリを積んだモデルなら、少し重めのモデルも軽快に動きます。

費用については、ハードウェア代を除けば完全無料です。
API料金の請求に怯えながらプロンプトを試行錯誤する日々から解放されるメリットは、想像以上に大きいですよ。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには、LM StudioやGPT4Allなど、クリックだけで完結するGUIツールも存在します。
それらと比較して、なぜ私が「Ollama + Open WebUI」の組み合わせを推すのか。

理由は「拡張性」と「インターフェースの完成度」にあります。
Ollamaはバックエンドとして非常に優秀で、APIがOpenAI互換であるため、CursorやDifyといった外部ツールとの連携が極めてスムーズです。
一方、Open WebUIは、本家ChatGPTに限りなく近い操作感を提供しており、RAG（ドキュメント読み込み）機能や画像生成（ComfyUI連携など）といった高度な機能を標準で備えています。

「ただ動かす」だけならLM Studioで十分ですが、「仕事のワークフローに組み込む」なら、この構成が現在のベストプラクティスだと断言できます。

## Step 1: 環境を整える

まずは、ベースとなるOllamaとDockerの準備をします。
WindowsやMacの方はDocker Desktopを、Linuxの方はDocker Engineをインストールしておいてください。

Linux環境でGPUを使用する場合は、NVIDIA Container Toolkitのインストールが必須です。
これがないと、Dockerコンテナ内からGPUを認識できず、推論がCPU実行になってしまい、レスポンスに数十秒かかるという地獄を見ることになります。

```bash
# NVIDIA Container Toolkitのインストール（Ubuntuの例）
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

⚠️ **落とし穴:**
WindowsのDocker Desktopを使っている場合、設定（Settings）→ Resources → WSL integrationで、使用しているディストリビューションが有効になっているか確認してください。
ここを忘れると、`nvidia-smi`コマンドがコンテナ内で通らず、GPUが宝の持ち腐れになります。

## Step 2: 基本の設定

個別にコマンドを叩くのは面倒なので、`docker-compose.yml`を作成して一括管理します。
適当な作業ディレクトリを作成し、以下の内容を保存してください。

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
      file: docker-compose.yaml # 自身を参照する設定ミスを防ぐため通常は直接記述
    build:
      context: .
      args:
        ollama_base_url: /ollama
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

各設定のポイントを解説します。
`OLLAMA_BASE_URL`に`http://ollama:11434`を指定しているのは、Dockerのネットワーク内でコンテナ名を使って通信するためです。
また、`volumes`を設定することで、ダウンロードしたモデルデータや会話履歴がコンテナを削除しても消えないようにしています。
モデルデータは1つ数GBから数十GBあるので、再ダウンロードの手間を省くのは実運用で必須の対策です。

## Step 3: 動かしてみる

ディレクトリで以下のコマンドを実行し、コンテナを起動します。

```bash
docker compose up -d
```

起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント作成を求められますが、これは「ローカル環境内の管理用アカウント」なので、好きなメールアドレスとパスワードで登録して大丈夫です。
外部に送信されることはありません。

ログイン後、まずはモデルをダウンロードする必要があります。
画面左下の設定アイコン、またはモデル選択メニューから「Llama 3.1」や、日本語に強い「Qwen 2.5 7B」などをプル（ダウンロード）してください。

### 期待される出力

ダウンロードが完了し、チャット欄に「こんにちは、自己紹介してください」と入力して、以下のような返答が返ってくれば成功です。

```
こんにちは！私はQwenという大規模言語モデルです。
あなたのローカル環境で動作しており、プライバシーを保ちながらお手伝いできます。
本日はどのようなご用件でしょうか？
```

レスポンス速度に注目してください。
GPUが正しく認識されていれば、文字が流れるように出力されるはずです。
もし、一文字ずつポツ、ポツと出るようなら、Step 1のGPU設定を疑ってください。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分ですが、ローカル環境の真骨頂は「RAG（検索拡張生成）」の活用にあります。
Open WebUIには、PDFやテキストファイルをアップロードして、その内容に基づいた回答をさせる機能が標準搭載されています。

例えば、社外秘のプロジェクト資料や、分厚い技術ドキュメントを読み込ませてみてください。
Open WebUIのチャット欄にファイルをドラッグ＆ドロップし、プロンプトで「#」を入力すると、アップロードしたドキュメントをソースとして指定できます。

```text
#資料.pdf この仕様書の内容に基づき、APIの実装手順を3ステップでまとめて。
```

これをクラウドLLMでやろうとすると、情報漏洩のリスクを気にする必要がありますが、ローカル環境なら完全に安全です。
私は自分専用の技術Wiki（数千ファイル）を全てインデックス化しており、過去の自分のコードから解決策を探し出す「セカンドブレイン」として運用しています。

また、APIエンドポイント（`http://localhost:11434/v1`）を公開すれば、Cursorなどのエディタから自分のローカルLLMを呼び出し、コード補完を行わせることも可能です。
これができるようになると、開発効率が劇的に変わります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Error: could not connect to ollama` | Open WebUIがOllamaコンテナを見失っている | `OLLAMA_BASE_URL`が正しいか確認。Dockerの再起動を試す。 |
| 回答が極端に遅い | CPUで推論が走っている | `docker logs ollama`を確認。GPUが検出されているかチェック。 |
| モデルのDLが途中で止まる | ストレージ容量不足またはタイムアウト | モデルデータは数GBあります。ディスク空き容量を確保してください。 |

## 次のステップ

環境が整ったら、次は「システムプロンプト」の最適化に挑戦してみてください。
Open WebUIでは「モデルファイル」として、特定の役割を持たせたエージェントを保存できます。
「熟練のPythonエンジニア」や「辛口のコードレビュアー」などの設定を作り込むことで、回答の質は驚くほど変化します。

さらに上を目指すなら、Docker ComposeにComfyUIを追加し、画像生成もローカルで完結させる構成も面白いですよ。
私のブログでは、ComfyUIとOllamaを連携させて「プロンプトから画像生成までを自動化するワークフロー」も解説しているので、興味があればぜひ。

## よくある質問

### Q1: VRAMが足りない場合、モデルを動かすことは全く不可能ですか？

動かすこと自体は可能です。OllamaはVRAMが足りない分をメインメモリ（RAM）にオフロードして処理します。ただし、推論速度は10倍から100倍ほど遅くなります。数秒で終わるはずの回答に数分かかるため、実用的とは言えません。

### Q2: 複数のモデルを同時に動かすことはできますか？

可能です。ただし、複数のモデルをVRAM上にロードしようとすると、メモリ不足でクラッシュしやすくなります。Ollamaは自動的にモデルを入れ替えてくれますが、切り替え時に数秒の待ち時間が発生します。

### Q3: 外部のPCやスマホからこのWebUIにアクセスできますか？

できます。Dockerを実行しているPCのIPアドレスを調べ、同じLAN内であれば `http://<PCのIP>:3000` でアクセス可能です。外出先からアクセスしたい場合は、TailscaleなどのVPNサービスを利用するのが安全で簡単ですね。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用の機密保持ローカルLLM環境を作る方法](/posts/2026-07-23-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "VRAMが足りない場合、モデルを動かすことは全く不可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動かすこと自体は可能です。OllamaはVRAMが足りない分をメインメモリ（RAM）にオフロードして処理します。ただし、推論速度は10倍から100倍ほど遅くなります。数秒で終わるはずの回答に数分かかるため、実用的とは言えません。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、複数のモデルをVRAM上にロードしようとすると、メモリ不足でクラッシュしやすくなります。Ollamaは自動的にモデルを入れ替えてくれますが、切り替え時に数秒の待ち時間が発生します。"
      }
    },
    {
      "@type": "Question",
      "name": "外部のPCやスマホからこのWebUIにアクセスできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "できます。Dockerを実行しているPCのIPアドレスを調べ、同じLAN内であれば http://<PCのIP>:3000 でアクセス可能です。外出先からアクセスしたい場合は、TailscaleなどのVPNサービスを利用するのが安全で簡単ですね。 ---"
      }
    }
  ]
}
</script>

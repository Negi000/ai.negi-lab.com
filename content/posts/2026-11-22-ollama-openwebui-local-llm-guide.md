---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-11-22T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-11-22-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker LLM サーバー"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、完全にオフラインかつ無料でChatGPTと同等の操作感を実現するローカルLLM環境を構築します。
- ブラウザから複数のAIモデル（Llama 3.1、Gemma 2、Qwen 2.5等）を切り替え、PDFなどのドキュメントを読み込ませるRAG機能までを動作させます。
- Python等からAPIとして呼び出すためのバックエンド基盤としても機能させます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MSI RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、中規模モデルを安価に動かすための最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMの世界では、CPU性能よりもVRAM（ビデオメモリ）の容量がすべてを決めます。
私がRTX 4090を2枚挿しているのは、単に速いからではなく、巨大なモデルをVRAMに載せきるためです。

まず、自分のPCスペックを確認してください。
WindowsならRTX 3060（12GBモデル）以上、MacならM1/M2/M3チップを搭載し、メモリが16GB以上あることが最低ラインです。
VRAMが8GB以下の場合は、Llama 3.1 8Bのような小型モデルであれば動作しますが、レスポンスにストレスを感じる可能性があります。

逆に、最新のRTX 40シリーズやApple Silicon Macであれば、月額$20のChatGPT Plusを解約できるレベルの快適さが手に入ります。
電気代を除けば、運用コストは完全にゼロです。
クラウドにデータを送りたくない機密性の高い案件を扱う実務者にとって、この環境は最強の武器になります。

## なぜこの方法を選ぶのか

ローカルLLMを動かすツールには、LM StudioやGPT4Allなどもあります。
それらと比較して、なぜ「Ollama + Open WebUI」の組み合わせがベストなのか。

理由は3つあります。
第一に、Ollamaのモデル管理が極めて優秀だからです。
`ollama run`の一言で、Hugging Faceからモデルを探して量子化する手間なく、最適な設定でモデルが立ち上がります。

第二に、Open WebUIが「仕事で使える」レベルのインターフェースを持っているからです。
複数人での共有、RAG（ドキュメント読み込み）、Web検索機能、画像生成連携など、商用サービスに劣らない機能がDocker一つで手に入ります。

第三に、拡張性です。
Ollamaは裏側でAPIサーバーとして動くため、自作のPythonスクリプトやCursorなどのエディタから簡単に接続できます。
「ただチャットするだけ」で終わらないのが、この組み合わせの最大の利点です。

## Step 1: Ollamaのインストールと動作確認

まずはエンジンとなるOllamaを導入します。
これはバックグラウンドでLLMを動かすためのデーモンとして機能します。

Ollama公式サイト（ollama.com）からインストーラーをダウンロードし、実行してください。
インストール後、ターミナル（WindowsならPowerShell）を開き、以下のコマンドを叩きます。

```bash
# バージョンが表示されればインストール成功
ollama --version

# Llama 3.1 8Bモデルをダウンロードして実行
ollama run llama3.1
```

初回はモデルのダウンロード（約4.7GB）が始まります。
終了後、プロンプトが表示されたら何か入力してみてください。
「Hello」と打って0.5秒以内に返信が来れば、GPUが正しく認識されています。
返信が1文字ずつゆっくり出てくる場合は、CPU実行になっている可能性があります。

⚠️ **落とし穴:**
Windowsユーザーで「GPUが使われていない気がする」場合、WSL2（Windows Subsystem for Linux）の設定や、NVIDIAドライバのバージョンが古いことが原因の9割です。
必ず最新のGame Readyドライバ、あるいはStudioドライバをインストールしてください。

## Step 2: DockerによるOpen WebUIの構築

次に、ブラウザから操作するためのGUI「Open WebUI」を立ち上げます。
本体を汚さず、依存関係を気にしなくて済むDockerを利用するのが最もクリーンな方法です。

Docker Desktopがインストールされている前提で、以下のコマンドを実行します。
ここでは、Ollamaが同じPC上で動いている場合の設定を書きます。

```bash
# GPUを利用可能な形式でOpen WebUIを起動
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します。
`-p 3000:8080`は、ブラウザから `localhost:3000` でアクセスするための設定です。
`--add-host=host.docker.internal:host-gateway` は、Dockerコンテナの中からホストPC上で動いているOllamaを見つけるために必須の設定です。
これを忘れると、WebUIから「Ollamaに接続できません」と怒られます。

⚠️ **落とし穴:**
Mac (Apple Silicon) の場合、Dockerの設定で「Use Rosetta 2 for x86_64/amd64 emulation」がオンになっていると動作が不安定になることがあります。
基本的にはネイティブなarm64イメージが選ばれますが、設定を見直しておくと無難です。

## Step 3: Webインターフェースの初期設定とモデル選択

ブラウザで `http://localhost:3000` を開きます。
最初にアカウント作成を求められますが、これはローカルに保存されるものなので、適当なメールアドレスとパスワードで構いません。
外部に送信されることはありません。

ログイン後、左上の設定アイコン（歯車）から「Settings」→「Connections」を確認します。
OllamaのURLが `http://host.docker.internal:11434` になっており、接続テストが通れば準備完了です。

次に、使いたいモデルを選択します。
トップ画面のモデル選択プルダウンに、先ほどコマンドラインで落とした `llama3.1:latest` が表示されているはずです。
もし他のモデルを試したいなら、プルダウンから直接モデル名を入力してダウンロードすることも可能です。

私が実務で推奨するモデルは以下の3つです。
1. **Llama 3.1 8B**: 汎用性が高く、動作が軽い。日常的な要約や翻訳に。
2. **Gemma 2 9B**: Google製。日本語の自然さが際立っています。
3. **Qwen 2.5 7B/14B**: コード生成や論理的思考に強い。エンジニアなら必携。

### 期待される出力

チャット画面で「Pythonで素数を判定する関数を書いて」と入力し、数秒でシンタックスハイライト付きのコードが返ってくれば成功です。
レスポンス速度（トークン/秒）は、画面右下の統計情報から確認できます。
15 tokens/s 以上出ていれば、読書スピードを上回るので快適に使えます。

## Step 4: 実用レベルのカスタマイズ（ModelfileとRAG）

ここからが「仕事で使える」かどうかの分かれ目です。
デフォルトの設定では、AIの回答が素っ気なかったり、期待するフォーマットにならなかったりします。

### 1. Modelfileで「自分専用AI」を定義する

Ollamaには `Modelfile` という設定ファイルがあり、システムプロンプト（役割設定）を固定できます。
例えば、「あなたは優秀なPythonエンジニアで、必ず型ヒントを付け、日本語で解説してください」という設定を焼き込んだモデルを作れます。

Open WebUI上で「Workspace」→「Models」から新しいモデルを作成し、ベースモデルを選択した上で「System Prompt」を記述してください。
これにより、毎回「日本語で答えて」と言う手間が省けます。

### 2. RAG（外部ドキュメント参照）を活用する

Open WebUIの強力な機能の一つが、PDFやテキストファイルをアップロードして、その内容に基づいた回答をさせる機能です。
チャット欄にファイルをドラッグ＆ドロップするか、`#` を入力してドキュメントを指定します。

私の場合、SIer時代の古い設計書（PDF）を読み込ませ、現在の技術スタックで書き直すための壁打ち相手として活用しています。
商用AIに投げられない社外秘の資料でも、ローカル環境なら安心して処理できます。

### 3. APIとして呼び出す

Pythonからこの環境を利用する方法も覚えておきましょう。
`ollama` ライブラリを使えば、驚くほど簡単に自作ツールに組み込めます。

```python
import ollama

# サーバーと通信して回答を得る
# stream=Trueにすることで、ChatGPTのように逐次表示が可能
response = ollama.chat(model='llama3.1', messages=[
  {
    'role': 'user',
    'content': 'ローカルLLMを導入する最大のメリットを3点、箇条書きで教えて。',
  },
])

print(response['message']['content'])
```

このコードを回す際、バックグラウンドでOllamaさえ動いていれば、特別なAPIキーは不要です。
社内ツールの自動化スクリプトなどに組み込む際、コストを気にせず数万回の試行を繰り返せるのは、開発者にとって至福の環境です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection Refused | Dockerからホストへの接続設定ミス | `host.docker.internal` の設定を見直す |
| 動作が異常に重い | VRAM不足でメインメモリ（RAM）にはみ出している | モデルの量子化サイズ（Q4, Q2等）を下げる |
| WebUIにモデルが出ない | Ollamaのモデルダウンロード未完了 | `ollama list` でモデルが存在するか確認 |
| Docker起動失敗 | NVIDIA Container Toolkitの未導入 | Linux/WSL2の場合はToolkitのインストールが必須 |

## 次のステップ

環境が整ったら、次は「プロンプトエンジニアリング」よりも「モデルの使い分け」を意識してみてください。
特定のタスクに特化したモデル（例えばコーディング特化の `deepseek-coder-v2` など）をOllamaで追加し、Open WebUIで切り替えながら使うことで、作業効率は劇的に上がります。

さらに踏み込むなら、Open WebUIの「Functions」機能を調べてみてください。
Pythonコードを記述して、LLMに特定のツール（計算機やWeb検索、DB操作）を実行させる「エージェント」的な動きをさせることが可能です。

ローカル環境は、壊しても誰にも迷惑をかけません。
設定ファイルをいじり倒し、自分の業務に最もフィットする構成を見つけ出してください。
それができるのが、クローズドな商用サービスにはない、ローカルLLM最大の醍醐味です。

## よくある質問

### Q1: グラボがないノートPCでも動きますか？

動きますが、快適とは言えません。CPUのみで動作させる場合、Llama 3.1 8Bで1秒間に1〜2文字程度の出力速度になります。本格的に使うなら、最低でもVRAM 12GB以上のデスクトップPCか、メモリを積んだMacをおすすめします。

### Q2: モデルのライセンスはどうなっていますか？

Llama 3.1はMetaのライセンスに従います（月間アクティブユーザー数などの制限がありますが、個人や一般的な法人利用ならほぼ無料）。各モデルのライセンス（Apache 2.0やMITなど）は、Ollamaのライブラリページで個別に確認可能です。

### Q3: 複数のPCから一つのOllamaサーバーを使えますか？

可能です。Ollamaの環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定して再起動すれば、LAN内の他のPCやスマホから接続できるようになります。自宅サーバーに強いGPUを積み、ノートPCからそこにアクセスするのが私の運用スタイルです。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-08-09-ollama-openwebui-local-llm-tutorial/)
- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-07-27-ollama-open-webui-local-llm-setup/)
- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)

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
        "text": "動きますが、快適とは言えません。CPUのみで動作させる場合、Llama 3.1 8Bで1秒間に1〜2文字程度の出力速度になります。本格的に使うなら、最低でもVRAM 12GB以上のデスクトップPCか、メモリを積んだMacをおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルのライセンスはどうなっていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1はMetaのライセンスに従います（月間アクティブユーザー数などの制限がありますが、個人や一般的な法人利用ならほぼ無料）。各モデルのライセンス（Apache 2.0やMITなど）は、Ollamaのライブラリページで個別に確認可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のPCから一つのOllamaサーバーを使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollamaの環境変数 OLLAMAHOST を 0.0.0.0 に設定して再起動すれば、LAN内の他のPCやスマホから接続できるようになります。自宅サーバーに強いGPUを積み、ノートPCからそこにアクセスするのが私の運用スタイルです。 ---"
      }
    }
  ]
}
</script>

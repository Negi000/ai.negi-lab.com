---
title: "OllamaとOpen WebUIで自分専用のローカルChatGPT環境を構築する方法"
date: 2026-11-11T00:00:00+09:00
slug: "ollama-openwebui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-11-11-ollama-openwebui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 構築"
  - "ローカルLLM GPU スペック"
  - "Docker LLM 環境"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

PC内部で完結し、外部へのデータ流出が一切ない「プライベートChatGPT環境」を構築します。
具体的には、バックエンドに軽量な推論エンジン「Ollama」、フロントエンドにChatGPTと遜色ない操作感を持つ「Open WebUI」を組み合わせたシステムです。
この構成により、Llama 3.1やGemma 2といった最新のオープンソースモデルを、Webブラウザから直感的に操作して業務に活用できるようになります。

### 前提知識
- 基本的なコマンド操作（PowerShellやターミナルでのコピペ）ができること
- Dockerの概念をなんとなく理解していること（インストール手順は解説します）

### 必要なもの
- Windows 10/11、macOS、またはLinuxが動作するPC
- インターネット接続（モデルのダウンロードに数GB使用します）
- NVIDIA製GPU（推奨）またはApple Silicon搭載Mac

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える速度」で動かすには、CPUではなくGPUの性能、特に「VRAM（ビデオメモリ）容量」がすべてを決めます。
最低ラインはVRAM 8GBです。これがあれば、現在主流の「7B〜8B（70億〜80億パラメータ）」クラスのモデルが快適に動作します。
12GBあれば少し余裕ができ、16GBあれば「14B〜20B」クラスの中規模モデルも選択肢に入ります。

もしこれからPCを新調するなら、WindowsならRTX 4060 Ti (16GBモデル) がコストパフォーマンス最強の選択肢です。
Mac派なら、メモリ32GB以上のM2/M3チップ搭載モデルを強く推奨します。MacはメインメモリをVRAMとして共有できるため、実はローカルLLMと非常に相性が良いです。
初期費用はかかりますが、API利用料（月額$20など）が一切かからないため、半年から1年使い倒せば元は取れます。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、LM StudioやGPT4Allなど他にもあります。
しかし、あえて「Ollama + Open WebUI」の組み合わせを推す理由は、圧倒的な「拡張性」と「実用性」にあります。

OllamaはAPIサーバーとして機能するため、PythonスクリプトやCursorなどのエディタから外部連携するのが非常に容易です。
そこにOpen WebUIを被せることで、RAG（ドキュメント読み込み回答）やマルチユーザー管理、さらにはWeb検索機能まで追加できます。
単に「動かして終わり」ではなく、将来的に業務フローへ組み込むことを考えるなら、この構成が現在のデファクトスタンダードだと言えます。

## Step 1: 環境を整える

まずは、推論エンジンの核となるOllamaをインストールします。

1. [Ollama公式サイト](https://ollama.com/)にアクセスし、OSに合わせたインストーラーをダウンロードします。
2. インストール完了後、ターミナル（WindowsならPowerShell）を開き、以下のコマンドを打ちます。

```bash
ollama --version
```

バージョン番号が表示されれば成功です。次に、モデルをダウンロードします。
今回は、日本語能力が高くバランスの良い「Llama 3.1 8B」を導入します。

```bash
# Llama 3.1の8Bモデルをダウンロードして起動
ollama run llama3.1
```

このコマンドは、モデルのダウンロード（約4.7GB）と対話モードの起動を同時に行います。
「>>>」と表示されたら何か入力してみてください。この時点ですでにローカルでの対話は可能です。
確認が終わったら `/bye` と入力して終了します。

⚠️ **落とし穴:**
Windowsの場合、デフォルトではGPUがうまく認識されないことがあります。
タスクマネージャーの「パフォーマンス」タブで、Ollama実行中にGPU（専用ビデオメモリ）の数値が上がっているか確認してください。
もし上がっていなければ、最新のNVIDIAドライバーをインストールし直す必要があります。

## Step 2: Dockerの導入と設定

次に、Open WebUIを動かすためのプラットフォーム「Docker」を準備します。
Open WebUIは依存関係が複雑なため、直接インストールするよりもDockerで「コンテナ」として動かすのが最もクリーンでトラブルが少ないです。

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストールします。
2. インストール後の設定で「Use the WSL 2 based engine」にチェックが入っていることを確認してください（Windowsの場合）。

ここで、GPUをDockerコンテナ内から認識させるための「NVIDIA Container Toolkit」が必要になります（Windows/Linuxのみ。Macは不要）。

```bash
# Windows (WSL2) の場合、通常はDocker Desktopの設定のみで動作しますが、
# うまくいかない場合は以下の設定を確認します。
```

Dockerの設定画面で「Resources」→「WSL Integration」を開き、使用しているディストリビューションが有効になっていることを確認してください。
これを忘れると、WebUI経由での回答が異常に遅くなる（CPU処理になる）原因になります。

## Step 3: Open WebUIを起動する

準備が整いました。以下のコマンドを1行で実行して、Open WebUIを起動します。
このコマンドは「Ollamaが同じPC上で動いている」ことを前提とした設定です。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

各オプションの意味を解説します：
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: PCの「http://localhost:3000」でアクセスできるようにします。
- `--add-host`: コンテナの中から、あなたのPC本体（Ollamaが動いている場所）を見えるようにする重要な設定です。
- `-v open-webui:/app/backend/data`: チャット履歴などのデータを保存する「ボリューム」を作成します。これがないと、コンテナを止めるたびに履歴が消えます。

### 期待される出力

コマンド実行後、長いIDが表示されれば成功です。
ブラウザを開き、`http://localhost:3000` にアクセスしてください。

ログイン画面が表示されますが、これはローカル環境なので、好きな名前とメールアドレスで「サインアップ」してアカウントを作ればOKです。
最初の1人は管理者権限を持ちます。

## Step 4: 実用レベルにする

Open WebUIが開いたら、画面上部の「モデルを選択」から、先ほどダウンロードした `llama3.1:latest` を選びます。
ここからは、実務で使うための2つの重要な設定を行います。

### 1. システムプロンプトの設定
デフォルトでは英語寄りの回答になることが多いため、「設定」→「一般」からシステムプロンプトに以下を入力します。
「あなたは優秀なアシスタントです。常に日本語で、簡潔かつ正確に回答してください。」
これにより、回答の安定感が劇的に増します。

### 2. RAG（ドキュメント参照）機能の活用
Open WebUIの強みは、PDFやテキストファイルをチャット欄にドラッグ＆ドキュメントするだけで、その内容に基づいた回答ができる点です。
「#」を入力してからファイル名を選択すると、そのファイルを参照範囲に指定できます。
例えば、社内の仕様書PDFを読み込ませれば、即座に「ローカル版・社内FAQシステム」が完成します。

```python
# PythonからOllamaを叩く例（自動化したい場合）
import requests

def chat_with_local_llm(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=data)
    return response.json()['response']

# 実行
# print(chat_with_local_llm("ローカルLLMのメリットを3つ教えて"))
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionRefusedError` | Ollamaが起動していない | タスクバーにOllamaのアイコンがあるか確認。なければ起動する。 |
| 回答が1文字ずつで非常に遅い | GPUが使われておらずCPUで推論している | Dockerの設定でGPUパススルーができているか確認。VRAM不足の可能性も。 |
| モデル一覧に何も出てこない | Open WebUIがOllamaを見失っている | Docker起動時の `--add-host` 設定を再確認。SettingsのOllama URLを `http://host.docker.internal:11434` に変更。 |

## 次のステップ

この環境が構築できたら、次は「モデルの使い分け」に挑戦してください。
例えば、コーディングには `codegemma`、論理的思考が必要なタスクには `qwen2.5` など、用途に合わせてモデルを追加ダウンロード（`ollama pull モデル名`）するだけで、瞬時に切り替えられます。

また、Open WebUIには「Functions」という機能があり、Pythonスクリプトを登録することで、AIに現在の時刻を教えたり、特定のURLの内容を取得させたりすることも可能です。
ローカルLLMは、もはや「ただのチャット」ではなく、自分のPC上のあらゆる操作を自動化する「OSの知能」になりつつあります。
まずは手元のドキュメントをいくつか読み込ませて、検索精度の高さを体感してみてください。

## よくある質問

### Q1: ネット接続がなくても動きますか？

はい、一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でも生成AIを利用できるのがローカル環境の最大の利点です。

### Q2: 家族やチームで共有して使えますか？

可能です。Open WebUIを動かしているPCのIPアドレス（例: 192.168.1.10:3000）に同じWi-Fi内の別のデバイスからアクセスすれば、家族や同僚もブラウザ経由で利用できます。

### Q3: データの学習（ファインチューニング）はできますか？

この記事の構成だけでは「学習」はできません。しかし、Open WebUIのRAG機能を使えば、追加学習なしでもあなたの持っている知識（PDFやメモ）に基づいた回答をさせることが十分に可能です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、中規模モデルまで快適に動かせるローカルLLMの最適解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIで最強のローカルLLM環境を作る方法](/posts/2026-09-24-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIの使い方！完全プライベートなローカルLLM環境を構築する方法](/posts/2026-07-07-ollama-openwebui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続がなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、一度モデルをダウンロードしてしまえば、完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でも生成AIを利用できるのがローカル環境の最大の利点です。"
      }
    },
    {
      "@type": "Question",
      "name": "家族やチームで共有して使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Open WebUIを動かしているPCのIPアドレス（例: 192.168.1.10:3000）に同じWi-Fi内の別のデバイスからアクセスすれば、家族や同僚もブラウザ経由で利用できます。"
      }
    },
    {
      "@type": "Question",
      "name": "データの学習（ファインチューニング）はできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "この記事の構成だけでは「学習」はできません。しかし、Open WebUIのRAG機能を使えば、追加学習なしでもあなたの持っている知識（PDFやメモ）に基づいた回答をさせることが十分に可能です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GB搭載で、中規模モデルまで快適に動かせるローカルLLMの最適解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

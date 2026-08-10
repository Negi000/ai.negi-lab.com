---
title: "OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法"
date: 2026-08-10T00:00:00+09:00
slug: "ollama-open-webui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-10-ollama-open-webui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "RAG 自作"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、手元のPCだけで動作する「自分専用のChatGPT風チャット画面」を構築します
- ネット環境がなくても、PDFやテキストファイルを読み込ませて回答させる（RAG）環境が完成します
- 必要なもの：Windows（WSL2導入済み）またはMac、およびミドルエンド以上のGPU（またはApple Silicon）

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

ローカルLLMを動かす上で、CPUよりも重要なのがVRAM（ビデオメモリ）の容量です。
結論から言うと、VRAMが8GBあれば「Llama 3 8B」などの軽量モデルが快適に動きますが、12GB以上あると実用的な「Command R」クラスが視野に入ります。
私はRTX 4090を2枚挿していますが、これは大規模なモデルを高速に回すためであり、初心者が最初に目指すべきはRTX 3060（12GBモデル）か、メモリ16GB以上のMacBook（M2/M3）です。

料金面では、API利用料は$0ですが、その分電気代がかかります。
RTX 4090をフル稼働させると1時間で数百ワット消費しますが、推論時のみの消費なので、月額$20のChatGPT Plusを契約し続けるよりは、長期的に見て安上がりになるケースが多いです。
もしこれからPCを買うなら、VRAM 12GB未満のGPUは「後で必ず後悔する」ので避けてください。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段はLM StudioやJanなど他にもありますが、私は「Ollama + Open WebUI」の組み合わせが最強だと考えています。
理由は、バックエンド（推論エンジン）とフロントエンド（UI）が分かれているため、将来的な拡張性が非常に高いからです。
Ollamaはモデルの管理がコマンド一つで済み、APIサーバーとしても機能するため、自作のPythonスクリプトからローカルLLMを呼び出すのが簡単になります。

また、Open WebUIは本家ChatGPTに酷似した操作感に加え、RAG（ドキュメント読み込み）機能が標準で備わっています。
他のツールだとRAGのために別のライブラリを組む必要がありますが、Open WebUIならPDFをドラッグ＆ドロップするだけで準備が完了します。
この「手軽さと拡張性の両立」こそが、私が実務でこの構成を推奨する最大の理由です。

## Step 1: 環境を整える

まずは推論エンジンであるOllamaをインストールします。
Windowsの場合はWSL2上で動かすのが最もパフォーマンスが出ますが、今回は最も手軽なインストーラー版を使います。

```bash
# macOS / Linux の場合は以下のコマンドで一発インストール可能です
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの方は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストール後、ターミナル（PowerShellやターミナル.app）を開き、以下のコマンドを叩いてバージョンが表示されれば成功です。

```bash
ollama --version
```

Ollamaは「モデルをダウンロードして管理するマネージャー」兼「推論サーバー」です。
インストールしただけでは中身（モデル）がないため、この後のステップで脳みそを追加していきます。

⚠️ **落とし穴:**
WindowsでGPUが認識されない場合、NVIDIAのドライバが古い可能性があります。
最新のGame Readyドライバ、あるいはStudioドライバをインストールしているか確認してください。
また、WSL2を使っている場合は、`nvidia-smi`コマンドがWSL内で通ることを確認するのが先決です。

## Step 2: 基本の設定

次に、チャット画面となるOpen WebUIを立ち上げます。
これはDockerを使って動かすのが一番環境を汚さず、アップデートも楽です。
Docker Desktopをインストールした状態で、以下のコマンドを実行してください。

```bash
# Ollamaが同じPCで動いている場合の起動コマンド
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

このコマンドには3つの重要な意味があります。
1. `-p 3000:8080`: ブラウザから`localhost:3000`でアクセスできるようにしています。
2. `--add-host`: コンテナの中から、ホストPCで動いているOllamaを見つけられるようにする魔法の言葉です。
3. `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域（ボリューム）を作っています。これがないと、コンテナを止めるたびにデータが消えます。

コマンド実行後、ブラウザで `http://localhost:3000` を開いてください。
最初にアカウント作成画面が出ますが、これはローカル保存されるだけなので、好きなメールアドレスとパスワードで登録してログインします。

## Step 3: 動かしてみる

ログインできても、まだモデルが選択できないはずです。
画面左下の設定、またはターミナルからモデルをダウンロード（Pull）する必要があります。
まずは、日本語能力と軽量さのバランスが良い「Llama 3 (8B)」を試してみましょう。

```bash
# ターミナルで実行
ollama pull llama3
```

ダウンロードが終わったら、Open WebUIの画面上部にある「モデルを選択」から `llama3:latest` を選びます。
適当に「こんにちは、自己紹介して」と送ってみてください。

### 期待される出力

```
こんにちは！私はMetaによってトレーニングされた大型言語モデルのLlama 3です。
あなたの質問に答えたり、文章を作成したり、プログラミングのサポートをしたりすることができます。
今日は何かお手伝いできることはありますか？
```

もし回答が英語になったり、日本語が怪しい場合は、システムプロンプトで「あなたは優秀な日本語アシスタントです」と設定してください。
Llama 3は英語ベースのモデルですが、このサイズ感（約5GB）でこれだけ動くのは驚異的です。

## Step 4: 実用レベルにする

「仕事で使えるか」を基準にするなら、単なるチャットでは不十分です。
Open WebUIの真骨頂である「RAG機能」を使い、手元のマニュアルや仕様書に基づいた回答をさせてみましょう。

1. チャット入力欄の左側にある「＋」アイコン、または「#」を入力します。
2. 「ドキュメントをアップロード」を選択し、手持ちのPDF（例えばツールの説明書や自社の規約など）を投げ入れます。
3. アップロード後、そのファイルを指定した状態で「この資料の内容を要約して」と入力します。

Open WebUIは裏側でドキュメントを「ベクトル化」し、質問に関連する箇所を抽出してLLMに渡してくれます。
これにより、LLMが学習していない最新情報や、社外秘の情報についても正確に答えられるようになります。

さらに、業務で特定の役割（コードレビュアー、翻訳者など）を固定したい場合は、「モデルファイル（Modelfile）」を作成します。
Open WebUIの「ワークスペース」メニューから、特定のシステムプロンプトを組み込んだカスタムモデルを作成し、チームや自分専用の「専門家」として保存しておくことができます。
これが、私が「仕事で使える」と判断したポイントです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 回答が異常に遅い（1文字/秒以下） | GPUではなくCPUで推論している | Ollamaの設定を確認し、VRAM容量が足りているかチェック。モデルサイズを小さくする。 |
| Docker起動時にポート重複 | すでに3000番ポートを他のアプリが使っている | `-p 3001:8080` のように左側の数字を変更する。 |
| Ollamaに接続できない | コンテナからホストへの通信が遮断されている | `--add-host` オプションを確認。Windows FirewallでOllamaの通信を許可する。 |

## 次のステップ

環境が整ったら、次は「どのモデルを使い分けるか」の選定に入りましょう。
日本語の長文を読ませるなら「Command R (35B)」が非常に優秀ですが、これにはVRAMが24GB（RTX 3090/4090）必要です。
もしVRAMが足りない場合は、量子化（Quantization）という技術を使ってモデルを軽量化したバージョン（Q4_K_Mなど）を探してみてください。

また、このOllama環境は `http://localhost:11434` でAPIとしても待ち受けています。
Pythonの `openai` ライブラリの `base_url` をここに書き換えるだけで、既存のスクリプトを「無料・無制限・プライベート」なローカルLLM仕様に改造できます。
まずは身近な作業（ログ解析、議事録の整形など）を、API経由で自動化することに挑戦してみてください。

## よくある質問

### Q1: ネット接続がなくても本当に動きますか？

はい、モデルのダウンロード時以外はインターネット不要です。飛行機の中でも、電波の届かないサーバー室でも、PCの電源さえあればChatGPTと同等の機能を利用できます。これがローカルLLMの最大の強みです。

### Q2: 4GBのVRAMしかないノートPCでも動きますか？

動きますが、モデルを選びます。Microsoftが公開している「Phi-3 Mini」などの超軽量モデルなら4GBでも高速に動作します。ただし、回答の賢さはLlama 3などに比べると一段落ちる点は覚悟してください。

### Q3: データのプライバシーは完全に守られますか？

もちろんです。クラウドへデータが送信されることは一切ありません。Open WebUIでアップロードしたドキュメントも、すべてあなたのPC内のDockerボリュームに保存されます。機密情報を扱う業務には最適の選択肢です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法](/posts/2026-08-01-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIで自分専用のローカルAI環境を構築する方法](/posts/2026-07-25-ollama-open-webui-local-llm-setup-guide/)
- [OllamaとOpen WebUIを組み合わせて自分専用のローカルChatGPT環境を構築する方法](/posts/2026-07-08-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続がなくても本当に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、モデルのダウンロード時以外はインターネット不要です。飛行機の中でも、電波の届かないサーバー室でも、PCの電源さえあればChatGPTと同等の機能を利用できます。これがローカルLLMの最大の強みです。"
      }
    },
    {
      "@type": "Question",
      "name": "4GBのVRAMしかないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、モデルを選びます。Microsoftが公開している「Phi-3 Mini」などの超軽量モデルなら4GBでも高速に動作します。ただし、回答の賢さはLlama 3などに比べると一段落ちる点は覚悟してください。"
      }
    },
    {
      "@type": "Question",
      "name": "データのプライバシーは完全に守られますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。クラウドへデータが送信されることは一切ありません。Open WebUIでアップロードしたドキュメントも、すべてあなたのPC内のDockerボリュームに保存されます。機密情報を扱う業務には最適の選択肢です。 ---"
      }
    }
  ]
}
</script>

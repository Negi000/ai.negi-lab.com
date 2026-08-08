---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-08-08T00:00:00+09:00
slug: "ollama-openwebui-local-llm-guide"
cover:
  image: "/images/posts/2026-08-08-ollama-openwebui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama"
  - "Open WebUI"
  - "ローカルLLM"
  - "環境構築"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- WebブラウザからChatGPT感覚で操作でき、かつデータが外部に一切漏れないローカルLLM環境を構築します。
- 前提知識：ターミナル（コマンドプロンプト）でのコピペ操作、Dockerの基本的な概念への抵抗がないこと。
- 必要なもの：NVIDIA製GPU搭載PC（推奨）またはApple Silicon搭載Mac、インターネット環境。

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

ローカルLLMを「仕事で使える」レベルで動かすには、推論速度が重要です。
結論から言うと、VRAM（ビデオメモリ）が12GB以上のNVIDIA GPU、もしくはメモリ24GB以上のMacを用意してください。
RTX 3060（12GB版）なら5万円台で手に入り、Llama 3 8Bクラスをサクサク動かせます。

一方で、メモリ8GBのMacBook Airなどでも動作自体は可能ですが、1秒間に3〜5文字程度しか生成されず、実務ではストレスが溜まります。
もしハードウェアをこれから揃えるなら、私は「RTX 4060 Ti 16GB版」を強く勧めます。
約7万円という価格で、現行の主要な軽量モデルをほぼVRAM内に収めて高速に動かせるからです。
クラウドAPIを使わないため、一度機材を揃えてしまえば電気代以外のランニングコストは0円になります。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやGPT4Allなど他にもあります。
しかし、実務での拡張性と運用効率を考えるなら「Ollama + Open WebUI」の組み合わせがベストです。
Ollamaはモデル管理が圧倒的に楽で、バックエンドとしてAPIを公開できるため、自作スクリプトとの連携が容易です。

Open WebUIは、見た目がChatGPTに酷似しているだけでなく、RAG（ドキュメント読み込み）機能やプロンプトの共有機能が標準装備されています。
他のツールは「動かして終わり」になりがちですが、この構成ならチーム内で共有したり、自分専用のナレッジベースを構築したりといった「実戦投入」が可能です。

## Step 1: 環境を整える

まずはLLMのエンジンとなる「Ollama」をインストールします。

```bash
# macOS / Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストール後、ターミナルで以下のコマンドを叩き、モデルをダウンロードします。

```bash
# Llama 3 8Bモデルをダウンロードして起動
ollama run llama3
```

このコマンドは、モデルファイルのダウンロード（約5GB）と推論エンジンの起動を同時に行います。
無事に「>>>」という入力待ち画面になれば、エンジン側の準備は完了です。

落とし穴：
Windowsユーザーで、WSL2上でDockerを動かしている場合、GPUのパススルー設定が漏れているとCPU推論になり、極端に遅くなります。
`nvidia-smi` コマンドでGPUが認識されているか必ず確認してください。

## Step 2: 基本の設定

次に、GUI（画面）となる「Open WebUI」をDockerで立ち上げます。
なぜDockerを使うかというと、Pythonの依存関係で環境を汚さず、アップデートがコマンド一つで完結するからです。

```bash
# GPUを利用する場合（NVIDIA GPU搭載機）
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:cuda

# MacやCPUのみで動かす場合
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

ここで重要なのが `--add-host=host.docker.internal:host-gateway` フラグです。
これにより、Dockerコンテナ内のOpen WebUIが、ホストPC上で動いているOllamaのAPIを認識できるようになります。
これを忘れると「Ollamaに接続できません」というエラーで1時間は悩むことになります。

設定ファイルの永続化のために `-v open-webui:/app/backend/data` を指定し、過去のチャット履歴が消えないようにしています。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスします。
最初にアカウント作成画面が出ますが、これはローカル内に保存される管理用アカウントなので、適当なメールアドレスとパスワードで登録してログインしてください。

画面上部のモデル選択メニューから「llama3:latest」を選びます。
試しに「ローカルLLMを導入するメリットを3つ教えて」と入力してみましょう。

期待される出力：
```text
1. プライバシーとセキュリティ：データが外部サーバーに送信されない。
2. コスト削減：API利用料がかからず、無制限に試行錯誤できる。
3. オフライン動作：インターネット環境がなくても利用可能。
```

もし回答が返ってこない場合は、OllamaのAPI（デフォルト11434ポート）がファイアウォールでブロックされていないか、Dockerの設定でホストIPが正しく指定されているかを確認してください。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。
ローカルLLMの真価は、特定のドキュメントを読み込ませる「RAG」と、プログラムからの自動呼び出しにあります。

まず、Open WebUIの画面左下にある「Documents」から、社内マニュアルや過去のプロジェクト資料（PDFやテキスト）をアップロードしてください。
その後、チャット欄で `#` を入力すると、アップロードした資料を引用して回答させることが可能になります。
これにより、「自社専用のAIアシスタント」が爆速で完成します。

さらに、Pythonからこのローカル環境を叩くスクリプトを用意することで、大量のテキスト分類やデータ整形を自動化できます。

```python
import requests
import json

# OllamaのAPIエンドポイント
URL = "http://localhost:11434/api/generate"

def ask_local_llm(prompt):
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(URL, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 大量のデータをバッチ処理する例
data_list = ["テキスト1", "テキスト2", "テキスト3"]
for item in data_list:
    result = ask_local_llm(f"以下の内容を要約して: {item}")
    print(f"結果: {result}")
```

このスクリプトを使えば、機密性の高い顧客アンケートの解析なども、一切の漏洩リスクなく、かつ無料で処理し続けることができます。
私はこの方法で、1日1万件以上のログ解析を回していますが、API料金を気にせず試行錯誤できるのは圧倒的な強みです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection refused | Ollamaが起動していない | `ollama serve` を実行するか、アプリを再起動 |
| 動作が異常に重い | GPUではなくCPUで動いている | Docker起動時の `--gpus all` オプションを確認 |
| モデルが見つからない | pullされていない | `ollama pull llama3` を実行 |
| WebUIにログインできない | DBの不整合 | Dockerボリュームを削除して再作成（履歴は消える） |

## 次のステップ

環境が整ったら、次は「モデルの使い分け」を試してください。
日本語の精度を求めるなら「Llama-3-Elyza」や「Gemma-2-9b」が非常に優秀です。
Ollamaなら `ollama run gemma2` と打つだけで新しいモデルを試せます。

また、Open WebUIの「Functions」機能を使えば、AIに特定のツール（計算機やWeb検索など）を使わせる「Agent」の構築も可能です。
ローカルLLMは、もはや「お遊び」ではなく、業務システムの一部として組み込めるフェーズに来ています。
まずは、毎日書いている日報のドラフト作成や、コードのデバッグなど、小さなタスクから「自分の相棒」として教育してみてください。

## よくある質問

### Q1: 会社で使う場合、セキュリティ上の懸念はありますか？

全くありません。今回構築した環境は、PC内部（または社内LAN）で完結しており、外部サーバーにプロンプトが送信されることはありません。Dockerの通信さえ絞れば、完全にオフラインでの運用も可能です。

### Q2: 4bit量子化などの難しい設定は不要ですか？

Ollamaがデフォルトで4bit量子化版をダウンロードしてくれるため、意識する必要はありません。VRAM消費を抑えつつ、精度を維持した状態で即座に利用できるよう最適化されています。

### Q3: モデルをカスタマイズ（微調整）することはできますか？

Modelfileという設定ファイルを作成することで、システムプロンプトやパラメータ（Temperatureなど）を固定した「自分専用モデル」を定義できます。Open WebUI上でも「Model Files」から簡単に作成・保存が可能です。

---

## あわせて読みたい

- [OllamaとOpen WebUIを連携させ、完全にオフラインで動作する「プライベートChatGPT環境」を構築します。](/posts/2026-07-20-ollama-open-webui-local-llm-tutorial/)
- [ModelHubレビュー MacメニューバーからローカルLLMを即起動する](/posts/2026-05-25-modelhub-mac-local-llm-review/)
- [ローカルLLM環境の選び方比較｜RTX 4060 Tiから4090、Macまで失敗しないVRAM選び](/posts/2026-07-18-local-llm-vram-gpu-comparison-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "会社で使う場合、セキュリティ上の懸念はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全くありません。今回構築した環境は、PC内部（または社内LAN）で完結しており、外部サーバーにプロンプトが送信されることはありません。Dockerの通信さえ絞れば、完全にオフラインでの運用も可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化などの難しい設定は不要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaがデフォルトで4bit量子化版をダウンロードしてくれるため、意識する必要はありません。VRAM消費を抑えつつ、精度を維持した状態で即座に利用できるよう最適化されています。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルをカスタマイズ（微調整）することはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Modelfileという設定ファイルを作成することで、システムプロンプトやパラメータ（Temperatureなど）を固定した「自分専用モデル」を定義できます。Open WebUI上でも「Model Files」から簡単に作成・保存が可能です。 ---"
      }
    }
  ]
}
</script>

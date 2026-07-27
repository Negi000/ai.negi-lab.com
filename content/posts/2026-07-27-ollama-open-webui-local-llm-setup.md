---
title: "OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法"
date: 2026-07-27T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup"
cover:
  image: "/images/posts/2026-07-27-ollama-open-webui-local-llm-setup.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker GPU連携"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- プライバシーを完全に保護した状態で、ChatGPTと同等の操作感を持つAIチャット環境をPC内に構築します。
- Ollamaをバックエンドに、Open WebUIをフロントエンドに使用し、モデルの切り替えやドキュメント読み込み（RAG）が自由自在なシステムを完成させます。
- 前提知識として、基本的なコマンド操作（ターミナルやPowerShell）への抵抗がないことを想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。8Bモデルが余裕で動く</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の容量です。
結論から言うと、実用レベル（Llama 3.1 8Bクラスを快適に動かす）には最低でも8GB、理想を言えば12GB以上のVRAMを搭載したGPUが必要です。
私が普段メインで使っているRTX 4090 24GBであれば、大抵の量子化モデルは爆速で動きますが、これから機材を揃えるならRTX 4060 Tiの16GB版が最もコストパフォーマンスに優れています。

Macユーザーの場合、メモリ（ユニファイドメモリ）がVRAMを兼ねるため、最低16GB、できれば24GB以上のモデルを選んでください。
8GBモデルのMacBook Airでも動くには動きますが、モデルの読み込みだけでメモリが枯渇し、スワップが発生してレスポンスが数秒単位で遅れるため、仕事で使うには厳しいのが現実です。
クラウドAPIと違い、月額料金は電気代以外かかりませんが、初期投資としてのハードウェア選びがそのまま体験の質に直結します。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、他にもLM StudioやJanなどいくつか存在します。
しかし、私が「仕事で使うならこれ一択」と考えているのが、OllamaとOpen WebUIの組み合わせです。
理由は、役割分担が明確で拡張性が非常に高いからです。

Ollamaはモデルの管理と実行に特化した軽量なバックエンドであり、APIサーバーとしても機能します。
一方のOpen WebUIは、ChatGPTのUIをほぼ踏襲しており、マルチユーザー対応やRAG（外部ファイル参照）、Web検索機能など、実務に必要な機能が最初から全て揃っています。
単一のアプリで完結するツールは手軽ですが、将来的に独自のスクリプトからAIを呼び出したり、社内サーバーとして公開したりすることを考えると、この「エンジンとUIを分ける構成」が最も合理的です。

## Step 1: 環境を整える

まずはLLMの実行エンジンであるOllamaをインストールします。

```bash
# Mac/Linuxの場合（公式スクリプトを利用）
curl -fsSL https://ollama.com/install.sh | sh
```

Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードして実行するだけです。
インストールが終わったら、ターミナル（またはPowerShell）を開き、以下のコマンドを叩いてください。

```bash
ollama --version
```

バージョンが表示されれば成功です。
Ollamaはバックグラウンドで常駐し、モデルのダウンロードから実行までを肩代わりしてくれます。
この時点ではまだ「脳」が入っていない状態なので、試しに軽量なモデルをダウンロードしてみましょう。

```bash
ollama pull llama3.1:8b
```

ここで`8b`（80億パラメータ）のモデルを選ぶのは、現時点で性能と速度のバランスが最も優れているからです。
日本語の対話性能を重視するなら、後に紹介するQwenやGemmaも検討しますが、まずは標準的なLlama 3.1で動作確認を行うのが定石です。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使用している場合、GPUが正しく認識されないことがあります。
基本的にはWindowsネイティブ版のOllamaをインストールするのが最もトラブルが少なく、GPUのアクセラレーションも効きやすいです。
「動いているけれど生成が異常に遅い」と感じたら、タスクマネージャーのGPU専用メモリ使用量を確認してください。ここが増えていなければ、CPUで計算してしまっています。

## Step 2: DockerでOpen WebUIを立ち上げる

次に、ブラウザから操作するためのGUI「Open WebUI」を導入します。
これを直接インストールするのは環境を汚す原因になるため、Dockerを使用してコンテナとして動かすのがプロのやり方です。

まず、Docker Desktopがインストールされていることを確認してください。
その上で、以下のコマンドを実行します。

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

このコマンドの各オプションには重要な意味があります。
`-p 3000:8080` は、ブラウザの `localhost:3000` でアクセスできるようにする設定です。
`--add-host=host.docker.internal:host-gateway` は、コンテナ内からホストPCで動いているOllama（Step 1で入れたもの）と通信するために必須の設定です。
これを忘れると、UIは立ち上がるのに「モデルが見つかりません」というエラーで一生悩むことになります。

⚠️ **落とし穴:**
ポート3000が他のアプリ（開発ツールなど）で既に使用されている場合、起動に失敗します。
その場合は `-p 3001:8080` のように、左側の数字を未使用のポートに変更してください。
また、Dockerのディスク割り当てが少なすぎると、後にファイルをアップロードするRAG機能でエラーが出るため、余裕を持って20GB以上割り当てておくことをおすすめします。

## Step 3: 動かしてみる

Dockerコマンドの実行完了後、数分待ってからブラウザで `http://localhost:3000` にアクセスしてください。
最初の画面でアカウント作成（メールアドレスとパスワード）を求められます。
「ローカルなのになぜアカウント？」と思うかもしれませんが、これはOpen WebUIがマルチユーザー対応の設計になっているためです。
データは全て自分のPC内に保存され、外部に送信されることはないので安心してください。

ログイン後、画面上部の「モデルを選択」から、先ほどpullした `llama3.1:8b` を選択します。
適当な日本語を入力してみましょう。

```text
USER: こんにちは。自己紹介をしてください。
ASSISTANT: こんにちは！私はLlama 3.1ベースのAIアシスタントです。あなたのPC上で動作しており、プライバシーを重視した対話が可能です。何かお手伝いできることはありますか？
```

### 期待される出力
レスポンス速度に注目してください。
RTX 3060以上の環境であれば、1秒間に50トークン（文字）以上の速度で文字が流れてくるはずです。
もし「1文字ずつゆっくり出てくる」状態であれば、GPUが活用されておらず、CPUで推論を行っている可能性があります。
その場合は、Ollamaのログを確認し、GPUドライバが最新かどうか、CUDAが正しく認識されているかを再確認する必要があります。

## Step 4: 実用レベルにする

単なるチャットで終わらせては、わざわざローカル環境を構築した意味がありません。
実務で使えるレベルに引き上げるための2つの設定を紹介します。

### 1. 日本語特化モデルの導入
Llama 3.1も優秀ですが、日本語の微細なニュアンスや敬語の使い方は、Alibabaの「Qwen 2.5」やGoogleの「Gemma 2」の方が自然な場合が多いです。
ターミナルから以下のコマンドで追加モデルを取得できます。

```bash
ollama pull qwen2.5:7b
ollama pull gemma2:9b
```

Open WebUI上でこれらのモデルを即座に切り替えて、回答精度を比較してみてください。
私の経験上、コード生成ならQwen、論理的な思考ならGemma、総合力ならLlamaという使い分けが安定します。

### 2. RAG（ドキュメント解析）機能の活用
Open WebUIの真骨頂は、PDFやテキストファイルをチャット欄にドラッグ＆ドロップするだけで、その内容に基づいた回答ができる点です。
設定（Settings）→ RAG（Documents）から、使用する埋め込みモデル（Embedding Model）を設定できます。
デフォルトでも動きますが、より日本語精度を高めたい場合は、埋め込みモデルもローカルで動かすよう設定変更が可能です。
機密性の高い社内規定や、未公開のプロジェクト資料を読み込ませても、データがOpenAIのサーバーに飛ぶことは一切ありません。

```python
# OllamaのAPIをPythonから叩く例
# 実務ではOpen WebUIだけでなく、このようなスクリプトからLLMを呼び出すことも多い
import requests
import json

def generate_response(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    return response.json()['response']

# 実行
# print(generate_response("ローカルLLMを導入するメリットを3つ挙げて"))
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| モデル一覧に何も表示されない | DockerとOllamaの通信失敗 | Docker起動コマンドに `add-host` が含まれているか確認 |
| 回答が英語ばかりになる | システムプロンプト未設定 | Open WebUIのモデル設定で「常に日本語で回答して」と追記 |
| 動作が異常に重い | VRAM容量不足 | より小さいモデル（`qwen2.5:1.5b`など）を試す |
| 接続を拒否されました | Ollamaが起動していない | ターミナルで `ollama serve` を実行するかアプリを起動する |

## 次のステップ

無事に環境が動いたら、次は「Modelfile」の作成に挑戦してみてください。
これは、既存のモデルに自分専用の性格や知識（システムプロンプト）を焼き付けた「カスタムモデル」を作る機能です。
例えば、「SIerの商習慣に詳しいエンジニア」や「Pythonのコードレビューに特化したシニア層」といった役割を固定することで、プロンプトを毎回書く手間が省けます。

また、API経由でCursorなどのコードエディタと連携させるのもおすすめです。
ローカルLLMをバックエンドに据えることで、コードが外部に漏れるリスクをゼロにしつつ、AIによるコーディング支援をフル活用できるようになります。
ここまで来れば、あなたはもう「AIを使わされている人」ではなく「AIを飼い慣らしている人」です。

## よくある質問

### Q1: グラフィックボードがないビジネスノートPCでも動きますか？

動きますが、快適ではありません。CPUのみでの推論になるため、回答速度は1秒間に1〜2文字程度になります。短文の要約程度なら我慢できるかもしれませんが、複雑な相談には不向きです。

### Q2: 複数のモデルを同時に起動して比較することはできますか？

可能です。Ollamaはリクエストに応じてモデルをメモリにロードします。ただし、複数のモデルを同時にメモリに載せるには、その分だけ膨大なVRAMが必要になります。24GBあれば8Bモデルを3つ同時に動かすことも可能です。

### Q3: 構築した環境をスマホや他のPCから使うことはできますか？

できます。Open WebUIを動かしているPCのローカルIPアドレス（192.168.x.xなど）に対して、同じWi-Fi内のデバイスからアクセスすれば、スマホのブラウザで自分専用AIを持ち歩けます。

---

## あわせて読みたい

- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラフィックボードがないビジネスノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、快適ではありません。CPUのみでの推論になるため、回答速度は1秒間に1〜2文字程度になります。短文の要約程度なら我慢できるかもしれませんが、複雑な相談には不向きです。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に起動して比較することはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollamaはリクエストに応じてモデルをメモリにロードします。ただし、複数のモデルを同時にメモリに載せるには、その分だけ膨大なVRAMが必要になります。24GBあれば8Bモデルを3つ同時に動かすことも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "構築した環境をスマホや他のPCから使うことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "できます。Open WebUIを動かしているPCのローカルIPアドレス（192.168.x.xなど）に対して、同じWi-Fi内のデバイスからアクセスすれば、スマホのブラウザで自分専用AIを持ち歩けます。 ---"
      }
    }
  ]
}
</script>

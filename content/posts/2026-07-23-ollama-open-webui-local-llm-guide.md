---
title: "OllamaとOpen WebUIで自分専用の機密保持ローカルLLM環境を作る方法"
date: 2026-07-23T00:00:00+09:00
slug: "ollama-open-webui-local-llm-guide"
cover:
  image: "/images/posts/2026-07-23-ollama-open-webui-local-llm-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM RAG"
  - "GPU VRAM 目安"
---
**所要時間:** 約25分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、手元のPCだけで動作するChatGPTライクなチャットUI環境
- 社外秘ドキュメントや未公開コードを読み込ませても情報漏洩の心配がないRAG（検索拡張生成）環境
- 複数のAIモデル（Llama 3.1, Gemma 2, Mistral等）をボタン一つで切り替えて比較できる検証基盤

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8Bモデルが余裕で動き、70Bの量子化モデルにも手が届く入門の決定版</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも圧倒的に重要なのが「GPUのVRAM（ビデオメモリ）」です。
結論から言うと、VRAM 8GBが最低ライン、快適に動かすなら12GB以上、実務でパラメーター数の大きいモデルを扱うなら16GB以上を推奨します。
私はRTX 4090の24GBを2枚挿していますが、これは特殊な例だとしても、中古のRTX 3060 (12GB) を4万円前後で調達するのが、最もコストパフォーマンスの良い入門方法です。

Macユーザーの場合、メモリ（ユニファイドメモリ）が16GB以上あれば、8B（80億パラメーター）クラスのモデルはサクサク動きます。
8GBモデルのMacだと、OSやブラウザがメモリを消費するため、LLMを動かすとスワップが発生し、レスポンスが10秒以上遅れることが多々あります。
料金面では、一度ハードウェアを揃えてしまえば、電気代以外は完全に0円です。
ChatGPT Plusに月額$20（約3,000円）払うのを1年やめれば、ミドルクラスのGPUが買える計算になります。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は「LM Studio」や「AnythingLLM」など他にもありますが、私は「Ollama + Open WebUI」の組み合わせがベストだと確信しています。
最大の理由は、バックエンド（推論エンジン）とフロントエンド（UI）が分離されているため、拡張性が非常に高いからです。
OllamaはAPIサーバーとして振る舞うため、Python自作スクリプトから呼び出すのも簡単ですし、Open WebUIはDockerで動くため、将来的にサーバーを別立てにする際も移行がスムーズです。
また、Open WebUIはRAG機能が標準実装されており、PDFやテキストファイルをドラッグ＆ドロップするだけで、その内容に基づいた回答を得られる点が、他のツールより実務向きです。

## Step 1: 環境を整える

まずは推論エンジンとなるOllamaをインストールします。
これは、大規模言語モデルをバックグラウンドで効率よく動かすための「器」のような存在です。

```bash
# macOS / Linux の場合（公式サイトからインストーラーも落とせます）
curl -fsSL https://ollama.com/install.sh | sh

# Windows の場合
# 公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
```

インストールが終わったら、ターミナル（またはコマンドプロンプト）で以下のコマンドを叩き、モデルをダウンロードします。
今回は日本語能力が高い「Llama 3.1 8B」を使用します。

```bash
ollama run llama3.1
```

ダウンロードが完了し「>>>」というプロンプトが出れば成功です。
何か適当に「こんにちは」と打ってみてください。
これだけでも動きますが、CUI（黒い画面）では長文のコピペやファイル読み込みが不便なため、次のステップでUIを構築します。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使用している場合、GPUドライバが最新でないと、OllamaがGPUを認識せずCPUで動いてしまうことがあります。
「レスポンスが1文字ずつ、数秒おきにしか出ない」という場合は、タスクマネージャーの「パフォーマンス」タブで、GPUの専用メモリが消費されているか確認してください。
CPU使用率が100%に張り付いている場合は、GPUが使われていません。

## Step 2: 基本の設定

次に、Dockerを使ってOpen WebUIを立ち上げます。
なぜ直接インストールせずDockerを使うかというと、Open WebUIが依存するPythonライブラリやライブラリ同士の衝突で、ローカル環境を汚したくないからです。

まず、Docker Desktop（またはOrbStack等）が起動していることを確認してください。
以下のコマンドを1行で実行します（WindowsはPowerShell推奨）。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

各オプションの意味は以下の通りです。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerコンテナの中から、ホストPCで動いているOllama（Step 1で入れたもの）を見つけられるようにする魔法の言葉です。これがないとUIとエンジンが通信できません。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する領域を確保しています。これがないと、Dockerを再起動したときに履歴が消えます。

コマンドを実行して数分待つ（イメージのダウンロードが行われる）と、準備完了です。

## Step 3: 動かしてみる

ブラウザを開き、`http://localhost:3000` にアクセスしてください。
最初にアカウント作成画面が出ますが、これはローカルに保存されるだけなので、好きなメールアドレスとパスワードを入れてください（外部には送信されません）。

ログイン後、画面上部の「モデルを選択」から `llama3.1:latest` を選びます。

### 期待される出力

```text
User: 日本の首都は？
Assistant: 日本の首都は東京です。
```

ここで「モデルが表示されない」場合は、画面左下のユーザー名をクリック → 「設定」 → 「外部接続」を確認してください。
OllamaのURLが `http://host.docker.internal:11434` になっている必要があります。
もし自作PCでGPUを積んでいるなら、この時点でレスポンスは「爆速」のはずです。
私の環境（RTX 4090）では、秒間100トークン以上、つまり一瞬で壁のようなテキストが表示されます。

## Step 4: 実用レベルにする

ここからが「仕事で使えるか」の分かれ道です。
Open WebUIの真骨頂である「ドキュメント読み込み（RAG）」と「システムプロンプトの固定」を設定します。

### ドキュメント読み込みの設定
1. チャット画面の「＋」ボタン、あるいは「#」を打つことで、ローカルのPDFファイルをアップロードできます。
2. 例えば、会社の「就業規則」や「自社製品の仕様書」をアップロードしてください。
3. その後、「この仕様書の3ページ目にある、APIの認証手順を要約して」と指示します。

これにより、LLMが学習していない最新の情報や、社内のプライベートな情報をベースにした回答が可能になります。
外部API（OpenAI等）では怖くて投げられなかった情報を、自分のPC内で完結して処理できるメリットは計り知れません。

### 日本語特化の設定
Llama 3.1は日本語も得意ですが、たまに英語で返してくることがあります。
これを防ぐために「モデルファイル」をカスタムします。
1. 「ワークスペース」 → 「モデル」 → 「モデルを作成」をクリック。
2. ベースモデルに `llama3.1:latest` を選択。
3. システムプロンプト欄に以下を記述します。

```text
あなたは優秀な日本人エンジニアの助手です。
回答は常に簡潔な日本語で行ってください。
技術的な解説については、具体的なコード例を必ず含めてください。
```

4. 名前を「My-Llama-JP」として保存。
以降はこのカスタムモデルを使うことで、常に安定した出力が得られるようになります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Error` | DockerとOllamaが通信できていない | 起動コマンドに `--add-host` が入っているか再確認 |
| 回答が極端に遅い | GPUが使われずCPU推論になっている | GPUドライバを更新し、DockerのGPU設定を有効化 |
| 動作が不安定、途切れる | メモリ（VRAM）不足 | 8Bより小さいモデル（Gemma-2-2b等）を試す |

## 次のステップ

ここまでできれば、あなたのPCは「プライバシーが完全に守られた知能」を手に入れたことになります。
次に挑戦すべきは、以下の3点です。

1. **モデルの使い分け**: コーディングには `DeepSeek-Coder`、論理的思考には `Gemma 2`、高速レスポンスには `Llama 3.1` と、用途に合わせてモデルを入れ替えてみてください。
2. **API経由での利用**: Pythonから `requests` ライブラリを使い、OllamaのAPI（ポート11434）を叩いてみましょう。社内ツールにAIを組み込む第一歩になります。
3. **ハードウェアの増強**: もし1分間に1回以上「遅い」と感じるなら、それはGPUへの投資時です。VRAM 16GB以上の環境を作れば、量子化された70B（700億パラメーター）クラスのモデルすら、個人環境で動かせるようになります。

ローカルLLMの世界は、一度足を踏み入れると「自分の手元に巨大な知能がある」という全能感に包まれます。
それは、かつて自作PCを初めて組み上げた時の感覚に近い、純粋なワクワク感です。

## よくある質問

### Q1: ネット接続は必要ですか？

モデルのダウンロード時と、Open WebUIのイメージ取得時のみ必要です。一度構築してしまえば、PCを機内モードにしても完全にオフラインで動作します。

### Q2: OpenAIのAPIキーは必要ですか？

一切不要です。これがローカルLLM環境の最大のメリットです。月額料金を気にせず、1日何万回でもプロンプトを投げることができます。

### Q3: 会社のPCに入れても大丈夫ですか？

技術的には可能ですが、Dockerのインストール権限が必要です。また、GPUを積んでいないオフィス用ノートPCだと、動作が非常に重いため、実用には向かないかもしれません。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法](/posts/2026-06-16-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIでプライベートなローカルLLM環境を構築する方法](/posts/2026-07-05-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続は必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルのダウンロード時と、Open WebUIのイメージ取得時のみ必要です。一度構築してしまえば、PCを機内モードにしても完全にオフラインで動作します。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIキーは必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "一切不要です。これがローカルLLM環境の最大のメリットです。月額料金を気にせず、1日何万回でもプロンプトを投げることができます。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のPCに入れても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的には可能ですが、Dockerのインストール権限が必要です。また、GPUを積んでいないオフィス用ノートPCだと、動作が非常に重いため、実用には向かないかもしれません。 ---"
      }
    }
  ]
}
</script>

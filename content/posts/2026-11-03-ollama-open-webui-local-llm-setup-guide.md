---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を構築する方法"
date: 2026-11-03T00:00:00+09:00
slug: "ollama-open-webui-local-llm-setup-guide"
cover:
  image: "/images/posts/2026-11-03-ollama-open-webui-local-llm-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 入門"
  - "ローカルLLM 構築"
  - "Llama 3 実行"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

完全オフライン・プライバシー重視の「自分専用ChatGPT」を構築します。
具体的には、バックエンドにLLM実行エンジンの「Ollama」、フロントエンドにChatGPTライクな操作感を持つ「Open WebUI」を組み合わせ、ブラウザから快適に最新AIと対話できる環境を作ります。
Pythonの知識がなくても、コマンドのコピペだけで実用レベルのAI環境が手に入ります。

### 前提知識
- 基本的なコマンド操作（PowerShellまたはターミナルでのコピペ）ができる
- Dockerという単語を聞いたことがある（手順通りに進めれば未経験でもOK）

### 必要なもの
- Windows 11、macOS、またはLinux
- NVIDIA製GPU（VRAM 8GB以上推奨） または Apple Silicon搭載Mac（M1以降）
- ストレージの空き容量：30GB以上（モデルを複数入れる場合は多めに確保）

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える速度」で動かすには、CPUではなくGPUの性能がすべてです。
私がRTX 4090を2枚挿ししているのは、大規模なモデル（Llama 3 70Bなど）をレスポンス0.5秒で動かすためですが、入門ならそこまで必要ありません。
最低でもVRAM（ビデオメモリ）が8GBあるNVIDIA製グラフィックボードを用意してください。

VRAMが8GBあれば、現在主流の「Llama 3.1 8B」や「Gemma 2 9B」といったモデルがサクサク動きます。
逆にVRAMが4GB以下だと、計算をCPUに頼ることになり、1文字ずつ数秒待たされる「苦行」になります。
Macユーザーなら、メモリ（ユニファイドメモリ）が16GB以上あれば、十分実用的な速度が出ます。

月額料金は完全に0円です。
APIを使わないため、どれだけ長文を投げても、どれだけ複雑なタスクを依頼しても、電気代以外はかかりません。
企業秘密や個人情報をAIに学習させたくないというニーズにも、この環境が唯一の正解になります。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、LM StudioやJan、AnythingLLMなど他にもあります。
しかし、現時点で「仕事で使う」なら、OllamaとOpen WebUIの組み合わせがベストです。
理由は、Ollamaの圧倒的な「モデル管理の楽さ」と、Open WebUIの「多機能さ」にあります。

Open WebUIは、RAG（ドキュメント読み込み）、Web検索機能、画像生成、ユーザー管理といった、ChatGPT Plusの有料機能に近いものがすべて無料で内包されています。
他のアプリは単なるチャット画面で終わることが多いですが、Open WebUIは「AIプラットフォーム」として完成されています。
バックエンドとフロントエンドを分離しておくことで、将来的に別のサーバーで動かしたり、複数のユーザーで共有したりといった拡張も容易です。

## Step 1: 環境を整える

まずは、LLMを動かすためのエンジンであるOllamaをインストールします。

1. [Ollama公式サイト](https://ollama.com/)からインストーラーをダウンロードし、実行します。
2. インストール完了後、ターミナル（WindowsはPowerShell）を開き、以下のコマンドを入力してください。

```bash
ollama --version
```

これでバージョンが表示されれば成功です。
次に、Open WebUIを動かすためにDocker Desktopをインストールします。

[Docker公式サイト](https://www.docker.com/products/docker-desktop/)からダウンロードしてインストールしてください。
「なぜDockerを使うのか」と思うかもしれませんが、Open WebUIには非常に多くの依存ライブラリが含まれています。
これらを自分のPCに直接インストールすると、Pythonのバージョン競合などで高確率で環境が壊れます。
Dockerという「仮想的な箱」の中で動かすのが、最もトラブルが少なく、かつアンインストールも簡単な方法です。

⚠️ **落とし穴:**
WindowsユーザーでDockerを初めて使う場合、「WSL 2 kernel update is required」というエラーが出ることがあります。
その場合は、画面の指示に従ってMicrosoftのサイトから更新プログラムをダウンロードし、適用してください。これを無視するとDockerが起動しません。

## Step 2: 基本の設定

OllamaとOpen WebUIを連携させるための設定を行います。
一番簡単な方法は、Dockerコマンド一つでOpen WebUIを立ち上げることです。

ターミナルで以下のコマンドを実行してください。

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

### コマンドの解説
- `-d`: バックグラウンドで実行します。
- `-p 3000:8080`: ブラウザから `http://localhost:3000` でアクセスできるようにします。
- `--add-host=host.docker.internal:host-gateway`: Dockerの中から、外側で動いているOllamaを見えるようにするための重要な設定です。
- `-v open-webui:/app/backend/data`: チャット履歴や設定を保存する場所を指定しています。これを書かないと、Dockerを止めるたびに履歴が消えます。

コマンドを実行して数分待つと（約1.5GBのイメージダウンロードがあります）、準備完了です。

## Step 3: 動かしてみる

ブラウザを開き、アドレスバーに `http://localhost:3000` と入力してください。

1. 最初の画面でアカウント作成を求められますが、これは**ローカルに保存されるだけ**です。適当なメールアドレスと名前で登録してください。
2. ログイン後、左上のモデル選択メニューから「llama3.1」などを選択します。
3. まだモデルがない場合は、設定画面（左下の自分の名前→Settings）の「Models」セクションから、`llama3.1` と入力してダウンロードボタンを押します。

試しに何か入力してみましょう。

```text
これからあなたのことを「専属秘書」と呼びます。
今日のタスクを整理して。
```

### 期待される出力

```text
承知いたしました。私はあなたの専属秘書として、タスクの管理やスケジューリングをサポートします。
現在、具体的なタスクリストが入力されていません。お手持ちの予定や今日完了すべき項目を教えていただけますか？
```

レスポンス速度に注目してください。
GPUが正しく認識されていれば、毎秒50〜100トークン（日本語なら一瞬で全文が表示されるレベル）で出力されるはずです。

## Step 4: 実用レベルにする

単にチャットするだけならChatGPTで十分です。
ローカルLLMを実務で使うための「RAG（検索拡張生成）」機能を試してみましょう。

Open WebUIのチャット欄にある「＋」ボタンや、ファイルをドラッグ＆ドロップすることで、PDFやテキストファイルを読み込ませることができます。
例えば、自社の分厚いマニュアル（PDF）をアップロードし、それについて質問してみてください。

```text
# このドキュメントに基づき、XXの手続き方法を3行で要約して
```

この際、Open WebUIは裏側で自動的にファイルをベクトル化し、関連箇所を抽出してLLMに渡します。
これを外部サービスで行うと「データ流出」のリスクが常に付きまといますが、ローカルなら安心です。
私はこの機能を使い、クライアントからの機密性の高い要件定義書を読み込ませて、矛盾点のチェックをさせています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection Refused` | Ollamaが起動していない | タスクトレイにOllamaのアイコンがあるか確認。なければ再起動。 |
| 動作が異常に遅い | GPUではなくCPUで動いている | NVIDIAドライバーを最新にし、Ollamaの設定でGPUが認識されているか確認。 |
| モデルがダウンロードできない | ネットワーク制限 | プロキシ環境下の場合、Dockerの環境変数にプロキシ設定が必要です。 |

## 次のステップ

ここまでできれば、あなたは自分だけの自由なAI環境を手に入れました。
次に挑戦してほしいのは、「システムプロンプト」の作り込みと「モデルの使い分け」です。

1. **システムプロンプト**: Open WebUIの「Workspace」→「Prompts」から、特定の役割を持たせたプロンプトを保存できます。
2. **モデルの使い分け**: コーディングなら `codegemma` や `deepseek-coder`、日本語の自然さなら `command-r` など、用途に合わせて `ollama pull` でモデルを切り替えてみてください。

また、もし「やっぱり少し遅いな」と感じたら、それはVRAM不足です。
その時は、RTX 4060 Ti 16GBモデルのような「メモリが多い」グラボへの換装を検討するタイミングかもしれません。
ローカルLLMの世界は、ハードウェアへの投資がダイレクトに体験価値として返ってくるので、エンジニアとしてこれほど面白い領域はありません。

## よくある質問

### Q1: 社内の他のPCからもこのAIを使わせることはできますか？

可能です。Dockerを動かしているPCのIPアドレスを調べ、他のPCから `http://(サーバーのIP):3000` にアクセスすれば共有できます。Open WebUIにはユーザー管理機能があるため、複数人での利用も想定されています。

### Q2: 4bit量子化（Q4_K_M）という表記をよく見ますが、精度は大丈夫ですか？

実用上、ほとんど問題ありません。FP16（元の精度）とQ4（4ビット圧縮）を比較しても、一般的な対話やコーディングにおける精度差は数%程度です。それよりも、圧縮してVRAMに収めることで得られる「速度メリット」の方が圧倒的に大きいです。

### Q3: ネットが切れていても本当に動きますか？

はい、完全にオフラインで動きます。モデルのダウンロード時だけネットが必要ですが、一度ダウンロードしてしまえば、山奥でも飛行機の中でも、最新のAIと対話することが可能です。これがローカルLLMの最大の醍醐味です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">NVIDIA RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で、中規模モデルを安価かつ高速に動かすための最適解。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPTをローカル構築する方法](/posts/2026-09-12-ollama-open-webui-local-llm-tutorial/)
- [OllamaとOpen WebUIで自分専用のローカルChatGPT環境を構築する方法](/posts/2026-08-15-ollama-open-webui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用の機密情報漏洩ゼロなChatGPT環境を構築する方法](/posts/2026-08-10-ollama-open-webui-local-llm-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "社内の他のPCからもこのAIを使わせることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Dockerを動かしているPCのIPアドレスを調べ、他のPCから http://(サーバーのIP):3000 にアクセスすれば共有できます。Open WebUIにはユーザー管理機能があるため、複数人での利用も想定されています。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化（Q4_K_M）という表記をよく見ますが、精度は大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "実用上、ほとんど問題ありません。FP16（元の精度）とQ4（4ビット圧縮）を比較しても、一般的な対話やコーディングにおける精度差は数%程度です。それよりも、圧縮してVRAMに収めることで得られる「速度メリット」の方が圧倒的に大きいです。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットが切れていても本当に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、完全にオフラインで動きます。モデルのダウンロード時だけネットが必要ですが、一度ダウンロードしてしまえば、山奥でも飛行機の中でも、最新のAIと対話することが可能です。これがローカルLLMの最大の醍醐味です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">NVIDIA RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GB搭載で、中規模モデルを安価かつ高速に動かすための最適解。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

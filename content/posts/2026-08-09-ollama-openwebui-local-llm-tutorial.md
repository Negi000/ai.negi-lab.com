---
title: "OllamaとOpen WebUIで自分専用のローカルLLM環境を作る方法"
date: 2026-08-09T00:00:00+09:00
slug: "ollama-openwebui-local-llm-tutorial"
cover:
  image: "/images/posts/2026-08-09-ollama-openwebui-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Open WebUI 環境構築"
  - "ローカルLLM おすすめ"
  - "Docker LLM 連携"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- PCのローカル環境のみで完結し、プライバシーを完全に保護したChatGPT風の対話システムを構築します
- ブラウザから操作可能なOpen WebUIを、LLM実行エンジンのOllamaと連携させて動かします
- Pythonの基礎知識とDockerの基本的な使い方がわかれば、誰でも再現可能です

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に現実的。安価に大規模モデルを回せる。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPU性能よりも重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、NVIDIA製のGPUを積んだWindows機、またはメモリ16GB以上のApple Silicon Mac（M1/M2/M3）が必須だと考えてください。
Llama 3（8B）などの軽量モデルをサクサク動かすにはVRAM 8GBが最低ラインで、12GBあればストレスが激減し、16GBあれば実務レベルの回答精度を持つモデルも視野に入ります。

もしVRAMが4GB以下なら、推論速度が「1秒間に1文字」以下になり、実用には耐えません。
その場合は無理にローカルで動かそうとせず、API経由でClaude 3.5やGPT-4oを使う方がコストパフォーマンスも生産性も高いです。
また、ディスク容量はモデル1つにつき5GB〜20GB程度消費するため、NVMe SSDの空き容量を30GB以上確保しておくことを推奨します。
電気代は負荷時に200W〜400W程度上がりますが、月額料金がかからないため、毎日3時間以上ハードに使うならAPIより安く済みます。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には「LM Studio」や「GPT4All」など、より簡単なオールインワンアプリも存在します。
しかし、私が実務で「Ollama + Open WebUI」の組み合わせを推す理由は、圧倒的な拡張性とチーム開発への転用しやすさにあります。
Open WebUIは単なるチャット画面ではなく、RAG（ドキュメント読み込み）機能や複数モデルの比較、Web検索連携機能が標準で備わっています。

また、Ollamaはバックグラウンドで「OpenAI互換サーバー」として動作するため、自作のPythonスクリプトから簡単に呼び出せる点も魅力です。
Dockerを利用することで、環境を汚さずに最新の機能を追従でき、将来的にサーバーを移行する際も設定ファイルをコピーするだけで済みます。
「とりあえず動く」のその先、業務自動化に組み込むことを考えるなら、この構成が現在のベストプラクティスです。

## Step 1: 環境を整える

まずはLLMの実行エンジンであるOllamaをインストールします。
Ollamaは難しい設定なしで、Llama 3やGemmaといった最新モデルを最適化された状態で動かしてくれます。

公式ページ（ollama.com）からインストーラーをダウンロードして実行してください。
インストールが終わったら、ターミナル（PowerShellやMacのターミナル）を開き、以下のコマンドを打ちます。

```bash
# バージョンが表示されればインストール成功
ollama --version

# とりあえずLlama 3をダウンロードして動かしてみる
ollama run llama3.1:8b
```

このコマンドは、モデルの重みファイルをダウンロード（約4.7GB）し、対話モードを起動します。
初回は時間がかかりますが、2回目以降は瞬時に立ち上がります。
ここで日本語で話しかけてみて、返答が返ってくることを確認してください。

落とし穴: Windowsユーザーの場合、WSL2（Windows Subsystem for Linux）が古いとGPUを認識しないことがあります。必ず`wsl --update`を実行し、最新の状態にしておきましょう。また、NVIDIAのドライバーも最新版に更新しておかないと、CPU推論にフォールバックされて極端に動作が遅くなります。

## Step 2: 基本の設定

次に、ChatGPTのような洗練されたUIを提供する「Open WebUI」をDockerで構築します。
なぜDockerを使うのかというと、Open WebUIは依存するライブラリが多く、直接PCにインストールすると環境構築で高確率でエラーが出るからです。

まず、Docker Desktopがインストールされていることを確認してください。
その上で、以下の内容で `docker-compose.yaml` という名前のファイルを作成します。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    # ホストマシンのOllamaと通信するための設定
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "3000:8080"
    volumes:
      - open-webui:/app/backend/data
    restart: always

volumes:
  open-webui:
```

この設定ファイルの肝は `extra_hosts` の部分です。
Dockerコンテナの中から、ホストPC上で動いているOllama（ポート11434）にアクセスするために必要な記述です。
これがないと、UIは立ち上がっても「AIモデルが見つかりません」というエラーで止まってしまいます。

## Step 3: 動かしてみる

ファイルを保存したディレクトリで、以下のコマンドを実行します。

```bash
docker compose up -d
```

起動したら、ブラウザで `http://localhost:3000` にアクセスしてください。
最初のサインアップ画面が出ますが、これはローカルに保存されるアカウントなので、適当なメールアドレスとパスワードで大丈夫です。
（ここで入力した情報が外部に送信されることはありません）

ログイン後、画面上部の「モデルを選択」から、先ほどOllamaでダウンロードした `llama3.1:8b` を選択します。
もしモデルが表示されない場合は、設定（Settings）→ 接続（Connections）から、OllamaのURLが `http://host.docker.internal:11434` になっているか確認してください。

### 期待される出力

チャット欄に「日本の首都は？」と入力して、以下のようなレスポンスが数秒以内に返ってくれば成功です。

```text
日本の首都は東京です。東京都は政治、経済、文化の中心地であり、世界でも有数の大都市です。
何か他に知りたいことはありますか？
```

もし回答が1文字ずつ非常にゆっくり出る場合は、GPUが使われずCPUで処理されています。
タスクマネージャーの「パフォーマンス」タブで、GPUの「Dedicated GPU Memory」が消費されているかチェックしてください。

## Step 4: 実用レベルにする

環境が整ったら、今度はこのローカルLLMを「自分専用のナレッジベース」として活用しましょう。
Open WebUIの「Documents」機能を使えば、PDFやテキストファイルをアップロードするだけで、その内容に基づいた回答（RAG）が可能になります。

また、開発者であればPythonスクリプトからこの環境を叩きたいはずです。
OllamaはOpenAI APIと互換性があるため、ライブラリをそのまま使い回せます。
以下のコードで、ローカルで動いているAIをプログラムから制御してみましょう。

```python
import openai

# OllamaのOpenAI互換エンドポイントを指定
# APIキーはローカルなので何でも良い（空でも可）
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def ask_local_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 実行例
if __name__ == "__main__":
    answer = ask_local_ai("Pythonで高速なAPIを作るならどのフレームワークがおすすめ？")
    print(f"AIの回答:\n{answer}")
```

この方法の利点は、既存のOpenAI向けに書かれたコードの `base_url` を書き換えるだけで、即座に「無料・無制限・プライバシー重視」のシステムに切り替えられることです。
私は、社外秘のソースコードをリファクタリングする際や、大量のログファイルを解析する際、このスクリプトを回して処理しています。
課金制限やトークン制限を気にせず、数万行のデータを流し込めるのはローカル環境ならではの特権です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Connection refused` | Ollamaが起動していない | タスクトレイにOllamaのアイコンがあるか確認。なければ起動する。 |
| モデルが表示されない | Dockerからホストへの通信失敗 | `extra_hosts` の設定を見直す。Windowsならファイアウォール設定も確認。 |
| 回答が壊れる（文字化け） | 量子化による精度劣化 | `q4_K_M` 以上の量子化ビット数を持つモデルを選び直す。 |
| 動作が異常に重い | VRAM不足でスワップが発生 | モデルサイズを小さくする（8B→3Bなど）か、他のアプリを閉じる。 |

## 次のステップ

無事に環境が動いたら、次は「モデルの使い分け」に挑戦してください。
汎用的な対話なら `Llama-3.1`、コーディング特化なら `DeepSeek-Coder`、日本語のニュアンスを重視するなら `Llama-3-Elyza` など、用途に合わせてモデルを切り替えるのがローカル運用の醍醐味です。
Ollamaなら `ollama run deepseek-coder` と打つだけで新しいモデルが手に入ります。

さらに、Open WebUIの「Functions」メニューを覗いてみてください。
ここには、ローカルLLMにWeb検索機能を追加したり、特定の計算ツールを連携させたりするコミュニティ製のプラグインが多数公開されています。
これらを組み合わせることで、特定の業務に特化した「自分専用のAIエージェント」を育てていくことができます。
APIの従量課金に怯える日々から脱却し、AIを「文房具」のように使い倒す生活を始めましょう。

## よくある質問

### Q1: ネット接続がなくても動きますか？

はい、モデルのダウンロード時以外は完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でも、全く同じようにAIと対話したりコードを書かせたりすることが可能です。

### Q2: 4bit量子化（q4_K_M）って何ですか？精度は落ちませんか？

モデルの重みデータを圧縮する技術です。16bitから4bitに圧縮するとメモリ消費量は1/4になりますが、回答精度は数%しか落ちません。個人PCで動かすなら、この4bitや5bitの量子化モデルが最もバランスが良い選択です。

### Q3: 複数のGPUを積んでいる場合はどう設定しますか？

Ollamaはデフォルトで利用可能な全てのNVIDIA GPUを認識してモデルをロードしようとします。特定のGPUだけを使いたい場合は、環境変数 `CUDA_VISIBLE_DEVICES` でデバイスIDを指定してOllamaサービスを起動してください。私のような複数挿し環境では必須の設定です。

---

## あわせて読みたい

- [OllamaとOpen WebUIで最強のローカルLLM環境を構築する方法](/posts/2026-07-27-ollama-open-webui-local-llm-setup/)
- [OllamaとOpen WebUI 使い方ガイド！ローカルLLM構築](/posts/2026-06-30-ollama-openwebui-local-llm-guide/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

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
        "text": "はい、モデルのダウンロード時以外は完全にオフラインで動作します。飛行機の中や、セキュリティの厳しいオフライン環境でも、全く同じようにAIと対話したりコードを書かせたりすることが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "4bit量子化（q4_K_M）って何ですか？精度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの重みデータを圧縮する技術です。16bitから4bitに圧縮するとメモリ消費量は1/4になりますが、回答精度は数%しか落ちません。個人PCで動かすなら、この4bitや5bitの量子化モデルが最もバランスが良い選択です。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のGPUを積んでいる場合はどう設定しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaはデフォルトで利用可能な全てのNVIDIA GPUを認識してモデルをロードしようとします。特定のGPUだけを使いたい場合は、環境変数 CUDAVISIBLEDEVICES でデバイスIDを指定してOllamaサービスを起動してください。私のような複数挿し環境では必須の設定です。 ---"
      }
    }
  ]
}
</script>

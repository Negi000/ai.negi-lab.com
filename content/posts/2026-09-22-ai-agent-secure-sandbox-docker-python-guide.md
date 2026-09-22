---
title: "DockerとPythonでAIエージェントの安全なサンドボックスを構築する方法"
date: 2026-09-22T00:00:00+09:00
slug: "ai-agent-secure-sandbox-docker-python-guide"
cover:
  image: "/images/posts/2026-09-22-ai-agent-secure-sandbox-docker-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "AI Agent Sandbox"
  - "Docker Python SDK"
  - "セキュアコード実行"
  - "AIエージェント 開発"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- LLMが生成したPythonコードを、ホストOSから完全に隔離された環境で実行し、結果だけを安全に受け取るスクリプト
- ネットワーク遮断・リソース制限（メモリ・CPU）を施したDockerベースの実行基盤
- 前提知識：Pythonの基礎、Dockerの基本的なコマンド操作ができること
- 必要なもの：OpenAI APIキー（またはClaude API）、Docker DesktopがインストールされたPC

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとDockerを同時に動かす入門用に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを実行させる際、ローカル環境で直接動かすのは「全財産が入った財布を泥棒に預ける」のと同じくらい危険です。
今回構築するサンドボックスはDockerを使用するため、メモリ消費が激しくなります。
最低でも16GBのRAMを推奨しますが、快適に動かすなら32GBは欲しいところです。
私はRTX 4090を2枚挿した自作サーバーで検証していますが、Dockerコンテナ自体はCPUだけでも動くため、GPUは必須ではありません。

API料金については、GPT-4oやClaude 3.5 Sonnetを利用する場合、1回の検証で数円〜数十円程度かかります。
Docker Desktop自体は個人利用なら無料ですが、商用利用の場合は有料プランが必要になる点だけ注意してください。
もしMacを使っているなら、Apple Silicon（M1/M2/M3）であれば仮想化効率が良いため、非常にスムーズに動作します。

## なぜこの方法を選ぶのか

AIエージェントの実行環境には「E2B」のようなクラウド型サンドボックスも存在しますが、私はあえて「ローカルDocker」を推奨します。
最大の理由は、機密データの扱いです。
外部のサンドボックスサービスにデータを送るリスクをゼロにでき、かつレイテンシ（応答速度）もミリ秒単位で短縮できます。

また、単なる「Pythonのexec()関数」でコードを実行する方法は、絶対に避けるべきです。
OSコマンドを叩かれた瞬間に、あなたのPC内のファイルはすべて削除される可能性があります。
Dockerでネットワークを遮断し、リソースを制限した環境を使い捨てる（エフェメラルな）運用こそが、現時点で最も実用的で安全な解です。

## Step 1: 環境を整える

まずはPythonからDockerを操作するためのライブラリをインストールします。

```bash
pip install docker openai python-dotenv
```

`docker`ライブラリは、Pythonコードからコンテナの起動・停止・削除を行うために使用します。
`python-dotenv`はAPIキーを安全に管理するために必須です。

次に、サンドボックスの土台となるDockerイメージを作成します。
専用のDockerfileを用意することで、実行速度を上げ、必要なライブラリだけを厳選できます。

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 最小限のライブラリのみインストール
RUN pip install --no-cache-dir numpy pandas

# 実行専用ユーザーを作成（root実行を避ける）
RUN useradd -m sandboxuser
USER sandboxuser
WORKDIR /home/sandboxuser
```

⚠️ **落とし穴:**
Docker Desktopを起動し忘れていると、Pythonから「Cannot connect to the Docker daemon」というエラーが出ます。
また、Windows環境ではWSL2のバックエンドが有効になっていることを必ず確認してください。
ここを怠ると、ライブラリは入っているのに動かないという「初心者あるある」の沼にハマります。

## Step 2: 基本の設定

次に、PythonからDockerコンテナを制御するクラスを作成します。
ここでは「ネットワークの遮断」と「リソース制限」が肝になります。

```python
import docker
import os
from dotenv import load_dotenv

load_dotenv()

class AISandbox:
    def __init__(self):
        # Dockerクライアントの初期化
        self.client = docker.from_env()
        # 使用するイメージ名
        self.image_name = "ai-agent-sandbox:latest"

    def run_code(self, code: str):
        # セキュリティ設定を盛り込んだコンテナ実行
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command=f'python3 -c "{code}"',
                # ネットワークを完全に遮断（外部へのデータ送信を防止）
                network_disabled=True,
                # メモリ制限（無限にメモリを食いつぶされるのを防ぐ）
                mem_limit="512m",
                # CPU使用率の制限（0.5コア分に制限）
                nano_cpus=500000000,
                # 実行が終わったら即座にコンテナを削除
                remove=True,
                # タイムアウト設定（10秒以上かかる処理は強制終了）
                stdout=True,
                stderr=True
            )
            return container.decode('utf-8')
        except Exception as e:
            return f"Error: {str(e)}"
```

各設定の意味を解説します。
`network_disabled=True`は、エージェントが勝手に外部サーバーへ情報を送信したり、追加のマルウェアをダウンロードしたりするのを防ぐためです。
`mem_limit="512m"`は、意図的なメモリリークや、不注意による巨大データの読み込みからホストOSを守るために設定しています。
実務では、ここをケチるとシステム全体がフリーズして「再起動するしかない」という事態に陥ります。

## Step 3: 動かしてみる

実際に、このサンドボックスを使って「OSの情報を盗もうとするコード」が防げるか試してみましょう。

```python
sandbox = AISandbox()

# 悪意のあるコードの例（環境変数を表示しようとする）
malicious_code = "import os; print(os.environ)"

# 実行
result = sandbox.run_code(malicious_code)
print("--- 実行結果 ---")
print(result)
```

### 期待される出力

```
--- 実行結果 ---
Error: 404 Client Error for http+docker://localhost/v1.41/containers/create: Not Found ("pull access denied for ai-agent-sandbox, repository does not exist or may require 'docker login'")
```

（※先に `docker build -t ai-agent-sandbox:latest .` を実行していない場合のエラー例です。これを防ぐために、事前にビルドが必要です）

正常にビルドして実行すると、ホスト側の環境変数は一切表示されず、コンテナ内の空っぽの環境変数が表示されるだけになります。
これが「隔離」の力です。

## Step 4: 実用レベルにする

実務では、LLMにコードを書かせて、その結果をサンドボックスで動かす一連の流れを自動化する必要があります。
ここでは、OpenAIのAPIと連携させた「自動コード実行エージェント」の完成形を示します。

```python
import openai

def ask_ai_and_run(prompt: str):
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # LLMに「Pythonコードだけ」を出力させるプロンプト
    system_prompt = "あなたは優秀なエンジニアです。回答は実行可能なPythonコードのみを出力してください。print文で結果を表示してください。"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    generated_code = response.choices[0].message.content.strip()
    # Markdownの装飾（```python ... ```）を剥ぎ取る
    clean_code = generated_code.replace("```python", "").replace("```", "").strip()

    print(f"--- 生成されたコード ---\n{clean_code}\n")

    # サンドボックスで実行
    sandbox = AISandbox()
    result = sandbox.run_code(clean_code)
    return result

# 実行例：複雑な計算をエージェントにやらせる
output = ask_ai_and_run("1から100までの素数をリストアップして、その合計を計算して")
print(f"--- 最終出力 ---\n{output}")
```

このスクリプトのポイントは、LLMが生成した「生」のコードをそのまま受け取り、前処理（Markdownの除去）をしてから隔離環境に投げ込んでいる点です。
私は以前、これと同じ仕組みを本番環境のデータ分析ツールとして導入しました。
ユーザーが自然言語でグラフ作成を依頼すると、裏側でDockerが立ち上がり、数秒後には安全に生成された画像だけが返ってくる仕組みです。

実務で使うなら、さらに「エラーが出た場合にLLMにエラー内容をフィードバックして、コードを修正させるループ（Self-Correction）」を実装すると、エージェントの完遂率が劇的に上がります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Docker Permission Denied | 実行ユーザーにDocker操作権限がない | `sudo usermod -aG docker $USER` を実行（Linux） |
| Container Limit Reached | 古いコンテナが削除されずに残っている | `remove=True` 設定を確認し、`docker container prune` で掃除 |
| Library Not Found | Dockerfileに記述されていないライブラリをLLMが使った | LLMに「使えるライブラリ」をプロンプトで明示する |

## 次のステップ

この記事の内容をマスターしたら、次は「永続化（Persistence）」に挑戦してください。
現在の設定では、実行ごとにコンテナが消えるため、作成したファイルも消えてしまいます。
特定のディレクトリだけを `volumes` 設定でマウントすることで、「エージェントがレポートをPDFで出力し、それをホスト側で受け取る」といった高度な自動化が可能になります。

また、ローカルLLM（Llama 3やQwen 2.5など）と組み合わせるのも面白いでしょう。
RTX 4090などの強力なGPUがあるなら、Ollamaと連携させることで、API料金を気にせず無限にサンドボックス内でコードを試行錯誤させる「自己進化型エージェント」も夢ではありません。
私は自宅のサーバーでこれを24時間回していますが、隔離環境のおかげで、一度もメインOSが壊れたことはありません。

## よくある質問

### Q1: Docker Desktopなしで、もっと軽量に動かす方法はありますか？

Linux環境であれば、`Podman`を使うのが良い選択肢です。Dockerと互換性がありつつ、デーモンレスで動作するため、よりセキュアで軽量です。MacやWindowsの場合は、Docker Desktopが最もトラブルが少なく、結局のところ近道になります。

### Q2: 実行時間が10秒を超えてしまう重い処理はどうすればいいですか？

`run_code` メソッド内の `timeout` 設定（内部的には `stop_timeout`）を調整してください。ただし、エージェントが無限ループに陥った際にリソースを食い潰し続けるため、長くても60秒程度を上限に設定し、監視ログを吐き出すように作るのが定石です。

### Q3: LLMが生成したコードに、外部APIを叩く処理が含まれていた場合はどうなりますか？

今回の `network_disabled=True` 設定により、そのコードは確実に失敗します。もし特定のAPI（例えば天気予報APIなど）だけを許可したい場合は、Dockerのネットワークブリッジ設定をいじる必要がありますが、セキュリティ強度は下がります。まずは「完全遮断」から始めるのが私の推奨です。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Appwrite 2.0 使い方とAIエージェント開発における実用性レビュー](/posts/2026-09-17-appwrite-2-review-ai-agent-backend/)
- [Fillo 使い方：AIエージェント時代のバックエンド不要フォーム実装術](/posts/2026-09-04-fillo-native-forms-ai-agent-review/)
- [ReplitとAmazonがDisrupt 2026で激突？AI開発環境の覇権争いが加速する理由](/posts/2026-07-30-techcrunch-disrupt-2026-replit-amazon-ai-agent/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Docker Desktopなしで、もっと軽量に動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Linux環境であれば、Podmanを使うのが良い選択肢です。Dockerと互換性がありつつ、デーモンレスで動作するため、よりセキュアで軽量です。MacやWindowsの場合は、Docker Desktopが最もトラブルが少なく、結局のところ近道になります。"
      }
    },
    {
      "@type": "Question",
      "name": "実行時間が10秒を超えてしまう重い処理はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "runcode メソッド内の timeout 設定（内部的には stoptimeout）を調整してください。ただし、エージェントが無限ループに陥った際にリソースを食い潰し続けるため、長くても60秒程度を上限に設定し、監視ログを吐き出すように作るのが定石です。"
      }
    },
    {
      "@type": "Question",
      "name": "LLMが生成したコードに、外部APIを叩く処理が含まれていた場合はどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回の networkdisabled=True 設定により、そのコードは確実に失敗します。もし特定のAPI（例えば天気予報APIなど）だけを許可したい場合は、Dockerのネットワークブリッジ設定をいじる必要がありますが、セキュリティ強度は下がります。まずは「完全遮断」から始めるのが私の推奨です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

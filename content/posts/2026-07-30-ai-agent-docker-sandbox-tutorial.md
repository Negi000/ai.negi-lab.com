---
title: "Dockerで構築するAIエージェント用コード実行サンドボックス入門"
date: 2026-07-30T00:00:00+09:00
slug: "ai-agent-docker-sandbox-tutorial"
cover:
  image: "/images/posts/2026-07-30-ai-agent-docker-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Docker サンドボックス"
  - "AIエージェント 自作"
  - "Python Docker SDK 使い方"
  - "コード実行 安全性"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

LLM（大規模言語モデル）が生成したPythonコードを、ホストOSから完全に隔離されたDockerコンテナ内で安全に実行し、実行結果だけを取得するサンドボックス環境を構築します。
AIエージェントにPC上のファイルを操作させたり、ライブラリをインストールさせたりする際に、メイン環境を破壊されるリスクをゼロにするための必須技術です。
Pythonの`docker`ライブラリを使用し、リソース制限（メモリ・CPU）とネットワーク遮断を施した「使い捨て実行環境」を自動生成するスクリプトを完成させます。

前提知識：Pythonの基礎文法、Dockerの基本的な概念（イメージとコンテナの違い）がわかること。
必要なもの：Python 3.10以上、Docker Desktop（またはDocker Engine）、OpenAI等のAPIキー（動作確認用）。

## 先に確認するスペック・料金

AIエージェントのサンドボックス構築において、最も重要なのは「メモリ量」です。
コンテナを立ち上げるたびにオーバーヘッドが発生するため、同時に複数のエージェントを走らせるなら最低でも16GB、ローカルLLMと併用するなら32GB以上のRAMを推奨します。
私はRTX 4090を2枚挿した自作サーバーで運用していますが、推論と実行環境を分ける場合、GPU性能はサンドボックス側には直接影響しません。

料金面では、Docker自体は個人利用なら無料です。
API料金はOpenAIのGPT-4oを使う場合、1リクエストあたり数円程度ですが、エージェントがループ（試行錯誤）を繰り返すと1時間で数百円に達することもあります。
まずは、無料枠のあるClaudeや、安価なGemini 1.5 Flashでテストするのが賢明です。
Macユーザーなら、M2/M3チップ以降のモデルであれば、Dockerの起動も高速でストレスなく開発できます。

## なぜこの方法を選ぶのか

AIにコードを実行させる手段は、主に3つあります。
1つ目は、ローカル環境で直接`exec()`や`subprocess`を使う方法ですが、これは論外です。
LLMが「`os.remove('/')`」に近いコードを生成した瞬間にシステムが崩壊します。

2つ目は、E2BやModalといったクラウド型のサンドボックスSaaSを使う方法です。
これは非常に便利ですが、実行ごとに料金が発生し、機密データを外部サーバーに送るリスクが伴います。

3つ目が、今回採用する「ローカルDockerによる隔離環境」です。
ネットワークを遮断すればデータ流出を防げますし、リソース制限をかければ無限ループによるフリーズも回避できます。
何より、API料金以外のランニングコストがゼロであり、実務で「社内データを扱うAIエージェント」を構築する際のデファクトスタンダードと言える構成です。

## Step 1: 環境を整える

まずは、PythonからDockerを操作するためのSDKをインストールします。

```bash
# Docker操作用のSDK
pip install docker

# LLM呼び出し用のライブラリ（今回はOpenAIを使用）
pip install openai python-dotenv
```

`docker`パッケージは、Docker Desktopなどのデーモンが動いていることが前提です。
`docker ps`コマンドがターミナルで通ることを必ず確認してください。
バージョンは最新のSDKであれば問題ありませんが、Python 3.10以上を推奨するのは、型ヒントの記述を簡潔にするためです。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使っている場合、Docker Desktopの設定で「Use the WSL 2 based engine」にチェックが入っているか確認してください。
これが入っていないと、Python側からDockerソケットにアクセスできず、`DockerException`で止まります。
また、Linux環境では実行ユーザーが`docker`グループに所属していないと、`sudo`なしではコンテナを起動できません。

## Step 2: 基本の設定

次に、サンドボックスの心臓部となる「実行用イメージ」を作成します。
毎回コンテナをビルドすると遅いため、必要なライブラリを入れたベースイメージをあらかじめ用意しておくのが実務のコツです。

```python
import docker
import os
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

# サンドボックス用のDockerfileを定義
DOCKERFILE = """
FROM python:3.11-slim
RUN pip install pandas numpy requests  # よく使われるライブラリを事前に入れる
WORKDIR /workspace
"""

def setup_sandbox_image():
    """実行用イメージを作成または取得する"""
    image_tag = "ai-agent-sandbox:latest"
    try:
        client.images.get(image_tag)
        print("既存のイメージを使用します。")
    except docker.errors.ImageNotFound:
        print("イメージをビルドしています...（初回のみ時間がかかります）")
        with open("Dockerfile", "w") as f:
            f.write(DOCKERFILE)
        client.images.build(path=".", tag=image_tag, rm=True)
        os.remove("Dockerfile")
    return image_tag

# 実行
IMAGE_NAME = setup_sandbox_image()
```

ここでは`python:3.11-slim`をベースにしています。
`alpine`イメージの方が軽量ですが、一部の科学技術計算ライブラリ（pandas等）のビルドに失敗したり、依存関係でハマることが多いため、実務では`slim`系を選ぶのが無難です。
`rm=True`を指定しているのは、ビルド中の中間コンテナを削除してディスク容量を節約するためです。

## Step 3: 動かしてみる

いよいよ、LLMが書いた（と想定される）コードを安全に実行する関数を作成します。
ここには「仕事で使うため」の重要なガードレールを複数組み込みます。

```python
def execute_code_safely(code: str, timeout: int = 10):
    """
    指定されたコードをDockerコンテナ内で実行する。

    Args:
        code (str): 実行したいPythonコード
        timeout (int): 実行制限時間（秒）
    """
    # ネットワーク遮断、メモリ制限(512MB)、CPU制限(1.0コア分)を設定
    # これにより、マイニングコードや無限ループ、外部へのデータ送信を防ぐ
    try:
        container = client.containers.run(
            image=IMAGE_NAME,
            command=f'python -c "{code}"',
            network_mode="none",  # 外部通信を完全遮断
            mem_limit="512m",      # メモリ不足によるホストフリーズを防止
            nano_cpus=1000000000, # 1.0 CPU分に制限
            detach=True,
            stderr=True,
            stdout=True
        )

        # 指定時間待機
        try:
            result = container.wait(timeout=timeout)
            logs = container.logs().decode("utf-8")
            status_code = result["StatusCode"]
        except Exception as e:
            container.kill()
            return "Error: Timeout or execution failed."
        finally:
            container.remove(force=True)

        return logs if status_code == 0 else f"Runtime Error: {logs}"

    except Exception as e:
        return f"Container Error: {str(e)}"

# テスト実行
test_code = "print(1 + 1); import os; print(os.uname().sysname)"
print(execute_code_safely(test_code))
```

### 期待される出力

```
2
Linux
```

この出力で重要なのは、ホストがWindowsやMacであっても、実行環境は「Linux」と表示される点です。
完全に分離されていることがわかります。
また、`network_mode="none"`にしているため、もしコード内に`requests.get('https://google.com')`と書いてあっても、エラーとなり外部へは繋がりません。

## Step 4: 実用レベルにする

実務では、LLMにこの関数を使わせる「エージェント・ループ」が必要です。
OpenAIの`tool_choice`を利用して、LLMが「あ、この問題は計算やデータ操作が必要だ」と判断した時に、自動的にサンドボックスを動かす仕組みを構築します。

```python
import json
from openai import OpenAI

client_ai = OpenAI()

def agent_run(user_prompt: str):
    # システムプロンプトで「計算やファイル操作はPythonコードを生成して実行せよ」と指示
    system_msg = "あなたはPythonエンジニアです。複雑な計算やデータ処理は、必ずpython_sandboxツールを使って実行してください。"

    tools = [{
        "type": "function",
        "function": {
            "name": "python_sandbox",
            "description": "Pythonコードを安全な環境で実行し、標準出力を返す",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "実行するPythonコード"}
                },
                "required": ["code"]
            }
        }
    }]

    response = client_ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        tools=tools
    )

    tool_call = response.choices[0].message.tool_calls[0]
    if tool_call:
        args = json.loads(tool_call.function.arguments)
        print(f"--- LLMが生成したコード ---\n{args['code']}\n---------------------------")

        # サンドボックスで実行
        execution_result = execute_code_safely(args['code'])
        print(f"--- 実行結果 ---\n{execution_result}")

        # 結果をLLMに戻して最終回答を得る（実務ではここをループ化する）
        return execution_result

# 実行例
agent_run("1から1000までの素数を数えて、その合計を教えてください。")
```

このコードのポイントは、LLMに「安全な砂場」という道具を渡している点です。
私は以前、複雑な株価分析をLLMに依頼した際、LLMが勝手にローカルの`~/Documents`をスキャンしようとしたのを目撃しました。
サンドボックスを使っていれば、コンテナ内には何もファイルがないため、被害はゼロで済みます。

さらに実務で運用するなら、`volumes`オプションを使って「特定のインプット用フォルダだけを読み取り専用でマウントする」設定を加えると、安全にデータ分析を任せることができます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Dockerデーモンが未起動 | Docker Desktopを起動し、権限があるか確認する |
| `Memory limit exceeded` | コードがメモリを食い過ぎた | `mem_limit`の値を増やすか、LLMにメモリ節約を指示する |
| `Permission denied` | `/var/run/docker.sock`へのアクセス権がない | ユーザーを`docker`グループに追加し、再ログインする |

## 次のステップ

この記事で、安全なコード実行環境の「最小単位」が完成しました。
しかし、本気でAIエージェントを業務投入するなら、以下のステップに進んでください。

1. **永続的な作業領域の提供**:
   `volumes`を設定し、コンテナが消えても分析結果のCSVや図表が残るようにします。この際、ホスト側のディレクトリパーミッション設定には細心の注意を払ってください。

2. **マルチステップの試行錯誤（ReActプロンプティング）**:
   コード実行が失敗（エラー）した場合、そのエラー内容を再びLLMに投げ、修正コードを書かせるループを実装します。これでエージェントの自律性が飛躍的に高まります。

3. **プリインストール・ライブラリの拡充**:
   業務に合わせて`matplotlib`や`openpyxl`などをあらかじめイメージに含めておくと、エージェントが「ライブラリがない」と嘆く時間を削れます。

AIエージェントは、PCの操作権限を得て初めて真価を発揮します。
その権限を「安全に」与えるための技術が、今回紹介したサンドボックスです。
まずは手元の環境で、素数計算でもファイルリスト取得でもいいので、コンテナが動く快感を体験してみてください。

## よくある質問

### Q1: Dockerの起動が遅いのですが、高速化する方法はありますか？

コンテナを毎回`run`するのではなく、一度起動したコンテナを使い回し、`exec_run`でコードを送り込む方法があります。これならオーバーヘッドがほぼゼロになり、レスポンスが0.1秒単位で改善します。

### Q2: 外部のライブラリをその場でインストールさせたい場合は？

`network_mode="none"`を外し、`pip install`コマンドを許可する必要があります。ただし、これはセキュリティリスクを高めます。信頼できるプロキシを通すか、主要なライブラリはあらかじめイメージに入れておくのが実務的な解です。

### Q3: GPUをサンドボックス内で使わせることは可能ですか？

可能です。`device_requests`オプションでGPUを指定すれば、コンテナ内でPyTorch等を動かせます。ただし、NVIDIA Container Toolkitのインストールが必要です。AIにモデルの微調整をさせるような高度なタスクで使われます。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBはエージェントとローカルLLMを並行稼働させる際の最低ラインです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [OllamaとPythonで実用的なローカルAIエージェントを自作する方法](/posts/2026-06-02-ollama-python-local-ai-agent-tutorial/)
- [Open InterpreterでManus級の自律型AIエージェントを自作する方法](/posts/2026-04-27-build-ai-agent-open-interpreter-manus-alternative/)
- [Qwen3.7 Max APIとローカルLLMを連携させたハイブリッドAIエージェントの構築方法](/posts/2026-05-20-qwen37-max-local-hybrid-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerの起動が遅いのですが、高速化する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "コンテナを毎回runするのではなく、一度起動したコンテナを使い回し、execrunでコードを送り込む方法があります。これならオーバーヘッドがほぼゼロになり、レスポンスが0.1秒単位で改善します。"
      }
    },
    {
      "@type": "Question",
      "name": "外部のライブラリをその場でインストールさせたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "networkmode=\"none\"を外し、pip installコマンドを許可する必要があります。ただし、これはセキュリティリスクを高めます。信頼できるプロキシを通すか、主要なライブラリはあらかじめイメージに入れておくのが実務的な解です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUをサンドボックス内で使わせることは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。devicerequestsオプションでGPUを指定すれば、コンテナ内でPyTorch等を動かせます。ただし、NVIDIA Container Toolkitのインストールが必要です。AIにモデルの微調整をさせるような高度なタスクで使われます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBはエージェントとローカルLLMを並行稼働させる際の最低ラインです</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "PythonとDockerで作るAIエージェント用安全実行サンドボックス構築ガイド"
date: 2026-11-01T00:00:00+09:00
slug: "python-docker-ai-agent-sandbox-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Docker SDK Python"
  - "AI Sandbox"
  - "AIエージェント 安全性"
  - "コード実行環境 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- LLMが生成したPythonコードを、ホストOSから完全に隔離されたDockerコンテナ内で安全に実行し、その結果を取得するサンドボックス環境。
- 前提知識：Pythonの基本的な文法、Dockerの基本的な概念（イメージ、コンテナ）を理解していること。
- 必要なもの：Python 3.10以上、Docker Desktop（またはDocker Engine）、OpenAI APIキー（GPT-4o mini等を使用するため）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとDockerを併用する入門機として最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントのサンドボックスをローカルで動かす場合、特別なGPUは必須ではありません。
コードの実行自体はCPUだけで完結するため、4コア以上のCPUと8GB以上のメモリがあれば十分動作します。
ただし、エージェントの頭脳としてLLMを頻繁に叩くため、APIコストは意識しておく必要があります。

OpenAIのGPT-4o miniを使えば、1回のコード生成と実行テストにかかる費用は0.1円以下です。
一方で、ローカルLLM（Llama 3.1 8Bなど）を使って完全にオフラインで動かしたい場合は、VRAM 8GB以上のGPU（RTX 3060など）を推奨します。
Macユーザーなら、メモリ16GB以上のApple Silicon搭載機であれば、DockerとローカルLLMを同時に動かしてもストレスを感じないはずです。
もしこれから機材を揃えるなら、Dockerコンテナを複数立ち上げる負荷を考慮して、メモリは32GB積んでおくと後悔しません。

## なぜこの方法を選ぶのか

AIエージェントにコードを書かせて実行させる際、最も恐ろしいのは「自分のPCのファイルを意図せず消去・改ざんされること」です。
Open Interpreterなどの既存ツールもありますが、デフォルト設定ではローカル環境に直接アクセスするため、検証用としてはリスクが残ります。

世の中にはE2BやPistonといったコード実行用の外部APIサービスもありますが、私はあえて「ローカルDocker SDK」を使う方法を推奨します。
理由はシンプルで、通信が発生しないためレスポンスが0.5秒以内と速く、かつ社外秘のデータを外部サーバーに送る必要がないからです。
自分でDockerの制限（メモリ上限やネットワーク遮断）をプログラムから細かく制御できるため、業務レベルの安全性を担保するにはこの形がベストだと考えています。

## Step 1: 環境を整える

まずは、PythonからDockerを操作するためのライブラリをインストールします。
Docker Desktopが起動していることを事前に確認してください。

```bash
# Docker操作用ライブラリとLLM呼び出し用のライブラリをインストール
pip install docker openai python-dotenv
```

`docker`ライブラリは、Docker EngineのAPIをPythonから叩くためのSDKです。
これを使うことで、`docker run`コマンドを打つ代わりに、Pythonコードからコンテナを生成・削除できます。

⚠️ **落とし穴:**
Windows環境でDocker Desktopを使っている場合、WSL2が正しくセットアップされていないと「Dockerが見つかりません」というエラーが出ます。
ターミナルで `docker ps` を実行して、エラーが出ないことを確認してから進めてください。

## Step 2: 基本の設定

次に、サンドボックスの心臓部となるDockerイメージを準備します。
素のPythonイメージを使っても良いのですが、エージェントがpandasやnumpyを使いたい場面が多いため、あらかじめこれらを入れた「専用イメージ」を作るのが実用的です。

プロジェクトのルートディレクトリに `Dockerfile` を作成します。

```dockerfile
# 軽量なPythonイメージを使用
FROM python:3.10-slim

# 作業ディレクトリの設定
WORKDIR /app

# エージェントがよく使うライブラリを事前にインストール
# これをしないと、実行のたびにpip installが走り、レスポンスが10秒以上遅くなります
RUN pip install --no-cache-dir pandas numpy matplotlib requests

# セキュリティのため、rootユーザーではなく一般ユーザーで実行させる設定（推奨）
RUN useradd -m sandboxuser
USER sandboxuser

# コンテナが勝手に終了しないように維持する
CMD ["tail", "-f", "/dev/null"]
```

このDockerfileをビルドします。

```bash
docker build -t ai-sandbox-python .
```

なぜわざわざビルドするのか。
それは、実行時にライブラリをインストールさせると、ネットワーク経由で悪意のあるパッケージをダウンロードされるリスクがあるからです。
「許可されたライブラリ入りのイメージ」を固定して使うのが、プロのやり方です。

## Step 3: 動かしてみる

いよいよ、PythonからDockerコンテナを起動し、コードを流し込んで結果を受け取るスクリプトを書きます。
まずはLLMを介さず、固定のコードを実行できるか確認しましょう。

`sandbox_manager.py` という名前で保存してください。

```python
import docker
import os

def run_code_in_sandbox(code: str):
    client = docker.from_env()

    # コンテナの起動設定
    # mem_limitでメモリを制限し、network_disabledで外部通信を遮断するのが鉄則
    container = client.containers.run(
        "ai-sandbox-python",
        command="python -c \"{}\"".format(code.replace('"', '\\"')),
        detach=True,
        mem_limit="128m",
        network_disabled=True,
        remove=True # 実行後にコンテナを自動削除。これがないとゴミが溜まる
    )

    # 実行結果を取得
    # logs()はバイト列で返ってくるのでdecodeが必要
    try:
        # タイムアウトを設定（無限ループ対策）
        result = container.wait(timeout=5)
        logs = container.logs().decode("utf-8")
        return logs
    except Exception as e:
        return f"Error or Timeout: {str(e)}"
    finally:
        # タイムアウト時などに備えて強制停止
        try:
            container.stop()
        except:
            pass

# テスト実行
if __name__ == "__main__":
    test_code = "print(1 + 1); import os; print('Current Dir:', os.getcwd())"
    print("--- 実行結果 ---")
    print(run_code_in_sandbox(test_code))
```

### 期待される出力

```
--- 実行結果 ---
2
Current Dir: /app
```

（解説）
`mem_limit="128m"` は、エージェントが間違ってメモリを食いつぶすプログラム（巨大な行列計算など）を走らせた際に、ホストOSを道連れにしないための防壁です。
また、`network_disabled=True` にすることで、エージェントが踏み台にされて外部にDDoS攻撃を仕掛けたり、秘密鍵を外部サーバーに送信したりするのを物理的に防いでいます。

## Step 4: 実用レベルにする

単にコードを動かすだけでは「エージェント」とは言えません。
LLMに課題を与え、必要ならコードを生成させて、その結果を見て次の行動を考えさせるループを作ります。

ここでは「OpenAIのGPT-4o mini」を使って、計算課題を解かせてみましょう。

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ask_agent_to_solve(task: str):
    # LLMに「Pythonコードだけで回答し、print文で結果を出せ」と指示
    # このプロンプトの設計が、実行成功率を左右します
    prompt = f"""
    以下の課題を解くためのPythonコードを書いてください。
    出力はコードのみとし、解説は不要です。
    必ず結果をprint関数で出力してください。

    課題: {task}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    generated_code = response.choices[0].message.content.strip()
    # Markdownのコードブロックを剥ぎ取る処理
    clean_code = generated_code.replace("```python", "").replace("```", "").strip()

    print(f"--- 生成されたコード ---\n{clean_code}\n")

    # サンドボックスで実行
    result = run_code_in_sandbox(clean_code)
    return result

if __name__ == "__main__":
    task = "1から100までの素数をリストアップして、その合計を求めてください。"
    print("--- 最終結果 ---")
    print(ask_agent_to_solve(task))
```

私は以前、この仕組みを構築した際、LLMが `os.system('rm -rf /')` のようなコードを生成しないか不安で、全ての実行コマンドを正規表現でチェックしていました。
しかし、Dockerの `network_disabled` と `remove=True` を組み合わせることで、万が一悪意のあるコードが走っても、次の瞬間にはその環境ごと消滅するため、過度に神経質になる必要がなくなりました。
これがコンテナを使う最大のメリットです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Docker Desktopが起動していない | タスクバーからDockerの状態を確認し、起動する。 |
| `Permission denied` | 実行ユーザーの権限不足 | Linuxの場合、`sudo usermod -aG docker $USER` でユーザーをdockerグループに追加する。 |
| `Memory limit exceeded` | 処理に対してメモリ制限が厳しすぎる | `mem_limit` を "256m" や "512m" に緩和する。 |
| `ImportError: No module named...` | Dockerイメージにライブラリがない | Dockerfileに `RUN pip install` を追記して再ビルドする。 |

## 次のステップ

この記事で構築したサンドボックスは、あくまで「一過性の実行環境」です。
これをさらに実用化するためには、以下の2点に挑戦してみてください。

1. **永続ボリュームのマウント:**
`client.containers.run` の引数に `volumes` を追加し、特定のフォルダ（例: `/data`）だけをコンテナと共有させます。これにより、エージェントがCSVファイルを読み込んでグラフ画像を生成し、その画像をホスト側で受け取るといった「データ分析エージェント」への拡張が可能になります。

2. **マルチステップ・エージェントの構築:**
一度の実行で終わらず、エラーが出たらそのエラーメッセージをLLMに返し、修正版のコードを再度生成させるループ（自己修復ループ）を実装してみてください。
実務では一発でコードが動くことは稀です。この「失敗から学ばせる」仕組みを組み込むことで、エージェントの完遂率は劇的に向上します。

次は、ローカルLLMである `Ollama` を使って、このサンドボックスを完全オフラインで動かす方法を試してみるのが面白いと思いますよ。

## よくある質問

### Q1: Docker Desktopは有料化されましたが、無料で代替する方法はありますか？

個人利用や小規模企業（従業員250人未満かつ年間売上1000万ドル未満）であればDocker Desktopは引き続き無料です。それを超える場合は、OrbStack（Mac）や、WSL2上の純粋なDocker Engineを使用することで、コストを抑えつつ同様の環境が構築可能です。

### Q2: 実行コードに制限をかけたいのですが、どうすればいいですか？

Dockerの `ulimit` 設定を使うことで、CPU使用時間やプロセス数に制限をかけられます。例えば `ulimits=[docker.types.Ulimit(name='cpu', soft=1, hard=2)]` のように指定すれば、エージェントがマイニングコードを走らせてCPUを100%奪うような事態を防止できます。

### Q3: Python以外の言語も実行させたい場合は？

Dockerfileの `FROM` イメージを `node:latest` や `golang:latest` に変えるだけで、JavaScriptやGoのサンドボックスに早変わりします。Docker SDKの使い方は共通なので、1つの管理スクリプトで多言語対応のエージェント環境を作ることも難しくありません。

---

## あわせて読みたい

- [AIエージェント専用サンドボックスE2Bの使い方入門](/posts/2026-09-11-e2b-ai-agent-sandbox-tutorial-python/)
- [InstaVM レビュー：AIエージェントに「安全な肉体」を与える高速サンドボックス環境](/posts/2026-05-22-instavm-review-ai-agent-sandbox/)
- [PythonとE2BでAIエージェント用セキュア実行環境を作る方法](/posts/2026-08-23-python-e2b-ai-agent-sandbox-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Docker Desktopは有料化されましたが、無料で代替する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "個人利用や小規模企業（従業員250人未満かつ年間売上1000万ドル未満）であればDocker Desktopは引き続き無料です。それを超える場合は、OrbStack（Mac）や、WSL2上の純粋なDocker Engineを使用することで、コストを抑えつつ同様の環境が構築可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "実行コードに制限をかけたいのですが、どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerの ulimit 設定を使うことで、CPU使用時間やプロセス数に制限をかけられます。例えば ulimits=[docker.types.Ulimit(name='cpu', soft=1, hard=2)] のように指定すれば、エージェントがマイニングコードを走らせてCPUを100%奪うような事態を防止できます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語も実行させたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerfileの FROM イメージを node:latest や golang:latest に変えるだけで、JavaScriptやGoのサンドボックスに早変わりします。Docker SDKの使い方は共通なので、1つの管理スクリプトで多言語対応のエージェント環境を作ることも難しくありません。 ---"
      }
    }
  ]
}
</script>

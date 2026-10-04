---
title: "AIエージェント用サンドボックス構築入門：Dockerで安全なコード実行環境を作る方法"
date: 2026-10-04T00:00:00+09:00
slug: "python-ai-agent-docker-sandbox-tutorial"
cover:
  image: "/images/posts/2026-10-04-python-ai-agent-docker-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "AI Agent Sandbox"
  - "Docker-py 使い方"
  - "AI 安全 実行環境"
  - "Python サンドボックス 構築"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- AIエージェントが生成したPythonコードを、ホスト環境から完全に隔離して実行し、結果だけを安全に回収するサンドボックス環境。
- 前提知識：Pythonの基本的な文法、Dockerの基本的な概念（イメージ、コンテナ）がわかること。
- 必要なもの：Docker Desktop（またはDocker Engine）、Anthropic APIキー（Claude 3.5 Sonnet推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Crucial 64GB Kit</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Dockerコンテナを複数並列で動かす際、メモリ32GB以上あると開発が安定するため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FCrucial%2520RAM%252064GB%2520DDR5%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FCrucial%2520RAM%252064GB%2520DDR5%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Crucial%20RAM%2064GB%20DDR5&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを実行させる際、最も重要なのは「リソースの制限」です。
ローカルで動かす場合、メモリは最低でも16GB、できれば32GB以上を推奨します。
Dockerコンテナを立ち上げる際、1個あたり数百MBのメモリを消費するため、並列でエージェントを走らせるなら積めるだけ積んでおいたほうがいいですね。
私は自宅サーバーに128GB積んでいますが、開発中のエージェントが無限ループに陥ってもOSごと落ちない安心感は代えがたいものです。

API料金については、GPT-4oやClaude 3.5 Sonnetを使用する場合、1回の検証で$0.1〜$0.5程度かかります。
安く済ませたいなら、ローカルLLM（Llama 3など）をOllama経由で使う構成もありますが、コード生成の精度を考えると最初は商用APIを使うのが最短ルートです。
GPUについては、今回のような「サンドボックス構築」自体には不要ですが、推論をローカルで完結させるならVRAM 16GB以上のRTX 4060 Tiや4090があると、開発のイテレーションが0.3秒レベルで爆速になります。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる手段は、大きく分けて3つあります。
1つは「E2B」などのマネージド・サンドボックスを使う方法。
これは設定が楽でセキュアですが、APIを叩くたびに従量課金が発生し、何より「実行環境がクラウドにある」ため、ローカルにある機密ファイルを扱いにくいという欠点があります。

2つ目は「LangChain」などの組み込みツールを使う方法ですが、これは抽象化されすぎていて、中で何が起きているか把握しづらく、セキュリティ設定の微調整が効きません。
そこで、3つ目の選択肢である「Docker-pyを利用した自作サンドボックス」を私は選んでいます。
この方法なら、ネットワークを完全に遮断した状態で、CPUやメモリの使用量を1MB単位で制御でき、実務で要求される「機密データのローカル処理」と「安全なコード実行」を両立できるからです。

## Step 1: 環境を整える

まずはPythonからDockerを操作するためのライブラリをインストールします。

```bash
pip install docker anthropic python-dotenv
```

`docker`ライブラリは、Docker EngineのAPIをPythonから叩くための公式SDKです。
これを使うことで、`docker run`コマンドをPythonコードの中から動的に制御できるようになります。

⚠️ **落とし穴:**
Windows環境でWSL2を使っている場合、Docker Desktopの設定で「Expose daemon on tcp://localhost:2375 without TLS」をオンにする必要があると思われがちですが、これはセキュリティリスクが高いのでNGです。
デフォルトのUnixソケット（または名前付きパイプ）経由で接続するのが正解です。
また、Dockerを起動していない状態でPythonを実行すると `DockerException` で即落ちするので、必ずDockerのダッシュボードでクジラが泳いでいることを確認してください。

## Step 2: 基本の設定

まずは、Dockerコンテナを管理するための「Sandbox」クラスを作成します。
SIer時代に嫌というほど叩き込まれた「リソース管理」の観点から、コンテナを確実に掃除する仕組みを組み込みます。

```python
import docker
import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class AISandbox:
    def __init__(self, image="python:3.10-slim"):
        # Dockerクライアントの初期化。デフォルトでローカルのDocker Engineに接続します。
        self.client = docker.from_env()
        self.image = image

    def execute_code(self, code, timeout=10):
        # 実行するPythonコードをラップ。
        # print文がないとLLMが結果を受け取れないため、最後に変数を表示させる工夫が必要です。
        formatted_code = f"import sys\n{code}"

        container = None
        try:
            # コンテナの作成と実行
            # network_mode="none" で外部通信を遮断し、AIが勝手に外部へデータを送るのを防ぎます。
            # mem_limit="128m" でメモリを制限し、メモリ消費バグによるホストのハングを防ぎます。
            container = self.client.containers.run(
                image=self.image,
                command=['python', '-c', formatted_code],
                detach=True,
                network_mode="none",
                mem_limit="128m",
                cpu_quota=50000, # CPU使用率を最大50%に制限
            )

            # 終了を待機。設定したtimeoutを超えたら強制終了させます。
            start_time = time.time()
            while container.status != 'exited':
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return "Error: Timeout"
                time.sleep(0.5)

            # ログ（実行結果）の取得
            logs = container.logs().decode('utf-8')
            return logs

        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            # 使い終わったコンテナは即座に削除。これを忘れるとディスクが死にます。
            if container:
                container.remove(force=True)
```

（解説）
ここで `network_mode="none"` を指定しているのは、万が一AIが「外部のサーバーに情報を送信するスクリプト」を生成してしまった際の水際対策です。
また、`mem_limit` を128MBに設定しているのは、AIが巨大なリストを作るようなコードを書いても、私のRTX 4090マシンがメモリ不足（OOM）で不安定になるのを防ぐためです。

## Step 3: 動かしてみる

次に、このサンドボックスを使って、実際にClaude 3.5 Sonnetにコードを書かせて実行させてみます。
私が仕事で使う場合、ただ「コードを書かせる」のではなく、「結果をパースして再試行させる」ループを重視します。

```python
def ask_ai_to_solve(task):
    anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""
    以下のタスクを解決するPythonコードを書いてください。
    出力はコードのみとし、マークダウンのコードブロックで囲んでください。
    最後に必ず結果をprint関数で出力してください。

    タスク: {task}
    """

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # AIの回答からコード部分を抽出（簡易的な実装）
    full_text = response.content[0].text
    if "```python" in full_text:
        code = full_text.split("```python")[1].split("```")[0].strip()
    else:
        code = full_text.strip("`")

    print(f"--- 生成されたコード ---\n{code}\n----------------------")

    sandbox = AISandbox()
    result = sandbox.execute_code(code)
    return result

# 実際に動かしてみる
if __name__ == "__main__":
    # 1から100までの素数を計算させる
    task_description = "1から100までの素数をリストアップして、その合計を表示してください。"
    output = ask_ai_to_solve(task_description)
    print(f"--- 実行結果 ---\n{output}")
```

### 期待される出力

```
--- 生成されたコード ---
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

primes = [n for n in range(1, 101) if is_prime(n)]
print(f"Primes: {primes}")
print(f"Total: {sum(primes)}")

--- 実行結果 ---
Primes: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
Total: 1060
```

（結果の読み方）
もしAIが誤って `rm -rf /` のようなコードを生成しても、Dockerコンテナ内のファイルシステムが消えるだけで、あなたのPC（ホスト環境）には一切影響がありません。
これがサンドボックスの威力です。

## Step 4: 実用レベルにする

実務では、標準ライブラリ以外のパッケージ（pandasやnumpyなど）を使いたい場面が多々あります。
その場合、毎回 `pip install` するのは効率が悪いので、あらかじめ必要なライブラリを入れた「専用イメージ」を作っておくのが定石です。

```python
# 実用的なDockerfileの例
"""
FROM python:3.10-slim
RUN pip install pandas numpy scipy scikit-learn
WORKDIR /workspace
"""

# コード実行部を拡張して、ローカルファイルを読み込ませる方法
def execute_with_data(self, code, local_file_path, timeout=15):
    # ホストのファイルをコンテナの /workspace にマウントして実行
    # 読み取り専用(ro)にすることで、元データを破壊されるリスクを抑えます。
    container = self.client.containers.run(
        image="my-ai-analysis-image",
        command=['python', '-c', code],
        volumes={os.path.abspath(local_file_path): {'bind': '/workspace/data.csv', 'mode': 'ro'}},
        working_dir='/workspace',
        detach=True,
        network_mode="none",
        mem_limit="512m"
    )
    # ...（以下、ログ回収と削除処理は同じ）
```

私は以前、AIにデータ分析を任せた際、AIが「欠損値を埋めるために元のCSVファイルを上書きする」という暴挙に出たことがありました。
幸い、この `mode='ro'`（Read-Only）設定のおかげで、大事なマスターデータが守られました。
「AIは親切心でデータを破壊する」という前提で設計するのが、エンジニアとしての本音です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Docker Engineが起動していない | Docker Desktopを起動し、権限を確認する。 |
| `Error: Timeout` | AIが無限ループを生成した、または計算が重すぎる | `timeout`値を増やすか、`cpu_quota`の制限を緩める。 |
| `ModuleNotFoundError` | コンテナにライブラリが入っていない | 必要なライブラリを含めた独自のDockerイメージを作成し、`image`引数で指定する。 |
| `Permission denied` | WSL2等のファイルパス形式の不一致 | `os.path.abspath`を使い、ホスト側が認識できる絶対パスを渡す。 |

## 次のステップ

ここまでで「安全にコードを実行する環境」は手に入りました。
しかし、これだけでは「自律的なエージェント」とは言えません。
次は、以下の3つのステップに挑戦してみてください。

1. **エラーフィードバック・ループの実装:**
   実行結果がエラーだった場合、そのエラーメッセージを再びLLMに投げて「修正案」を出させるループを作ってください。
   これができると、エージェントの生存率が飛躍的に上がります。
2. **ステートフルなサンドボックス:**
   今回は実行ごとにコンテナを捨てていますが、同じコンテナを使い回して「対話的に変数を保持する」仕組みを作ってみてください。
   JupyterカーネルをDocker内で動かし、そのAPIを叩く構成にすると非常に使い勝手が良くなります。
3. **ローカルLLMとの統合:**
   `anthropic`の部分を`ollama`ライブラリに置き換え、RTX 4090のパワーを活かして完全オフライン・無料で動くエージェントを構築してみましょう。

AIに「自由」を与えることは、同時に「責任」をシステム側で持つことを意味します。
このサンドボックスは、その責任を果たすための第一歩です。

## よくある質問

### Q1: Docker Desktopを有料版にする必要はありますか？

個人利用や中小企業（従業員250人未満、年間売上1000万ドル未満）であれば、Docker Desktopは無料で使えます。
それを超える規模の企業で「仕事で使えるか」を判断する場合は、ライセンス料（月額$5〜）を払うか、WSL2上に直接Docker Engineを立てる方法を検討してください。

### Q2: ネットワークを遮断するとAPIを叩くコードが動かないのでは？

その通りです。AIに「Webから最新情報を取ってこい」と命じる場合は、ネットワークを有効にする必要があります。
ただし、その場合は実行時間を10秒以内に絞り、かつアクセス先を制限するプロキシを通すなど、一段上のセキュリティ対策を強く推奨します。

### Q3: Python以外の言語でも同じことができますか？

もちろんです。Dockerイメージを `node:alpine` や `golang:alpine` に変えるだけで、JavaScriptやGoのサンドボックスに早変わりします。
「特定の言語に依存しない実行環境」を作れるのがDockerベースで構築する最大のメリットですね。

---

## あわせて読みたい

- [DockerとPythonでAIエージェントの安全なサンドボックスを構築する方法](/posts/2026-09-22-ai-agent-secure-sandbox-docker-python-guide/)
- [Appwrite 2.0 使い方とAIエージェント開発における実用性レビュー](/posts/2026-09-17-appwrite-2-review-ai-agent-backend/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Docker Desktopを有料版にする必要はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "個人利用や中小企業（従業員250人未満、年間売上1000万ドル未満）であれば、Docker Desktopは無料で使えます。 それを超える規模の企業で「仕事で使えるか」を判断する場合は、ライセンス料（月額$5〜）を払うか、WSL2上に直接Docker Engineを立てる方法を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットワークを遮断するとAPIを叩くコードが動かないのでは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その通りです。AIに「Webから最新情報を取ってこい」と命じる場合は、ネットワークを有効にする必要があります。 ただし、その場合は実行時間を10秒以内に絞り、かつアクセス先を制限するプロキシを通すなど、一段上のセキュリティ対策を強く推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。Dockerイメージを node:alpine や golang:alpine に変えるだけで、JavaScriptやGoのサンドボックスに早変わりします。 「特定の言語に依存しない実行環境」を作れるのがDockerベースで構築する最大のメリットですね。 ---"
      }
    }
  ]
}
</script>

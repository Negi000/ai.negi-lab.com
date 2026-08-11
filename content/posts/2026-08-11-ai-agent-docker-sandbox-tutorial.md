---
title: "DockerでAIエージェント用セキュア実行環境を構築する方法"
date: 2026-08-11T00:00:00+09:00
slug: "ai-agent-docker-sandbox-tutorial"
cover:
  image: "/images/posts/2026-08-11-ai-agent-docker-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "AIエージェント"
  - "サンドボックス"
  - "Docker Python"
  - "コード実行 隔離"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- AIエージェントが生成したPythonコードを、ホストOSから隔離された環境で安全に実行・結果取得するサンドボックスシステム
- Pythonの基礎（関数、例外処理）とDockerの基本的な概念がわかること
- Docker Desktop（またはEngine）がインストールされたPC、OpenAIかAnthropicのAPIキー

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとサンドボックスを同時に回す入門機として最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを実行させる際、最も重要なのは「計算リソースの分離」と「セキュリティ」です。
最低でもメモリは16GB、できれば32GB以上を推奨します。
Dockerコンテナ自体は軽量ですが、複数のエージェントを並列で動かしたり、ローカルLLMと連携させたりすると一気にメモリを消費するためです。

私は現在RTX 4090を2枚挿した自作サーバーで検証していますが、推論と実行環境を分けることで、GPUメモリをLLMに、メインメモリをサンドボックスに割り振る安定した運用ができています。
API料金については、GPT-4oやClaude 3.5 Sonnetを使用する場合、1回の検証で$0.5〜$2程度見積もっておけば十分でしょう。
もしローカルLLM（Llama 3など）を使うのであれば、API料金は無料になりますが、VRAM 12GB以上のGPUがないとレスポンスが遅く、デバッグが苦行になります。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる手段として、クラウド型のサンドボックスAPI（E2BやPistonなど）を使う方法もあります。
しかし、実務での導入を考えると「機密データの取り扱い」と「コスト」が壁になります。
顧客データを外部のサンドボックスに投げるわけにはいきませんし、大量のタスクを回すとAPI利用料も馬鹿になりません。

そこで、自前でDockerベースのサンドボックスを構築するのがベストな選択肢となります。
Docker SDK for Pythonを使えば、コンテナの起動からコードの注入、実行結果の回収、そしてコンテナの破棄までをすべてコードで制御できます。
この方法なら、ネットワークを遮断して完全にオフラインでコードを実行させることも可能で、セキュリティレベルを自在に調整できるのが強みです。

## Step 1: 環境を整える

まずは、サンドボックスの土台となるDockerイメージを作成します。
標準のPythonイメージに、データ分析でよく使うライブラリをプリインストールした専用イメージを準備しましょう。

```bash
# 作業ディレクトリの作成
mkdir agent-sandbox
cd agent-sandbox

# Dockerfileの作成
cat <<EOF > Dockerfile
FROM python:3.11-slim

# セキュリティのため非ルートユーザーを作成
RUN useradd -m sandboxuser
WORKDIR /home/sandboxuser

# 必要最小限のライブラリをインストール
RUN pip install --no-cache-dir pandas numpy matplotlib seaborn

# ユーザーを切り替え
USER sandboxuser

# 実行コマンドを待機状態にする（コンテナを即終了させないため）
CMD ["tail", "-f", "/dev/null"]
EOF

# イメージのビルド
docker build -t ai-agent-sandbox .
```

`python:3.11-slim`を選択したのは、イメージサイズを小さく抑えつつ、実務に必要なライブラリとの互換性を保つためです。
また、`useradd`で非特権ユーザーを作成しているのは、万が一エージェントが「`rm -rf /`」のような破壊的なコードを生成しても、システムへの影響を最小限に抑えるためです。

⚠️ **落とし穴:**
Windows環境のDocker Desktopを使っている場合、WSL2のメモリ割り当て制限により、大きなデータ処理でコンテナが突然落ちることがあります。
`.wslconfig`ファイルでメモリ制限を明示的に広げておくか、処理するデータのサイズを最初は小さくして試してください。

## Step 2: 基本の設定

次に、PythonからこのDockerコンテナを操作するための制御クラスを作成します。
`docker`ライブラリを使用するので、あらかじめインストールしておいてください。

```bash
pip install docker
```

それでは、サンドボックスを管理する`SandboxManager`クラスを実装します。

```python
import docker
import os
import time

class SandboxManager:
    def __init__(self, image_name="ai-agent-sandbox"):
        self.client = docker.from_env()
        self.image_name = image_name
        self.container = None

    def start(self):
        # 既存のコンテナがあれば削除
        self.stop()
        # コンテナの起動（CPUとメモリを制限）
        self.container = self.client.containers.run(
            self.image_name,
            detach=True,
            mem_limit="512m",  # メモリ使用量を512MBに制限
            nano_cpus=1000000000,  # CPU 1コア相当に制限
            network_disabled=True  # 外部ネットワークへのアクセスを禁止
        )
        return self.container.id

    def execute_code(self, code):
        if not self.container:
            raise Exception("コンテナが起動していません。")

        # 実行するコードを一時ファイルとして書き込む（コンテナ内）
        with open("temp_script.py", "w") as f:
            f.write(code)

        # ファイルをコンテナにコピー（簡易的な実装としてcatを使用）
        os.system(f"docker cp temp_script.py {self.container.id}:/home/sandboxuser/script.py")

        # コードの実行
        result = self.container.exec_run("python /home/sandboxuser/script.py")

        # 実行後、スクリプトは削除
        os.remove("temp_script.py")

        return {
            "exit_code": result.exit_code,
            "output": result.output.decode("utf-8")
        }

    def stop(self):
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
            except:
                pass
            self.container = None

# 使用例
if __name__ == "__main__":
    sandbox = SandboxManager()
    sandbox.start()
    print("サンドボックス起動完了")
```

ここで重要なのは`mem_limit`と`network_disabled=True`の設定です。
エージェントが無限ループを書いたり、外部の怪しいサーバーにデータを送信したりするリスクを、インフラレベルで封じ込めています。
実務で使うなら、この制限は「厳しすぎる」くらいから始めるのが正解です。

## Step 3: 動かしてみる

実際にエージェントが生成しそうな「少し複雑な計算」をサンドボックス内で実行させてみましょう。
ここでは、Pandasを使ってダミーデータを集計するコードを想定します。

```python
sandbox = SandboxManager()
sandbox.start()

test_code = """
import pandas as pd
import numpy as np

# ダミーデータの作成
df = pd.DataFrame({
    'A': np.random.randn(100),
    'B': np.random.randn(100)
})

# 集計処理
summary = df.describe()
print(summary)
"""

result = sandbox.execute_code(test_code)

print(f"終了コード: {result['exit_code']}")
print("--- 出力 ---")
print(result['output'])

sandbox.stop()
```

### 期待される出力

```
終了コード: 0
--- 出力 ---
                A           B
count  100.000000  100.000000
mean     0.123456   -0.012345
std      1.012345    0.987654
min     -2.345678   -2.123456
25%     -0.567890   -0.678901
50%      0.234567    0.123456
75%      0.890123    0.789012
max      2.567890    2.345678
```

コンテナ内でPandasが正常に動作し、その標準出力がホスト側のPythonに返ってきていることが確認できます。
もしコードの中で`import os; os.system('rm -rf /')`のような処理が行われても、コンテナ内の非特権ユーザー環境での出来事なので、ホスト側のファイルが消えることはありません。

## Step 4: 実用レベルにする

実務で「使える」レベルにするには、LLMと連携させ、エラーが発生した際に自動で修正（セルフヒーリング）させる仕組みを組み込みます。
以下は、LangChainや単純なAPIコールを使ってエージェントにコードを書かせ、実行結果をフィードバックするループの骨組みです。

```python
import openai

def ask_agent_and_run(prompt, sandbox):
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # 1. LLMにコードを生成させる
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたはPythonコードのみを出力するエンジニアです。マークダウンのコードブロックで囲んでください。"},
            {"role": "user", "content": prompt}
        ]
    )

    raw_content = response.choices[0].message.content
    # コードブロックの抽出（簡易版）
    code = raw_content.split("```python")[1].split("```")[0].strip()

    print(f"実行するコード:\n{code}")

    # 2. サンドボックスで実行
    result = sandbox.execute_code(code)

    # 3. エラーがあればLLMに修正させる（最大2回）
    attempt = 0
    while result["exit_code"] != 0 and attempt < 2:
        print(f"エラー発生。修正を依頼中... (試行 {attempt + 1})")
        error_msg = result["output"]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "コードにエラーがありました。修正してください。"},
                {"role": "user", "content": f"コード:\n{code}\n\nエラー内容:\n{error_msg}"}
            ]
        )
        code = response.choices[0].message.content.split("```python")[1].split("```")[0].strip()
        result = sandbox.execute_code(code)
        attempt += 1

    return result

# 実行
sandbox = SandboxManager()
sandbox.start()
final_result = ask_agent_and_run("1から100までの素数をリストアップして表示して", sandbox)
print(f"最終結果:\n{final_result['output']}")
sandbox.stop()
```

この構成の肝は、`exit_code`を見て「失敗したかどうか」を機械的に判断している点です。
人間がいちいちエラーを見て直すのではなく、サンドボックスの出力をそのままLLMに返すことで、エージェントが自律的にデバッグを行う環境が整います。
これは、データ分析の自動化や、複雑なファイル操作をエージェントに任せる際に非常に強力なパターンとなります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Dockerデーモンが起動していない | Docker Desktopを起動し、権限があるか確認。 |
| `MemoryLimitExceeded` (OOM) | `mem_limit`が小さすぎる | 処理内容に合わせて`1g`や`2g`に調整する。 |
| ライブラリが見つからない | Dockerイメージに未インストール | Dockerfileに`pip install`を追加して再ビルド。 |

## 次のステップ

この記事の内容をマスターしたら、次は「永続化」と「マルチエージェント」に挑戦してみてください。
現在はコードを実行するたびに使い捨てる設定にしていますが、特定のディレクトリをホスト側とマウント（`volumes`設定）することで、エージェントが作成したCSVやグラフ画像を直接取り出すことができるようになります。

また、複数のサンドボックスを立ち上げ、それぞれに異なる役割（データ収集用、分析用、可視化用）を与えて連携させることで、より高度な業務自動化が可能になります。
その際は、各コンテナ間の通信を制限するDockerネットワークの設定を学ぶと、さらにセキュアなシステムが構築できます。
まずは手元で、エージェントにグラフを描かせて自分のPCに保存させるところから始めてみてください。

## よくある質問

### Q1: Docker Desktopを有償版にする必要がありますか？

商用利用（従業員数250人以上または年間売上1000万ドル以上の企業）の場合は有料ライセンスが必要ですが、個人開発や小規模な検証であれば無料のPersonalプランで問題ありません。Linux環境であればDocker Engineを使えばライセンス費用はかかりません。

### Q2: 実行時間が非常に長いコードを途中で止めたい場合は？

`container.exec_run`にはタイムアウト設定がありません。実務では`subprocess`を使ってタイムアウト付きで実行するか、Docker SDKの`params`で`timeout`を指定した低レベルAPIを叩く必要があります。最初は、無限ループを避けるためにLLMへ「必ず終了条件を書いて」と指示するのも手です。

### Q3: Python以外の言語も実行させたいのですが。

Dockerfileを書き換えるだけで対応可能です。例えばNode.jsをベースイメージにすればJavaScriptエージェント用のサンドボックスになります。複数の言語を扱うなら、言語ごとに別々のイメージを作っておき、リクエストに応じて使い分けるマネージャークラスを作ると管理が楽になります。

---

## あわせて読みたい

- [DockerでAIエージェントのコード実行環境を隔離する方法](/posts/2026-07-03-python-ai-agent-docker-sandbox-tutorial/)
- [AIエージェントを安全に実行するサンドボックス環境の構築方法](/posts/2026-06-24-ai-agent-safe-sandbox-e2b-guide/)
- [Suprboxレビュー：AIエージェントのデータ操作を隔離・保護するセキュアなストレージ](/posts/2026-05-12-suprbox-ai-agent-secure-storage-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Docker Desktopを有償版にする必要がありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "商用利用（従業員数250人以上または年間売上1000万ドル以上の企業）の場合は有料ライセンスが必要ですが、個人開発や小規模な検証であれば無料のPersonalプランで問題ありません。Linux環境であればDocker Engineを使えばライセンス費用はかかりません。"
      }
    },
    {
      "@type": "Question",
      "name": "実行時間が非常に長いコードを途中で止めたい場合は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "container.execrunにはタイムアウト設定がありません。実務ではsubprocessを使ってタイムアウト付きで実行するか、Docker SDKのparamsでtimeoutを指定した低レベルAPIを叩く必要があります。最初は、無限ループを避けるためにLLMへ「必ず終了条件を書いて」と指示するのも手です。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語も実行させたいのですが。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerfileを書き換えるだけで対応可能です。例えばNode.jsをベースイメージにすればJavaScriptエージェント用のサンドボックスになります。複数の言語を扱うなら、言語ごとに別々のイメージを作っておき、リクエストに応じて使い分けるマネージャークラスを作ると管理が楽になります。 ---"
      }
    }
  ]
}
</script>

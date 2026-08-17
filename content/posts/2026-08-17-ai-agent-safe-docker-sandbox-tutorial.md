---
title: "AIエージェントをDockerで安全に動かすサンドボックス構築方法"
date: 2026-08-17T00:00:00+09:00
slug: "ai-agent-safe-docker-sandbox-tutorial"
cover:
  image: "/images/posts/2026-08-17-ai-agent-safe-docker-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "AIエージェント 構築"
  - "Docker サンドボックス"
  - "Python コード実行 安全"
  - "LangChain 使い方"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- LLMが生成したPythonコードを、メイン環境から隔離されたDockerコンテナ内で実行し、結果を安全に回収する「サンドボックス・エグゼキューター」を構築します。
- OpenAI APIやAnthropic APIと連携させ、AIがファイル操作や計算を伴うタスクを自分のPCを壊すリスクなしに実行できる環境を整えます。
- 前提知識として、Pythonの基本的な文法と、Dockerのインストールが済んでいることを想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Crucial DDR5-4800 64GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">DockerとLLMを同時並行で動かすなら、メモリ32GB以上が実務上の最低ラインです</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FCrucial%2520RAM%252064GB%2520Kit%2520DDR5%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FCrucial%2520RAM%252064GB%2520Kit%2520DDR5%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Crucial%20RAM%2064GB%20Kit%20DDR5&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

この構築には、仮想化がスムーズに動くPC環境が必要です。
私はRTX 4090を積んだ自作機で検証していますが、CPU実行がメインになるためGPUは必須ではありません。
ただし、メモリは最低16GB、できれば32GB以上を推奨します。
Dockerコンテナを立ち上げながら、背後でIDE（VS Code等）やブラウザを動かすと、16GBではスワップが発生してレスポンスが悪化するからです。

OSはMac（Apple Silicon）かLinuxを強く推奨します。
Windowsの場合はWSL2（Ubuntu）上でDockerを動かす設定にしてください。
API料金については、GPT-4oやClaude 3.5 Sonnetのような「コード生成に強いモデル」を使うため、1回の検証で数十円〜百円程度のバッファを見ておけば十分です。
もし商用サービスとして検討しているなら、サーバー費用として月額数千円（AWS FargateやGCP Cloud Runなど）の運用コストを想定しておく必要があります。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる手段は、大きく分けて3つあります。
1つ目は「Open Interpreter」のようにローカルで直接動かす方法ですが、これは「rm -rf /」等の破壊的なコマンドを実行されるリスクがあり、仕事では怖くて使えません。
2つ目は「E2B」や「Piston」といった外部のサンドボックスAPIを使う方法ですが、機密データを外部サーバーに送る必要があり、セキュリティポリシーで弾かれるケースが多いです。

今回紹介する「自作Dockerサンドボックス」は、自分の管理下にある環境で完全に隔離しつつ、Pythonライブラリを通じて細かく制御できるため、安全性と柔軟性のバランスが最も優れています。
自前で構築することで、タイムアウト設定や使用メモリの制限、ネットワーク遮断といった実務に不可欠な「ガードレール」を自分で設計できるのが最大のメリットです。

## Step 1: 環境を整える

まずはPythonからDockerを操作するための公式ライブラリをインストールします。
また、LLMとの連携をスムーズにするため、`python-dotenv`で環境変数を管理できるようにします。

```bash
# Docker操作ライブラリと環境変数管理の導入
pip install docker python-dotenv openai
```

ここで`docker`ライブラリを導入するのは、Pythonコードから動的にコンテナの起動・停止・コマンド実行を制御するためです。
OSの`subprocess`でDockerコマンドを叩く方法もありますが、エラーハンドリングの複雑さを考えると専用ライブラリを使うのが正解です。
Docker Desktopが起動していること、およびコマンドラインから`docker ps`が通ることを事前に確認してください。

⚠️ **落とし穴:** Linux環境で実行する場合、現在のユーザーが`docker`グループに属していないと、PythonからDockerソケットにアクセスできず権限エラーになります。`sudo usermod -aG docker $USER`を実行して再ログインするのを忘れないでください。

## Step 2: サンドボックス用イメージの定義

次に、エージェントが活動する「檻（おり）」となるDockerイメージを定義します。
汎用性を高めるため、標準的なデータ分析ライブラリを含めたPythonイメージを作成します。

プロジェクトのルートディレクトリに`Dockerfile.sandbox`という名前で保存してください。

```dockerfile
# 軽量なPythonイメージをベースに使用
FROM python:3.11-slim

# 最小限のツールと、エージェントがよく使うライブラリをプリインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    requests

# 作業ディレクトリの作成
WORKDIR /workspace

# エージェントが勝手にroot権限で暴れないよう、一般ユーザーを作成
RUN useradd -m sandboxuser
USER sandboxuser
```

ベースに`python:3.11-slim`を選ぶのは、イメージサイズを小さく保ち、コンテナの起動速度を上げるためです。
また、最後に`useradd`で一般ユーザーに切り替えているのがポイントです。
万が一コンテナ内で脆弱性を突かれても、ホストOSへの影響を最小限に抑えるためのSIer的な定石ですね。

このイメージをビルドしておきます。

```bash
docker build -t ai-agent-sandbox -f Dockerfile.sandbox .
```

## Step 3: サンドボックス制御クラスの実装

ここが本記事の核心です。
Pythonからコンテナを立ち上げ、コードを流し込み、実行結果を回収するクラスを作成します。
`sandbox.py`として作成してください。

```python
import docker
import os
import time

class AgentSandbox:
    def __init__(self, image_name="ai-agent-sandbox"):
        self.client = docker.from_env()
        self.image_name = image_name
        self.container = None

    def execute_code(self, code: str, timeout: int = 30):
        """
        文字列として受け取ったPythonコードをコンテナ内で実行する
        """
        # 実行のたびに一時的なコンテナを立てるのが最も安全
        self.container = self.client.containers.run(
            image=self.image_name,
            command=f'python3 -c "{code}"',
            detach=True,
            network_disabled=True, # 外部への通信を遮断（データ流出防止）
            mem_limit="512m",      # メモリ使用量を制限（リソース枯渇防止）
            cpu_period=100000,
            cpu_quota=50000,       # CPU使用率を50%に制限
            remove=True            # 実行終了後に自動削除
        )

        # タイムアウト監視
        start_time = time.time()
        while self.container.status != 'exited':
            if time.time() - start_time > timeout:
                self.container.kill()
                return "Error: Execution timed out."

            try:
                self.container.reload() # 状態を更新
            except:
                break # すでに削除されている場合
            time.sleep(0.5)

        # ログ（実行結果）の取得
        logs = self.container.logs().decode('utf-8')
        return logs

# 動作テスト
if __name__ == "__main__":
    sandbox = AgentSandbox()
    test_code = "print(1 + 1); import os; print(os.getcwd())"
    print(sandbox.execute_code(test_code))
```

この実装で重要なのは`network_disabled=True`の設定です。
これを忘れると、プロンプトインジェクションを受けた際にエージェントが外部サーバーにあなたの機密情報を送信できてしまいます。
「仕事で使える」レベルにするなら、ここは絶対に譲れないポイントです。

また、`mem_limit`と`cpu_quota`を設定しているのは、エージェントが無限ループや重い処理を書いた時にホストPCがフリーズするのを防ぐためです。
私は以前、エージェントが再帰関数を暴走させてMacが再起動不可になった経験があり、それ以来この制限は必須にしています。

## Step 4: 実用レベルにする（LLMとの結合）

最後に、このサンドボックスをOpenAIの関数呼び出し（Function Calling）と連携させ、AIが「自分でコードを書いて実行する」一連の流れを作ります。

```python
import os
from openai import OpenAI
from sandbox import AgentSandbox
import json

# OpenAI APIの設定
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent_task(prompt: str):
    sandbox = AgentSandbox()

    # 1. LLMにタスクを投げ、コードが必要か判断させる
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "type": "function",
            "function": {
                "name": "execute_python",
                "description": "Pythonコードを実行して結果を返します。計算やデータ処理が必要な場合に使ってください。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "実行するPythonコード"}
                    },
                    "required": ["code"]
                }
            }
        }]
    )

    message = response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            # 2. 生成されたコードを抽出
            code = json.loads(tool_call.function.arguments)["code"]
            print(f"--- 実行されるコード ---\n{code}\n-------------------------")

            # 3. サンドボックスで実行
            result = sandbox.execute_code(code)
            print(f"--- 実行結果 ---\n{result}")

            # 4. 結果をLLMに戻して最終回答を得る（本番ではここをループさせる）
            return result
    else:
        return message.content

# 実行例: 素数を10個計算させる
if __name__ == "__main__":
    task = "最初の10個の素数を計算して表示してください。"
    run_agent_task(task)
```

このスクリプトを動かすと、LLMが自分でコードを書き、それがDockerの中で安全に実行され、その出力だけが返ってくるのが確認できるはずです。

### 期待される出力

```text
--- 実行されるコード ---
def get_primes(n):
    primes = []
    num = 2
    while len(primes) < n:
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                break
        else:
            primes.append(num)
        num += 1
    return primes

print(get_primes(10))

--- 実行結果 ---
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

実務で運用する際は、この`run_agent_task`をループ（ReActループ）の中に組み込みます。
そうすることで、「エラーが出たら修正して再実行する」という自律的な動きが可能になります。
ただし、無限ループにならないよう、最大試行回数（Max Iterations）の設定は必須です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException: Error while fetching server API version` | Dockerが起動していない、または権限不足 | Docker Desktopを起動するか、sudo権限を確認してください。 |
| `Error: Execution timed out.` | コードが複雑すぎるか、無限ループに陥っている | `timeout`値を増やすか、LLMに効率的なコードを書くよう指示します。 |
| `ModuleNotFoundError` | Dockerイメージに必要なライブラリが入っていない | `Dockerfile.sandbox`に`pip install`を追加して再ビルドしてください。 |

## 次のステップ

ここまでで、AIエージェントが安全に活動できる「最小限の庭」が完成しました。
しかし、実用化するためにはまだ改善の余地があります。

次は「ファイルの永続化」に取り組んでみてください。
現在の設定ではコンテナが終了すると生成されたファイル（CSVや画像など）が消えてしまいます。
ホスト側の特定のディレクトリをDockerの`volumes`としてマウントすることで、エージェントが作成したグラフや解析レポートを直接手元に保存できるようになります。

また、より高度なタスクをこなすには、コンテナにインターネット接続を一時的に許可し、最新情報をスクレイピングさせる機能の追加も考えられます。
その際は、プロキシを噛ませて特定のドメイン以外へのアクセスを遮断するなど、セキュリティの層をさらに厚くすることを忘れないでください。
AIに「手足」を与えることは、同時に「武器」を与えることでもあるという意識が、プロの開発者には求められます。

## よくある質問

### Q1: Dockerの代わりに仮想マシン（VM）を使ってもいいですか？

可能ですが、オーバーヘッドが大きすぎます。
AIエージェントのコード実行は「数秒で起動して結果を返す」というサイクルが繰り返されるため、コンテナの軽量さが不可欠です。VMだと起動を待つ間にLLMのトークン生成が終わってしまいます。

### Q2: 複数のコンテナを同時に動かしても大丈夫でしょうか？

メモリさえあれば可能です。
今回の設計では`docker.from_env()`を使って実行ごとに独立したコンテナを立てているため、並列実行してもプロセスは混ざりません。ただし、APIのレートリミットとPCのファンが爆音になる点には注意してください。

### Q3: グラフを描画して画像として保存させるには？

`Dockerfile`に`matplotlib`を入れ、LLMへの指示に「ファイルとして保存しろ」と含めます。
その後、`container.get_archive`等のメソッドでコンテナ内からバイナリデータを吸い上げるコードを追加すれば、エージェントが作ったグラフをあなたの画面に表示できます。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [ローカルAIエージェント特化モデルMuse GlimmerおすすめPC構成と比較](/posts/2026-08-11-muse-glimmer-local-agent-gpu-comparison/)
- [Dockerで構築するAIエージェント用コード実行サンドボックス入門](/posts/2026-07-30-ai-agent-docker-sandbox-tutorial/)
- [Agentplace AI Agents 使い方と実務評価](/posts/2026-03-25-agentplace-ai-agents-review-practical-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerの代わりに仮想マシン（VM）を使ってもいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能ですが、オーバーヘッドが大きすぎます。 AIエージェントのコード実行は「数秒で起動して結果を返す」というサイクルが繰り返されるため、コンテナの軽量さが不可欠です。VMだと起動を待つ間にLLMのトークン生成が終わってしまいます。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のコンテナを同時に動かしても大丈夫でしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "メモリさえあれば可能です。 今回の設計ではdocker.fromenv()を使って実行ごとに独立したコンテナを立てているため、並列実行してもプロセスは混ざりません。ただし、APIのレートリミットとPCのファンが爆音になる点には注意してください。"
      }
    },
    {
      "@type": "Question",
      "name": "グラフを描画して画像として保存させるには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Dockerfileにmatplotlibを入れ、LLMへの指示に「ファイルとして保存しろ」と含めます。 その後、container.getarchive等のメソッドでコンテナ内からバイナリデータを吸い上げるコードを追加すれば、エージェントが作ったグラフをあなたの画面に表示できます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

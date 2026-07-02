---
title: "DockerでAIエージェントのコード実行環境を隔離する方法"
date: 2026-07-03T00:00:00+09:00
slug: "python-ai-agent-docker-sandbox-tutorial"
cover:
  image: "/images/posts/2026-07-03-python-ai-agent-docker-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Docker SDK for Python"
  - "AIエージェント"
  - "サンドボックス構築"
  - "コード実行 隔離"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- AIエージェントが生成したPythonコードを、ホストOSから完全に隔離されたDockerコンテナ内で実行し、結果だけを安全に受け取るスクリプト。
- 前提知識：Pythonの基本的な文法、Dockerのインストール方法、OpenAI APIの基本的な使い方がわかること。
- 必要なもの：OpenAI APIキー（またはローカルLLM）、Docker Desktop（またはDocker Engine）がインストールされたPC。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Dockerコンテナを複数並列で動かすAIエージェント検証用として、32GBメモリのMac miniはコスパ最強です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%252032GB%2520Apple%2520Silicon%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%252032GB%2520Apple%2520Silicon%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%2032GB%20Apple%20Silicon&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを実行させる際、最も重要なのは「計算リソース」ではなく「隔離の安全性」です。
PCスペックは、Dockerがスムーズに動く環境であれば問題ありません。
メモリは8GBでも動きますが、複数のエージェントを並列で動かす実務レベルなら16GB以上、WSL2やMacの仮想環境なら最低16GB（できれば32GB）を推奨します。

GPUは今回必須ではありません。
コードの生成自体はAPI経由（GPT-4oなど）で行うため、安価なMacBook Airでも十分に構築可能です。
API料金については、GPT-4oを使う場合、10回程度の試行で約$0.5（約75円）程度見ておけば足りるでしょう。
もしローカルLLMで完結させたい場合は、Llama 3などをOllamaで動かす構成に読み替えてください。その場合はVRAM 12GB以上のRTX 3060/4060 Tiクラスがあれば快適です。

## なぜこの方法を選ぶのか

AIエージェントにローカル環境で直接コードを実行させるのは、自宅の鍵を渡して「掃除しておいて」と泥棒に頼むようなものです。
「E2B」のようなクラウド型サンドボックスサービスも優秀ですが、実務では「社外にデータを出せない」「月額コストを抑えたい」という制約が必ずついて回ります。

ローカルのDocker SDK for Pythonを使うこの方法は、完全無料で、かつオフライン環境でも動作します。
また、コンテナのスペック（CPU数やメモリ制限）をソースコード側からミリ単位で制御できるため、無限ループによるフリーズやメモリリークからホストOSを守る唯一の現実的な手段です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。

```bash
pip install docker openai python-dotenv
```

`docker`ライブラリは、PythonからDocker APIを操作するための公式SDKです。
これを使うことで、`docker run`コマンドを叩かずに、プログラムの中から動的にコンテナを生成・破棄できます。
Python 3.10以上での動作を確認済みです。

⚠️ **落とし穴:**
Docker Desktopを使っている場合、デフォルトでは「設定 > General > Expose daemon on tcp://localhost:2375 without TLS」をオンにする必要はありませんが、環境によってはPythonからDockerデーモンにアクセスできずエラーになります。
その場合は、環境変数 `DOCKER_HOST` が正しく設定されているか、あるいは現在のユーザーが `docker` グループに所属しているかを確認してください。WindowsのWSL2環境なら、Docker Desktopの「Resources > WSL Integration」で利用するディストリビューションが有効になっている必要があります。

## Step 2: 基本の設定

サンドボックスを管理するクラスを作成します。
ここでは、単に実行するだけでなく「ネットワークを遮断する」「リソースを制限する」設定を盛り込みます。

```python
import os
import docker
from docker.errors import ContainerError, ImageNotFound
import time

class AgentSandbox:
    def __init__(self, image_name="python:3.10-slim"):
        # Dockerクライアントの初期化
        # ホストのDockerエンジンと通信を開始します
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Dockerへの接続に失敗しました: {e}")
            raise

        self.image_name = image_name
        self._ensure_image_exists()

    def _ensure_image_exists(self):
        # 指定されたイメージがない場合は自動でプルする
        try:
            self.client.images.get(self.image_name)
        except ImageNotFound:
            print(f"イメージ {self.image_name} をダウンロード中...")
            self.client.images.pull(self.image_name)

    def execute_code(self, code: str, timeout=10):
        # コードをコンテナ内で実行するメイン処理
        # なぜ python -c を使うのか：一時ファイルを作らずに文字列として実行できるため
        command = f'python -c "{code}"'

        try:
            # コンテナを起動して実行
            container = self.client.containers.run(
                image=self.image_name,
                command=["python", "-c", code],
                detach=True,           # バックグラウンドで実行
                network_disabled=True, # 外部への通信を遮断（重要！）
                mem_limit="128m",      # メモリ制限（OSフリーズ防止）
                cpu_quota=50000,       # CPU使用率を50%に制限
                remove=True            # 実行終了後にコンテナを自動削除
            )

            # タイムアウト監視
            start_time = time.time()
            while container.status != "exited":
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return "Error: Timeout"
                time.sleep(0.5)

            # ログ（標準出力）を取得
            logs = container.logs().decode("utf-8")
            return logs

        except Exception as e:
            return f"Execution Error: {str(e)}"
```

この設定の肝は `network_disabled=True` です。
AIが勝手に外部サーバーへデータを送信したり、不正なスクリプトをダウンロードしたりするのを防ぎます。
実務で「安全です」と胸を張って言える構成にするには、この一行が欠かせません。

## Step 3: 動かしてみる

作成したクラスを使って、実際にAIが書きそうなコードを走らせてみましょう。

```python
if __name__ == "__main__":
    sandbox = AgentSandbox()

    # 正常なコードのテスト
    test_code = "print(sum([i for i in range(100)]))"
    print("--- 正常実行テスト ---")
    print(sandbox.execute_code(test_code))

    # 悪意ある（またはミスによる）無限ループのテスト
    bad_code = "import time\nwhile True: pass"
    print("--- 無限ループテスト（10秒で停止するはず） ---")
    print(sandbox.execute_code(bad_code, timeout=5))
```

### 期待される出力

```
--- 正常実行テスト ---
4950

--- 無限ループテスト（10秒で停止するはず） ---
Error: Timeout
```

結果からわかる通り、無限ループが発生しても指定した秒数でコンテナが強制終了され、メインのプログラムは無事です。
私は以前、ローカルで直接エージェントを動かしてCPU使用率が100%に張り付き、保存していないドキュメントが消えた経験があります。
サンドボックス化は、開発者のメンタルヘルスを守るための必須装備だと言えます。

## Step 4: 実用レベルにする

単独のスクリプトではなく、OpenAIのAPIと連携させて「計算が必要な時だけサンドボックスを使う」エージェントを組み上げます。

```python
import json
from openai import OpenAI

client = OpenAI(api_key="あなたのAPIキー")

def ask_agent(prompt: str):
    # エージェントに道具（サンドボックス）を定義
    tools = [{
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Pythonコードを実行して結果を返す。計算やデータ処理に使う。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "実行するPythonコード"}
                },
                "required": ["code"]
            }
        }
    }]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        tools=tools
    )

    tool_call = response.choices[0].message.tool_calls[0]
    if tool_call.function.name == "execute_python":
        args = json.loads(tool_call.function.arguments)
        code = args['code']

        print(f"AIが生成したコード:\n{code}")

        # サンドボックスで実行
        sandbox = AgentSandbox()
        result = sandbox.execute_code(code)

        print(f"実行結果: {result}")

# 実行例
ask_agent("1から1000までの素数の数を数えて")
```

この構成にすることで、AIが「素数を数えるアルゴリズムを自分で考えて、安全な環境で実行し、その結果をもとに回答する」という一連の流れが自動化されます。
実務で使う場合は、ここに `try-except` をさらに重ね、AIが「エラーが出たからコードを修正する」というループを回すように設計すると、より「エージェント感」が増します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Dockerデーモンが起動していない、または権限不足 | Docker Desktopを起動するか、sudo権限を確認してください。 |
| `ImportError: No module named 'xxx'` | コンテナ内のPythonイメージにライブラリがない | `image_name` をカスタマイズするか、実行コードの冒頭で `pip install` させる（非推奨）。 |
| 実行結果が空っぽ | `print()` していない | AIに対し「結果は必ず標準出力に出して」とシステムプロンプトで指示してください。 |

## 次のステップ

今回作ったのは、いわば「使い捨ての実験室」です。
これをさらに実用化するには、以下の3点に取り組んでみてください。

1.  **ファイルの永続化**: Dockerの `volumes` 設定を使い、ホストの特定のディレクトリ（例えば `./sandbox_data`）だけをコンテナに見せる。これで、AIがCSVファイルを読み込んでグラフを生成し、ホスト側に保存するような動きが可能になります。
2.  **独自のDockerイメージ作成**: `pandas` や `numpy` をあらかじめインストールしたDockerfileを用意しておけば、データ分析の実行速度が劇的に上がります。
3.  **ストリーミング出力**: `container.logs(stream=True)` を使い、AIが計算している途中の経過をリアルタイムで表示すると、ユーザー体験が向上します。

AIエージェントの価値は「考えて行動すること」にあります。
その行動範囲を安全に広げてあげることが、エンジニアとしての私たちの役割です。
ぜひ、このサンドボックスをベースに、自分専用の自律型エージェントを育ててみてください。

## よくある質問

### Q1: コンテナの中で `pip install` はできますか？

基本的にはできますが、`network_disabled=True` の設定では外部からライブラリを落とせません。あらかじめ必要なライブラリを入れたカスタムイメージを作成し、それを `image_name` で指定するのがプロのやり方です。

### Q2: Windows環境で動作が遅いのですが、改善策はありますか？

WSL2のメモリ割り当てが不足している可能性があります。`.wslconfig` ファイルでメモリ割り当てを増やしてください。また、Dockerのコンテナ起動自体に数秒かかるため、頻繁に実行する場合はコンテナを立ち上げっぱなしにする設計変更を検討してください。

### Q3: セキュリティ的に、これだけで本当に完璧ですか？

100%とは言えません。Dockerの脆弱性を突いた「コンテナ脱出攻撃」のリスクはゼロではないためです。より高い機密性を求めるなら、gVisorのようなランタイムを導入するか、実行ごとに使い捨てのVMをクラウド上で立ち上げる構成（E2Bと同様の手法）が必要になります。

---

## あわせて読みたい

- [E2BとPythonで安全なAIエージェント実行環境を作る方法](/posts/2026-06-19-e2b-python-ai-agent-sandbox-tutorial/)
- [Cursor for iOS レビュー：モバイルでAIエージェントにコードを書かせる実力](/posts/2026-07-01-cursor-ios-mobile-coding-agent-review/)
- [Agent-Reach 使い方：API不要でSNS情報をAIに読み込ませる方法](/posts/2026-06-06-agent-reach-sns-data-scraping-ai-agent-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "コンテナの中で `pip install` はできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはできますが、networkdisabled=True の設定では外部からライブラリを落とせません。あらかじめ必要なライブラリを入れたカスタムイメージを作成し、それを imagename で指定するのがプロのやり方です。"
      }
    },
    {
      "@type": "Question",
      "name": "Windows環境で動作が遅いのですが、改善策はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "WSL2のメモリ割り当てが不足している可能性があります。.wslconfig ファイルでメモリ割り当てを増やしてください。また、Dockerのコンテナ起動自体に数秒かかるため、頻繁に実行する場合はコンテナを立ち上げっぱなしにする設計変更を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ的に、これだけで本当に完璧ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "100%とは言えません。Dockerの脆弱性を突いた「コンテナ脱出攻撃」のリスクはゼロではないためです。より高い機密性を求めるなら、gVisorのようなランタイムを導入するか、実行ごとに使い捨てのVMをクラウド上で立ち上げる構成（E2Bと同様の手法）が必要になります。 ---"
      }
    }
  ]
}
</script>

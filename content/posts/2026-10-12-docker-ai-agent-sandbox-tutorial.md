---
title: "AIエージェントの暴走を防ぐDockerサンドボックス構築入門"
date: 2026-10-12T00:00:00+09:00
slug: "docker-ai-agent-sandbox-tutorial"
cover:
  image: "/images/posts/2026-10-12-docker-ai-agent-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Docker"
  - "AI Agent"
  - "サンドボックス"
  - "セキュリティ"
  - "Python"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- LLMが生成したPythonコードを、ホストOSから隔離された環境で実行し、結果だけを安全に受け取るスクリプト
- AIエージェントに「ファイルの削除」や「ネットワーク攻撃」の指示が含まれていても、自身のPCやサーバーを守れる保護環境
- 前提知識：Pythonの基礎（pip操作、クラスの概念）、Dockerの基本用語（イメージ、コンテナ）がわかること
- 必要なもの：Docker Desktop（またはDocker Engine）、OpenAI APIキー（またはClaude APIキー）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMを動かしつつ、サンドボックスを複数回すのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントを動かすだけであれば、特別なGPUは必須ではありません。
CPU 4コア以上、メモリ16GB以上の一般的なPCで十分に動作します。
ただし、エージェントの推論にローカルLLM（Llama 3など）を自前で動かす場合は、VRAM 12GB以上のGPU（RTX 3060 12GBやRTX 4070以上）が欲しくなります。

API料金については、GPT-4oやClaude 3.5 Sonnetを利用する場合、1回の検証（5〜10回のやり取り）で$0.1〜$0.5程度かかります。
安く済ませたいなら、サンドボックスのテスト段階ではGPT-4o miniなどの軽量モデルを使うのが賢明です。
クラウド型のサンドボックス（E2Bなど）を使う選択肢もありますが、今回は「プライバシー」と「カスタマイズ性」を重視し、完全ローカルのDocker環境で構築します。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる際、最も手軽なのはPythonの`exec()`関数をそのまま使うことです。
しかし、これは「目隠しをして見知らぬ他人に家の鍵を渡す」のと同じくらい危険な行為です。
LLMがハルシネーションを起こし、環境変数をすべて外部に送信するコードを書いたり、重要ファイルを削除したりするリスクが常にあります。

他にはVM（仮想マシン）を使う方法もありますが、起動に数十秒かかるため、エージェントのレスポンスとしては実用的ではありません。
Dockerであれば、コンテナの起動は1秒未満（0.5〜0.8秒程度）で済み、リソース制限（CPU使用率、メモリ上限）も容易です。
実務で「仕事に使える」レベルの安全性を担保するには、Dockerベースのサンドボックスが現在のベストプラクティスです。

## Step 1: 環境を整える

まずは、エージェントが活動するための「専用コンテナイメージ」を作成します。
標準のPythonイメージでも動きますが、解析に必要なライブラリをあらかじめ入れておくことで、実行時の待ち時間を減らします。

```dockerfile
# Dockerfile
FROM python:3.11-slim

# セキュリティのため、rootユーザーではなく一般ユーザーで実行させる
RUN useradd -m sandboxuser
WORKDIR /home/sandboxuser

# 解析によく使うライブラリをプリインストール
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    requests

USER sandboxuser
```

このDockerfileを保存し、以下のコマンドでイメージを作成します。

```bash
docker build -t ai-sandbox:v1 .
```

`--no-cache-dir`を付けているのは、イメージサイズを削るためです。
また、`USER sandboxuser`の設定は必須です。
root権限のままコンテナを動かすと、コンテナ脱出（Container Escape）の脆弱性を突かれた際のリスクが跳ね上がります。

⚠️ **落とし穴:** Dockerが起動していないと、この後のPythonスクリプトで`docker.errors.DockerException`が出ます。WSL2やMacのDocker Desktopが「Running」になっていることを必ず確認してください。

## Step 2: 基本の設定

PythonからDockerを操作するために、`docker`ライブラリを使用します。
また、環境変数の管理には`python-dotenv`を使います。

```bash
pip install docker python-dotenv openai
```

次に、サンドボックスを管理するクラスを作成します。

```python
import docker
import os
from dotenv import load_dotenv

load_dotenv()

class AISandbox:
    def __init__(self, image_name="ai-sandbox:v1"):
        self.client = docker.from_env()
        self.image_name = image_name

    def run_code(self, code: str):
        # 実行するコードを一時ファイルとして渡す代わりに
        # dockerの'command'引数で直接pythonに渡す
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command=f'python3 -c "{code}"',
                detach=False,           # 実行完了を待つ
                stdout=True,            # 標準出力を取得
                stderr=True,            # エラー出力を取得
                remove=True,            # 実行後にコンテナを自動削除
                network_disabled=True,  # 外部への通信を遮断（重要！）
                mem_limit="128m",       # メモリ使用量を制限
                nano_cpus=500000000     # CPUを0.5コアに制限
            )
            return container.decode("utf-8")
        except docker.errors.ContainerError as e:
            return e.stderr.decode("utf-8")
```

`network_disabled=True`にしている理由は、LLMが万が一、内部ネットワークのスキャンやAPIキーの外部送信を試みた際、それを物理的に遮断するためです。
もしエージェントにWeb検索などをさせたい場合は、この設定を外すのではなく、特定のプロキシ経由でのみ通信を許可する構成にするのがプロのやり方です。

## Step 3: 動かしてみる

実際に、LLMにコードを生成させ、それをサンドボックスで実行する一連の流れを実装します。

```python
import openai

# APIキーの設定
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_agent(prompt: str):
    system_prompt = """
    あなたはデータ分析の専門家です。
    ユーザーの依頼に対して、Pythonコードのみを出力してください。
    解説は一切不要です。コードは必ず print() で結果を表示するようにしてください。
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# 実行テスト
sandbox = AISandbox()
agent_code = ask_agent("1から100までの素数をリストアップして、その合計を計算して")

print("--- 生成されたコード ---")
print(agent_code)

print("\n--- 実行結果 ---")
result = sandbox.run_code(agent_code)
print(result)
```

### 期待される出力

```
--- 生成されたコード ---
primes = [n for n in range(2, 101) if all(n % i != 0 for i in range(2, int(n**0.5) + 1))]
print(sum(primes))

--- 実行結果 ---
1060
```

ここで重要なのは、`agent_code`の中身がどれだけ無茶苦茶でも、私たちのPC本体には影響が出ないという安心感です。

## Step 4: 実用レベルにする

実務で使うには「エージェントにファイルを渡して処理させ、結果を受け取る」というフローが必要です。
コンテナ内の`/data`ディレクトリを、ホスト側の特定ディレクトリにマウントして共有します。

```python
def run_code_with_data(self, code: str, host_data_dir: str):
    # ホスト側の絶対パスを取得
    abs_path = os.path.abspath(host_data_dir)

    container = self.client.containers.run(
        image=self.image_name,
        command=f'python3 -c "{code}"',
        volumes={abs_path: {'bind': '/home/sandboxuser/data', 'mode': 'rw'}},
        working_dir='/home/sandboxuser/data',
        remove=True,
        network_disabled=True,
        mem_limit="256m"
    )
    return container.decode("utf-8")
```

この際、`host_data_dir`は必ず「エージェント専用の作業フォルダ」を指定してください。
間違ってもプロジェクトのルートディレクトリやデスクトップをマウントしてはいけません。
エージェントが「データを整理します」と言って、マウントされたフォルダの中身を一掃する可能性があるからです。

私は以前、テスト中にエージェントが「ライブラリが足りないからpip installする」というコードを無限ループで回し、ディスク容量を食いつぶした経験があります。
そのため、実運用では`storage_opt={'size': '1G'}`のようなクォータ制限（Dockerのストレージドライバが対応している場合）も検討すべきです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Permission denied` (Docker Socket) | 実行ユーザーにDocker操作権限がない | `sudo usermod -aG docker $USER` を実行して再ログイン |
| `Memory limit reached` | LLMが巨大な配列を作成した | `mem_limit` を増やすか、LLMにメモリ効率の良いコードを書くよう指示 |
| `ModuleNotFoundError` | Dockerイメージに必要なライブラリがない | Dockerfileに `pip install` を追加してビルドし直す |

## 次のステップ

この記事で構築したサンドボックスは、自律型エージェント開発の「最低限のガードレール」です。
これをマスターした後は、以下の発展的な課題に挑戦してみてください。

1. **タイムアウトの実装**: LLMが`while True`のような無限ループコードを書いた場合、コンテナが終了しなくなります。`containers.run`の引数に`timeout`は直接ないので、Python側の`threading`や`subprocess`を組み合わせて、強制終了させる仕組みを自作する必要があります。
2. **OpenAIのCode Interpreter（Assistants API）との比較**: 自分でサンドボックスを持つ最大のメリットは「コスト」と「自由度」です。Assistants APIは1セッション$0.03かかりますが、自前Dockerなら無料です。また、独自の社内ライブラリを組み込むことも可能です。
3. **LangChain / CrewAIとの統合**: `Tool`としてこのサンドボックスを定義し、既存のエージェントフレームワークに組み込んでみましょう。

「AIに仕事を任せる」ということは、その責任を開発者が負うということです。
まずはこのサンドボックスを土台にして、安全に「失敗」できる環境を作り上げてください。

## よくある質問

### Q1: WSL2でDockerを使っていますが、パスの指定でハマります。

WSL2の場合、ホスト側のパスは`/mnt/c/Users/...`のような形式になります。Pythonの`os.path.abspath()`を使えば環境に合わせて変換してくれますが、Docker Desktopの設定で「WSL Integration」が有効になっていることを確認してください。

### Q2: ネットワークを遮断すると `pip install` ができません。

はい、意図的な仕様です。必要なライブラリは、実行時ではなく「Step 1」のDockerfile構築時にすべて入れておきます。これがセキュリティと実行速度を両立させるコツです。どうしても動的に入れたい場合は、プロキシを立てて特定のドメインのみ許可する設定が必要です。

### Q3: GPUをコンテナ内で使わせることはできますか？

可能です。`nvidia-container-toolkit`をインストールし、`docker.from_env().containers.run()`の引数に`device_requests=[docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]`を追加してください。ただし、エージェントがGPUを占有してしまわないよう、リソース制限をより厳格にする必要があります。

---

## あわせて読みたい

- [Suprboxレビュー：AIエージェントのデータ操作を隔離・保護するセキュアなストレージ](/posts/2026-05-12-suprbox-ai-agent-secure-storage-review/)
- [OrgComputers 実行環境の切り出しでAIエージェントの安全性と再現性を担保する](/posts/2026-10-06-orgcomputers-ai-agent-workspace-review/)
- [harness-sdk レビュー：本番用AIエージェントの制御を標準化する](/posts/2026-09-23-harness-sdk-ai-agent-sandbox-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "WSL2でDockerを使っていますが、パスの指定でハマります。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "WSL2の場合、ホスト側のパスは/mnt/c/Users/...のような形式になります。Pythonのos.path.abspath()を使えば環境に合わせて変換してくれますが、Docker Desktopの設定で「WSL Integration」が有効になっていることを確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "ネットワークを遮断すると `pip install` ができません。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、意図的な仕様です。必要なライブラリは、実行時ではなく「Step 1」のDockerfile構築時にすべて入れておきます。これがセキュリティと実行速度を両立させるコツです。どうしても動的に入れたい場合は、プロキシを立てて特定のドメインのみ許可する設定が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUをコンテナ内で使わせることはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。nvidia-container-toolkitをインストールし、docker.fromenv().containers.run()の引数にdevicerequests=[docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]を追加してください。ただし、エージェントがGPUを占有してしまわないよう、リソース制限をより厳格にする必要があります。 ---"
      }
    }
  ]
}
</script>

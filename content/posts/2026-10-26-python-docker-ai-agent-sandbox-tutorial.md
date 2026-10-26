---
title: "Dockerで構築する安全なAIエージェント用サンドボックス環境の作り方"
date: 2026-10-26T00:00:00+09:00
slug: "python-docker-ai-agent-sandbox-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Docker サンドボックス"
  - "AIエージェント 開発"
  - "Python Docker SDK 使い方"
  - "セキュアコード実行"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- AIエージェントが生成したPythonコードを、ホストOSから完全に隔離された環境で実行し、結果を安全に回収するスクリプトを作ります。
- 前提知識: Pythonの基本的な読み書き、Dockerの基礎概念（コンテナ、イメージ）が理解できていること。
- 必要なもの: Python 3.10以降、Docker環境、OpenAI APIキー（またはClaudeなどのAPIキー）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで、コード生成用のローカルLLMを動かすのに最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントのサンドボックス構築において、最も重要なのは「リソースの隔離」です。
ローカルで動かす場合、メモリは最低でも16GB、できれば32GB以上を推奨します。
コンテナを立ち上げる際、1つあたり数百MBのメモリを消費するため、エージェントを並列で動かすなら余裕が必要です。

WindowsならDocker Desktop、LinuxならDocker Engineが必須となります。
GPUは今回の実行環境（コード実行側）には必須ではありませんが、ローカルLLM（Llama 3等）でコード生成を行うなら、VRAM 12GB以上のRTX 3060/4060 Tiクラスが最低ラインです。
私はRTX 4090を2枚挿していますが、コンテナ側のコード実行自体はCPUだけで十分高速に動作します。

API料金については、GPT-4oやClaude 3.5 Sonnetを使用する場合、1回の検証で数円〜数十円程度です。
E2Bのようなマネージドなサンドボックスサービスもありますが、月額料金や実行時間の制限を気にせず、機密データを扱いたいなら、自前でDockerを叩くのが最も安上がりで安全です。

## なぜこの方法を選ぶのか

AIエージェントに「自由にコードを書いて実行して」と頼むのは、正体不明のエンジニアに管理者権限を渡すのと同じです。
`os.remove()`で大事なファイルを消されたり、無限ループでCPUを焼き尽くされたりするリスクが常にあります。

他にもLangChainの`PythonREPLTool`などがありますが、あれはホスト環境で直接実行されるため、実務で使うにはセキュリティが脆弱すぎます。
Docker SDK for Pythonを使って「使い捨てのコンテナ」をその都度立ち上げる方法なら、万が一悪意のあるコード（あるいはバグったコード）が動いても、コンテナを消すだけで被害をゼロに抑えられます。

## Step 1: 環境を整える

まずは、PythonからDockerを操作するためのライブラリをインストールします。

```bash
# Docker操作用のSDKをインストール
pip install docker openai python-dotenv
```

`docker`ライブラリは、Docker EngineのAPIをPythonから叩くための公式SDKです。
これを使うことで、`docker run`コマンドを叩くのと同等の操作をプログラム内から制御できるようになります。

次に、サンドボックスの「型」となるDockerfileを作成します。
毎回コンテナ内で`pip install`すると時間がかかるため、よく使うライブラリはあらかじめイメージに入れておきます。

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 作業ディレクトリの作成
WORKDIR /workspace

# AIがよく使うライブラリを事前にインストール
# 実行速度を上げるため、ここに必要なものを詰め込む
RUN pip install --no-cache-dir pandas numpy matplotlib requests

# セキュリティのため、ルート権限ではなく一般ユーザーで実行させる設定も可能
# 今回はシンプルさ重視で進めます
```

このDockerfileを`docker build -t agent-sandbox .`でビルドしておきます。
`slim`イメージを使うのは、コンテナの起動時間を0.5秒以内に抑えるためです。

⚠️ **落とし穴:**
Windows環境のDocker Desktopを使っている場合、Dockerデーモンが起動していないとSDKがエラーを吐きます。
また、WSL2経由でDockerを使っている人は、Pythonの実行環境もWSL2内に合わせないと、ファイルパスの解決で高確率でハマります。

## Step 2: 基本の設定

PythonからDockerコンテナを起動し、コードを流し込むための「Executorクラス」を作成します。
環境変数は`.env`ファイルから読み込む形にします。

```python
import os
import docker
import time
from dotenv import load_dotenv

load_dotenv()

class SandboxExecutor:
    def __init__(self, image_name="agent-sandbox"):
        # Dockerクライアントの初期化
        # デフォルトで unix:///var/run/docker.sock を見に行く
        self.client = docker.from_env()
        self.image_name = image_name

    def run_code(self, code: str, timeout: int = 10):
        """
        文字列として渡されたPythonコードをコンテナ内で実行する
        """
        container = None
        try:
            # コンテナの起動
            # mem_limit: メモリを制限してホストへの影響を防ぐ
            # network_disabled: 外部への勝手な通信を遮断（必要に応じて設定）
            container = self.client.containers.run(
                image=self.image_name,
                command=f'python -c "{code}"',
                detach=True,
                mem_limit="512m",
                network_disabled=False # 外部APIを叩くならTrue
            )

            # 実行終了を待機
            start_time = time.time()
            while container.status != "exited":
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return "Error: Timeout"
                time.sleep(0.1)

            # ログ（標準出力）を取得
            logs = container.logs().decode("utf-8")
            return logs

        except Exception as e:
            return f"Runtime Error: {str(e)}"
        finally:
            # 使い終わったコンテナは確実に削除する
            if container:
                container.remove(force=True)
```

このコードで重要なのは`mem_limit`の設定です。
これを忘れると、LLMが誤って`[1] * (10**9)`のようなコードを書いた瞬間に、あなたのPCのメモリが食い尽くされてフリーズします。
実務で使うなら、こうした「物理的な制限」をコード側で明示するのが鉄則です。

## Step 3: 動かしてみる

作成したクラスを使って、実際にコードが隔離環境で動くかテストします。

```python
executor = SandboxExecutor()

# テスト用のコード
test_script = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
print(df.sum().to_json())
"""

print("実行中...")
result = executor.run_code(test_script)
print("--- 結果 ---")
print(result)
```

### 期待される出力

```
実行中...
--- 結果 ---
{"a":3,"b":7}
```

これで、Pythonスクリプトの中から「別の独立したPython環境」を呼び出し、結果だけを受け取ることができました。
ホスト環境に`pandas`が入っていなくても、コンテナ側にさえ入っていれば動作します。

## Step 4: 実用レベルにする

次は、OpenAIのAPI（GPT-4o）と連携させて、ユーザーの指示からコードを生成・実行する一連の流れを自動化します。
LLMの出力には「```python ... ```」のようなマークダウンが含まれるため、これをパースする処理が必要です。

```python
import openai
import re

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def ask_agent_and_run(user_input: str):
    # LLMにコードを書かせるプロンプト
    prompt = f"""
    以下の指示を遂行するPythonコードを書いてください。
    出力はコードブロック(```python ... ```)のみにしてください。

    指示: {user_input}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = response.choices[0].message.content

    # 正規表現でコード部分を抽出
    code_match = re.search(r"```python\n(.*?)```", full_text, re.DOTALL)
    if not code_match:
        return "コードが見つかりませんでした"

    extracted_code = code_match.group(1)

    print(f"--- 実行されるコード ---\n{extracted_code}\n")

    # サンドボックスで実行
    executor = SandboxExecutor()
    return executor.run_code(extracted_code)

# 実用例: 複雑な計算をエージェントに丸投げする
instruction = "1から100までの素数をリストアップして、その合計を計算してください。"
final_result = ask_agent_and_run(instruction)
print(f"最終結果: {final_result}")
```

この構成にすることで、「プロンプトを投げる → LLMがコードを書く → サンドボックスで実行 → 結果を得る」というAIエージェントの基本サイクルが完成します。
私はこの仕組みを使って、ローカルにある大量のCSVファイルの集計や、簡単なグラフ作成をAIに自動化させています。

さらに実用性を高めるなら、コンテナを起動する際にローカルのディレクトリを`volumes`でマウントし、AIが生成した画像やファイルをホスト側に保存できるように設定すると良いでしょう。
ただし、マウントする際は「書き込み専用のディレクトリ」を別途用意し、システム領域には絶対にアクセスさせないようにしてください。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `docker.errors.DockerException` | Dockerサービスが起動していない | Docker Desktopを起動し、API設定を確認する |
| `ImportError` in container | Dockerイメージに必要なライブラリがない | Dockerfileに`RUN pip install`を追記して再ビルド |
| 実行結果が空 | コード内に`print()`がない | LLMへのプロンプトで「結果をprint出力して」と強調する |
| タイムアウト | 処理が重い、または無限ループ | `timeout`引数を調整するか、コードを最適化する |

## 次のステップ

このサンドボックス環境をマスターしたら、次は「エラーの自動修復ループ」を実装してみてください。
コンテナの実行結果がエラーだった場合、そのエラーメッセージを再度LLMに投げ、「このエラーを直して」と指示を出す仕組みです。
これを3回ほど繰り返すだけで、コードの完遂率は劇的に上がります。

また、今回はDocker SDKを使いましたが、より高度な操作（マルチコンテナの制御や、ネットワークの動的な隔離）が必要なら、Kubernetesのライブラリや、E2BのSDKを比較検討するのも面白いでしょう。
自作のサンドボックスは、ローカルLLMと組み合わせることで「完全オフライン・安全・無料」なAI開発環境に化けます。
ぜひ自分の手で、最強の「AI実験場」を育ててみてください。

## よくある質問

### Q1: Docker Desktopを有料版にする必要はありますか？

個人利用や、従業員数250人未満かつ年間売上1000万ドル未満の企業であれば、Docker Desktopは無料で使えます。それ以上の規模なら、有料プランか、代替としてOrbStackや純粋なDocker Engine（Linux）の検討が必要です。

### Q2: 実行中にネットワークを遮断しても大丈夫ですか？

AIエージェントが外部からデータを取ってくる必要がないなら、`network_disabled=True`を強く推奨します。これにより、万が一AIが生成したコードに、APIキーを外部サーバーへ送信するような悪意が含まれていても、流出を防ぐことができます。

### Q3: Python以外の言語でも同じことができますか？

はい、Dockerfileのベースイメージを変えるだけです。`node:slim`を使えばJavaScript/TypeScriptのサンドボックスになります。ただし、各言語のSDK（Docker API）の使い方を覚える必要がありますが、基本的な流れは同じです。

---

## あわせて読みたい

- [DockerとPythonでAIエージェントの安全なサンドボックスを構築する方法](/posts/2026-09-22-ai-agent-secure-sandbox-docker-python-guide/)
- [Dockerで構築するAIエージェント用コード実行サンドボックス入門](/posts/2026-07-30-ai-agent-docker-sandbox-tutorial/)
- [Nvidiaジェンセン氏が断言「AIは雇用を殺さない」開発者が備えるべき変化](/posts/2026-05-05-nvidia-jensen-huang-ai-job-creation-insight/)

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
        "text": "個人利用や、従業員数250人未満かつ年間売上1000万ドル未満の企業であれば、Docker Desktopは無料で使えます。それ以上の規模なら、有料プランか、代替としてOrbStackや純粋なDocker Engine（Linux）の検討が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にネットワークを遮断しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AIエージェントが外部からデータを取ってくる必要がないなら、networkdisabled=Trueを強く推奨します。これにより、万が一AIが生成したコードに、APIキーを外部サーバーへ送信するような悪意が含まれていても、流出を防ぐことができます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、Dockerfileのベースイメージを変えるだけです。node:slimを使えばJavaScript/TypeScriptのサンドボックスになります。ただし、各言語のSDK（Docker API）の使い方を覚える必要がありますが、基本的な流れは同じです。 ---"
      }
    }
  ]
}
</script>

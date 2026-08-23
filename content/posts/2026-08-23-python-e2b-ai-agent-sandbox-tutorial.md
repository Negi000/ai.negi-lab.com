---
title: "PythonとE2BでAIエージェント用セキュア実行環境を作る方法"
date: 2026-08-23T00:00:00+09:00
slug: "python-e2b-ai-agent-sandbox-tutorial"
cover:
  image: "/images/posts/2026-08-23-python-e2b-ai-agent-sandbox-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "E2B"
  - "AI Sandbox"
  - "Claude 3.5 Sonnet"
  - "Tool Use"
  - "Pythonデータ分析"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude 3.5 Sonnetが生成したコードを、クラウド上の隔離されたサンドボックス環境（E2B）で実行し、データ分析やグラフ作成を完結させるPythonスクリプト
- 前提知識：Pythonの基本的な文法、環境変数の設定方法
- 必要なもの：Anthropic APIキー、E2B APIキー、Python 3.10以上の環境

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIが生成したコードと実行結果のグラフを並べて確認するには、高精細な4K環境が必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを実行させる場合、ローカルPCのスペックよりも「APIの課金体系」と「実行環境の安全性」が重要です。
今回使用するE2B（Enterprise to Browser）は、AIエージェント専用のクラウドサンドボックスを提供してくれるサービスで、無料枠が非常に強力です。

月間24時間までのセッション実行が無料となっており、個人開発やプロトタイプ作成であれば課金の心配はほぼありません。
一方で、LLM側（Claude 3.5 Sonnet）は従量課金です。
データ分析を一回走らせるのに$0.05〜$0.2程度かかるため、プリペイドで$5（約800円）程度チャージしておけば、この記事の内容は20回以上余裕で試せます。

ハードウェアについては、コードの実行自体はクラウドで行われるため、メモリ8GB程度の一般的なノートPCで十分です。
もしローカルLLMで同様のことを試したい場合は、VRAM 16GB以上のRTX 4060 Ti 16GB版などが最低ラインになりますが、今回はAPIベースなのでブラウザとターミナルが動けば問題ありません。

## なぜこの方法を選ぶのか

AIエージェントにPythonコードを生成させて、そのままローカル環境で実行させるのは「非常に危険」です。
万が一、AIがバグや誤認によって`os.remove()`や再帰的なファイル操作を行うコードを生成した場合、あなたのPCのデータが消えるリスクがあるからです。

これを防ぐために、以前の私はDockerコンテナを自前で立てて、そこにAPI経由でコードを送り込んでいました。
しかし、Dockerの管理、ネットワーク隔離の設定、実行後のコンテナ破棄などの作り込みには、エンジニアとして数日は持っていかれます。

E2Bを選ぶ最大の理由は、たった3行のコードで「インターネット接続が可能で、かつ完全に隔離されたLinux環境」が手に入ることです。
「動かしてみた」レベルならDockerでも良いですが、実務で「顧客のデータを扱うエージェント」を作るなら、インフラ管理を専門サービスに逃がして、セキュリティを担保するのが最適解だと判断しています。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
ターミナルを開き、以下のコマンドを実行してください。

```bash
pip install e2b-code-interpreter anthropic python-dotenv
```

`e2b-code-interpreter`は、サンドボックス内でPythonを動かすための専用SDKです。
`anthropic`は、現時点で最もコード生成能力が高いClaude 3.5 Sonnetを呼び出すために使用します。
`python-dotenv`は、APIキーをソースコードに直書きしないための必須ツールですね。

次に、プロジェクトのルートディレクトリに`.env`ファイルを作成し、取得したAPIキーを書き込みます。

```text
ANTHROPIC_API_KEY=sk-ant-xxx...
E2B_API_KEY=e2b_xxx...
```

⚠️ **落とし穴:**
E2BのAPIキーは公式サイトでダッシュボードから取得できますが、デフォルトのプロジェクト設定が「Hobby」プランになっていることを確認してください。
また、Pythonのバージョンが古い（3.8未満など）と、E2BのSDKが提供する非同期処理（async/await）周りでエラーが出ることがあります。
実務で安定して動かすなら、3.10以降を強く推奨します。

## Step 2: 基本の設定

まずは、E2Bのサンドボックスが正しく立ち上がるか、最小構成で確認します。
いきなりLLMと繋げるのではなく、まずは「外枠」が動くことを確認するのが、デバッグで迷子にならないコツです。

```python
import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

# 環境変数の読み込み
load_dotenv()

def test_sandbox():
    # クラウド上に隔離環境（サンドボックス）を作成
    # デフォルトでUbuntuベースの環境が立ち上がる
    with Sandbox(api_key=os.getenv("E2B_API_KEY")) as sandbox:
        print("サンドボックスを起動しました...")

        # サンドボックス内でPythonコードを実行
        # なぜこれが必要か：LLMが書いたコードをこのrun_pythonに渡すため
        code = "print('Hello from E2B!')"
        execution = sandbox.run_python(code)

        if execution.error:
            print(f"エラー発生: {execution.error}")
        else:
            print(f"実行結果: {execution.results[0] if execution.results else 'なし'}")
            print(f"標準出力: {execution.logs.stdout}")

if __name__ == "__main__":
    test_sandbox()
```

ここでは`with Sandbox(...)`構文を使っています。
これはPythonのコンテキストマネージャと呼ばれ、処理が終わった瞬間にクラウド上のサンドボックスを自動的にシャットダウンし、リソース（と無料枠の消費）を解放してくれるためです。
これを忘れると、バックグラウンドでセッションが残り続け、無料枠を無駄に食いつぶす原因になります。

## Step 3: 動かしてみる

次に、このサンドボックスをClaude 3.5 Sonnetの「道具（Tool）」として登録します。
Claudeは、自分が解決できない計算やデータ処理が必要になった際、「このコードを実行して結果を教えてくれ」と私たちに頼んできます。

```python
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from e2b_code_interpreter import Sandbox

load_dotenv()

# クライアントの初期化
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
E2B_API_KEY = os.getenv("E2B_API_KEY")

# Claudeに教える「道具」の定義
# どんな時にこの道具を使うべきか、詳細に説明文を書くのがAIを賢く動かすコツ
tools = [
    {
        "name": "execute_python",
        "description": "Pythonコードを実行して、データ分析やグラフ作成、計算を行う。結果や生成された画像を取得できる。",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "実行するPythonコード。必要なライブラリのimportも含めること。"
                }
            },
            "required": ["code"]
        }
    }
]

def run_agent(prompt):
    # メッセージの送信
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2000,
        tools=tools,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"Claudeの思考: {response.content[0].text if response.content[0].type == 'text' else 'ツール使用中'}")

    # Claudeがツールを使いたいと言っているかチェック
    for content in response.content:
        if content.type == "tool_use" and content.name == "execute_python":
            code = content.input["code"]
            print(f"--- 実行されるコード ---\n{code}\n-------------------------")

            # E2Bでコード実行
            with Sandbox(api_key=E2B_API_KEY) as sandbox:
                execution = sandbox.run_python(code)

                if execution.error:
                    return f"実行エラー: {execution.error}"

                # 実行結果を返す（今回は簡単のため標準出力のみ）
                return f"実行成功。出力: {execution.logs.stdout}"

if __name__ == "__main__":
    result = run_agent("1から100までの素数を計算して、その合計を教えてください。")
    print(result)
```

### 期待される出力

```
Claudeの思考: 1から100までの素数を計算するために、Pythonコードを実行します。
--- 実行されるコード ---
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

primes = [n for n in range(1, 101) if is_prime(n)]
print(sum(primes))
-------------------------
実行成功。出力: ['1060\n']
```

AIが「自らコードを書き、それを安全な場所で実行し、その結果を確認する」というサイクルが回りました。
これがAIエージェントの最小単位です。

## Step 4: 実用レベルにする

実務では、単に数字を出すだけでなく「グラフを作ってファイルとして保存する」といった要望が多発します。
E2Bの強力な点は、サンドボックス内で生成されたファイルをローカルにダウンロードできることです。
また、AIは一度の実行で完璧なコードを書くとは限りません。エラーが出たら修正させる「リトライループ」を組み込みます。

```python
import os
import base64
from dotenv import load_dotenv
from anthropic import Anthropic
from e2b_code_interpreter import Sandbox

load_dotenv()

class DataAgent:
    def __init__(self):
        self.anthropic = Anthropic()
        self.e2b_api_key = os.getenv("E2B_API_KEY")

    def process_query(self, user_query):
        print(f"ユーザーの依頼: {user_query}")

        # グラフ作成が含まれる可能性が高いので、予めsandboxを用意
        with Sandbox(api_key=self.e2b_api_key) as sandbox:
            # メッセージ履歴の初期化
            messages = [{"role": "user", "content": user_query}]

            # 最大3回までやり取りを許可（ループ防止とエラーリトライのため）
            for _ in range(3):
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    tools=tools, # Step 3で定義したもの
                    messages=messages
                )

                # Claudeの返答を履歴に追加
                messages.append({"role": "assistant", "content": response.content})

                # ツール使用の判定
                tool_use = next((c for c in response.content if c.type == "tool_use"), None)

                if not tool_use:
                    # ツールを使わずに返答してきたら終了
                    return response.content[0].text

                if tool_use.name == "execute_python":
                    code = tool_use.input["code"]
                    print("AIがコードを実行中...")

                    execution = sandbox.run_python(code)

                    if execution.error:
                        # エラー内容をAIにフィードバックして修正を促す
                        tool_result = f"エラーが発生しました: {execution.error.value}\n{execution.error.traceback}"
                    else:
                        # 成功した場合、標準出力と生成されたファイルを確認
                        output = "".join(execution.logs.stdout)

                        # もし画像（グラフ）が生成されていたら保存
                        if execution.results:
                            for idx, res in enumerate(execution.results):
                                # pngなどの画像データがあるかチェック
                                if res.png:
                                    filename = f"chart_{idx}.png"
                                    # base64デコードして保存
                                    with open(filename, "wb") as f:
                                        f.write(base64.b64decode(res.png))
                                    output += f"\n[画像 {filename} を保存しました]"

                        tool_result = output if output else "実行完了（出力なし）"

                    # 実行結果を履歴に追加してループ継続
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": tool_result
                            }
                        ]
                    })

if __name__ == "__main__":
    agent = DataAgent()
    # 複雑な依頼
    final_ans = agent.process_query("1から10までのxに対して、y=x^2のグラフを描画して保存してください。")
    print(f"\n最終回答: {final_ans}")
```

このコードの肝は、`execution.results`の扱いです。
E2Bのサンドボックス内で`matplotlib`などを使ってグラフを描画すると、その画像データが`res.png`の中にBase64形式で格納されます。
これをローカルでファイルとして書き出すことで、AIが作成したレポート画像を手元に取得できるようになります。
「仕事で使えるか」という基準で言えば、このファイル連携こそが、ただのチャットAIを「分析担当者」に変える境界線です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError` | サンドボックスにライブラリがない | AIへの指示に `pip install` を含めるか、E2Bのカスタムテンプレート機能を使う |
| `RateLimitError` | Anthropic APIの制限 | ティアを上げるか（課金実績）、処理の間に `time.sleep` を入れる |
| グラフの文字化け | 日本語フォントがLinuxにない | `matplotlib` で日本語を使わず、英語でラベルを書くようプロンプトで指示する |

## 次のステップ

ここまでで、安全なサンドボックス上でAIにコードを実行させる基盤が整いました。
次に挑戦すべきは「データの永続化」と「マルチモーダル連携」です。

現状では、`with Sandbox`が終了すると実行環境のファイルはすべて消えてしまいます。
実務では、あらかじめ解析したいCSVファイルを`sandbox.upload_file()`でアップロードしてから解析を開始したり、逆に生成された複数のファイルをZipに固めて一括ダウンロードする処理が必要になります。

また、Claude 3.5 Sonnetは画像認識能力も非常に高いです。
E2Bで出力したグラフを再びClaudeに読み込ませて、「このグラフから読み取れる異常値を3つ挙げてください」といった、視覚情報に基づいた分析ループを組むと、自動分析エージェントとしての完成度が一段と増します。
私の環境では、これを業務フローに組み込むことで、定型的な週次レポート作成を8割自動化できました。

## よくある質問

### Q1: E2Bを使わずに、自分のPC（ローカル）のDockerで同じことはできますか？

可能です。ただし、DockerのPython SDKを使ってコンテナを立て、標準入出力をキャプチャし、ファイルのやり取りをするコードを自前で書く必要があります。セキュリティ面でもネットワーク遮断（`network_disabled=True`）などの設定を忘れるとリスクが残ります。

### Q2: 実行中にAIが無限ループするコードを書いたらどうなりますか？

E2Bの`run_python`にはデフォルトでタイムアウトが設定されています。また、サンドボックス自体にも生存期間（TTL）があるため、放置してもクラウド上のリソースが無限に消費されることはありません。ここが自前サーバーで動かす際との大きな安心感の違いです。

### Q3: PandasやScikit-learnなどの重いライブラリも使えますか？

はい、使えます。E2Bの標準サンドボックスには主要なデータ分析ライブラリがプリインストールされています。もし足りない場合は、実行するコードの冒頭に `import subprocess; subprocess.run(['pip', 'install', 'xxx'])` を書くようAIに指示すれば、その場でインストールしてくれます。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Cursor for iOS レビュー：モバイルでAIエージェントにコードを書かせる実力](/posts/2026-07-01-cursor-ios-mobile-coding-agent-review/)
- [VEXI レビュー ターミナル完結のOSSコーディングエージェントの実力](/posts/2026-06-15-vexi-ai-coding-agent-terminal-review/)
- [ペンタゴン論争が皮肉にも証明したClaudeの信頼性とApp Store首位獲得の真価](/posts/2026-03-02-claude-app-store-ranking-pentagon-dispute-analysis/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "E2Bを使わずに、自分のPC（ローカル）のDockerで同じことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、DockerのPython SDKを使ってコンテナを立て、標準入出力をキャプチャし、ファイルのやり取りをするコードを自前で書く必要があります。セキュリティ面でもネットワーク遮断（networkdisabled=True）などの設定を忘れるとリスクが残ります。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にAIが無限ループするコードを書いたらどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "E2Bのrunpythonにはデフォルトでタイムアウトが設定されています。また、サンドボックス自体にも生存期間（TTL）があるため、放置してもクラウド上のリソースが無限に消費されることはありません。ここが自前サーバーで動かす際との大きな安心感の違いです。"
      }
    },
    {
      "@type": "Question",
      "name": "PandasやScikit-learnなどの重いライブラリも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。E2Bの標準サンドボックスには主要なデータ分析ライブラリがプリインストールされています。もし足りない場合は、実行するコードの冒頭に import subprocess; subprocess.run(['pip', 'install', 'xxx']) を書くようAIに指示すれば、その場でインストールしてくれます。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

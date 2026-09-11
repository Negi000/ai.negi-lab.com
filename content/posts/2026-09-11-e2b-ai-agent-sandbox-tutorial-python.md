---
title: "AIエージェント専用サンドボックスE2Bの使い方入門"
date: 2026-09-11T00:00:00+09:00
slug: "e2b-ai-agent-sandbox-tutorial-python"
cover:
  image: "/images/posts/2026-09-11-e2b-ai-agent-sandbox-tutorial-python.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "E2B Code Interpreter"
  - "AI Sandbox"
  - "AIエージェント 安全性"
  - "Python API 使い方"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- AIエージェントが生成したPythonコードを、あなたのPCから完全に隔離されたクラウド上の「砂場（サンドボックス）」で実行し、グラフ画像を取得するシステムを作ります。
- 前提知識：Pythonの基本的な文法がわかり、環境変数（.env）の扱いを知っていること。
- 必要なもの：OpenAI APIキー、E2B APIキー（無料枠あり）、Python 3.10以降の環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Air M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AI開発のフロントエンドとして、静音かつ十分なメモリで快適に動作する</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Air%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Air%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントにコードを書かせて実行させる際、最も怖いのはローカル環境の破壊やファイル流出です。
これを防ぐために「E2B（Elements to Binaries）」という、AIエージェント専用のクラウドサンドボックスを利用します。
E2Bの料金体系は、無料枠（Free Tier）で月間100時間程度のセッション実行が可能です。
有料プランも1インスタンスあたり1分$0.0125（約2円）程度からと非常に安価で、個人開発なら無料枠で十分お釣りが来ます。

ハードウェアについては、コードの実行自体はクラウドで行われるため、あなたのPCに高いGPU性能は不要です。
MacBook Airや一般的なノートPCで問題ありませんが、APIのレスポンスを待機するため、メモリは8GB以上あると開発時にストレスがありません。
私は普段RTX 4090を2枚挿した自作サーバーでLLMを動かしていますが、コード実行の安全性に関しては、ローカルのDockerよりも管理が楽なE2Bに軍配を上げています。

## なぜこの方法を選ぶのか

AIにコードを実行させる手段は、他にも「ローカルのDockerコンテナ」や「LangChainのPythonREPL」があります。
しかし、Dockerを自分で運用すると、ネットワークの隔離設定やリソース制限の管理が非常に手間です。
また、LangChainの標準的なREPLは、うっかり設定を間違えるとホストOSのファイルにアクセスできてしまうリスクが拭えません。

E2Bを選ぶ最大の理由は、SDK一つで「数秒で起動する、外部と遮断されたLinux環境」が手に入り、かつファイルの上書きや取得がAPI経由で完結するからです。
SIer時代、本番環境のデータを扱う際に最も神経を使ったのが「実行環境の汚染」でした。
E2Bはセッションが終われば環境ごと消滅するため、実務でAIエージェントを運用するなら、現状これが最も賢い選択肢だと言えます。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
今回はOpenAIのGPT-4oを頭脳として使い、E2Bをその「実行の手足」として使います。

```bash
# E2BのSDKと、OpenAIを操作するためのライブラリをインストール
pip install e2b-code-interpreter openai python-dotenv
```

`e2b-code-interpreter`は、E2Bが提供している最新のSDKです。
以前は`e2b`という名前でしたが、現在はコード実行に特化したこのパッケージが推奨されています。
Python 3.10以上が必要な理由は、SDK内で使われている型ヒントや非同期処理の仕様に合わせるためです。

⚠️ **落とし穴:**
E2BのAPIキーを取得する際、公式サイトでプロジェクトを作成する必要があります。
キーを作成したらすぐにコピーしてください。一度画面を閉じると二度と表示されません。
私は一度これを忘れて、プロジェクトを3回作り直す羽目になりました。

## Step 2: 基本の設定

APIキーをコードに直書きするのは、GitHubに誤ってプッシュした際のリスクが大きすぎます。
必ず`.env`ファイルを作成し、そこから読み込む形式を徹底しましょう。

まず、カレントディレクトリに`.env`という名前のファイルを作り、以下の内容を書き込みます。

```text
OPENAI_API_KEY=sk-xxxx...
E2B_API_KEY=e2b_xxxx...
```

次に、Pythonスクリプトの冒頭でこれらを読み込みます。

```python
import os
from dotenv import load_dotenv
from openai import OpenAI
from e2b_code_interpreter import Sandbox

# .envファイルから環境変数を読み込む
load_dotenv()

# APIキーの存在チェック。これがないと後のエラーが分かりにくくなる
openai_key = os.getenv("OPENAI_API_KEY")
e2b_key = os.getenv("E2B_API_KEY")

if not openai_key or not e2b_key:
    raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")

client = OpenAI(api_key=openai_key)
```

「なぜ存在チェックを入れるのか」と思うかもしれませんが、大規模な開発になると、環境変数の読み込み失敗は原因の特定に時間がかかります。
最初に明示的にエラーを出すのが、SIer流の「ハマらないコード」の書き方です。

## Step 3: 動かしてみる

まずはAIを使わず、E2Bのサンドボックスが正しく動くか、最小限のコードで確認します。
クラウド上にLinuxコンテナが立ち上がり、Pythonコードが実行される感覚を掴んでください。

```python
# サンドボックスを起動
with Sandbox(api_key=e2b_key) as sandbox:
    # クラウド上のPythonで実行したいコードを書く
    code = "print('Hello from E2B Sandbox!')"

    # コードを実行
    execution = sandbox.run_code(code)

    # 実行結果を表示
    print(execution.logs.stdout)
```

### 期待される出力

```
['Hello from E2B Sandbox!']
```

この時、裏側ではAWSやGCPのようなクラウド環境のどこかで、あなた専用の小さなコンテナが一瞬で立ち上がっています。
`with`構文を使っているのは、実行が終わった瞬間にコンテナを確実にシャットダウン（削除）するためです。
これを忘れると、セッションが残り続けて無料枠を無駄に消費する原因になります。

## Step 4: 実用レベルにする

いよいよAIエージェントに「データ分析をしてグラフを作成する」というタスクを投げます。
AIに「コードを生成」させ、そのコードを「サンドボックスで実行」し、生成された「画像ファイルをローカルに保存」する流れを実装します。

```python
import base64

def run_ai_analysis(user_query):
    # 1. AIにコードを書かせる
    # ここでは「Matplotlibを使ってサイン波のグラフを書き、'chart.png'として保存するコード」を生成させます
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは優秀なデータサイエンティストです。Pythonコードのみを出力し、markdownの装飾（```python）は含めないでください。"},
            {"role": "user", "content": f"{user_query}。ファイル名は'chart.png'として保存してください。"}
        ]
    )

    generated_code = response.choices[0].message.content
    print("--- 生成されたコード ---")
    print(generated_code)
    print("------------------------")

    # 2. E2Bサンドボックスで実行
    with Sandbox(api_key=e2b_key) as sandbox:
        # AIが生成したコードを実行
        execution = sandbox.run_code(generated_code)

        # エラーがあれば出力
        if execution.error:
            print(f"実行エラー: {execution.error.value}")
            print(execution.error.traceback)
            return

        # 3. 生成されたファイルをダウンロード
        # サンドボックス内の '/home/user/chart.png' を読み出す
        try:
            # list_filesでファイルが存在するか確認する癖をつけるとデバッグが捗る
            files = sandbox.files.list("/home/user")
            print(f"生成されたファイル一覧: {[f.name for f in files]}")

            # バイナリとしてファイルを読み込み
            file_content = sandbox.files.read("/home/user/chart.png", format="binary")

            with open("output_chart.png", "wb") as f:
                f.write(file_content)

            print("グラフの保存に成功しました: output_chart.png")

        except Exception as e:
            print(f"ファイル取得失敗: {e}")

# 実行
run_ai_analysis("0から10までのサイン波のグラフを描画して")
```

実務でこのコードを運用する際、最も重要なのは「AIが生成したコードをそのまま信じない」ことです。
E2Bを使うことで、万が一AIが`os.system('rm -rf /')`のような破壊的なコードを生成しても、被害はその使い捨てコンテナ内だけに限定されます。
また、`format="binary"`を指定してファイルを読み出す点は重要です。
画像データはテキストとして読み込むと破損するため、必ずバイナリ形式を選択してください。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Sandbox` not found | ライブラリが古い、または名称変更 | `pip install e2b-code-interpreter` を使用しているか確認。 |
| Timeout Error | コードの実行時間が長すぎる | `sandbox.run_code(code, timeout=60)` のように制限時間を延ばす。 |
| No such file or directory | AIが違うパスに保存した | `sandbox.files.list()` でファイル名と場所を確認する。 |

## 次のステップ

ここまでで、安全なAIエージェントの「実行基盤」が手に入りました。
次に挑戦すべきは、このサンドボックスに「あなたの持っているCSVデータ」をアップロードして分析させることです。
`sandbox.files.write("data.csv", open("my_data.csv", "rb"))`を使うことで、ローカルのデータを安全にサンドボックスへ送り込めます。

さらに発展させるなら、LangChainやLlamaIndexといったフレームワークの「Tool」として、このE2Bを組み込んでみてください。
「ネットで最新の株価を検索し、その推移をサンドボックスでグラフ化して、PDFレポートにまとめる」といった一連の業務自動化エージェントが、驚くほど簡単に作れるようになります。
AIに自由奔放にコードを書かせる楽しさと、鉄壁のセキュリティを両立させることが、実務でAIを使いこなすための第一歩です。

## よくある質問

### Q1: Dockerをローカルで動かすのと比べて、コスト以外にメリットはありますか？

ネットワーク隔離がデフォルトで強力な点です。
ローカルDockerだと、設定を誤るとホストのポートを叩かれたり、ローカルネットワーク内の他のマシンをスキャンされたりするリスクがありますが、E2Bはデフォルトで外部インターネット以外へのアクセスが厳しく制限されています。

### Q2: 実行できるライブラリに制限はありますか？

E2Bの標準テンプレートには、pandas, matplotlib, numpy, scipyなどの主要なデータサイエンス系ライブラリが最初からインストールされています。
もし独自のライブラリが必要な場合は、`sandbox.commands.run("pip install custom-lib")`でその場でインストール可能です。

### Q3: 日本語のフォントがグラフで文字化けしてしまいます。

これはLinux環境共通の課題です。サンドボックスには日本語フォントが入っていないため、グラフを描画する際は「Japanize-matplotlib」をpipでインストールするか、AIに「英語でラベルを書いて」と指示するのが一番手っ取り早い解決策です。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [GLM-5.3-Flash使い方入門：ローカル環境で爆速推論を実現する最短手順](/posts/2026-09-01-glm-5-3-flash-python-tutorial-guide/)
- [PythonとE2BでAIエージェント用セキュア実行環境を作る方法](/posts/2026-08-23-python-e2b-ai-agent-sandbox-tutorial/)
- [InstaVM レビュー：AIエージェントに「安全な肉体」を与える高速サンドボックス環境](/posts/2026-05-22-instavm-review-ai-agent-sandbox/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Dockerをローカルで動かすのと比べて、コスト以外にメリットはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ネットワーク隔離がデフォルトで強力な点です。 ローカルDockerだと、設定を誤るとホストのポートを叩かれたり、ローカルネットワーク内の他のマシンをスキャンされたりするリスクがありますが、E2Bはデフォルトで外部インターネット以外へのアクセスが厳しく制限されています。"
      }
    },
    {
      "@type": "Question",
      "name": "実行できるライブラリに制限はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "E2Bの標準テンプレートには、pandas, matplotlib, numpy, scipyなどの主要なデータサイエンス系ライブラリが最初からインストールされています。 もし独自のライブラリが必要な場合は、sandbox.commands.run(\"pip install custom-lib\")でその場でインストール可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のフォントがグラフで文字化けしてしまいます。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "これはLinux環境共通の課題です。サンドボックスには日本語フォントが入っていないため、グラフを描画する際は「Japanize-matplotlib」をpipでインストールするか、AIに「英語でラベルを書いて」と指示するのが一番手っ取り早い解決策です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

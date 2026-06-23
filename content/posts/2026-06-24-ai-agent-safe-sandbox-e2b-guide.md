---
title: "AIエージェントを安全に実行するサンドボックス環境の構築方法"
date: 2026-06-24T00:00:00+09:00
slug: "ai-agent-safe-sandbox-e2b-guide"
cover:
  image: "/images/posts/2026-06-24-ai-agent-safe-sandbox-e2b-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "E2B"
  - "AIエージェント"
  - "サンドボックス"
  - "Python"
  - "セキュリティ"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

AIエージェントが生成したPythonコードを、メインシステムから完全に隔離された環境で実行し、安全にグラフ作成やデータ分析の結果を受け取る仕組みを構築します。
具体的には、E2B（Execution for AI Agents）というSDKを利用し、数秒で起動するMicroVM（軽量な仮想マシン）上でコードを実行するPythonスクリプトを作成します。

前提知識：
- Pythonの基本的な文法がわかること
- ターミナル（コマンドプロンプト）の操作に慣れていること
- OpenAIやAnthropicのAPIを一度でも使ったことがあること

必要なもの：
- Python 3.10以上
- E2B API Key（無料枠あり）
- OpenAI API Key または Anthropic API Key
- VS Codeなどのエディタ

## 先に確認するスペック・料金

AIエージェントにコードを実行させる際、自分のPC上で直接実行するのは「正気の沙汰ではない」と断言します。
生成AIは時として、OSを破壊するコマンドや、ファイルを全削除するコードを出力する可能性があるからです。

そこで必要になるのがサンドボックスですが、自前でDockerをセキュアに構成するのは非常に手間がかかります。
ポート開放の制限、リソースの制限、ネットワークの遮断など、考慮すべきセキュリティホールが多すぎるためです。

今回使用する「E2B」は、AIエージェント専用のクラウドサンドボックスを提供しており、初期費用は0円です。
無料枠（Free Tier）で月間120時間程度の実行が可能なため、個人開発やプロトタイプ作成なら課金の必要はありません。

ローカル環境で完結させたい場合は、RTX 3060（12GB）以上のVRAMを積んだPCでDockerコンテナを立てる方法もありますが、今回は「実務で即使える」ことを優先し、環境構築のオーバーヘッドが最も低いE2Bを採用します。

## なぜこの方法を選ぶのか

AIエージェントのコード実行環境として、真っ先に思い浮かぶのは「Dockerコンテナ」でしょう。
しかし、DockerをAIエージェント向けに安全に運用するには、コンテナの特権昇格対策やメモリ制限、実行時間の監視など、インフラエンジニア並みの設定が求められます。

一方、E2Bのような「MicroVM」ベースのサービスは、起動時間が約1秒と高速でありながら、各実行環境がハードウェアレベルで完全に隔離されています。
万が一エージェントが無限ループに陥ったり、悪意のあるライブラリをインストールしようとしたりしても、サンドボックスごと破棄すればメイン環境への影響はゼロです。

「自分のローカルPCを壊したくないが、ChatGPTのCode Interpreterのような自由度が欲しい」というニーズに対して、現状この構成が最もコストパフォーマンスと安全性のバランスが取れています。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
今回はサンドボックス操作用の `e2b_code_interpreter` と、AIモデルを呼び出すための `langchain` 関連ライブラリを組み合わせて使用します。

```bash
# 仮想環境を作成して有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なパッケージを一括インストール
pip install e2b_code_interpreter langchain-openai python-dotenv
```

`e2b_code_interpreter` は、以前の `e2b` SDKよりもコード実行に特化した新しいパッケージです。
グラフ（matplotlib）の出力などを自動でバイナリデータとして受け取れる機能があるため、こちらを選択しています。

次に、環境変数を管理するための `.env` ファイルをプロジェクトのルートディレクトリに作成してください。

```text
E2B_API_KEY=your_e2b_api_key
OPENAI_API_KEY=your_openai_api_key
```

⚠️ **落とし穴:**
E2BのAPIキーは公式サイト（e2b.dev）でサインアップ後、ダッシュボードから取得する必要があります。
これを設定し忘れると、実行時に `Authentication Error` で止まります。
また、`.env` ファイルは必ず `.gitignore` に追加してください。GitHubにAPIキーを流出させるのは、この業界で最も避けたい「あるある」の失敗です。

## Step 2: 基本の設定

まずは、AIを介さずに「サンドボックスが正しく動くか」だけを確認する最小構成のコードを書きます。
いきなりAIと連携させると、動かなかった時に「AIの指示が悪いのか、環境が悪いのか」の切り分けができなくなるからです。

```python
import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

# .envからキーを読み込み
load_dotenv()

def test_sandbox():
    # サンドボックスのインスタンスを作成
    # この時点でクラウド上に軽量なVMが立ち上がります
    with Sandbox() as sandbox:
        print("サンドボックスを起動しました。")

        # Pythonコードを実行
        # なぜ exec ではなく run_python なのか：
        # 出力結果やエラー、作成されたファイルを構造化データとして受け取るためです
        execution = sandbox.run_python("print('Hello from Sandbox!')")

        # 実行結果を表示
        if execution.error:
            print(f"エラー発生: {execution.error}")
        else:
            print(f"出力: {execution.results[0] if execution.results else '出力なし'}")
            print(f"標準出力: {execution.logs.stdout}")

if __name__ == "__main__":
    test_sandbox()
```

このコードのポイントは `with Sandbox() as sandbox:` というコンテキストマネージャを使っている点です。
処理が終わった後に自動的にサンドボックスを破棄してくれるため、APIの接続時間を無駄に消費せず、リソースの消し忘れを防げます。

## Step 3: 動かしてみる

上記のスクリプトを実行して、以下の出力を確認してください。

### 期待される出力

```text
サンドボックスを起動しました。
出力: Hello from Sandbox!
標準出力: ['Hello from Sandbox!']
```

もしここでエラーが出る場合、多くはネットワーク設定かAPIキーの不備です。
プロキシ環境下で作業している場合は、E2Bの通信がブロックされていないか確認してください。

ここで「出力」と「標準出力」が分かれている理由に注目してください。
`run_python` は、最後に評価された式の値（Jupyter Notebookの挙動に近い）を `results` に格納し、`print()` 関数による出力を `logs.stdout` に格納します。
この仕様のおかげで、AIエージェントが書いたコードの「計算結果」と「ログ」を明確に区別して処理できます。

## Step 4: 実用レベルにする

いよいよ、AIエージェントにコードを書かせ、それをサンドボックスで実行する実用的なスクリプトを作成します。
ここでは「ユーザーがアップロードしたデータの統計を取り、グラフを作成する」というタスクを想定します。

```python
import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from e2b_code_interpreter import Sandbox

load_dotenv()
client = OpenAI()

def run_ai_agent(user_prompt: str):
    # 1. AIにコードを生成させる
    # システムプロンプトで「必ずPythonコードだけを出し、グラフは 'chart.png' に保存しろ」と指示するのがコツです
    system_prompt = """
    あなたは優秀なデータサイエンティストです。
    ユーザーの依頼に対し、Pythonコードを生成して解決してください。

    【ルール】
    - matplotlibなどのグラフ作成時は必ず 'chart.png' という名前で保存すること。
    - 必要なライブラリ（pandas等）はコード内で import すること。
    - 回答はPythonコードのみを出力し、解説は含めないでください。
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    code = response.choices[0].message.content.strip()
    # Markdownのコードブロック（```python ... ```）を除去する処理
    code = code.replace("```python", "").replace("```", "").strip()

    print(f"--- 生成されたコード ---\n{code}\n-----------------------")

    # 2. サンドボックスで実行
    with Sandbox() as sandbox:
        execution = sandbox.run_python(code)

        if execution.error:
            print(f"実行エラー: {execution.error}")
            return

        # 3. 生成されたファイル（グラフ）を回収
        # AIが作成した画像ファイルをバイナリとして読み出します
        try:
            # chart.pngを探す
            files = sandbox.files.list("/")
            if "chart.png" in [f.name for f in files]:
                chart_data = sandbox.files.read("chart.png", format="binary")
                with open("output_chart.png", "wb") as f:
                    f.write(chart_data)
                print("グラフを 'output_chart.png' として保存しました。")
        except Exception as e:
            print(f"ファイル回収中にエラー: {e}")

        # 標準出力の表示
        for log in execution.logs.stdout:
            print(f"LOG: {log}")

if __name__ == "__main__":
    prompt = "1から10までの数値の2乗を計算し、その折れ線グラフを作成して。データの一覧も表示して。"
    run_ai_agent(prompt)
```

このコードでは、以下の3つの実務的な工夫を入れています。

1. **プロンプトの厳格化**: AIが余計な解説文を混ぜるとコード実行が失敗するため、システムプロンプトで「コードのみ」を強制しています。
2. **ファイルパスの固定**: AIに「ファイル名は自由にして」と頼むと、あとでプログラムから探し出すのが困難になります。`chart.png` という固定名を使わせるのが運用上の定石です。
3. **成果物の回収**: サンドボックスは処理が終わると消滅します。必要な画像やCSVは、インスタンスが消える前に `sandbox.files.read` でホスト側にコピーする必要があります。

⚠️ **落とし穴:**
AIが勝手にライブラリをインストールしようとすると時間がかかり、タイムアウトの原因になります。
E2Bのデフォルト環境には `pandas`, `numpy`, `matplotlib` などの主要ライブラリがプリインストールされているので、それらを使うよう誘導するのがスムーズです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError` | サンドボックス内にライブラリがない | `sandbox.run_python("!pip install ...")` で入れるか、標準環境にあるものを使うようプロンプトを調整する |
| `Sandbox timed out` | 処理が重すぎるか無限ループ | `Sandbox(timeout=60)` のように引数で実行制限時間を延ばす（ただし課金に注意） |
| `API Key not found` | 環境変数が読み込めていない | `load_dotenv()` を呼ぶタイミングが `os.getenv` より後になっていないか確認 |

## 次のステップ

ここまでで「AIにコードを書かせ、安全な場所で実行し、結果を受け取る」というエージェントの最小コアが完成しました。
実務でこれを活用するためには、さらに以下の3点に取り組むのがおすすめです。

1. **マルチターン対話でのエラー修正**:
実行エラーが起きた際、そのエラー内容を再度AIに投げ、「このエラーを修正したコードを再生成して」とループさせる仕組み（自己修復機能）を作ってみてください。これだけでタスク成功率が劇的に上がります。

2. **ローカルファイルのアップロード**:
`sandbox.files.write()` を使えば、ローカルにあるCSVファイルをサンドボックスに送り込めます。これを組み込めば「自社の売上データをAIに分析させる」といった業務自動化ツールへ進化します。

3. **LangChainツールとしての統合**:
今回の処理をLangChainの `Tool` として定義すれば、AgentExecutorなどの既存フレームワークに組み込めます。他のAPI（検索など）と組み合わせることで、より複雑な推論が可能になります。

AIエージェントの可能性は、この「実行環境」の自由度に比例します。
安全な砂場を手に入れた今、どんどん複雑な命令をAIに投げてみてください。

## よくある質問

### Q1: Docker Desktopをローカルで動かすのと何が違いますか？

E2Bは内部でMicroVM（Firecracker等）を使用しており、Dockerよりもプロセスの隔離レベルが高いです。また、クラウド上で実行されるため、万が一リソースを食いつぶすようなコードが走っても、あなたのPCの動作が重くなることはありません。

### Q2: 実行時間はどのくらいかかりますか？

サンドボックスの起動に約1〜2秒、コードの実行は内容によりますが数秒程度です。OpenAIのAPIレスポンスを待つ時間を含めても、1つのタスクに10秒〜20秒程度で結果が返ってきます。

### Q3: グラフ以外のファイルも取得できますか？

はい、可能です。`sandbox.files.list()` でディレクトリ内を確認し、CSVやテキストファイルなど、どんな形式でもバイナリまたは文字列として読み取ることができます。AIに「分析結果をCSVで出力して」と指示するのも有効な活用法です。

---
### メタデータ

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM環境とサンドボックスを併用するのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Suprboxレビュー：AIエージェントのデータ操作を隔離・保護するセキュアなストレージ](/posts/2026-05-12-suprbox-ai-agent-secure-storage-review/)
- [E2BとPythonで安全なAIエージェント実行環境を作る方法](/posts/2026-06-19-e2b-python-ai-agent-sandbox-tutorial/)
- [DockerでAIエージェント専用サンドボックスを構築してコード実行を安全にする方法](/posts/2026-06-15-ai-agent-docker-sandbox-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Docker Desktopをローカルで動かすのと何が違いますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "E2Bは内部でMicroVM（Firecracker等）を使用しており、Dockerよりもプロセスの隔離レベルが高いです。また、クラウド上で実行されるため、万が一リソースを食いつぶすようなコードが走っても、あなたのPCの動作が重くなることはありません。"
      }
    },
    {
      "@type": "Question",
      "name": "実行時間はどのくらいかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "サンドボックスの起動に約1〜2秒、コードの実行は内容によりますが数秒程度です。OpenAIのAPIレスポンスを待つ時間を含めても、1つのタスクに10秒〜20秒程度で結果が返ってきます。"
      }
    },
    {
      "@type": "Question",
      "name": "グラフ以外のファイルも取得できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、可能です。sandbox.files.list() でディレクトリ内を確認し、CSVやテキストファイルなど、どんな形式でもバイナリまたは文字列として読み取ることができます。AIに「分析結果をCSVで出力して」と指示するのも有効な活用法です。 ---"
      }
    }
  ]
}
</script>

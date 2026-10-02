---
title: "AIエージェントを安全に動かすE2Bサンドボックス構築ガイド"
date: 2026-10-03T00:00:00+09:00
slug: "ai-agent-safe-sandbox-e2b-tutorial"
cover:
  image: "/images/posts/2026-10-03-ai-agent-safe-sandbox-e2b-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "E2B"
  - "AIエージェント"
  - "サンドボックス"
  - "Python"
  - "Code Interpreter"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- GPT-4oなどのLLMが生成したコードを、あなたのPCから完全に隔離されたクラウド上の仮想環境（サンドボックス）で安全に実行し、結果（グラフ画像や計算結果）を受け取るPythonスクリプトを作ります。
- LLMが「ファイルを削除する」「OSの設定を書き換える」といったリスクをゼロにし、実務でAIエージェントを運用するための必須基盤を構築します。
- 前提知識：Pythonの基本的な文法（変数、関数、pip）がわかること、OpenAI APIの使用経験があること。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとサンドボックスを並行稼働させる入門機として最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

AIエージェントをローカル環境で直接動かすのは、私に言わせれば「防弾チョッキなしで戦場に行く」ようなものです。
特に、ファイル操作やシェルコマンド実行権限をLLMに与える場合、バグやプロンプトインジェクション一つでPCが初期化されるリスクがあります。

今回のガイドでは、クラウド型サンドボックス「E2B」を使用します。
E2Bは、Firecrackerという軽量VM技術を使い、実行ごとに使い捨ての隔離環境を0.5秒以内に立ち上げてくれるサービスです。

必要な料金とスペックは以下の通りです。
- **E2B料金:** 月間100セッション（実行）までは無料、それ以上は従量課金ですが、個人開発なら無料枠で十分です。
- **PCスペック:** CPU/メモリ負荷はクラウド側が持つため、エントリークラスのMacBook Airや古いWindows機でも全く問題ありません。
- **API料金:** OpenAIのGPT-4o（またはClaude 3.5 Sonnet）のAPI利用料がかかります。1回のリサーチで数円〜数十円程度です。

もし「ローカルLLMを自分のマシンでぶん回して、サンドボックスも自前で構築したい」というこだわり派なら、RTX 4060 Ti 16GB以上のGPUを積んだPCでDockerを立てるのが最低ラインですね。
ただ、今回は「仕事で即使える」ことを重視し、環境構築のダルさを排除したE2B構成を選びました。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる手段は、大きく分けて3つあります。
1. **ローカル直接実行:** 自分のPCで実行。最も危険で、二度とやりたくありません。
2. **Docker環境:** 隔離はされていますが、ホストOSへのマウント設定をミスると穴が開きます。また、ネットワーク制限の設定が面倒です。
3. **E2B (Execution to Business):** API経由でMicroVMを借りる方法。

私はかつて、自前のDocker環境で動かしていたエージェントが、無限ループで巨大なログファイルを生成し続け、SSDの空き容量を数分でゼロにした苦い経験があります。
E2Bなら、セッションごとに計算リソースもタイムアウトも厳格に管理されており、何かあっても「セッションを閉じる」だけで全てが消滅します。
「コードインタープリター機能を自作アプリに組み込みたい」なら、現時点でこれ以上の選択肢はありません。

## Step 1: 環境を整える

まずは、必要なライブラリをインストールします。
Python 3.9以上が必要です。私はPython 3.11で検証しています。

```bash
# E2BのSDKと、OpenAI APIを叩くためのライブラリをインストール
pip install e2b_code_interpreter openai python-dotenv
```

各ライブラリの役割を説明しておきます。
- `e2b_code_interpreter`: クラウド上に隔離されたPython実行環境（Jupyter Kernelのようなもの）を制御するためのメインツールです。
- `openai`: LLM（GPT-4o）にコードを書かせるために使います。
- `python-dotenv`: APIキーをソースコードに直書きしないための、実務における「最低限のマナー」用です。

⚠️ **落とし穴:**
Windowsユーザーの場合、環境変数設定後にコマンドプロンプトを再起動しないと、インストールしたライブラリが認識されないことがあります。
また、Pythonのパスが通っていない場合は `python -m pip install` で試してみてください。

## Step 2: 基本の設定

次に、APIキーを取得して設定ファイルを作ります。

1. **E2B API Key:** [E2B公式サイト](https://e2b.dev/)にサインアップし、DashboardからAPIキーを発行します。
2. **OpenAI API Key:** [OpenAI Platform](https://platform.openai.com/)から取得してください。

プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、以下を記述します。

```text
E2B_API_KEY=your_e2b_key_here
OPENAI_API_KEY=your_openai_key_here
```

次に、Pythonからこれらを読み込む初期設定コードを書きます。

```python
import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from openai import OpenAI

# .envファイルから環境変数を読み込む
load_dotenv()

# クライアントの初期化
# APIキーが正しくセットされていないと、ここでエラーを吐いて止まってくれます
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
e2b_api_key = os.environ.get("E2B_API_KEY")

if not e2b_api_key:
    raise ValueError("E2B_API_KEYが設定されていません。")

print("セットアップ完了。安全なサンドボックスへの扉が開きました。")
```

なぜ `os.environ.get` を使うのか。
それは、本番環境（GitHub ActionsやVercelなど）にデプロイする際、コードを書き換えずに環境変数を切り替えられるようにするためです。
「実務で使える」コードとは、こういうポータビリティを意識したコードのことを指します。

## Step 3: 動かしてみる

まずは、LLMを使わずに「サンドボックス内でPythonコードが動くこと」だけを確認しましょう。

```python
def run_test_code():
    # Sandboxインスタンスを生成（クラウド上にMicroVMが立ち上がる）
    # この処理には通常1秒もかかりません
    with Sandbox(api_key=e2b_api_key) as sandbox:
        # サンドボックス内で実行したいコードを文字列で渡す
        code = "print('Hello from E2B Sandbox!'); x = 10 + 20; print(f'Result: {x}')"

        print("実行中...")
        # run_pythonメソッドでコードを実行
        execution = sandbox.run_python(code)

        # 標準出力を表示
        print(f"出力: {execution.results}")
        print(f"標準出力ログ: {execution.logs.stdout}")

run_test_code()
```

### 期待される出力

```
セットアップ完了。安全なサンドボックスへの扉が開きました。
実行中...
出力: []
標準出力ログ: ['Hello from E2B Sandbox!', 'Result: 30']
```

（※ `results` は関数の戻り値やグラフオブジェクトが入る場所なので、単純なprint文の場合は `logs.stdout` に結果が入ります。）

ここで注目すべきは `with Sandbox(...) as sandbox:` という書き方です。
このブロックを抜けた瞬間に、クラウド上のVMは即座に破棄されます。
ゴミを残さない、これがエージェント開発における「安全」の定義です。

## Step 4: 実用レベルにする（AIエージェントとの連携）

いよいよ本番です。「GPT-4oにデータ分析コードを書かせ、それをサンドボックスで実行し、生成されたグラフを保存する」という実務的なフローを実装します。

ここでは、仮想の売上データ（CSV）をAIに渡し、それを可視化させます。

```python
def data_analysis_agent(user_query):
    # 1. LLMに「Pythonコード」を書かせる
    prompt = f"""
    あなたはデータサイエンティストです。
    以下の要求に対して、Pythonコードのみを出力してください。

    要求: {user_query}

    制約:
    - グラフは matplotlib を使用して作成してください。
    - グラフは 'chart.png' という名前で保存してください。
    - markdownのコードブロック（```python）は使わず、純粋なコードのみを出力してください。
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    generated_code = response.choices[0].message.content
    print("--- 生成されたコード ---")
    print(generated_code)
    print("-----------------------")

    # 2. 生成されたコードをサンドボックスで実行
    with Sandbox(api_key=e2b_api_key) as sandbox:
        print("サンドボックスで実行開始...")
        execution = sandbox.run_python(generated_code)

        if execution.error:
            print(f"エラー発生: {execution.error}")
            return

        # 3. サンドボックス内で生成された画像ファイルを取り出す
        # E2Bのサンドボックスは実行後もファイルを保持している（withブロック内であれば）
        try:
            files = sandbox.files.list("/")
            print(f"生成されたファイル一覧: {[f.name for f in files]}")

            # chart.png が存在すればローカルにダウンロード
            chart_data = sandbox.download_file("chart.png")
            with open("output_chart.png", "wb") as f:
                f.write(chart_data)
            print("画像を output_chart.png として保存しました。")

        except Exception as e:
            print(f"ファイル取得失敗: {e}")

# 実行
data_analysis_agent("2023年の月別売上推移を適当なデータで折れ線グラフにして。")
```

このスクリプトの肝は「LLMが書いたコードを、あなたのPCのPython環境では一切実行していない」という点です。
もしGPT-4oが間違えて `os.system('rm -rf /')` と書いたとしても、消えるのは使い捨てのMicroVM内のファイルだけで、あなたのPCは無傷です。

また、E2Bの環境には `pandas`, `matplotlib`, `numpy` などの主要なライブラリが最初からインストールされています。
わざわざ `pip install` をエージェントにさせなくて済むのも、レスポンス速度を上げる重要なポイントですね。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `E2B_API_KEY` not found | 環境変数が読み込めていない | `.env`ファイルの場所がスクリプトと同じか確認し、`load_dotenv()`を呼んでいるかチェック。 |
| Timeout Error | コードの実行が長すぎる（デフォルト値超え） | `sandbox.run_python(code, timeout=60)` のように明示的にタイムアウトを伸ばす。 |
| ModuleNotFoundError | 標準外のライブラリが必要 | `sandbox.commands.run("pip install xxx")` を先に実行するか、カスタムイメージを作成する。 |

## 次のステップ

ここまでで、あなたは「AIエージェントのための安全な実験場」を手に入れました。
次に挑戦すべきは、以下の3点です。

1. **ステートフルな対話の実現:**
現在は `with` ブロックで毎回環境を捨てていますが、同じサンドボックスIDを使い回すことで、「前の実行結果を引き継いで次のコードを実行する」対話型エージェントが作れます。
2. **インターネットアクセスの制限:**
実務では、エージェントが勝手に外部サーバーにデータを送信するのを防ぎたい場合があります。E2Bの設定でネットワークを遮断する方法を調べると、よりセキュアな設計が可能です。
3. **Open Interpreterとの比較:**
ローカルで動く `Open Interpreter` も有名ですが、あちらをDockerで動かす場合と、今回のE2B経由を比較してみてください。運用の楽さはE2Bが勝るはずです。

「AIに仕事を任せる」ための第一歩は、AIを信頼することではなく、AIが失敗しても大丈夫な環境を作ることです。
今回のサンドボックスはそのための、最も堅牢な土台になります。

## よくある質問

### Q1: E2Bの無料枠を超えたらどうなりますか？

自動的に有料プランへ移行することはありませんが、APIリクエストがエラーになります。本格的なサービスに組み込む場合は、ダッシュボードから支払い情報を登録し、月額$0〜の従量課金プランに切り替える必要があります。1セッションあたり数円の世界です。

### Q2: 実行中にエラーが出た際、LLMに修正させるには？

`execution.error` の内容を再度LLMに投げて、「このエラーを直して」とプロンプトを送るループ（Self-Correction）を実装してください。これでエージェントの自律性が一気に高まります。

### Q3: Python以外の言語も動かせますか？

はい。E2BはJavaScript/TypeScript、Java、C++などの環境も提供しています。`Sandbox` クラスの代わりに各言語用のクラスを使うか、汎用的なシェル実行機能を使えば、ほぼ全ての言語がサンドボックス内で動作します。

---

## あわせて読みたい

- [E2BとPythonで安全なAIエージェント実行環境を作る方法](/posts/2026-06-19-e2b-python-ai-agent-sandbox-tutorial/)
- [AIエージェントを安全に実行するサンドボックス環境の構築方法](/posts/2026-06-24-ai-agent-safe-sandbox-e2b-guide/)
- [Suprboxレビュー：AIエージェントのデータ操作を隔離・保護するセキュアなストレージ](/posts/2026-05-12-suprbox-ai-agent-secure-storage-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "E2Bの無料枠を超えたらどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "自動的に有料プランへ移行することはありませんが、APIリクエストがエラーになります。本格的なサービスに組み込む場合は、ダッシュボードから支払い情報を登録し、月額$0〜の従量課金プランに切り替える必要があります。1セッションあたり数円の世界です。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にエラーが出た際、LLMに修正させるには？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "execution.error の内容を再度LLMに投げて、「このエラーを直して」とプロンプトを送るループ（Self-Correction）を実装してください。これでエージェントの自律性が一気に高まります。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語も動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。E2BはJavaScript/TypeScript、Java、C++などの環境も提供しています。Sandbox クラスの代わりに各言語用のクラスを使うか、汎用的なシェル実行機能を使えば、ほぼ全ての言語がサンドボックス内で動作します。 ---"
      }
    }
  ]
}
</script>

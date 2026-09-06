---
title: "AIエージェント実行環境をE2Bで安全に構築する方法"
date: 2026-09-06T00:00:00+09:00
slug: "ai-agent-sandbox-e2b-python-guide"
cover:
  image: "/images/posts/2026-09-06-ai-agent-sandbox-e2b-python-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "E2B"
  - "Code Interpreter"
  - "AIエージェント 構築"
  - "Claude 3.5 Sonnet 使い方"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

AIエージェント（LLM）が生成したPythonコードを、あなたのPCから完全に隔離されたクラウド上の「サンドボックス」で実行し、結果やグラフ画像を取得する仕組みを構築します。
Pythonの基礎知識があれば、この記事のコードをコピーするだけで、安全なコード実行エージェントの基盤が完成します。

### 前提知識
- Pythonの基本的な文法（変数、関数の定義）
- ターミナル（コマンドプロンプト）でのpip操作

### 必要なもの
- E2B APIキー（無料枠あり）
- Anthropic APIキー（Claude 3.5 Sonnet推奨）
- Python 3.10以上がインストールされた環境

## 先に確認するスペック・料金

AIエージェントを自機（ローカル）で直接動かすのは、熟練のエンジニアでも「怖い」と感じる行為です。
LLMが誤って `os.remove()` やシステム設定の破壊を行うリスクがあるからです。
そこで今回は、クラウド型サンドボックス「E2B（Education to Business）」を採用します。

E2Bは無料プランで月間100時間、同時に2つまでのインスタンスを実行可能です。
趣味や小規模な検証なら無料で十分間に合いますし、有料プランも月額$0〜の従量課金設定があります。
ローカルでDockerを立てる方法もありますが、ポート管理やファイルマウントの権限設定が煩雑で、結局「動かない」とハマる人が多いため、私は迷わずE2Bを推奨しています。

PCスペックは、Pythonが動けばMacBook Airの最小構成でも問題ありません。
重い処理はすべてE2Bのクラウドサーバー側（2 vCPU, 4GB RAM）で実行されるため、あなたのPCの負荷はほぼゼロです。

## なぜこの方法を選ぶのか

AIエージェントにコードを実行させる手段は、大きく分けて3つあります。

1. **ローカル直接実行**: 最も速いが、セキュリティリスクが最大。一度ミスればOSが飛びます。
2. **ローカルDocker**: 安全だが、ファイルの受け渡しやネットワーク隔離の設定が難しく、開発環境が汚れます。
3. **E2B（クラウドサンドボックス）**: SDKを一行書くだけで隔離環境が立ち上がり、処理が終われば自動消去されます。

私はかつて、自前のDocker環境でエージェントを動かしていましたが、ゾンビプロセスが溜まってメモリを食いつぶす問題に悩まされました。
E2Bに移行してからは、セッションのタイムアウト管理をAPI任せにできるため、運用コストが劇的に下がりました。
「仕事で使えるか」という観点で見ると、再現性と安全性が担保されているE2B一択です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
今回はE2Bのコード実行用SDKと、LLM呼び出し用のAnthropic SDK、環境変数を管理するpython-dotenvを使用します。

```bash
pip install e2b-code-interpreter anthropic python-dotenv
```

`e2b-code-interpreter` は、単なるサンドボックスではなく「Jupyter Notebook」に近い環境を提供してくれます。
これにより、グラフの表示やデータの永続化が非常に扱いやすくなっています。

⚠️ **落とし穴:**
Pythonのバージョンが3.9以下だと、E2BのSDKが内部で使用している非同期処理（asyncio）の挙動でエラーが出る場合があります。必ず `python --version` で3.10以上であることを確認してください。

## Step 2: 基本の設定

APIキーをコードに直書きするのは、GitHubに誤ってプッシュした際の大惨事を防ぐため、実務では厳禁です。
`.env` ファイルを作成して管理します。

まず、カレントディレクトリに `.env` ファイルを作成してください。

```text
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

次に、これらを読み込んで初期化するベースコードを書きます。
`main.py` という名前で保存してください。

```python
import os
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from anthropic import Anthropic

# .envファイルから環境変数を読み込む
# これにより、コード内に機密情報を残さず安全に運用できます
load_dotenv()

e2b_api_key = os.getenv("E2B_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# クライアントの初期化
client = Anthropic(api_key=anthropic_api_key)

def run_code_in_sandbox(code: str):
    # Sandboxインスタンスを作成。実行完了後に自動で閉じるようにwith構文を使います
    # 独自の隔離環境がクラウド上に0.5秒程度で爆速起動します
    with Sandbox(api_key=e2b_api_key) as sandbox:
        print("サンドボックスを起動中...")
        execution = sandbox.run_code(code)
        return execution
```

各設定項目の意味：
- `Sandbox(api_key=...)`: これを呼び出した瞬間、あなた専用のマイクロVM（Firecracker）が起動します。
- `sandbox.run_code(code)`: Jupyterのようにセル単位でコードを実行し、標準出力やグラフ、エラー内容を返します。

## Step 3: 動かしてみる

まずは、AIに頼らず「サンドボックスが正しく動くか」を確認します。
`main.py` の末尾に以下のテストコードを追加して実行してください。

```python
if __name__ == "__main__":
    test_code = """
import numpy as np
data = np.array([1, 2, 3, 4, 5])
print(f"平均値は: {data.mean()}")
"""
    result = run_code_in_sandbox(test_code)

    # 実行結果の出力
    if result.logs.stdout:
        for line in result.logs.stdout:
            print(f"[出力]: {line}")

    if result.error:
        print(f"[エラー]: {result.error}")
```

### 期待される出力

```text
サンドボックスを起動中...
[出力]: 平均値は: 3.0
```

E2Bのサンドボックスには、主要なデータ分析ライブラリ（numpy, pandas, matplotlib等）があらかじめインストールされています。
「ライブラリがない」というエラーで止まることが少ないのが、実務で重宝する理由です。

## Step 4: 実用レベルにする

ここからが本番です。Claude 3.5 Sonnetに指示を出し、彼が書いたコードを自動でサンドボックスに送り、結果をユーザーに返す「AIデータ分析エージェント」を構築します。

AIがコードを出力する際、マークダウンの「\`\`\`python」という囲み記号が入ってしまいます。
これをパースして抽出するロジックを含めた実用的なコードがこちらです。

```python
import re

def ask_ai_and_run(prompt: str):
    # 1. AIにコードを書かせる
    # 思考プロセスの精度が高いClaude 3.5 Sonnetを使用
    system_prompt = "あなたはデータサイエンティストです。Pythonコードのみを出力してください。結果はprint文で出力してください。"

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_content = response.content[0].text

    # 2. マークダウンからコードブロックを抽出
    # AIは説明文を混ぜることが多いため、正規表現でコード部分だけを抜き取ります
    code_match = re.search(r"```python\n(.*?)\n```", raw_content, re.DOTALL)
    code = code_match.group(1) if code_match else raw_content

    print(f"--- 実行されるコード ---\n{code}\n-----------------------")

    # 3. 安全なサンドボックスで実行
    with Sandbox(api_key=e2b_api_key) as sandbox:
        execution = sandbox.run_code(code)

        # 4. 結果の解析
        if execution.error:
            return f"実行エラー: {execution.error.value}"

        output = "\n".join(execution.logs.stdout)

        # グラフなどのファイルが生成された場合の処理（応用）
        if execution.results:
            for i, res in enumerate(execution.results):
                if res.png:
                    # PNGデータがある場合は保存
                    with open(f"chart_{i}.png", "wb") as f:
                        import base64
                        f.write(base64.b64decode(res.png))
                    output += f"\n[画像保存完了: chart_{i}.png]"

        return output

# 実行例
if __name__ == "__main__":
    user_input = "1から100までの素数を計算して、その合計を教えて。"
    print(ask_ai_and_run(user_input))
```

このコードの肝は、`execution.results` の判定部分です。
E2Bは、matplotlib等で生成されたグラフを自動的に検知し、Base64エンコードされたPNGデータとして返してくれます。
これにより、AIエージェントに「分析してグラフ化して」と頼むだけで、ローカルに画像ファイルが保存される仕組みが手に入ります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError` | サンドボックス内にライブラリがない | `sandbox.install_pip_package("name")` を使うか、デフォルトで入っている主要ライブラリを使用する |
| `API Key not found` | `.env` の読み込み失敗 | `os.getenv` の前に `load_dotenv()` が実行されているか確認。ファイル名が `.env.txt` になっていないか注意 |
| タイムアウト | 処理が長時間（デフォルト数分）に及んでいる | `Sandbox(timeout=300)` のように引数で実行可能時間を延ばす |

## 次のステップ

これで、AIエージェントが安全に暴れ回れる「砂場（サンドボックス）」が完成しました。
この基盤があれば、次に以下のような高度な自動化に挑戦できます。

1. **GitHub連携**: リポジトリをクローンし、AIにコードを修正させてからテストを実行、成功したらPRを出すエージェント。
2. **データ分析アシスタント**: CSVファイルをE2Bにアップロードし、AIに「このデータの傾向を可視化して」と頼むだけでレポートを作成させる。
3. **APIサーバーの自動デバッグ**: 本番環境で起きたエラーログをAIに渡し、サンドボックス内で再現コードを走らせて修正案を作る。

実務では、この「実行して結果を見る」というフィードバックループがAIの精度を飛躍的に高めます。
LLMは「書くだけ」なら嘘をつきますが、実行環境があれば「動かないから修正する」という自己修正が可能になるからです。

## よくある質問

### Q1: E2Bを使わずにローカルのDockerで同じことはできますか？

可能です。ただし、Dockerコンテナ内のファイルをホストに取り出す処理や、実行ごとにコンテナをクリーンアップするスクリプトを自前で書く必要があります。開発効率を考えると、月数百円程度のコスト（または無料枠）でE2Bを使う方が圧倒的に「タイパ」が良いです。

### Q2: 実行中にAIが外部サイトに攻撃を仕掛ける可能性はありませんか？

E2Bのサンドボックスはデフォルトでインターネット接続が許可されています。悪用を防ぐため、非常に高い頻度でのアウトバウンド通信には制限がかかることがありますが、完全に遮断したい場合は、エンタープライズプランでのネットワーク制御が必要です。個人開発なら、APIキーの制限設定で対応するのが現実的です。

### Q3: 対応している言語はPythonだけですか？

いいえ、E2BはJavaScript/TypeScript、Java、C++など主要な言語に対応しています。ただし、最もライブラリが充実しており、AIエージェントと相性が良いのはPythonです。まずはPythonから始め、必要に応じて他言語に拡張することをお勧めします。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIの生成コードとサンドボックスの実行ログを横並びで確認する開発環境に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [E2BとPythonで安全なAIエージェント実行環境を作る方法](/posts/2026-06-19-e2b-python-ai-agent-sandbox-tutorial/)
- [PythonとE2BでAIエージェント用セキュア実行環境を作る方法](/posts/2026-08-23-python-e2b-ai-agent-sandbox-tutorial/)
- [AIエージェントをDockerで安全に動かすサンドボックス構築方法](/posts/2026-08-17-ai-agent-safe-docker-sandbox-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "E2Bを使わずにローカルのDockerで同じことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。ただし、Dockerコンテナ内のファイルをホストに取り出す処理や、実行ごとにコンテナをクリーンアップするスクリプトを自前で書く必要があります。開発効率を考えると、月数百円程度のコスト（または無料枠）でE2Bを使う方が圧倒的に「タイパ」が良いです。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にAIが外部サイトに攻撃を仕掛ける可能性はありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "E2Bのサンドボックスはデフォルトでインターネット接続が許可されています。悪用を防ぐため、非常に高い頻度でのアウトバウンド通信には制限がかかることがありますが、完全に遮断したい場合は、エンタープライズプランでのネットワーク制御が必要です。個人開発なら、APIキーの制限設定で対応するのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "対応している言語はPythonだけですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、E2BはJavaScript/TypeScript、Java、C++など主要な言語に対応しています。ただし、最もライブラリが充実しており、AIエージェントと相性が良いのはPythonです。まずはPythonから始め、必要に応じて他言語に拡張することをお勧めします。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Dell U2723QE</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIの生成コードとサンドボックスの実行ログを横並びで確認する開発環境に最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

---
title: "OllamaとPythonで実用的なローカルAIエージェントを自作する方法"
date: 2026-06-02T00:00:00+09:00
slug: "ollama-python-local-ai-agent-tutorial"
cover:
  image: "/images/posts/2026-06-02-ollama-python-local-ai-agent-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Llama 3.1 8B"
  - "AIエージェント 自作"
  - "Function Calling ローカル"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Llama 3.1 8Bをベースに、PCローカル環境で「自律的にツールを使いこなす」AIエージェントを構築します。
- Pythonを使ってLLMに「計算機」や「ファイル操作」などの外部ツールを認識させ、指示に応じてそれらを自動で呼び出す仕組みを実装します。
- クラウドAPIを一切使わず、完全にオフラインかつ無料で動く実戦的なプログラムを完成させます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMを動かすには現在最もコスパが良い選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Pythonの基本的な文法（関数の定義やライブラリのインポート）を理解している必要があります。
また、Docker等の複雑なツールは使わず、シンプルなPythonスクリプトとOllamaだけで完結させます。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、最も重要なのは「VRAM（ビデオメモリ）」の量です。
今回のガイドで扱うLlama 3.1 8Bモデルを快適に動かすには、最低でも8GB、できれば12GB以上のVRAMを搭載したNVIDIA製GPUを推奨します。
私はRTX 4090の2枚挿しで検証していますが、RTX 3060（12GB版）やRTX 4060 Ti（16GB版）があれば、業務レベルのレスポンスが得られます。

Macユーザーであれば、メモリ16GB以上のApple Silicon（M1/M2/M3）があれば十分実用的です。
WindowsでGPUがない場合、CPU推論も可能ですが、回答までに数分かかるため「仕事で使う」には正直厳しいのが本音です。
初期費用以外にAPI使用料は一切かかりませんが、高負荷時はPCの消費電力が300W〜500W程度まで跳ね上がるため、電気代だけは覚悟してください。

## なぜこの方法を選ぶのか

現在、AIエージェントを作る方法はOpenAIの「Assistants API」を使うのが一般的ですが、私はあえて「Ollama + Python（LangChain/LangGraph）」によるローカル構築を推します。
最大の理由は「機密データの扱い」と「コストの予測可能性」です。
SIer時代、顧客から「データは社外に出せない」と言われ続けましたが、ローカルLLMならその壁を突破できます。

また、DifyなどのGUIツールを使う方法もありますが、細かいロジックの調整や既存システムとの連携を考えると、Pythonコードで記述する方が圧倒的に自由度が高いです。
特にLlama 3.1が登場してから、ローカルモデルでも「Function Calling（関数呼び出し）」の精度が劇的に向上しました。
わざわざGPT-4にお金を払わなくても、特定のタスクに特化させればローカルで同等の自動化が可能です。

## Step 1: 環境を整える

まずは推論エンジンとなる「Ollama」をインストールし、モデルをダウンロードします。

```bash
# Ollamaのインストール（Mac/Linux）
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合は公式サイトからインストーラーを実行してください。

# モデルのダウンロード
ollama pull llama3.1:8b
```

`llama3.1:8b` は、Metaが公開した最新の軽量モデルです。
128kトークンのコンテキストウィンドウを持ち、日本語の理解力も以前のモデルより格段に向上しています。
Ollamaはバックグラウンドでサーバーとして常駐し、API（デフォルトはポート11434）を提供してくれます。

⚠️ **落とし穴:**
Windowsユーザーで「Ollama command not found」と出る場合は、環境変数のパスが通っていないか、インストール後にターミナルを再起動していない可能性が高いです。
また、GPUが認識されているかは `ollama serve` 実行時のログで確認できます。「CPU only」と出ている場合は、最新のNVIDIAドライバーがインストールされているか確認してください。

## Step 2: 基本の設定

次に、PythonからOllamaを制御するためのライブラリをインストールします。
今回はシンプルさを重視して、公式の `ollama` ライブラリを使用します。

```bash
pip install ollama
```

スクリプトを作成します。ここでは、LLMに「ツール」の存在を教えるための初期設定を行います。

```python
import ollama

# 使用するモデル名
MODEL = "llama3.1:8b"

def get_current_weather(city: str):
    """指定された都市の天気を取得する（モック関数）"""
    # 実際にはここで外部APIを叩くが、今回はテスト用に固定値を返す
    if "東京" in city:
        return "晴れ、25度"
    return "不明"

# LLMに「どんなツールが使えるか」を定義する
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_current_weather',
            'description': '指定された都市の現在の天気を取得します',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {
                        'type': 'string',
                        'description': '都市名（例：東京）',
                    },
                },
                'required': ['city'],
            },
        },
    },
]
```

ここでは、LLMに対して「天気を調べる関数があるよ」という情報をJSON形式で渡しています。
これが「Function Calling」の肝です。
LLM自体は天気を知りませんが、「天気を教えて」と言われた時に「この関数を使えばいいんだな」と判断できるようになります。

## Step 3: 動かしてみる

実際に、LLMが関数を呼び出す判断ができるかテストします。

```python
# ユーザーからの質問
messages = [{'role': 'user', 'content': '東京の天気を教えてください'}]

# Ollamaに問い合わせ
response = ollama.chat(
    model=MODEL,
    messages=messages,
    tools=tools, # ここでツール定義を渡す
)

# LLMの回答を確認
print(response['message'])
```

### 期待される出力

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": [
    {
      "function": {
        "name": "get_current_weather",
        "arguments": {
          "city": "東京"
        }
      }
    }
  ]
}
```

LLMが「文章で答える」のではなく、「関数 `get_current_weather` を引数 `{"city": "東京"}` で実行せよ」という命令（tool_calls）を出していることがわかります。
これができれば、エージェント構築の8割は完了したも同然です。

## Step 4: 実用レベルにする

LLMから返ってきた「関数の実行命令」をキャッチして、実際にPython側で関数を実行し、その結果を再度LLMに投げて最終的な回答を作らせる「ループ」を実装します。
これこそが「AIエージェント」の正体です。

```python
def run_agent(user_input):
    messages = [{'role': 'user', 'content': user_input}]

    # 1. LLMに判断を仰ぐ
    response = ollama.chat(model=MODEL, messages=messages, tools=tools)

    # ツール呼び出しが必要ない場合はそのまま回答を返す
    if not response['message'].get('tool_calls'):
        return response['message']['content']

    # 2. ツール（関数）を実行する
    if response['message'].get('tool_calls'):
        messages.append(response['message']) # LLMの判断を履歴に追加

        for tool in response['message']['tool_calls']:
            function_name = tool['function']['name']
            arguments = tool['function']['arguments']

            if function_name == 'get_current_weather':
                # 実際の関数を実行
                result = get_current_weather(arguments['city'])

                # 実行結果を履歴に追加
                messages.append({
                    'role': 'tool',
                    'content': result,
                })

    # 3. 実行結果を踏まえて、LLMに最終回答を生成させる
    final_response = ollama.chat(model=MODEL, messages=messages)
    return final_response['message']['content']

# 実行
print(run_agent("東京の天気を教えて"))
```

このコードのポイントは、`role: 'tool'` として関数の実行結果をメッセージ履歴に加えている点です。
LLMは「自分がツールを使おうとしたこと」と「その結果がこうだったこと」を理解し、人間にとって自然な文章（例：「東京の天気は晴れで、気温は25度です」）を生成します。

これを応用すれば、ファイルの読み書き、DBへのクエリ実行、Slackへの投稿など、あらゆるPython関数をLLMに「外注」できるようになります。
私はこの仕組みを使って、ローカルPC内のドキュメントを検索して要約する「自分専用秘書」を動かしています。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| responseにtool_callsが含まれない | モデルが関数の必要性を理解していない | プロンプトを具体的にするか、Llama 3.1等の高性能モデルを使う |
| VRAM不足でクラッシュする | 8Bモデルでも4-bit量子化版でないと重い | `ollama pull llama3.1:8b` で通常は量子化版が入るが、メモリ不足ならより小さなモデル（Phi-3等）を検討 |
| 回答が英語になる | システムプロンプトで日本語指定がない | `messages` の先頭に `{'role': 'system', 'content': 'あなたは日本語で答える優秀な助手です'}` を追加する |

## 次のステップ

ここまでで、基本的なエージェントの仕組みは理解できたはずです。
次に挑戦すべきは「RAG（検索拡張生成）」との組み合わせです。
今回の天気APIのように固定値を返すのではなく、自分のPC内のPDFやテキストファイルをベクトルデータベースに保存し、LLMが必要に応じてその情報を「検索ツール」経由で取得するように拡張してみてください。

また、複数のツールを使い分ける場合は、条件分岐が増えてコードが複雑になります。
その際は `LangGraph` のようなライブラリを使うと、状態遷移（ステート管理）が楽になります。
ローカルLLMの世界は、RTX 3060一枚あれば十分に遊べます。
まずは自分の手元で、API代を気にせず1日中コードを回し続けてみてください。その経験こそが、エンジニアとしての本当の武器になります。

## よくある質問

### Q1: GPUがなくても動きますか？

動きますが、非常に遅いです。CPU推論の場合、1文字出すのに数秒かかることも珍しくありません。仕事でエージェントとして使うなら、中古のRTX 3060（12GB）で良いので、VRAMが多めのGPUを導入することを強くおすすめします。

### Q2: セキュリティ面で気をつけることは？

ローカルで動かす最大のメリットは安全であることですが、LLMに「ファイル削除」や「シェル実行」の関数を渡す場合は注意が必要です。LLMが誤操作をして、PC内の重要なファイルを消してしまうリスクがあるため、関数の実行範囲は限定的にしましょう。

### Q3: 商用利用は可能ですか？

Llama 3.1はMetaが提供するライセンスに従えば、多くの場合で商用利用可能です（月間アクティブユーザー数などの制限はありますが、一般的なビジネス用途なら問題ありません）。ただし、モデルによってライセンスが異なるため、必ず使用前に確認してください。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [Qwen 2.5やGemma 2をローカル環境で高速に動かす方法](/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "GPUがなくても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、非常に遅いです。CPU推論の場合、1文字出すのに数秒かかることも珍しくありません。仕事でエージェントとして使うなら、中古のRTX 3060（12GB）で良いので、VRAMが多めのGPUを導入することを強くおすすめします。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で気をつけることは？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ローカルで動かす最大のメリットは安全であることですが、LLMに「ファイル削除」や「シェル実行」の関数を渡す場合は注意が必要です。LLMが誤操作をして、PC内の重要なファイルを消してしまうリスクがあるため、関数の実行範囲は限定的にしましょう。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3.1はMetaが提供するライセンスに従えば、多くの場合で商用利用可能です（月間アクティブユーザー数などの制限はありますが、一般的なビジネス用途なら問題ありません）。ただし、モデルによってライセンスが異なるため、必ず使用前に確認してください。 ---"
      }
    }
  ]
}
</script>

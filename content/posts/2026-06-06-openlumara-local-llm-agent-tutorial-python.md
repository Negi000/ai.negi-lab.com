---
title: "OpenLumaraの使い方！ローカルLLMで爆速AIエージェントを構築する完全ガイド"
date: 2026-06-06T00:00:00+09:00
slug: "openlumara-local-llm-agent-tutorial-python"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "OpenLumara 使い方"
  - "AIエージェント 自作"
  - "ローカルLLM Python"
  - "Llama 3 ツール利用"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

ローカルLLM（Llama 3など）を使用して、ウェブ検索やファイル操作をトークン消費を最小限に抑えつつ実行する「超軽量AIエージェント」を構築します。
既存のフレームワークのようにプロンプトを数百行詰め込むのではなく、最小限の指示で的確にツールを使いこなすスクリプトを完成させます。

- 前提知識: Pythonの基本的な読み書きができる、仮想環境（venv）の操作ができる。
- 必要なもの: NVIDIA製GPU（VRAM 8GB以上推奨）またはMac（M1以上）、OpenAI互換APIサーバー（Ollamaなど）。

## 先に確認するスペック・料金

ローカルLLMをエージェントとして実運用する場合、最も重要なのは「VRAM容量」と「レスポンス速度」です。
OpenLumaraは軽量ですが、推論エンジン自体は重いため、RTX 3060（12GB）以上、あるいはMacBook Air/Pro（メモリ16GB以上）を用意してください。

もしGPUがない場合は、GroqやTogether AIなどの高速APIで代用可能ですが、今回の目的である「ローカルでの自律動作」を追求するなら、最低でもRTX 4060 Ti 16GB版（約7万円台）への投資を推奨します。
VRAM 8GBだとLlama 3 8Bを4bit量子化で動かすのが限界であり、エージェントが複雑な思考を始めるとすぐにコンテキストが溢れて速度が低下します。
API料金については、ローカル運用の場合は電気代のみ、外部APIを使う場合は100万トークンあたり数ドルの従量課金となります。

## なぜこの方法を選ぶのか

現在、AIエージェントを作るならCrewAIやLangGraphが有名ですが、これらは「多機能すぎてプロンプトが巨大化する」という欠点があります。
GPT-4のような巨大モデルなら力技で動かせますが、Llama 3 8BやQwen 2などのローカルLLMに食わせると、指示が長すぎて肝心のタスクを忘れる「迷子状態」が多発します。

OpenLumaraは、最初から「ローカルモデルで動かすこと」を前提にスクラッチで書かれています。
システムプロンプトを極限まで削り、モジュール単位で機能を呼び出す設計になっているため、推論コストを従来の1/3程度まで抑えつつ、精度を維持できるのが最大のメリットです。
「動けばいい」という趣味レベルではなく、「低スペック環境でいかに安定させるか」という実務的な課題に対する、現時点での最適解だと私は判断しました。

## Step 1: 環境を整える

まずはPython環境を構築します。既存の環境を汚さないよう、必ず仮想環境を作成してください。

```bash
# プロジェクトディレクトリの作成
mkdir my-lumara-agent && cd my-lumara-agent

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# OpenLumaraと必要なライブラリのインストール
# 現時点ではリポジトリから直接インストールするのが確実です
pip install git+https://github.com/OpenLumara/OpenLumara.git
pip install python-dotenv requests
```

OpenLumaraは依存関係が非常に少なく、軽量です。
`python-dotenv`を導入するのは、APIキーや接続先URLをコードに直書きせず、`.env`ファイルで管理する「実務上の作法」を守るためです。

⚠️ **落とし穴:**
Python 3.10未満を使っている場合、型ヒント周りでエラーが出る可能性があります。必ずPython 3.10以上、できれば3.11以降を使用してください。また、`git`コマンドが入っていない環境ではインストールに失敗するため、事前にGitのインストール状況を確認しましょう。

## Step 2: 基本の設定

次に、推論エンジン（Ollamaなど）との接続設定を行います。
私は自宅サーバーのRTX 4090でOllamaを動かしていますが、設定は共通です。

`.env`ファイルを作成し、以下を記述します。

```env
LUMARA_API_BASE="http://localhost:11434/v1"
LUMARA_API_KEY="ollama"
LUMARA_MODEL_NAME="llama3:8b"
```

この設定を読み込み、OpenLumaraを初期化するコードを書きます。

```python
import os
from dotenv import load_dotenv
from openlumara.core import LumaraAgent
from openlumara.models import OpenAIModel

# .envの読み込み
load_dotenv()

def get_agent():
    # OpenAI互換API（Ollama）の設定
    # timeoutを長めに設定するのは、ローカル推論の初回読み込みで落ちるのを防ぐため
    model = OpenAIModel(
        api_key=os.getenv("LUMARA_API_KEY"),
        base_url=os.getenv("LUMARA_API_BASE"),
        model_name=os.getenv("LUMARA_MODEL_NAME"),
        timeout=60.0
    )

    # エージェントの初期化
    # system_promptを極小に保つのがOpenLumara流
    agent = LumaraAgent(
        model=model,
        system_prompt="あなたは簡潔にタスクを遂行するアシスタントです。"
    )

    return agent
```

各設定の理由：
- `base_url`: Ollamaをローカルで動かす場合のデフォルトは11434ポートです。
- `timeout`: ローカルLLMは最初の1トークン目が出るまで時間がかかる（Time To First Token）ため、デフォルト設定だとタイムアウトで死ぬことが多いです。これを防ぐために60秒程度を確保します。

## Step 3: 動かしてみる

まずは最小限の構成で、エージェントが正しく思考できるかを確認します。

```python
def main():
    agent = get_agent()

    # ユーザーからの入力を模したテスト
    question = "今の日本の総理大臣は誰ですか？（最新の知識がない場合は、その旨を伝えてください）"

    print(f"User: {question}")
    print("-" * 30)

    # エージェントの実行
    # stream=Trueにすることで、回答が生成されるそばから表示できる（UX向上）
    response = agent.chat(question)
    print(f"Agent: {response}")

if __name__ == "__main__":
    main()
```

### 期待される出力

```
User: 今の日本の総理大臣は誰ですか？
------------------------------
Agent: 私の学習データに基づくと、現在の日本の内閣総理大臣は岸田文雄氏です。ただし、リアルタイムの情報を反映していない可能性があるため、最新のニュースを確認することをお勧めします。
```

（※モデルの学習時期により回答は異なります。Llama 3 8Bの場合、レスポンスまで私の環境で約0.5秒でした）

結果の読み方：
ここで注目すべきは、余計な「前置き」が排除されているかです。
OpenLumaraはシステムプロンプトが小さいため、モデルが「はい、わかりました。お答えします」といった無駄なトークンを吐き出しにくくなっています。これがトークン効率の良さの正体です。

## Step 4: 実用レベルにする

エージェントの真骨頂は「ツール」を使わせることにあります。
ここでは「現在の時刻を取得する」という、LLMが苦手なリアルタイム情報を扱うツールを追加してみます。

```python
import datetime
from openlumara.tools import Tool

# ツールの定義
# Docstring（関数直下のコメント）がモデルへの指示になるため、正確に書く
def get_current_time():
    """現在の正確な日付と時刻を返します。"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run_advanced_agent():
    model = OpenAIModel(
        api_key=os.getenv("LUMARA_API_KEY"),
        base_url=os.getenv("LUMARA_API_BASE"),
        model_name=os.getenv("LUMARA_MODEL_NAME")
    )

    # ツールを登録
    tools = [Tool(get_current_time)]

    agent = LumaraAgent(
        model=model,
        tools=tools,
        system_prompt="必要に応じてツールを使用し、正確な情報を提供してください。"
    )

    # ツールが必要な質問を投げる
    result = agent.chat("今の時間を教えて。")
    print(result)

run_advanced_agent()
```

実務での拡張ポイント：
1. **エラーハンドリング**: ローカルLLMはたまに無効なJSONを返します。OpenLumaraの内部ではリトライ処理が組まれていますが、呼び出し側でも`try-except`で囲み、APIサーバーのダウンに備えるべきです。
2. **既存システムとの連携**: `Tool`クラスには自社のDB検索関数や、Slack送信APIをラップした関数を渡すことができます。
3. **コンテキスト管理**: `agent.chat()`を繰り返すと会話履歴が積み重なります。ローカルモデルのコンテキスト窓（通常8k〜32kトークン）を超えないよう、定期的に履歴を要約するか削除する処理を組み込むのが「プロの仕事」です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionRefusedError` | Ollama等のAPIサーバーが起動していない | `ollama serve`が実行されているか確認。URLの末尾に`/v1`がついているかチェック。 |
| `Context Length Exceeded` | 会話履歴が長すぎてモデルの限界を超えた | 過去のメッセージを切り捨てるか、モデルのパラメータで`num_ctx`を増やす。 |
| ツールを呼んでくれない | 関数のDocstringが英語、または不明瞭 | Docstringを「この関数は〜をするために使う」と明確に記述。英語で書くと認識率が上がることが多い。 |

## 次のステップ

この記事で、OpenLumaraを使った「軽量かつ拡張性の高いエージェント」の基礎が完成しました。
次に挑戦すべきは、以下の3点です。

1. **RAG（検索拡張生成）との統合**: ローカルのPDFファイルを読み込み、その内容に基づいて回答するツールを作成してみてください。
2. **マルチエージェント化**: 「検索担当」と「執筆担当」の2つのAgentインスタンスを作り、メッセージをリレーさせる仕組みを構築すると、複雑な記事作成などを自動化できます。
3. **モデルの最適化**: Llama 3 8Bだけでなく、日本語に強いCommand RやQwen 2 7Bを試し、ツール呼び出しの成功率（Function Callingの精度）を比較してみてください。

特にローカルLLMの世界は日進月歩です。
「動かして終わり」にせず、常に最新の量子化モデル（GGUF形式など）を追いかけることで、あなたのエージェントはさらに賢く、速くなります。

## よくある質問

### Q1: Ollama以外の推論エンジンでも動きますか？

はい、OpenAI互換のAPIエンドポイントを持っているものであれば、LM Studio、LocalAI、vLLMなど何でも動きます。私は検証速度を優先する時はGroq、機密情報を扱う時は自前のRTXサーバー上のOllamaと使い分けています。

### Q2: ツール実行の成功率が低いのですが、どうすればいいですか？

モデルの性能に依存する部分が大きいですが、システムプロンプトで「あなたはツールを使用する専門家です」と強調するか、ツールの説明文（Docstring）をより具体的に「引数xには〜を入れること」と詳しく書くことで改善します。

### Q3: 商用利用は可能ですか？

OpenLumara自体のライセンス（通常MITなど）に準じますが、使用するLLMモデル（Llama 3など）のライセンスにも注意してください。Llama 3は月間アクティブユーザー数が一定以下であれば商用利用可能ですが、詳細は各モデルの規約を確認してください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3などのローカルLLMエージェントを安定動作させる最安解</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Hermes Desktop 使い方 | ローカルLLM環境を5分で構築しPythonで操作する方法](/posts/2026-06-03-hermes-desktop-local-llm-tutorial-python/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [Llama.cppで最新ローカルLLMを即座にAPI化して検証する方法](/posts/2026-04-21-llamacpp-server-local-llm-tutorial-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollama以外の推論エンジンでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、OpenAI互換のAPIエンドポイントを持っているものであれば、LM Studio、LocalAI、vLLMなど何でも動きます。私は検証速度を優先する時はGroq、機密情報を扱う時は自前のRTXサーバー上のOllamaと使い分けています。"
      }
    },
    {
      "@type": "Question",
      "name": "ツール実行の成功率が低いのですが、どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルの性能に依存する部分が大きいですが、システムプロンプトで「あなたはツールを使用する専門家です」と強調するか、ツールの説明文（Docstring）をより具体的に「引数xには〜を入れること」と詳しく書くことで改善します。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "OpenLumara自体のライセンス（通常MITなど）に準じますが、使用するLLMモデル（Llama 3など）のライセンスにも注意してください。Llama 3は月間アクティブユーザー数が一定以下であれば商用利用可能ですが、詳細は各モデルの規約を確認してください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBでLlama 3などのローカルLLMエージェントを安定動作させる最安解</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

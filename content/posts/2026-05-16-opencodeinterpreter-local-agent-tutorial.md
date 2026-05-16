---
title: "ローカルLLMで自律型エージェントを作る方法 OpenCodeInterpreter 構築ガイド"
date: 2026-05-16T00:00:00+09:00
slug: "opencodeinterpreter-local-agent-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "OpenCodeInterpreter"
  - "Ollama 使い方"
  - "自律型エージェント"
  - "Python AI 開発"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

- ユーザーが投げた曖昧な指示に対し、自らPythonコードを生成・実行・修正し、最終的な結果を出す自律型AIエージェント。
- OpenCodeInterpreter（DS-6.7Bまたは33B）を「頭脳（オーケストレーター）」として活用し、ローカル環境（Ollama）で完結するシステム。
- Pythonの基礎知識と、Dockerを少し触ったことがあれば完遂できるレベルの構成。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24GBのVRAMはOpenCodeInterpreter 33Bを快適に動かすための必須条件</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLM、特に「実務で使えるレベルのコード生成」を求めるなら、VRAM（ビデオメモリ）が全てです。
今回推奨する `OpenCodeInterpreter-DS-6.7B` を快適に動かすなら、VRAMは最低でも12GB、理想は16GB以上です。
もし33Bモデルを試したいなら、RTX 3090/4090の24GBが1枚、あるいは私のように2枚挿し（NVLink不要）の構成が必要になります。

「Macなら動く？」という質問も多いですが、Apple Silicon（M2/M3 Max）でメモリ64GB以上積んでいるなら十分実用圏内です。
逆に、VRAM 8GB以下のノートPCや、旧世代のGTXシリーズでは、推論速度が「1文字/秒」以下になり、エージェントとしての実用性はゼロになります。
その場合は、おとなしく月額$20を払ってClaude 3.5 SonnetのAPIを使うか、OpenRouter経由で回したほうが、あなたの貴重な時間を無駄にせずに済みます。

## なぜこの方法を選ぶのか

AIエージェントを作る際、一般的にはGPT-4oやClaude 3.5 SonnetをAPI経由で使うのが最短ルートです。
しかし、Redditの「Opencode you naughty minx」という投稿が示唆するように、特定のコーディングタスクや自律的なデバッグにおいては、OpenCodeInterpreterのような「コード実行フィードバック」を前提に学習されたモデルが、汎用モデルを凌駕することがあります。

QwenやGemmaも優秀ですが、彼らは「指示に従う」のは得意でも、「自分で書いたコードがエラーになった時に、エラー文を読み解いて執筆し直す」という粘り強さに欠ける場面が多い。
OpenCodeInterpreterは、その名の通り「コードを解釈し、実行結果を見て、次の手を打つ」という思考プロセスが強化されています。
これをローカルで動かす最大のメリットは、機密データを含むファイルを扱わせても情報漏洩のリスクがないこと、そして「無限に試行錯誤させてもAPI料金が1円もかからない」ことです。

## Step 1: 環境を整える

まずはLLMの実行基盤としてOllamaを導入し、OpenCodeInterpreterのモデルをプルします。

```bash
# Ollamaのインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# OpenCodeInterpreterのモデルを取得
# 今回はバランスの良い6.7Bを使用します
ollama run opencodeinterpreter:6.7b
```

このコマンドは、モデルの重みをダウンロードし、ローカルサーバーを立ち上げます。
なぜ6.7Bなのか。それは、このサイズが「一般的なハイエンドGPU（RTX 4070 Tiなど）で高速に動作しつつ、論理破綻が少ない」スイートスポットだからです。
もしVRAMが24GB以上あるなら、`opencodeinterpreter:33b` を強く推奨します。コーディング精度が一段階跳ね上がります。

⚠️ **落とし穴:** Ollamaでモデルを動かした際、メモリが足りないとシステム全体がフリーズすることがあります。
実行前に `nvidia-smi`（NVIDIA環境）やアクティビティモニタを確認し、他の重いアプリ（ブラウザのタブ100個など）を閉じておいてください。

## Step 2: 基本の設定

エージェントを動かすためのPython環境を構築します。
コードを直接自分のPCで実行させるのは危険（rm -rf / などを書きかねない）なため、簡易的なサンドボックスを用意する思想で書きます。

```python
import os
import requests
import json
import subprocess

# Ollama APIの設定
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "opencodeinterpreter:6.7b"

def call_llm(prompt):
    """
    Ollama APIを叩いてLLMの応答を得る。
    stream=Falseにすることで、レスポンスが全て完了してから処理を開始する設定。
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" # 構造化データで受け取るためにJSONモードを指定
    }

    response = requests.post(OLLAMA_URL, json=payload)
    return response.json().get("response")

# エージェントの「システムプロンプト」
SYSTEM_PROMPT = """
あなたは熟練のPythonエンジニアです。
ユーザーの要望に対し、必ず以下のJSON形式で回答してください。
{
    "thought": "あなたの思考プロセス",
    "code": "実行するPythonコード",
    "is_finished": true/false (タスクが完了したか)
}
"""
```

ここで「なぜJSON形式にするのか」という点ですが、エージェント（プログラム）がLLMの出力をパース（解析）しやすくするためです。
「はい、わかりました。コードはこちらです」といった不要な挨拶を除去し、純粋に「思考」と「コード」だけを抽出することで、次のステップの自動実行に繋げます。

## Step 3: 動かしてみる

最小限の「生成・実行ループ」を実装します。
指示を与えると、LLMがコードを書き、それをローカルのPythonインタープリタで実行し、結果をLLMに戻すという流れです。

```python
def execute_code(code):
    """
    生成されたコードを一時ファイルに書き出し、実行して標準出力を返す。
    """
    with open("temp_script.py", "w") as f:
        f.write(code)

    try:
        # 実行時間を10秒に制限（無限ループ対策）
        result = subprocess.run(
            ["python3", "temp_script.py"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return str(e)

# メインループ
user_task = "現在のカレントディレクトリにあるファイル一覧を取得し、ファイルサイズ順に並べ替えて表示して。"
context = f"{SYSTEM_PROMPT}\nユーザーの依頼: {user_task}"

for i in range(5): # 最大5回のリトライ/修正ループ
    print(f"--- ターン {i+1} ---")
    response_raw = call_llm(context)
    data = json.loads(response_raw)

    print(f"思考: {data['thought']}")
    print(f"実行コード:\n{data['code']}")

    output = execute_code(data['code'])
    print(f"実行結果:\n{output}")

    if data.get("is_finished"):
        break

    # 実行結果を文脈に追加して、次のターンへ
    context += f"\n実行結果: {output}\n上記の結果を元に、必要なら修正し、完了ならis_finishedをtrueにしてください。"
```

### 期待される出力

```
--- ターン 1 ---
思考: osモジュールを使用してファイル一覧を取得し、os.path.getsizeでサイズを確認します。
実行コード:
import os
files = [(f, os.path.getsize(f)) for f in os.listdir('.') if os.path.isfile(f)]
for f, s in sorted(files, key=lambda x: x[1], reverse=True):
    print(f"{f}: {s} bytes")
実行結果:
main.py: 2048 bytes
temp_script.py: 156 bytes
...
```

この「実行結果を見て、次の出力を決める」というプロセスこそが、Redditで話題になった「naughty minx」な挙動の源泉です。
1回目でライブラリが足りなくてエラーになれば、2回目ではそれをインストールするか、別の方法を探るようになります。

## Step 4: 実用レベルにする

実務で使うためには、上記のような「裸の実行」は非常に危険です。
例えば、「CSVを処理してグラフを保存して」と頼んだとき、LLMが間違って必要なシステムファイルを削除しない保証はありません。

そこで、Dockerを使ったサンドボックス環境での実行に切り替えます。
また、OpenCodeInterpreterの真価を発揮させるには、「Execution Result」という特別なタグを用いたプロンプトエンジニアリングが有効です。

```python
# 実用的なサンドボックス実行例（概念）
def safe_execute_code(code):
    """
    Dockerコンテナ内でコードを実行し、ホストOSを保護する。
    """
    # 実際の実装では、docker-pyライブラリ等を使用して
    # 'python:3.11-slim' イメージ上で実行するのが望ましい。
    # ここではイメージの提示に留めます。
    pass

# OpenCodeInterpreter専用のテンプレート
# この形式に合わせると、モデルは「実行結果」をより正確に認識します。
prompt_template = """
## Task
{task}

## Code
{code}

## Execution Result
{result}
"""
```

私が実務でこのエージェントを使う際は、特定のディレクトリ（例えば `/data`）だけをDockerにマウントし、その中のファイルだけを操作させるようにしています。
これにより、データ分析の自動化や、大量のログファイルからのパターン抽出などを、完全に放置した状態で（自律的に）行わせることが可能になります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| JSONDecodeError | LLMがJSON以外の挨拶文を混ぜた | プロンプトで「JSON以外出力するな」と厳命するか、正規表現で `{}` の中身だけ抽出する。 |
| Out of Memory (OOM) | VRAM容量不足 | モデルを4-bit量子化（q4_K_M等）されたものに変えるか、コンテキスト長を短くする。 |
| Timeout | 無限ループするコードを生成した | `subprocess.run` の `timeout` 引数を必ず設定し、プロセスを強制終了させる。 |

## 次のステップ

この記事で作成した最小構成のエージェントが動いたら、次は「外部ツールの接続」に挑戦してください。
例えば、Google検索APIを叩く関数をエージェントに「道具」として渡せば、最新の情報をネットで調べて、それを元にPythonでグラフを描くといった高度な連携が可能になります。

また、ローカルLLMの性能を限界まで引き出すには、推論エンジンの最適化も欠かせません。
Ollama以外にも、vLLMやTGI（Text Generation Inference）を検討してみてください。
特に複数のリクエストを同時に捌く必要があるなら、vLLMの継続的バッチング機能は、あなたのRTX 4090を真の意味で「仕事道具」に変えてくれるはずです。

ローカルで動くエージェントは、一度構築してしまえば、誰にも邪魔されない自分専用の「超有能な部下」になります。
まずは簡単なスクレイピングやファイル整理から任せてみることをお勧めします。

## よくある質問

### Q1: OpenCodeInterpreterは他のモデル（Llama-3など）と何が違うのですか？

コーディングに特化したデータセットに加え、「コードを実行した結果、どうなったか」という対話ログで学習されている点が異なります。エラーに対する修正能力が非常に高く、自己完結型のタスクに向いています。

### Q2: GPUがありませんが、CPUだけで動かせますか？

動作自体は可能ですが、OpenCodeInterpreter-DS-6.7Bクラスでも、CPU（特にIntel/AMD）だと1秒間に数文字という速度になります。試行錯誤のループを回すエージェント用途では、ストレスが溜まりすぎて実用的とは言えません。

### Q3: エージェントが勝手にファイルを削除したりしませんか？

そのリスクは常にあります。だからこそ、Docker等のコンテナ技術を用いた隔離環境での実行が必須です。また、実行前に人間がコードを確認する「Human-in-the-loop」のステップを挟むのも、実務では重要な設計です。

---

## あわせて読みたい

- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)
- [OpenAIマフィアが150億円超の「Zero Shot」を設立。API叩きだけのビジネスが死ぬ時代の生存戦略](/posts/2026-04-07-openai-alums-zero-shot-fund-analysis/)
- [Manus AIの失墜と「自律型エージェント」の過剰な期待が招いた必然の結末](/posts/2026-03-26-manus-ai-agent-reality-check-and-reckoning/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "OpenCodeInterpreterは他のモデル（Llama-3など）と何が違うのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "コーディングに特化したデータセットに加え、「コードを実行した結果、どうなったか」という対話ログで学習されている点が異なります。エラーに対する修正能力が非常に高く、自己完結型のタスクに向いています。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUがありませんが、CPUだけで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動作自体は可能ですが、OpenCodeInterpreter-DS-6.7Bクラスでも、CPU（特にIntel/AMD）だと1秒間に数文字という速度になります。試行錯誤のループを回すエージェント用途では、ストレスが溜まりすぎて実用的とは言えません。"
      }
    },
    {
      "@type": "Question",
      "name": "エージェントが勝手にファイルを削除したりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "そのリスクは常にあります。だからこそ、Docker等のコンテナ技術を用いた隔離環境での実行が必須です。また、実行前に人間がコードを確認する「Human-in-the-loop」のステップを挟むのも、実務では重要な設計です。 ---"
      }
    }
  ]
}
</script>

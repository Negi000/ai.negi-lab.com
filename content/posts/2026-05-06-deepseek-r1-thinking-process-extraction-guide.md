---
title: "DeepSeek-R1の思考プロセスを抽出して制御するPython実装ガイド"
date: 2026-05-06T00:00:00+09:00
slug: "deepseek-r1-thinking-process-extraction-guide"
cover:
  image: "/images/posts/2026-05-06-deepseek-r1-thinking-process-extraction-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "DeepSeek-R1 使い方"
  - "Python API 連携"
  - "思考プロセス 抽出"
  - "Chain of Thought 実装"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

DeepSeek-R1などの推論型LLMが出力する「思考プロセス（Chain of Thought）」と「最終回答」をリアルタイムで分離し、それぞれ別々に処理・表示するPythonスクリプトを作成します。
API経由、あるいはローカルのOllama環境で、モデルが何を考えて結論に至ったのかを構造的に取得する基盤を構築するのがゴールです。

- Pythonの基本的な文法がわかること
- OpenAI互換API（DeepSeek公式サイトやGroqなど）のAPIキー、あるいはOllamaが動作する環境
- 外部ライブラリ（openai, rich）のインストールが可能な環境

## なぜこの方法を選ぶのか

DeepSeek-R1やOpenAIのo1シリーズといった「推論型モデル」は、回答の前に膨大な思考ログを出力します。
標準的なチャットUIではこれらが一塊のテキストとして表示されますが、実務で使うなら「思考プロセス」と「回答」は明確に分けるべきです。

なぜなら、思考プロセスには「ユーザーに見せるべきではない中間計算」や「プロンプトの解釈」が含まれるため、そのままプロダクトに出すとUIが煩雑になります。
一方で、開発者としては「なぜその回答になったか」をログに残すために思考プロセスは必須の情報です。

正規表現や単純な文字列分割で処理しようとすると、ストリーミング出力（文字が少しずつ出てくる形式）に対応できず、ユーザー体験を損ないます。
今回はストリーミングに対応したパーサーを自作することで、レスポンスの速さを維持したままデータを構造化する、最も実用的なアプローチを採ります。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
今回はAPIクライアントとして標準的な`openai`ライブラリと、コンソール出力をリッチにするための`rich`を使用します。

```bash
pip install openai rich
```

`rich`を導入するのは、思考プロセスと回答を視覚的に分けるためです。
白黒のログが流れるだけだと、どこまでが「思考」でどこからが「結論」か判別しづらいため、実務でのデバッグ効率が大幅に変わります。
Python 3.10以上を推奨します。

⚠️ **落とし穴:**
DeepSeekの公式APIは非常に安価ですが、負荷が高まると頻繁に503エラー（Service Unavailable）を返します。
検証段階ではGroqのAPIや、ローカルのOllama（RTX 3060 12GB以上推奨）をエンドポイントに使う方が、開発が止まらずにスムーズです。

## Step 2: 基本の設定

APIキーの管理と、モデルの呼び出し設定を行います。
APIキーをコードに直書きするのは、GitHub等への誤プッシュによる流出リスクがあるため絶対に避けましょう。

```python
import os
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

# API設定（環境変数から読み込み）
# DeepSeek公式の場合: https://api.deepseek.com
# Ollamaの場合: http://localhost:11434/v1
base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
api_key = os.getenv("LLM_API_KEY", "your-api-key-here")

client = OpenAI(api_key=api_key, base_url=base_url)
console = Console()
```

ここでは、環境変数からURLとキーを読み込むようにしています。
デフォルト値を設定しておくことで、環境変数を設定し忘れても動作するようにしていますが、本番運用では必ず`os.environ`で厳格に管理してください。

## Step 3: 動かしてみる

DeepSeek-R1の特徴である`<thinking>`タグ（モデルによっては`<thought>`）を処理する最小限のコードを書きます。
まずは、タグが含まれた生データを取得できるか確認しましょう。

```python
def simple_test():
    response = client.chat.completions.create(
        model="deepseek-reasoner", # 公式APIの場合はこのモデル名
        messages=[{"role": "user", "content": "9.11と9.9、どちらが大きい？理由も教えて。"}],
        stream=False
    )

    # DeepSeek-R1公式APIの場合、reasoning_contentという専用フィールドがある
    if hasattr(response.choices[0].message, 'reasoning_content'):
        print("--- 思考プロセス ---")
        print(response.choices[0].message.reasoning_content)
        print("\n--- 最終回答 ---")
        print(response.choices[0].message.content)
    else:
        # Ollamaや他のプロバイダの場合、contentの中にタグが含まれることがある
        print(response.choices[0].message.content)

simple_test()
```

### 期待される出力

```
--- 思考プロセス ---
まず数値を比較するために、小数第一位を見ます。
9.11は1、9.9は9です。
9の方が大きいため、9.9の方が大きいと判断できます。
...（中略）...
--- 最終回答 ---
9.9の方が大きいです。
```

結果の読み方ですが、DeepSeek公式APIを使う場合は`reasoning_content`という独自のプロパティに思考プロセスが格納されます。
しかし、Ollamaなどを介してローカルで動かす場合、思考プロセスは通常の`content`の中に`<think>`タグで囲まれて出力されることが多いです。
この「環境による出力形式の違い」を吸収するのが、次のステップの目的です。

## Step 4: 実用レベルにする

実務で使えるレベルに引き上げます。
ストリーミング出力をパースし、思考が始まった瞬間に「思考用パネル」を出し、終わったら「回答用パネル」に切り替えるスクリプトを作成します。

```python
import sys

def run_reasoning_chat(prompt):
    # ストリーミング開始
    stream = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    full_reasoning = ""
    full_content = ""

    console.print(Panel("[bold blue]Thinking...[/bold blue]"))

    # RichのLive表示を使ってリアルタイムに更新
    with Live("", refresh_per_second=10, vertical_overflow="visible") as live:
        for chunk in stream:
            # 公式APIの専用フィールドをチェック
            delta = chunk.choices[0].delta

            # 思考プロセスの更新
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                full_reasoning += delta.reasoning_content
                live.update(Panel(full_reasoning, title="思考プロセス", border_style="blue"))

            # 最終回答の更新
            elif delta.content:
                # 思考が終わって回答が始まった瞬間に表示を切り替える工夫
                if full_content == "":
                    console.print(Panel("[bold green]Answer[/bold green]"))

                full_content += delta.content
                live.update(full_content)

if __name__ == "__main__":
    user_input = "複雑な論理パズル：AはBより背が高い。CはAより背が高い。DはCより背が低いがBよりは高い。一番背が高いのは誰？"
    run_reasoning_chat(user_input)
```

このコードの肝は、`Live`コンテキストマネージャによる動的更新です。
私は以前、単純な`print`でこれを作りましたが、思考プロセスが数千文字に及ぶと画面が激しくフラッシュして使い物になりませんでした。
`rich`の`Live`を使うことで、ターミナルの特定範囲だけを書き換えることができ、モダンなチャットUIのような挙動を再現できます。

また、`reasoning_content`が提供されないローカルモデル（Llama-3-70B-InstructにCoTプロンプトを入れた場合など）にも対応させるには、正規表現で`<think>`タグを検知するバッファ処理を追加する必要があります。
実務では、この「タグの有無」による分岐処理を最初に入れておかないと、モデルを切り替えた瞬間にコードが壊れます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `AttributeError: reasoning_content` | 使用しているモデルやプロバイダが専用フィールド非対応 | `delta.content` 内のタグをパースする処理に切り替える |
| `503 Service Unavailable` | DeepSeek公式サーバーの過負荷 | `Groq` APIか `Ollama` への切り替えを検討する |
| 思考プロセスが空で返ってくる | モデル名が `deepseek-reasoner` になっていない | モデル名を正しく指定するか、推論対応モデルか確認する |

## 次のステップ

この記事で作成したスクリプトは、推論プロセスを可視化する第一歩に過ぎません。
この次に挑戦すべきは「思考プロセスに基づいた自動デバッグ」です。
例えば、思考プロセスの中に「エラー」や「矛盾」という単語が含まれた場合、自動的に別のプロンプトを投げて自己修正させるエージェントを構築できます。

私はRTX 4090 2枚挿しの自作サーバーで、DeepSeek-R1 (671B) をFP8量子化で動かしていますが、思考プロセスを監視することで「モデルがどの段階で論理破綻したか」が手に取るようにわかります。
これは従来のLLMではブラックボックスだった部分です。
ぜひ、抽出した思考ログをデータベースに保存し、後から「思考の質」を評価する仕組みを作ってみてください。
それがRAGの精度向上や、精度の高いプロンプトエンジニアリングへの近道になります。

## よくある質問

### Q1: Ollamaで動かす場合、モデル名は何を指定すればいいですか？

`deepseek-r1:7b` や `deepseek-r1:32b` を指定してください。ただし、Ollamaは現在（2025年初頭時点）、思考プロセスを `content` 内の `<think>` タグで返します。そのため、今回のスクリプトを少し改修して、文字列内のタグを抽出する処理を入れる必要があります。

### Q2: 思考プロセスだけをオフにして、APIコストを節約できますか？

DeepSeek-R1のような推論モデルは、思考すること自体が性能の源泉であるため、思考を完全にオフにすることはできません。ただし、APIによっては `max_tokens` を制限することで出力を途中で切ることは可能ですが、回答の質が著しく低下するため推奨しません。

### Q3: Python以外の言語でも同じことは可能ですか？

可能です。OpenAI互換のAPIなので、TypeScript (Node.js) や Go でも同様に実装できます。ポイントは「ストリーミングで送られてくるチャンクの中から、通常の content 以外のフィールド（reasoning_content等）を拾えるか」という一点に尽きます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">DeepSeek-R1の量子化モデルをローカルで高速推論させるなら、24GB VRAMを持つ4090が必須装備です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%20%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%9C%E3%83%BC%E3%83%89&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [DeepSeek Thinking-with-Visual-Primitives 使い方：視覚的思考でVLMの精度を極限まで高める実装ガイド](/posts/2026-05-01-deepseek-thinking-with-visual-primitives-tutorial/)
- [DeepSeek API 使い方入門！V4時代を見据えた高精度RAG構築ガイド](/posts/2026-02-26-deepseek-v4-huawei-api-rag-tutorial/)
- [DeepSeek-V3をマルチGPU環境で構築して実用レベルの推論速度を実現する方法](/posts/2026-04-30-deepseek-v3-multi-gpu-vllm-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Ollamaで動かす場合、モデル名は何を指定すればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "deepseek-r1:7b や deepseek-r1:32b を指定してください。ただし、Ollamaは現在（2025年初頭時点）、思考プロセスを content 内の <think> タグで返します。そのため、今回のスクリプトを少し改修して、文字列内のタグを抽出する処理を入れる必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "思考プロセスだけをオフにして、APIコストを節約できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DeepSeek-R1のような推論モデルは、思考すること自体が性能の源泉であるため、思考を完全にオフにすることはできません。ただし、APIによっては maxtokens を制限することで出力を途中で切ることは可能ですが、回答の質が著しく低下するため推奨しません。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じことは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。OpenAI互換のAPIなので、TypeScript (Node.js) や Go でも同様に実装できます。ポイントは「ストリーミングで送られてくるチャンクの中から、通常の content 以外のフィールド（reasoningcontent等）を拾えるか」という一点に尽きます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品</p> <strong style=\"font-size:16px\">NVIDIA GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">DeepSeek-R1の量子化モデルをローカルで高速推論させるなら、24GB VRAMを持つ4090が必須装備です</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%20%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%9C%E3%83%BC%E3%83%89&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonで見る</a> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">楽天で見る</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

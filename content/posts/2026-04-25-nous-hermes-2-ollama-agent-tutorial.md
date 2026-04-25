---
title: "Nous Hermes 2とOllamaで自律型エージェントの基礎を構築する方法"
date: 2026-04-25T00:00:00+09:00
slug: "nous-hermes-2-ollama-agent-tutorial"
cover:
  image: "/images/posts/2026-04-25-nous-hermes-2-ollama-agent-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Nous Hermes 2"
  - "Ollama 使い方"
  - "Function Calling Python"
  - "ローカルLLM エージェント"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Nous Researchが開発した最強クラスのオープンソースモデル「Nous Hermes 2」をローカル環境で動かし、外部関数を呼び出してタスクを完結させるPythonスクリプトを作ります。
- 前提知識: Pythonの基本的な文法（関数定義やリスト操作）がわかること。
- 必要なもの: Python 3.10以上、RAM 16GB以上のPC（GPU推奨）、Ollamaのインストール。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBあれば、8Bクラスのモデルを非常に高速かつ余裕を持って動作させられます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

オープンソースLLMの世界では、Llama 3やMistralが有名ですが、実務で「エージェント」を作ろうとすると、指示追従性の低さに絶望することが多々あります。
特に「JSON形式で返せ」という指示を無視したり、不要な解説を付け加えたりするモデルは、プログラムに組み込む際に致命的なエラーの原因になります。
今回使用するNous Hermesシリーズは、OpenAIのGPT-4に匹敵する指示追従性を目指してファインチューニングされており、特に「関数呼び出し（Function Calling）」の精度が他のオープンソースモデルとは一線を画します。
APIコストを気にせず、かつ商用利用も可能なライセンスで、自律型エージェントの試作を行うなら、現時点でNous Hermes 2が最も「仕事で使える」選択肢だと私は確信しています。

## Step 1: 環境を整える

まずはローカルでLLMを動かすためのランタイム「Ollama」を導入し、モデルをダウンロードします。

```bash
# Ollamaのインストール（Mac/Linux）
curl -fsSL https://ollama.com/install.sh | sh

# Nous Hermes 2 (Llama 3 8Bベース) をダウンロード
ollama pull adrienbrault/nous-hermes-2-theta-llama-3-8b
```

Ollamaを使う理由は、複雑な量子化設定やCUDAの設定を隠蔽し、REST APIとしてLLMを即座に叩けるようになるからです。
RTX 4090を2枚挿している私の環境でも、開発の初期段階ではこの手軽さを優先します。
`nous-hermes-2-theta-llama-3-8b` は、従来のHermes 2 Proをさらに改良したモデルで、論理的思考能力が向上しています。

⚠️ **落とし穴:** メモリが不足している場合、モデルの読み込みでPCがフリーズすることがあります。
8Bモデル（約5GB）を動かすには、最低でも8GBのVRAM、もしくは16GB以上のシステムRAMが必要です。
もし動作が重い場合は、ブラウザのタブを閉じるか、より軽量な4-bit量子化版が選ばれていることを確認してください。

## Step 2: 基本の設定

PythonからOllamaを操作するためのライブラリをインストールし、スクリプトの土台を作ります。

```bash
pip install ollama
```

次に、Pythonスクリプト（`agent.py`）を作成し、ライブラリのインポートと定数定義を行います。

```python
import ollama
import json

# 使用するモデル名。先ほどpullした名前と一致させる
MODEL_NAME = "adrienbrault/nous-hermes-2-theta-llama-3-8b"

def chat_with_hermes(prompt):
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}],
            options={"temperature": 0} # 精度を安定させるために0に設定
        )
        return response['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
```

`temperature` を0に設定するのは、エージェントとしての動作に「揺らぎ」を排除するためです。
クリエイティブな文章を書かせるなら0.7程度が良いですが、関数呼び出しや論理パズルの場合は、常に同じ回答を得られる設定が実務上の鉄則です。

## Step 3: 動かしてみる

まずはモデルが正しく応答するか、指示通りに動くかを確認します。

```python
if __name__ == "__main__":
    test_prompt = "以下の情報をJSON形式で抽出してください：私の名前はねぎ。Python歴は8年です。"
    print(chat_with_hermes(test_prompt))
```

### 期待される出力

```json
{
  "name": "ねぎ",
  "experience": "8 years",
  "language": "Python"
}
```

Nous Hermes 2の凄いところは、多くを語らず、求められた形式だけを返してくる点です。
Llama 3の純正モデルだと「はい、承知しました。JSON形式で出力しますね：」といった余計な一言が入ることがありますが、Hermesは最初から「システムへの組み込み」を意識した挙動を見せます。

## Step 4: 実用レベルにする（関数呼び出しの実装）

ここからが本番です。LLMに「自分の知らない情報（現在の天気など）」を、外部ツールを使って取得させる「エージェント機能」を実装します。
今回は疑似的な天気取得関数をLLMに使わせてみます。

```python
def get_weather(city):
    """特定の都市の天気を取得する（疑似関数）"""
    # 実務ではここでAPIを叩く
    weather_data = {
        "東京": "晴れ、25度",
        "大阪": "雨、22度",
        "札幌": "雪、-2度"
    }
    return weather_data.get(city, "不明な都市です")

def run_agent(user_input):
    # 1. ユーザーの入力をモデルに投げる
    # システムプロンプトで「ツールが必要なら特定の形式で答えろ」と指示する
    system_instruction = (
        "あなたは便利なアシスタントです。"
        "天気の情報を聞かれたら、必ず 'CALL_FUNCTION: get_weather(都市名)' という形式で返してください。"
    )

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': user_input}
        ]
    )

    content = response['message']['content']
    print(f"[LLMの思考]: {content}")

    # 2. 関数呼び出しが必要か判定
    if "CALL_FUNCTION" in content:
        # 簡易的なパース処理
        city = content.split("(")[1].split(")")[0].replace("'", "").replace('"', '')
        print(f"[システム]: 関数 get_weather を引数 {city} で実行します...")

        result = get_weather(city)

        # 3. 関数の実行結果をモデルに返して、最終回答を得る
        final_response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': "関数の実行結果をユーザーに分かりやすく伝えてください。"},
                {'role': 'user', 'content': f"実行結果: {result}"}
            ]
        )
        return final_response['message']['content']

    return content

# 実行
if __name__ == "__main__":
    answer = run_agent("東京の天気を教えてくれる？")
    print(f"[最終回答]: {answer}")
```

このコードでは、モデルに「ツールを使うためのキーワード」を出力させるように調整しています。
OpenAIのAPIにあるようなネイティブな関数呼び出し機能（Tools API）もOllamaはサポートし始めていますが、このように「特定の文字列を出力させる」手法をマスターしておくと、どんなローカルモデルでもエージェント化できる汎用性が身につきます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ollama.ResponseError: model not found` | モデルのダウンロード（pull）が未完了。 | `ollama pull adrienbrault/nous-hermes-2-theta-llama-3-8b` を再実行。 |
| 出力が途中で切れる | `num_predict` のデフォルト値が短い。 | オプションで `num_predict: 1024` 等を指定する。 |
| 回答に余計な解説が入る | システムプロンプトの指示が弱い。 | 「解説は不要です。出力はJSONのみにしてください」と強く指示する。 |

## 次のステップ

今回は基本的な関数呼び出しを体験しましたが、Nous Researchが公開している「Hermes Function Calling」のデータセットを確認すると、さらに複雑なマルチステップのタスク（複数のツールを組み合わせて問題を解く）が可能であることがわかります。
次は、RAG（検索拡張生成）と組み合わせて、ローカルにあるPDFファイルを読み込み、その内容に基づいてツールを実行する「ドキュメント解析エージェント」の構築に挑戦してみてください。
また、Nous ResearchのDiscordやReddit（r/LocalLLaMA）では、最新の量子化モデルやプロンプトテクニックが日々議論されています。
今回のAMAのようなイベントを機に、開発者たちの生の声に触れることは、仕様書には載っていない「モデルの癖」を掴む最短ルートになります。

## よくある質問

### Q1: RTX 3060（12GB）でも動きますか？

はい、十分に動きます。8Bモデルであれば12GBのVRAMに完全に収まるため、推論速度も毎秒50トークン以上出るはずです。非常に快適な開発体験が得られるでしょう。

### Q2: OpenAIのAPIと比べて精度はどうですか？

複雑な推論や長文の文脈理解ではGPT-4に軍配が上がります。しかし、今回のような特定のフォーマット出力や単純なツール利用であれば、Nous Hermes 2で実用上問題ないレベルに達しています。コストとプライバシーの面では圧倒的にこちらが有利です。

### Q3: 日本語の能力は問題ないでしょうか？

今回使用したThetaモデルはLlama 3がベースになっており、日本語の理解能力も非常に高いです。ただし、内部的な思考は英語で行わせた方が精度が上がる傾向にあるため、システムプロンプトを英語で書き、出力だけを日本語にするという手法も有効です。

---

## あわせて読みたい

- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [Qwen2.5 32B 使い方 入門：ローカル環境で爆速RAGシステムを構築する方法](/posts/2026-04-13-local-rag-qwen2-5-32b-ollama-tutorial/)
- [ローカルLLMで漫画翻訳！Manga Translatorの使い方と導入手順](/posts/2026-03-15-local-manga-translator-rust-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060（12GB）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、十分に動きます。8Bモデルであれば12GBのVRAMに完全に収まるため、推論速度も毎秒50トークン以上出るはずです。非常に快適な開発体験が得られるでしょう。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIと比べて精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "複雑な推論や長文の文脈理解ではGPT-4に軍配が上がります。しかし、今回のような特定のフォーマット出力や単純なツール利用であれば、Nous Hermes 2で実用上問題ないレベルに達しています。コストとプライバシーの面では圧倒的にこちらが有利です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力は問題ないでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "今回使用したThetaモデルはLlama 3がベースになっており、日本語の理解能力も非常に高いです。ただし、内部的な思考は英語で行わせた方が精度が上がる傾向にあるため、システムプロンプトを英語で書き、出力だけを日本語にするという手法も有効です。 ---"
      }
    }
  ]
}
</script>

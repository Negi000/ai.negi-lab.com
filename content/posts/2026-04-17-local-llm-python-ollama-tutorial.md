---
title: "OllamaとPythonでローカルLLM環境を構築する手順"
date: 2026-04-17T00:00:00+09:00
slug: "local-llm-python-ollama-tutorial"
cover:
  image: "/images/posts/2026-04-17-local-llm-python-ollama-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Python ローカルLLM"
  - "Llama 3 構築"
  - "AI 自動化 スクリプト"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- 外部APIを一切使わず、自分のPC内で完結するAI自動推論Pythonスクリプト
- Llama 3やQwenといった最新のオープンソースモデルをコードから制御する基盤
- 前提知識: Pythonの基本的な文法（pipインストールや関数の呼び出し）がわかること
- 必要なもの: Windows/Mac/Linux PC（GPU推奨だがCPUでも動作可能）、メモリ8GB以上

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを動かす際、最も重要なのはVRAM容量。16GBあれば7B〜14Bモデルを快適に動かせます</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

ChatGPT（GPT-4o）やClaude 3は確かに高性能ですが、ビジネス実務では「データの外部送信禁止」や「APIコストの肥大化」が常に壁となります。
今回紹介するOllamaを用いたローカル環境構築は、これら全ての懸念をゼロにするための最短ルートです。
LangChainなどの巨大なフレームワークをいきなり使うと構造が複雑になりすぎて保守が困難になるため、まずは公式ライブラリで「モデルに直接命令を送る」という最も純粋でデバッグしやすい方法を採ります。
SIer時代、複雑なラッパーライブラリの仕様変更に泣かされてきた私が行き着いた、最も堅牢で「仕事に繋がる」最小構成です。

## Step 1: 環境を整える

まずは推論エンジンとなる「Ollama」をインストールします。
これはバックエンドでモデルのロードやGPUのメモリ管理を自動で行ってくれる、現時点で最も優れたツールの一つです。

```bash
# 公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
# インストール完了後、ターミナルでモデルをダウンロード
ollama run llama3
```

`ollama run llama3` は、Metaが公開した高性能なオープンソースモデルをローカルに落とし、対話モードを起動するコマンドです。
この段階で「/bye」と打って一度終了させ、次にPythonから操作するためのライブラリをインストールします。

```bash
pip install ollama
```

⚠️ **落とし穴:**
GPU（NVIDIA）を積んでいるのに推論が遅い場合、OllamaがGPUを認識していない可能性があります。
Windowsならタスクマネージャーの「パフォーマンス」タブで、専用GPUメモリが使用されているか確認してください。
認識されない場合は、最新のNVIDIAドライバを入れ直すのが一番の近道です。

## Step 2: 基本の設定

PythonからOllamaを呼び出すための初期設定を行います。
APIキーの管理が不要なのでコードは非常にシンプルになりますが、その分「どのモデルを使うか」の指定が重要になります。

```python
import ollama

# 使用するモデル名を定義
# 自分のPCスペックに合わせて 'llama3' (8B) や 'qwen2' (7B) を選択します
MODEL_NAME = "llama3"

def generate_response(prompt):
    # stream=False にすることで、回答が全て生成されてから結果を受け取ります
    # リアルタイム性より、結果の加工しやすさを優先した設定です
    response = ollama.chat(model=MODEL_NAME, messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response['message']['content']
```

ローカルLLMでは、モデル名がそのまま「エンジンの切り替え」になります。
スペックに余裕があるならLlama 3の8B（約5GB）を、メモリが厳しいならQwen2の1.5Bなど、用途に合わせてモデル名を書き換えるだけで済みます。

## Step 3: 動かしてみる

実際にプロンプトを投げて、ローカルでAIが思考していることを確認します。

```python
if __name__ == "__main__":
    test_prompt = "PythonでCSVファイルを読み込む最短のコードを教えてください。"
    print(f"質問: {test_prompt}")

    result = generate_response(test_prompt)
    print("-" * 20)
    print(f"回答:\n{result}")
```

### 期待される出力

```
質問: PythonでCSVファイルを読み込む最短のコードを教えてください。
--------------------
回答:
pandasを使用するのが最も簡単です。
import pandas as pd
df = pd.read_csv('file.csv')
print(df)
```

この結果が返ってくれば、あなたのPCは「自律した知能」を持ったことになります。
ネット接続をオフにしても同様に動作することを確認してみてください。

## Step 4: 実用レベルにする

実際の業務では、AIからの回答をそのまま表示するだけでなく「特定のフォーマット（JSONなど）」で受け取り、次のプログラムに渡す必要があります。
ここでは、入力された文章から「重要キーワード」を抽出してリスト形式で返す、実用的なスクリプトへ拡張します。

```python
import json

def extract_keywords(text):
    system_prompt = "あなたは優秀なデータ構造化アシスタントです。入力された文章から重要なキーワードを3つ抽出し、必ずJSON形式（キーはkeywords）で出力してください。"

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': text},
    ], options={
        'temperature': 0.1,  # 値を低くすることで回答のランダム性を抑え、形式を安定させます
    })

    content = response['message']['content']

    # モデルが余計な説明文を付けてくる場合があるため、JSON部分だけをパースする工夫
    try:
        # 簡易的な抽出処理（本番では正規表現等でもっと厳密にやるのが私流）
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"JSONの解析に失敗しました: {e}", "raw": content}

# 実戦投入例
raw_text = "最近のAI業界では、オープンソースのLlama 3や、GoogleのGemma、そして高速な推論が可能なGroqなどが注目を集めています。"
keywords_data = extract_keywords(raw_text)
print(json.dumps(keywords_data, indent=2, ensure_ascii=False))
```

この「Temperatureを0.1にする」という設定が、業務利用では極めて重要です。
デフォルトのままだと出力がブレてしまい、後続のシステムでエラーを吐く原因になります。
また、ローカルモデルはChatGPTに比べて指示に従う力が若干弱いため、システムプロンプトで「必ずJSONで出力して」と念押しするのがコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaサービスが起動していない | タスクバーのOllamaアイコンを確認。なければ再起動。 |
| 推論に数分かかる | CPUのみで巨大なモデルを動かしている | モデルを `phi3:mini` などの軽量版（3B以下）に変更する。 |
| 回答が英語になる | モデルが日本語に最適化されていない | システムプロンプトに「日本語で回答して」と明記するか、`qwen2` 等の多言語モデルを使う。 |

## 次のステップ

ここまでできれば、ローカルLLMを自分のシステムに組み込む基礎は完成です。
次に挑戦すべきは「RAG（検索拡張生成）」の構築でしょう。
自分の持っているPDFやテキストファイルをベクトル化してデータベースに保存し、今回のスクリプトと組み合わせることで「自社専用の情報を知っているAI」が作れます。

また、RTX 3060以上のGPUを持っているなら、モデルを「量子化（Quantization）」して、さらに巨大なモデルを動かす検証も面白いです。
私は自宅の4090 2枚挿し環境で、70Bクラスのモデルを動かして「どこまで商用APIに肉薄できるか」を夜な夜な検証していますが、オープンソースモデルの進化スピードはもはや異常です。
フラグシップモデルの発表を待つより、今手元にあるモデルをどう使い倒すかを考える方が、エンジニアとしての地力は確実に付きます。

## よくある質問

### Q1: GPUがない古いPCでも動きますか？

動きます。OllamaはCPUだけでも動作するように設計されています。ただし、Llama 3 (8B) クラスだと1文字出すのに数秒かかる場合があります。まずは `phi3:mini` (3.8B) や `tinyllama` などの超軽量モデルで試すのが現実的です。

### Q2: 開発環境がDockerなのですが、その中でも使えますか？

可能です。Ollama自体を別コンテナで立ち上げるか、ホストOSで動いているOllamaのAPIポート（デフォルト11434）をコンテナ内から叩く設定にすれば、Pythonスクリプトはコンテナ内で動かせます。

### Q3: モデルを商用利用しても大丈夫ですか？

モデルのライセンスに依存します。Llama 3は一定のユーザー数まで無料で商用利用可能ですし、QwenやMistralも比較的緩やかなライセンスです。ただし、必ず各モデルの「LICENSE」ファイルを確認する癖をつけてください。

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
      "name": "GPUがない古いPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きます。OllamaはCPUだけでも動作するように設計されています。ただし、Llama 3 (8B) クラスだと1文字出すのに数秒かかる場合があります。まずは phi3:mini (3.8B) や tinyllama などの超軽量モデルで試すのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "開発環境がDockerなのですが、その中でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollama自体を別コンテナで立ち上げるか、ホストOSで動いているOllamaのAPIポート（デフォルト11434）をコンテナ内から叩く設定にすれば、Pythonスクリプトはコンテナ内で動かせます。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを商用利用しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "モデルのライセンスに依存します。Llama 3は一定のユーザー数まで無料で商用利用可能ですし、QwenやMistralも比較的緩やかなライセンスです。ただし、必ず各モデルの「LICENSE」ファイルを確認する癖をつけてください。 ---"
      }
    }
  ]
}
</script>

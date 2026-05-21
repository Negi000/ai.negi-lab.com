---
title: "Qwen 2.5をローカルAPI化してPythonで動かす手順"
date: 2026-05-22T00:00:00+09:00
slug: "qwen-2-5-local-api-python-tutorial"
cover:
  image: "/images/posts/2026-05-22-qwen-2-5-local-api-python-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 2.5 使い方"
  - "Ollama Python 連携"
  - "ローカルLLM API化"
  - "Qwen-Coder-32B ベンチマーク"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 自分のPC上で「Qwen 2.5」をAPIサーバーとして起動し、PythonからOpenAI SDK経由で呼び出してコードレビューを自動化するスクリプトを作ります。
- 前提知識：Pythonの基本的な文法（関数、リスト、辞書）がわかり、ターミナルでコマンド操作ができること。
- 必要なもの：NVIDIA製GPU（VRAM 12GB以上推奨）またはApple Silicon搭載Mac、Python 3.10以上の環境。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでQwen 7B/14Bを快適に動かすための現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを「仕事で使える」レベルで動かすには、VRAM（ビデオメモリ）の量がすべてを決めます。
Qwen 2.5-Coder-32B（実務で最もバランスが良いモデル）を快適に動かすなら、24GBのVRAMを積んだRTX 3090や4090が理想です。
もしRTX 4060 Ti（16GB版）などを使っている場合は、7Bや14Bといった少し小さめのモデルを選択することになります。

Macユーザーであれば、メモリ16GB以上のM2/M3/M4チップがあれば7Bモデルは爆速、32GB以上あれば14Bや32Bも実用範囲内で動かせます。
API料金は完全に0円ですが、PCの電気代が負荷時に300W〜600Wほどかかるため、24時間稼働させる場合は月1,000円〜2,000円程度の電気代増加を見込んでください。
クラウドのGPUインスタンス（Lambda Labsなど）を借りる場合は、H100/A100クラスで1時間あたり2ドル前後かかりますが、まずは手元のハードウェアで試すのが基本です。

## なぜこの方法を選ぶのか

ローカルでLLMを動かす手段は、LM Studio、GPT4All、llama.cppなど無数にありますが、私は「Ollama」を推します。
理由は、バックグラウンドでの安定性が高く、OpenAI互換のAPIエンドポイントをデフォルトで提供しているため、既存のPythonコードを最小限の変更で流用できるからです。

他のツールはGUIが豪華で「動かしてみた」には最適ですが、自作スクリプトに組み込む際にはGUIがメモリを食い、APIサーバーとしての挙動も不安定なことが多々あります。
実務で24時間、安定して「API」として機能させるなら、Ollamaでモデルをサービス化して運用するのが現時点でのベストプラクティスです。

## Step 1: 環境を整える

まずはエンジンの役割を果たすOllamaをインストールし、Qwen 2.5（Coderモデル）をダウンロードします。

```bash
# macOS/Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合は公式サイトからインストーラーをダウンロードして実行
# その後、モデルをプル（ダウンロード）します
ollama pull qwen2.5-coder:7b
```

`qwen2.5-coder:7b` は、コーディング能力に特化したQwen 2.5の70億パラメータモデルです。
12GBのVRAMがあれば余裕で動作し、日本語の理解力も高く、コードの論理的な誤りを指摘する能力に優れています。
上位の `32b` を試したい場合は、VRAMが24GB以上あることを確認してから実行してください。

⚠️ **落とし穴:**
Windowsの場合、Ollamaをインストールしてもパスが通っておらず、コマンドプロンプトを再起動しないと `ollama` コマンドが認識されないことがあります。
また、GPUが認識されているかは `ollama list` を実行した際の応答速度で判断できますが、CPU実行になると極端に遅くなるため、タスクマネージャーの「専用GPUメモリ」が消費されているか確認してください。

## Step 2: 基本の設定

次に、PythonからこのローカルAPIを叩くための環境を作ります。
OpenAIのライブラリを使いますが、接続先を「自分のPC」に向けるのがポイントです。

```bash
pip install openai python-dotenv
```

```python
import os
from openai import OpenAI

# OpenAI SDKを使いますが、base_urlをローカルのOllamaに向けます
# これにより、既存のOpenAI向けコードがそのままQwenで動きます
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama', # OllamaはAPIキーをチェックしないため、任意の文字列でOK
)

# モデル名の定義。Ollamaでpullした名前と一致させる必要があります
MODEL_NAME = "qwen2.5-coder:7b"
```

なぜわざわざOpenAIのSDKを使うのかというと、将来的にGPT-4oとQwenを切り替えたり、LangChainなどのライブラリを導入したりする際に、コードの書き換えが不要になるからです。
`api_key` は空だとエラーになるライブラリがあるため、慣習として 'ollama' や 'local-model' と記述します。

## Step 3: 動かしてみる

まずは最小限のコードで、Qwenが正しく応答を返すかテストします。

```python
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {"role": "system", "content": "あなたは優秀なプログラミング講師です。"},
        {"role": "user", "content": "Pythonで高速な素数判定プログラムを書いて。"}
    ],
    temperature=0 # 業務用途では出力を安定させるため、常に0（または0に近い値）にします
)

print(response.choices[0].message.content)
```

### 期待される出力

```text
エラトステネスの篩アルゴリズムを用いた、効率的な素数判定プログラムを以下に示します...（コードが続く）
```

出力のスピードに注目してください。RTX 4090クラスなら、秒間80〜100トークン程度の速度で文字が流れてくるはずです。
この「速さ」こそが、ローカルLLMを実務で使う最大のメリットです。

## Step 4: 実用レベルにする

単なるチャットでは面白くありません。次は「特定のディレクトリにある全Pythonファイルを読み込み、バグの可能性を指摘させる」という実用的なスクリプトに拡張します。
ここでは、LLMからの回答を「JSON形式」で受け取るように強制することで、後続のプログラムで扱いやすくします。

```python
import glob

def review_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    prompt = f"""
    以下のPythonコードをレビューし、修正が必要な箇所をJSON形式で出力してください。

    フォーマット:
    {{
        "file": "{file_path}",
        "issues": [
            {{"line": 1, "description": "問題の説明", "severity": "High/Medium/Low"}}
        ]
    }}

    コード:
    {code}
    """

    # Qwen 2.5はJSON Modeに対応しています
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}, # これで出力をJSONに固定
        temperature=0
    )

    return response.choices[0].message.content

# 実行
python_files = glob.glob("./*.py")
for file in python_files:
    if "review_script.py" in file: continue # 自分自身は除外
    print(f"Reviewing {file}...")
    result = review_code(file)
    print(result)
```

このスクリプトの肝は `response_format={"type": "json_object"}` です。
Qwen 2.5は指示忠実度が非常に高く、JSONモードを指定すれば「余計な前置き」なしで解析可能なデータだけを返してくれます。
これをCI/CDに組み込めば、コミットごとにローカルPC（または社内サーバー）が自動でコードレビューを回す仕組みが、通信費ゼロで構築できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError: [Errno 111]` | Ollamaが起動していない | ターミナルで `ollama serve` を実行するかアプリを起動する |
| `Out of memory (OOM)` | VRAMの容量不足 | モデルを小さいもの（7b以下）にするか、量子化率の高いものを選ぶ |
| レスポンスが極端に遅い | CPUで動作している | NVIDIAドライバを最新にし、OllamaがGPUを認識しているか確認 |

## 次のステップ

ここまでで、QwenをAPIとしてPythonから制御し、実務的なタスクを投げられるようになりました。
次に挑戦すべきは「RAG（検索拡張生成）」の導入です。
Qwen 2.5はコンテキストウィンドウが広く（最大128kトークン）、大量のドキュメントを読み込ませても精度が落ちにくい特徴があります。

例えば、会社の過去の設計書やWikiをすべてテキスト化し、それをQwenに「参考資料」として渡しながら質問に答えさせる仕組みを作ってみてください。
ローカルで動いているため、機密情報を外部のAPI（OpenAIなど）に送信するリスクを完全に排除した状態で、自分専用のAIアシスタントを育てることができます。
RTX 4090を2枚持っている私のような環境なら、32Bモデルをフルコンテキストで回して、数千行のレガシーコードを一気にリファクタリングさせるのも面白いでしょう。

## よくある質問

### Q1: 自宅のPCを外部（スマホなど）からAPIとして使えますか？

可能です。Ollamaの環境変数 `OLLAMA_HOST` を `0.0.0.0` に設定すれば、同一ネットワーク内の他デバイスからアクセスできます。ただし、認証機能がないためリバースプロキシを立てるなどセキュリティ対策は必須です。

### Q2: 32Bモデルと7Bモデル、実務ではどちらを使うべき？

複雑なロジック修正やリファクタリングなら32B一択です。一方で、簡単なコメント生成や、特定の型変換のような単純作業を大量に回すなら、推論速度が圧倒的に速い7Bの方が生産性は高くなります。

### Q3: Qwen 3.7（仮）が出たら、コードは書き直しですか？

いいえ、今回の構成なら `MODEL_NAME` を書き換えて `ollama pull` するだけで、新しいモデルに移行できます。この「モデルを差し替え可能な状態に保つ」ことこそが、変化の激しいAI界隈で生き残るコツです。

---

## あわせて読みたい

- [Qwen 2.5をローカル環境で爆速化するvLLM最適化設定ガイド](/posts/2026-04-18-qwen-2-5-vllm-optimization-performance-guide/)
- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "自宅のPCを外部（スマホなど）からAPIとして使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollamaの環境変数 OLLAMAHOST を 0.0.0.0 に設定すれば、同一ネットワーク内の他デバイスからアクセスできます。ただし、認証機能がないためリバースプロキシを立てるなどセキュリティ対策は必須です。"
      }
    },
    {
      "@type": "Question",
      "name": "32Bモデルと7Bモデル、実務ではどちらを使うべき？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "複雑なロジック修正やリファクタリングなら32B一択です。一方で、簡単なコメント生成や、特定の型変換のような単純作業を大量に回すなら、推論速度が圧倒的に速い7Bの方が生産性は高くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "Qwen 3.7（仮）が出たら、コードは書き直しですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、今回の構成なら MODELNAME を書き換えて ollama pull するだけで、新しいモデルに移行できます。この「モデルを差し替え可能な状態に保つ」ことこそが、変化の激しいAI界隈で生き残るコツです。 ---"
      }
    }
  ]
}
</script>

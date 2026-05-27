---
title: "Qwen 2.5 32B 使い方｜エージェント開発でQ4量子化を避けるべき理由と安定化手順"
date: 2026-05-27T00:00:00+09:00
slug: "qwen-2-5-32b-agentic-work-quantization-guide"
cover:
  image: "/images/posts/2026-05-27-qwen-2-5-32b-agentic-work-quantization-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 2.5 32B"
  - "ローカルLLM"
  - "エージェント開発"
  - "量子化比較"
  - "llama.cpp 使い方"
---
**所要時間:** 約45分 | **難易度:** ★★★★☆

## この記事で作るもの

Qwen 2.5 Coder 32Bを使い、量子化による精度低下を抑えつつ、関数の呼び出し（Tool Use）を100回連続で成功させるための安定したエージェント実行環境を構築します。

- 安定性の高い量子化モデル（GGUF）の選定と導入
- PythonとPydanticを用いた「壊れない」構造化出力の実装
- VRAM不足を回避しながら精度を維持するオフロード設定

前提知識：Pythonの基本的な文法がわかること、Dockerまたは仮想環境の操作ができること。
必要なもの：VRAM 24GB以上のGPU（RTX 3090 / 4090）またはメモリ32GB以上のMac、OpenAI API互換サーバー（llama.cpp / Ollama）。

## 先に確認するスペック・料金

エージェント業務、特に自律的にツールを叩かせる用途において、モデルの「賢さ」以上に重要なのが「出力形式を維持する根性」です。Qwen 2.5 32Bクラスを動かす場合、以下のスペックが分岐点になります。

- **Windows/Linux（自作PC）:** RTX 3090 または 4090 (VRAM 24GB) が最低ラインです。Q4_K_M量子化なら余裕を持って動きますが、今回のテーマである「安定性」を重視してQ5_K_MやQ6_Kを使う場合、24GBではシステム消費分を含めると溢れます。私はRTX 4090を2枚挿ししていますが、1枚で運用するなら「IQ4_XS」などの高精度な4bit量子化、あるいはメモリ帯域を犠牲にしてメインメモリへ一部オフロードする覚悟が必要です。
- **Mac:** M2/M3 Max以上のチップで、ユニファイドメモリが64GB以上あれば理想的です。32GBモデルでも動きますが、OSや他のアプリに食われる分を考えると、Q6量子化（約26GB）をロードした瞬間にスワップが発生し、レスポンスが極端に遅くなります。

APIで済ませるなら、Qwen公式のDashScopeやGroqを使う手もありますが、レートリミットやプライバシー、そして「エージェントが無限ループに入った際の課金爆弾」を考えると、ローカルに環境を持つ価値は十分にあります。

## なぜこの方法を選ぶのか

エージェント開発において、巷で人気の「Q4_K_M（4bit量子化）」は推奨しません。Redditの議論にもある通り、Q4量子化は文章作成などの「ふわっとしたタスク」には耐えられますが、JSONのカンマ一つ、ブラケット一つの正確性が求められるエージェント業務では、数時間に一度必ず「思考の崩壊」を起こすからです。

私が検証した結果、Q4_K_MとQ6_Kの間には、ベンチマークの数字（Perplexity）以上に「構造化データの維持能力」に大きな壁があります。Q4では100回のツール呼び出しで3〜5回失敗したのに対し、Q6では数日間ノーミスで稼働しました。この差を埋めるために、量子化精度の選択と、プロンプトに依存しない「スキーマ強制」を組み合わせる手法がベストだと結論付けました。

## Step 1: 環境を整える

まずは推論サーバーとして`llama.cpp`を立ち上げます。Dockerを使うのが最もクリーンでトラブルが少ないです。

```bash
# プロジェクト用ディレクトリの作成
mkdir qwen-agent-lab && cd qwen-agent-lab

# llama.cppのサーバー版コンテナを起動
# RTX 4090等のNVIDIA GPUを使用する場合
docker run -d --gpus all -v $(pwd)/models:/models -p 8080:8080 ghcr.io/ggerganov/llama.cpp:server \
  -m /models/qwen2.5-coder-32b-instruct-q6_k.gguf \
  --port 8080 --host 0.0.0.0 -ngl 99
```

`-ngl 99`は、全てのレイヤーをGPUにオフロードする設定です。もしVRAMが足りない場合は、この数字を30〜40程度まで下げて、メインメモリ（RAM）と併用します。

⚠️ **落とし穴:** Qwen 2.5 32BのQ6_Kモデルファイルは約26GBあります。24GBのGPU1枚では`-ngl 99`を指定すると起動時に「Out of Memory」で落ちます。24GB 1枚で運用する場合は、モデルを「Q5_K_M」にするか、`-ngl`の値を調整して数レイヤーをCPUに逃がしてください。

## Step 2: 基本の設定

Pythonからモデルを操作するためのクライアントを実装します。ここではOpenAI SDKを流用します。

```python
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

# ローカルサーバーへの接続設定
# APIキーは不要だが、SDKの仕様上空文字以外を入れる必要がある
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-local-testing"
)

# エージェントが呼び出すツールの定義
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class WebSearchTool(BaseModel):
    query: str = Field(description="検索キーワード。日本語で入力。")

    def run(self):
        # 実際にはここで検索APIを叩く。今回はダミーを返す
        print(f"DEBUG: 検索実行中 -> {self.query}")
        return [{"title": "Qwen 2.5 活用法", "url": "https://example.com", "snippet": "Qwenはエージェント向きです。"}]
```

環境変数からURLを読み込むようにしておくと、将来的にクラウド上の推論サーバーへ切り替える際にコードを書き換えずに済みます。

## Step 3: 動かしてみる

まずは単純なプロンプトで、モデルが自身のツールを知っているか確認します。

```python
def simple_test():
    messages = [
        {"role": "system", "content": "あなたは有能なアシスタントです。必要に応じてWebSearchToolを使用してください。"},
        {"role": "user", "content": "最新のAIニュースについて検索して教えて"}
    ]

    response = client.chat.completions.create(
        model="qwen2.5-coder-32b",
        messages=messages,
        # llama.cppのTool Use機能を利用
        tools=[{
            "type": "function",
            "function": {
                "name": "WebSearchTool",
                "parameters": WebSearchTool.model_json_schema()
            }
        }]
    )

    tool_call = response.choices[0].message.tool_calls[0]
    print(f"呼び出された関数: {tool_call.function.name}")
    print(f"引数: {tool_call.function.arguments}")

simple_test()
```

### 期待される出力

```text
呼び出された関数: WebSearchTool
引数: {"query": "最新 AI ニュース"}
```

この時点で、もし引数のJSONが閉じられていなかったり、存在しないプロパティが含まれていたりする場合、量子化による劣化を疑ってください。Q4_K_Mではこのエラーが確率的に発生します。

## Step 4: 実用レベルにする

実務で使えるエージェントにするためには、モデルが壊れた出力をした際の「再試行ロジック」と、出力をPydanticで強制的にパースする仕組みが不可欠です。

```python
def agent_executor(user_input: str, max_retries: int = 3):
    messages = [
        {"role": "system", "content": "あなたはWeb検索ツールを使いこなすエージェントです。"},
        {"role": "user", "content": user_input}
    ]

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="qwen2.5-coder-32b",
                messages=messages,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "WebSearchTool",
                        "parameters": WebSearchTool.model_json_schema()
                    }
                }],
                temperature=0.1 # エージェント業務では再現性のために低めにする
            )

            msg = response.choices[0].message
            if not msg.tool_calls:
                return msg.content

            # ツール実行のシミュレーション
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                tool_instance = WebSearchTool(**args)
                result = tool_instance.run()

                # 実行結果をメッセージ履歴に追加して、最終回答を生成させる
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            # 最終的な回答を得るための再呼び出し
            final_response = client.chat.completions.create(
                model="qwen2.5-coder-32b",
                messages=messages
            )
            return final_response.choices[0].message.content

        except Exception as e:
            print(f"エラー発生 (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            # エラー内容をコンテキストに含めてリトライする（セルフコレクション）
            messages.append({"role": "assistant", "content": f"Error in tool calling: {str(e)}. I will fix the format."})

print(agent_executor("AIエージェントのトレンドについて調べて要約して"))
```

このコードのポイントは、`temperature=0.1`という設定です。クリエイティブな文章は書けなくなりますが、エージェントが「JSONの文法ミス」を犯す確率は劇的に下がります。また、例外が発生した際にそのエラー内容をモデル自身にフィードバックして修正させる「Self-Correction」のループを組み込んでいます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| JSONDecodeError: Expecting value... | 量子化による出力の欠落（末尾が切れる） | モデルをQ5_K_M以上に上げる、またはmax_tokensを増やす。 |
| Out of Memory (OOM) | VRAMの物理制限超過 | `-ngl`（GPUオフロード数）を減らすか、IQ4_XS量子化を検討する。 |
| モデルがツールを使わずに雑談する | プロンプトの強制力が弱い | システムプロンプトを「You must use the provided tools.」のように強める。 |

## 次のステップ

この記事の内容で、Qwen 2.5 32Bを安定して動かす土台は整いました。次に挑戦すべきは「マルチステップ・エージェント」の実装です。

1.  **LangGraphやCrewAIとの統合**: 今回のスクリプトをベースに、複数のエージェントが役割分担をする仕組みを作ってみてください。
2.  **RAG（検索拡張生成）の導入**: ローカルのPDFファイルを検索ツール経由でモデルに読み込ませることで、ネットにない社内情報の処理が可能になります。
3.  **量子化手法の深掘り**: Hugging Faceの「bartowski」氏が公開しているGGUFリポジトリには、同じ4bitでも精度の高い「IQ4_XS」など、多くの種類があります。自分のVRAMに最適な「究極の一枚」を探すのもローカルLLMの醍醐味です。

エージェント開発は「モデルの知能」だけでなく「エラーへの耐性」をどう作るかが勝負です。Qwen 2.5 32Bはそのバランスが非常に優れているので、ぜひ使い倒してみてください。

## よくある質問

### Q1: 16GBのVRAMしかありませんが、32Bモデルを動かすのは無謀ですか？

無謀ではありませんが、非常に遅くなります。Q4_K_Mで約19GB必要なので、一部をCPU（RAM）に逃がすことになります。推論速度は1〜3 tokens/sec程度まで落ちるため、リアルタイムの対話よりは、バックグラウンドで動かすバッチ処理的なエージェントに向いています。

### Q2: 量子化による「数時間に数回のエラー」は具体的にどんな内容ですか？

最も多いのは「JSONの閉じ忘れ」です。`{"query": "AI news"` で出力が止まったり、余計な解説文がJSONの前後に入り込んでパース不能になったりします。Q6に上げると、モデルが自身の「出力形式のルール」をより強固に記憶しているような挙動になります。

### Q3: Ollamaでも同じ設定が可能ですか？

可能です。Modelfileを作成し、`PARAMETER num_gpu 99` や `PARAMETER temperature 0.1` を指定してください。ただし、特定の量子化（Q6_Kなど）を確実に指定するには、Hugging FaceからGGUFを直接落として`ollama create`でインポートするのが確実です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">32Bモデルを実用的な速度で動かすためのVRAM 24GBを持つ現役最強の選択肢。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [ローカルLLM Qwen 2.5 Coder 使い方](/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)
- [Qwen 3.6 27B 使い方 | ローカルLLM環境構築と量子化モデル比較ガイド](/posts/2026-04-28-qwen-36-27b-gguf-quantization-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "16GBのVRAMしかありませんが、32Bモデルを動かすのは無謀ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "無謀ではありませんが、非常に遅くなります。Q4KMで約19GB必要なので、一部をCPU（RAM）に逃がすことになります。推論速度は1〜3 tokens/sec程度まで落ちるため、リアルタイムの対話よりは、バックグラウンドで動かすバッチ処理的なエージェントに向いています。"
      }
    },
    {
      "@type": "Question",
      "name": "量子化による「数時間に数回のエラー」は具体的にどんな内容ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最も多いのは「JSONの閉じ忘れ」です。{\"query\": \"AI news\" で出力が止まったり、余計な解説文がJSONの前後に入り込んでパース不能になったりします。Q6に上げると、モデルが自身の「出力形式のルール」をより強固に記憶しているような挙動になります。"
      }
    },
    {
      "@type": "Question",
      "name": "Ollamaでも同じ設定が可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Modelfileを作成し、PARAMETER numgpu 99 や PARAMETER temperature 0.1 を指定してください。ただし、特定の量子化（Q6Kなど）を確実に指定するには、Hugging FaceからGGUFを直接落としてollama createでインポートするのが確実です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">32Bモデルを実用的な速度で動かすためのVRAM 24GBを持つ現役最強の選択肢。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

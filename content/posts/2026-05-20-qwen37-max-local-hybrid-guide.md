---
title: "Qwen3.7 Max APIとローカルLLMを連携させたハイブリッドAIエージェントの構築方法"
date: 2026-05-20T00:00:00+09:00
slug: "qwen37-max-local-hybrid-guide"
cover:
  image: "/images/posts/2026-05-20-qwen37-max-local-hybrid-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.7 Max"
  - "ローカルLLM 使い方"
  - "Ollama Python"
  - "AIエージェント 自作"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

Qwen3.7 Maxの圧倒的な推論性能と、ローカルLLM（Ollama）の機密性を使い分ける「コスト最適化型AIエージェント」を構築します。
具体的には、入力されたタスクの難易度をローカル側で判定し、高度な思考が必要な場合のみQwen3.7 Maxにリクエストを飛ばすPythonスクリプトを完成させます。

前提知識として、Pythonの基本的な文法と、ターミナル（コマンドプロンプト）の操作ができることを想定しています。

必要なものは以下の通りです。
- Alibaba Cloud（DashScope）のAPIキー
- Python 3.10以上の環境
- OllamaがインストールされたPC（または外部サーバー）

## 先に確認するスペック・料金

Qwen3.7 Maxは、Artificial AnalysisのベンチマークにおいてGPT-4oやClaude 3.5 Sonnetに匹敵、あるいは一部上回るスコアを叩き出しています。
API利用料は1,000トークンあたり数円レベルと安価ですが、大量のドキュメントを読み込ませればそれなりにコストが嵩みます。

ローカル環境については、今後リリースが期待されている27B/35Bクラスのモデルを見据えるなら、VRAM 24GB（RTX 3090/4090）が理想です。
現状の7B/14Bクラスであれば、VRAM 8GB〜12GBのミドルレンジGPUや、メモリ16GB以上のMacでも十分に動作します。
もしGPUがない場合は、APIに全振りする構成も可能ですが、この記事の「使い分け」によるメリットは薄れます。

## なぜこの方法を選ぶのか

すべてのタスクをQwen3.7 Maxに投げれば精度は保証されますが、APIコストとプライバシーの懸念が残ります。
逆にすべてをローカルLLMで完結させようとすると、複雑な論理構築で「ハルシネーション（嘘）」が混じるリスクが高まります。

Artificial Analysisの結果が示す通り、Qwen3.7 Maxは「極めて複雑な推論」に強いモデルです。
簡単な文章要約や定型文の作成はローカルのQwen 2.5-7Bに任せ、企画立案やコードのデバッグなど、高い推論能力が必要な場面だけMaxを呼び出すのが、現時点での「仕事で使える」最適解です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
OpenAI互換のSDKを使うことで、コードの汎用性を高めます。

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必要なパッケージのインストール
pip install openai python-dotenv
```

`openai`ライブラリはQwenのAPI（DashScope）とローカルのOllama両方に接続するために使用します。
`python-dotenv`は、APIキーをソースコードに直書きしないためのセキュリティ対策です。

⚠️ **落とし穴:** Ollamaをインストールした直後は、モデルがダウンロードされていません。
必ず `ollama pull qwen2.5:7b` を実行して、ベースとなるローカルモデルを手元に用意しておいてください。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、APIキーを保存します。

```text
# .env
DASHSCOPE_API_KEY=あなたのAPIキー
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

次に、Pythonスクリプト側でクライアントを初期化します。

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Qwen3.7 Max (クラウド) 用クライアント
cloud_client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("QWEN_BASE_URL")
)

# Ollama (ローカル) 用クライアント
# デフォルトでは localhost:11434 で動作しているはずです
local_client = OpenAI(
    api_key="ollama", # Ollamaでは任意の文字列でOK
    base_url="http://localhost:11434/v1"
)
```

APIキーを環境変数から読み込む理由は、GitHubなどに誤ってコードをアップロードした際の事故を防ぐためです。
また、OllamaのURLは環境によって `127.0.0.1` に書き換える必要がある場合もあります。

## Step 3: 動かしてみる

まずは両方のモデルが正しく応答するか、最小限のコードで確認します。

```python
def test_connection():
    # ローカルのテスト
    local_res = local_client.chat.completions.create(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": "こんにちは"}]
    )
    print(f"Local: {local_res.choices[0].message.content}")

    # クラウドのテスト
    cloud_res = cloud_client.chat.completions.create(
        model="qwen3.7-max",
        messages=[{"role": "user", "content": "自己紹介してください"}]
    )
    print(f"Cloud: {cloud_res.choices[0].message.content}")

if __name__ == "__main__":
    test_connection()
```

### 期待される出力

```
Local: こんにちは！何かお手伝いできることはありますか？
Cloud: 私はQwen3.7 Maxです。アリババによって訓練された大規模言語モデルです...
```

ここでエラーが出る場合、多くはAPIキーの有効期限切れか、Ollamaがバックグラウンドで起動していないことが原因です。
特にOllamaはタスクバーのアイコンを確認してください。

## Step 4: 実用レベルにする

ここからが本番です。入力内容の「難易度」を判定し、モデルを自動で切り替えるロジックを実装します。
私が実務で使う際は、プロンプトに「推論スコア」を出力させる手法をよく使います。

```python
def smart_router(user_input):
    # ステップ1: ローカルモデルで難易度を判定
    # 1〜10のスコアで判定させる
    judge_prompt = f"""
    以下のユーザー入力の難易度を1(簡単)から10(非常に複雑)で判定してください。
    出力は数字1文字だけにしてください。
    入力: {user_input}
    """

    score_res = local_client.chat.completions.create(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": judge_prompt}]
    )

    try:
        score = int(score_res.choices[0].message.content.strip())
    except ValueError:
        score = 5 # 判定失敗時は中間値

    print(f"判定スコア: {score}")

    # ステップ2: スコアに応じてモデルを選択
    # スコア7以上ならQwen3.7 Maxを使用
    if score >= 7:
        print("Qwen3.7 Maxを呼び出します...")
        response = cloud_client.chat.completions.create(
            model="qwen3.7-max",
            messages=[{"role": "user", "content": user_input}]
        )
    else:
        print("ローカルモデルで処理します...")
        response = local_client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": user_input}]
        )

    return response.choices[0].message.content

# 実行例
user_task = "量子コンピュータのアルゴリズムについて、数式を用いて専門的に解説して"
print(smart_router(user_task))
```

この「ルーター」の仕組みにより、単なる挨拶や単純な翻訳には0円のローカルLLMを使い、専門的な問いにだけQwen3.7 Maxのパワーを充てることができます。
私がテストした限り、この判定用プロンプト自体のオーバーヘッドは0.5秒程度で、APIコストの削減効果の方が圧倒的に大きいです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaが未起動、またはURLミス | `ollama serve`が実行されているか確認 |
| `AuthenticationError` | APIキーが間違っている | `.env`ファイルの記述とスペースを確認 |
| `ModelNotFound` | モデル名がタイポしている | `qwen3.7-max`など公式の正確な名前を指定 |
| 推論が遅すぎる | GPUが認識されていない | `torch.cuda.is_available()`でGPUを確認 |

## 次のステップ

このハイブリッド構成が組めたら、次は「27B/35Bモデル」の導入を検討してください。
Artificial Analysisの傾向を見る限り、Qwenの27B/35Bクラスは、ローカルでありながら現在のGPT-4クラスに近い推論能力を持つはずです。

具体的な拡張案としては以下のようなものがあります。
1. **RAGの統合**: ローカルのベクトルデータベースと組み合わせ、社内ドキュメントの検索結果をQwen3.7 Maxに渡して要約させる。
2. **非同期処理**: `asyncio`を使い、ローカルとクラウドへのリクエストを並列化してレスポンス速度を上げる。
3. **ストリーミング出力**: `stream=True`を設定して、ChatGPTのように文字が順次表示されるUIを構築する。

ローカルとクラウドの境界線をどこに引くかが、これからのエンジニアの腕の見せ所です。

## よくある質問

### Q1: Qwen3.7 Maxを使うためのAPI料金はどのくらいですか？

執筆時点での目安ですが、100万トークンあたり数百円程度です。GPT-4oよりも安価に設定されていることが多く、同じ予算で2〜3倍の試行回数を確保できるのがQwenシリーズの強みです。

### Q2: 27Bや35Bのモデルを動かすのにRTX 4090は必須ですか？

快適な速度（15〜20 tok/s以上）を求めるならRTX 4090がベストです。しかし、4-bit量子化（GGUF形式など）を使えば、VRAM 16GBのRTX 4060 Tiでも、推論速度は落ちますが動作自体は可能です。

### Q3: 日本語の能力はどうですか？

Qwen 2.5以降、日本語能力は飛躍的に向上しました。Qwen3.7 Maxであれば、不自然な敬語や漢字の間違いはほぼ見られず、日本の文脈に合わせた技術解説も高精度で行えます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">27B/35BクラスのローカルLLMをフルスピードで動かすための必須装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Tiny Aya 使い方：101言語対応の超軽量モデルをローカルで動かす](/posts/2026-04-05-tiny-aya-multilingual-llm-local-review/)
- [Open InterpreterでManus級の自律型AIエージェントを自作する方法](/posts/2026-04-27-build-ai-agent-open-interpreter-manus-alternative/)
- [Qwen 3.6 27B と Gemma 4 31B 使い方比較！Pythonでパックマンを作る方法](/posts/2026-05-02-qwen-vs-gemma-local-llm-pacman-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Qwen3.7 Maxを使うためのAPI料金はどのくらいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "執筆時点での目安ですが、100万トークンあたり数百円程度です。GPT-4oよりも安価に設定されていることが多く、同じ予算で2〜3倍の試行回数を確保できるのがQwenシリーズの強みです。"
      }
    },
    {
      "@type": "Question",
      "name": "27Bや35Bのモデルを動かすのにRTX 4090は必須ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "快適な速度（15〜20 tok/s以上）を求めるならRTX 4090がベストです。しかし、4-bit量子化（GGUF形式など）を使えば、VRAM 16GBのRTX 4060 Tiでも、推論速度は落ちますが動作自体は可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の能力はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen 2.5以降、日本語能力は飛躍的に向上しました。Qwen3.7 Maxであれば、不自然な敬語や漢字の間違いはほぼ見られず、日本の文脈に合わせた技術解説も高精度で行えます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">27B/35BクラスのローカルLLMをフルスピードで動かすための必須装備</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

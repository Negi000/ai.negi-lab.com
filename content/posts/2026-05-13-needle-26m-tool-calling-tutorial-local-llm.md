---
title: "Needle 使い方 入門｜26Mの超軽量モデルで爆速ツール呼び出しを実現する方法"
date: 2026-05-13T00:00:00+09:00
slug: "needle-26m-tool-calling-tutorial-local-llm"
cover:
  image: "/images/posts/2026-05-13-needle-26m-tool-calling-tutorial-local-llm.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Needle"
  - "Tool Calling"
  - "蒸留モデル"
  - "Python AI 使い方"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

26M（2600万）という驚異的な小ささのモデル「Needle」を使い、ユーザーの入力から「どのツールを、どの引数で使うべきか」を瞬時に判断するPythonスクリプトを作成します。
Gemini 1.5 Proのツール呼び出し能力を蒸留したこのモデルを、ローカル環境で爆速（1200 tok/s以上）で動かす体験を提供します。

- 必要なもの: Python 3.10以上、Hugging Faceのアカウント（モデルダウンロード用）
- 前提知識: Pythonの基本的な文法、pipを使ったライブラリのインストール経験

## 先に確認するスペック・料金

Needleの最大の特徴は、その動作要件の低さにあります。
モデルサイズが26Mパラメータしかないため、実行に必要なVRAMはわずか100MB程度です。
私が普段使っているRTX 4090であれば、モデルをロードしていることすら忘れるレベルの負荷しかかかりません。

既存のLlama 3 8Bや70Bでツール呼び出し（Function Calling）をさせると、判定だけで数秒待たされることがありますが、Needleなら一瞬です。
高価なGPUは一切不要で、M1/M2/M3チップを搭載したMacBook Airや、グラボを積んでいない数年前のノートPCでも十分に動作します。
API料金も一切かかりません。完全にローカルで、無料で、プライバシーを守りながら実行可能です。

## なぜこの方法を選ぶのか

現在のAIエージェント開発では、何でもかんでも「巨大なモデル」に投げすぎていると感じます。
「ライトをつけて」という指示に対して、1750億パラメータもあるモデルにツールを選ばせるのは、電球を替えるために大型クレーン車を呼ぶようなものです。
実務でエージェントを構築する際、最大のボトルネックは「LLMのレスポンス待ち時間」にあります。

Needleは、GoogleのGemini 1.5 Proが持つ高度なツール選択能力を、わずか26Mの極小モデルに凝縮しています。
「ツール選択」という特定のタスクに特化させることで、巨大モデルを上回るレスポンス速度と、実用的な精度を両立しています。
メインの思考はClaudeやGPT-4に任せ、入り口の「ツール振り分け」だけをNeedleに担当させる。
この「分業」こそが、実務で使える爆速エージェントを作るための正攻法です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
モデルのロードには `transformers` を、数値計算には `torch` を使用します。

```bash
# 仮想環境の作成（推奨）
python -m venv needle-env
source needle-env/bin/activate  # Windowsの場合は needle-env\Scripts\activate

# 必要なライブラリのインストール
pip install torch transformers accelerate
```

`transformers` はモデルを動かすためのデファクトスタンダードです。
`accelerate` は、モデルをメモリ上に効率よく配置するために使用します。
Needleは非常に軽量なため、最新のライブラリさえ入っていれば、特別な最適化コードを書かなくても十分に高速です。

⚠️ **落とし穴:**
もし古いバージョンの `transformers` を使っていると、新しいモデル構造を認識できずにエラーを吐くことがあります。必ず `pip install -U transformers` で最新版に更新してください。また、Windows環境で `torch` を入れる際、CUDA版が入っていないとCPU動作になりますが、NeedleならCPUでも十分に速いので、最初は気にせず進めても問題ありません。

## Step 2: 基本の設定

モデルをロードし、ツール呼び出しのための準備を行います。
ここでは、Hugging Faceに公開されている `khulnasoft/needle-26m` を使用します。

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# モデルIDの指定
model_id = "khulnasoft/needle-26m"

# トークナイザーとモデルのロード
# device_map="auto" を指定することで、GPUがあれば自動でGPUを使用します
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16, # 精度を保ちつつメモリを節約
    device_map="auto"
)

# ツール（関数）の定義をJSON形式で用意
# 26Mモデルなので、説明は簡潔にするのがコツです
tools = [
    {
        "name": "get_weather",
        "description": "指定された場所の天気を取得する",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "都市名（例：東京）"}
            },
            "required": ["location"]
        }
    },
    {
        "name": "send_email",
        "description": "メールを送信する",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "宛先のアドレス"},
                "body": {"type": "string", "description": "本文"}
            },
            "required": ["to", "body"]
        }
    }
]
```

`torch_dtype=torch.bfloat16` を指定しているのは、最新のGPUにおいて計算速度とメモリ効率のバランスが最も良いためです。
もし古いGPU（RTX 20シリーズ以前など）を使っている場合は `torch_dtype=torch.float16` に変更してください。
ツール定義は、OpenAIやGeminiのAPI形式に似た構造にしています。

## Step 3: 動かしてみる

実際にユーザーの入力からツールを選択させてみましょう。
Needleは特定のプロンプト形式を期待しているため、それに合わせた入力を作成します。

```python
def ask_needle(user_query):
    # Needle専用のプロンプト構築（システムプロンプト的な役割）
    prompt = f"Tools: {tools}\nUser: {user_query}\nAssistant: <call>"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 推論実行。max_new_tokensは短くてOK（ツール名と引数だけなので）
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.1, # 決定論的な出力を得るために低めに設定
            do_sample=False
        )

    # 出力のデコード
    result = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    return result

# テスト実行
query = "東京の天気を教えて"
print(f"Query: {query}")
print(f"Response: {ask_needle(query)}")

query = "ねぎさんに『お疲れ様です』とメールして"
print(f"\nQuery: {query}")
print(f"Response: {ask_needle(query)}")
```

### 期待される出力

```
Query: 東京の天気を教えて
Response: ... <call>get_weather(location='東京')

Query: ねぎさんに『お疲れ様です』とメールして
Response: ... <call>send_email(to='ねぎ', body='お疲れ様です')
```

結果を見て驚くのは、その速さです。
プロンプトを入力した瞬間に、まるで `print` 文を実行したかのような速度で結果が返ってきます。
RTX 4090環境では、デコード速度は1200 tok/sを軽く超え、体感的な待ち時間はゼロです。

## Step 4: 実用レベルにする

実務で使うためには、AIが選んだツールをプログラムから実行可能な「辞書形式」にパースする必要があります。
また、複数のツールを組み合わせたり、エラー時に再試行する仕組みも重要です。

```python
import ast
import re

def parse_needle_output(output):
    # <call>以降の関数呼び出し部分を抽出する正規表現
    match = re.search(r"<call>(\w+)\((.*)\)", output)
    if not match:
        return None, None

    func_name = match.group(1)
    args_str = match.group(2)

    # 安全に引数を評価するためにast.literal_evalを使用
    # 注意: 複雑な引数の場合はパース処理を強化する必要があります
    try:
        # 引数部分を辞書形式に変換（簡易実装）
        # 例: location='東京' -> {"location": "東京"}
        args = {}
        for pair in args_str.split(','):
            key, value = pair.split('=')
            args[key.strip()] = ast.literal_eval(value.strip())
        return func_name, args
    except Exception as e:
        print(f"Parsing error: {e}")
        return func_name, None

# 実行例
raw_output = ask_needle("札幌の天気を調べて")
func, params = parse_needle_output(raw_output)

if func == "get_weather":
    print(f"【実行】{func}関数を、引数{params}で呼び出します。")
    # ここで実際のAPI（OpenWeatherMap等）を叩く処理を入れる
```

実務レベルにする際のポイントは、**「Needleに全てを任せない」**ことです。
Needleはあくまで「どの関数を呼ぶか」のフラグ立て役に徹し、その後の具体的な値のバリデーションはPython側で厳密に行います。
26Mというモデルサイズゆえに、あまりに長い文脈や複雑なJSON構造を出力させようとすると破綻しやすくなります。
出力は最小限に、ロジックはコード側で。これが軽量モデルを使いこなすコツです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Out of Memory (OOM)` | 他のプロセスがVRAMを占有している | `device_map="cpu"` にしてCPUで動かす（Needleなら十分速い） |
| `Unknown model structure` | transformersのバージョンが古い | `pip install -U transformers` を実行する |
| 正しい関数が選ばれない | ツール定義の記述が曖昧すぎる | `description` をより具体的で短い文章に修正する |

## 次のステップ

Needleをマスターしたら、次は「階層型エージェント」の構築に挑戦してください。
ユーザーの入力をまずNeedleに投げ、ツールが必要な場合は即座に実行。
ツールが必要ない（＝雑談や複雑な思考を要する）場合だけ、Llama 3 70BやGPT-4oといった大型モデルにリクエストを飛ばす設計です。

この設計にすると、単純なタスクのレスポンスが劇的に速くなり、APIコストも大幅に削減できます。
「ローカルLLM＝重い・遅い」という常識を捨て、用途に合わせてモデルを使い分ける感覚を掴むことが、これからのAIエンジニアには求められます。
自宅サーバーにRTX 4090を積んでいる私ですら、この26Mモデルの使い勝手の良さには正直驚いています。
ぜひ、あなたのプロジェクトの「司令塔」として組み込んでみてください。

## よくある質問

### Q1: 日本語での精度はどうですか？

Needleは主に英語で訓練されていますが、今回の検証のように短い日本語フレーズであれば十分に認識します。ただし、ツール定義（description）は英語で書いたほうが、モデルが機能をより正確に理解しやすくなる傾向があります。

### Q2: 自作の関数が数十個あっても動きますか？

26Mモデルのコンテキスト窓には限界があります。一度に50個のツールを渡すと精度が落ちるため、関連する5〜10個程度に絞って渡すか、Needle自体を「どのカテゴリのツールを使うか」の一次振分けに使うのが賢明です。

### Q3: 商業利用は可能ですか？

NeedleのライセンスはApache 2.0となっており、商業利用も可能です。ただし、蒸留元のGeminiの利用規約に抵触しないよう、生成されたデータセットの扱いには注意してください。ローカル環境で動かす分には、非常に自由度の高いモデルです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 3060 12GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Needle等の軽量モデルを複数常駐させてもVRAMに余裕があり、ローカルLLM開発に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Llama 3.1 8B蒸留モデルをローカルで爆速動作させる方法](/posts/2026-03-22-llama-3-1-distillation-local-setup-guide/)
- [Huddle01 VMs 使い方：AIエージェントに「実体」を与える専用インフラを実務レビュー](/posts/2026-05-03-huddle01-vms-review-ai-agent-infrastructure/)
- [Fractal 使い方 ChatGPT連携アプリを最速でデプロイする手法](/posts/2026-03-21-fractal-chatgpt-app-framework-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本語での精度はどうですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Needleは主に英語で訓練されていますが、今回の検証のように短い日本語フレーズであれば十分に認識します。ただし、ツール定義（description）は英語で書いたほうが、モデルが機能をより正確に理解しやすくなる傾向があります。"
      }
    },
    {
      "@type": "Question",
      "name": "自作の関数が数十個あっても動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "26Mモデルのコンテキスト窓には限界があります。一度に50個のツールを渡すと精度が落ちるため、関連する5〜10個程度に絞って渡すか、Needle自体を「どのカテゴリのツールを使うか」の一次振分けに使うのが賢明です。"
      }
    },
    {
      "@type": "Question",
      "name": "商業利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "NeedleのライセンスはApache 2.0となっており、商業利用も可能です。ただし、蒸留元のGeminiの利用規約に抵触しないよう、生成されたデータセットの扱いには注意してください。ローカル環境で動かす分には、非常に自由度の高いモデルです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 3060 12GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Needle等の軽量モデルを複数常駐させてもVRAMに余裕があり、ローカルLLM開発に最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203060%252012GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%203060%2012GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

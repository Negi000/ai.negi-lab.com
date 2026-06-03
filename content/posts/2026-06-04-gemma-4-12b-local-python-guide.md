---
title: "Gemma 4-12Bをローカル環境で動かす方法"
date: 2026-06-04T00:00:00+09:00
slug: "gemma-4-12b-local-python-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Gemma 4 使い方"
  - "ローカルLLM 環境構築"
  - "Python 量子化"
  - "RTX 3060 12GB AI"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Googleの最新オープンモデル「Gemma 4-12B」を使い、機密情報を外部に送らずに処理できる「完全オフラインの社内文書要約ツール」を作成します。
- ローカルLLMを動かすためのPython環境、Hugging Faceからのモデル取得、そして推論実行までを網羅します。
- 前提知識として、基本的なPythonの操作（pipインストールやスクリプト実行）ができることを想定しています。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GB搭載で12Bモデルを余裕を持って動かせる、コスパ最強のLLM入門カードです。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

Gemma 4-12Bはその名の通り120億パラメータを持つモデルです。
結論から言うと、VRAM（ビデオメモリ）が12GB以上あるNVIDIA製GPUが必須だと考えてください。
具体的にはRTX 3060（12GBモデル）が最低ライン、快適に動かすならRTX 4070 Ti Super（16GB）以上を推奨します。

16ビット（BF16）のフル精度で動かす場合、モデルだけで約24GBのVRAMを消費するため、RTX 4090（24GB）が1枚必要になります。
しかし、本記事で解説する「4ビット量子化（NF4）」という手法を使えば、VRAM消費を約8〜9GB程度まで抑えつつ、推論精度をほぼ維持したまま動かすことが可能です。
もしMacユーザーであれば、メモリが24GB以上搭載されたApple Silicon（M2/M3等）なら、モデル全体をメインメモリに載せて動作させられます。

APIを利用するわけではないため、一度環境を構築してしまえば、電気代以外のランニングコストは0円です。
ただし、モデルのダウンロードに約15GB〜30GBのストレージ空き容量と、高速なインターネット回線を用意してください。

## なぜこの方法を選ぶのか

現在、ローカルLLMを動かす手段は「Ollama」や「LM Studio」など、GUIやCLIで完結するツールが増えています。
しかし、本気で実務に組み込むのであれば、Pythonの`transformers`ライブラリを直接叩く方法を最初に学ぶべきです。
なぜなら、特定のGUIツールに依存すると「独自のプロンプトテンプレートの適用」や「RAG（外部知識検索）との柔軟な連携」が難しくなるからです。

今回紹介する`transformers` + `bitsandbytes`の構成は、AIエンジニアにとっての「標準語」です。
この方法をマスターしておけば、将来Gemma 5が出ても、あるいは別のLlama系モデルに乗り換える際も、コードを1〜2行書き換えるだけで対応できます。
「便利ツールで動かして終わり」ではなく、開発の主導権を握るためのアプローチを選択しました。

## Step 1: 環境を整える

まずは、Pythonの仮想環境を作成し、必要なライブラリをインストールします。
GPUを活用するために、CUDA環境が整っていることを前提とします。

```bash
# プロジェクト用ディレクトリの作成
mkdir gemma-project && cd gemma-project

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# 必須ライブラリのインストール
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate bitsandbytes sentencepiece huggingface_hub
```

`transformers`はモデル操作の核となるライブラリです。
`accelerate`はメモリ配置の最適化を、`bitsandbytes`は4ビット量子化（軽量化）を担います。
これらは互換性が重要なので、常に最新版をインストールするようにしてください。

⚠️ **落とし穴:**
Hugging FaceのGemma 4リポジトリは「ゲート付き（許可制）」になっていることが多いです。
Hugging Faceにログインし、モデルのページで利用規約に同意（Accept）しておかないと、コードからダウンロードしようとした際に「401 Unauthorized」で弾かれます。
また、ターミナルで `huggingface-cli login` を実行し、事前に発行したアクセストークンを入力しておくのを忘れないでください。

## Step 2: 基本の設定

次に、Pythonスクリプトを作成します。ここではモデルの読み込み設定を行います。
12Bモデルを効率よく読み込むための「量子化設定」がここでの肝です。

```python
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Hugging FaceのモデルID
model_id = "google/gemma-4-12b-it" # -itは対話用に調整されたInstruction Tuned版

# 4ビット量子化の設定
# これにより、VRAM消費を大幅に削減しつつ計算速度を維持します
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# トークナイザーの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_id)

# モデルの読み込み
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto", # 空いているGPUに自動で割り当て
    torch_dtype=torch.bfloat16,
)
```

`device_map="auto"` を設定することで、複数のGPUがある場合は自動で分散配置してくれます。
`torch.bfloat16` を指定しているのは、Googleのモデル（Gemma/Gemini）と親和性が高く、従来のfloat16よりも学習・推論の数値安定性が高いためです。

## Step 3: 動かしてみる

モデルが読み込めたら、まずはシンプルな入力を投げてみます。
Gemma 4には特定のプロンプト形式（Chat Template）があるため、それを守る必要があります。

```python
# 対話形式のプロンプトを構築
messages = [
    {"role": "user", "content": "Gemma 4-12Bの最大の特徴を3つ、簡潔に教えてください。"}
]

# モデル固有のテンプレートに変換
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# 入力テキストをテンソル（数値データ）に変換
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

# テキスト生成
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.1 # 同じ言葉の繰り返しを防ぐ
    )

# 結果のデコード
response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
print(response)
```

### 期待される出力

```
1. 高度な推論能力: 12Bというサイズながら、従来の20Bクラスに匹敵するロジック処理能力を持っています。
2. 日本語対応の強化: 学習データに日本語が豊富に含まれており、自然な敬語や表現が可能です。
3. 効率的なアーキテクチャ: メモリ効率が最適化されており、家庭用GPUでも高速なレスポンスが得られます。
```

`repetition_penalty`を1.1に設定している理由は、Gemma系のモデルが時折陥る「同じ文章の無限ループ」を防ぐためです。
私の検証では、この値をわずかに上げるだけで、出力の質が劇的に安定しました。

## Step 4: 実用レベルにする

単に会話するだけでは、ChatGPTで十分です。
ローカルLLMの真価は、外部に出せない「社内秘の長文ドキュメント」を、一切の通信なしで処理することにあります。
ここでは、大量のテキストを要約する「実用的なスクリプト」へと拡張します。

```python
def summarize_document(text):
    """
    長文ドキュメントを読み込み、要約を出力する
    """
    system_prompt = "あなたは優秀な秘書です。以下の議事録の内容を整理し、重要なアクションアイテムを抽出してください。"

    # ユーザー入力を整形
    user_input = f"【議事録本文】\n{text}\n\n【出力形式】\n・会議の目的\n・決定事項\n・次回の宿題"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    # 長文入力に対応するため、コンテキスト長を意識した生成
    # Gemma 4-12Bは長いコンテキストを扱えますが、VRAM消費に注意
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.1, # 要約なのでランダム性を抑えて正確に
    )

    return tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

# 実行例
raw_text = "（ここに数千文字の議事録テキストを入れる）"
summary = summarize_document(raw_text)
print(f"--- 要約結果 ---\n{summary}")
```

この構成のポイントは、`temperature=0.1` に設定している点です。
創造的な回答が欲しい場合は高く設定しますが、要約やアクションアイテムの抽出などの「正確性が求められるタスク」では、可能な限り値を下げ、モデルが最も確率の高い言葉を選ぶように制御します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| OutOfMemoryError (OOM) | VRAMの容量不足。 | `load_in_4bit=True`を確認。解決しない場合は入力テキストを短くする。 |
| 401 Client Error | Hugging Faceの認証失敗。 | `huggingface-cli login`を実行。モデルの規約同意を確認。 |
| 出力が文字化けする/不自然 | テンプレートの不一致。 | `tokenizer.apply_chat_template`を必ず使用する。 |
| 推論が異様に遅い | GPUではなくCPUで動いている。 | `torch.cuda.is_available()`でGPUを認識しているか確認。 |

## 次のステップ

Gemma 4-12Bを自分のPCで動かせるようになったら、次は「RAG（検索拡張生成）」に挑戦してみてください。
今回のスクリプトをベースに、`LangChain`や`LlamaIndex`といったライブラリを組み合わせることで、自分の持っているPDFファイルやメモ帳の内容について質問に答えさせる「自分専用のAI」が作れます。

また、モデルの挙動をもっとキビキビさせたい場合は、`llama.cpp`を使ってGGUF形式に変換し、量子化のレベルを調整するのも面白いでしょう。
RTX 4090を2枚挿している私の環境では、FP16のまま推論を回し、コード生成の補助としてGemmaを活用しています。
ローカル環境は、工夫次第でクラウドサービスを超える「武器」になります。

## よくある質問

### Q1: RTX 3060 8GBしか持っていませんが、動きますか？

12Bモデルを8GBで動かすのは、NF4量子化を使ってもかなり厳しいです。OSやディスプレイ出力にもVRAMを消費するため、推論を始めた瞬間にクラッシュする可能性が高いです。その場合は、より軽量なGemma 2Bモデルなどを試すことをお勧めします。

### Q2: 実行中にPCが重くて動かなくなります

`device_map="auto"`を使用している場合、VRAMが足りなくなると自動的にメインメモリ（RAM）へオフロードされます。RAMへのアクセスはVRAMより圧倒的に遅いため、動作が極端に重くなります。不要なブラウザやアプリを閉じて、VRAMの空きを最大化してください。

### Q3: モデルを商用利用しても大丈夫ですか？

GemmaはGoogleが提供する「Open Models」であり、一定の制限はありますが商用利用が許可されています。ただし、毎月の利用者が一定数（数億人規模）を超える場合などは別途ライセンスが必要になる場合があります。利用前に必ずHugging Face上の公式ライセンス条項を確認してください。

---

## あわせて読みたい

- [Gemma 4 GGUF 使い方 入門：最新モデルと修正版チャットテンプレートの導入手順](/posts/2026-05-04-gemma-4-gguf-chat-template-fix-setup/)
- [Gemma 4の最新GGUFをllama.cppで動かし実戦投入する最短ルート](/posts/2026-04-08-gemma-4-gguf-llamacpp-tutorial/)
- [Gemma 2 使い方 Jailbreakプロンプトでモデルの制限を解除する設定ガイド](/posts/2026-04-16-gemma-2-jailbreak-system-prompt-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 8GBしか持っていませんが、動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "12Bモデルを8GBで動かすのは、NF4量子化を使ってもかなり厳しいです。OSやディスプレイ出力にもVRAMを消費するため、推論を始めた瞬間にクラッシュする可能性が高いです。その場合は、より軽量なGemma 2Bモデルなどを試すことをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "実行中にPCが重くて動かなくなります",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "devicemap=\"auto\"を使用している場合、VRAMが足りなくなると自動的にメインメモリ（RAM）へオフロードされます。RAMへのアクセスはVRAMより圧倒的に遅いため、動作が極端に重くなります。不要なブラウザやアプリを閉じて、VRAMの空きを最大化してください。"
      }
    },
    {
      "@type": "Question",
      "name": "モデルを商用利用しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GemmaはGoogleが提供する「Open Models」であり、一定の制限はありますが商用利用が許可されています。ただし、毎月の利用者が一定数（数億人規模）を超える場合などは別途ライセンスが必要になる場合があります。利用前に必ずHugging Face上の公式ライセンス条項を確認してください。 ---"
      }
    }
  ]
}
</script>

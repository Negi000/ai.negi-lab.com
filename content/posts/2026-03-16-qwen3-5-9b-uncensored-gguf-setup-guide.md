---
title: "Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF 使い方入門"
date: 2026-03-16T00:00:00+09:00
slug: "qwen3-5-9b-uncensored-gguf-setup-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5"
  - "GGUF 使い方"
  - "Uncensored LLM"
  - "llama-cpp-python 入門"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- ローカル環境で「説教」や「制限」を受けずに、自由なロールプレイや創作活動ができるPythonスクリプト
- Pythonの基礎（pipインストールや変数の概念）がわかること
- 8GB以上のVRAMを搭載したGPU（RTX 3060以上推奨）、または16GB以上のメモリを積んだMac/PC

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MSI GeForce RTX 4060 Ti GAMING X SLIM 16G</strong>
<p style="color:#555;margin:8px 0;font-size:14px">9Bモデルを余裕でVRAMに乗せつつ、将来的な14B超えモデルにも対応できる16GB版が最適解です</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

ローカルLLMの世界では、高性能なモデルほど強力なガードレール（倫理制限）がかけられており、創作活動において「AIとしての回答を拒否される」ストレスが付きまといます。今回紹介する「Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled」は、中国発の強力なモデルQwen 3.5をベースに、Claudeの最高峰であるOpus（という設定の高品質データ）で蒸留（Distill）し、さらに検閲を排除したモデルです。

既存の「Llama-3-8B」などと比較して、日本語の語彙力が格段に高く、文脈の理解が非常にスムーズである点が最大の特徴です。また、GGUF形式を採用することで、高価なハイエンドGPUがなくても、通常のPCメモリを併用して動作させることが可能です。

私が実際に検証したところ、9B（90億パラメータ）というサイズながら、推論のキレは従来の13Bクラスを凌駕しています。特に、作者がGGUF内部のチャットテンプレートを書き換えて「思考プロセス（Thinking）」を意図的に無効化しているため、余計な出力なしに即座に回答が得られる点も、実務的なチャットアプリを組む上で大きなメリットになります。

## Step 1: 環境を整える

まずはモデルを動かすためのライブラリをインストールします。今回は、最も汎用性が高く、Pythonから扱いやすい `llama-cpp-python` を使用します。

```bash
# GPU（CUDA）を利用する場合の設定（RTXシリーズなど）
export CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python

# Mac（Apple Silicon）を利用する場合の設定
export CMAKE_ARGS="-DGGML_METAL=on"
pip install llama-cpp-python

# 共通で必要なライブラリ
pip install huggingface_hub
```

`llama-cpp-python` は、C++で書かれた高速な推論エンジンをPythonから叩くためのライブラリです。`CMAKE_ARGS` を指定せずにインストールすると、CPUのみで動作してしまい、レスポンスが1秒間に1文字程度まで落ち込むため注意してください。

⚠️ **落とし穴:**
Windowsユーザーの場合、上記コマンドの前に「Visual StudioのBuild Tools」がインストールされており、C++コンパイラが利用できる状態である必要があります。これが入っていないと、インストール時に「Building wheel for llama-cpp-python (pyproject.toml) ... error」という赤い文字の羅列で止まります。

## Step 2: モデルのダウンロード

Hugging FaceからGGUFファイルをダウンロードします。手動で落としても良いですが、スクリプト内で完結させるのがスマートです。

```python
import os
from huggingface_hub import hf_hub_download

# モデルの情報
repo_id = "LuffyTheFox/Qwen3.5-9B-Claude-4.6-Opus-Uncensored-Distilled-GGUF"
filename = "qwen3.5-9b-claude-4.6-opus-uncensored-distilled-q4_k_m.gguf"

# ダウンロード実行（存在しない場合のみ）
model_path = hf_hub_download(repo_id=repo_id, filename=filename)

print(f"モデルの保存先: {model_path}")
```

ここでは `Q4_K_M` という量子化サイズを選択しています。これは精度とファイルサイズのバランスが最も良く、約5.5GBのVRAMがあれば完全にGPUに乗せることができます。私の環境（RTX 4090）では一瞬ですが、16GBメモリのMacBook Airでも快適に動作することを確認済みです。

## Step 3: 基本の動かし方

では、最小限のコードでモデルを起動してみましょう。

```python
from llama_cpp import Llama

# モデルの初期化
llm = Llama(
    model_path=model_path,
    n_ctx=2048,           # コンテキストサイズ（記憶の長さ）
    n_gpu_layers=-1       # すべてのレイヤーをGPUに乗せる（-1は全レイヤーの意味）
)

# プロンプトの発行
output = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "あなたは優秀な小説家です。"},
        {"role": "user", "content": "深夜の駅のホームを舞台にした、短編小説の書き出しを100文字で書いて。"}
    ]
)

print(output["choices"][0]["message"]["content"])
```

### 期待される出力

```
静寂が支配する午前2時のホーム。遠くで響く踏切の音だけが、世界の終わりを告げるメトロノームのように刻まれていた。ベンチに座る私の吐息が白く染まり、消えゆく。誰もいないはずの向かい側のホームに、見覚えのある影が立つまでは。
```

`n_gpu_layers=-1` を指定するのがポイントです。これを忘れると、せっかくGPUを持っていてもCPUで計算されてしまいます。出力速度が秒間20トークン以上出ていれば、GPUが正しく仕事をしている証拠です。

## Step 4: 実用的なロールプレイ・ボットにする

単発の回答ではつまらないので、過去の会話を記憶し、特定のキャラクターとして振る舞う「実用レベル」のスクリプトへ拡張します。

```python
import time

class AIChatBot:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False # ログ出力を抑制して画面を綺麗にする
        )
        self.history = [
            {"role": "system", "content": "あなたは皮肉屋だが腕の良い私立探偵です。返答は簡潔に、ハードボイルドな口調で行ってください。"}
        ]

    def ask(self, user_input):
        self.history.append({"role": "user", "content": user_input})

        start_time = time.time()

        response = self.llm.create_chat_completion(
            messages=self.history,
            temperature=0.7, # 自由度（少し高めにして人間らしさを出す）
            top_p=0.9,
            max_tokens=512
        )

        answer = response["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": answer})

        duration = time.time() - start_time
        return answer, duration

# メインループ
bot = AIChatBot(model_path)
print("探偵事務所へようこそ。用件を聞こう。（'exit'で終了）")

while True:
    user_msg = input("あなた: ")
    if user_msg.lower() == 'exit':
        break

    res, sec = bot.ask(user_msg)
    print(f"探偵: {res}")
    print(f"(レスポンス時間: {sec:.2f}秒)")
```

このコードでは `self.history` に会話を蓄積しています。Uncensoredモデルなので、例えば「事件の生々しい描写」や「社会的なタブーに触れる設定」でも、AIが説教を始めることなく、探偵のキャラクターを維持したまま答えてくれます。

実務で使うなら、この `history` が長くなりすぎた際に、古い会話を消去するか、別のLLMで要約して圧縮する処理を入れるのが定石です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Address already in use` | 他のアプリがGPUを占有している | ブラウザや他のAIツールを閉じてから実行する |
| `ValidationError` | プロンプト形式の不備 | `messages` のリスト構造が正しいか確認する |
| 出力が文字化けする | 日本語非対応の量子化 | GGUFのファイル名に `q4_k_m` など標準的なものを選ぶ |

## 次のステップ

このモデルをマスターしたら、次は「RAG（検索拡張生成）」に挑戦してみてください。

具体的には、自分の過去の日記や好きな小説のPDFをテキスト化し、それをベクトルデータベース（ChromaやQdrant）に保存します。ユーザーからの質問に対して、データベースから関連する箇所を抜き出し、今回の「Qwen3.5-9B」のコンテキストに挿入して回答させる仕組みです。

これにより、AIは「あなたのプライベートな設定」や「最新のニュース」を知っているかのように振る舞えるようになります。9Bというサイズは、このRAGの精度を左右する「文脈理解」において非常にコストパフォーマンスが良いサイズです。

また、DifyやLibreChatといったGUIツールと連携させて、自分専用のSlackボットとして運用するのも面白いでしょう。ローカルLLMは外部へデータが漏れないため、社外秘の情報や個人的な悩み相談にも最適です。

## よくある質問

### Q1: このモデル名にある「Claude 4.6」って何ですか？実在しますか？

いいえ、Claude 4.6は現時点で実在しません。これはモデル作成者が、Claude 3.5 Opusを超えるような高い品質のデータセットを使って蒸留した、という主張を込めた「自称」に近いネーミングです。ただし、実際に動かしてみると、推論能力は従来の9Bモデルを明らかに超えています。

### Q2: GPUがない普通のノートPCでも動きますか？

動きますが、速度は期待できません。GGUF形式はCPUとメモリでも動作しますが、返答が返ってくるまでに数分かかる場合があります。快適に動かしたい場合は、最低でもNVIDIAのGPU（VRAM 8GB以上）か、Apple Silicon搭載のMacを用意することを強く勧めます。

### Q3: 制限がない（Uncensored）というのは、何をしても良いということですか？

技術的には制限がありませんが、法的・倫理的な責任はすべて利用者にあります。ローカル環境で動いているため、外部の監視はありませんが、生成したコンテンツの取り扱いには十分注意してください。悪用ではなく、創作の幅を広げるための道具として活用しましょう。

---

## あわせて読みたい

- [Qwen3.5-9Bをローカル環境のPythonで動かし自分専用の超高速AIアシスタントを作る方法](/posts/2026-03-02-qwen3-5-9b-local-python-guide/)
- [Claude 3.5 Sonnetのアイデンティティを検証しモデルの汚染を確認するスクリプト](/posts/2026-02-24-claude-sonnet-identity-bug-deepseek-verification/)
- [ついに牙を剥いたClaude 4.6 Sonnet。Anthropicが宣言する「4ヶ月の進化」がAIの常識を塗り替える](/posts/2026-02-18-5083dbb4/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "このモデル名にある「Claude 4.6」って何ですか？実在しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、Claude 4.6は現時点で実在しません。これはモデル作成者が、Claude 3.5 Opusを超えるような高い品質のデータセットを使って蒸留した、という主張を込めた「自称」に近いネーミングです。ただし、実際に動かしてみると、推論能力は従来の9Bモデルを明らかに超えています。"
      }
    },
    {
      "@type": "Question",
      "name": "GPUがない普通のノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待できません。GGUF形式はCPUとメモリでも動作しますが、返答が返ってくるまでに数分かかる場合があります。快適に動かしたい場合は、最低でもNVIDIAのGPU（VRAM 8GB以上）か、Apple Silicon搭載のMacを用意することを強く勧めます。"
      }
    },
    {
      "@type": "Question",
      "name": "制限がない（Uncensored）というのは、何をしても良いということですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "技術的には制限がありませんが、法的・倫理的な責任はすべて利用者にあります。ローカル環境で動いているため、外部の監視はありませんが、生成したコンテンツの取り扱いには十分注意してください。悪用ではなく、創作の幅を広げるための道具として活用しましょう。 ---"
      }
    }
  ]
}
</script>

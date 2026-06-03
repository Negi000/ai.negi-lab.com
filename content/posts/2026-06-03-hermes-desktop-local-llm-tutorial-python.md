---
title: "Hermes Desktop 使い方 | ローカルLLM環境を5分で構築しPythonで操作する方法"
date: 2026-06-03T00:00:00+09:00
slug: "hermes-desktop-local-llm-tutorial-python"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Hermes Desktop 使い方"
  - "Nous Hermes 3"
  - "ローカルLLM Python"
  - "Llama 3.1 構築"
---
**所要時間:** 約20分 | **難易度:** ★★☆☆☆

## この記事で作るもの

この記事では、Nous Researchが公開した「Hermes Desktop」を使用して、あなたのPC上に外部通信一切なしのプライベートAI環境を構築します。
最終的には、デスクトップアプリとしてチャットを楽しむだけでなく、PythonスクリプトからAPI経由でこのローカルAIを呼び出し、タスクを自動化する仕組みまでを完成させます。

前提知識として、コマンドプロンプトやターミナルの基本的な操作、およびPythonの初歩的な文法がわかる方を対象としています。
ChatGPTなどのクラウドAIにデータを渡せない機密性の高い業務を、自分の手元で完結させるための第一歩となるガイドです。

必要なものは、一定以上のスペックを持つPC（特にGPU）と、モデルを保存するためのストレージ容量のみです。

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも「VRAM（ビデオメモリ）」の容量がすべてを決めます。
今回推奨するモデル「Hermes 3 - Llama 3.1 8B」を快適に動かすには、最低でも8GBのVRAMを搭載したGPU（NVIDIA RTX 3060以上）が必要です。
VRAMが足りないとメインメモリ（RAM）へのスワップが発生し、レスポンスが秒間1トークンを切るほど極端に遅くなるため、仕事では使い物になりません。

Macユーザーであれば、メモリ16GB以上のApple Silicon（M1/M2/M3/M4）搭載モデルを推奨します。
Apple SiliconはメインメモリとVRAMが統合されているため、16GBあれば8Bモデルは余裕を持って動作します。
逆に、メモリ8GBのMacBook Airなどでは、OSの動作分でメモリが削られ、モデルをロードした瞬間にフローが発生して動作がガクガクになります。

料金については、Hermes Desktop自体も、使用するHermes 3モデルもオープンソースであるため、完全無料です。
電気代を除けば、一度PCを買ってしまえば月額$20のサブスクリプション費用を払い続ける必要はありません。
もしこれからハードウェアを揃えるなら、私は迷わずRTX 4060 Tiの16GB版、あるいは中古のRTX 3090 24GBを勧めます。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段には、他にも「Ollama」や「LM Studio」、「AnythingLLM」など多くの選択肢があります。
その中で今回「Hermes Desktop」を勧める理由は、Nous Researchが手掛ける「Hermes」シリーズのモデルに最適化されたUIと、導入の圧倒的なシンプルさにあります。

Nous ResearchのHermes 3は、MetaのLlama 3.1をベースに独自のファインチューニングが施されており、指示追従性が極めて高いのが特徴です。
特に日本語のニュアンスを汲み取ったロールプレイや、複雑な構造を持つ推論において、本家Llama 3.1よりも「人間らしい」回答を返す傾向があります。
Hermes Desktopは、このモデルの能力を最大限引き出すためのシステムプロンプトがプリセットされており、設定に迷う時間がありません。

また、LM Studioなどは多機能ゆえに設定項目が多く、初心者が「どの量子化モデルを選べばいいか」で迷いがちです。
Hermes Desktopは、Nous Researchが推奨する最適な重みを自動的に選んでくれるため、導入時の「動かない」「遅すぎる」といったトラブルを最小限に抑えられます。
実務で使うなら、ツールの設定に凝るよりも、さっさと動かしてプロンプトの調整に入るべきだと私は考えています。

## Step 1: 環境を整える

まずはHermes Desktopをインストールし、必要なモデルをダウンロードする準備をします。
公式サイト（GitHubリポジトリ）から、自分のOSに合ったインストーラーを取得してください。

```bash
# Gitがインストールされている場合は、リポジトリをクローンしてビルドすることも可能ですが、
# 執筆時点ではバイナリ（.exeや.dmg）を直接ダウンロードするのが最も確実です。
# 以下の手順は、アプリ起動後の内部的な準備を想定しています。
```

インストーラーを実行すると、ElectronベースのクリーンなUIが立ち上がります。
初回起動時に「どのモデルをダウンロードするか」を聞かれますが、迷わず「Hermes 3 Llama 3.1 8B」を選択してください。
70Bモデルは、私の環境（RTX 4090 × 2）でも動かすのに工夫が必要なほど重いため、まずは8Bで「ローカルLLMの速度感」を体感するのが正解です。

⚠️ **落とし穴:** Windows環境で「ウイルス対策ソフト」によって実行ファイルがブロックされることが多々あります。
特にローカルLLM関連のツールは、署名のない実行ファイルが含まれるケースがあるため、不審な挙動ではなく仕様です。
また、ダウンロード中にネットワークが切れるとファイルが破損し、起動時に「Model load error」が出ることがあります。その際は、モデル保存フォルダを一度空にしてから再試行してください。

## Step 2: 基本の設定

アプリが起動したら、設定画面（Settings）を開き、推論エンジンとAPIの設定を確認します。
Hermes Desktopの強みは、バックエンドでOpenAI互換のAPIサーバーを立ててくれる点にあります。

```python
# ここでは、Pythonから操作するために必要な「APIキー」と「エンドポイント」の概念を整理します。
# 実際には、ローカルで動くためAPIキーは何でも良い（または不要）場合が多いですが、
# スクリプトの汎用性を高めるために、ダミーのキーを設定しておくのが通例です。

import os

# ローカル環境なので、セキュリティを気にする必要はありませんが、
# 将来的にクラウド版に切り替える可能性を考えて環境変数に逃がす癖をつけます。
os.environ["LOCAL_HERMES_API_KEY"] = "lm-studio"  # 何でもOK
os.environ["LOCAL_HERMES_BASE_URL"] = "http://localhost:1234/v1" # デフォルトのポート
```

ここで「なぜOpenAI互換にするのか」という理由ですが、世の中にあるAI連携ライブラリ（LangChainやLlamaIndexなど）の多くが、OpenAIのインターフェースを前提に作られているからです。
Hermes DesktopをOpenAI互換モードで動かしておけば、既存の「ChatGPTを動かすコード」のURLを1行書き換えるだけで、そのまま自前AIに置き換えられます。
これは開発効率を上げる上で非常に重要なポイントです。

## Step 3: 動かしてみる

設定が終わったら、まずはアプリ内のチャット画面で動作確認をします。
「今日の夕飯の献立を3つ提案して」といった簡単な質問を投げ、レスポンスが返ってくるか確認してください。
ここで正常に動くことが確認できたら、いよいよPythonからこのAIを制御します。

```python
from openai import OpenAI

# Hermes DesktopのAPIサーバーに接続するためのクライアント初期化
# base_urlにローカルのURLを指定するのが肝です
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

def ask_hermes(prompt):
    response = client.chat.completions.create(
        model="hermes-3-llama-3.1-8b", # ダウンロードしたモデル名に合わせる
        messages=[
            {"role": "system", "content": "あなたは優秀なエンジニアです。簡潔に回答してください。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7, # 創造性の調整。0に近いほど堅実、1に近いほど自由
    )
    return response.choices[0].message.content

# 実行
if __name__ == "__main__":
    result = ask_hermes("Pythonでファイルを再帰的に検索するコードを書いて。")
    print(result)
```

### 期待される出力

```
import os

def find_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            print(os.path.join(root, file))

# このコードは os.walk を使用して、指定されたディレクトリ以下のすべてのファイルをリストアップします。
```

出力結果を確認してください。
クラウド経由ではなく、自分のPCのGPUファンが回転し、文字が生成されているはずです。
この「自分のマシンが思考している感覚」こそが、ローカルLLM運用の醍醐味です。

## Step 4: 実用レベルにする

単発の質問ができるようになったら、次は「実務で使えるレベル」に引き上げます。
具体的には、大量のテキストデータを一括で要約したり、特定のフォーマット（JSONなど）でデータを出力させたりするバッチ処理を実装します。
ローカルLLMは「API使用料が無料」なので、数千件のデータ処理でもコストを気にする必要がありません。

```python
import json

def batch_summarize(texts):
    summaries = []
    for i, text in enumerate(texts):
        print(f"処理中... {i+1}/{len(texts)}")

        # 失敗したときのためにエラーハンドリングを入れる
        try:
            prompt = f"以下の文章を20文字程度で要約し、JSON形式で出力してください。キー名は 'summary' としてください。\n\n文章: {text}"

            response = client.chat.completions.create(
                model="hermes-3-llama-3.1-8b",
                messages=[{"role": "user", "content": prompt}],
                # response_format={"type": "json_object"} # モデルが対応している場合
            )

            content = response.choices[0].message.content
            summaries.append(content)

        except Exception as e:
            print(f"エラー発生: {e}")
            summaries.append(None)

    return summaries

# テストデータ
data_list = [
    "本日は晴天なり。明日の天気も良好との予報が出ています。お出かけには最適でしょう。",
    "新しいGPUが届いた。RTX 4090の性能は圧倒的で、ローカルLLMの推論速度が劇的に向上した。",
    "Pythonのライブラリ管理にはPoetryを使うのが今のトレンドだ。依存関係の解決がスムーズになる。"
]

results = batch_summarize(data_list)
for r in results:
    print(r)
```

実務で使う際のコツは、`temperature`を低め（0.1〜0.3）に設定することです。
ローカルLLM、特に8Bクラスのモデルは、自由度を高くしすぎると回答がブレやすく、フォーマットが崩れる原因になります。
また、長い文章を入力する場合は、コンテキストウィンドウ（一度に読み込める文字数）の制限に注意してください。
Hermes 3 Llama 3.1 8Bは最大128kトークンまで対応していますが、ローカル環境ではVRAMの消費量が増えるため、現実的には8k〜16k程度で運用するのが安定します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | APIサーバーが起動していない | Hermes Desktopの設定で「Local Server」がONになっているか確認。ポート番号（1234など）が一致しているかチェック。 |
| `Out of Memory (OOM)` | VRAM不足 | モデルのサイズを下げる（8Bからより小さいモデルへ）、または量子化ビット数（Q4_K_Mなど）がより小さいものを選ぶ。 |
| 回答が英語になる | システムプロンプトの設定不足 | システムプロンプトに「必ず日本語で回答してください」と明記する。Hermesは英語がデフォルトの傾向があります。 |
| 推論が異様に遅い | CPUで動作している | 設定画面で「GPU Acceleration」が有効になっているか、NVIDIAドライバが最新かを確認してください。 |

## 次のステップ

ここまでで、Hermes Desktopを核としたローカルAI環境の構築と、Pythonからの制御ができるようになりました。
次にあなたが取り組むべきは、「RAG（検索拡張生成）」の導入です。
自分のPC内にあるPDFやMarkdownファイルをAIに読み込ませ、それに基づいた回答をさせる仕組みを構築してみてください。

具体的には「LangChain」とベクトルデータベース（ChromaやFAISS）を組み合わせることで、完全オフラインの「自分専用ナレッジベース」が作れます。
Hermes 3は指示追従性が高いため、与えられたコンテキストから正確に情報を抽出するタスクに非常に向いています。
また、Difyのようなノーコードツールをローカルで立ち上げ、そのバックエンドとしてHermes Desktopを接続するのも、実務への導入としては非常に賢い選択です。

AIは「使う」段階から「飼い慣らす」段階へ進化しています。
月額課金の制限に縛られず、24時間365日、自分のマシンのリソースをフルに活用して、あなただけのAIエージェントを育ててみてください。

## よくある質問

### Q1: NVIDIAのGPUを持っていないのですが、動かせますか？

AMDのGPU（Radeon）や、Apple Silicon（Mシリーズチップ）であれば、それぞれのアクセラレーション機能（ROCmやMetal）を利用して動作可能です。
ただし、Intelの内蔵グラフィックスのみの場合は、CPU推論になるため非常に低速です。その場合は、モデルサイズを3B以下の軽量なものに変更することをお勧めします。

### Q2: 会社で使いたいのですが、セキュリティ上のリスクはありますか？

Hermes Desktopは基本的にローカル環境で動作し、データを外部サーバーに送信することはありません。
ただし、モデルのダウンロード時のみHugging Faceなどの外部サイトにアクセスします。
一度ダウンロードが完了すれば、物理的にインターネットを遮断した状態でも動作するため、セキュリティ要件が厳しい職場でも採用しやすいツールです。

### Q3: Hermes 3モデルの「70B」を動かすにはどれくらいのスペックが必要ですか？

70Bモデルを4ビット量子化（Q4_K_M）で動かす場合、約40GB以上のVRAMが必要です。
具体的にはRTX 3090や4090を2枚挿しするか、Mac Studioのメモリ64GB以上のモデルを用意する必要があります。
個人開発や日常のタスクであれば、8Bモデルを高速（秒間50トークン以上）で回す方が圧倒的に快適です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで8Bモデルを余裕で動かせ、省電力なためローカルLLM入門に最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Local LLM 使い方 入門：OllamaとPythonで自分専用のAIアシスタントを作る方法](/posts/2026-04-10-local-llm-ollama-python-tutorial-llama3/)
- [Qwen 3.6 使い方: ローカルLLMで爆速・高精度な推論環境を構築する手順](/posts/2026-04-18-qwen3-6-local-python-ollama-guide/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "NVIDIAのGPUを持っていないのですが、動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AMDのGPU（Radeon）や、Apple Silicon（Mシリーズチップ）であれば、それぞれのアクセラレーション機能（ROCmやMetal）を利用して動作可能です。 ただし、Intelの内蔵グラフィックスのみの場合は、CPU推論になるため非常に低速です。その場合は、モデルサイズを3B以下の軽量なものに変更することをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使いたいのですが、セキュリティ上のリスクはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hermes Desktopは基本的にローカル環境で動作し、データを外部サーバーに送信することはありません。 ただし、モデルのダウンロード時のみHugging Faceなどの外部サイトにアクセスします。 一度ダウンロードが完了すれば、物理的にインターネットを遮断した状態でも動作するため、セキュリティ要件が厳しい職場でも採用しやすいツールです。"
      }
    },
    {
      "@type": "Question",
      "name": "Hermes 3モデルの「70B」を動かすにはどれくらいのスペックが必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "70Bモデルを4ビット量子化（Q4KM）で動かす場合、約40GB以上のVRAMが必要です。 具体的にはRTX 3090や4090を2枚挿しするか、Mac Studioのメモリ64GB以上のモデルを用意する必要があります。 個人開発や日常のタスクであれば、8Bモデルを高速（秒間50トークン以上）で回す方が圧倒的に快適です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">RTX 4060 Ti 16GB</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">VRAM 16GBで8Bモデルを余裕で動かせ、省電力なためローカルLLM入門に最適</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

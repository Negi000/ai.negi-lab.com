---
title: "ローカルLLMをPythonで制御して自分専用のプライベートAIを作る方法"
date: 2026-07-26T00:00:00+09:00
slug: "local-llm-python-ollama-guide"
cover:
  image: "/images/posts/2026-07-26-local-llm-python-ollama-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Python AI 開発"
  - "Llama 3.1 ローカル"
  - "自宅サーバー AI"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- OllamaとPythonを連携させ、完全にオフラインで動作するテキスト解析エージェントを構築します。
- 前提知識: Pythonの基本的な文法（変数、関数、pipでのライブラリ導入）を理解していること。
- 必要なもの: Docker不要のOllama環境、Python 3.10以上、VRAM 8GB以上のGPU（推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでLlama 3.1 8Bが爆速で動き、実務検証に最もコスパが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを「仕事で使えるレベル」で動かすなら、最も重要なのはGPUのVRAM（ビデオメモリ）容量です。
最低でも8GB、理想を言えば16GB以上のVRAMを搭載したNVIDIA製GPUを用意してください。
私はRTX 4090の2枚挿し（VRAM 48GB）で運用していますが、Llama 3.1の8BモデルやMistralクラスなら、RTX 4060 Ti (16GB版) 1枚で驚くほど快適に動きます。

Macユーザーであれば、メモリ32GB以上のApple Silicon（M2/M3 Pro以上）が現実的な選択肢になります。
メモリが16GB以下だと、推論中にシステム全体が重くなり、開発どころではなくなるからです。
API料金は一切かかりませんが、電気代とハードウェアへの初期投資がコストだと考えてください。
もし手元に強靭なGPUがない場合は、月額$20を払ってClaude APIを叩き続けるほうが、時間対効果は高いです。

## なぜこの方法を選ぶのか

OpenAIやAnthropicのAPIは非常に優秀ですが、常に「規約変更」と「検閲」のリスクが付きまといます。
Andrej KarpathyがAnthropicをプロフィールの支援先から外したというニュースは、AIの巨塔たちがよりクローズドな方向へ向かっている兆候かもしれません。
私たちは、モデルの重みを自分のディスクに持ち、コードで完全に制御する術を身につけておくべきです。

今回は数あるローカルLLM実行環境の中でも、セットアップが最も簡単で、かつPythonライブラリが充実している「Ollama」を採用します。
llama.cppを直接ビルドする方法もありますが、APIサーバーとしての安定性と、ライブラリの抽象度の高さから、実務への導入スピードはOllamaが圧倒的です。

## Step 1: 環境を整える

まずはLLMの実行エンジンとなるOllamaをインストールし、モデルをローカルに落とします。

```bash
# Ollamaのインストール（公式サイトからダウンロードして実行するだけです）
# モデル（Llama 3.1 8B）のダウンロードと起動確認
ollama run llama3.1
```

コマンドを実行すると、数GBのモデルファイルがダウンロードされます。
ダウンロード完了後、ターミナルで対話が始まったら成功です。
`/exit` で一旦終了してください。

なぜ Llama 3.1 を選ぶのかというと、現時点で「日本語の理解力」と「推論速度」のバランスが最も優れているからです。
より軽量なモデルに Qwen2 や Gemma 2 がありますが、最初は最もエコシステムが強い Llama シリーズで環境を組むのが、トラブルを避けるコツです。

⚠️ **落とし穴:**
Windows環境でGPUを認識しない場合、最新のNVIDIAドライバーがインストールされているか確認してください。
WSL2を使わなくてもネイティブ版Ollamaで動きますが、タスクマネージャーの「専用GPUメモリ」が消費されているか必ずチェックしましょう。
ここが動いていないと、CPU推論になり、1秒に1文字程度しか出力されない絶望的な速度になります。

## Step 2: 基本の設定

PythonからOllamaを操作するためのライブラリを導入し、接続設定を書きます。

```bash
# 仮想環境を作成してライブラリをインストール
python -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install ollama
```

次に、エディタを開いて `app.py` を作成します。

```python
import ollama

# 使用するモデル名を定義
# 自分のPCスペックに合わせて 'llama3.1' または 'phi3' などに変更可能
MODEL_NAME = "llama3.1"

def check_connection():
    try:
        # Ollamaサーバーが起動しているか確認
        response = ollama.list()
        print("接続成功。ロード済みのモデル一覧:")
        for m in response['models']:
            print(f"- {m['name']}")
    except Exception as e:
        print(f"接続エラー: {e}")
        print("Ollamaアプリが起動しているか確認してください。")

if __name__ == "__main__":
    check_connection()
```

ここではAPIキーの設定が不要です。
なぜなら、自分のローカルマシン内で閉じた通信（localhost:11434）を行うからです。
外部サーバーにデータが飛ばないため、企業の機密情報や個人の日記を流し込んでも、学習データに利用される心配はありません。

## Step 3: 動かしてみる

実際にPythonからテキストを投げて、レスポンスを取得します。
実務で使うことを想定し、一括で結果を待つのではなく「ストリーミング形式」で実装します。

```python
import ollama

def ask_ai(prompt):
    stream = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    print("AIの回答: ", end="", flush=True)
    for chunk in stream:
        # トークンごとに逐次出力
        content = chunk['message']['content']
        print(content, end="", flush=True)
    print()

if __name__ == "__main__":
    user_input = "AIのローカル実行がエンジニアにとって重要な理由を3つ挙げて。"
    ask_ai(user_input)
```

### 期待される出力

```
AIの回答: ローカル実行が重要な理由は以下の3点です。
1. プライバシーとセキュリティ：データが外部へ送信されないため、機密情報を扱えます。
2. コスト：API利用料がかからず、ハードウェアのリソースを使い倒せます。
3. カスタマイズ性：モデルのパラメータやシステムプロンプトを完全に制御可能です。
```

ストリーミングを導入する理由は、ローカルLLMの「最初の1文字が出るまでの遅延」を感じさせないためです。
一括取得にすると、全文章が生成されるまで画面が止まってしまい、ユーザーは「フリーズしたのかな？」と不安になります。
レスポンスを0.3秒程度で体感させるために、ストリーミングは必須の実装だと考えてください。

## Step 4: 実用レベルにする

単に会話するだけならブラウザ版のChatGPTで十分です。
Pythonで動かす真の価値は「構造化データの抽出」にあります。
例えば、大量のテキストから「日付」「場所」「重要度」を抜き出してJSONで出力させる機能を実装しましょう。

```python
import json
import ollama

def extract_event_info(text):
    system_prompt = (
        "あなたは優秀なデータ抽出アシスタントです。"
        "入力された文章から、日付、場所、イベント名を抽出し、必ず以下のJSON形式で回答してください。"
        '{"date": "YYYY/MM/DD", "location": "string", "event_name": "string"}'
    )

    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text}
        ],
        format='json', # ここが重要
        options={'temperature': 0} # 再現性を高めるために0に設定
    )

    return response['message']['content']

# テスト実行
raw_text = "来週の月曜日、10月28日に渋谷のスクランブルスクエアでAI勉強会を開催します。"
json_output = extract_event_info(raw_text)

# 文字列を辞書オブジェクトに変換して中身を確認
data = json.loads(json_output)
print(f"日付: {data['date']}")
print(f"場所: {data['location']}")
print(f"イベント: {data['event_name']}")
```

ここで `format='json'` を指定している点に注目してください。
これはOllama独自の機能で、モデルの出力を強制的にJSONフォーマットに制限するものです。
従来のLLM開発では、AIが余計な解説文（「はい、JSON形式で出力します」など）を付けてしまい、パースエラーになることがよくありました。
この設定を入れることで、プログラムから直接データベースに保存できる形式を安定して得られます。

また、 `temperature`（温度感）を `0` にしているのは、抽出タスクにおいて「AIの創造性」は不要だからです。
事実を事実として、毎回同じ結果を出す設定にするのが実務上の「お作法」です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| ConnectionError | Ollamaアプリが起動していない | タスクバーにOllamaのアイコンがあるか確認。 |
| 出力が極端に遅い | GPUではなくCPUで動作している | GPUドライバを更新。VRAM不足でモデルが溢れている可能性あり。 |
| JSONが壊れる | モデルの能力不足（小さいモデル） | 8B以上のモデルを使うか、プロンプトを簡略化する。 |
| Out of Memory | 他のアプリがVRAMを占有している | ブラウザのハードウェアアクセラレーションをオフにするか、モデルサイズを下げる。 |

## 次のステップ

ここまでできれば、あなたは「自分専用のAI基盤」を手に入れたことになります。
Karpathyが提唱した「AI OS」の概念に近い、ローカルでの自律的な処理が可能になります。

次のステップとして挑戦してほしいのは「RAG（検索拡張生成）」の構築です。
今回作ったスクリプトに、自分の過去のメモやPDFファイルを読み込ませる機能を追加してみてください。
Pythonの `PyPDF2` ライブラリでテキストを抽出し、それをプロンプトのコンテキストとして渡すだけで、あなた専用の知識ベースを持つAIが出来上がります。

また、API化してスマホから自宅のサーバーにアクセスできるようにするのも面白いでしょう。
RTX 4090を積んだ自宅サーバーを ngrok や Tailscale で公開すれば、外出先でも世界最強クラスのプライベートAIを無料で使い放題になります。
この「所有感」こそが、ローカルLLM最大の醍醐味です。

## よくある質問

### Q1: ネット接続がなくても本当に動きますか？

はい、完全にオフラインで動きます。モデルのダウンロード時だけネットが必要ですが、一度落としてしまえばLANケーブルを抜いてもPythonコードは動作します。プライバシーを極限まで気にする用途に最適です。

### Q2: 4-bit量子化などのモデルが色々ありますが、どれが良いですか？

初心者は「4-bit（q4_K_M）」を選べば間違いありません。モデルサイズが半分以下になり、推論速度が劇的に上がりますが、回答の精度低下は体感できるほどではありません。Ollamaのデフォルトもこれに近い設定です。

### Q3: Python以外の言語でも動かせますか？

Ollamaは内部的にHTTP APIを公開しているため、JavaScriptやGo、Rustなど、あらゆる言語から叩けます。ですが、AI界隈のライブラリ（LangChainやLlamaIndex）の充実度を考えると、Pythonで開発するのが最も効率的です。

---

## あわせて読みたい

- [Qwen 27Bクラスをローカル環境で爆速動作させる方法](/posts/2026-05-21-qwen-27b-local-setup-ollama-python/)
- [ローカルLLMで自律型エージェントを作る方法 OpenCodeInterpreter 構築ガイド](/posts/2026-05-16-opencodeinterpreter-local-agent-tutorial/)
- [OllamaとOpen WebUIで自分専用のChatGPTを構築する方法](/posts/2026-06-22-ollama-open-webui-local-llm-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "ネット接続がなくても本当に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、完全にオフラインで動きます。モデルのダウンロード時だけネットが必要ですが、一度落としてしまえばLANケーブルを抜いてもPythonコードは動作します。プライバシーを極限まで気にする用途に最適です。"
      }
    },
    {
      "@type": "Question",
      "name": "4-bit量子化などのモデルが色々ありますが、どれが良いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "初心者は「4-bit（q4KM）」を選べば間違いありません。モデルサイズが半分以下になり、推論速度が劇的に上がりますが、回答の精度低下は体感できるほどではありません。Ollamaのデフォルトもこれに近い設定です。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ollamaは内部的にHTTP APIを公開しているため、JavaScriptやGo、Rustなど、あらゆる言語から叩けます。ですが、AI界隈のライブラリ（LangChainやLlamaIndex）の充実度を考えると、Pythonで開発するのが最も効率的です。 ---"
      }
    }
  ]
}
</script>

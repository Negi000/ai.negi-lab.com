---
title: "ローカルLLM構築入門 OllamaとPythonでAIを自前運用する方法"
date: 2026-06-02T00:00:00+09:00
slug: "ollama-python-local-llm-tutorial"
cover:
  image: "/images/posts/2026-06-02-ollama-python-local-llm-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Ollama 使い方"
  - "Llama 3 ローカル"
  - "Python AI 構築"
  - "ローカルLLM 入門"
---
**所要時間:** 約40分 | **難易度:** ★★☆☆☆

## この記事で作るもの

- Ollamaを使用して、自分のPC上にLlama 3やGemma 2などの最新LLMをAPIサーバーとして立ち上げます。
- PythonからそのAPIを呼び出し、ストリーミング形式（逐次出力）で回答を表示する実用的なチャットスクリプトを完成させます。
- 前提知識として、Pythonの基本的な文法（変数、関数、pipでのライブラリインストール）を理解している必要があります。
- Windows、Mac、LinuxのいずれかのPCが必要です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLM入門に最も現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLMを動かす上で、CPUよりも重要なのがGPUのVRAM（ビデオメモリ）容量です。
結論から言うと、実用的な速度で動かしたいならVRAM 8GBが最低ライン、12GBあれば快適、16GB以上あれば「仕事で使える」レベルになります。
8B（80億パラメータ）クラスのモデルを4bit量子化で動かす場合、約5GB前後のVRAMを消費します。

Macユーザーの場合、ユニファイドメモリがVRAMとして機能するため、メモリ16GB以上のモデルを推奨します。
8GBのMacBook Airでも動かないことはありませんが、ブラウザなどを開くとすぐにスワップが発生し、レスポンスが10秒以上かかることも珍しくありません。
もし手元のPCのスペックが足りない場合は、RTX 3060 12GBの中古を探すのが最もコストパフォーマンスが良い選択肢です。

API料金は一切かかりません。
電気代を除けば、どれだけ大量のテキストを生成しても、どれだけ長い時間推論を回しても「無料」です。
これがOpenAIやAnthropicのAPIを使い続けるのと比較した際の、ローカルLLM最大のメリットです。

## なぜこの方法を選ぶのか

ローカルLLMを動かす手段は、llama.cpp、LM Studio、LocalAIなど多岐にわたります。
その中で私が「Ollama」を推奨するのは、環境構築の圧倒的な手軽さと、APIサーバーとしての安定性が高いからです。
特にOllamaはバックグラウンドでデーモンとして常駐してくれるため、Pythonコード側からいつでも呼び出せるのが魅力です。

LM StudioなどはGUIが綺麗ですが、プログラムから自動化する際の柔軟性はOllamaに軍配が上がります。
また、Ollamaはライブラリ管理がDockerに近く、モデルのプルや更新がコマンド一つで完結します。
複雑なビルド設定や依存関係に悩まされる時間をゼロにして、AIを「使う」ことに集中するために、この構成がベストだと判断しました。

## Step 1: 環境を整える

まずは、LLMの実行エンジンとなるOllamaをインストールします。

公式サイト（ollama.com）からインストーラーをダウンロードして実行してください。
インストールが終わったら、ターミナル（WindowsはPowerShell）を開いて以下のコマンドを叩きます。

```bash
# Llama 3 8Bモデルをダウンロードして起動
ollama run llama3
```

このコマンドは「モデルのダウンロード」と「対話インターフェースの起動」を同時に行います。
初回は数GBのデータ転送があるため、回線速度によりますが5〜10分ほどかかります。
正常に起動し、ターミナルで対話ができるようになったら、一度 `/bye` と入力して終了してください。

次に、PythonからOllamaを制御するためのライブラリをインストールします。

```bash
# Ollama公式のPythonライブラリをインストール
pip install ollama
```

このライブラリはOllamaのREST APIをラップしたもので、HTTPリクエストを自前で書く必要がなくなります。
Python 3.8以上が必要です。バージョンが古い場合はあらかじめアップデートしておいてください。

⚠️ **落とし穴:**
Windowsで「ollama command not found」と出る場合は、パスが通っていない可能性があります。
インストール後に一度PCを再起動するか、タスクバーのインジケーターにOllamaのアイコンがあるか確認してください。
また、VPNを接続しているとモデルのダウンロードが極端に遅くなる、あるいは失敗することがあります。

## Step 2: 基本の設定

Pythonスクリプトを作成し、まずは最もシンプルな形でモデルを呼び出す設定を書きます。
ここでは、環境変数などの複雑な設定を抜きにして、確実に接続できることを確認します。

```python
import ollama

# 使用するモデル名を定義
# 事前に `ollama pull` している必要があります
MODEL_NAME = "llama3"

def simple_chat(prompt):
    try:
        # ollama.chatは標準でローカルホストの11434ポートを見にいきます
        response = ollama.chat(model=MODEL_NAME, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    test_prompt = "ローカルLLMの利点を3つ教えてください。"
    print(f"質問: {test_prompt}")
    answer = simple_chat(test_prompt)
    print(f"回答: {answer}")
```

このコードでは、`ollama.chat` メソッドを使用しています。
`messages` リストを渡す形式は、OpenAIのAPI（Chat Completion API）とほぼ同じ設計になっています。
このため、将来的にローカルLLMからGPT-4などの外部APIへ切り替える際も、ロジックの修正が最小限で済みます。

なぜ `ollama.generate` ではなく `ollama.chat` を使うのか。
それは、チャット形式の方が「過去の会話履歴」を保持させる拡張が容易だからです。
実務でAIを使う場合、単発の質問で終わることは稀であり、文脈（コンテキスト）の管理が必須になります。

## Step 3: 動かしてみる

上記のスクリプトを実行すると、ターミナルに回答が表示されます。
しかし、これでは回答がすべて生成されるまで待機する必要があります。
LLMの良さを引き出すには、生成された文字から順次表示する「ストリーミング」が必要です。

以下のコードに書き換えて実行してみてください。

```python
import ollama

def stream_chat(prompt):
    # stream=Trueにすることで、ジェネレータが返されます
    stream = ollama.chat(
        model='llama3',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    print("回答: ", end='', flush=True)
    for chunk in stream:
        # 各チャンクの内容を表示
        content = chunk['message']['content']
        print(content, end='', flush=True)
    print()

if __name__ == "__main__":
    stream_chat("Pythonで素数を判定する関数を書いてください。")
```

### 期待される出力

```
回答: 以下は、Pythonで素数を判定するシンプルな関数です。
```python
def is_prime(n):
    if n <= 1:
        return False
...
```

ストリーミングを有効にすると、最初の1文字目が出るまでの時間（Time To First Token）が劇的に短縮されます。
私のRTX 4090環境では、ほぼ0.1秒以内にレスポンスが始まります。
ユーザー体験において、この「すぐに反応が来る」という感覚は、モデルの賢さと同じくらい重要です。

## Step 4: 実用レベルにする

実務で使うためには、以下の3つの要素を追加する必要があります。
1. **システムプロンプトの設定**: AIの振る舞い（「あなたは優秀なエンジニアです」など）を指定する。
2. **履歴の保持**: 前の質問を覚えているようにする。
3. **エラーハンドリング**: Ollamaが起動していない場合に適切なメッセージを出す。

これらを盛り込んだ、実戦用チャットスクリプトがこちらです。

```python
import ollama
import sys

class LocalAIContext:
    def __init__(self, model="llama3", system_prompt=""):
        self.model = model
        # 会話履歴を保持するリスト
        self.messages = []
        if system_prompt:
            self.messages.append({'role': 'system', 'content': system_prompt})

    def ask(self, user_input):
        self.messages.append({'role': 'user', 'content': user_input})

        try:
            stream = ollama.chat(
                model=self.model,
                messages=self.messages,
                stream=True,
            )

            full_response = ""
            print(f"\n[{self.model}]: ", end='', flush=True)

            for chunk in stream:
                content = chunk['message']['content']
                print(content, end='', flush=True)
                full_response += content

            print("\n")
            # AIの回答も履歴に追加
            self.messages.append({'role': 'assistant', 'content': full_response})

        except ConnectionError:
            print("エラー: Ollamaが起動していません。アプリを立ち上げてください。")
        except Exception as e:
            print(f"予期せぬエラー: {e}")

def main():
    # システムプロンプトで日本語での回答を強制する
    ai = LocalAIContext(
        model="llama3",
        system_prompt="あなたは親切なAIアシスタントです。必ず日本語で、簡潔に回答してください。"
    )

    print("Local LLM Chat (Ctrl+Cで終了)")
    while True:
        try:
            user_input = input("あなた: ")
            if not user_input.strip():
                continue
            ai.ask(user_input)
        except KeyboardInterrupt:
            print("\n終了します。")
            break

if __name__ == "__main__":
    main()
```

このコードでは、`LocalAIContext` クラスを作成し、その中で会話履歴を管理しています。
`self.messages` に過去のやり取りをすべて蓄積し、毎回Ollamaに送ることで「さっきのコードを解説して」といった指示が通るようになります。

ただし、履歴が長くなりすぎると、モデルのコンテキストウィンドウ（扱えるトークン数の上限）を超えてしまいます。
実務で数時間のチャットを行う場合は、過去10発分だけを残すなどの「窓関数」的な処理を `self.messages = self.messages[-10:]` のように入れるのがセオリーです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ConnectionError` | Ollamaサービスが未起動 | タスクトレイにOllamaがあるか確認し、アプリを再起動する。 |
| `Response slow (1 token/sec)` | VRAM不足でCPU推論になっている | モデルを小さいもの（Llama3 8B → Phi-3 Miniなど）に変える。 |
| `Model not found` | 指定したモデルがプルされていない | `ollama pull [モデル名]` をターミナルで実行する。 |
| 日本語が不自然 | モデルの学習データ不足 | `gemma2` や `command-r` など、日本語に強いモデルを試す。 |

## 次のステップ

この環境ができたら、次に挑戦すべきは「RAG（検索拡張生成）」の構築です。
今回作ったスクリプトに、自分のPDFファイルやメモ帳の内容を読み込ませて、その内容に基づいて回答させる仕組みです。
ローカルLLMの真価は、機密情報を外部に送らずに、自分のデータについてAIと会話できる点にあります。

また、Difyなどのノーコードツールと連携させるのも面白いでしょう。
OllamaのAPIは、Difyのローカル環境から簡単に接続できます。
Pythonコードを書くのが面倒なワークフローはDifyに任せ、独自のロジックが必要な部分だけ今回のようなスクリプトで実装するという使い分けが、現場での賢い立ち回りです。

最後に、ハードウェアの増強も検討してください。
ローカルLLMの世界は「VRAMこそが正義」です。
12GBから24GBへ移行したときの、動かせるモデルの選択肢が広がる感覚は、一度味わうと戻れません。

## よくある質問

### Q1: グラボがないノートPCでも動きますか？

動きますが、速度は期待しないでください。CPUのみで推論する場合、1秒間に1〜2文字程度の速度になることが多いです。文章の要約など、裏側で時間をかけても良いタスクなら実用的ですが、チャットとしてはストレスが溜まるはずです。

### Q2: 複数のモデルを同時に動かすことはできますか？

VRAMが許す限り可能です。Ollamaはリクエストに応じてモデルをメモリにロードします。複数のモデルを同時にアクティブにする設定も可能ですが、基本的には一つのモデルがメモリを占有して高速に動くように調整するのが一般的です。

### Q3: 商用利用は可能ですか？

使用するモデルのライセンスに依存します。例えばLlama 3は「月間アクティブユーザー数が7億人未満」であれば無料で商用利用可能です。多くのオープンモデルは寛容なライセンスですが、必ず各モデルのHugging Faceページ等でライセンスを確認してください。

---

## あわせて読みたい

- [OllamaとOpen WebUIで自分専用のChatGPT環境を作る方法](/posts/2026-05-31-ollama-openwebui-local-llm-setup-guide/)
- [Qwen2.5をローカル環境で動かし、API料金を気にせずコード生成を自動化するPythonスクリプトを作る方法](/posts/2026-05-09-qwen-2-5-coder-local-python-guide/)
- [Qwen 2.5やGemma 2をローカル環境で高速に動かす方法](/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "グラボがないノートPCでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、速度は期待しないでください。CPUのみで推論する場合、1秒間に1〜2文字程度の速度になることが多いです。文章の要約など、裏側で時間をかけても良いタスクなら実用的ですが、チャットとしてはストレスが溜まるはずです。"
      }
    },
    {
      "@type": "Question",
      "name": "複数のモデルを同時に動かすことはできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VRAMが許す限り可能です。Ollamaはリクエストに応じてモデルをメモリにロードします。複数のモデルを同時にアクティブにする設定も可能ですが、基本的には一つのモデルがメモリを占有して高速に動くように調整するのが一般的です。"
      }
    },
    {
      "@type": "Question",
      "name": "商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "使用するモデルのライセンスに依存します。例えばLlama 3は「月間アクティブユーザー数が7億人未満」であれば無料で商用利用可能です。多くのオープンモデルは寛容なライセンスですが、必ず各モデルのHugging Faceページ等でライセンスを確認してください。 ---"
      }
    }
  ]
}
</script>

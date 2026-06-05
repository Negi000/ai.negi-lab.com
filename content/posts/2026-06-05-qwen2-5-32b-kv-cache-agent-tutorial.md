---
title: "Qwen2.5 32BとKV Cache最適化で自律型AIエージェントを構築する方法"
date: 2026-06-05T00:00:00+09:00
slug: "qwen2-5-32b-kv-cache-agent-tutorial"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen2.5 32B 使い方"
  - "KV Cache 最適化"
  - "Ollama Python エージェント"
  - "ローカルLLM ツール利用"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

ローカルLLMのQwen2.5-32B-Instructを使い、KV Cache（キー・バリュー・キャッシュ）を最適化することで、複雑なツール利用（MCP連携など）を高速にこなす自律型エージェントの基盤を構築します。
PythonのコードからOllamaのAPIを叩き、長いシステムプロンプトを保持したまま、レスポンス速度を維持する設定を実装します。
この記事を読み終える頃には、手元のPCで「思考が速く、指示を忘れない」実用レベルのAIエージェントが動いています。

前提知識として、Pythonの基本的な文法と、ターミナル（コマンドプロンプト）でのコマンド操作ができることを想定しています。

## 先に確認するスペック・料金

今回の検証には「VRAM（ビデオメモリ）量」がすべてと言っても過言ではありません。
Qwen2.5-32B-Instructを4-bit量子化で動かす場合、モデル本体だけで約18GBから20GBのVRAMを消費します。
さらにKV Cache（コンテキストの記憶領域）を確保するため、RTX 3090やRTX 4090といったVRAM 24GB搭載のグラボが必須となります。

16GB以下のグラボ（RTX 4070 Ti Superなど）でも動作自体は可能ですが、KV Cacheの容量を削る必要があり、長い指示を与えると途端に処理が重くなるか、メモリ不足でクラッシュします。
もしVRAMが足りない場合は、MacのM2/M3/M4 Maxなど、ユニファイドメモリを32GB以上積んだモデルを用意してください。
API料金はローカル実行のため0円ですが、電気代とハードウェア代への投資が必要です。

## なぜこの方法を選ぶのか

エージェント開発において、多くの人がGPT-4oなどのクラウドAPIを使いますが、私はあえてローカルのQwen2.5-32Bを推奨します。
理由は「コンテキストの再利用効率」と「プライバシー」です。
RedditのLocalLLaMAコミュニティでも話題になった通り、Qwenの30Bクラスは、70Bクラスに匹敵するツール利用（Tool Use）の精度を持っています。

特に今回の肝であるKV Cacheは、一度読み込んだ長いシステムプロンプト（ツールの定義など）をメモリ上に保持する仕組みです。
これを適切に設定することで、2回目以降の発言にかかる「プレフィックス（前提条件）の計算時間」をほぼゼロにできます。
クラウドAPIでは毎回トークン料金がかかり、かつ内部的なキャッシュ制御がブラックボックスですが、ローカルならミリ秒単位で制御可能です。

## Step 1: 環境を整える

まずはOllamaをインストールし、Qwen2.5の32Bモデルを取得します。

```bash
# Ollamaのインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# Qwen2.5 32Bモデルのダウンロード
# 標準の4-bit量子化版をプルします
ollama pull qwen2.5:32b
```

Ollamaを使う理由は、複雑なKV Cacheの管理や、GPUへのレイヤー割り当てを自動で行ってくれるからです。
手動でllama.cppをビルドしてパラメータをいじるのも楽しいですが、実務で「即座に動くもの」を作るならOllama一択です。
Qwen2.5 32Bは、日本語の理解力も非常に高く、エンジニア向けのコード生成能力も突出しています。

⚠️ **落とし穴:**
VRAM 24GBのグラボを使っていても、ブラウザや他のソフトがVRAMを数GB占有していると、32BモデルがGPUに乗り切らず、CPU推論に切り替わって極端に遅くなります。
実行前に必ずタスクマネージャーや `nvidia-smi` コマンドで、空き容量が20GB以上あることを確認してください。

## Step 2: 基本の設定

PythonからOllamaを制御するためのライブラリをインストールし、KV Cacheを意識した設定を記述します。

```bash
pip install ollama
```

次に、エージェントの骨組みとなるスクリプトを作成します。ここでは `num_ctx`（コンテキストサイズ）を明示的に指定するのがポイントです。

```python
import ollama

# モデル名とコンテキストサイズの設定
# Qwen2.5-32Bは最大128kトークンまで対応していますが、
# VRAM 24GB環境では32768(32k)程度に留めるのが現実的です。
MODEL_NAME = "qwen2.5:32b"
CONTEXT_SIZE = 32768

def initialize_agent():
    """
    エージェントの初期化。
    KV Cacheを有効活用するために、最初に空のプロンプトを投げて
    モデルをVRAMにロードさせておきます。
    """
    print(f"モデル {MODEL_NAME} をロード中...")
    response = ollama.generate(
        model=MODEL_NAME,
        prompt="",
        options={
            "num_ctx": CONTEXT_SIZE, # ここでKV Cacheのサイズが決まる
            "temperature": 0.7,
            "num_gpu": 99 # 全レイヤーをGPUに乗せる指定
        }
    )
    print("ロード完了。")

initialize_agent()
```

`num_ctx` を大きく設定するほど、KV Cache用のVRAM領域が事前に確保されます。
Redditで指摘されていた「KV Cacheの重要性」とは、この領域が不足すると、過去の会話や長いシステム指示を「再計算」しなければならず、1レスポンスに数十秒かかるという事態を指しています。
32kという値は、MCP（Model Context Protocol）で大量のツール定義を流し込んでも余裕を持って動作する数値です。

## Step 3: 動かしてみる

エージェントに「11個のツール定義」という重いシステムプロンプトを与えて、正しくツールを選択できるかテストします。

```python
system_prompt = """
あなたは高度な自律型エージェントです。以下のツールを状況に応じて使い分けてください。
1. search_web: ウェブ検索を行う
2. read_file: ファイルを読み込む
3. write_code: Pythonコードを書く
...（中略）...
11. final_answer: 最終的な回答を出す

回答は常にJSON形式で行い、次の形式を守ってください：
{"tool": "ツール名", "parameters": {"引数名": "値"}}
"""

def chat_with_agent(user_input):
    response = ollama.generate(
        model=MODEL_NAME,
        system=system_prompt,
        prompt=user_input,
        options={
            "num_ctx": CONTEXT_SIZE,
        }
    )
    return response['response']

# 動作確認
print(chat_with_agent("最新のAIニュースを調べて、結果をresult.txtに保存して。"))
```

### 期待される出力

```json
{"tool": "search_web", "parameters": {"query": "latest AI news 2024"}}
```

最初の1回目は、システムプロンプトの読み込み（KV Cacheの構築）に数秒かかるはずです。
しかし、2回目以降、別の質問を投げたときには、システムプロンプトの再計算がスキップされるため、0.x秒でレスポンスが返ってくるはずです。
これが「KV Cacheが効いている」状態です。

## Step 4: 実用レベルにする

実務では、AIがツールを実行した結果を再びAIに戻し、次のステップを考えさせる「エージェント・ループ」が必要です。
また、OllamaのAPIがタイムアウトしたり、不正なJSONを返したりした場合のエラーハンドリングも追加します。

```python
import json
import time

def agent_loop(task_description):
    history = []
    current_input = task_description

    # 最大5ステップまでループさせる
    for i in range(5):
        print(f"\n--- ステップ {i+1} ---")
        start_time = time.time()

        try:
            response = ollama.generate(
                model=MODEL_NAME,
                system=system_prompt,
                prompt=current_input,
                options={"num_ctx": CONTEXT_SIZE}
            )

            content = response['response']
            duration = time.time() - start_time
            print(f"推論時間: {duration:.2f}秒")

            # JSONのパース
            action = json.loads(content)
            print(f"AIの選択: {action['tool']}")

            if action['tool'] == "final_answer":
                print(f"最終回答: {action['parameters']['answer']}")
                break

            # ここで本来は実際のツール（関数）を実行する
            # 今回はシミュレーションとして、実行結果を文字列で返す
            tool_result = f"{action['tool']} の実行に成功しました。"
            current_input = f"ツール実行結果: {tool_result}\n次のステップに進んでください。"

        except json.JSONDecodeError:
            print("エラー: AIが正しいJSONを返しませんでした。リトライします。")
            current_input = "もう一度JSON形式だけで回答してください。"
        except Exception as e:
            print(f"予期せぬエラー: {e}")
            break

agent_loop("ファイルを読み込んで解析し、その結果を要約して報告せよ。")
```

このコードのポイントは、`ollama.generate` を繰り返しても、同じ `system_prompt` を使っている限り、Ollama内部でKV Cacheが使い回される点です。
Redditの投稿者が「RivetでMCPサブグラフを組んだ」と言っているのも、このように複雑な命令を階層化し、各ステップで高速な推論を行わせるためです。
Qwen2.5 32Bなら、このループを非常に高い精度で完遂できます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| 推論が1文字ずつ出るのが異様に遅い | VRAM不足で一部がCPUに逃げている | モデルを量子化レベルが高いものに変更するか、他のアプリを閉じる |
| `Context window exceeded` | `num_ctx` を超える長い会話をした | 定期的に古い会話履歴を削除（サマライズ）する実装を追加する |
| AIがJSON以外の余計な文章を喋る | Qwenの性格による指示無視 | `system_prompt` の末尾に「JSON以外は一切出力しないでください」と強く書く |

## 次のステップ

この記事で構築した基盤は、あくまで「思考エンジン」の部分です。
ここから実務で使えるレベルに引き上げるには、以下の3点に取り組んでみてください。

1. **本物のツール実装**: `search_web` なら DuckDuckGo API、`read_file` なら Python の `open()` 関数を実際に呼び出すコードを書く。
2. **MCP (Model Context Protocol) への対応**: Anthropicが提唱したMCPサーバーを自作し、今回のエージェントと接続する。これにより、ブラウザ操作やデータベース操作が驚くほど簡単に繋がります。
3. **ストリーミング出力の統合**: 長文回答を待つのは苦痛です。`ollama.generate(stream=True)` を使い、逐次結果を表示するUI（Streamlitなど）を作ってみる。

ローカルLLMは、もはや「おもちゃ」の域を超え、特定のワークフローにおいてはクラウドを凌駕するコストパフォーマンスと速度を発揮します。
特にQwen2.5 32Bのような「中規模で高性能」なモデルと、KV Cacheの適切な管理の組み合わせは、2025年のAI開発のスタンダードになるでしょう。

## よくある質問

### Q1: RTX 3060 12GBしか持っていませんが、動かす方法はありますか？

Qwen2.5の7Bモデル（qwen2.5:7b）なら快適に動きます。32Bモデルを動かしたい場合は、量子化レベルを「Q2_K」などの極端に低いものにする必要がありますが、賢さが大幅に低下するため、実務エージェントとしては7Bの方が安定するかもしれません。

### Q2: KV Cacheは、PCを再起動しても残りますか？

残りません。KV CacheはVRAM（メモリ）上のデータなので、プロセスを終了したりPCを落としたりすると消えます。ただし、Ollamaは同じプロンプトが送られてきた際にキャッシュを再構築する最適化を持っているので、2回目以降のロードは速くなります。

### Q3: Pythonではなく、TypeScript（Node.js）でも同じことができますか？

可能です。Ollamaには公式のJSライブラリがあり、同様に `options` 引数で `num_ctx` を指定できます。エージェントのロジック自体は言語に依存しませんが、データ解析ツールなどと連携させるならPythonの方がライブラリが豊富で楽です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Qwen2.5-32Bを快適に動かし、KV Cacheを確保するための必須装備</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Qwen2.5-Coder 使い方 | ローカルでコード生成AIを動かす](/posts/2026-05-19-qwen-coder-local-setup-python-refactor/)
- [Qwen2.5-CoderのQ6量子化でコーディングエージェントを自作する方法](/posts/2026-05-28-qwen2-5-coder-q6-quantization-setup-guide/)
- [Qwen2.5-Coder 使い方 | ローカルでGPT-4o級の開発環境をPythonで構築する](/posts/2026-03-21-qwen2-5-coder-python-local-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 12GBしか持っていませんが、動かす方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Qwen2.5の7Bモデル（qwen2.5:7b）なら快適に動きます。32Bモデルを動かしたい場合は、量子化レベルを「Q2K」などの極端に低いものにする必要がありますが、賢さが大幅に低下するため、実務エージェントとしては7Bの方が安定するかもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "KV Cacheは、PCを再起動しても残りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "残りません。KV CacheはVRAM（メモリ）上のデータなので、プロセスを終了したりPCを落としたりすると消えます。ただし、Ollamaは同じプロンプトが送られてきた際にキャッシュを再構築する最適化を持っているので、2回目以降のロードは速くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "Pythonではなく、TypeScript（Node.js）でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。Ollamaには公式のJSライブラリがあり、同様に options 引数で numctx を指定できます。エージェントのロジック自体は言語に依存しませんが、データ解析ツールなどと連携させるならPythonの方がライブラリが豊富で楽です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Qwen2.5-32Bを快適に動かし、KV Cacheを確保するための必須装備</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

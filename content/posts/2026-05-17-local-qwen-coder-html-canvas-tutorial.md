---
title: "ローカルLLM Qwen 2.5 Coder 使い方"
date: 2026-05-17T00:00:00+09:00
slug: "local-qwen-coder-html-canvas-tutorial"
cover:
  image: "/images/posts/2026-05-17-local-qwen-coder-html-canvas-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen 2.5 Coder"
  - "Ollama 使い方"
  - "ローカルLLM コーディング"
  - "HTML Canvas アニメーション"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen 2.5 Coder 32Bをローカル環境で動かし、物理演算を含むHTML Canvasアニメーションを1発で生成します
- ブラウザだけで動作し、パーティクルの衝突や重力シミュレーションを実装したシングルファイルHTMLを完成させます
- 前提知識：ターミナルでのコマンド入力に抵抗がなく、HTML/JavaScriptの基礎（タグや変数の意味）がわかること
- 必要なもの：VRAM 12GB以上のNVIDIA製GPU、またはメモリ24GB以上のApple Silicon搭載Mac

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで32Bモデルの量子化版を動かすのに最もコストパフォーマンスが良い</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

ローカルLLM、特に今回扱うQwen 2.5 Coder 32Bを快適に動かすにはハードウェアへの投資が不可欠です。
このモデルを4bit量子化（実用レベルの軽量化）で動かす場合、約19GBのVRAMを消費します。
RTX 3060 12GBのようなエントリークラスのGPUではメモリが足りず、メインメモリ（RAM）へのスワップが発生してレスポンスが極端に低下します。
理想はRTX 3090や4090といったVRAM 24GBモデルですが、予算が限られているならRTX 4060 Ti 16GB版が最低ラインの選択肢になります。

Macユーザーであれば、ユニファイドメモリの恩恵を受けられるため、M2/M3チップのメモリ32GB以上のモデルが望ましいです。
16GBメモリのMacでも動かせないことはありませんが、OSやブラウザの消費分を考えるとモデルサイズをさらに削る（Qwen 2.5 Coder 7Bや14Bにする）必要が出てきます。
API料金は一切かかりませんが、電気代と初期のハードウェア投資がコストだと考えてください。
もし手元のPCスペックが足りない場合は、OpenRouterなどのAPI経由でQwen 2.5 Coderを叩く方法もありますが、今回は「自分のマシンで完結させる」ことにこだわります。

## なぜこの方法を選ぶのか

コーディング支援AIといえばClaude 3.5 SonnetやGitHub Copilotが有名ですが、Qwen 2.5 Coder 32Bはそれらに匹敵する性能をローカルで実現しています。
RedditのLocalLLaMAコミュニティでも、HTML Canvasのような「複雑なロジックと視覚的表現が混ざるタスク」において、Qwenが商用モデルを凌駕する場面が報告されています。
ローカルで動かす最大のメリットは、機密性の高いソースコードを外部サーバーに送信せずに済むこと、そしてプロンプトの試行錯誤を無限に繰り返せることです。
特にフロントエンドのプロトタイピングでは、1日に何百回とコードを書き直すため、APIのレートリミットを気にせず秒速で生成できるローカル環境が最強の武器になります。

## Step 1: 環境を整える

まずはローカルLLMを実行するためのバックエンドとして、最も導入が簡単な「Ollama」をインストールします。
Llama.cppを直接ビルドする方法もありますが、設定の簡便さとAPIサーバーとしての使い勝手から、現在はOllama一択だと思っています。

```bash
# macOS/Linuxの場合
curl -fsSL https://ollama.com/install.sh | sh

# Windowsの場合は、公式サイト（ollama.com）からインストーラーをダウンロードしてください。
```

インストール完了後、ターミナルで以下のコマンドを実行してモデルをダウンロードします。

```bash
ollama run qwen2.5-coder:32b
```

このコマンドは、Qwen 2.5 Coder 32Bモデルをダウンロードし、対話可能な状態にします。
32Bモデルはファイルサイズが約19GBあるため、回線速度によっては10分〜20分ほどかかります。
もしVRAMが8GB以下の方は、代わりに `ollama run qwen2.5-coder:7b` を選んでください。性能は落ちますが、速度は圧倒的に速くなります。

⚠️ **落とし穴:** ダウンロード中に接続が切れることがありますが、Ollamaは再開（レジューム）機能があるため、同じコマンドを叩けば続きから開始されます。また、GPUドライバーが最新でないと、モデルのロード時にエラーが出るか、極端に動作が重くなることがあります。必ず最新のGame ReadyまたはStudioドライバーを当てておいてください。

## Step 2: Python経由で制御する設定

Ollamaはデフォルトでローカルの11434ポートでAPIを受け付けています。
ターミナルで直接チャットしてもいいのですが、生成されたHTMLファイルを自動で保存するスクリプトを組んだほうが、実務での開発効率は3倍以上になります。

```python
import requests
import json
import os

# Ollama APIのURL
OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_code(prompt):
    payload = {
        "model": "qwen2.5-coder:32b",
        "prompt": prompt,
        "stream": False,
        "format": "json" # JSON形式で出力を強制する設定
    }

    # タイムアウトを長めに設定（32Bモデルの初回起動時はロードに時間がかかるため）
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    return response.json()['response']

# APIキー不要、外部通信なし
```

ここでは `requests` ライブラリを使用してOllamaに命令を飛ばしています。
なぜJSON形式を指定するのかというと、LLMが余計な解説文を出力してプログラムのパースを邪魔するのを防ぐためです。
実務でAIを使う際、最もストレスが溜まるのは「コードの前後にある不要な挨拶」を削除する作業です。最初から構造化データとして受け取るのが正解です。

## Step 3: 物理演算アニメーションを生成する

それでは実際に、Qwen 2.5 Coderに「物理演算を伴うCanvasアニメーション」を書かせてみましょう。
ここでのポイントは、AIに対して「シングルファイルで作れ」と「物理定数を指定しろ」と命じることです。

```python
prompt = """
以下の仕様でHTML Canvasアニメーションを作成し、有効なJSON形式で出力してください。
キー名は 'html_code' としてください。

仕様：
1. 1枚のHTMLファイルで完結（CSS, JSをインクルード）
2. 画面内を跳ね回る50個のネオンカラーの円を作成
3. 円同士が衝突した際、物理的に正しく弾むように計算（弾性衝突）
4. マウスカーソルが近づくと円が逃げる「斥力」を実装
5. 背景は深い紺色（#000b1e）
6. 画面リサイズに対応
"""

# スクリプトの実行（Step 2の関数を利用）
raw_response = generate_code(prompt)
data = json.loads(raw_response)
html_content = data['html_code']

with open("animation.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("ファイル 'animation.html' が生成されました。")
```

### 期待される出力

実行すると、カレントディレクトリに `animation.html` が作成されます。
これをブラウザ（ChromeやEdge）で開くと、以下の挙動が確認できるはずです。
- 画面を埋め尽くす色鮮やかな円が、重力や壁の跳ね返りを考慮して動く
- 円同士が重なることなく、衝突判定が正確に行われている
- マウスを動かすと、波紋のように円が散っていく

私自身の試行錯誤では、GPT-4oでも「円同士の衝突判定」をサボって重なってしまうことがありましたが、Qwen 2.5 Coder 32Bは1回目からベクトル演算を正確に記述してきました。

## Step 4: 実用レベルにする（エラーハンドリングとデバッグ）

AIが生成したコードがたまに動かない、あるいは画面が真っ白になることがあります。
これはCanvasの初期化タイミングの問題であったり、変数の定義漏れであったりします。
実務レベルに引き上げるには、「AIに自己デバッグさせる」プロセスを組み込みます。

```python
def self_fix_code(initial_code, error_message):
    repair_prompt = f"""
    提供したコードに以下のエラーが含まれているか、期待通りに動作しません。
    コードを修正して、再度HTML全体を出力してください。

    エラー・不具合内容: {error_message}
    元のコード:
    {initial_code}
    """
    return generate_code(repair_prompt)

# もし動かなかったら、ブラウザのコンソールログの内容を渡して再生成させる
# 修正例：
# fixed_html = self_fix_code(html_content, "Canvas context is null at init")
```

この「エラー内容を食わせる」手法は、ローカルLLM運用において極めて重要です。
APIと違って1リクエスト数円というコストが発生しないため、納得がいくまでループを回せます。
私は複雑なシェーダーを書かせる際、この自己ループを3回ほど回すようにしていますが、最終的な完成度は手書きするよりも遥かに高くなります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Ollama error: model not found` | モデル名が間違っているか未取得 | `ollama pull qwen2.5-coder:32b` を実行 |
| 生成速度が1文字/秒以下 | VRAM不足でCPU推論になっている | モデルを7B版に変更するか、量子化ビット数を下げる |
| ブラウザで表示すると画面が真っ白 | JSのエラーが発生している | F12キーでコンソールを確認し、そのエラーをAIに投げて修正させる |

## 次のステップ

この記事で、Qwen 2.5 Coderが「フロントエンドのロジック構築」において極めて強力であることを体感できたと思います。
次は、このスクリプトを「Cursor」や「Aider」といった外部エディタと連携させてみてください。
Ollamaをバックエンドに設定すれば、ローカルにある大量のソースコードを読み込ませた状態で、Qwenにリファクタリングを命じることができます。

特に、ReactやVue.jsといったフレームワークのコンポーネント作成において、Qwen 2.5 Coder 32Bの「文脈理解の深さ」は驚異的です。
特定のライブラリ（Three.jsやD3.jsなど）に特化したプロンプトを組んで、自分専用の「コード生成エンジン」を構築することをおすすめします。
一度この自由度とプライバシーを知ってしまうと、クラウド型AIには戻れなくなるはずです。

## よくある質問

### Q1: NVIDIA以外のグラフィックボード（Radeonなど）でも動きますか？

基本的にはROCm環境を構築すれば動作しますが、OllamaのWindows版などはNVIDIAに最適化されているため、設定に苦労するかもしれません。素直にWSL2上でROCmを動かすか、安定性を求めるならNVIDIA製GPUへの乗り換えを推奨します。

### Q2: 32Bモデルを動かすとPCのファンが爆音になるのですが故障ですか？

正常です。LLMの推論はGPUに高い負荷をかけます。特にVRAMがいっぱいになると発熱も増えるため、ケースのエアフローやGPUの冷却設定（MSI Afterburnerなどでのファン制御）を見直すいい機会かもしれません。

### Q3: 日本語のコメントを入れてもらうことは可能ですか？

可能です。プロンプトに「JavaScriptのコメントはすべて日本語で記述し、各関数の役割を詳しく説明してください」と一言添えるだけで、非常に丁寧な解説付きコードを出力してくれます。

---

## あわせて読みたい

- [Qwen3-Coder-Next 使い方 | 最強のコード生成AIで開発を自動化する手順](/posts/2026-03-07-qwen3-coder-next-local-python-tutorial/)
- [Qwen 2.5 27B 使い方 入門：24GB VRAMでGPT-4級のコード生成環境を構築する方法](/posts/2026-04-24-qwen-2-5-27b-local-python-guide/)
- [Qwen 2.5やGemma 2をローカル環境で高速に動かす方法](/posts/2026-04-29-how-to-setup-local-llm-qwen-python-ollama/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "NVIDIA以外のグラフィックボード（Radeonなど）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはROCm環境を構築すれば動作しますが、OllamaのWindows版などはNVIDIAに最適化されているため、設定に苦労するかもしれません。素直にWSL2上でROCmを動かすか、安定性を求めるならNVIDIA製GPUへの乗り換えを推奨します。"
      }
    },
    {
      "@type": "Question",
      "name": "32Bモデルを動かすとPCのファンが爆音になるのですが故障ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "正常です。LLMの推論はGPUに高い負荷をかけます。特にVRAMがいっぱいになると発熱も増えるため、ケースのエアフローやGPUの冷却設定（MSI Afterburnerなどでのファン制御）を見直すいい機会かもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のコメントを入れてもらうことは可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。プロンプトに「JavaScriptのコメントはすべて日本語で記述し、各関数の役割を詳しく説明してください」と一言添えるだけで、非常に丁寧な解説付きコードを出力してくれます。 ---"
      }
    }
  ]
}
</script>

---
title: "Qwen3.5-35B-A3BとAiderで爆速コーディング環境を構築する方法"
date: 2026-02-25T00:00:00+09:00
slug: "qwen35-35b-aider-local-ai-coding-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Qwen3.5-35B-A3B 使い方"
  - "Aider 入門"
  - "ローカルLLM コーディング"
  - "Ollama Python 連携"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Qwen3.5-35B-A3Bをローカルで動かし、AIエージェント「Aider」と連携させて、既存のPythonコードのバグ修正と機能追加を全自動で行う環境を構築します。
- 前提知識：Pythonの基本的な読み書きができること、ターミナルの操作に抵抗がないこと。
- 必要なもの：VRAM 12GB以上のGPU（RTX 3060 12GB / 4070以上推奨）、Docker（任意だが推奨）。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBあればQwen3.5-35Bの量子化版を余裕を持って高速動作させられるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

これまでローカルLLMでのコーディングといえば、Llama 3や旧Qwenの70Bクラスを無理やり動かすか、軽量な7Bクラスで妥協するかの二択でした。
しかし、Qwen3.5-35B-A3Bは「MoE（Mixture of Experts）」を採用しており、総パラメータは35Bありながら、推論時に動くのはわずか3B程度です。
これにより、RTX 3060のようなミドルレンジのGPUでも、Claude 3.5 Sonnetに匹敵する「エージェントとしての思考能力」をローカルで実現できるようになりました。

他の軽量モデルは指示を忘れたり、ファイル構造を壊したりすることが多々ありますが、このモデルは「ツール利用（Function Calling）」の精度が異常に高いです。
有料のAPIに課金し続けるのではなく、プライバシーを守りつつ、手元のハードウェア資産をフル活用して「24時間働いてくれるプログラミング助手」を作るには、現時点でこの構成がベストな選択肢だと言い切れます。

## Step 1: 環境を整える

まずはLLMを動かすためのバックエンドとして「Ollama」を導入し、Qwen3.5-35B-A3Bをダウンロードします。

```bash
# Ollamaのインストール（未導入の場合）
curl -fsSL https://ollama.com/install.sh | sh

# Qwen3.5-35B-A3Bをダウンロードして起動
ollama run qwen3.5:35b-coder-instruct-q4_K_M
```

Ollamaは複雑な設定なしにモデルをAPIサーバー化してくれるツールです。
今回使用する `q4_K_M` 量子化版は、推論精度をほぼ維持したままVRAM消費を約20GB程度に抑えてくれます。
もしVRAMが12GB程度しかない場合は、さらに軽量な `q2_K` などを選ぶ必要がありますが、まずはこの標準的な量子化版で試すべきです。

⚠️ **落とし穴:**
WindowsユーザーでWSL2を使用している場合、GPUが正しく認識されないことがあります。
`nvidia-smi` コマンドでGPUが見えるか確認し、見えない場合はNVIDIA Container Toolkitのインストールが必要です。
これを確認せずに進めると、CPU推論になってしまい、1文字出すのに数秒かかる地獄を見ることになります。

## Step 2: 基本の設定

次に、AIエージェントである「Aider」をインストールし、Ollama経由でQwen3.5を使えるように設定します。

```bash
# Aiderのインストール
pip install aider-chat

# 作業ディレクトリの作成
mkdir ai-coding-test && cd ai-coding-test
git init

# AiderをQwen3.5設定で起動する
export OLLAMA_API_BASE=http://localhost:11434
aider --model ollama/qwen3.5:35b-coder-instruct-q4_K_M
```

Aiderは「チャットで指示すると、ファイルを直接書き換えてGitコミットまでしてくれる」強力なCLIツールです。
なぜ `export` でAPIベースを指定するのかというと、AiderがデフォルトでOpenAIのAPIを探しに行ってしまうため、接続先をローカルのOllamaに強制的に向ける必要があるからです。
Gitを初期化（git init）するのは、AIがコードを壊したときにいつでもロールバックできるようにするためです。これは実務でAIを使う際の鉄則です。

## Step 3: 動かしてみる

実際に、わざとバグを含んだFlaskアプリをQwenに直させてみましょう。
まずは適当なファイルを作成します。

```python
# app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    # わざと変数を間違えるバグ
    return f"Hello, {name}!"

if __name__ == "__main__":
    app.run(debug=True)
```

Aiderのプロンプト画面で、以下のように指示を出してください。

```
/add app.py
app.pyには'name'が定義されていないというバグがあります。
クエリパラメータからnameを取得するように修正し、デフォルト値を'World'にしてください。
また、修正が終わったらこのコードを実行するためのrequirements.txtも作成してください。
```

### 期待される出力

```
（Qwenの思考プロセスが表示された後）
Applied edit to app.py
Created requirements.txt
Commit 1234abc: Fix undefined variable bug and add requirements.txt
```

Qwen3.5-35B-A3Bは、ファイルのコンテキストを正確に理解し、`request.args.get('name', 'World')` という修正案を提示するはずです。
注目すべきは、単にコードを出すだけでなく「既存のコードのどこを消してどこに挿入するか」というDiff形式の指示をAiderに完璧に送っている点です。

## Step 4: 実用レベルにする

単一ファイルの修正だけでなく、複数のファイルにまたがるリファクタリングをさせると、このモデルの真価がわかります。
実務では、以下の設定を追加して「思考の深さ」を調整します。

```bash
# コンテキストウィンドウを拡張して起動（大規模プロジェクト用）
aider --model ollama/qwen3.5:35b-coder-instruct-q4_K_M --cache-prompts --map-tokens 1024
```

`--cache-prompts` を使う理由は、大規模なコードベースを読み込ませた際に、毎回同じコードを送り直してVRAMを消費するのを防ぐためです。
また、Qwen3.5は英語での指示の方がわずかに精度が高い傾向にありますが、日本語でも十分に論理的な推論が可能です。
私はSIer時代、手動でテストコード（Unit Test）を書くのに1日費やしていましたが、今は `/test` と指示するだけで、QwenがPytestのコードを数秒で生成してくれます。

さらに実用性を高めるには、`.aider.conf.yml` という設定ファイルを作っておくと便利です。
そこに「常に使うモデル」や「除外するディレクトリ（node_modulesなど）」を書いておくことで、タイピングの手間を減らせます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Connection refused | Ollamaが起動していない | `ollama serve` を別ターミナルで実行する |
| CUDA out of memory | VRAM不足 | モデルの量子化サイズを `q2_K` などに変更する |
| Aiderが修正を適用しない | モデルがDiff形式を失敗している | プロンプトで「必ずDiff形式で出力して」と念押しする |

## 次のステップ

Qwen3.5-35B-A3Bを使ったローカル開発環境が整ったら、次は「Open Interpreter」との連携に挑戦してみてください。
Aiderはコード修正に特化していますが、Open InterpreterはOSレベルでの操作（ファイルの整理、グラフの作成、ブラウジング）が可能です。
この2つを使い分けることで、設計はClaude 3.5 Sonnetで行い、実装とデバッグはローカルのQwenで行うという、コストと効率の最適解が見つかるはずです。

また、RTX 4090を2枚挿ししているような環境であれば、さらに大きな70Bモデルも視野に入りますが、正直なところ「レスポンスの速さ」と「賢さ」のバランスでは、この35B-A3Bが現状のローカルLLM界の覇者だと言えます。
まずは自分のプロジェクトに導入して、1時間かかっていたリファクタリングが5分で終わる快感を味わってください。

## よくある質問

### Q1: RTX 3060 (12GB) でも快適に動きますか？

動きますが、35Bモデルの `q4_K_M` 量子化だとVRAMが少し溢れるかもしれません。その場合は `q3_K_L` 以下の量子化モデルを試してください。動作速度は若干落ちますが、思考のロジック自体は大きく崩れません。

### Q2: 日本語で指示しても大丈夫ですか？

問題ありません。Qwenシリーズは中国語と英語がメインですが、日本語の理解力も非常に高いです。ただし、技術的な用語は英語で伝えたほうが、モデルが学習データ内の正解にたどり着きやすくなります。

### Q3: API（OpenAI等）を使うのとどちらが安いですか？

初期投資（GPU代）を除けば、圧倒的にローカルです。特にエージェント機能は何度もLLMにリクエストを投げるため、APIだと月額数万円飛ぶこともあります。1日3時間以上開発するなら、RTX 4090を買っても数ヶ月で元が取れます。

---

## あわせて読みたい

- [次世代AI「Qwen3.5」をいち早くローカル環境で試す方法](/posts/2026-02-08-5c9988c9/)
- [Claude 3.5 Sonnetのアイデンティティを検証しモデルの汚染を確認するスクリプト](/posts/2026-02-24-claude-sonnet-identity-bug-deepseek-verification/)
- [オープンソース最強候補「Kimi K2.5」をローカル環境で導入し、マルチモーダルAIエージェントを構築する方法](/posts/2026-01-27-d3150ffa/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 3060 (12GB) でも快適に動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、35Bモデルの q4KM 量子化だとVRAMが少し溢れるかもしれません。その場合は q3KL 以下の量子化モデルを試してください。動作速度は若干落ちますが、思考のロジック自体は大きく崩れません。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語で指示しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "問題ありません。Qwenシリーズは中国語と英語がメインですが、日本語の理解力も非常に高いです。ただし、技術的な用語は英語で伝えたほうが、モデルが学習データ内の正解にたどり着きやすくなります。"
      }
    },
    {
      "@type": "Question",
      "name": "API（OpenAI等）を使うのとどちらが安いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "初期投資（GPU代）を除けば、圧倒的にローカルです。特にエージェント機能は何度もLLMにリクエストを投げるため、APIだと月額数万円飛ぶこともあります。1日3時間以上開発するなら、RTX 4090を買っても数ヶ月で元が取れます。 ---"
      }
    }
  ]
}
</script>

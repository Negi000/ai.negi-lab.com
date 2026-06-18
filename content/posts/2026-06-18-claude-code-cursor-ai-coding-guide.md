---
title: "Claude CodeとCursorを併用したAI爆速開発入門"
date: 2026-06-18T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-06-18-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 開発効率"
  - "AIコーディング 併用"
  - "Python 自動化"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

- 特定のニュースサイトから最新記事を取得し、その内容をAIで要約してMatplotlibで可視化するPythonツールを作成します
- Claude Codeが全体構造の設計とターミナル操作を、Cursorがコードの細部修正とリファクタリングを担う「AI二刀流」の開発スタイルを習得できます
- 前提知識: Pythonの基本的な構文がわかり、ターミナルの基本操作（cd, ls等）ができること
- 必要なもの: Anthropic APIキー、Cursorのインストール、Node.js（Claude Code用）

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツールを複数同時起動しても余裕のある32GBメモリ以上が推奨</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

まず、財布とPCの準備が必要です。Claude CodeはAnthropicのAPIを直接叩くため、従量課金が発生します。目安として、この記事の内容を完走するのに$1〜$2程度（約150円〜300円）のAPI使用料を見込んでください。無料枠ではありません。

Cursorについては、無料枠でも可能ですが、モデルを「Claude 3.5 Sonnet」に固定して使い倒すなら月額$20のProプランが理想です。ハードウェアに関しては、ローカルLLMを動かすわけではないのでRTX 4090は不要ですが、ブラウザとCursor、ターミナルを同時に立ち上げるためメモリは最低16GB、できれば32GB以上を推奨します。M1/M2/M3チップ搭載のMacであれば、ベースモデルでも十分快適に動きます。

## なぜこの方法を選ぶのか

現在、Cursorだけでも開発は完結しますが、あえてClaude Codeを併用する理由は「自律性の違い」にあります。CursorのComposerはコード編集に特化していますが、外部ライブラリのインストールやデバッグのためのファイル実行、ディレクトリ構造の把握においては、CLI（コマンドライン）で動作するClaude Codeの方が圧倒的に「話が早い」です。

私の検証では、Cursorでコードを書き、Claude Codeに「このコードを実行して、エラーが出たら勝手に直して」と丸投げするスタイルが最も開発効率が高かった。エディタの中で人間がポチポチ操作する時間を極限まで減らし、AIに「現場監督」を任せるのが今の最適解です。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはAnthropicが公式に提供しているCLIツールで、Node.js環境が必要です。

```bash
# Node.jsがインストールされているか確認
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが立ち上がるのでログインする）
claude auth login
```

次に、今回作成するプロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-news-app
cd ai-news-app
cursor .
```

なぜNode.js経由でインストールするのかというと、Claude Code自体がTypeScriptで構築された高度なエージェントツールだからです。Pythonプロジェクトであっても、管理ツールとしてNode.jsが必要になる点は覚えておいてください。

⚠️ **落とし穴:**
Windows環境でPowerShellを使っている場合、実行ポリシーの関係で `claude` コマンドが弾かれることがあります。その場合は管理者権限で `Set-ExecutionPolicy RemoteSigned` を実行してください。また、APIの残高（Credits）が0だと動作しません。Anthropic Consoleから最低$5はチャージしておきましょう。

## Step 2: 基本の設定

Claude Codeを起動する前に、プロジェクトの「ガードレール」を設定します。AIに勝手に消されたくないファイルや、読み込んでほしくない巨大なデータがある場合、`.gitignore` を参照させます。

```bash
# ターミナルでClaude Codeを起動
claude
```

初回起動時に「このディレクトリをスキャンしていいか？」と聞かれます。`y` を入力します。

次に、Cursor側の設定です。
1. Cursorの設定（Settings > Models）を開く
2. `Claude 3.5 Sonnet` が有効になっていることを確認
3. 他の古いモデル（GPT-4など）は、混乱を避けるためオフにするのが私の推奨です。

なぜモデルを固定するのか。それは、Claude CodeとCursorの両方で同じ「脳（3.5 Sonnet）」を共有させるためです。異なるモデルを使うと、片方が書いたコードをもう片方が「不適切だ」と判断して修正し始める「AI同士の喧嘩」が発生し、トークンを無駄に消費します。

## Step 3: 動かしてみる

いよいよ開発をスタートします。ターミナルの `claude` 画面で以下のプロンプトを投げてください。

```text
ニュースサイト（例: YahooニュースのITカテゴリ）から見出しを取得して、
単語の出現頻度をカウントし、上位5件を棒グラフで表示するPythonスクリプトを作りたい。
必要なライブラリのインストールから始めて、ベースのコードを書いて。
```

### 期待される出力

Claude Codeは、以下のように動くはずです。
1. `pip install requests beautifulsoup4 matplotlib` を実行していいか聞いてくる（yで承認）
2. `main.py` というファイルを作成する
3. 実行して、実際にスクレイピングができるかテストする

もしエラーが出たら、Claude Codeが勝手にログを読み取り「セレクタが間違っていました。修正します」と自己解決します。これがCursor単体では難しい「自律デバッグ」の威力です。

## Step 4: 実用レベルにする

Claude Codeが作ったコードは、往々にして「動くけれど見た目が悪い」あるいは「日本語が文字化けする」といった課題があります。ここでCursorの出番です。

Cursorで `main.py` を開き、コード全体を選択して `Cmd + K`（またはComposer）を叩きます。

```text
# Cursorへの指示
- グラフの日本語文字化けを防ぐために、Japanize-matplotlibを導入して
- ニュースの取得件数を10件から20件に増やして
- 取得したデータを `data/results.json` に保存する機能を追加して
```

Cursorはエディタ内の差分表示が非常に見やすいため、AIがどこをどう変えようとしているのかを人間がレビューするのに適しています。

次に、このコードをより堅牢にします。再度、ターミナルの Claude Code に戻り、以下のように指示します。

```text
作成したスクリプトにエラーハンドリングを追加して。
特にネットワークエラーや、サイトの構造が変わって要素が見つからない場合の処理を重点的に。
また、処理の進捗を rich ライブラリを使ってプログレスバーで表示するようにして。
```

なぜここでまたClaude Codeに戻るのか。それは、`rich` などの新しいライブラリが必要になった際、Claude Codeなら「インストールから実装、動作確認まで」をワンストップでこなしてくれるからです。Cursorだと「ライブラリが足りません」というエラーをターミナルで見て、自分で `pip install` する手間が発生します。

### 完成したコードの例（参考）

```python
import requests
from bs4 import BeautifulSoup
from collections import Counter
import matplotlib.pyplot as plt
import japanize_matplotlib
import os
import json
from rich.progress import track

def fetch_news():
    url = "https://news.yahoo.co.jp/categories/it"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    # 実際はサイトの構造に合わせてセレクタを調整
    articles = soup.select('.sc-iBkjds')

    titles = []
    for article in track(articles[:20], description="Processing articles..."):
        titles.append(article.get_text())
    return titles

def analyze_and_plot(titles):
    # 簡易的な単語カウント（本来はMeCab等を使用）
    words = []
    for title in titles:
        words.extend([w for w in title.split() if len(w) > 1])

    counts = Counter(words).most_common(5)
    labels, values = zip(*counts)

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title("ITニュース頻出キーワード")
    plt.savefig("result.png")
    print("Graph saved as result.png")

if __name__ == "__main__":
    try:
        data = fetch_news()
        analyze_and_plot(data)
    except Exception as e:
        print(f"Error occurred: {e}")
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが止まる | APIのRate Limit（制限）に達した | 数分待つか、Tierを上げる（課金額を増やす） |
| ライブラリが見つからない | 仮想環境（venv）の不一致 | `claude` 起動前に `source venv/bin/activate` する |
| スクレイピングで中身が空 | サイトの構造変更またはBot検知 | User-Agentの設定をClaude Codeに依頼する |

## 次のステップ

ここまでで、Claude Codeに「実行と修正」を任せ、Cursorで「設計の微調整」を行うワークフローが体験できたはずです。

この次のステップとしては、Claude Codeに「テストコードの作成」を依頼してみてください。`pytest` を使ったテストを自動生成させ、それを実際に実行してパスするまで修正させる作業は、AIが最も得意とする領域の一つです。

また、今回は単純なスクリプトでしたが、FastAPIなどを使ったWebアプリ開発でもこの併用スタイルは威力を発揮します。CursorでHTML/CSSのレイアウトを調整し、Claude Codeでバックエンドのロジックとデータベース移行（Migration）を自動化する。この役割分担を意識するだけで、あなたの開発速度は従来の3倍以上になります。

最後に私からのアドバイスです。AIは完璧ではありません。時には間違ったライブラリを提案することもあります。その時は「それは古いよ」と一言指摘してあげてください。彼らはすぐに学習し、最新のドキュメントを読みに行きます。

## よくある質問

### Q1: Claude CodeとCursor、どっちをメインで使うべき？

基本はCursorです。コードの全体像を眺めながら書くのはエディタの方が向いています。Claude Codeは「面倒な環境構築」「依存関係の解決」「一括リファクタリング」など、ターミナルが絡む重たい作業の時に召喚する「特効薬」として使うのがベストです。

### Q2: API代が怖いです。節約する方法は？

Claude Code内で `/compact` コマンドを使って、会話履歴を圧縮してください。また、巨大なログファイルを読み込ませないように `.claudeignore` を適切に設定しましょう。不要な情報を読ませないことが最大の節約です。

### Q3: Python以外の言語でも同じことができますか？

もちろんです。TypeScript/Next.jsやGo、Rustでも同様のフローが可能です。特にコンパイルが必要な言語（RustやGo）では、Claude Codeに「コンパイルエラーが消えるまで直して」と命令できるため、非常に相性が良いです。

---

## あわせて読みたい

- [CursorとClaude Codeを併用して爆速でPythonツールを開発する方法](/posts/2026-06-14-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Spotlight by Backplanes：Claude Codeの「思考の軌跡」を可視化して開発効率を最大化する](/posts/2026-06-10-spotlight-backplanes-claude-code-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeとCursor、どっちをメインで使うべき？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本はCursorです。コードの全体像を眺めながら書くのはエディタの方が向いています。Claude Codeは「面倒な環境構築」「依存関係の解決」「一括リファクタリング」など、ターミナルが絡む重たい作業の時に召喚する「特効薬」として使うのがベストです。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code内で /compact コマンドを使って、会話履歴を圧縮してください。また、巨大なログファイルを読み込ませないように .claudeignore を適切に設定しましょう。不要な情報を読ませないことが最大の節約です。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じことができますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScript/Next.jsやGo、Rustでも同様のフローが可能です。特にコンパイルが必要な言語（RustやGo）では、Claude Codeに「コンパイルエラーが消えるまで直して」と命令できるため、非常に相性が良いです。 ---"
      }
    }
  ]
}
</script>

---
title: "CursorとClaude Codeの併用でAI開発を極める！最新環境構築ガイド"
date: 2026-06-23T00:00:00+09:00
slug: "cursor-claude-code-integration-guide"
cover:
  image: "/images/posts/2026-06-23-cursor-claude-code-integration-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "Anthropic API 料金"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- CursorのGUIとClaude CodeのCLIエージェントをシームレスに連携させた開発環境
- FastAPIを使用した「株価リアルタイム監視・通知API」のプロトタイプ

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro 32GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Cursorのインデックス作成とClaude Codeの並行動作には32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520Apple%2520Silicon%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%252032GB%2520Apple%2520Silicon%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%2032GB%20Apple%20Silicon&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

### 前提知識
- Pythonの基本的な文法
- ターミナル（Terminal / PowerShell）の基本操作
- Node.jsがインストールされていること

### 必要なもの
- Anthropic APIキー（Claude Code用）
- Cursorの有料プラン（Pro以上推奨、無料枠でも可）
- Node.js v18.19.0 以上

## 先に確認するスペック・料金

AIコーディングを本気で行うなら、ケチってはいけないのが「API代」と「メモリ」です。Claude Codeは非常に強力なエージェントですが、ターミナル上で自律的に動くため、1回のタスクで数十円〜数百円のAPI費用（Claude 3.5 Sonnet使用分）が飛ぶこともあります。

私はRTX 4090を2枚挿した自作PCでローカルLLMも回していますが、VS Code/Cursorの拡張機能やClaude Codeのような最新ツールに関しては、ローカルよりもAPI経由のほうが圧倒的に「賢さ」の恩恵を受けられます。

PCスペックとしては、Cursorのインデックス作成とClaude Codeの同時並行を考えると、メモリ32GB以上が理想です。16GBでも動きますが、大規模なリポジトリを読み込ませるとスワップが発生し、レスポンスが1秒以上遅れることがあります。この「1秒の差」が開発のリズムを壊すため、可能な限りハードウェアへの投資を優先してください。

## なぜこの方法を選ぶのか

これまで私は「Cursor（Cline/Aider等の拡張機能含む）」だけで完結させようとしてきました。しかし、Claude Codeの登場で結論が変わりました。

Cursorは「コードの全体像を視覚的に把握し、インラインで修正する」のに適しています。一方でClaude Codeは「ターミナル操作、テスト実行、Git操作を含めた自律的なタスク遂行」において圧倒的に手数が少ないです。

例えば「テストコードを全件実行して、エラーが出た箇所をすべて修正し、コミットまで済ませる」という作業。Cursorだと人間がボタンを押す回数が多いですが、Claude Codeなら1行の命令で済みます。この「GUIとCLIの使い分け」が、現時点で最も生産性が高いAI開発の正解だと確信しています。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorから呼び出せるようにします。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# バージョン確認（2025年3月時点の最新版を確認）
claude --version

# 初回認証（ブラウザが開くのでAnthropicアカウントでログイン）
claude auth login
```

Claude CodeはNode.js環境で動作するCLIツールです。`npm`を使用してグローバルにインストールすることで、Cursor内のターミナルから直接呼び出せるようになります。

⚠️ **落とし穴:**
Node.jsのバージョンが古いと、インストール中にエラーが出るか、実行時に謎の挙動をします。`node -v`で18.19.0以上であることを必ず確認してください。また、WindowsユーザーはPowerShellを管理者権限で実行しないとシンボリックリンク作成で失敗することがあります。

## Step 2: 基本の設定

Claude Codeを起動し、開発環境の権限を与えます。これをしないと、ファイルを作成したりコマンドを実行したりするたびに許可を求められ、エージェントの良さが死にます。

```bash
# プロジェクトディレクトリを作成して移動
mkdir ai-stock-app && cd ai-stock-app

# Claude Codeの起動
claude
```

起動後、まず以下の設定を確認・変更してください。

```bash
# Claude Codeの対話モード内で実行
/config set -g autoExecute true
```

「なぜこの設定にするのか」という点ですが、Claude Codeはデフォルトでは「コマンド実行前にユーザーの許可」を求めます。しかし、エンジニアが横でずっと見ているなら、信頼できるディレクトリ内では自動実行（autoExecute）をオンにしたほうが、開発スピードは3倍速くなります。

## Step 3: 動かしてみる

それでは、Cursorの画面を開いた状態で、下のターミナルからClaude Codeに「株価を取得するAPI」を作らせてみましょう。

```bash
# Claude Codeのプロンプトに入力
yfinanceを使って、指定したティッカーシンボルの最新価格を返すFastAPIのアプリを作って。
ディレクトリ構成はシンプルに main.py 1ファイルで。
必要なライブラリのインストールも済ませておいて。
```

### 期待される出力

Claude Codeが自律的に以下を判断して実行します。
1. `pip install fastapi uvicorn yfinance` の実行
2. `main.py` の作成とコード記述
3. サーバーの起動確認

```python
# main.py の例
import yfinance as yf
from fastapi import FastAPI

app = FastAPI()

@app.get("/price/{ticker}")
def get_price(ticker: str):
    stock = yf.Ticker(ticker)
    price = stock.history(period="1d")['Close'].iloc[-1]
    return {"ticker": ticker, "price": price}
```

Cursorの画面上で、左側のファイルツリーに即座に `main.py` が現れるはずです。これがGUIとCLIを併用する醍醐味です。

## Step 4: 実用レベルにする

ここからが本番です。プロトタイプを「仕事で使えるレベル」に引き上げます。エラーハンドリングを追加し、さらに「特定の価格を超えたらログを出す」機能を追加させます。

今度はCursorの「Composer（Ctrl+I / Cmd+I）」を使って、コードのロジックを修正しましょう。

1. Cursorで `main.py` を開く。
2. Composerに以下を入力：
   「このAPIに、株価が取得できなかった場合の例外処理を追加して。また、価格チェックのバックグラウンドタスクを実装するための雛形も作って」

```python
# 修正後の実用的なコード例
import yfinance as yf
from fastapi import FastAPI, HTTPException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

def fetch_stock_price(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            raise ValueError(f"No data found for {ticker}")
        return data['Close'].iloc[-1]
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None

@app.get("/price/{ticker}")
async def get_price(ticker: str):
    price = fetch_stock_price(ticker)
    if price is None:
        raise HTTPException(status_code=404, detail="Stock info not found")
    return {"ticker": ticker, "price": float(price)}
```

「なぜこの方法か」というと、細かいロジックの修正やリファクタリングは、CursorのComposerで変更箇所を「差分（Diff）」として確認しながら進めるほうが、AIの暴走を防げるからです。

逆に、この後の「Gitへのコミット」や「README.mdの自動生成」は、再びターミナルのClaude Codeに戻って一言命じるだけです。

```bash
# 再びClaude Codeで
これまでの変更内容を要約して、Conventional Commitsに従ってコミットしておいて。
```

これで、メッセージの作成からコミットまで完了します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm bin -g` でパスを確認し、環境変数に追加する。 |
| API代が急激に増える | Claude Codeがループしている | `/config set -g maxIterations 5` などで最大ループ数を制限する。 |
| ライブラリの競合 | venv（仮想環境）を使っていない | 常に `python -m venv .venv` を作成し、Claude Codeにそれを認識させる。 |

## 次のステップ

この環境が整えば、あなたは「仕様を考える人」になり、AIが「手を動かす人」になります。次に挑戦すべきは、以下の3つです。

1. **GitHub Actionsとの連携**:
   Claude Codeに「このプロジェクト用のCI/CDパイプラインを組んで」と頼み、自動テスト環境を構築してみてください。
2. **MCP（Model Context Protocol）の導入**:
   CursorやClaude CodeにGoogle検索やSlack通知の権限を与えるMCPサーバを導入することで、AIが自ら最新情報を検索してコードを書くようになります。
3. **プロンプトエンジニアリングの自動化**:
   `.claudecode.md` というファイルをプロジェクトルートに作り、プロジェクト独自の命名規則や禁止事項を記述してください。これにより、AIの出力品質が劇的に安定します。

AIコーディングは、ツールを一つに絞る必要はありません。Cursorの「目」とClaude Codeの「手」を使い分けるのが、現在の最適解です。

## よくある質問

### Q1: Cursorの有料プランに入っていますが、Claude CodeのAPI代は別途かかりますか？

はい、かかります。Cursorの料金はCursor社のモデル利用料であり、Claude CodeはAnthropic社のAPIを直接叩くため、従量課金となります。月額$20のCursor代とは別に、月間$10〜30程度のAPI予算を見ておくのが現実的です。

### Q2: Claude Codeがファイルを勝手に消したりしませんか？

100%安全とは言い切れません。そのため、必ずGit管理下のディレクトリで作業してください。Claude Codeが何かミスをしても、CursorのGUIからGit Graphを見れば即座に `git restore` で戻せます。

### Q3: Python以外の言語でも同じように動きますか？

もちろんです。TypeScriptやRust、Goなどでも同様のフローが使えます。特にTypeScript環境では、Claude Codeが `npm test` を自分で回してエラーを潰していく様子は感動的ですらあります。

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)
- [CursorとClaude Codeを併用して爆速でPythonツールを開発する方法](/posts/2026-06-14-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorの有料プランに入っていますが、Claude CodeのAPI代は別途かかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、かかります。Cursorの料金はCursor社のモデル利用料であり、Claude CodeはAnthropic社のAPIを直接叩くため、従量課金となります。月額$20のCursor代とは別に、月間$10〜30程度のAPI予算を見ておくのが現実的です。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeがファイルを勝手に消したりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "100%安全とは言い切れません。そのため、必ずGit管理下のディレクトリで作業してください。Claude Codeが何かミスをしても、CursorのGUIからGit Graphを見れば即座に git restore で戻せます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じように動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScriptやRust、Goなどでも同様のフローが使えます。特にTypeScript環境では、Claude Codeが npm test を自分で回してエラーを潰していく様子は感動的ですらあります。 ---"
      }
    }
  ]
}
</script>

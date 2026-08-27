---
title: "Claude CodeとCursorを併用したAIコーディング環境構築と実践ガイド"
date: 2026-08-28T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-08-28-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "Python 自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude Code（CLI）に設計とテストを任せ、Cursor（IDE）でコードの最終調整を行う「ハイブリッド開発フロー」を構築します
- 実践として「ニュースサイトから記事を取得し、要約してSlackへ通知するPythonツール」を、自ら1行もコードを書かずに完成させます
- プロンプトの指示だけで、スクレイピングからAPI連携、ユニットテストの作成までを自動化する手順を体験できます

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIによる大量のファイル読み書きとIDE動作にはメモリ32GB以上が推奨</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 先に確認するスペック・料金

この環境を構築するには、Claude Proのサブスクリプション（月額$20）とは別に、AnthropicのAPIコンソールでのクレジット購入が必要です。Claude Codeは現在パブリックベータ版であり、CLIからの操作はすべてAPI経由の課金となるため、最低$5程度のデポジット（前払い）を推奨します。

PCスペックに関しては、MacBook Pro（M1チップ以上、メモリ16GB以上）であれば快適に動作します。Windows環境の場合は、WSL2（Ubuntu）の導入が必須です。AIがファイルを高速に読み書きするため、ストレージはNVMe SSDであることが望ましいです。

Cursor Pro（月額$20）も併用しますが、これは無料枠でも試せます。ただし、大規模なリファクタリングを行う際は、Claude 3.5 Sonnetを制限なく使えるProプランが実質的な標準装備となります。合計で月額5,000円程度のコストがかかりますが、開発速度が3倍以上になることを考えれば、エンジニアとしては「安い投資」だと判断しています。

## なぜこの方法を選ぶのか

Cursorだけでも十分強力ですが、Cursorはあくまで「エディタ」であり、ターミナルの操作や複数のファイルにまたがる破壊的なリファクタリングには限界があります。一方でClaude Codeは「エージェント型CLI」であり、テストの実行、エラーログの解析、修正案の適用を自律的に繰り返す能力に長けています。

設計図を描き、ターミナルでテストを回しながら骨組みを作るのはClaude Code。そのコードを視覚的に確認し、UIの微調整やインテリセンスを効かせた細かな修正を行うのはCursor。この役割分担が、2024年末時点でのAIコーディングにおける最適解だと私は確信しています。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。Node.js（v18以上）が必要ですので、未導入の場合は公式サイトからLTS版を入れてください。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# バージョン確認（正常にインストールされたか）
claude --version

# Anthropic APIとの連携（ブラウザが開くので認証する）
claude auth login
```

`npm install -g` でグローバルにインストールするのは、どのプロジェクトディレクトリからでも即座に呼び出せるようにするためです。`claude auth login`を実行すると、APIキーの管理をClaude Codeが代行してくれるため、環境変数を手動で汚す必要がありません。

⚠️ **落とし穴:** Node.jsのバージョンが古いと、インストール中に「Unexpected token」などのエラーが出ることがあります。`node -v`で18.x以降であることを必ず確認してください。また、APIのクレジットが0だとログイン後の初期化で失敗するため、事前に数ドル分チャージしておくのが無難です。

## Step 2: プロジェクトの初期化とCursorの設定

次に、開発用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-news-agent
cd ai-news-agent
cursor .
```

Cursorを開いたら、`Ctrl + Shift + J`（または設定画面）から、モデルに「Claude 3.5 Sonnet」が選択されていることを確認してください。Claude CodeとCursorで同じモデルを使うことで、思考のズレを最小限に抑えられます。

次に、Cursorの「Rules for AI」（.cursorrules）に以下の設定を追記します。

```text
- コードの修正は常にテストコードとセットで行うこと
- 日本語でコメントを記述すること
- 外部ライブラリを使用する場合は、まずrequirements.txtに追記すること
```

この設定をする理由は、AIが勝手にライブラリをインストールして環境を汚すのを防ぎ、かつ保守性の高いコード（テスト付き）を強制するためです。

## Step 3: Claude Codeで骨組みを自動生成する

Cursor内のターミナル（`Ctrl + ~`）を開き、`claude`と入力してClaude Codeを起動します。ここからが本番です。以下のプロンプトを打ち込んでください。

```bash
# Claude Codeの対話画面で入力
> 「ニュースサイト（例：TechCrunch）の最新記事5件を取得し、Claude APIで3行に要約して、SlackのWebhookへ送信するPythonツール」の骨組みを作ってください。
> 1. uv（Pythonパッケージ管理）を使用して環境を構築すること
> 2. スクレイピングにはBeautifulSoup、HTTPリクエストにはhttpxを使うこと
> 3. 各機能のユニットテストも作成すること
```

### 期待される出力

```
- .python-version の作成
- pyproject.toml の作成
- main.py (スクレイピング、要約、送信ロジック) の作成
- tests/test_main.py の作成
- uv sync による依存関係の解決
```

Claude Codeは、単にコードを書くだけでなく、実際に`uv sync`コマンドを実行して仮想環境を構築し、ファイルを作成します。これがCursor単体では難しい「エージェント」としての挙動です。

### 動作確認

次に、作成されたコードが動くかテストを命じます。

```bash
> テストを実行して、問題があれば修正してください。
```

Claude Codeは`pytest`を自動で実行し、エラーが出ればスタックトレースを読み取って自らコードを修正します。私はこのプロセスを「AIによる自食」と呼んでいますが、人間がデバッグに費やす時間を8割削減できます。

## Step 4: 実用レベルにする

骨組みができたら、Cursorの出番です。Claude Codeが作成したコードには、しばしば「実用上の配慮」が欠けていることがあります。例えば、リトライ処理や詳細なログ出力などです。

Cursorのチャット（`Ctrl + L`）を開き、`main.py`を参照しながら以下のように指示します。

```python
# Cursorへの指示
@main.py に対して、以下の改良を加えてください。
1. HTTPリクエストが失敗した際に、最大3回まで指数バックオフでリトライする処理を追加
2. ログ出力を標準出力だけでなく、logs/app.log に保存するように変更
3. SlackのURLやAPIキーは、.env ファイルから読み込むように修正
```

このように、**「0から1を作るのはClaude Code、1から10にするのはCursor」**という使い分けが、最もストレスが少ないです。

### 完成した実用コードの例

```python
import os
import httpx
import logging
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHeader("logs/app.log"),
        logging.StreamHandler()
    ]
)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_news():
    url = "https://techcrunch.com/"
    response = httpx.get(url)
    response.raise_for_status()
    # スクレイピングロジック（実際にはAIが詳細に記述）
    return BeautifulSoup(response.text, 'html.parser').find_all('h2', limit=5)

def main():
    try:
        articles = fetch_news()
        logging.info(f"{len(articles)}件の記事を取得しました。")
        # 要約と送信のロジックが続く...
    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeがファイルを作らない | 権限不足またはディレクトリロック | 管理者権限で実行するか、別のディレクトリで試す |
| API Rate Limit Exceeded | 短時間に大量の指示を送った | `claude config set --global max-tokens-per-period` 等で制限を確認するか時間を置く |
| Cursorの索引が古い | ファイル変更が反映されていない | `Ctrl + Shift + J`から「Resync Index」を実行する |

## 次のステップ

この記事で構築した環境は、AIコーディングの「入り口」に過ぎません。次に挑戦すべきは、**「GitHub Actionsとの連携」**です。

Claude Codeに「このプロジェクトをGitHub Actionsで毎日AM9時に実行するワークフローを作って」と頼んでみてください。AIがYAMLファイルを生成し、リポジトリのSecrets設定手順まで教えてくれます。

さらに、RTX 4090を積んでいるような私と同類の方なら、CursorのモデルをローカルLLM（Llama 3など）に切り替えて、プライベートなコードの流出を防ぎつつ開発する構成にも挑戦してほしいところです。AIに「書かせる」のではなく、AIと「並走する」感覚を掴めれば、あなたのエンジニアとしての市場価値は飛躍的に高まります。

## よくある質問

### Q1: Claude Codeを使うとAPI料金が跳ね上がりませんか？

その通りです。Claude Codeはコンテキスト全体を頻繁に読み取るため、大規模なプロジェクトでは1時間で数ドル消費することもあります。こまめに`/compact`コマンド（コンテキストの要約）を使い、不要なファイルは`.claudeignore`で除外するのがコツです。

### Q2: WindowsでWSLを使わないとダメですか？

現状、Claude Codeの持つシェル操作能力をフルに活かすにはWSLが必須です。PowerShellでも動きますが、AIが生成するシェルスクリプトの多くがUNIX系を想定しているため、コマンドエラーで詰まる可能性が高くなります。

### Q3: CursorのCopilot機能とClaude Codeは競合しませんか？

競合しません。CursorのCopilot（自動補完）は「今書いている行」の補完に集中し、Claude Codeは「プロジェクト全体の構造変更」に集中します。車で例えるなら、Cursorはハンドル操作の支援、Claude Codeはナビゲーションと自動運転の役割です。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用して開発効率を最大化する使い方](/posts/2026-07-24-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うとAPI料金が跳ね上がりませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "その通りです。Claude Codeはコンテキスト全体を頻繁に読み取るため、大規模なプロジェクトでは1時間で数ドル消費することもあります。こまめに/compactコマンド（コンテキストの要約）を使い、不要なファイルは.claudeignoreで除外するのがコツです。"
      }
    },
    {
      "@type": "Question",
      "name": "WindowsでWSLを使わないとダメですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "現状、Claude Codeの持つシェル操作能力をフルに活かすにはWSLが必須です。PowerShellでも動きますが、AIが生成するシェルスクリプトの多くがUNIX系を想定しているため、コマンドエラーで詰まる可能性が高くなります。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのCopilot機能とClaude Codeは競合しませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "競合しません。CursorのCopilot（自動補完）は「今書いている行」の補完に集中し、Claude Codeは「プロジェクト全体の構造変更」に集中します。車で例えるなら、Cursorはハンドル操作の支援、Claude Codeはナビゲーションと自動運転の役割です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

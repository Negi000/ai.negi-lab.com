---
title: "Claude CodeとCursorを併用したAIコーディング環境構築と実践ガイド"
date: 2026-11-17T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-11-17-claude-code-cursor-ai-coding-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "Python 自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude CodeとCursorを併用し、OpenWeatherMap APIから取得した気象データを元に、雨が降りそうな場合のみSlackへ通知を送る「自律型AI作成Pythonツール」を構築します。

- Claude Codeがターミナル上でライブラリのインストールからデバッグまでを自律的に行います。
- Cursorがコードの全体構造を視覚化し、ロジックの微調整を担当します。
- Pythonの基礎（pipや仮想環境）を理解している方を対象としています。

## 先に確認するスペック・料金

AIコーディング環境を本気で整えるなら、ツールのサブスク代とAPI使用料を「投資」と割り切る必要があります。

まず、CursorのProプラン（月額$20）は必須です。無料枠でも動きますが、今回のClaude Codeとの併用において、Cursorの「Composer」機能で全体を見渡しつつ、Claude Codeで実行させるスタイルをとるなら、制限のないProプランがストレスありません。

次にClaude Codeですが、これはAnthropicのAPIを使用します。Claude 3.5 Sonnetをバックエンドで動かすため、プロジェクトの規模によりますが、1時間集中して開発すると$1〜$5程度のAPI費用が発生します。月額固定ではなく従量課金なので、使いすぎを恐れるならAnthropicのコンソールで「Usage limits」を設定しておきましょう。

ハードウェアについては、MacBook Pro（M2/M3以上）であればメモリ16GB以上を推奨します。私はRTX 4090を2枚挿した自作機でローカルLLMを動かしていますが、Claude Codeのようなクラウドベースのツールを使う際も、IDEとブラウザ、ターミナルを同時に立ち上げるため、メモリの余裕は開発体験に直結します。

## なぜこの方法を選ぶのか

現在、AIコーディングツールはCursor、Aider、Cline、GitHub Copilotなど群雄割拠の状態です。その中で「Claude CodeとCursorの併用」がベストだと断言する理由は、エージェントの「実行力」とIDEの「視認性」の補完関係にあります。

Cursorはファイル全体の書き換えや、チャット形式でのコード生成において現時点で最高峰のUIを持っています。しかし、作成したコードを実行し、エラーが出たらそのログを読み取り、依存ライブラリをインストールして……といった「ターミナル作業の自律化」においては、Anthropic公式のClaude Codeに軍配が上がります。

Claude Codeはターミナル自体をLLMが支配する設計です。エンジニアが手動で`python script.py`と叩いてエラーをコピペする手間がありません。「エディタはCursor、コマンド実行と自律デバッグはClaude Code」という役割分担をすることで、開発速度は体感で3倍以上になります。

## Step 1: 環境を整える

まずはClaude Codeを動かすためのNode.js環境と、本体のインストールを行います。

```bash
# Node.jsがインストールされているか確認（v18以上必須）
node -v

# Claude Codeのインストール（Anthropic公式のCLIツール）
npm install -g @anthropic-ai/claude-code

# 正常にインストールされたか確認
claude --version
```

Node.jsはv18以上が必要です。もし古いバージョンを使っている場合は、`nvm`などで最新のLTSにアップデートしてください。Claude Codeは非常に強力な権限を持つため、グローバルにインストールしてどこからでも呼び出せるようにします。

次に、作業用ディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-weather-bot
cd ai-weather-bot
cursor .
```

⚠️ **落とし穴:**
Windows環境のWSL2を使っている場合、Claude Codeからのファイル書き込み権限で稀にエラーが出ます。必ずプロジェクトフォルダ内で`git init`を実行しておいてください。Claude CodeはGitの状態を監視して変更を管理するため、Gitがない環境ではその実力を発揮できません。

## Step 2: 基本の設定

Claude Codeを認証し、APIを使える状態にします。

```bash
# Claude Codeの認証を開始
claude auth login
```

ブラウザが立ち上がり、Anthropicアカウントでのログインを求められます。ログイン後、ターミナルに戻ると認証が完了しています。

次に、今回使用する環境変数を管理するための`.env`ファイルを作成します。Cursorで以下の内容を作成してください。

```text
OPENWEATHER_API_KEY=あなたのAPIキー
SLACK_WEBHOOK_URL=あなたのWebhookURL
```

APIキーを持っていない場合は、OpenWeatherMapの公式サイトで無料枠のキーを取得してください。SlackのWebhook URLも同様に、Incoming Webhooksアプリから取得しておきます。

なぜ環境変数を分けるのか。それはClaude Codeにコードを書かせる際、「APIキーを直書きしないで」と指示するよりも、最初から`.env`を使うルールを徹底させる方が、セキュリティ事故を防げるからです。

## Step 3: 動かしてみる

ここからがClaude Codeの本領発揮です。ターミナルで`claude`と入力して対話モードを起動します。

```bash
claude
```

起動したら、以下の指示をClaude Codeに投げてください。

「OpenWeatherMapから東京の天気を取得し、雨が降りそうならSlackに通知するPythonスクリプトを作ってください。依存ライブラリのインストールも自動で行い、最後にテスト実行まで完了させてください。」

### 期待される動作

Claude Codeは以下の手順を**勝手に**進めます。
1. `pip install requests python-dotenv` を実行する。
2. `weather_bot.py` を作成する。
3. `.env` からキーを読み込むコードを書く。
4. 実際にスクリプトを実行し、エラーが出ないか確認する。

この間、あなたはターミナルを眺めているだけで構いません。

```python
# Claude Codeが生成するコードのイメージ
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_weather():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    # ...（API呼び出しロジック）...
    if "rain" in weather_description:
        send_slack_notification("雨が降りそうです！")

if __name__ == "__main__":
    check_weather()
```

## Step 4: 実用レベルにする

単に動くだけでは不十分です。実務で使うなら「エラーハンドリング」と「定時実行」を考慮する必要があります。ここからはCursorの画面を見ながら、Claude Codeに修正を依頼しましょう。

Cursorで`weather_bot.py`を開いた状態で、Claude Codeにこう伝えます。

「APIがタイムアウトした時のリトライ処理を追加し、ログを `weather.log` に出力するように修正してください。また、現在のコードをCursorで見ているので、可読性を上げるために型ヒントを付けてください。」

Claude Codeはファイルのコンテキストを理解しているため、必要な部分だけを的確に修正します。

```python
# 実用的なコードへの進化例
import time
import logging
from typing import Optional

logging.basicConfig(filename='weather.log', level=logging.INFO)

def get_weather_data(city: str) -> Optional[dict]:
    for i in range(3):  # 3回までリトライ
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Attempt {i+1} failed: {e}")
            time.sleep(2)
    return None
```

このように、Cursorでコードの全体像（美しさ）を確認し、Claude Codeに「泥臭い修正（リトライ、ログ、環境構築）」を任せるのが、私が行き着いた最強の布陣です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | パスが通っていない | `npm install -g` 後にターミナルを再起動 |
| `Insufficient quota` | APIのクレジット不足 | AnthropicのDashboardでチャージする |
| `Permission denied` | ファイル書き込み権限 | `sudo`は使わず、フォルダの所有権を確認 |

## 次のステップ

ここまでで、「AIが自ら考え、ツールを構築し、実行まで行う」という流れを体験できました。

次のステップとしては、Claude Codeに「MCP（Model Context Protocol）」を導入することをお勧めします。MCPを使えば、Claude CodeにGoogle Driveの中身を読ませたり、GitHubのIssueを自動で作成させたりすることが可能になります。

具体的には、今回作った天気通知ツールを「GitHub Actionsで毎日朝8時に実行するためのワークフロー設定ファイル」もClaude Codeに作らせてみてください。デプロイ設定までAIに任せることで、あなたは「何を作りたいか」という上流工程の設計に集中できるようになります。

## よくある質問

### Q1: CursorのComposer機能だけで十分ではないですか？

CursorのComposerも優秀ですが、ターミナルの「実行結果」を受けて自律的に修正を繰り返すループの安定性は、Claude Codeの方が一段上です。Cursorは「書く」ことに強く、Claude Codeは「動かす」ことに強いという特性があります。

### Q2: API代がいくらかかるか不安です。

最初はAnthropicの「Tier 1」制限にかかるかもしれませんが、まずは$10程度をチャージして試すのが無難です。1回のプロンプトでトークンを消費しますが、手動で数時間悩むコストを考えれば格安と言えます。

### Q3: Python以外の言語でも使えますか？

もちろんです。TypeScriptやRust、Goなど、CLIでコンパイルや実行ができる言語であれば、Claude Codeの恩恵を最大限に受けられます。特に依存関係の解決が複雑な言語ほど、その真価を発揮します。

---

### 【重要】メタデータ出力

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS) **
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude CodeとCursorを同時並行で動かし、ブラウザを多用する開発環境にはメモリ容量が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252064GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2064GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを使い分ける最強のAIコーディング環境構築ガイド](/posts/2026-08-24-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-08-06-claude-code-cursor-ai-coding-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposer機能だけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposerも優秀ですが、ターミナルの「実行結果」を受けて自律的に修正を繰り返すループの安定性は、Claude Codeの方が一段上です。Cursorは「書く」ことに強く、Claude Codeは「動かす」ことに強いという特性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "API代がいくらかかるか不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最初はAnthropicの「Tier 1」制限にかかるかもしれませんが、まずは$10程度をチャージして試すのが無難です。1回のプロンプトでトークンを消費しますが、手動で数時間悩むコストを考えれば格安と言えます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScriptやRust、Goなど、CLIでコンパイルや実行ができる言語であれば、Claude Codeの恩恵を最大限に受けられます。特に依存関係の解決が複雑な言語ほど、その真価を発揮します。 ---"
      }
    }
  ]
}
</script>

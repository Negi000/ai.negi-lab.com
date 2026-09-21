---
title: "Claude CodeとCursorを併用してAPI連携ツールを爆速で開発する方法"
date: 2026-09-21T00:00:00+09:00
slug: "claude-code-cursor-ai-workflow-guide"
cover:
  image: "/images/posts/2026-09-21-claude-code-cursor-ai-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用 開発"
  - "AIエージェント コーディング"
  - "Python API連携 自動化"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事では、Cursorでプロジェクトの全体構造を設計し、Claude Codeに複雑なロジック実装を任せる手法で「OpenWeatherMap APIと連携して、特定の天候時にSlackへ通知を送るPythonスクリプト」を完成させます。

- Cursorを「プロジェクトの司令塔」として使用
- Claude Codeを「自律的な実装職人」として使用
- Python 3.10以上を使用し、環境変数管理まで含めた実務レベルのコードを作成

## 先に確認するスペック・料金

この環境を構築する前に、避けて通れないのがコストとスペックの話です。
まず、Cursor Pro（月額$20）は必須だと考えてください。
無料枠でも動きますが、Claude 3.5 Sonnetを制限なく（あるいは高枠で）使えないと、開発のリズムが途切れてストレスが溜まるだけです。

次にAnthropicのAPI料金です。
Claude CodeはCLI上で直接APIを叩くため、Cursorのサブスクとは別に「従量課金」のデポジットが必要です。
目安として、今回のスクリプトを1つ完成させるのに$0.5〜$2程度は消費します。
「高い」と感じるかもしれませんが、5年目のエンジニアの時給を考えれば、30分で完成する対価としては破格の安さです。

ハードウェアについては、MacBook（M1以降）またはRTX 3060以上のGPUを積んだWindows機を推奨します。
AIコーディング自体はクラウドで行われますが、Cursorのインデックス作成やローカルでのLinter実行において、メモリ16GB以下だと挙動がもたつきます。
私はRTX 4090を2枚挿した自作サーバーでローカルLLMも併用していますが、APIベースの開発でもPCの基礎体力は作業効率に直結します。

## なぜこの方法を選ぶのか

巷には「Cursorだけで十分」「Claude Codeだけで完結する」という声もありますが、実務経験から言えば「併用」がベストです。
Cursorは、GUIでプロジェクト全体のファイル構造を眺めたり、チャットでUIの微調整を指示したりする「静的な俯瞰」に優れています。

一方で、2025年に登場したClaude Codeは、ターミナルから直接コマンドを実行し、テストが通るまで自律的にデバッグを繰り返す「動的な完遂能力」が圧倒的です。
Cursorで「何を作るか」の骨子を決め、Claude Codeに「動く状態にするまで」の泥臭い作業を丸投げする。
この役割分担により、人間がコードを1行も書かずに、かつ品質を落とさずにツールを完成させられるようになります。

## Step 1: 環境を整える

まずはClaude Codeをインストールし、Cursorと共存できる状態にします。

```bash
# Claude Codeのインストール（Node.js 18以上が必要）
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version

# Anthropic APIとの連携（ブラウザが開くのでログインして認証）
claude auth
```

Claude CodeはNode.js環境で動作するため、入っていない場合は公式からLTS版を入れてください。
Python環境は、仮想環境（venv）を使うのが鉄則です。
グローバル環境を汚すと、後で別のプロジェクトを作るときにライブラリの競合で地獄を見ることになります。

```bash
# プロジェクトディレクトリの作成
mkdir ai-weather-notifier
cd ai-weather-notifier

# Python仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate
```

⚠️ **落とし穴:**
Claude Codeをインストールする際、パーミッションエラーが出る場合があります。
その場合は `sudo npm install -g ...` を試したくなりますが、Node.jsのバージョン管理ツール（nvmなど）を使っている場合は、sudoを使わずにパスを通す設定を確認してください。
sudoで入れると、後でClaude Codeがファイルを書き換える際に権限の問題で止まることがあります。

## Step 2: 基本の設定

ここでCursorを起動し、プロジェクトの「種」を植えます。
`code .` コマンドでCursorを開き、まずは環境変数を管理するための `.env` ファイルと、依存ライブラリを記す `requirements.txt` を作らせます。

Cursorのチャット（Cmd+K または Ctrl+K）を開き、以下の指示を出してください。

「OpenWeatherMap APIとSlack Webhookを使って、雨が降りそうな時に通知するツールを作ります。まずは .env.example と requirements.txt を作成して。必要なライブラリは requests と python-dotenv です。」

```python
# requirements.txt
requests==2.31.0
python-dotenv==1.0.0
```

作成された `.env.example` をコピーして `.env` を作り、自分のAPIキーを書き込みます。

```bash
cp .env.example .env
```

APIキーを持っていない場合は、OpenWeatherMapの公式サイトでフリートライアルを有効にしてください。
Slackは「Incoming Webhooks」を設定して、通知先のURLを取得しておきます。

なぜ最初からコードを書かせないのか。
それは、AIに「環境変数を使う」というルールを最初に叩き込まないと、ソースコードに直接APIキーを書き込む（ハードコーディング）という、セキュリティ上の大失敗を犯す可能性があるからです。

## Step 3: 動かしてみる

ここからがClaude Codeの真骨頂です。
ターミナルで `claude` と打ち込み、Claude Codeのエージェントモードを起動します。

```bash
claude
```

起動したら、以下のプロンプトを投げてください。

「カレントディレクトリの .env を読み込んで、現在の東京の天気を取得し、雨ならSlackに通知する main.py を作成して。作成後、実際に `python main.py` を実行して動作確認まで行って。エラーが出たら修正して。」

### 期待される出力

Claude Codeが自律的に思考を開始します。
1. `main.py` のコード案を作成
2. ファイルを保存
3. 実行コマンドを生成
4. 実行結果を確認（雨が降っていなければ「通知スキップ」というログが出るはず）

```text
Thinking...
I will create main.py with weather check and Slack notification logic.
[File Created: main.py]
Running command: python main.py
Output: 2025-05-20 10:00:00 - INFO - Weather is Clear. No notification sent.
```

Claude Codeの凄いところは、実行してエラーが出た場合、人間が指示しなくても「あ、ライブラリが足りなかった」「環境変数の読み込みに失敗した」と自分で判断して修正コードを書き直す点です。
私はこの挙動を初めて見た時、SIer時代のデバッグ作業がすべて過去のものになったと確信しました。

## Step 4: 実用レベルにする

単発で動くだけでは「仕事で使える」とは言えません。
実務では「エラー時にログを残す」「定期的に実行する」「通知内容をリッチにする」といった要素が必要です。

Claude Codeに対し、さらに具体的なリファクタリングを命じます。

「main.py を実用レベルに強化して。具体的には、
1. ログを weather.log ファイルに保存するようにする
2. 5分おきに天気をチェックするループ処理を追加（ただしAPI制限を考慮して待機を入れる）
3. Slack通知には現在の気温と湿度も含める
4. 例外処理（APIダウン等）を徹底する
これらを反映してコードを更新して。」

```python
import os
import time
import logging
import requests
from dotenv import load_dotenv

# ログの設定: ファイルとコンソールの両方に出力
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("weather.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
CITY_NAME = "Tokyo"

def check_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather_main = data["weather"][0]["main"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        logging.info(f"Current weather: {weather_main}, Temp: {temp}C")

        # 雨、雷、雪の場合に通知
        if weather_main in ["Rain", "Thunderstorm", "Snow"]:
            send_slack_notification(weather_main, temp, humidity)

    except Exception as e:
        logging.error(f"Error fetching weather: {e}")

def send_slack_notification(condition, temp, humidity):
    payload = {
        "text": f"⚠️ 天気警告: {CITY_NAME}で{condition}が検出されました。\n気温: {temp}℃ / 湿度: {humidity}%"
    }
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        logging.info("Slack notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send Slack notification: {e}")

if __name__ == "__main__":
    logging.info("Starting Weather Monitor...")
    while True:
        check_weather()
        time.sleep(300)  # 5分待機
```

このコードを反映させた後、Cursorの画面に戻って全体を確認してください。
Claude Codeが書いたコードに対し、Cursorの「Composer」機能を使って、「この関数の型定義を追加して」といった細かい修正を加えるのが、現代における最高峰のワークフローです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | npmのパスが通っていない | `npm bin -g` でパスを確認し、PATH環境変数に追加する |
| `401 Unauthorized (API)` | OpenWeatherMapのキーが有効化されていない | キー作成後、有効化まで最大数時間かかる場合があるので待つ |
| `Token limit exceeded` | Claude Codeが大量のファイルを読み込みすぎた | `.gitignore` に不要なフォルダ（venv, node_modules）を正しく記述する |

## 次のステップ

ここまでで、「Cursorで設計し、Claude Codeで実装・検証する」という流れを掴めたはずです。
この構成をマスターしたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
Claude CodeはMCPサーバーと連携することで、Googleカレンダーの予定を読み取ったり、ローカルのデータベースを直接操作したりすることが可能になります。

例えば、「今日の予定に『外出』があれば、1時間前に天気をチェックして雨なら傘を持つようSlackに通知する」といった、より高度なエージェントの構築も、今のあなたなら数時間の試行錯誤で作れるでしょう。
AIは「動かしてみる」のが最大の学習です。
まずは今回作ったスクリプトを、自分の好きなサービス（LINE通知やDiscordなど）にカスタマイズすることから始めてみてください。

## よくある質問

### Q1: CursorのComposer機能だけで十分ではないですか？

CursorのComposerも非常に強力ですが、ターミナルの実行結果を100%正確に把握し、自律的にコマンドを打ち直す能力はClaude Codeの方が一歩先を行っています。特に「ライブラリのインストールからテスト実行まで」を丸投げできる安心感はClaude Code固有のものです。

### Q2: Claude CodeでAPI料金を使いすぎてしまわないか心配です。

Claude Codeには、1回のセッションでの予算制限を設定するオプションがあります。また、大規模なファイルを読み込ませないよう `.claudeignore` を設定することで、トークンの消費を劇的に抑えることができます。私は常に、重要なファイルだけをコンテキストに含めるようにしています。

### Q3: Python以外の言語でも同じワークフローが使えますか？

もちろんです。TypeScriptやRust、Goなど、CLIツールが充実している言語ほどClaude Codeの恩恵を強く受けられます。コンパイルエラーをClaude Codeに読み取らせ、その場で修正させるサイクルは、言語を問わず開発スピードを3倍以上に引き上げてくれます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIコーディング中の複数ツール起動やインデックス作成でも動作が安定する</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを使い分け爆速でWebAPIを開発する方法](/posts/2026-09-03-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-08-19-claude-code-cursor-ai-coding-tutorial/)

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
        "text": "CursorのComposerも非常に強力ですが、ターミナルの実行結果を100%正確に把握し、自律的にコマンドを打ち直す能力はClaude Codeの方が一歩先を行っています。特に「ライブラリのインストールからテスト実行まで」を丸投げできる安心感はClaude Code固有のものです。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude CodeでAPI料金を使いすぎてしまわないか心配です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeには、1回のセッションでの予算制限を設定するオプションがあります。また、大規模なファイルを読み込ませないよう .claudeignore を設定することで、トークンの消費を劇的に抑えることができます。私は常に、重要なファイルだけをコンテキストに含めるようにしています。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じワークフローが使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScriptやRust、Goなど、CLIツールが充実している言語ほどClaude Codeの恩恵を強く受けられます。コンパイルエラーをClaude Codeに読み取らせ、その場で修正させるサイクルは、言語を問わず開発スピードを3倍以上に引き上げてくれます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIコーディング中の複数ツール起動やインデックス作成でも動作が安定する</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

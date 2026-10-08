---
title: "Claude CodeとCursorの併用入門：爆速でAPI連携アプリを開発する最強環境の構築"
date: 2026-10-09T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-guide"
cover:
  image: "/images/posts/2026-10-09-claude-code-cursor-ai-coding-guide.jpg"
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
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

OpenWeatherMap APIと連携して、指定した都市の気温を取得し、設定温度を超えたらデスクトップ通知を飛ばすPythonツールを作成します。
Cursorで全体のコード構造を見渡しながら、Claude Codeにコマンド実行やテスト、デバッグを「丸投げ」するワークフローを構築します。
Pythonの基本的な構文が分かり、ターミナルでコマンドを叩くことに抵抗がない方を対象としています。

## 先に確認するスペック・料金

AIコーディング環境を整える前に、財布とマシンスペックの確認が必要です。
まず、Claude Codeを利用するには、Anthropicコンソールの「APIクレジット」への事前チャージが必要です。
月額プランのClaude Pro（$20/月）とは別枠で、最低$5からの従量課金制となるため注意してください。

次にエディタですが、Cursor Pro（$20/月）の使用を強く推奨します。
無料枠でも動かせますが、Claude 3.5 Sonnetを無制限に近い感覚で叩けないと、思考の速度がAIに追いつかれ、併用のメリットが半減します。
マシンはMacBook（M1以降）か、WSL2が動くWindows機が必要です。
特にClaude Codeはファイルシステムやターミナルを直接操作するため、安定したUNIXライクな環境が望ましいです。
## なぜこの方法を選ぶのか

現在、Cursor単体でも十分強力ですが、唯一の弱点は「ターミナルとの分断」です。
CursorのComposer（Ctrl+I）はコードは書けますが、ライブラリのインストールや、テスト実行後のエラーログを読み取って修正するループは、依然として人間の指示を必要とします。

ここでClaude Codeを導入します。
Claude CodeはAnthropic公式のCLIエージェントであり、自分自身で `pip install` を実行し、`pytest` を回し、エラーが出たら勝手にコードを直すという「自律的な自浄作用」を持っています。
Cursorを「設計図を書くための司令塔」、Claude Codeを「泥臭い実装とデバッグをこなす現場監督」として分担させるのが、2024年末時点での最適解です。

## Step 1: 環境を整える

まずはClaude Codeをシステムにインストールします。
Node.jsのバージョン18以上が必要なので、入っていない場合は公式から入れておいてください。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが立ち上がります）
claude login

# プロジェクト用ディレクトリの作成
mkdir ai-weather-notifier
cd ai-weather-notifier
touch main.py .env
```

`claude login`を実行すると、Anthropicのコンソール画面に飛びます。
APIキーを直接コピペするのではなく、OAuth形式で認証されるため、キーを紛失するリスクが低いのが良い点です。
ここで「クレジットが足りない」と出た場合は、最低$5をチャージしてください。

⚠️ **落とし穴:**
WindowsのPowerShellで実行すると、実行ポリシーの関係でスクリプトがブロックされることがあります。
その場合はWSL2（Ubuntu等）を使うか、管理者権限のターミナルで `Set-ExecutionPolicy RemoteSigned` を試してください。
また、Node.jsのバージョンが古いとインストール時に謎のエラーで止まるため、必ず `node -v` で18以上であることを確認しましょう。

## Step 2: 基本の設定

次に、Cursorでこのフォルダを開き、Claude Codeが自律的に動けるように環境変数を設定します。
直接コードにAPIキーを書くとGitHub等に流出した際に悲惨なことになるので、`.env`での管理を徹底します。

```python
# .env ファイルの中身
OPENWEATHER_API_KEY=your_api_key_here
THRESHOLD_TEMP=25.0
CITY_NAME=Tokyo
```

OpenWeatherMapのAPIキーは公式サイトから無料で取得できます。
次に、Claude Codeをプロジェクトルートで起動します。

```bash
claude
```

起動したら、まず最初に以下の指示をClaude Codeに投げてください。
「このプロジェクトの目的は、指定した都市の気温を監視して通知することです。Pythonの仮想環境を作成し、必要なライブラリをリストアップしてインストールしてください」

これにより、Claude Codeが勝手に `python -m venv .venv` を実行し、`requests` や `python-dotenv` などのライブラリを特定してインストールを始めます。
人間が `requirements.txt` を書く必要はありません。

## Step 3: 動かしてみる

環境が整ったら、いよいよメインの実装です。
ここでCursorの画面を横に並べておいてください。
Claude Codeに以下のプロンプトを投げます。

「`.env`から設定を読み込み、OpenWeatherMapから現在の気温を取得する `main.py` を作成してください。取得に成功したら気温を表示し、もし `THRESHOLD_TEMP` を超えていたらコンソールに警告を出してください。まずは動作確認用のシンプルなコードでお願いします」

```python
# Claude Codeが生成するであろうコードの例
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    city = os.getenv("CITY_NAME")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        print(f"現在の{city}の気温は {temp}°C です。")

        threshold = float(os.getenv("THRESHOLD_TEMP", 25.0))
        if temp > threshold:
            print("【警告】設定温度を超えました！暑いです。")
    else:
        print(f"エラーが発生しました: {response.status_code}")

if __name__ == "__main__":
    get_weather()
```

### 期待される出力

```
現在のTokyoの気温は 28.5°C です。
【警告】設定温度を超えました！暑いです。
```

Claude Codeはコードを書くだけでなく、`python main.py` を実行して結果まで見せてくれます。
もしAPIキーが間違っていたり、ライブラリが足りなかったりすれば、そのログを見て勝手に修正案を出してきます。
私たちはただ「y（Yes）」を押して実行を許可するだけです。

## Step 4: 実用レベルにする

単発の実行では面白くないので、これを「1時間ごとに実行し、デスクトップ通知を飛ばし、かつエラーハンドリングが完璧な状態」まで昇華させます。
ここからがClaude Codeの真骨頂です。

Claude Codeにこう指示してください。
「このコードをリファクタリングして、以下の機能を追加してください。
1. `schedule` ライブラリを使って1時間ごとに実行する。
2. デスクトップ通知には `plyer` ライブラリを使う。
3. ネットワークエラーが発生してもプログラムが終了しないように、リトライ処理を入れる。
4. 最後に `pytest` で `get_weather` 関数のモックテストを作成し、テストが通るまで修正してください」

```python
# 実用的なコードの一部（Claude Codeによるリファクタリング後）
import time
import schedule
from plyer import notification
# ...（その他のインポート）

def send_notification(temp):
    notification.notify(
        title="高温注意",
        message=f"現在の気温が{temp}°Cに達しました。",
        timeout=10
    )

def job():
    try:
        temp = get_weather()
        if temp > float(os.getenv("THRESHOLD_TEMP")):
            send_notification(temp)
    except Exception as e:
        print(f"予期せぬエラー: {e}")

schedule.every(1).hours.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
```

この指示を出すと、Claude Codeは自ら `pip install schedule plyer pytest` を実行し、コードを書き換え、さらに `tests/test_main.py` を作成してテストを実行します。
テストが失敗すれば、エラー内容を読んで `main.py` を修正し、再度テストを回します。
Cursorの画面上では、ファイルが次々と書き換わっていく様子がリアルタイムで見えるはずです。
人間は「現場監督がサボっていないか」をCursorの画面で眺めているだけで、動く成果物が完成します。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Permission denied` | Claude Codeがファイル操作権限を持っていない | `claude` 起動時に権限昇格のプロンプトが出るので許可する。または `--dangerously-skip-permissions` フラグを使う。 |
| `API Key Invalid` | `.env` の読み込み失敗 | `os.getenv` で取得できているか、Claude Codeにデバッグプリントを挟ませて確認する。 |
| トークン消費が激しい | 指示が曖昧でループしている | 一度 `exit` で終了し、再度具体的なゴールを指定して起動し直す。 |

## 次のステップ

この記事の内容で、AIエージェントに「実装・テスト・修正」を丸投げする感覚が掴めたはずです。
次に挑戦すべきは、このツールをローカル環境ではなく、Dockerコンテナ化して自宅サーバーやクラウドで常時稼働させることです。

Claude Codeに対して「このアプリをDocker化するためのDockerfileとdocker-compose.ymlを作成し、ビルドが通るか確認して」と指示してみてください。
これまで数時間かかっていた「デプロイ準備」が、わずか数分で終わる衝撃を味わえるでしょう。
また、大規模なリファクタリングが必要な場合は、Cursorの「Codebase Indexing」機能を使って全体の構造をAIに把握させ、その知見をClaude Codeへの指示に反映させるという連携も強力です。
AIは「道具」ではなく「同僚」として扱うフェーズに入っています。

## よくある質問

### Q1: Claude CodeとCursorのComposer、どっちでコードを書くべきですか？

設計の相談や、複雑なロジックをじっくり考える時はCursorのComposerが向いています。一方で、ライブラリのインストールを伴う機能追加や、テストを回しながらのバグ修正、シェルスクリプトの作成などは、ターミナルを直接操作できるClaude Codeの方が圧倒的に速いです。

### Q2: Claude CodeのAPI消費を抑えるコツはありますか？

プロジェクトに関係のない巨大なログファイルやバイナリデータがディレクトリにあると、Claude Codeがそれを読み取ろうとしてトークンを無駄遣いします。`.gitignore` を適切に設定するか、重要なファイルだけを指定して `claude` を起動するようにしてください。

### Q3: 会社のプロキシ環境下でも動きますか？

Node.jsのHTTPSプロキシ設定（`HTTPS_PROXY`環境変数）を正しく行っていれば動くことが多いですが、Claude Codeは外部のAnthropicサーバーと頻繁に通信するため、セキュリティポリシーによっては遮断される可能性があります。まずは個人のテザリング環境などで動作確認をすることをお勧めします。

---

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIを複数立ち上げながらのビルドでもメモリ不足に陥らない最低ライン</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAI開発環境作り](/posts/2026-10-02-claude-code-cursor-ai-coding-setup/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude CodeとCursorのComposer、どっちでコードを書くべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "設計の相談や、複雑なロジックをじっくり考える時はCursorのComposerが向いています。一方で、ライブラリのインストールを伴う機能追加や、テストを回しながらのバグ修正、シェルスクリプトの作成などは、ターミナルを直接操作できるClaude Codeの方が圧倒的に速いです。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude CodeのAPI消費を抑えるコツはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "プロジェクトに関係のない巨大なログファイルやバイナリデータがディレクトリにあると、Claude Codeがそれを読み取ろうとしてトークンを無駄遣いします。.gitignore を適切に設定するか、重要なファイルだけを指定して claude を起動するようにしてください。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロキシ環境下でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Node.jsのHTTPSプロキシ設定（HTTPSPROXY環境変数）を正しく行っていれば動くことが多いですが、Claude Codeは外部のAnthropicサーバーと頻繁に通信するため、セキュリティポリシーによっては遮断される可能性があります。まずは個人のテザリング環境などで動作確認をすることをお勧めします。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIを複数立ち上げながらのビルドでもメモリ不足に陥らない最低ライン</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

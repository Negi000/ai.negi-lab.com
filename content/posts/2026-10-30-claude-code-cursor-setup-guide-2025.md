---
title: "Claude CodeとCursorを併用した最強AIコーディング環境構築ガイド"
date: 2026-10-30T00:00:00+09:00
slug: "claude-code-cursor-setup-guide-2025"
cover:
  image: "/images/posts/2026-10-30-claude-code-cursor-setup-guide-2025.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング"
  - "Anthropic API"
  - "自律型AIエージェント"
---
**所要時間:** 約45分 | **難易度:** ★★★☆☆

## この記事で作るもの

「外部API（OpenWeatherMap）から情報を取得し、Slackへ通知するPythonスクリプト」を、Claude CodeとCursorを組み合わせて開発します。
単にコードを書くだけではなく、Claude Codeにテストを実行させ、エラーがあれば自律修正させ、Cursorで全体像をレビューする「AIエージェント併用型ワークフロー」を構築します。

前提知識：
- ターミナル（Terminal/iTerm2等）の基本的な操作ができる
- Pythonの基礎的な文法を知っている
- Anthropic APIキー、Slack APIキーを準備できる（取得手順も解説します）

## 先に確認するスペック・料金

AIコーディングを本気でやるなら、ハードウェアとAPI予算に投資してください。
この記事の内容を快適に動かすには、Apple Silicon（M1/M2/M3/M4）搭載のMacで、メモリは32GB以上を強く推奨します。
16GBでも動きますが、Cursorを立ち上げつつブラウザでドキュメントを開き、裏でClaude Codeを走らせるとスワップが発生して思考の速度が落ちるからです。

私は自宅でRTX 4090を2枚挿したサーバーを運用していますが、Claude CodeのようなAPIベースのツールを使う際は、マシンのGPU性能よりも「ネットワークの安定性」と「APIの利用上限（Tier）」が重要になります。
AnthropicのAPIは「Tier 2（累計$50以上の支払い）」以上になっていないと、レート制限（Rate Limit）でClaude Codeが途中で止まるストレスに晒されます。

また、料金についてですが、Claude Codeは1回の自律タスクで数十円〜数百円のAPI費用を平気で消費します。
便利だからと放置すると、1日で数千円飛ぶこともあるため、後述するコスト制限の設定は必須です。
「月額$20のサブスク」で済むCursorとは、課金の性質が根本から違う点に注意してください。

## なぜこの方法を選ぶのか

Cursorの「Composer」機能は非常に優秀ですが、あくまでエディタ上の編集に特化しています。
一方でAnthropicが公式に提供を開始した「Claude Code」は、ターミナルを支配下に置き、シェルコマンドを自由に実行できる「自律型エンジニア」です。

Cursorに「全体の設計とコードの微調整」を任せ、Claude Codeに「テストの実行、環境構築、エラーの自己解決」を任せるのが、現時点で最も開発速度が上がります。
Cursorだけでデバッグしようとすると、エラーが出るたびにログをコピペしてAIに渡す手間が発生しますが、Claude Codeなら勝手に`pytest`を叩いてエラーを読み取り、修正まで完結させます。
この「ターミナルとの密結合」こそが、私がCursor単体からこの併用スタイルへ移行した最大の理由です。

## Step 1: 環境を整える

まずはClaude Codeを動かすためのNode.js環境を用意します。
Claude CodeはNode.js v18以上が必要ですが、互換性の問題を避けるために最新のLTS（Long Term Support）バージョンを推奨します。

```bash
# Node.jsのバージョン確認
node -v

# 18未満の場合は nvm 等でインストール
# Claude Codeのインストール（グローバル）
npm install -g @anthropic-ai/claude-code

# 正常にインストールされたか確認
claude --version
```

`npm install -g`を使うのは、どのプロジェクトディレクトリからでも即座にClaudeを呼び出せるようにするためです。
もしパーミッションエラーが出る場合は、`sudo`をつけるのではなく、Node.jsの管理に`nvm`や`volta`を使うことを検討してください。

⚠️ **落とし穴:** Node.jsのバージョンが古いと、Claude Codeのインストール自体は成功しても、実行時に「AsyncLocalStorage...」といったエラーでクラッシュします。必ず`node -v`で18以上であることを確認してください。また、Python環境を汚さないために、プロジェクトごとに仮想環境（venv）を作成するのが鉄則です。

## Step 2: 基本の設定

Claude Codeを起動する前に、AnthropicのAPIキーを環境変数にセットします。
毎回入力するのは非効率なので、シェル（zshやbash）の設定ファイルに書き込みます。

```bash
# ~/.zshrc または ~/.bash_profile に追記
export ANTHROPIC_API_KEY='sk-ant-xxx...'

# 反映
source ~/.zshrc
```

次に、プロジェクトディレクトリを作成し、Claude Codeを初期化します。

```bash
mkdir ai-coding-test
cd ai-coding-test
# 仮想環境の作成
python -m venv .venv
source .venv/bin/activate

# Claude Codeの起動
claude
```

初回起動時に認証を求められます。指示に従ってブラウザでログインしてください。
起動したら、まずは`/config`コマンドを打って、コスト制限を設定しましょう。

```bash
# Claude Code内のプロンプトで
/config set max_tokens_per_session 50000
```

これは1セッションあたりの最大トークン数を制限する設定です。
「なぜこの値にするのか」というと、AIエージェントがループに陥った際、際限なくAPI費用を消費するのを防ぐためです。

## Step 3: 動かしてみる

ここでは、簡単な天気取得スクリプトを作成させます。
Cursorでこのディレクトリを開いた状態で、Claude Codeのターミナルにこう指示を出してください。

「OpenWeatherMapから東京の天気を取得し、結果を表示する`weather.py`を作成してください。`requests`ライブラリを使い、例外処理も入れてください。また、必要なライブラリを`requirements.txt`に書き出し、インストールまで完了させてください。」

### 期待される出力

```text
Thinking...
- Creating requirements.txt
- Running pip install -r requirements.txt
- Creating weather.py
Finished. I've created the script and installed the dependencies.
You can run it with `python weather.py`.
```

Claude Codeは、自らファイルを生成し、自ら`pip install`を実行します。
これがCursorのComposerとの決定的な違いです。

## Step 4: 実用レベルにする

次に、このスクリプトに「Slack通知機能」と「ユニットテスト」を追加し、自動でテストをパスさせます。
ここがClaude Codeの真骨頂です。

まず、Cursorで`weather.py`を開き、AIが書いたコードを確認してください。
おそらく、APIキーが直書きされているか、プレースホルダーになっているはずです。
それを`.env`ファイルから読み込むように指示します。

Claude Codeに以下のタスクを投げます。

```bash
# Claude Codeのプロンプト
SlackのWebHookURLを使って、天気の情報を通知する機能を追加して。
その後、pytestを使ってweather.pyのメインロジックをテストするtest_weather.pyを作成して。
最後に、テストを実行して、すべてパスするまでコードを修正して。
```

ここで使用する実用的なコードの雛形は以下のようになります。

```python
# weather.py (AIによって生成・修正されるコードのイメージ)
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather(city_name):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweather.com/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"

    response = requests.get(url)
    # 401エラー（キー不正）などのハンドリングを確実に行う
    response.raise_for_status()
    return response.json()

def send_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    payload = {"text": message}
    requests.post(webhook_url, json=payload)

if __name__ == "__main__":
    try:
        data = get_weather("Tokyo")
        msg = f"今日の東京の天気は {data['weather'][0]['description']} です。"
        send_slack(msg)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
```

Claude Codeは、`pytest`を実行し、「APIキーがないのでテストが落ちた」というログを見れば、「Mock（擬似データ）を使ってテストを書き直す」という判断まで自分で行います。
私たちがやることは、Cursorでその修正内容を眺め、「よし、いい筋だ」と承認（Enterキーを押す）するだけです。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Rate limit reached` | APIの支払い実績が少なくTierが低すぎる | $50以上チャージして数日待つか、使用間隔を空ける |
| `Command not found: claude` | パスが通っていない | `npm list -g`で場所を確認し、PATHを通す |
| `Permission denied` | ファイル書き込み権限がない | `claude`起動時に書き込み権限を確認、またはディレクトリの所有権を修正 |

## 次のステップ

Claude CodeとCursorの併用環境が整ったら、次は「既存の巨大なプロジェクトの解析」に挑戦してください。
`claude`をプロジェクトのルートで起動し、「このプロジェクトのディレクトリ構造を分析して、README.mdを最新の状態に更新して」と頼んでみてください。
Cursorがコードの「点」と「線」を直すツールなら、Claude Codeは「面」でプロジェクトを捉えるツールです。

また、GitHub Actionsのワークフロー作成や、Dockerfileの作成など、OSのコマンドが絡む作業を積極的にClaude Codeへ振ってみることをお勧めします。
これらはCursorよりもClaude Codeの方が圧倒的に得意な領域です。
「AIにコードを書かせる」段階から、「AIに開発プロセスを回させる」段階へシフトしましょう。

## よくある質問

### Q1: Cursorの有料プランに入っているのに、さらにClaudeのAPI代を払う価値はありますか？

あります。Cursorの月額$20は「自分と一緒に考えてくれる相棒」への投資、Claude CodeのAPI代は「自分の代わりに手を動かして、テストまで回してくれる外注エンジニア」への投資です。1時間のデバッグ作業が100円のAPI代で終わるなら、エンジニアの時給を考えれば安すぎます。

### Q2: Claude Codeが勝手にファイルを削除したりしませんか？

デフォルトでは、破壊的な変更を加える前に必ずユーザーの承認を求めてきます。`/config`で自動承認をオンにしない限り、勝手にコードが消えることはありません。CursorでGitの差分を常に表示しておけば、万が一の際もすぐにロールバックできます。

### Q3: Python以外の言語でも同じように使えますか？

もちろんです。TypeScriptやGo、Rustなど、CLIツールが充実している言語ほど、Claude Codeの恩恵を受けられます。例えばRustなら、Claude Codeに`cargo check`を回させながらコンパイルエラーを全自動で潰させるという、中毒性の高い開発体験が得られます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3 Max</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールを同時稼働させる開発環境には32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を最大化するAIコーディング環境構築ガイド](/posts/2026-07-04-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-10-19-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築と実践](/posts/2026-10-09-claude-code-cursor-ai-coding-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorの有料プランに入っているのに、さらにClaudeのAPI代を払う価値はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "あります。Cursorの月額$20は「自分と一緒に考えてくれる相棒」への投資、Claude CodeのAPI代は「自分の代わりに手を動かして、テストまで回してくれる外注エンジニア」への投資です。1時間のデバッグ作業が100円のAPI代で終わるなら、エンジニアの時給を考えれば安すぎます。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeが勝手にファイルを削除したりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "デフォルトでは、破壊的な変更を加える前に必ずユーザーの承認を求めてきます。/configで自動承認をオンにしない限り、勝手にコードが消えることはありません。CursorでGitの差分を常に表示しておけば、万が一の際もすぐにロールバックできます。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じように使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScriptやGo、Rustなど、CLIツールが充実している言語ほど、Claude Codeの恩恵を受けられます。例えばRustなら、Claude Codeにcargo checkを回させながらコンパイルエラーを全自動で潰させるという、中毒性の高い開発体験が得られます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3 Max</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">複数のAIツールを同時稼働させる開発環境には32GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%2520Max%252036GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%20Max%2036GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

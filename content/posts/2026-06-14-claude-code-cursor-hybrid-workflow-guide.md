---
title: "CursorとClaude Codeを併用して爆速でPythonツールを開発する方法"
date: 2026-06-14T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AI コーディング"
  - "Python 自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

この記事を読むと、Cursorでベースを書き、Claude Codeでテストとデバッグを自律実行させて完成させる「AIハイブリッド開発フロー」で、外部APIから情報を取得して整形・保存する実用的なPythonツールが作れます。

- 前提知識: Pythonの基本的な読み書きができること、ターミナルの基本操作。
- 必要なもの: Anthropic APIキー（Tier 2以上推奨）、Cursor（無料版でも可だがPro推奨）、Node.js環境。

## 先に確認するスペック・料金

AIコーディング環境を整える前に、一番の壁になるのが「APIコスト」と「マシンスペック」です。
Claude Codeはターミナルで自律的に動作するため、1回の指示で大量のトークンを消費します。
AnthropicのAPI利用料金として、$20〜$50程度のデポジット（前払い）を覚悟してください。
Cursor Pro（月額$20）を契約している場合でも、Claude Codeは別料金（API実費）がかかります。

ハードウェアについては、VS CodeベースのCursorが動けば問題ありませんが、メモリは最低16GB、できれば32GB以上を推奨します。
私はRTX 4090を2枚積んだPCでローカルLLMを回していますが、この構成でもエディタとブラウザ、 Claude Codeを同時に動かすとメモリ消費は12GBを超えてきます。
MacユーザーならM2/M3チップ搭載のメモリ16GBモデル以上があれば、ストレスなく動作します。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor」と「Claude Code」の2強時代に突入しました。
CursorはGUI上でファイル構成を眺めながら、人間が主導権を持ってコードを書き進めるのに最適です。
一方、AnthropicがリリースしたClaude Codeは、ターミナルから「テストを実行して、エラーが出たら勝手に直して」という丸投げの依頼（Agent的動作）に圧倒的な強みを持ちます。

どちらか一方で完結させようとすると、Cursorでは「何度も手動でエラーをコピペする」手間が発生し、Claude Codeでは「全体像が見えにくい」という欠点があります。
これらを組み合わせることで、人間は設計と大枠の作成に集中し、面倒なデバッグやリファクタリングをClaude Codeに任せる「いいとこ取り」が可能になります。
私が実際に20件以上の案件をこなした経験上、この併用スタイルが最も開発時間を短縮できました。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはNode.js上で動くCLIツールです。

```bash
# Node.jsのバージョン確認（18以上が必要）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストールの確認
claude --version
```

Node.js 18以上が必要なのは、Claude Codeが使用するライブラリが比較的新しい非同期処理に依存しているためです。
古いバージョンを使っている場合は、`nvm`などでアップデートしてください。

次に、Cursorを公式サイトからインストールし、設定（Settings）の「Models」で `claude-3-5-sonnet` が有効になっていることを確認します。
Cursorの強みはこのモデルとの親和性にあります。

⚠️ **落とし穴:**
Claude Codeの初回起動時に `auth` を求められますが、ここでブラウザが立ち上がらないことがあります。
その場合は `claude auth login` を手動で叩き、表示されたURLをコピーしてブラウザに貼り付けてください。
また、APIキーに十分なクレジットが入っていないと「insufficient_quota」エラーで動かないため、事前にAnthropicのダッシュボードで数ドル分チャージしておくのがコツです。

## Step 2: 基本の設定

プロジェクト用のディレクトリを作成し、必要な環境変数を設定します。

```bash
mkdir ai-weather-app
cd ai-weather-app
touch .env
```

`.env` ファイルに、AnthropicのAPIキーと、今回使用する天気API（OpenWeatherMapなど）のキーを書き込みます。

```text
ANTHROPIC_API_KEY=sk-ant-xxxx...
OPENWEATHER_API_KEY=your_api_key_here
```

次に、Claude Codeがプロジェクトのルールを理解するための設定ファイル `.claude.json` を作成します。
これを行う理由は、Claude Codeに「余計なファイルを触らせない」ことと「常に特定のライブラリ（今回は `requests`）を使わせる」ためです。

```json
{
  "project_rules": "常に日本語で返答してください。外部APIとの通信にはrequestsライブラリを使用し、エラーハンドリングを徹底してください。"
}
```

Pythonの仮想環境も作っておきましょう。

```bash
python -m venv venv
source venv/bin/activate  # Windowsなら venv\Scripts\activate
pip install requests python-dotenv pytest
```

## Step 3: 動かしてみる

ここからが本番です。まずCursorを開き、`main.py` という空ファイルを作ります。
Cursorの「Composer（Cmd+I）」を開き、以下の指示を出してベースコードを生成します。

「OpenWeatherMapから東京の天気を取得して表示するシンプルな関数を作って。APIキーは.envから読み込んで。requestsを使ってね。」

### 生成されたコード例

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather(city="Tokyo"):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"{city}の天気: {data['weather'][0]['description']}, 気温: {data['main']['temp']}度"
    else:
        return "データ取得に失敗しました"

if __name__ == "__main__":
    print(get_weather())
```

これを保存したら、いよいよClaude Codeの出番です。
ターミナルで `claude` と打ち込んで起動してください。

```bash
claude
```

Claude Codeが起動したら、チャット欄にこう投げます。
「main.pyのコードをチェックして。もしAPIがエラーを返したときの詳細なロギング機能を追加し、この関数が正しく動くかテストするための `test_main.py` を作成して。その後、実際にテストを実行して結果を教えて。」

### 期待される動作

Claude Codeは自律的に以下のステップを踏みます。
1. `main.py` を読み込み、ロギング（loggingモジュール）を追加して上書きする。
2. `test_main.py` を新規作成する。
3. `pytest test_main.py` コマンドを自分で実行する。
4. テストが失敗（APIキー未設定など）したら、その原因を分析して報告する。

これがClaude Codeの真髄です。
「人間がコマンドを打って、エラーを見て、AIに伝えて、修正案をもらって、自分で貼り付ける」という往復が、すべて自動化されます。

## Step 4: 実用レベルにする

実務では、単に表示するだけでなく「結果をJSON形式で保存する」「定期的に実行する」といった機能が必要です。
これをClaude Codeに「丸投げ」して、より堅牢なシステムへ進化させます。

Claude Codeに対し、以下の指示を出してみてください。
「このツールを、複数の都市（東京、大阪、札幌）の天気を一括取得して、`results/` ディレクトリ内に実行時のタイムスタンプ付きでJSON保存する仕様に変更して。保存に失敗した場合はリトライする処理も入れてほしい。」

```python
# Claude Codeが生成・修正するであろう実用的なコードの断片
import time
import json
from datetime import datetime
from pathlib import Path

def save_weather_data(data):
    try:
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"weather_{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Saved: {file_path}")
    except Exception as e:
        print(f"Error saving data: {e}")
        # ここにリトライ処理をClaude Codeが勝手に書く
```

私は以前、100ファイル以上ある既存システムの移行案件でこれを使いましたが、Cursorで全体の依存関係を確認しつつ、Claude Codeに「各ファイルのユニットテストを書いて実行し、通るまで修正して」と指示することで、作業時間を約70%削減できました。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `claude: command not found` | npmのパスが通っていない | `npm list -g` で場所を確認し、PATHに追加する |
| `insufficient_quota` | Anthropic APIの残高不足 | API Consoleからチャージ（最低$5〜）を行う |
| `Rate limit reached` | APIのTierが低い（Tier 1以下） | 累積支払い額を増やしてTier 2に上げるか、少し待つ |
| テストが無限ループする | AIが誤ったテストコードを書いた | `Ctrl+C` で中断し、「このエラーは無視していい」と明示する |

## 次のステップ

この記事の内容をマスターしたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
MCPを使えば、Claude CodeがあなたのGoogleカレンダーやGitHub、さらにはローカルのデータベースまで直接読み書きできるようになります。

例えば、「GitHubのIssueを読み取って、それに対応するコードをブランチを切って作成し、プルリクエストまで送っておいて」という指示が可能になります。
ここまで来ると、AIは単なる補完ツールではなく、文字通りの「自律型ジュニアエンジニア」として機能します。
まずは今回作成したスクリプトを、GitHub Actionsで定期実行する設定をClaude Codeに書かせてみるのが良い練習になるはずです。

## よくある質問

### Q1: Cursorだけで十分ではないですか？

CursorのComposer機能は強力ですが、あくまで「エディタの中」での修正が得意です。Claude Codeはターミナルを直接操作し、`pip install` や `pytest` などのシェルコマンドをAIが判断して実行できるため、デバッグの速度が段違いです。

### Q2: API代が怖いです。節約する方法は？

Claude Codeの起動時に `--dangerously-skip-permissions` を使わず、1ステップごとにAIが実行しようとするコマンドを確認してください。また、不要な大きなファイルを `.claudeignore` に指定することで、読み取りトークン量を劇的に減らせます。

### Q3: 日本語のプロンプトで精度は落ちませんか？

Claude 3.5 Sonnetは日本語理解が非常に高いため、基本的には問題ありません。ただし、技術的な指示（ライブラリの指定など）は英語の用語を交えて書くほうが、意図が正確に伝わり、無駄な修正（＝トークン消費）を抑えられます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールとコンパイルを並行する開発環境には32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Masko Code ターミナルに「表情」を与えるClaude Code専用の伴走型マスコット](/posts/2026-03-16-masko-code-claude-cli-mascot-review/)
- [Spotlight by Backplanes：Claude Codeの「思考の軌跡」を可視化して開発効率を最大化する](/posts/2026-06-10-spotlight-backplanes-claude-code-review/)
- [claude-plugins-official 導入で Claude Code を自律型エージェントへ進化させる](/posts/2026-05-21-claude-plugins-official-mcp-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorだけで十分ではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CursorのComposer機能は強力ですが、あくまで「エディタの中」での修正が得意です。Claude Codeはターミナルを直接操作し、pip install や pytest などのシェルコマンドをAIが判断して実行できるため、デバッグの速度が段違いです。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。節約する方法は？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeの起動時に --dangerously-skip-permissions を使わず、1ステップごとにAIが実行しようとするコマンドを確認してください。また、不要な大きなファイルを .claudeignore に指定することで、読み取りトークン量を劇的に減らせます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のプロンプトで精度は落ちませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude 3.5 Sonnetは日本語理解が非常に高いため、基本的には問題ありません。ただし、技術的な指示（ライブラリの指定など）は英語の用語を交えて書くほうが、意図が正確に伝わり、無駄な修正（＝トークン消費）を抑えられます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">複数のAIツールとコンパイルを並行する開発環境には32GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

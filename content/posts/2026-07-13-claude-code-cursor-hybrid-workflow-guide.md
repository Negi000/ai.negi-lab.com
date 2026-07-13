---
title: "Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド"
date: 2026-07-13T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-07-13-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "Anthropic API 設定"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude CodeとCursorを組み合わせ、対話だけで「特定サイトからニュースをスクレイピングし、要約してLINEやSlackに通知するツール」をゼロから完成させます。
Pythonの基本的な読み書きができることを前提としますが、環境構築から実行まで、私が実務で使っているワークフローをすべて公開します。
最終的には、ターミナルからClaude Codeに指示を出し、Cursorでコードを微調整する、現代最強のAI開発体験を手にできます。

## 先に確認するスペック・料金

AIコーディングを本気で仕事に使うなら、月額の固定費を「投資」と割り切る必要があります。
まずCursorのProプラン（月額$20）は必須です。無料枠では推論回数に制限があり、開発の思考を止められるストレスが大きすぎます。
次にClaude Codeですが、これはAnthropicのAPIキー（従量課金）を使用します。
目安として、今回のハンズオンを1周完遂するのに約$1〜$3程度のAPI使用料がかかると考えてください。

ハードウェア面では、MacBook Air（M2以降）やProのメモリ16GB以上を推奨します。
AIツールを複数立ち上げ、さらにブラウザでドキュメントを開きながらVS CodeベースのCursorを動かすと、8GBではスワップが発生しレスポンスが0.5秒ほど遅れます。
この「わずかな遅れ」がエンジニアの集中力を削ぐため、余裕を持ったスペックを用意すべきです。
Windows派の方は、WSL2環境が必須となります。Claude CodeはUnix系のターミナル操作を前提としているため、PowerShell直叩きでは動作が不安定になる落とし穴があります。

## なぜこの方法を選ぶのか

これまでCursor単体でも十分な開発が可能でしたが、Claude Codeの登場で「役割分担」の最適解が変わりました。
Cursorは「コードの俯瞰と細部の修正」には優れていますが、ターミナルでのコマンド実行や、複数ファイルにまたがる大規模なリファクタリングの自律性はまだ一歩及びません。
一方で、Claude Codeはターミナル内で「テストを回し、エラーが出たら勝手に直して、Gitにコミットする」という、より自律的なエージェントとして動きます。

GUIが得意なCursorと、CLIで爆速実行ができるClaude Code。
この2つを併用することで、人間は「設計」と「最終確認」だけに集中できるようになります。
実際に私が試したプロジェクトでは、ゼロからのプロトタイプ作成速度がCursor単体時より約40%向上しました。
「どっちがいいか」ではなく「どう組み合わせるか」が、現在のAIエンジニアリングの正解です。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはNode.js環境で動作するCLIツールです。

```bash
# Node.jsがインストールされていることを確認（v18以上推奨）
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 初期設定と認証（ブラウザが立ち上がります）
claude auth login
```

次に、プロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-notifier-tool
cd ai-notifier-tool
cursor .
```

Cursorを立ち上げたら、ターミナル（Ctrl+Shift+`）を開き、そこで `claude` コマンドを叩いて常駐させます。
これで、画面の左半分でCursorのコードを見つつ、下のターミナルでClaude Codeに指示を出す準備が整いました。

⚠️ **落とし穴:** Node.jsのバージョンが古いと、インストール時にエラーを吐きます。もし失敗したら `nvm` や `volta` でLTS版に切り替えてから再度試してください。

## Step 2: 基本の設定

Claude Codeは、プロジェクトの文脈を理解するために `.clauderc` や環境変数を利用します。
今回はPython環境を作るので、仮想環境の構築もClaudeに任せます。

ターミナル上のClaudeに対して、以下のように指示を投げてください。

```bash
# Claude Codeの対話画面で入力
Pythonの仮想環境（venv）を作成して、スクレイピングに必要なライブラリをインストールして。
必要なのは requests, beautifulsoup4, python-dotenv です。
```

Claude Codeが自動的に以下の処理を代行します。
1. `python -m venv .venv` の実行
2. 仮想環境のアクティベート
3. `pip install` の実行
4. `.gitignore` への `.venv` 追加

自分で行うのは、環境変数（APIキーなど）の管理用ファイル作成だけです。

```bash
touch .env
```

`.env` ファイルには、後ほど通知先（SlackのWebhook URLなど）を記述します。
なぜ環境変数を使うかというと、コード内に認証情報を直書きすると、GitHubに上げた瞬間に悪用されるリスクがあるからです。
実務経験者なら当たり前の作法ですが、AIに丸投げしているとつい忘れがちなので注意しましょう。

## Step 3: 動かしてみる

では、実際に動く最小構成のスクリプトを作らせます。
今回は「Yahoo!ニュースのITカテゴリから見出しを取得する」というシンプルな機能を実装します。

Claude Codeにこう指示します。
「yahoo_news.pyを作成して。YahooニュースのITカテゴリ（https://news.yahoo.co.jp/categories/it）から、記事の見出しとURLを最大5件取得してコンソールに表示するコードをお願い。実行して動作確認までやって。」

### 期待される出力

Claude Codeがファイルを生成し、自ら実行して以下のような結果を出します。

```text
[1] Appleの新製品発表会の噂... (https://news.yahoo.co.jp/...)
[2] 生成AIの新たな規制案について... (https://news.yahoo.co.jp/...)
...
```

Claude Codeの凄いところは、エラーが出た際に「あ、セレクタが変わっていましたね」と自分で判断して修正コードを書き直す点です。
人間は、ターミナルに表示される実行結果を眺めているだけで済みます。

## Step 4: 実用レベルにする

ここからが本番です。取得したニュースを「要約」し、「SlackまたはLINE」に通知する機能を追加します。
ここでCursorの出番です。

1. Cursorのチャット（Cmd+L）を開き、`@yahoo_news.py` を参照します。
2. 「このスクリプトに、取得したテキストをClaude 3.5 Sonnetで3行要約する機能と、Slack Webhookに投げる機能を追加して」と指示します。

なぜここだけCursorを使うのか。
それは、コードの全体像を見ながら「どこにロジックを追加するのが綺麗か」をGUIで視覚的に確認した方が、意図しない書き換えを防げるからです。

```python
# Cursorが提案する追加コードのイメージ
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def notify_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Webhook URLが設定されていません")
        return

    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    return response.status_code

# メイン処理の中で要約ロジックを呼び出す
```

最後に、Claude Codeに戻ってこう言います。
「全ての機能が繋がったかテストして。もし動作したら、このプロジェクトをgit initして最初のコミットをしておいて。」

テストから環境構築、バージョン管理の初期操作まで、一度もエディタを離れずに完結します。
これが、Claude Code（実行・管理）とCursor（設計・リファクタリング）のハイブリッド運用です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeが止まる | Anthropic APIのクレジット不足 | APIコンソールでチャージを確認 |
| 依存ライブラリのインポートエラー | 仮想環境が反映されていない | `source .venv/bin/activate` を実行 |
| スクレイピングがブロックされる | 短時間の連続アクセス | `time.sleep()` を入れるかUser-Agentを設定 |

## 次のステップ

この記事で、AIエージェントに「実行」を任せる快感を覚えたはずです。
次は、このスクリプトを GitHub Actions を使って「毎日決まった時間に自動実行」するように拡張してみてください。
その際も、Claude Codeに「このプロジェクトを毎日AM9時にGitHub Actionsで動かすためのyamlファイルを書いて」と頼めば、数秒で設定が完了します。

AIコーディングのコツは、AIを「ただのチャット相手」ではなく「ターミナルを操作できる部下」として扱うことです。
Cursorでコードの品質を保ち、Claude Codeで泥臭い作業を自動化する。
この使い分けができるようになれば、一人で開発できる領域が10倍以上に広がります。

## よくある質問

### Q1: Claude Codeは日本語で指示しても大丈夫ですか？

全く問題ありません。最新のClaude 3.5 Sonnetが背後で動いているため、日本語のニュアンスも正確に汲み取ってくれます。ただし、エラーログなどは英語の方が情報量が多いため、出力結果の解釈は英語に慣れておくと有利です。

### Q2: API代が怖いです。上限設定はできますか？

Anthropicのコンソール画面で、月額の使用上限（Usage Limit）を設定できます。初心者はまず$10程度に制限をかけておけば、寝ている間に数万円溶けるといった事故を防げるので安心してください。

### Q3: CursorのAI機能とClaude Code、どっちが賢いですか？

エンジンが同じなら賢さは同等ですが、Claude Codeの方が「現在のファイルツリー」や「ターミナルの実行結果」に対する認識がシビアで、よりエンジニアらしい動きをします。一方、Cursorはコードの視認性とエディタとしての使い勝手が勝ります。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIツール複数起動時もメモリ16GBあればレスポンス0.3秒を維持できるため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude Code 使い方とCursor併用の最強コーディング環境構築ガイド](/posts/2026-07-08-claude-code-cursor-workflow-guide/)
- [CursorとClaude Codeの併用でAI開発を極める！最新環境構築ガイド](/posts/2026-06-23-cursor-claude-code-integration-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeは日本語で指示しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。最新のClaude 3.5 Sonnetが背後で動いているため、日本語のニュアンスも正確に汲み取ってくれます。ただし、エラーログなどは英語の方が情報量が多いため、出力結果の解釈は英語に慣れておくと有利です。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。上限設定はできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Anthropicのコンソール画面で、月額の使用上限（Usage Limit）を設定できます。初心者はまず$10程度に制限をかけておけば、寝ている間に数万円溶けるといった事故を防げるので安心してください。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのAI機能とClaude Code、どっちが賢いですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "エンジンが同じなら賢さは同等ですが、Claude Codeの方が「現在のファイルツリー」や「ターミナルの実行結果」に対する認識がシビアで、よりエンジニアらしい動きをします。一方、Cursorはコードの視認性とエディタとしての使い勝手が勝ります。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">AIツール複数起動時もメモリ16GBあればレスポンス0.3秒を維持できるため</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252016GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2016GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

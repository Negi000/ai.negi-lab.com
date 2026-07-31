---
title: "Claude CodeとCursorを併用する最強AIコーディング環境の使い方"
date: 2026-07-31T00:00:00+09:00
slug: "claude-code-cursor-setup-guide"
cover:
  image: "/images/posts/2026-07-31-claude-code-cursor-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "エージェント型開発"
---
**所要時間:** 約40分 | **難易度:** ★★★★☆

## この記事で作るもの

- GitHubのトレンドリポジトリを自動取得し、要約してSlackまたはDiscordへ通知するPythonツール
- Cursorで全体の設計とUIを構築し、Claude Codeでデバッグと環境構築を自動化するハイブリッドワークフロー
- AIエージェントに「自律的にエラーを修正させる」具体的なプロンプト術

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Mac mini M4</strong>
<p style="color:#555;margin:8px 0;font-size:14px">メモリ32GB以上で、複数のAIエージェントを動かしても動作が極めて安定する</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMac%2520mini%2520M4%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Mac%20mini%20M4%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

**前提知識:**
- Pythonの基礎文法（変数、関数、import）がわかる
- ターミナルでの基本的なコマンド操作（cd, ls等）ができる
- GitHubアカウントを所有している

**必要なもの:**
- Anthropic API Key（Tier 2以上: 合計$40以上の支払い実績が必要）
- Cursor Proプラン推奨（月額$20）
- Node.js 18.19.0以上

## 先に確認するスペック・料金

AIコーディング環境を整える際、最も高いハードルは「ハードウェア」ではなく「APIの権限」です。
Claude Codeを利用するには、AnthropicのAPIコンソールでTier 2以上のステータスが求められます。
過去に$40以上の入金実績がない場合、まずはクレジットを追加して数日待つ必要がある点に注意してください。

PCスペックに関しては、ローカルLLMを動かすわけではないため、RTX 4090のような超高性能GPUは必須ではありません。
ただし、CursorとClaude Code、ブラウザを同時に立ち上げるため、メモリは最低でも16GB、できれば32GB以上を推奨します。
Macユーザーであれば、メモリ帯域の広いM2/M3/M4チップ搭載モデルが、AIのレスポンスを待つ間のストレスを軽減してくれます。

コスト面では、Cursor Pro（$20/月）とClaude Codeの従量課金（1プロジェクトあたり$1〜$5程度）を見込んでください。
「高い」と感じるかもしれませんが、5年間のSIer経験から断言すると、開発工数が3分の1になるため、時給換算すれば数時間で元が取れます。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor一強」に見えますが、Cursorには「ターミナル操作の自律性」という弱点があります。
CursorのTerminal AIは、コマンドを提案はしてくれますが、実行の最終判断や、実行結果を受けた連続的な修正は苦手です。

一方、Claude Codeはターミナル上で動く「エージェント」です。
「テストが通るまで勝手に修正して」と指示すれば、ファイル作成、ライブラリインストール、エラーログの読み取り、コード修正を全自動で繰り返します。

- **Cursor:** ファイル間の大規模なリファクタリング、UIのデザイン、全体構造の把握
- **Claude Code:** 依存ライブラリの解決、単体テストの自動実行、特定バグの徹底的なデバッグ

この「視覚的な編集（Cursor）」と「自律的な実行（Claude Code）」を組み合わせるのが、2024年現在、最も効率的な開発手法です。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはNode.js環境で動作するCLIツールです。

```bash
# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# バージョン確認（インストールできたかチェック）
claude -v

# 初回ログイン（ブラウザが開くので認証する）
claude auth login
```

次に、作業用ディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-trend-bot && cd ai-trend-bot
cursor .
```

⚠️ **落とし穴:**
Claude Codeのインストール時に`EACCES`エラーが出る場合は、権限の問題です。`sudo npm install -g`は推奨されないため、`nvm`（Node Version Manager）を使用してユーザー権限内にNode.jsをインストールしているか確認してください。また、Anthropic APIの残高が0だとログイン後に即座にエラーで終了します。

## Step 2: 基本の設定

プロジェクトのルートに`.clauderc`を作成する、といった手作業は不要です。
Claude Codeを起動して、最初の指示を出す際に設定を自動生成させます。

Cursor内のターミナルを開き、以下のコマンドでClaude Codeを起動します。

```bash
claude
```

起動後、まず以下の設定を確認してください。

```text
> /config
```

ここで「Auto-approve」の設定が表示されます。
私は「Read-only operations」のみをAuto-approveに設定しています。
書き込み操作を自動許可すると、予期しないコード削除が発生するリスクがあるため、実務では「確認ステップ」を残すのが私の鉄則です。

次に、環境変数を管理するための`.env`ファイルを作成します。

```bash
# .env（手動で作成するか、Claudeに作らせる）
GITHUB_TOKEN=your_github_token_here
SLACK_WEBHOOK_URL=your_webhook_url_here
```

⚠️ **落とし穴:**
APIキーを直接コードに書き込むのは絶対に避けてください。Claude Codeは`.gitignore`を読み取るため、`.env`を無視するように設定しておかないと、AIがキーを読み取って外部に送信したり、コードベースに含めてしまうリスクがあります。

## Step 3: 動かしてみる

ここからが本番です。Cursorで空の`main.py`を作成し、Claude Codeに以下のプロンプトを投げます。

```text
GitHubのPythonリポジトリのトレンドTop 5を取得するスクリプトを書いてください。
PyGitHubライブラリを使用し、結果を整形してコンソールに出力するところまで実装して。
必要なライブラリのインストールも、必要なら提案して実行して。
```

### 期待される出力

Claude Codeは、まずプロジェクト構成を確認し、`pip install PyGitHub`が必要であると判断します。

```bash
# Claude Codeの思考プロセス
1. 依存ライブラリの確認
2. `requirements.txt`の作成（または直接インストール）
3. `main.py`の実装
4. 実行テスト
```

完了すると、以下のような出力が得られるはずです。

```text
Summary of changes:
- Created requirements.txt
- Created main.py
- Installed PyGitHub

Output:
1. claudevinc/claude-code - 12,000 stars
2. cursor-ai/cursor - 45,000 stars
...
```

（※スター数は実行時のリアルな数字が表示されます）

## Step 4: 実用レベルにする

単に動くだけでは不十分です。実務では「エラーハンドリング」と「自動実行」が欠かせません。
ここでCursorの「Composer（Ctrl+I）」に切り替えます。
Cursorの方が、複数のファイルにまたがる変更を視覚的に確認しやすいからです。

Composerを開き、以下のように指示します。

「今の`main.py`を拡張して、取得したトレンドをMarkdown形式に整形し、Slackに通知する機能を追加して。また、GitHubのレートリミットに達した時のリトライ処理も入れてください」

Cursorがコードを生成したら、再びターミナル（Claude Code）に戻り、こう指示します。

```text
今の変更が正しく動作するかテストして。
特にSlack通知の部分は、モックを使ってネットワーク通信が発生しないテストコードを `tests/test_main.py` に作成して、pytestを実行して。
```

私は以前、このステップを怠ってAPI課金が跳ね上がった経験があります。
Claude Codeは、テストコードの作成と実行のループを非常に得意としています。
「テストが通るまでループして」という指示を出すと、エンジニアが寝ている間にバグを修正し続けるエージェントになります。

```python
# 実用的なコードの一部（Claude Codeが生成するリトライ処理の例）
import time
from github import GithubException

def fetch_with_retry(func, retries=3):
    for i in range(retries):
        try:
            return func()
        except GithubException as e:
            if e.status == 403: # Rate limit
                wait = (i + 1) * 60
                print(f"Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
```

「なぜこのコードにするのか」をClaude Codeに問い詰めると、「指数バックオフ（Exponential Backoff）を採用することで、APIサーバーへの負荷を抑えつつ成功率を高めています」といった理論的な回答が返ってきます。
これこそが、単なるコピペエンジニアを脱却するために必要な対話です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Model not found` | API Tierが不足している | Anthropicで$40以上の入金と数日の待機を確認する |
| `SyntaxError` | Pythonのバージョン不一致 | `python --version`を確認し、Claudeに環境を伝える |
| `Loop detected` | AIが同じ修正を繰り返している | 一度中断（Ctrl+C）し、手動で一箇所修正してから再開する |

## 次のステップ

この記事で、CursorとClaude Codeを併用する「エージェント型開発」の入り口に立ちました。
次に挑戦すべきは「既存の巨大なプロジェクトへの導入」です。

まずは、自分の過去のプロジェクトをClaude Codeに読み込ませ、`/compact` コマンドでコンテキストを整理させてみてください。
その上で、「このコードの中で、パフォーマンス上のボトルネックになっている関数を見つけて、高速化して」と指示を出すのです。
自分の書いたコードが、AIによって秒速でリファクタリングされる快感（と少しの恐怖）を味わうことが、AI時代のエンジニアとしての第一歩になります。

さらに、GitHub Actionsと連携させて、このスクリプトを毎日定時に実行するようにデプロイしてみてください。
Claude Codeに「このツールをGitHub Actionsで毎日AM9時に動かすためのYAMLファイルを作って」と言えば、一瞬で解決します。

## よくある質問

### Q1: Claude Codeは日本語で指示しても大丈夫ですか？

はい、全く問題ありません。指示は日本語で行い、コード内のコメントやログは英語にするよう指定するのが、最もエラーが少なく、かつ世界中の開発者が読みやすいコードになるため、私は常にそうしています。

### Q2: API代が怖いです。制限をかける方法はありますか？

Anthropicのコンソールで「Monthly Budget」を設定してください。また、Claude Code起動中に「Cost: $0.12」のように都度利用額が表示されるので、それをこまめにチェックする癖をつけるのが一番の対策です。

### Q3: Cursorの有料版（Pro）は絶対に必要ですか？

Claude Codeだけなら不要ですが、今回紹介した「視覚的な全体リファクタリング」にはCursor Proの「Composer」機能が不可欠です。月額$20は、エンジニアの生産性を考えれば最も安い投資の一つだと私は考えています。

---

## あわせて読みたい

- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用する最強のAI開発環境の作り方](/posts/2026-07-27-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用してAI開発を完全自動化する方法](/posts/2026-07-18-claude-code-cursor-ai-coding-tutorial/)

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
        "text": "はい、全く問題ありません。指示は日本語で行い、コード内のコメントやログは英語にするよう指定するのが、最もエラーが少なく、かつ世界中の開発者が読みやすいコードになるため、私は常にそうしています。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。制限をかける方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Anthropicのコンソールで「Monthly Budget」を設定してください。また、Claude Code起動中に「Cost: $0.12」のように都度利用額が表示されるので、それをこまめにチェックする癖をつけるのが一番の対策です。"
      }
    },
    {
      "@type": "Question",
      "name": "Cursorの有料版（Pro）は絶対に必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeだけなら不要ですが、今回紹介した「視覚的な全体リファクタリング」にはCursor Proの「Composer」機能が不可欠です。月額$20は、エンジニアの生産性を考えれば最も安い投資の一つだと私は考えています。 ---"
      }
    }
  ]
}
</script>

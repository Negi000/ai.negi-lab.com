---
title: "Claude CodeとCursorを併用して爆速でAPI連携ツールを開発する方法"
date: 2026-11-19T00:00:00+09:00
slug: "claude-code-cursor-integrated-workflow-guide"
cover:
  image: "/images/posts/2026-11-19-claude-code-cursor-integrated-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIコーディング環境"
  - "Anthropic API 連携"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

GitHubリポジトリのURLを入力すると、最新のコミットメッセージとREADMEを解析して「開発状況を3行で要約する」CLIツールをPythonで作ります。
Pythonの基本的な文法（if文や関数の定義）がわかれば、Claude CodeとCursorの「分業」の真髄を体験できる構成にしています。
この記事の指示通りに進めれば、環境構築からツール完成、そしてテスト実行までを一気通貫で完了できます。

## 先に確認するスペック・料金

Claude CodeはAnthropicが提供する「ターミナルで動くAIエージェント」ですが、VS Code派生のIDEであるCursorと併用することで最強の環境になります。
ただし、Claude Codeは「自分でコマンドを叩いてエラーを確認し、修正して再実行する」という自律的な動きをするため、APIトークンの消費が非常に激しいです。
AnthropicのAPI Tierが「Tier 2（累計$50以上の支払い）」以上でないと、レートリミット（回数制限）に引っかかり、作業が中断してストレスが溜まります。

ハードウェアについては、MacBook（M1以降）またはLinux環境を推奨します。
Windowsの場合はWSL2（Ubuntu）が必須です。PowerShell直叩きだとClaude Codeがファイル操作でコケることが多いからです。
また、API料金として、この記事の内容を完走するだけで$2〜$5程度は溶ける覚悟をしてください。
時間を金で買う感覚がない人には、正直この環境はおすすめしません。

## なぜこの方法を選ぶのか

Cursorだけで開発は完結しますが、あえてClaude Codeを併用するのは「ターミナル操作の自動化」が圧倒的に楽だからです。
CursorのComposer（Ctrl+I）も優秀ですが、ライブラリのインストールやディレクトリ構造の作成、テストの実行までは、まだ人間に「実行ボタンを押して」と頼る場面が多いのが現状です。
Claude Codeは「このライブラリが足りないからインストールしたよ」「テストが落ちたからコード直して再実行したよ」という自律ループを勝手に回してくれます。

私はこれまで20件以上の機械学習案件をこなしてきましたが、一番時間がかかるのは「環境依存のエラー解決」でした。
Cursorでコードの全体像を俯瞰し、Claude Codeに泥臭いデバッグと環境構築を任せる。
この「司令塔（Cursor）」と「実行部隊（Claude Code）」の役割分担が、現時点で最も生産性が高いと断言できます。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。Node.jsのバージョン18以上が必要です。

```bash
# Node.jsのバージョン確認
node -v

# Claude Codeのインストール
npm i -g @anthropic-ai/claude-code

# 認証（ブラウザが開くのでAnthropicアカウントでログイン）
claude auth
```

Claude Codeはnpm経由で提供されています。
グローバルインストールすることで、どのプロジェクトディレクトリからでも `claude` コマンドを呼び出せるようになります。
この際、`nvm`（Node Version Manager）を使っている人は、使用中のNodeバージョンにインストールされているか注意してください。

⚠️ **落とし穴:**
`claude auth` でエラーが出る場合、多くはブラウザのキャッシュかAPIキーの権限不足です。
特に法人アカウントの場合、管理者が「Claude Code」の使用を許可していないと弾かれます。
個人アカウントで、かつクレジットカードを登録して$5以上のクレジットをチャージした状態で進めるのが最も確実です。

## Step 2: 基本の設定

プロジェクト用のディレクトリを作成し、Claude Codeを起動します。

```bash
mkdir github-summarizer
cd github-summarizer
git init
claude
```

Claude Codeが起動すると、専用のシェルに入ります。
ここで、プロジェクトの初期設定を「会話」で進めます。

```text
> PythonでGitHub APIを使うツールを作りたい。必要なライブラリをインストールして。
```

Claude Codeは「`requests` と `python-dotenv` が必要ですね」と判断し、自ら `pip install` を実行します。
なぜ `python-dotenv` を入れるのかというと、APIキーをコードに直書きするリスクを避けるためです。
Claude Codeはこのあたりの「開発のベストプラクティス」を指示なしでも守ってくれるのが、ただのチャットAIとの違いです。

## Step 3: 動かしてみる

次に、最小限のコードを生成させます。
Cursorを開いて横に並べておくと、Claude Codeがファイルを作成する様子がリアルタイムで確認できて面白いです。

```text
> .envファイルにGITHUB_TOKENを保存する仕組みを作って。
> その後、特定のリポジトリのREADMEを取得するだけの最小限のスクリプト main.py を書いて。
```

### 期待される出力

Claude Codeが以下のような `main.py` を作成し、実行まで提案してくれます。

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_readme(repo_owner, repo_name):
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/readme"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return content
    else:
        return f"Error: {response.status_code}"

if __name__ == "__main__":
    # テストとして自分の適当なリポジトリか、公開リポジトリを指定
    print(get_readme("psf", "requests")[:200])
```

（結果の読み方: 200 OKが返ってきて、READMEの冒頭が表示されれば疎通確認完了です）

## Step 4: 実用レベルにする

ここからが本番です。単なる取得ではなく「要約」の機能を組み込みます。
Claude Codeに「Anthropic APIを使って、取得したREADMEの内容を要約する機能」を追加させます。

```text
> AnthropicのPython SDKをインストールして。
> main.pyを修正して、READMEの内容をClaude 3.5 Sonnetに渡し、「このプロジェクトは何をするものか」を3行で日本語要約する機能を追加して。
```

私は以前、これを手動でやろうとして `base64` デコードの処理で型エラー（bytes vs str）にハマりました。
しかし、Claude Codeに任せると、実行環境のPythonバージョン（3.10以上か未満かなど）をチェックした上で、最適なコードを吐き出します。

```python
# 最終的な実用コード例（Claude Codeが生成・修正したもの）
import os
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

def get_github_info(repo_url):
    # URLからownerとrepoを抽出
    parts = repo_url.strip("/").split("/")
    owner, repo = parts[-2], parts[-1]

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}

    # README取得
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    readme_res = requests.get(readme_url, headers=headers)
    readme_content = ""
    if readme_res.status_code == 200:
        import base64
        readme_content = base64.b64decode(readme_res.json()['content']).decode('utf-8')

    # コミット履歴取得
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commit_res = requests.get(commit_url, headers=headers)
    latest_commit = "No commit info"
    if commit_res.status_code == 200:
        latest_commit = commit_res.json()[0]['commit']['message']

    return readme_content, latest_commit

def summarize_project(readme, commit):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""以下のGitHubプロジェクトの内容（READMEと最新コミット）を解析し、
    何をするプロジェクトかを3行の日本語で要約してください。

    README:
    {readme[:3000]}

    最新コミット:
    {commit}
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

if __name__ == "__main__":
    url = input("GitHubリポジトリURLを入力してください: ")
    readme, commit = get_github_info(url)
    summary = summarize_project(readme, commit)
    print("\n--- プロジェクト要約 ---")
    print(summary)
```

このコードを動かすために、Claude Codeは自ら `pip install anthropic` を実行し、`.env` ファイルに `ANTHROPIC_API_KEY` があるか確認を求めてきます。
もしキーが設定されていなければ「設定してからもう一度 `python main.py` を実行してみて」とガイドしてくれます。
この「次に何をすべきか」をツール側が知っている状態が、開発体験を劇的に変えます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Permission denied` | Claude Codeがファイル作成権限を持たない | `sudo` は使わず、ディレクトリの所有権を確認。WSLならWindows側パス（/mnt/c/）を避ける |
| `Rate limit exceeded` | 短時間にAPIを叩きすぎた | API Tierを上げるか、1分ほど待って再開。Claude Codeの自動実行を一時停止する |
| `ModuleNotFoundError` | 仮想環境（venv）の不一致 | `claude config` で使用するpythonパスを明示的に指定する |

## 次のステップ

この「GitHub要約ツール」が動いたら、次は **Cursorの「 codebase indexing 」機能との使い分け** を意識してみてください。
今回のように「ゼロからツールを作る」「依存関係を解決する」のはClaude Codeが得意です。
一方で、できたコードに対して「ここのUIを少し青くして」「この関数を別のファイルに切り出して」といった視覚的な修正やリファクタリングは、CursorのGUIでコード全体を眺めながら行う方がミスが少ないです。

私はよく、Claude Codeでスクリプトの骨格を作り、ユニットテストを自動生成させて全パスを通した後に、Cursorでコードの可読性を整えるという「二段構え」で開発しています。
次に挑戦するなら、今回のツールに「Slack通知機能」を追加するようClaude Codeに命じてみてください。
APIドキュメントを読みに行き、必要なペイロード構造を勝手に調べて実装してくれるはずです。

## よくある質問

### Q1: Claude Codeを使うとAPI料金が跳ね上がりそうで怖いです。

節約したいなら、`/config` で `auto-execute` を `false` に設定してください。AIがコマンドを実行する前に必ず確認を求めるようになります。これだけで無駄なリトライを防げます。

### Q2: CursorのAI機能（Composer）があれば、Claude Codeはいらなくないですか？

Composerは「エディタ内の変更」に強いですが、Claude Codeは「OSを含めた操作」に強いです。例えば、DBのマイグレーション実行や、ローカルサーバーの起動確認を含めたループはClaude Codeの方がスムーズです。

### Q3: 日本語での指示は完璧に通りますか？

基本的には通じますが、複雑なディレクトリ構造の指示は英語の方が確実です。ただし、出力されるコメントやドキュメントを日本語にしたい場合は「日本語で書いて」と一言添えるだけで十分対応してくれます。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Claude Codeの並列処理とCursorのインデックス作成を快適に行うには32GBメモリが理想</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用して開発効率を3倍に引き上げるAIコーディング環境構築ガイド](/posts/2026-11-09-claude-code-cursor-ai-coding-setup-guide/)
- [Claude CodeとCursorを併用した最強のAIコーディング環境構築ガイド](/posts/2026-10-18-claude-code-cursor-ai-coding-workflow-guide/)
- [Claude CodeとCursorを併用したAIコーディング環境の構築と使い方](/posts/2026-10-31-claude-code-cursor-ai-development-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Codeを使うとAPI料金が跳ね上がりそうで怖いです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "節約したいなら、/config で auto-execute を false に設定してください。AIがコマンドを実行する前に必ず確認を求めるようになります。これだけで無駄なリトライを防げます。"
      }
    },
    {
      "@type": "Question",
      "name": "CursorのAI機能（Composer）があれば、Claude Codeはいらなくないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Composerは「エディタ内の変更」に強いですが、Claude Codeは「OSを含めた操作」に強いです。例えば、DBのマイグレーション実行や、ローカルサーバーの起動確認を含めたループはClaude Codeの方がスムーズです。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語での指示は完璧に通りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には通じますが、複雑なディレクトリ構造の指示は英語の方が確実です。ただし、出力されるコメントやドキュメントを日本語にしたい場合は「日本語で書いて」と一言添えるだけで十分対応してくれます。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Claude Codeの並列処理とCursorのインデックス作成を快適に行うには32GBメモリが理想</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

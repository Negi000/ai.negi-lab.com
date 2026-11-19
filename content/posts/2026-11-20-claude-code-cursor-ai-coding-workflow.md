---
title: "Claude CodeとCursorを併用して爆速で開発環境を構築する方法"
date: 2026-11-20T00:00:00+09:00
slug: "claude-code-cursor-ai-coding-workflow"
cover:
  image: "/images/posts/2026-11-20-claude-code-cursor-ai-coding-workflow.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor AI 連携"
  - "AIプログラミング"
  - "Claude 3.5 Sonnet API"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

GitHub APIと連携して、指定したリポジトリの最新リリース情報とコミット履歴を自動で取得・要約し、Markdown形式でレポートを出力するCLIツールを開発します。
Cursorでコードのロジックを組み上げ、Claude Codeにテスト実行とターミナル操作を任せる「AI二刀流」のワークフローを完成させます。

前提知識：
- 基本的なPythonの読み書きができる
- ターミナル（コマンドプロンプトやzsh）の操作に抵抗がない
- GitHubアカウントを所有している

必要なもの：
- Anthropic APIキー（Claude Code用）
- Cursor（Proプラン推奨）
- Node.js v18以上（Claude Codeの動作環境）
- Python 3.10以上

## 先に確認するスペック・料金

AIコーディングを本格化させるなら、まず「APIコスト」と「マシンパワー」の現実を見る必要があります。
Claude CodeはAnthropicの公式ツールであり、現在は利用にAnthropic APIの従量課金が発生します。
私の検証では、中規模なリポジトリで1時間集中して開発すると、$3〜$5程度のAPI費用が飛んでいきます。

Cursor Proの月額$20とは別にこのコストがかかるため、予算管理が重要です。
ハードウェアについては、VS CodeベースのCursorと、Node.js上で動くClaude Codeを同時に立ち上げるため、メモリは最低でも16GB、できれば32GB以上を推奨します。
私はRTX 4090を積んだ自作機で動かしていますが、この構成はローカルLLMを動かさない限り必須ではありません。
むしろ、画面領域が重要になるため、27インチ以上の4Kモニターを導入して「左にCursor、右にターミナル（Claude Code）」を配置するのが最も効率的です。

## なぜこの方法を選ぶのか

Cursorだけでも、あるいはClaude Codeだけでも開発は可能です。
しかし、Cursorは「エディタとしての編集能力」に長けている反面、ターミナルでの複雑なコマンド実行やファイル操作の連続性において、Claude Codeに一歩譲ります。
一方でClaude Codeは「ターミナルネイティブ」であり、Git操作やテストの実行、環境構築の自動化において圧倒的なコンテキスト理解力を発揮します。

つまり、Cursorを「精緻な手術を行うメス」として使い、Claude Codeを「現場全体を指揮する執刀医」として配置するのが、2024年末時点での最強のAI開発布陣です。
両者を併用することで、人間は「何を作るか」という意思決定だけに集中し、実装とデバッグのループをAIに丸投げできる環境が整います。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。
これはnpmパッケージとして提供されているため、Node.js環境が必要です。

```bash
# Claude Codeをグローバルにインストール
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

次に、Claude Codeを認証します。
以下のコマンドを打つとブラウザが立ち上がるので、AnthropicのコンソールからAPIキーを発行して連携してください。

```bash
claude auth
```

⚠️ **落とし穴:**
Node.jsのバージョンが古いと、インストール中に「Unexpected token」などのエラーが出ることがあります。
必ず `node -v` で18以上であることを確認してください。
また、macOSユーザーで `npm install -g` が権限エラーになる場合は、`sudo` をつけるのではなく、nvm（Node Version Manager）を使用してユーザー権限内に環境を構築することを強く勧めます。

## Step 2: 基本の設定

開発用のディレクトリを作成し、Cursorで開きます。
ここで、今回のツールに必要なライブラリをインストールし、環境変数を設定します。

```bash
mkdir ai-repo-summary
cd ai-repo-summary
touch main.py .env
```

次に、`.env` ファイルにGitHubのパーソナルアクセストークンを記述します。
これは、APIのレート制限を回避し、プライベートリポジトリにもアクセスできるようにするためです。

```text
GITHUB_TOKEN=your_github_token_here
```

次に、Cursorの「Settings > Models」から「Claude 3.5 Sonnet」が有効になっていることを確認してください。
なぜSonnet 3.5を使うのか。
それは、現在のコーディング特化モデルの中で、推論能力とレスポンス速度（約0.5秒〜1.5秒の初動）のバランスが最も優れているからです。

## Step 3: 動かしてみる

まず、CursorのComposer（Cmd+I）を開き、以下のプロンプトを投げます。

「GitHub APIを使って、指定されたリポジトリの最新リリース名と最新3件のコミットメッセージを取得し、Markdownで出力するPythonスクリプトの雛形を作って。requestsライブラリを使って、APIトークンは.envから読み込む形式で。」

生成されたコードが以下のような形であることを確認してください。

```python
import os
import requests
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

def get_repo_summary(owner, repo):
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"}

    # リリース情報の取得
    release_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    release_res = requests.get(release_url, headers=headers)

    # コミット履歴の取得
    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=3"
    commits_res = requests.get(commits_url, headers=headers)

    if release_res.status_code != 200 or commits_res.status_code != 200:
        return "エラー: データの取得に失敗しました。"

    release_data = release_res.json()
    commits_data = commits_res.json()

    summary = f"# Summary for {owner}/{repo}\n\n"
    summary += f"## Latest Release: {release_data.get('name', 'N/A')}\n\n"
    summary += "## Recent Commits:\n"
    for c in commits_data:
        summary += f"- {c['commit']['message']}\n"

    return summary

if __name__ == "__main__":
    # テストとして、自分の興味あるリポジトリを指定
    print(get_repo_summary("python", "cpython"))
```

### 期待される出力

```markdown
# Summary for python/cpython

## Latest Release: Python 3.13.0

## Recent Commits:
- gh-126000: Update documentation
- [main] Fix reference leaks in test_typing
- Add missing NEWS entry for PR #12345
```

## Step 4: 実用レベルにする

ここからがClaude Codeの真骨頂です。
ターミナルで `claude` と打ち込み、Claude Codeを起動します。
そして、以下の指示を伝えます。

「今Cursorで作った main.py がある。これにエラーハンドリングを追加して、さらに出力結果を report.md というファイルに保存する機能を追加して。終わったら実際に実行して、動作確認までやっておいて。」

Claude Codeは自動でファイルを読み込み、コードを修正し、さらに `python main.py` を実行して結果を確認します。
私が手動で行うのは、Claude Codeが提案するファイル書き換えを `y` キーで承認することだけです。

```python
# 実用的なコードへの進化例（Claude Codeによる修正後）
import os
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

def get_repo_summary(owner, repo):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env")
        sys.exit(1)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # タイムアウトを設定してハングを防ぐ（実務上の必須設定）
        release_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/releases/latest",
            headers=headers,
            timeout=10
        )
        release_res.raise_for_status()

        commits_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=3",
            headers=headers,
            timeout=10
        )
        commits_res.raise_for_status()

        release_data = release_res.json()
        commits_data = commits_res.json()

        # 出力の構築
        content = [
            f"# Summary for {owner}/{repo}",
            f"## Latest Release: {release_data.get('name', 'N/A')}",
            "## Recent Commits:"
        ]
        for c in commits_data:
            msg = c['commit']['message'].split('\n')[0]
            content.append(f"- {msg}")

        return "\n".join(content)

    except requests.exceptions.RequestException as e:
        return f"API Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <owner> <repo>")
        sys.exit(1)

    owner, repo = sys.argv[1], sys.argv[2]
    result = get_repo_summary(owner, repo)

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(result)
    print("Report saved to report.md")
```

このフローの凄さは、私が一度も「エディタとターミナルを往復してコピペ」をしていない点にあります。
Cursorでロジックを「点」で作り、Claude Codeで「線」につなげていく感覚です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `ModuleNotFoundError: No module named 'requests'` | 仮想環境にライブラリが入っていない | `pip install requests python-dotenv` を実行 |
| `401 Client Error: Unauthorized` | GitHubトークンが無効または未設定 | `.env` のトークンを確認し、スコープに `repo` が含まれているかチェック |
| `Claude Code: Command not found` | npmのパスが通っていない | ターミナルを再起動するか、Node.jsのパスを再設定する |

## 次のステップ

この「Cursor + Claude Code」の連携に慣れたら、次は「MCP（Model Context Protocol）」の導入に挑戦してください。
Claude CodeはMCPサーバーを介して、Google Searchやローカルのデータベース、さらにはSlackなどと直接連携できるようになります。

例えば、「最新のAIニュースを検索し（MCP Search）、その内容を要約するコードを書き（Cursor）、実際にリポジトリにコミットしてデプロイする（Claude Code）」という一連の動作を、一つのターミナル上で完結させることが可能です。
もはやプログラミングは「コードを書く作業」から「AIという部下に指示を出し、成果物を検収する作業」へと完全にシフトしました。
この感覚を掴むために、まずは今日作ったCLIツールをベースに、自分の業務を一つ自動化してみてください。

## よくある質問

### Q1: Cursorの有料プランに入っていれば、Claude Codeの料金は無料ですか？

いいえ、別料金です。Cursorは自身のサブスクリプション内でモデルを提供していますが、Claude CodeはAnthropicのAPIを直接叩くため、従量課金（Creditを事前に購入する形式）が必要です。

### Q2: Claude Codeにファイルを勝手に消されたりしませんか？

Claude Codeはファイル操作の前に必ず「このファイルを書き換えても良いか？」と許可を求めてきます。また、Gitを使用していれば、万が一の際も `git checkout .` で即座に復元できるため、必ずGit管理下で作業してください。

### Q3: Python以外の言語でも同じワークフローが使えますか？

もちろんです。TypeScriptやGo、Rustなど、ほぼすべての主要言語で機能します。特にコンパイルが必要な言語（Rustなど）では、Claude Codeに「ビルドエラーが出なくなるまで修正して」と指示を投げる使い方が非常に強力です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CursorとClaude Codeを左右に並べて俯瞰するには、広大な4K作業領域が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド](/posts/2026-06-27-claude-code-cursor-workflow-guide/)
- [Claude CodeとCursorを併用して開発効率を3倍に引き上げるAIコーディング環境構築ガイド](/posts/2026-11-09-claude-code-cursor-ai-coding-setup-guide/)
- [Navox Agents レビュー Claude Codeを組織で安全に運用するための特化型エージェント管理](/posts/2026-04-17-navox-agents-claude-code-review-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Cursorの有料プランに入っていれば、Claude Codeの料金は無料ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、別料金です。Cursorは自身のサブスクリプション内でモデルを提供していますが、Claude CodeはAnthropicのAPIを直接叩くため、従量課金（Creditを事前に購入する形式）が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "Claude Codeにファイルを勝手に消されたりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeはファイル操作の前に必ず「このファイルを書き換えても良いか？」と許可を求めてきます。また、Gitを使用していれば、万が一の際も git checkout . で即座に復元できるため、必ずGit管理下で作業してください。"
      }
    },
    {
      "@type": "Question",
      "name": "Python以外の言語でも同じワークフローが使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "もちろんです。TypeScriptやGo、Rustなど、ほぼすべての主要言語で機能します。特にコンパイルが必要な言語（Rustなど）では、Claude Codeに「ビルドエラーが出なくなるまで修正して」と指示を投げる使い方が非常に強力です。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Dell U2723QE</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">CursorとClaude Codeを左右に並べて俯瞰するには、広大な4K作業領域が必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

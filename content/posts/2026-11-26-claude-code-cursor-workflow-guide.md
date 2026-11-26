---
title: "Claude CodeとCursorを併用して爆速でプロダクトを開発する環境を構築する方法"
date: 2026-11-26T00:00:00+09:00
slug: "claude-code-cursor-workflow-guide"
cover:
  image: "/images/posts/2026-11-26-claude-code-cursor-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIエージェント コーディング"
  - "ソフトウェア開発 自動化"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

FastAPIを使用した「AIによる要約機能付きMarkdownエディタ」のバックエンドとテスト環境を、CursorとClaude Codeの役割分担だけで完結させて構築します。
Pythonの基本的な文法がわかる方を対象に、API設計からテストコードの実装、デバッグまでをAIエージェントに丸投げするワークフローを確立します。
必要なものは、AnthropicのAPIキー（Tier 2以上推奨）とCursorの有料プラン、Node.jsが動く環境です。

## 先に確認するスペック・料金

Claude CodeはAnthropicが提供するエージェント型CLIツールであり、手元のマシンパワーよりも「APIのレート制限」がボトルネックになります。
実務で使うなら、API使用実績が$50以上の「Tier 2」以上でないと、頻繁なリクエストですぐに制限がかかり、作業が止まってしまいます。
一方、CursorはIDEとしての補完やチャットに特化しており、こちらは月額$20のProプランで提供される「Claude 3.5 Sonnet使い放題」の枠を使い倒すのが最もコスパが良いです。

ハードウェアについては、VS Codeが快適に動くスペック（メモリ16GB以上）があれば十分ですが、Claude CodeのインストールにはNode.js 18.19.0以上が必要です。
もしAPIキーの準備がまだなら、まずAnthropicのConsoleからクレジットをチャージしてください。
ローカルLLMを動かすわけではないのでRTX 4090は必須ではありませんが、Claude Codeからの提案を高速にプレビューするために、画面は2枚以上あると作業効率が劇的に変わります。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「IDE型（Cursor）」と「エージェント型（Claude Code, Aider, Cline）」の2種類に分かれています。
Cursorはコードを書きながら「ここを直して」と指示するUIには優れていますが、プロジェクト全体の依存関係を把握して「テストを全部通るまで修正し続けて」といった自律的なタスクは苦手です。
逆にClaude Codeはターミナル上で自律的にシェルコマンドを叩き、エラーが出たら勝手に修正案を考えて実行する「自走力」がありますが、エディタとしての使い勝手はありません。

私はこれまでClineやAiderも試してきましたが、Claude Codeの「公式ゆえの安定感」と「ファイル編集の正確性」は群を抜いています。
Cursorを「高精度なハンドル（操作）」、Claude Codeを「優秀なメカニック（整備・自動化）」として使い分けるのが、現在の開発における最適解だと断言できます。
この併用スタイルにより、人間は「設計」と「最終確認」だけに集中し、泥臭いデバッグやボイラープレートの記述から解放されます。

## Step 1: 環境を整える

まず、Claude Codeをグローバルにインストールします。
既存のプロジェクトがある場合は、そのルートディレクトリで作業を開始してください。

```bash
# Node.js 18.19.0以上が必要です
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# 認証（ブラウザが開くのでAnthropicアカウントでログイン）
claude auth
```

このツールは、あなたの代わりにファイルを読み書きし、ターミナルでコマンドを実行します。
そのため、最初に実行権限の確認が求められますが、実務効率を優先するために私は常に全ての権限を許可しています。
Node.jsのバージョンが古いとインストール時にエラーが出るので、その場合は`nvm`などで最新のLTSに切り替えてください。

⚠️ **落とし穴:**
Claude Codeはデフォルトで`git`管理されていないファイルを編集することを嫌がります。
新しいプロジェクトを始める際は、必ず最初に`git init`を実行してください。
これを忘れると、Claude Codeが「変更を戻せなくなる可能性がある」と警告を出し、動作が制限されることがあります。

## Step 2: 基本の設定

Claude Codeを起動する前に、プロジェクト固有の設定を行います。
特に「どのファイルをAIに見せないか」の設定は、APIトークンの節約とセキュリティの両面で重要です。

```bash
# プロジェクトディレクトリを作成して移動
mkdir ai-markdown-api && cd ai-markdown-api
git init

# Claude Codeの初期化（対話形式で進みます）
claude init
```

`.claudeignore`というファイルが生成されるので、ここには`node_modules`や`__pycache__`、`.env`などを追記してください。
Claude Codeはプロジェクト全体をスキャンしようとするため、不要なバイナリファイルが含まれていると、それだけでトークンを大量に消費し、レスポンスが悪化します。

次に、Cursorを開きます。
Cursorの設定（Settings > Models）で「Claude 3.5 Sonnet」が優先的に使われるようになっていることを確認してください。
私は「CursorのComposer機能」と「Claude CodeのCLI」を同時に画面に並べて運用しています。

## Step 3: 動かしてみる

まずは最小限のFastAPIアプリケーションを作成します。
ここではCursorのComposer（Cmd+I）を使い、「FastAPIでMarkdownをHTMLに変換するエンドポイントを持つmain.pyを作って」と指示してください。

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import markdown

app = FastAPI()

class MarkdownInput(BaseModel):
    content: str

@app.post("/convert")
async def convert_markdown(input_data: MarkdownInput):
    # ここに変換ロジックを記述
    html = markdown.markdown(input_data.content)
    return {"html": html}
```

### 期待される出力

Cursorがコードを生成したら、保存してターミナルに戻ります。
ここでClaude Codeの出番です。
ターミナルで`claude`と打ち込み、エージェントを起動します。

```bash
claude
# 起動後、プロンプトに以下を入力
> "このプロジェクトに必要な依存関係をrequirements.txtに書き出して、venvを作成してインストールして。その後、サーバーを起動してcurlで動作確認までやって。"
```

Claude Codeは`ls`でファイルを確認し、`main.py`の内容を読み取り、`markdown`と`fastapi`が必要だと判断して`requirements.txt`を自動生成します。
その後、仮想環境の構築から`pip install`、さらには`uvicorn`の起動とテストリクエストまでを、あなたの許可を得ながら（あるいは自動で）完結させます。

## Step 4: 実用レベルにする

ここからが本番です。
単なる変換機能だけでなく、「AIによる要約機能」を追加し、さらに「ユニットテストを100%通す」という実務的なタスクをClaude Codeに命じます。

まず、`.env`にOpenAIやAnthropicのAPIキーを設定してください（Claude Codeにキーを直接渡さないよう注意）。
その上で、Claude Codeに以下のヘビーな指示を投げます。

```bash
> "main.pyに、LangChainを使ってMarkdownの内容を3行で要約する/summarizeエンドポイントを追加して。
その後、pytestを使って/convertと/summarizeの両方のテストコードを作成し、すべてのテストがパスするまでバグを修正し続けて。"
```

私が見てきた中で、初心者が最も時間を溶かすのは「環境変数まわりのエラー」と「テストライブラリのインポートエラー」です。
Claude Codeは、pytestを実行して`ModuleNotFoundError`が出れば、即座に`pip install pytest-asyncio`を実行するなど、自律的にエラーを解決していきます。
もしライブラリの仕様変更でコードが動かない場合は、Claude Codeが内蔵のウェブ検索機能（Google検索等）を使って最新のドキュメントを読みに行き、修正案を提示します。

この間、あなたはCursor側で生成されていくコードを眺めているだけでOKです。
「あ、ここは少しロジックを変えたいな」と思ったら、Cursorのエディタ上で直接修正すれば、Claude Codeは次のステップでその修正を反映したテストを書いてくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | Anthropic APIのTierが低い | $50以上チャージしてTier 2に上げるか、1分待つ |
| Command not found | パスが通っていない | `npm install -g`のパスを確認するか、`npx @anthropic-ai/claude-code`を使う |
| Permission denied | Claude Codeの権限不足 | 実行時に`--dangerously-skip-permissions`フラグを検討（自己責任） |

## 次のステップ

このワークフローをマスターすると、個人開発の速度は3倍以上に跳ね上がります。
次に挑戦すべきは「既存の巨大なレガシーコードのドキュメント化とリファクタリング」です。
Claude Codeに「このディレクトリ配下の全ての関数の型ヒントを修正し、Googleスタイルのdocstringを追加して。終わったらカバレッジを測定して」と指示してみてください。

人間がやれば数日かかる作業が、APIコスト数百円と数十分の待ち時間で完了します。
ただし、AIは時として「動くけれどメンテナンスしにくいトリッキーなコード」を書くことがあります。
最終的なコードレビューは必ず人間が行い、特にセキュリティに関わる部分は自分の目で確認する習慣をつけてください。
私は常に、重要なロジックに関しては「なぜこの実装にしたのか？」をClaude Codeに質問し、その回答が論理的かを確認するようにしています。

## よくある質問

### Q1: Cursorだけで十分ではないですか？

CursorのComposer機能も強力ですが、ターミナルを実行してその結果を元にループを回す「自律性」においては、Claude Codeの方が圧倒的に上です。
テストを回しながらエラーを潰す作業はClaude Codeに、UIを見ながら微調整する作業はCursorに任せるのが、現時点での最適解です。

### Q2: API料金が高額になりそうで怖いです。

Claude Codeは一回の指示で数十トークン〜数万トークンを消費します。
対策として、`.claudeignore`を適切に設定し、大きなファイルを読み込ませすぎないことが重要です。
まずは数ドルのクレジットチャージから始めて、消費ペースを把握することをお勧めします。

### Q3: 会社のプロプライエタリなコードに使っても大丈夫ですか？

AnthropicのAPI（特にClaude Code経由）は、送信されたデータがモデルの学習に利用されないことが明記されています。
しかし、会社の規定で「外部APIへのコード送信」自体が禁止されているケースも多いです。
導入前に必ず社内のセキュリティポリシーを確認し、必要に応じてオプトアウトの設定やプロキシの検討を行ってください。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Cursorとターミナルを横並びにする開発環境には高解像度モニタが不可欠</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude CodeとCursorを併用する最強のAIコーディング環境構築ガイド](/posts/2026-08-19-claude-code-cursor-ai-coding-tutorial/)
- [Claude CodeとCursorを併用した最強のAIコーディング環境構築ガイド](/posts/2026-10-18-claude-code-cursor-ai-coding-workflow-guide/)
- [Claude CodeとCursorを併用したAIコーディング環境構築と実践ガイド](/posts/2026-08-28-claude-code-cursor-ai-coding-guide/)

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
        "text": "CursorのComposer機能も強力ですが、ターミナルを実行してその結果を元にループを回す「自律性」においては、Claude Codeの方が圧倒的に上です。 テストを回しながらエラーを潰す作業はClaude Codeに、UIを見ながら微調整する作業はCursorに任せるのが、現時点での最適解です。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が高額になりそうで怖いです。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeは一回の指示で数十トークン〜数万トークンを消費します。 対策として、.claudeignoreを適切に設定し、大きなファイルを読み込ませすぎないことが重要です。 まずは数ドルのクレジットチャージから始めて、消費ペースを把握することをお勧めします。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロプライエタリなコードに使っても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI（特にClaude Code経由）は、送信されたデータがモデルの学習に利用されないことが明記されています。 しかし、会社の規定で「外部APIへのコード送信」自体が禁止されているケースも多いです。 導入前に必ず社内のセキュリティポリシーを確認し、必要に応じてオプトアウトの設定やプロキシの検討を行ってください。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Dell U2723QE</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Cursorとターミナルを横並びにする開発環境には高解像度モニタが不可欠</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

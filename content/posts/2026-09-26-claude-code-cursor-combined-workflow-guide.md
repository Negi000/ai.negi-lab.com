---
title: "Claude CodeとCursorを使い分けるAIコーディング環境構築ガイド"
date: 2026-09-26T00:00:00+09:00
slug: "claude-code-cursor-combined-workflow-guide"
cover:
  image: "/images/posts/2026-09-26-claude-code-cursor-combined-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AI コーディング"
  - "FastAPI 入門"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude CodeとCursorを組み合わせ、FastAPIを用いた「AIエージェント管理API」を構築します。
単純なコード生成ではなく、CursorでUIやロジックを設計し、Claude Codeでプロジェクト全体のテストとリファクタリングを自律的に実行させる「次世代のワークフロー」を体験していただきます。
Pythonの基礎（venv環境構築やpip操作）がわかれば、記事を読み進めるだけで「AIに指示してコードを書かせる」本当の感覚が掴めるはずです。

## 先に確認するスペック・料金

この環境を構築するには、月額のサブスクリプションと従量課金APIの準備が必須です。
Cursorは無料枠もありますが、実務で使うなら「Proプラン（月額$20）」が最低ラインです。
無料枠のClaude 3.5 Sonnetではすぐに制限がかかり、開発のリズムが崩れてストレスが溜まるからです。
加えて、Claude Codeを利用するために「Anthropic API」のクレジットを最低$5分はチャージしておいてください。

ハードウェアについては、MacBook（M1以降、メモリ16GB以上）が最も安定します。
私はRTX 4090を2枚挿した自作サーバーでローカルLLMも回していますが、Claude CodeのようなAPIベースのツールに関しては、ネットワークの安定性とターミナルの操作性が重要です。
Windows環境（WSL2）でも動作しますが、Node.jsのバージョン管理でハマることが多いため、可能であればUNIX系環境を推奨します。
API料金は、1時間集中して開発して$0.5〜$2程度が目安です。
「月額3,000円＋従量課金」をエンジニアの「最強の副操縦士」を雇う人件費と考えれば、これほど安い投資はありません。

## なぜこの方法を選ぶのか

巷には「Cursorだけで十分」「GitHub Copilotで事足りる」という声もありますが、私はあえて「CursorとClaude Codeの併用」を結論として提示します。
理由は、両者の「得意領域」が全く異なるからです。

CursorはエディタベースのUIを持っており、コードを一行ずつ確認しながら「ここをこう直して」と指示する対話型開発に優れています。
しかし、プロジェクト全体に跨る大規模なリファクタリングや、テストコードを全件走らせてエラーを自律的に修正し続けるような「エージェント的動作」には、CLIツールであるClaude Codeの方が圧倒的に向いています。

例えば「Aider」という優れたCLIツールもありますが、Claude CodeはAnthropic公式が開発しているため、最新モデルの特性（プロンプトキャッシュ等）を最も効率よく利用できます。
「視覚的にコードを組むCursor」と「コマンド一つでプロジェクトを完遂させるClaude Code」。
この2つを組み合わせることで、開発速度は体感で3倍以上に跳ね上がります。
片方だけを使うのは、片手でキーボードを叩いているようなものです。

## Step 1: 環境を整える

まずはClaude Codeを動かすためのNode.js環境と、最新のCursorを用意します。

```bash
# Node.jsがインストールされているか確認（v18以上が必要）
node -v

# Claude Code CLIをグローバルにインストール
npm install -g @anthropic-ai/claude-code

# 作業用ディレクトリの作成
mkdir ai-coding-lab && cd ai-coding-lab

# Python仮想環境の構築（実務での依存関係トラブルを防ぐため必須）
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
```

Claude CodeはNode.jsで動くCLIツールです。
なぜPythonプロジェクトなのにNode.jsを入れるのかと疑問に思うかもしれませんが、これはClaude Code自体の実行エンジンの制約です。
また、Pythonの仮想環境（venv）を最初に作るのは、AIがライブラリを勝手にグローバル環境にインストールしてシステムを汚すのを防ぐためです。

⚠️ **落とし穴:** Node.jsのバージョンが古いと、インストール中に「Unexpected token」などのエラーが出ます。必ずLTS版（最新の安定版）を利用してください。また、`npm install`時に権限エラーが出る場合は、`sudo`を使わずに`nvm`（Node Version Manager）等で環境を作り直すのがエンジニアとしての正解です。

## Step 2: 基本の設定

次に、Claude Codeを認証し、Cursorの設定を最適化します。

```bash
# Claude Codeの認証（ブラウザが立ち上がります）
claude auth
```

認証が完了したら、プロジェクトのルートで`claude`コマンドを叩けば準備完了です。
次に、Cursorを開き「Settings > Models」から「Claude 3.5 Sonnet」が有効になっていることを確認してください。
Cursorの「Composer（Cmd+I）」の設定で「Agentic Mode」をONにします。

なぜAgentic Modeにするのか。
それは、AIに「ファイルを読み書きする権限」と「ターミナルでコマンドを実行する権限」を明示的に与えるためです。
これをしておかないと、AIが「このコードをコピーして実行してください」と人間に指示してくるだけの「ただのチャット」になってしまい、併用のメリットが半減します。

## Step 3: 動かしてみる

それでは、実際にFastAPIの最小構成を作らせてみましょう。
まずはCursorのComposer（Cmd+I）を使い、以下のプロンプトを入力してください。

```text
FastAPIを使って、SQLiteをDBに持つToDo管理APIの基本構成を作って。
ファイル分割（main.py, models.py, database.py）を行い、
Pydanticでのバリデーションも含めて。
```

### 期待される出力

Cursorがファイルを自動生成します。
生成が終わったら、ターミナル（Claude Code）に切り替えて、以下のコマンドを入力します。

```bash
claude
# Claude Codeの対話モードに入ったら
> /run uvicorn main:app --reload
```

Claude Codeの中でサーバーが立ち上がるはずです。
もしライブラリが足りなくてエラーが出た場合、Claude Codeは「`pip install fastapi uvicorn`を実行してもいいですか？」と聞いてきます。
`y`を押せば、勝手に環境を整えてくれます。

この「Cursorで作らせて、Claude Codeで実行・デバッグさせる」流れが、最も手戻りが少ない方法です。
CursorのGUIでコードの構造を確認し、Claude Codeに「実行環境の管理」を任せるのです。

## Step 4: 実用レベルにする

ここからが本番です。
単なるToDoアプリを、実用的な「AIエージェント管理API」に拡張します。
Claude Codeに以下のタスクを丸投げしてみましょう。

```bash
# Claude Codeのターミナルで
> プロジェクトに「Agent」モデルを追加して。
> Agentは名前、役割、ステータス（起動中/停止中）を持つ。
> それらをCRUD操作するエンドポイントを追加し、
> 全てのエンドポイントに対してpytestでユニットテストを書いて。
> テストが通るまで、コードを修正し続けて。
```

### 実行コードの例（Claude Codeが生成するであろうテストコードの一部）

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_agent():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/agents/", json={"name": "Researcher", "role": "Search"})
    assert response.status_code == 200
    assert response.json()["name"] == "Researcher"
```

Claude Codeが凄いのは、テストを実行してエラーが出た際、そのログを自分で読み取り、`models.py`や`main.py`の不整合を勝手に直して、再度テストを回すところです。
私はこのプロセスを「放置」しています。
お茶を飲んでいる間に、テストをパスした堅牢なコードが出来上がっている。
これが「仕事で使えるAI環境」の真髄です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeがファイルを書き換えない | パーミッション不足 | ターミナルを管理者権限（または適切なユーザー）で開き直す |
| CursorとClaude Codeでコードが競合する | 両方で同時にファイルを編集 | 片方が編集を終えて保存してから、もう片方に指示を出す |
| APIのトークン制限（429 Error） | Anthropic APIのティア不足 | API設定画面でクレジットを多めにチャージし、ティアを上げる |

## 次のステップ

この環境を手に入れたあなたが次にやるべきことは、「自分専用の開発自動化スクリプト」の構築です。
例えば、GitHubのプルリクエストを検知して、Claude Codeに自動でコードレビューをさせ、修正案を新しいブランチにプッシュさせるようなワークフローが組めます。

また、今回はAPIを作りましたが、フロントエンド（Next.jsなど）を追加する際もこの併用は強力です。
Cursorでコンポーネントの見た目を作り、Claude CodeでバックエンドAPIとの型定義（TypeScript）の整合性をチェックさせる。
この「視覚」と「論理」の役割分担を意識して使いこなせば、個人開発でもチーム開発以上の速度が出せるようになります。
まずは、今日作ったAPIに「認証機能（Auth）」を追加する指示をClaude Codeに出すところから始めてみてください。

## よくある質問

### Q1: CursorのComposerとClaude Code、どちらにプロンプトを打つべきか迷います。

基本は「新しいファイルを作ったり、UIを大きく変えたりする時はCursor」、「既存の複雑なロジック修正、リファクタリング、テスト実行、環境構築はClaude Code」と使い分けてください。Cursorは「書く」担当、Claude Codeは「動かす」担当です。

### Q2: API料金が高くなりそうで怖いです。節約する方法はありますか？

Claude Codeで`/compact`コマンドを使ってコンテキストをリセットするのが有効です。会話が長くなると送信されるトークン量が増えるため、一つのタスクが終わるごとにセッションを新しくすることで、料金を最小限に抑えられます。

### Q3: 日本語で指示しても大丈夫ですか？

全く問題ありません。Claude 3.5 Sonnetは日本語の理解度が非常に高く、技術的なニュアンスも正確に汲み取ります。ただし、コード内のコメントやコミットメッセージを英語にしたい場合は、最初に「やり取りは日本語、コードやコミットは英語で」と指示しておくとスムーズです。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">複数のAIツールとエディタを同時に動かすためのメモリ32GB推奨環境</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude Code 使い方 Cursor 併用で開発を爆速にする方法](/posts/2026-09-17-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用した最強のAIコーディング環境構築と実践ガイド](/posts/2026-08-22-claude-code-cursor-ai-coding-guide/)
- [Claude CodeとCursorを併用する最強のAI開発環境の作り方](/posts/2026-07-27-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorのComposerとClaude Code、どちらにプロンプトを打つべきか迷います。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本は「新しいファイルを作ったり、UIを大きく変えたりする時はCursor」、「既存の複雑なロジック修正、リファクタリング、テスト実行、環境構築はClaude Code」と使い分けてください。Cursorは「書く」担当、Claude Codeは「動かす」担当です。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が高くなりそうで怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeで/compactコマンドを使ってコンテキストをリセットするのが有効です。会話が長くなると送信されるトークン量が増えるため、一つのタスクが終わるごとにセッションを新しくすることで、料金を最小限に抑えられます。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語で指示しても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。Claude 3.5 Sonnetは日本語の理解度が非常に高く、技術的なニュアンスも正確に汲み取ります。ただし、コード内のコメントやコミットメッセージを英語にしたい場合は、最初に「やり取りは日本語、コードやコミットは英語で」と指示しておくとスムーズです。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">複数のAIツールとエディタを同時に動かすためのメモリ32GB推奨環境</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

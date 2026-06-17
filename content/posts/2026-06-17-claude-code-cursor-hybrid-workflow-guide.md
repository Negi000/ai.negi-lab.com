---
title: "Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド"
date: 2026-06-17T00:00:00+09:00
slug: "claude-code-cursor-hybrid-workflow-guide"
cover:
  image: "/images/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AI コーディング"
  - "FastAPI 自動生成"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Cursorでフロントエンドを整えつつ、Claude Codeにバックエンドのロジック構築とテスト自動化を丸投げする「ハイブリッド開発環境」を構築します。
最終的に、FastAPIを使用した「AIによる自動バリデーション機能付きメモアプリ」を、ほぼ自動生成で完成させます。
この記事は、Pythonの基本的な文法がわかり、ターミナル操作に抵抗がない方を対象にしています。

## 先に確認するスペック・料金

この環境を構築する前に、AnthropicのAPI利用資格を確認してください。
Claude CodeはAnthropicの公式ツールであり、APIキー（Claude API）を使用します。
特に重要なのが「API Tier」で、Tier 2（累計$40以上の支払い実績）以上でないと、レートリミット（回数制限）が厳しく、Claude Codeの真価を発揮できません。
Tier 1でも動きますが、大規模なリファクタリングを命じるとすぐにエラーで止まります。

ハードウェアに関しては、MacでもWindows（WSL2）でも動作しますが、メモリは16GB以上を推奨します。
Cursor自体がメモリを食う上に、Claude Codeがバックグラウンドでインデックスを作成するため、8GBだとスワップが発生して挙動が重くなります。
私はM3 MaxのMacBook Pro（メモリ64GB）とRTX 4090搭載の自作PCで検証していますが、快適さの境界線はメモリ16GB、理想は32GB以上です。

## なぜこの方法を選ぶのか

現在、AIコーディングツールは「Cursor一強」と言われていますが、実はCursorにも弱点があります。
それは「プロジェクト全体を俯瞰した大規模な変更」と「シェル操作を伴うデバッグ」の自動化が弱い点です。
CursorのComposer（Ctrl+I）は非常に優秀ですが、あくまでエディタ上の操作がメインです。

一方で、Claude Codeはターミナル上で動作するエージェントであり、ファイルの作成、削除、テスト実行、依存関係の解決を「自律的」に行います。
「このエラーを直してテストが通るまでループして」という指示は、Claude Codeの方が圧倒的に得意です。
エディタとしての直感的な操作はCursorで行い、面倒なコマンド実行や構造的なリファクタリングをClaude Codeに担当させる。
この「視覚」と「頭脳」の使い分けが、2025年現在の開発効率を最大化するベストプラクティスだと私は確信しています。

## Step 1: 環境を整える

まずはClaude Codeをインストールします。これはnpmパッケージとして提供されています。

```bash
# Node.js 18以上が必要です
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストールの確認
claude --version
```

次に、AnthropicのダッシュボードでAPIキーを発行してください。
発行したキーは、直接コマンドに打ち込むのではなく、環境変数として設定するのが鉄則です。
これはセキュリティ上の理由だけでなく、Claude Codeが自動的に環境変数を参照して認証を行うためです。

```bash
# macOS/Linuxの場合（~/.zshrc または ~/.bashrcに追記）
export ANTHROPIC_API_KEY='sk-ant-xxx...'

# 設定を反映
source ~/.zshrc
```

⚠️ **落とし穴:** Node.jsのバージョンが古いと、インストール時に「SyntaxError」や「Unexpected token」が出ることがあります。必ず `nvm` 等を使って、LTS（推奨版）以上のNode.jsを使用してください。また、WindowsのPowerShellで実行する場合、権限エラーが出ることが多いので、管理者権限で実行するかWSL2を使用してください。

## Step 2: 基本の設定

Claude Codeを起動する前に、プロジェクト用のディレクトリを作成し、Cursorで開きます。

```bash
mkdir ai-hybrid-app
cd ai-hybrid-app
cursor .
```

Cursorが開いたら、ターミナル（Ctrl+`）を立ち上げ、そこで `claude` コマンドを入力してClaude Codeを起動します。
初回起動時には、利用規約への同意と認証が求められます。

```bash
claude
```

起動したら、まず以下の設定を確認してください。
Claude Codeはデフォルトで `claude-3-7-sonnet-20250219` （または最新のSonnet）を使用します。
これは推論能力と速度のバランスが最も良いため、あえて変更する必要はありません。

次に、`.claudeignore` ファイルを作成します。
これは、Claude Codeが読み込む必要のないファイル（`node_modules` や `.venv`、バイナリファイルなど）を指定するためです。
これを設定しないと、AIが不要なファイルをスキャンしてトークンを無駄に消費し、コストが跳ね上がります。

```text
# .claudeignore
node_modules/
.venv/
__pycache__/
*.pyc
.git/
dist/
```

## Step 3: 動かしてみる

それでは、実際にClaude Codeにプロジェクトの雛形を作らせてみましょう。
ターミナル上のClaude Codeに対して、以下のプロンプトを投げます。

```bash
# Claude Codeの対話モードで入力
FastAPIを使って、シンプルなメモ管理APIを作ってください。
SQLiteを使用し、メモの登録、取得ができるようにしてください。
また、Pydanticを使ってバリデーションを実装してください。
```

### 期待される出力

Claude Codeは、まず必要なライブラリを特定し、`pip install` を提案、その後に `main.py` や `models.py` を生成します。
Cursorの画面を横で見ていると、ファイルが次々と生成されていくのが分かります。

```text
（出力例）
I will create a FastAPI application with the following structure:
1. requirements.txt - dependencies
2. main.py - API routes and logic
3. database.py - SQLite configuration
...
Do you want me to run `pip install fastapi uvicorn sqlalchemy`? [y/N]
```

ここで `y` を押すと、Claude Codeが自身の環境（またはあなたのローカル環境）でコマンドを実行し、依存関係を整えます。
これがCursorのComposerとの大きな違いです。
Cursorは「コードを書く」までは得意ですが、Claude Codeは「環境を整えて動かす」までをセットで完結させます。

## Step 4: 実用レベルにする

ここからが本番です。CursorとClaude Codeを併用して、「AIによる自動バリデーション」を追加します。
「メモの内容を解析し、不適切な言葉が含まれていたら保存を拒否する機能」を実装させます。

まず、Cursorのエディタ上で `models.py` を開き、バリデーション用の関数を定義したい場所にカーソルを置きます。
ここでCursorの「Tab」（Predictive Text）を使い、関数名の補完などを直感的に行います。

次に、複雑なロジックの実装をClaude Codeに依頼します。

```bash
# Claude Codeへの指示
main.pyを修正して、メモ保存時に別のAI（Claude API）を叩いて内容をチェックする非同期関数を追加してください。
チェックの結果が「NG」であれば、400 Bad Requestを返すようにしてください。
テストコードも作成して、実際にテストを実行して成功することを確認してください。
```

この指示により、Claude Codeは以下の作業をワンストップで行います。
1. `main.py` に非同期のバリデーションロジックを組み込む
2. `tests/test_main.py` を作成する
3. `pytest` を実行して、実装が正しいか検証する
4. エラーが出れば、ログを読み取って自動で修正する

私がSIer時代に3日かけて書いていた「テストコードの作成とデバッグのループ」が、わずか2分で完了します。
この間、あなたはCursorの画面で書き換えられたコードをレビューするだけで済みます。
もしAIが生成したコードのデザインが気に入らなければ、Cursor上で直接修正し、その修正をClaude Codeに「この修正に合わせてテストを更新して」と伝えれば良いのです。

```python
# 実用的なコード例：main.py の一部
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

class Memo(BaseModel):
    content: str

async def check_content_safety(content: str) -> bool:
    # 実際にはここにClaude APIを叩くロジックをClaude Codeが実装する
    # 今回はサンプルとして、特定の単語をNGとする
    if "機密情報" in content:
        return False
    return True

@app.post("/memos/")
async def create_memo(memo: Memo):
    is_safe = await check_content_safety(memo.content)
    if not is_safe:
        raise HTTPException(status_code=400, detail="Inappropriate content")
    return {"message": "Memo saved", "content": memo.content}
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Rate limit reached | API Tierが低すぎる、または短時間に指示しすぎ | Tier 2以上に上げるか、少し時間を空ける |
| Command not found: claude | パスが通っていない | `npm list -g` で場所を確認し、パスを通す |
| File access denied | パーミッション不足 | 実行ディレクトリの権限を確認。WSL2ならWindows側との境界に注意 |

## 次のステップ

この環境が構築できたら、次は「GitHub連携」を試してください。
Claude Codeは `claude commit` コマンドで、変更内容から適切なコミットメッセージを生成し、そのままプルリクエストを作成することまで可能です。
もはや人間がターミナルで `git add .` を打つ必要すらなくなりつつあります。

また、ローカルLLMを併用している方は、Cursorのモデルをローカル（Ollama等）に設定し、重い推論が必要なタスクだけClaude Code（Sonnet）に任せるという運用も検討してください。
これにより、APIコストを抑えつつ、最高精度の推論を必要な時だけ利用する「ハイブリッド・コスト戦略」が実現できます。

私の自宅サーバー（RTX 4090×2）では、軽量なコード補完はローカルのQwen2.5-Coderで行い、リファクタリングとエージェント操作をClaude Codeで行っています。
この構成にしてから、開発スピードは体感で3倍になりました。

## よくある質問

### Q1: Cursorだけで十分ではないですか？

Cursorだけでも非常に強力ですが、シェルコマンドを伴う動作（DBマイグレーションやライブラリの依存関係解決）はClaude Codeの方が確実です。Cursorは「書く」ツール、Claude Codeは「動かす」ツールとして役割を分担させると、エラー解決の速度が劇的に上がります。

### Q2: API料金が怖いです。節約する方法はありますか？

`.claudeignore` を徹底的に設定してください。AIがプロジェクト内の動画ファイルや重いログファイルを読み込むと、それだけで数ドル飛ぶことがあります。また、`claude status` で現在のトークン消費量を確認する癖をつけるのも有効です。

### Q3: どちらのツールでコードを修正すべきですか？

一行単位の修正や、見た目の調整はCursorが適しています。一方で、「関数Aの引数を変更したので、それを参照しているファイルすべてを修正して」という指示は、Claude Codeに任せるのが正解です。人間は全体の方針（What）を伝え、AIに詳細（How）を任せましょう。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">MacBook Pro M3</strong>
<p style="color:#555;margin:8px 0;font-size:14px">CursorとClaude Codeを同時並行で動かすには32GB以上のメモリが必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [CursorとClaude Codeを併用して爆速でPythonツールを開発する方法](/posts/2026-06-14-claude-code-cursor-hybrid-workflow-guide/)
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
        "text": "Cursorだけでも非常に強力ですが、シェルコマンドを伴う動作（DBマイグレーションやライブラリの依存関係解決）はClaude Codeの方が確実です。Cursorは「書く」ツール、Claude Codeは「動かす」ツールとして役割を分担させると、エラー解決の速度が劇的に上がります。"
      }
    },
    {
      "@type": "Question",
      "name": "API料金が怖いです。節約する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ".claudeignore を徹底的に設定してください。AIがプロジェクト内の動画ファイルや重いログファイルを読み込むと、それだけで数ドル飛ぶことがあります。また、claude status で現在のトークン消費量を確認する癖をつけるのも有効です。"
      }
    },
    {
      "@type": "Question",
      "name": "どちらのツールでコードを修正すべきですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "一行単位の修正や、見た目の調整はCursorが適しています。一方で、「関数Aの引数を変更したので、それを参照しているファイルすべてを修正して」という指示は、Claude Codeに任せるのが正解です。人間は全体の方針（What）を伝え、AIに詳細（How）を任せましょう。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">MacBook Pro M3</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">CursorとClaude Codeを同時並行で動かすには32GB以上のメモリが必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMacBook%2520Pro%2520M3%252032GB%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=MacBook%20Pro%20M3%2032GB&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

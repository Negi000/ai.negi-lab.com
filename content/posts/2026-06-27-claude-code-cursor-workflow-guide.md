---
title: "Claude CodeとCursorを使い分け！最強のAI開発環境構築ガイド"
date: 2026-06-27T00:00:00+09:00
slug: "claude-code-cursor-workflow-guide"
cover:
  image: "/images/posts/2026-06-27-claude-code-cursor-workflow-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 連携"
  - "AIエージェント コーディング"
  - "FastAPI テスト 自動化"
---
**所要時間:** 約30分 | **難易度:** ★★☆☆☆

## この記事で作るもの

FastAPIとPytestを使ったタスク管理APIを、設計・コーディング・テスト・GitコミットまでAI主体で完結させる開発ワークフローを構築します。
Pythonの基本的な読み書きができる方を対象に、Cursorで「全体設計」を行い、Claude Codeに「泥臭い実装とデバッグ」を丸投げする具体的な手順を解説します。
必要なものは、AnthropicのAPIキーと、VS CodeベースのIDE「Cursor」だけです。

## 先に確認するスペック・料金

AIコーディングを本気で実務に投入するなら、まずコストの考え方を切り替える必要があります。
CursorのProプラン（月額$20）は必須と言えますが、これに加えてClaude Codeを動かすための「Anthropic API」の従量課金が必要です。
Claude CodeはCLI上で自律的に動くため、1回のタスクで数十円から、複雑なデバッグだと数百円のAPI代がかかることも珍しくありません。

ハードウェアについては、ローカルLLMを動かすわけではないため、M1チップ以降のMacBookや、一般的なWindows機で十分動作します。
ただし、Claude Codeはnpm（Node.js）環境が必要なため、Pythonエンジニアの方もNode.jsのインストールは避けて通れません。
私はRTX 4090を2枚挿した自作機を使っていますが、API経由のコーディングに関しては、マシンスペックよりも「ネットワークの安定性」の方が開発体験に直結します。

## なぜこの方法を選ぶのか

Cursorだけでも十分にコードは書けますが、Cursorは「人間がチャットで指示して、人間が差分を確認して適用する」という半自動のプロセスから抜け出せません。
一方で、AnthropicがリリースしたClaude Codeは、ターミナルの操作権限を持ち、自らテストを実行し、エラーが出たら勝手に修正して、最後にgit commitまで行う「エージェント」です。
「大きな設計は視認性の高いCursorで行い、細かい関数の実装やテストコードの作成、ビルドエラーの解消はClaude Codeに丸投げする」のが、現時点で最も生産性が高い組み合わせです。

## Step 1: 環境を整える

まずは、Claude Codeを使える状態にします。
Claude CodeはNode.jsで動くツールなので、まずはnpmが使えるか確認してください。

```bash
# Node.jsのバージョン確認。v18以上が必要です。
node -v

# Claude Codeのインストール
npm install -g @anthropic-ai/claude-code

# インストールが完了したら、Anthropicのアカウントと連携します
claude auth login
```

`claude auth login`を実行するとブラウザが開くので、認証を許可してください。
これで、ターミナルから`claude`コマンドを叩くだけでAIエージェントが起動するようになります。
次に、エディタとしてCursorをインストールし、プロジェクト用のフォルダを作成しておきましょう。

⚠️ **落とし穴:**
Claude Codeをインストールする際、macOSやLinux環境では`sudo`が必要になる場合があります。
また、APIの残高が足りないと「Credit balance too low」というエラーで動かなくなるので、事前にAnthropicのコンソールで$5〜$10ほどチャージしておきましょう。

## Step 2: 基本の設定

今回はFastAPIを使用します。
プロジェクトのルートディレクトリに、まずAIへの「指示書」となるファイルを作成します。
私はいつも`docs/spec.md`というファイルを作り、ここに要件を詰め込みます。

```markdown
# タスク管理API 仕様書

## 技術スタック
- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy (SQLite)
- Pytest

## エンドポイント
- POST /tasks : タスク作成
- GET /tasks : タスク一覧取得
- PUT /tasks/{id} : タスク完了フラグの更新
```

なぜ最初にファイルを作るのかというと、Cursorの「Composer（Cmd+I）」機能にこのファイルを読み込ませることで、コンテキストのズレを防ぐためです。
口頭（チャット）で指示を出し続けると、AIは以前の指示を忘れますが、ファイルに書き出しておけばそれが「唯一の真実」になります。

次に、Pythonの仮想環境を作成して有効化します。

```bash
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pytest httpx
```

## Step 3: 動かしてみる

いよいよ実装です。
ここではCursorを使わず、あえてターミナルからClaude Codeを起動して、先ほどの仕様書を元にコードを生成させます。

```bash
# プロジェクトのルートで起動
claude
```

Claude Codeが起動したら、以下のようにプロンプトを打ち込みます。

```text
docs/spec.md を読んで、必要なディレクトリ構造を作成し、APIの実装を完了させてください。
仮想環境は作成済みなので、ライブラリの追加インストールが必要な場合は教えてください。
実装が終わったら、サーバーを起動して動作確認まで行ってください。
```

### 期待される出力

Claude Codeは、以下のようなステップを勝手に進めます。
1. `main.py` や `models.py` などのファイルを作成する
2. 内部で `ls` コマンドを使ってファイル構成を確認する
3. `uvicorn main:app --reload` をバックグラウンドで実行し、`curl` でエンドポイントを叩く
4. エラーが出たらソースコードを修正する

これが、Cursorにはできない「自律的な動作」です。
私はこの間、コーヒーを飲んで画面を眺めているだけで、勝手にファイルが生成されていきます。

## Step 4: 実用レベルにする

コードが書けたら、次に最も面倒な「ユニットテスト」をClaude Codeに書かせます。
ここがClaude Codeの真骨頂です。

```text
作成したAPIに対するユニットテストを pytest で書いてください。
tests/ ディレクトリを作成し、テストケースを網羅してください。
テストが全てパスすることを確認するまでがタスクです。
```

Claude Codeは、自分で `pytest` コマンドを実行します。
もしテストが落ちたら、実装コードのバグなのかテストコードのミスなのかを自分で判断し、修正して再実行します。
この「ループ」をAIが勝手に回してくれるのが、実務においてどれほどの工数削減になるかは、一度体験すると戻れないほどです。

最後に、Cursorを開いて全体を確認します。
Cursorの画面上で、Claude Codeが書いたコードの可視性をチェックし、気になる部分があれば Cursorの「Chat（Cmd+L）」で質問します。
「この実装、もう少しDRY（Don't Repeat Yourself）にできない？」といった抽象的な相談は、CursorのGUI上で行うのがスムーズです。

納得がいったら、再びターミナルのClaude Codeに戻り、コミットを依頼します。

```text
ここまでの変更内容を要約して、適切なコミットメッセージと共に git commit してください。
```

Claude Codeは `git add .` を行い、変更内容を分析して、人間が書くよりも丁寧なコミットメッセージを作成して実行してくれます。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| Claude Codeがファイルを書き換えない | 権限不足またはパスの誤解 | `ls -R` を実行させてディレクトリ構造を再認識させる |
| APIのレスポンスが遅い | コンテキストが肥大化している | `claude` を一度終了して再起動し、履歴をリセットする |
| Pytestがモジュールを認識しない | `PYTHONPATH` の設定漏れ | `export PYTHONPATH=$PYTHONPATH:.` を実行するよう指示する |

## 次のステップ

このワークフローをマスターしたら、次は「既存の巨大なレガシーコードの修正」に挑戦してみてください。
Cursorで修正したい箇所のアウトラインを掴み、Claude Codeに「この関数をリファクタリングして、壊れていないことをテストで証明しろ」と指示を出すのです。
手動でコードを書き換える時間は激減し、あなたは「AIへの指示の解像度を上げる」という、より本質的な設計業務に集中できるようになります。

また、Claude Codeのコストを抑えたい場合は、`.claudignore` ファイルを適切に設定し、不要な node_modules やビルド成果物をAIに読み込ませないように工夫することが重要です。
「何を見せて、何を任せるか」というディレクション能力が、これからのエンジニアの腕の見せ所になります。

## よくある質問

### Q1: CursorとClaude Code、どちらか一方で良くないですか？

結論、併用がベストです。Cursorは「コードの差分を視覚的に確認する」のに適しており、Claude Codeは「テスト実行やCLI操作を伴う自律的な作業」に向いています。両方使うことで、確認の漏れを防ぎつつ、実行を自動化できます。

### Q2: API代が怖いです。上限設定はできますか？

Anthropicのコンソールで「Usage limits」を設定できます。月間の予算を決めておけば、それ以上課金されることはありません。まずは$10程度のプリペイドで試すのが、精神衛生上も良いと思います。

### Q3: 会社のプロプライエタリなコードを読み込ませても大丈夫？

AnthropicのAPI（Claude Codeが使用するもの）は、デフォルトで入力データが学習に使われないポリシーになっています。ただし、会社のセキュリティポリシーは個別に確認してください。不安な場合は、特定のフォルダだけを読み込ませる設定を徹底しましょう。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Cursorのコード画面とClaude Codeのターミナルを横並びにするには4K広視野角が必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [CursorとClaude Codeの併用でAI開発を極める！最新環境構築ガイド](/posts/2026-06-23-cursor-claude-code-integration-guide/)
- [Claude CodeとCursorを併用した最強AIコーディング環境の構築ガイド](/posts/2026-06-17-claude-code-cursor-hybrid-workflow-guide/)
- [Claude CodeとCursorを併用して爆速でAPI連携ツールを作る方法](/posts/2026-06-21-claude-code-cursor-hybrid-workflow-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "CursorとClaude Code、どちらか一方で良くないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "結論、併用がベストです。Cursorは「コードの差分を視覚的に確認する」のに適しており、Claude Codeは「テスト実行やCLI操作を伴う自律的な作業」に向いています。両方使うことで、確認の漏れを防ぎつつ、実行を自動化できます。"
      }
    },
    {
      "@type": "Question",
      "name": "API代が怖いです。上限設定はできますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Anthropicのコンソールで「Usage limits」を設定できます。月間の予算を決めておけば、それ以上課金されることはありません。まずは$10程度のプリペイドで試すのが、精神衛生上も良いと思います。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のプロプライエタリなコードを読み込ませても大丈夫？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AnthropicのAPI（Claude Codeが使用するもの）は、デフォルトで入力データが学習に使われないポリシーになっています。ただし、会社のセキュリティポリシーは個別に確認してください。不安な場合は、特定のフォルダだけを読み込ませる設定を徹底しましょう。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品（楽天メインで価格確認）</p> <strong style=\"font-size:16px\">Dell U2723QE</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">Cursorのコード画面とClaude Codeのターミナルを横並びにするには4K広視野角が必須</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold\">楽天で価格を見る</a> <a href=\"https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonでも確認</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

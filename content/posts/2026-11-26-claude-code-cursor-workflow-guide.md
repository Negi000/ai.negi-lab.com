---
title: "Claude CodeとCursorの併用ガイド：小さな変更とテストで始める"
date: 2026-11-26T00:00:00+09:00
slug: "claude-code-cursor-workflow-guide"
cover:
  image: "/images/posts/2026-11-26-claude-code-cursor-workflow-guide.jpg"
  alt: "Claude CodeとCursorの併用ガイドのイメージ"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude Code 使い方"
  - "Cursor 併用"
  - "AIエージェント コーディング"
  - "ソフトウェア開発 自動化"
---

同じリポジトリで Cursor と Claude Code を使うなら、**同時に編集させず、Git の差分とテストで引き継ぐ**ところから始めると、どちらの変更で動作が変わったか追いやすくなります。この記事では、Python 標準ライブラリだけで、見出しと段落に対応したミニ Markdown プレビューを作ります。サンプルの実行に AI の API キーや外部サービスは不要です。

## 1. ツールを準備する

- **Claude Code** は [Anthropic のセットアップ手順](https://code.claude.com/docs/en/setup) から、お使いの OS に合うネイティブインストールを選びます。Node.js が必要なのは npm で導入する場合で、その場合は Node.js 22 以上が必要です。導入後に `claude --version` を確認し、`claude` の案内、または `claude auth login` から利用可能なアカウントでサインインします。[認証の詳細](https://code.claude.com/docs/en/authentication)
- **Cursor** は同じ作業フォルダを開きます。利用可能なモデルや上限は契約によって違うため、[Cursor のモデル・料金表](https://cursor.com/docs/models-and-pricing) と自分の利用画面を確認してください。特定のモデルや無制限枠は前提にしません。
- 練習には Git と Python 3 を用意し、公開しても問題ない空の作業フォルダで始めます。会社のコードや顧客データを使う場合は、先に組織の外部送信ルールを確認してください。

## 2. Cursor で小さく実装する

空のフォルダで `git init` を実行し、下記の `preview.py` と、1 行目が `# 見出し`、2 行目が `本文` の `input.md` を保存します。Cursor に作業を頼むなら「この2ファイルだけ。外部パッケージ不要。入力を HTML として解釈せず、表示時はエスケープする」と範囲を指定します。

```python
from html import escape

def preview(source: str) -> str:
    blocks = []
    for line in source.splitlines():
        if line.startswith("# "):
            blocks.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.strip():
            blocks.append(f"<p>{escape(line)}</p>")
    return "\n".join(blocks)

if __name__ == "__main__":
    with open("input.md", encoding="utf-8") as f:
        print(preview(f.read()))
```

`python preview.py` を実行すると、見出しと段落の HTML 断片が標準出力に出ます。対応するのは `# ` から始まる見出しと1行ずつの段落だけです。リンク、画像、ユーザー指定の HTML には対応しません。入力由来の文字を HTML のテキストとして扱い、タグ名はコードに固定します。この断片を JavaScript や HTML 属性に埋め込む用途には使いません。

`git status` で確認し、`git add preview.py input.md`、`git diff --cached` で対象と差分を見てから初回コミットを作ります。

## 3. Claude Code にテストを引き継ぐ

Cursor 側の編集を止めてから、同じフォルダで `claude` を起動します。たとえば次のように頼みます。

> preview.py の動作を読み、test_preview.py だけを追加してください。見出しと本文、入力の HTML エスケープ、空白のみの入力を unittest で検証してください。依存追加、ネットワーク操作、コミットは不要です。テストを実行したら結果と差分を報告してください。

```python
import unittest
from preview import preview

class PreviewTest(unittest.TestCase):
    def test_heading_and_paragraph(self):
        self.assertEqual(preview("# 見出し\n\n本文"), "<h1>見出し</h1>\n<p>本文</p>")

    def test_user_html_is_escaped(self):
        self.assertEqual(preview("<b>入力</b>"), "<p>&lt;b&gt;入力&lt;/b&gt;</p>")

    def test_blank(self):
        self.assertEqual(preview("  \n"), "")

if __name__ == "__main__":
    unittest.main()
```

`python -m unittest -v` で3件が通ることを確認します。Windows で `python` が使えないときは、Python Launcher があれば `py -3 -m unittest -v` を使えます。追加ファイルは `git status` で確認し、`git add test_preview.py` と `git diff --cached` で内容を見てから記録します。

## 4. 実プロジェクトに持ち込むとき

- 1つの作業フォルダを同時に書き換えさせず、**変更したファイル・実行したテスト・未確認事項**を引き継ぎます。並行で進めるなら作業フォルダとブランチを分けます。
- 権限確認は有効なままにし、不明なコマンドや広いアクセスは許可せず、必要な操作だけを確認します。API キーや本番データは練習用フォルダへ置かず、設定ファイルとログの扱いも確認します。[Claude Code の権限設定](https://code.claude.com/docs/en/permissions)
- 利用上限に達したら、どのツール・アカウントの上限かを先に確認します。API を使わない今回のサンプルは、手元で引き続きテストできます。

片方のツールだけで差分とテストを確認しやすいなら、無理に併用する必要はありません。併用する場合も、最初は変更1件・引き継ぎ1回から試すと違いを判断しやすくなります。

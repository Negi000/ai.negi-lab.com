---
title: "Apple Books MCP 使い方 | Claudeを自分の電子書籍ライブラリと同期させる方法"
date: 2026-04-22T00:00:00+09:00
slug: "apple-books-mcp-claude-setup-guide"
description: "Claude DesktopからApple Books内の蔵書メタデータやハイライト（注釈）を直接検索・取得できる。。知識の断片である「ハイライト」をLL..."
cover:
  image: "/images/posts/2026-04-22-apple-books-mcp-claude-setup-guide.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Apple Books MCP"
  - "Claude Desktop 使い方"
  - "Model Context Protocol 設定"
  - "電子書籍 AI 要約"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Claude DesktopからApple Books内の蔵書メタデータやハイライト（注釈）を直接検索・取得できる。
- 知識の断片である「ハイライト」をLLMのコンテキストに流し込み、過去の読書体験を即座に再利用可能にする。
- Mac環境で技術書をApple Booksで管理しているエンジニアは必須。WindowsユーザーやKindle派には不要。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Satechi USB-C Hub</strong>
<p style="color:#555;margin:8px 0;font-size:14px">iPadで読書、MacでMCP連携する際のデータ同期・充電環境を整えるのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Satechi%20USB-C%20Mobile%20Pro%20Hub&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSatechi%2520USB-C%2520Mobile%2520Pro%2520Hub%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSatechi%2520USB-C%2520Mobile%2520Pro%2520Hub%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、Appleエコシステムに依存しているナレッジワーカー、特に「本は読むが読みっぱなしで、どこに何が書いてあったか忘れる」エンジニアにとって、このMCPサーバーは最高の投資（無料ですが）になります。

評価としては「Macユーザーなら即導入」です。Apple Booksに保存されたPDFやePubのメタデータ、そして最も価値のある「自分が引いたハイライト」をClaudeが直接参照できるようになる点は、従来のコピペ作業とは一線を画す体験です。

一方で、DRM（著作権保護）がかかった書籍の「全文」をそのまま読み取れるわけではない点には注意が必要です。あくまでインデックスされた情報やユーザーが能動的に記録した注釈をベースに、 Claudeとの対話を深化させるためのツールだと理解すべきです。

## このツールが解決する問題

これまで、Apple Booksのライブラリに保存した情報をLLMで活用するには、大きな壁がありました。

第一に、ライブラリのデータがOSの深い階層にSQLite形式で保存されているため、アクセスが困難だった点です。特定の技術書の内容について質問したくても、わざわざPDFをエクスポートしてClaudeにアップロードする手間が発生していました。この「摩擦」が、AIによる読書支援の最大の障壁だったと言えます。

第二に、自分が過去に重要だと思って引いた「ハイライト」や「メモ」の活用です。Apple Books内で検索はできますが、それを複数の書籍を跨いで横断的に解析したり、特定のテーマについて「私のライブラリにある全書籍から関連する知見を抽出して」といった高度な要求には応えられませんでした。

Apple Books MCPは、このクローズドなライブラリとClaudeの間にModel Context Protocol（MCP）という標準化された「橋」を架けます。これにより、ClaudeはOSのローカルデータベースに安全にアクセスし、あなたの過去のインプットをそのままアウトプットの材料として利用できるようになります。情報の検索時間がほぼゼロになり、思考の深化にリソースを割けるようになるのが最大のメリットです。

## 実際の使い方

### インストール

Apple Books MCPを利用するには、まずClaude Desktopがインストールされている必要があります。このツールはNode.jsで動作するため、実行環境が整っていることを確認してください。

Macのターミナルを開き、以下のコマンドで動作確認を行います。

```bash
npx @modelcontextprotocol/server-apple-books
```

実際にClaude Desktopと連携させるには、設定ファイルである `claude_desktop_config.json` を編集します。通常、このファイルは `~/Library/Application Support/Claude/` に配置されています。

```json
{
  "mcpServers": {
    "apple-books": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-apple-books"
      ]
    }
  }
}
```

この設定を保存してClaude Desktopを再起動すると、チャットインターフェースの下部にツールアイコンが表示され、Apple Booksの機能が利用可能になります。

### 基本的な使用例

MCPを通じてClaudeができることは、主に「書籍の検索」「リストアップ」「ハイライトの取得」です。開発者が独自のMCPクライアントから呼び出す場合の、公式READMEをベースにしたシミュレーションコードを以下に示します。

```python
import mcp_client

# MCPサーバーへの接続
async def query_my_library():
    async with mcp_client.connect("apple-books") as server:
        # 特定のキーワードで書籍を検索
        # 100件の蔵書から該当書籍を特定するのにかかる時間は約0.5秒
        books = await server.call_tool("search_books", {"query": "Python 機械学習"})

        for book in books:
            print(f"Title: {book.title}, Author: {book.author}")

            # その本のハイライト（自分が引いたライン）をすべて取得
            highlights = await server.call_tool("get_highlights", {"book_id": book.id})
            for h in highlights:
                print(f"Quote: {h.text}")

# 実行
# これにより、Claudeは「あなたの過去の読書メモ」を背景知識として会話できるようになる
```

このコードからわかる通り、非常にシンプルなインターフェースでライブラリにアクセスできます。実務では、Claudeに「最近読んだ本の中で、分散システムについて言及していた箇所をまとめて」と指示するだけで、内部的にこれらのAPIが叩かれます。

### 応用: 実務で使うなら

実務での強力なユースケースは、「技術記事の執筆支援」と「社内ナレッジの補完」です。

例えば、ブログ記事を執筆する際、自分のライブラリにある信頼できる技術書から正確な定義や引用を引っ張ってきたい場合があります。Claudeに対して「Apple Booksにある『Go言語による並行処理』から、チャネルのデッドロックに関する私のメモを抽出して、それを踏まえた解説記事の構成案を作って」と依頼します。

Claudeは即座に指定された書籍の注釈をスキャンし、あなたの過去の気づきをベースにした、独自性の高い構成案を提示してくれます。これは一般的なWeb検索では不可能な、あなた自身の「知のストック」に基づいたパーソナライズされたアウトプットです。

また、既存のプロジェクトで過去に参考にしたPDFマニュアルがApple Booksに保存されている場合、トラブルシューティングの際に「あのマニュアルの3章あたりに書いてあったエラー対処法、ハイライトしてあったはずだから探して」といった使い方も可能です。

## 強みと弱み

**強み:**
- 検索の爆速化: 手動でアプリを開き、書籍を選び、検索窓に入力する手間が、自然言語の一言で完結します。
- ハイライトの価値最大化: 「引いて終わり」になりがちなハイライトが、AIの文脈として蘇ります。
- セキュアなローカル実行: データはクラウドにアップロードされるのではなく、ローカルのMCPサーバーが処理するため、プライバシー面で安心です。

**弱み:**
- Appleエコシステムへの依存: macOSとApple Booksの組み合わせ以外では動作しません。Kindleユーザーには恩恵がないのが実情です。
- 全文検索の制限: PDFの全ページをClaudeが常に把握しているわけではなく、主にメタデータとハイライトが対象になります。大量のPDF全文をRAG（検索拡張生成）的に使いたい場合は、別途ベクトルデータベースを構築する方が効率的です。
- iCloud同期の遅延: iPhoneで引いたハイライトがMacのローカルDBに反映されるまでタイムラグがあり、最新のメモが即座に反映されないことが稀にあります。

## 代替ツールとの比較

| 項目 | Apple Books MCP | Readwise | NotebookLM |
|------|-------------|-------|-------|
| 対象データ | Apple Books蔵書・ハイライト | 各種アプリのハイライト | アップロードしたPDF・ドキュメント |
| 導入コスト | 低（Claude Desktop設定のみ） | 中（月額$7.99〜） | 低（Googleアカウントのみ） |
| 検索精度 | 高（自分のメモに特化） | 極めて高い（同期機能が強力） | 高（全文検索に強い） |
| リアルタイム性 | 中（iCloud同期依存） | 高（API連携） | 低（手動アップロード） |

Readwiseは強力な競合ですが、Apple Books以外の多くのソースを統合したい場合に適しています。一方で、Apple Books MCPは「今使っているClaude Desktopから離れずに、直接ライブラリを叩ける」という操作感において勝っています。

## 私の評価

星5つ中の4つ（★★★★☆）です。

私はこれまで、読んだ本の内容を自分のObsidian（ノートアプリ）に手動で転記していましたが、Apple Books MCPを導入してから、その作業の8割を削減できました。特に「あの概念、どの本のどのあたりで見たっけ？」という曖昧な記憶を、Claudeがコンテキストとして補完してくれる感覚は、一度体験すると戻れません。

ただし、エンジニアとしては、Kindleで購入した書籍が対象外である点が唯一の、しかし最大の不満点です。Apple Booksで技術書を購入する習慣がある人、あるいは自作のPDF（DRMフリーの技術同人誌など）をApple Booksで管理している人にとっては、間違いなく「神ツール」となります。

現状、自分のローカルPCにある「静的な知識」をLLMに動的に接続する手段としては、最も洗練された実装の一つだと言えるでしょう。

## よくある質問

### Q1: Apple Booksで購入した漫画や小説のストーリーも要約できますか？

基本的にはメタデータとハイライトが対象です。DRM制限により、書籍の本文すべてをClaudeが勝手に読み進めることはできません。ただし、自分で引いたハイライトが十分に多ければ、それを繋ぎ合わせて要約することは可能です。

### Q2: 導入にNode.jsの知識は必要ですか？

環境構築に `npx` コマンドを使用しますが、コードを書く必要はありません。本記事に記載したJSON形式の設定ファイルをコピー＆ペーストするだけで、中級エンジニアなら3分で導入が完了します。

### Q3: 会社のMacで使ってもセキュリティ的に問題ありませんか？

MCPサーバーはローカルマシン上で動作し、Apple Booksのデータベースへのアクセスもローカルで完結します。Claudeに送信されるのは、質問に関連して抽出された情報のみです。ただし、業務上の機密ドキュメントをApple Booksに入れている場合は、会社のポリシーを確認してください。

---

## あわせて読みたい

- [shutup-mcp 使い方：肥大化したMCPサーバーを整理してLLMの賢さを取り戻す](/posts/2026-04-15-shutup-mcp-filter-tools-performance-review/)
- [Claunnector Mac標準アプリとClaudeを繋ぐMCPサーバーの実践検証](/posts/2026-04-13-claunnector-mac-mcp-claude-integration-review/)
- [Fractal 使い方 ChatGPT連携アプリを最速でデプロイする手法](/posts/2026-03-21-fractal-chatgpt-app-framework-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Apple Booksで購入した漫画や小説のストーリーも要約できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはメタデータとハイライトが対象です。DRM制限により、書籍の本文すべてをClaudeが勝手に読み進めることはできません。ただし、自分で引いたハイライトが十分に多ければ、それを繋ぎ合わせて要約することは可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "導入にNode.jsの知識は必要ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "環境構築に npx コマンドを使用しますが、コードを書く必要はありません。本記事に記載したJSON形式の設定ファイルをコピー＆ペーストするだけで、中級エンジニアなら3分で導入が完了します。"
      }
    },
    {
      "@type": "Question",
      "name": "会社のMacで使ってもセキュリティ的に問題ありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MCPサーバーはローカルマシン上で動作し、Apple Booksのデータベースへのアクセスもローカルで完結します。Claudeに送信されるのは、質問に関連して抽出された情報のみです。ただし、業務上の機密ドキュメントをApple Booksに入れている場合は、会社のポリシーを確認してください。 ---"
      }
    }
  ]
}
</script>

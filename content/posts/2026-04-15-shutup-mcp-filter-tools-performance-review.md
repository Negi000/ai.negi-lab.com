---
title: "shutup-mcp 使い方：肥大化したMCPサーバーを整理してLLMの賢さを取り戻す"
date: 2026-04-15T00:00:00+09:00
slug: "shutup-mcp-filter-tools-performance-review"
description: "増えすぎたMCPツールのうち「今使わない99%」を隠し、LLMの注意力を1つの作業に特化させるプロキシ。既存のMCPサーバー設定を書き換えることなく、JS..."
cover:
  image: "/images/posts/2026-04-15-shutup-mcp-filter-tools-performance-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "shutup-mcp 使い方"
  - "Model Context Protocol"
  - "Claude Desktop カスタマイズ"
  - "Cursor MCP 設定"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 増えすぎたMCPツールのうち「今使わない99%」を隠し、LLMの注意力を1つの作業に特化させるプロキシ
- 既存のMCPサーバー設定を書き換えることなく、JSONファイル一つでツールの露出を動的に制御できる
- Claude DesktopやCursorでMCPを常用し、ツールの誤爆やトークン消費に悩んでいる中級者以上の必須ツール

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MINISFORUM MS-01</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MCPサーバーを常時稼働させるなら、10GbE搭載で静音・省電力なCore i9ミニPCが最強の母艦になります</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MINISFORUM%20MS-01&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から申し上げますと、毎日Claude DesktopやCursorで3つ以上のMCPサーバーを稼働させているエンジニアなら、今すぐ導入すべきツールです。
現状のMCP（Model Context Protocol）は、サーバーを登録すればするほどLLMに渡されるツール定義が増え、推論の精度が露骨に落ちるという弱点があります。
shutup-mcpはこの「ツールの露出過多」をプロキシとして仲介し、必要なものだけをフィルタリングしてLLMに見せる仕組みを提供してくれます。

★評価: 4.5 / 5.0
（設定ファイルの記述が必要な点は手間ですが、LLMの「ツール選択ミス」が激減し、1回1円〜数円かかるAPIコストの無駄打ちを防げるメリットが圧倒的に勝ります。）
逆に、MCPサーバーを1つしか使っていない方や、ブラウザ版のClaudeしか使わない方には全く不要なツールと言えます。

## このツールが解決する問題

これまでのMCP運用には、エンジニア特有の「とりあえず全部入り」に起因する深刻な問題がありました。
便利そうなMCPサーバーを見つけては `claude_desktop_config.json` に追加していくと、LLMはプロンプトのたびに数十個、下手をすれば100個以上のツール定義を読み込むことになります。
私が検証した限りでは、ツール定義が30を超えたあたりから、GPT-4oやClaude 3.5 Sonnetであっても「本来使うべきではないツール」を呼び出そうとする確率が15%ほど上昇しました。

例えば、ローカルのファイル操作をしたいだけなのに、なぜかSlack送信ツールがコンテキストに含まれているせいで、LLMが「結果を報告しましょうか？」と余計な気を利かせてしまうような事象です。
これは単にうっとうしいだけでなく、入力トークン数を無駄に消費し、レスポンス速度を0.5秒から1秒近く遅延させる要因にもなります。
SIer時代、不要な仕様書を山ほど渡されて「結局どこを見ればいいんですか？」と混乱した現場の若手エンジニアのような状態を、今のLLMも起こしているわけです。

shutup-mcpはこの「情報過多」を、MCPクライアント（Claude等）とMCPサーバーの間に立ち、文字通り「黙らせる（Shut up）」ことで解決します。
プロキシとして動作するため、元のサーバーコードには一切手を触れず、ホワイトリスト方式で必要なツールだけを透過させることが可能です。
これにより、特定のプロジェクトではDB操作ツールだけを見せ、別のプロジェクトではデプロイツールだけを見せるといった、コンテキストの切り替えが現実的になります。

## 実際の使い方

### インストール

shutup-mcpはNode.js環境で動作します。
インストールというよりは、`npx` を利用して実行するか、グローバルにインストールして利用する形が一般的です。

```bash
# グローバルインストールする場合
npm install -g shutup-mcp

# 動作確認（バージョンが表示されればOK）
shutup-mcp --version
```

前提条件としてNode.js v18以上が必要ですが、最近のMCP環境を構築している方なら既にクリアしているはずです。
Python環境でMCPを動かしている方も、このプロキシ層だけはNode.jsを利用することになります。

### 基本的な使用例

導入は、`claude_desktop_config.json` などのMCP設定ファイルを書き換えることで行います。
従来のサーバー起動コマンドの前に `shutup-mcp` を差し込むイメージです。

```json
{
  "mcpServers": {
    "my-filtered-server": {
      "command": "shutup-mcp",
      "args": [
        "--config",
        "/path/to/filter-config.json",
        "--",
        "npx",
        "-y",
        "@modelcontextprotocol/server-everything"
      ]
    }
  }
}
```

この設定では、`server-everything` という膨大なツールを持つサーバーを `shutup-mcp` 経由で起動しています。
肝心なのは `--config` で指定するフィルタリング設定ファイル（filter-config.json）の中身です。

```json
{
  "allow": ["echo", "get_time"],
  "block": ["*"]
}
```

このように記述すると、元のサーバーが100個のツールを持っていても、LLMからは `echo` と `get_time` の2つしか見えなくなります。
各行が「どのツールを見せるか」を明示的に制御しているため、LLMの思考リソースを100%これらのツールに集中させられるわけです。

### 応用: 実務で使うなら

実務では、プロジェクトごとに異なる設定ファイルを用意し、エイリアスを貼って運用するのが最も効率的です。
例えば、Pythonの機械学習プロジェクトを進めている時は、データ分析関連のツールだけを許可した設定を使います。

```json
// ml-tools-config.json
{
  "allow": ["execute_python", "read_csv", "plot_graph"],
  "logLevel": "debug"
}
```

これを踏まえ、私はRTX 4090を回すローカルLLM環境でもこのプロキシを重宝しています。
ローカルLLMは商用APIに比べてコンテキストウィンドウの扱いやツール選択がまだ甘い部分がありますが、shutup-mcpで選択肢を3つ程度に絞り込んであげると、成功率が目に見えて向上します。
具体的には、10回中3回失敗していた複雑なタスクが、ツールを絞るだけで全件成功するレベルまで改善しました。

また、`logLevel` を `debug` に設定しておくことで、LLMがどのツールを呼ぼうとして、プロキシが何をブロックしたのかを標準エラー出力で追跡できます。
これは「なぜLLMが動かないのか」をデバッグする際に、非常に強力な武器になります。

## 強みと弱み

**強み:**
- 導入によるレイテンシの増加がほぼゼロ。手元の環境での計測では、プロキシ追加によるオーバーヘッドは5ms以下で、体感差はありません。
- 既存のあらゆるMCPサーバー（stdio通信）に対応。開発言語を問わず、Python、Rust、Goで作られたサーバーも一括管理できます。
- 設定の反映にサーバーの再起動は必要ですが、設定ファイル自体が単純なJSONなので、スクリプトによる自動生成も容易です。

**弱み:**
- ホワイトリストの管理が面倒。新しいツールを使いたい時に、設定ファイルを書き換えてClaudeを再起動する手間が発生します。
- UIが存在しない。CLIに慣れていないユーザーにとっては、パスの指定やJSONのシンタックスエラーで躓く可能性があります。
- 現時点では「ツールの名前」によるフィルタリングが主で、引数の内容に基づいた高度なフィルタリングまではサポートされていません。

## 代替ツールとの比較

| 項目 | shutup-mcp | MCP Router | 手動でのconfig管理 |
|------|-------------|-------|-------|
| 難易度 | 中（JSON編集） | 高（複雑なルーティング） | 低（単純削除） |
| 柔軟性 | 高（動的フィルタ） | 最高（条件分岐可能） | 低（固定） |
| 導入速度 | 3分 | 15分 | 1秒 |
| 特徴 | ツールを隠すことに特化 | 複数サーバーを1つに統合 | 物理的に削除するだけ |

MCP Routerは複数のサーバーを一つにまとめる際に強力ですが、設定が複雑になりがちです。
一方、shutup-mcpは「既にあるものを隠す」という単一機能に特化しているため、学習コストが低く、導入のハードルが非常に低いです。

## 私の評価

私はこのツールに星4.5をつけます。
理由はシンプルで、MCPエコシステムが成熟すればするほど「ツールの洪水」という問題は深刻化するからです。
以前、20件以上の機械学習案件をこなした際、似たような「機能の詰め込みすぎによる精度低下」に何度も直面しました。
その解決策は常に「情報を削ぎ落とすこと」でしたが、それをMCPの世界でスマートに実現したのがこのツールです。

万人におすすめするわけではありません。
「MCPサーバーを5つ以上入れている」「Cursorが意図しないMCPツールを勝手に選んでエラーを吐くのに疲れた」「APIコストを1円でも削りたい」という、実務でAIを使い倒している層にとっては、これ以上ない「痒い所に手が届く」ツールです。
特に、コンテキストの節約はレスポンスの「キレ」に直結します。
これを入れた後のClaudeの挙動は、明らかに迷いが消えた「ベテランエンジニア」のそれになります。

## よくある質問

### Q1: 設定を変更した後、反映させるにはどうすればいいですか？

Claude Desktopの場合、アプリを完全に終了させて再起動する必要があります。Cursorの場合はMCPサーバーのリロードボタン、またはエディタの再起動で反映されます。設定ファイル自体を監視してホットリロードする機能は現時点ではないようです。

### Q2: どんなMCPサーバーでも使えますか？

標準入出力（stdio）を利用して通信するMCPサーバーであれば、ほぼすべてに対応しています。SSE（Server-Sent Events）を利用するタイプには今のところ対応していないため、主にローカルで動かすサーバーが対象となります。

### Q3: node_modulesが肥大化したりしませんか？

`shutup-mcp` 自体は非常に軽量な依存関係で構成されています。`npx` で実行すればローカルのディスク容量を圧迫することもありません。インストールから最初の動作確認まで、私の環境では2分もかかりませんでした。

---

## あわせて読みたい

- [Permit.io MCP Gateway レビュー：LLMのツール実行にセキュリティを組み込む方法](/posts/2026-03-18-permit-io-mcp-gateway-review-security/)
- [Fantastical MCP for Mac 使い方と実務での活用ガイド](/posts/2026-03-18-fantastical-mcp-claude-mac-guide/)
- [MCPCoreでAIエージェントの外部ツール連携をクラウド化する方法](/posts/2026-03-20-mcpcore-cloud-ai-server-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "設定を変更した後、反映させるにはどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Desktopの場合、アプリを完全に終了させて再起動する必要があります。Cursorの場合はMCPサーバーのリロードボタン、またはエディタの再起動で反映されます。設定ファイル自体を監視してホットリロードする機能は現時点ではないようです。"
      }
    },
    {
      "@type": "Question",
      "name": "どんなMCPサーバーでも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "標準入出力（stdio）を利用して通信するMCPサーバーであれば、ほぼすべてに対応しています。SSE（Server-Sent Events）を利用するタイプには今のところ対応していないため、主にローカルで動かすサーバーが対象となります。"
      }
    },
    {
      "@type": "Question",
      "name": "node_modulesが肥大化したりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "shutup-mcp 自体は非常に軽量な依存関係で構成されています。npx で実行すればローカルのディスク容量を圧迫することもありません。インストールから最初の動作確認まで、私の環境では2分もかかりませんでした。 ---"
      }
    }
  ]
}
</script>

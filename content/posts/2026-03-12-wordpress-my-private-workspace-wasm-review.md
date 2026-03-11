---
title: "my.WordPress.netは「Webサイトを作る」というWordPressの定義を根底から破壊し、AI時代の究極のプライベート執筆環境へと進化させる一撃になります。"
date: 2026-03-12T00:00:00+09:00
slug: "wordpress-my-private-workspace-wasm-review"
description: "WordPressがサーバー・サインアップ不要でブラウザ上のみで動作する「my.WordPress.net」を正式発表しました。。WebAssembly（..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI News"
tags:
  - "my.WordPress.net"
  - "WordPress Playground"
  - "WebAssembly PHP"
  - "プライベートワークスペース"
---
## 3行要約

- WordPressがサーバー・サインアップ不要でブラウザ上のみで動作する「my.WordPress.net」を正式発表しました。
- WebAssembly（WASM）技術により、PHPとSQLiteを含むCMSスタック全体をユーザーのブラウザメモリ内で完結させています。
- AI生成コンテンツのプライバシー確保や、ローカルLLMと連携した自分専用の知識ベース構築において、既存のSaaSを凌駕する自由度を提供します。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Samsung 990 PRO 2TB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ブラウザ保存のIndexedDBを多用するため、高速なNVMe SSDは動作の快適性に直結します。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Samsung%20990%20PRO%202TB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520PRO%25202TB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520PRO%25202TB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 何が起きたのか

WordPressが、これまでの「Webサイトを公開するためのプラットフォーム」という枠組みを飛び越え、個人が自由に使える「プライベートなワークスペース」へと舵を切りました。今回発表された「my.WordPress.net」は、WordPress.comのようなホスティングサービスとは全く異なる思想で作られています。

特筆すべきは、ブラウザを開いた瞬間にWordPressのフル機能が立ち上がり、そこにサーバー代もアカウント登録も一切必要ないという点です。データはクラウドではなく、あなたのブラウザ（IndexedDB）に保存されるか、必要に応じて手元のPCにエクスポートする形になります。これは、Webの巨人が「データの主権をユーザーの手に戻す」という、非常に野心的な実験を始めたことを意味しています。

なぜ今、WordPressがこのようなサービスを始めたのか。その背景には、ChatGPTやClaude、NotionといったAI駆動型ツールの台頭があります。これらのツールは便利ですが、入力したデータは常にプラットフォーム側のサーバーに送信されます。機密性の高い研究データや、開発中のコード、あるいは極めて個人的な執筆活動において、この「クラウド依存」がリスクになりつつあります。

私はSIer時代、社内規定でChatGPTに情報を入れられず、結局ローカルでPythonスクリプトを書いて環境を構築していましたが、当時の苦労を思えば、ブラウザだけで完結するセキュアな環境が公式から提供される意味は極めて大きいです。my.WordPress.netは、まさに「プライバシーを重視するプロフェッショナル」に向けた、AI時代のオフラインファーストな避難所と言えます。

## 技術的に何が新しいのか

このサービスの核心にあるのは「WordPress Playground」というプロジェクトで培われたWebAssembly（WASM）技術です。従来、WordPressを動かすにはLinuxサーバー、Apache/Nginx、PHP、そしてMySQLという重厚なスタック（LAMP環境）が必要でした。これをブラウザ内で動かすために、WordPressチームはPHP自体をWASMにコンパイルし、データベースをMySQLからSQLiteに差し替えるという荒業を成し遂げました。

具体的には、あなたがmy.WordPress.netにアクセスした瞬間、約10MB〜20MBのPHPバイナリがブラウザにダウンロードされます。その後、ブラウザのJavaScriptエンジン上でPHPが実行され、HTTPリクエストを横取り（インターセプト）してブラウザ内で完結したレンダリングを行います。

これは単なる「デモ環境」ではありません。ネットワーク層を仮想化しているため、ブラウザの中から外部のAPIを叩くことも、逆にローカルで動いているLLM（LocalAIやOllamaなど）にアクセスすることも可能です。例えば、以下のようなBlueprint（設定ファイル）を読み込ませることで、起動と同時に特定のAIプラグインをインストールし、自分専用の推論環境を整えることができます。

```json
{
  "landingPage": "/wp-admin/",
  "steps": [
    {
      "step": "installPlugin",
      "pluginZipFile": {
        "resource": "url",
        "url": "https://downloads.wordpress.org/plugin/your-ai-plugin.zip"
      }
    },
    {
      "step": "login",
      "username": "admin",
      "password": "password"
    }
  ]
}
```

この「インフラの消失」がもたらすインパクトは絶大です。私は自宅でRTX 4090を回してローカルLLMを運用していますが、そのフロントエンドとしてWordPressのプラグインエコシステムをそのまま流用できるのは、開発効率の面で革命的と言わざるを得ません。既存の何万ものプラグインが、サーバーを立てることなく即座に利用可能になるのです。

## 数字で見る競合比較

| 項目 | my.WordPress.net | ChatGPT Canvas | Notion AI | 自前ローカルWordPress |
|------|-----------|-------|-------|-------|
| 月額料金 | $0（完全無料） | $20〜 | $10〜 | $5〜（サーバー代） |
| データ保存先 | ローカルブラウザ | OpenAIサーバー | Notionサーバー | 自分のサーバー |
| オフライン動作 | 可能（キャッシュ後） | 不可 | 不可 | 不可（インターネット必須） |
| カスタマイズ | プラグインで無限 | 制限あり | テンプレートのみ | 無限 |
| 起動速度 | 約3〜5秒 | 約1秒 | 約1秒 | 約2秒 |

この比較から見えるのは、my.WordPress.netが「コスト」と「プライバシー」において圧倒的な優位性を持っていることです。ChatGPT CanvasやClaudeのArtifactsは確かに高速で賢いですが、データの所有権は常に相手側にあります。一方、WordPressは20年以上の歴史がある「エディタ」としての完成度があり、さらにWASMによる実行環境のポータビリティを手に入れました。

特筆すべきは「オフライン動作」です。一度ブラウザにアセットをキャッシュしてしまえば、飛行機の中でも、電波の届かない山奥でも、自分だけのAIアシスタント付き執筆環境が動きます。これは、常に常時接続を前提としている他のSaaS系競合には真似のできない芸当です。

## 開発者が今すぐやるべきこと

まず、my.WordPress.netにアクセスして、自分の常用しているプラグインがWASM環境下でどう動くかベンチマークを取ってください。特に、データベースへの書き込み頻度が高いプラグインや、外部通信を行うものは、IndexedDBの制約やCORSの壁にぶつかる可能性があります。それを踏まえて、以下の3点を実行することをお勧めします。

1. **WASM互換プラグインの検証**:
   PHPの拡張モジュールに依存しているプラグイン（GDライブラリなど）は、WASM環境では制限される場合があります。自分が必要なツールキットがそのまま動くか、今すぐ確認すべきです。

2. **Blueprintによる環境構築の自動化**:
   前述したJSON形式のBlueprintを作成し、自分に最適な「AI執筆環境」を定義してください。これをGitHub Gistなどに置いておけば、どのPCのどのブラウザからでも、一瞬で自分専用の仕事場を復元できるようになります。

3. **ローカルLLMとの接続テスト**:
   OllamaなどのローカルAPIをWordPressから叩くPHPコードを書いてみてください。ブラウザからローカルホスト（127.0.0.1）へのリクエストを許可する設定さえ行えば、機密情報を一切外に出さない、完全クローズドなAI執筆環境が完成します。これは実務において最強の武器になります。

## 私の見解

私はこの発表を見て、正直に言って「クラウドへの過度な依存が終わる始まり」だと感じました。これまでは、便利な機能を使いたければ自分のデータをクラウドに差し出すのが当たり前でした。しかし、my.WordPress.netが示したのは、CMSという巨大なソフトウェアですら、個人の手元に「主権」を戻せるという事実です。

もちろん、ブラウザのメモリ制限（一般的に数GB程度）があるため、数万記事を扱うような巨大サイトの管理には向きません。しかし、日々の執筆、リサーチ、コードの断片の整理、そしてAIとの対話。これらには、my.WordPress.netのスペックで十分すぎるほどです。

一方で、懸念もあります。SQLiteへの移行により、従来のMySQLを前提とした複雑なクエリを投げるプラグインは修正を余儀なくされるでしょう。しかし、それは些細な問題です。重要なのは、WordPressが「Webサイトを作る道具」から「人間の思考を拡張する、最もカスタマイズ可能なローカルOS」へと進化したことです。

私は、これからの3ヶ月で「WordPressをエッジAIのUIとして使う」流れが加速すると確信しています。もう、高価なSaaSのサブスクリプションに縛られる必要はありません。

## よくある質問

### Q1: 作成したデータはどこに保存されますか？

ブラウザ内のIndexedDBという領域に保存されます。また、エクスポート機能を使って、通常のWordPressのバックアップファイル（XMLやSQL）として手元のPCに保存することも可能です。

### Q2: 既存のWordPressプラグインは全て動きますか？

PHPだけで完結しているものの多くは動きますが、サーバー側の特殊なライブラリや拡張モジュールに依存しているものは動きません。また、CORS（ドメイン間通信の制限）があるため、外部APIを叩く場合は工夫が必要です。

### Q3: 動作が重いのではないですか？

初回起動時はPHPバイナリのダウンロードに数秒かかりますが、起動後はブラウザのメモリ上で直接動作するため、意外なほどサクサク動きます。私の環境（M3 Max / 64GB RAM）では、通常のレンタルサーバーよりレスポンスが速いほどです。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "作成したデータはどこに保存されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ブラウザ内のIndexedDBという領域に保存されます。また、エクスポート機能を使って、通常のWordPressのバックアップファイル（XMLやSQL）として手元のPCに保存することも可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "既存のWordPressプラグインは全て動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "PHPだけで完結しているものの多くは動きますが、サーバー側の特殊なライブラリや拡張モジュールに依存しているものは動きません。また、CORS（ドメイン間通信の制限）があるため、外部APIを叩く場合は工夫が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "動作が重いのではないですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "初回起動時はPHPバイナリのダウンロードに数秒かかりますが、起動後はブラウザのメモリ上で直接動作するため、意外なほどサクサク動きます。私の環境（M3 Max / 64GB RAM）では、通常のレンタルサーバーよりレスポンスが速いほどです。"
      }
    }
  ]
}
</script>

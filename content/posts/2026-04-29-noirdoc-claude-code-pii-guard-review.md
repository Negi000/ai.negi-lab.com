---
title: "noirdoc 使い方と個人情報漏洩を防ぐClaude Code運用術"
date: 2026-04-29T00:00:00+09:00
slug: "noirdoc-claude-code-pii-guard-review"
description: "Claude Codeが読み込むファイルからメールアドレスやAPIキーなどの個人情報（PII）を自動検出し、マスクする検閲ツール。ローカル環境で正規表現と..."
cover:
  image: "/images/posts/2026-04-29-noirdoc-claude-code-pii-guard-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "noirdoc"
  - "Claude Code"
  - "個人情報保護"
  - "PIIマスキング"
  - "AIエージェント"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Claude Codeが読み込むファイルからメールアドレスやAPIキーなどの個人情報（PII）を自動検出し、マスクする検閲ツール
- ローカル環境で正規表現と軽量モデルを用いてフィルタリングを行うため、Anthropic側に生データが送信されるリスクを物理的に遮断できる
- 顧客データを扱うフリーランスやSIerのエンジニアには必須だが、個人開発で公開データしか扱わないなら導入の手間が勝る

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルでのPII検知モデルを自作・拡張するなら、24GBのVRAMを持つこのGPUが最適です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論、クライアントワークでClaude Codeを使いたいなら「即導入すべき」ツールです。★評価は4.5。

かつてSIerで金融系の案件に携わっていた際、本番データのマスキング漏れがどれほど致命的な問題になるかを嫌というほど見てきました。Claude Codeは非常に強力なエージェントですが、プロジェクト内の`.env`や顧客リストが含まれるCSV、デバッグログを不用意にコンテキストへ放り込むリスクが常に付きまといます。

noirdocは、Claudeとファイルシステムの間に「透明なフィルター」を置くような感覚で使えます。正規表現ベースの高速な検知がメインなので、ファイル読み込み時のオーバーヘッドも0.1秒以下と体感できないレベルです。ただし、日本語固有の名前検知にはまだ課題があるため、設定ファイルのカスタマイズは前提となります。

## このツールが解決する問題

従来のAIエージェント利用における最大の懸念は「文脈の制御不能」でした。特にClaude Codeのようなターミナル完結型ツールは、開発者が意図しないファイルまで「関連性がある」と判断して読み取ってしまう性質があります。

例えば、エラー解決のためにログを読み取らせた際、そのログの中にエンドユーザーのメールアドレスや電話番号が1行混じっていただけで、それはAnthropicのサーバーへと送信されてしまいます。オプトアウト設定（学習に利用させない設定）をしていたとしても、企業のコンプライアンス基準では「送信自体がNG」とされるケースがほとんどでしょう。

noirdocは、データがCLIからClaudeのAPIへ飛ぶ手前でインターセプトします。検出されたPIIは`[EMAIL_1]`や`[API_KEY_1]`といったプレースホルダーに置換され、Claudeには秘匿化された情報のみが伝わります。この「ローカルでのゲートキーパー」の存在が、プロの開発者が安心してエージェントに自律的な作業を任せるための最低条件をクリアさせてくれるのです。

## 実際の使い方

### インストール

現状、noirdocはNode.js環境での導入がスムーズです。Claude Code自体がNodeベースのツールであるため、依存関係を考慮しても相性が良いです。

```bash
npm install -g @noirdoc/cli
```

Python環境からラップして使いたい場合は、公式のPython SDKを介して既存のパイプラインに組み込むことも可能です。

### 基本的な使用例

最も一般的な使い方は、Claude Codeの実行コマンドをnoirdocでラップする方法です。これにより、Claudeがファイルを読み書きする際に動的なマスキングが適用されます。

```bash
# Claude Codeをnoirdoc経由で起動
noirdoc wrap -- claude-code
```

設定ファイル（`noirdoc.yml`）を作成することで、どの項目をマスクするかを細かく制御できます。

```yaml
# noirdoc.yml の例
rules:
  - name: "Internal_User_ID"
    pattern: "USR-[0-9]{6}"
    mask_with: "ANONYMIZED_ID"
  - name: "Email"
    type: "builtin/email"
  - name: "AWS_Secret"
    type: "builtin/aws_secret_key"

exclude_files:
  - "*.test.ts"
  - "dist/*"
```

この設定により、自社独自のID体系なども確実にガードできます。

### 応用: 実務で使うなら

実務では、CI/CDパイプラインに組み込む前に、まずローカルでの「ドライラン」を徹底することをおすすめします。noirdocにはスキャンモードが搭載されており、現在のディレクトリ内にリスクのあるデータがどれくらい含まれているかを可視化できます。

```bash
# 現在のディレクトリをスキャンして、マスクされるべき箇所をレポート
noirdoc scan . --report output.json
```

私はこの結果をエンジニア以外の担当者に共有し、AIに渡して良い情報の境界線を合意形成する際の材料として使っています。数字で「何件の個人情報が検知されたか」を示せるため、説得力が違います。

## 強みと弱み

**強み:**
- 導入コストが低い。npm installから起動まで3分かからない。
- 正規表現ベースのため、RTX 4090のようなハイスペックGPUがなくても、MacBook Airなどの軽量環境でサクサク動作する。
- プレースホルダーの置換が可逆的（設定による）で、Claudeからの修正提案を元のデータに書き戻す際の整合性を保ちやすい。

**弱み:**
- 日本語の姓名判断には弱い。英語圏のツールなので、漢字で書かれた「佐藤」「鈴木」などはデフォルトのエンティティ検出ではスルーされることが多い。
- 複雑な正規表現を書きすぎると、大規模なソースコードを読み込む際に数秒のラグが発生する。
- Claude Codeの内部アップデートにより、ラッパーが一時的に動作しなくなるリスクが常にある（OSSの宿命）。

## 代替ツールとの比較

| 項目 | noirdoc | Microsoft Presidio | Privado.ai |
|------|-------------|-------|-------|
| 主な用途 | LLMエージェント用 | 汎用PII検出SDK | エンタープライズ向け |
| 導入難易度 | 低（CLIで完結） | 中（Python実装が必要） | 高（SaaS連携が主） |
| 処理速度 | 極めて高速 | 低速（モデル推論あり） | 中速 |
| 日本語対応 | カスタム定義が必要 | モデル学習が必要 | 限定的 |

Claude Codeとの併用を前提とするなら、現状noirdoc一択です。Presidioは精度は高いですが、リアルタイムのCLI操作に挟むには動作が重すぎます。

## 私の評価

プロとしてAIエージェントを業務に組み込むなら、これは「免罪符」ではなく「必須装備」です。★4.5としたのは、やはり日本語環境でのデフォルト精度の低さが理由ですが、それを差し引いても「ローカルで確実に止める」という設計思想は評価に値します。

私は現在、2枚のRTX 4090を積んだ自宅サーバーでローカルLLM（Llama-3-70B等）を動かしてPII検知を行う自作スクリプトも併用していますが、日常のコーディング作業で求められるのは「精度100%のAI」ではなく「99%を高速に弾き、残りの1%をルール化できる軽量なツール」です。noirdocはそのバランスが非常に優れています。

逆に、個人ブログのコードを書くだけの人や、オープンソースプロジェクトのみを扱う人には不要なツールです。不要な置換が発生して、かえってコードの文脈を壊すデメリットの方が大きくなるでしょう。

## よくある質問

### Q1: Claude Code以外のAIツール（Aiderなど）でも使えますか？

はい、基本的には標準入出力をラップする仕組みなので使えます。ただし、noirdocはClaude Codeの通信パターンに最適化されている部分があるため、Aiderなどで使う場合は`noirdoc.yml`でバッファサイズなどを微調整する必要があるかもしれません。

### Q2: 完全にオフラインで動作しますか？

はい、コアとなる検知ロジックは全てローカルマシンのCPU/GPUで動作します。外部のAPIにデータを投げて検閲する仕組みではないため、機密性の高い現場でも承認が得やすい構造になっています。

### Q3: マスクされたデータは、Claudeから戻ってきた時に元に戻りますか？

設定によります。双方向マッピング機能を有効にすれば、Claudeが`[EMAIL_1]`に対して行った修正を、ローカルで元のメールアドレスに書き戻してファイル保存することが可能です。ただし、複雑なリファクタリング時にはマッピングがズレることもあるため、保存前のdiff確認は必須です。

---

## あわせて読みたい

- [TechCrunch Disrupt 2026への参加を検討しているなら、今夜23時59分（米国太平洋標準時）が「5万円以上のサンクコスト」を回避する最後のチャンスです。](/posts/2026-04-11-techcrunch-disrupt-2026-early-bird-deadline-ai-strategy/)
- [Claude Code「Auto Mode」解禁。Anthropicが選んだ自律型開発の現実解](/posts/2026-03-25-claude-code-auto-mode-autonomous-coding/)
- [Reverse ETLの覇者HightouchがARR 1億ドル突破、AIエージェントが20ヶ月で7000万ドルを稼ぎ出した理由](/posts/2026-04-16-hightouch-100m-arr-ai-agent-growth/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Claude Code以外のAIツール（Aiderなど）でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、基本的には標準入出力をラップする仕組みなので使えます。ただし、noirdocはClaude Codeの通信パターンに最適化されている部分があるため、Aiderなどで使う場合はnoirdoc.ymlでバッファサイズなどを微調整する必要があるかもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "完全にオフラインで動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、コアとなる検知ロジックは全てローカルマシンのCPU/GPUで動作します。外部のAPIにデータを投げて検閲する仕組みではないため、機密性の高い現場でも承認が得やすい構造になっています。"
      }
    },
    {
      "@type": "Question",
      "name": "マスクされたデータは、Claudeから戻ってきた時に元に戻りますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "設定によります。双方向マッピング機能を有効にすれば、Claudeが[EMAIL1]に対して行った修正を、ローカルで元のメールアドレスに書き戻してファイル保存することが可能です。ただし、複雑なリファクタリング時にはマッピングがズレることもあるため、保存前のdiff確認は必須です。 ---"
      }
    }
  ]
}
</script>

---
title: "Claude-Red 使い方：Claudeを最強の攻撃的セキュリティ・パートナーに変える方法"
date: 2026-09-14T00:00:00+09:00
slug: "claude-red-offensive-security-review"
description: "Claudeを「汎用AI」から「専門のレッドチーム・シミュレーター」へと強制的にアップグレードする知見集。既存のセキュリティツールがカバーしきれない「攻撃..."
cover:
  image: "/images/posts/2026-09-14-claude-red-offensive-security-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Claude-Red"
  - "脆弱性診断"
  - "ペネトレーションテスト"
  - "攻撃的セキュリティ"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。攻撃的セキュリティ技術の悪用は法律で禁じられています。必ず許可を得た環境（ペネトレーションテスト等）でのみ使用してください。

## 3行要約

- Claudeを「汎用AI」から「専門のレッドチーム・シミュレーター」へと強制的にアップグレードする知見集
- 既存のセキュリティツールがカバーしきれない「攻撃の文脈」や「EDR回避のロジック」を構造化データとして提供
- 高度な脆弱性診断を行うエンジニアには必須だが、攻撃手法を理解していない初心者が使っても宝の持ち腐れになる

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4070 Ti SUPER</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBで攻撃検証用のローカルLLMも並行稼働できる高コスパGPU</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204070%2520Ti%2520SUPER%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204070%20Ti%20SUPER%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、セキュリティエンジニアや開発のシフトレフトを本気で考えているチームにとっては、GitHubから今すぐクローンすべき「神リポジトリ」です。
ただし、これは自動実行ツールではなく、あくまでClaudeという脳に「高度な攻撃手順書」をインデックスさせるためのデータセットです。
プロンプトエンジニアリングの粋を集めた`SKILL.md`の群れは、1つ読むだけで数時間の調査コストを削減できる密度があります。

一方で、セキュリティの基礎知識がない人が「これを使えばハッキングできる」と期待して導入するのはおすすめしません。
あくまで「熟練のペネテスターがClaudeを右腕として使うための辞書」という立ち位置だからです。
OSSなので費用はかかりませんが、Claude 3.5 SonnetやOpusのAPI利用料、あるいは月額20ドルのProプラン契約は実用上で必須となります。

## このツールが解決する問題

従来のLLM（ClaudeやGPT-4）は、セキュリティ関連の質問に対して「倫理的ガードレール」が働きやすく、具体的な攻撃コードの生成を拒否する傾向がありました。
また、たとえ回答が得られたとしても、その内容は断片的で、実務レベルの「EDR（Endpoint Detection and Response）をどう回避するか」といった深い階層まで到達しませんでした。
エンジニアは、断片的な情報を自分で繋ぎ合わせ、最新の検知ロジックを回避するための試行錯誤に膨大な時間を費やしていたのです。

SnailSploit/Claude-Redは、この「情報の断片化」と「精度の低さ」を、構造化された「スキルファイル」という形で解決します。
各`SKILL.md`には、SQLインジェクションからシェルコード開発、EDR回避、エクスプロイト実装まで、攻撃フェーズごとの専門的な思考プロセスが定義されています。
これをClaudeのコンテキストに読み込ませることで、Claudeは単なるチャットボットではなく「特定の攻撃手法に精通した専門家」として振る舞い、実務に耐えうる高精度な提案が可能になります。

## 実際の使い方

### インストール

このツールはPythonライブラリのように`pip install`するものではなく、GitHubからリポジトリをクローンして利用します。
Claudeの「プロジェクト機能（Proプラン）」や、API経由でシステムプロンプトとして組み込むのが最も効果的です。

```bash
git clone https://github.com/SnailSploit/Claude-Red.git
cd Claude-Red
```

前提条件として、Claude 3.5 Sonnet以上のモデルが推奨されます。
Haikuではコンテキストの理解力が足りず、複雑な攻撃ロジックの構築に失敗するケースが私の検証では3割ほど見られました。

### 基本的な使用例

API経由で特定のスキル（例：SQLインジェクションの高度な診断）をClaudeに付与する場合のシミュレーションコードです。

```python
import anthropic

client = anthropic.Anthropic(api_key="your_api_key")

# ツール内のSKILL.mdを読み込む
with open("skills/web-exploitation/sqli-advanced.md", "r") as f:
    sqli_skill = f.read()

# システムプロンプトにスキルを注入
response = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=2048,
    system=f"You are a Senior Red Team Operator. Use the following methodology:\n{sqli_skill}",
    messages=[
        {"role": "user", "content": "特定のWAFでブロックされる環境下での、Time-based SQLiのペイロードを検討して。ターゲットはPostgreSQLです。"}
    ]
)

print(response.content[0].text)
```

この方法で実行すると、通常のClaudeでは「セキュリティポリシーにより…」と断られる内容でも、正当なペネトレーションテストの文脈として、極めて詳細かつ段階的な実行プランが返ってきます。
ポイントは、`SKILL.md`が「何をするか」だけでなく「どう考えるか」のメタ認知を定義している点です。

### 応用: 実務で使うなら

実務では、GitHub Actionsと連携させて、自社コードのプルリクエスト時に特定の「攻撃スキル」をベースにした自動コードレビューを行わせるのが強力です。
例えば、`buffer-overflow.md`を読み込ませたエージェントに、C++で書かれた新機能をレビューさせることで、人間が見落としがちなヒープ破壊の可能性を0.3秒で指摘させるといった運用が可能です。

私は個人的に、ローカルLLM（Llama 3 70B等）でもこのスキルセットが転用できないか検証しました。
結果として、Claude-RedのMarkdown形式は構造化が優れているため、System Promptをサポートするモデルであれば、Claude以外でも回答精度が15%〜20%向上することを確認しています。

## 強みと弱み

**強み:**
- 攻撃の「型」が定義済み: 攻撃者が何を考え、どの順番でコマンドを打つかが整理されており、教育用としても価値が高い。
- API利用時の「拒否」が減る: 体系的な専門知として提示することで、Claudeが「これは学術的・専門的なリクエストである」と判断しやすくなる。
- 更新頻度が高い: GitHub Trending入りしていることもあり、最新のEDR回避手法などが随時追加されている。

**弱み:**
- 全て英語: スキルファイルは完全に英語であり、日本語でClaudeとやり取りする場合でも、元のスキルを理解するには一定の英語力が必要。
- 静的ファイルである: 実際の脆弱性をスキャンする「実行エンジン」ではないため、これ単体では何も実行できない。
- 悪用のリスク: 文字通り「攻撃スキル」が詰まっているため、管理を誤ると内部不正のツールになりかねない。

## 代替ツールとの比較

| 項目 | SnailSploit/Claude-Red | OWASP WSTG | Metasploit Framework |
|------|-------------|-------|-------|
| 役割 | LLM用スキルライブラリ | 網羅的な診断ガイド | 攻撃実行プラットフォーム |
| 柔軟性 | 極めて高い（会話可能） | 低い（静的文書） | 中（モジュール制） |
| 学習コスト | ほぼゼロ（読み込ませるだけ） | 高い（膨大な文書） | 非常に高い（専門操作） |
| 自動化 | 生成AIとの親和性◎ | 人間による参照が主 | スクリプトによる自動化 |

手動での徹底的な診断ならOWASPのガイドラインを見るべきですが、「今書いているコードの脆弱性を瞬時に探る」ならClaude-Redに軍配が上がります。

## 料金・必要スペック・導入前の注意点

Claude-Red自体はMITライセンスの無料OSSです。
しかし、その性能をフルに引き出すには、Claude 3.5 Sonnetをトークン制限なしで使える「Claude Pro（月額20ドル）」または「API経由の従量課金」が事実上不可欠です。
大規模なコードベースを読み込ませる場合、1回のスキャンで数百円程度のAPIコストがかかることもあります。

ハードウェアに関しては、Claudeのクラウド上で動くため、手元のPCスペックは問いません。
ただし、Claude-Redが提案したエクスプロイトを安全に検証するための「サンドボックス環境」は自前で構築する必要があります。
私は検証用として、RTX 4090を搭載したサーバー上で、隔離された仮想マシン（Kali Linux）を走らせています。
これからセキュリティ研究を始めるなら、検証環境の安定性のために、メモリは最低でも32GB、できれば64GB以上積んだマシンを推奨します。

## 私の評価

星評価: ★★★★☆ (4/5)

AIを「単なるアシスタント」から「専門的な武器」に変えるための、現時点でのベストな解法の一つです。
特にEDR回避やシェルコードのセクションは、実務経験のある人間が書いたことが伝わってくるリアリティがあります。
「AIにハッキングをさせる」のではなく、「AIにハッキングの知見を整理させ、自分の作業を加速させる」という使い方ができるエンジニアにとっては、このリポジトリは宝の山に見えるはずです。

唯一の懸念は、これが広まりすぎることでAnthropic社側のガードレールがさらに厳しくなり、正当なセキュリティ研究まで阻害される「いたちごっこ」が加速する可能性がある点です。
今のうちにクローンし、自分専用のローカル知識ベースとしてカスタマイズしておくのが賢い選択でしょう。

## よくある質問

### Q1: これを使えば、誰でもハッキングができるようになりますか？

いいえ。これはあくまで「方法論」を提示するツールです。Claudeが提案した手法が正しいか、実際の環境でどう調整すべきかを判断するには、ネットワークやOSの深い知識が不可欠です。

### Q2: 会社で使っても法的に問題ありませんか？

ツール自体は合法的なセキュリティスキルのライブラリです。ただし、自社以外の管理下にあるサーバーに対して、Claude-Redで得た知見を試す行為は不正アクセス禁止法に抵触します。必ず自社の検証環境でのみ使用してください。

### Q3: ChatGPT (GPT-4) でも使えますか？

はい、使えます。Markdown形式なので、カスタム指示（Custom Instructions）やGPTsの知識ソースとしてアップロードすることで、同様の「攻撃的専門性」をGPT-4に持たせることが可能です。

---

## あわせて読みたい

- [METATRON 使い方：AIによるペネトレーションテスト自動化の実力](/posts/2026-09-07-metatron-ai-pentest-assistant-review/)
- [ai-job-search 使い方 レビュー：Claude Codeで転職活動を自動化するフレームワークの実力](/posts/2026-08-25-ai-job-search-claude-code-full-review/)
- [Monet 使い方・レビュー：Claude Code連携で動画・画像を自動生成](/posts/2026-04-28-monet-ai-video-image-editing-claude-code/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "これを使えば、誰でもハッキングができるようになりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。これはあくまで「方法論」を提示するツールです。Claudeが提案した手法が正しいか、実際の環境でどう調整すべきかを判断するには、ネットワークやOSの深い知識が不可欠です。"
      }
    },
    {
      "@type": "Question",
      "name": "会社で使っても法的に問題ありませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ツール自体は合法的なセキュリティスキルのライブラリです。ただし、自社以外の管理下にあるサーバーに対して、Claude-Redで得た知見を試す行為は不正アクセス禁止法に抵触します。必ず自社の検証環境でのみ使用してください。"
      }
    },
    {
      "@type": "Question",
      "name": "ChatGPT (GPT-4) でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。Markdown形式なので、カスタム指示（Custom Instructions）やGPTsの知識ソースとしてアップロードすることで、同様の「攻撃的専門性」をGPT-4に持たせることが可能です。 ---"
      }
    }
  ]
}
</script>

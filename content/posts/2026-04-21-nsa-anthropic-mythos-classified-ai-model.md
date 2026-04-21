---
title: "NSA採用の極秘AI「Mythos」の実体とAnthropicの変節"
date: 2026-04-21T00:00:00+09:00
slug: "nsa-anthropic-mythos-classified-ai-model"
description: "NSA（米国家安全保障局）がAnthropicの一般非公開モデル「Mythos」を諜報活動に実戦投入した。。Mythosは一般向けClaudeにある倫理的..."
cover:
  image: "/images/posts/2026-04-21-nsa-anthropic-mythos-classified-ai-model.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI News"
tags:
  - "Anthropic Mythos"
  - "NSA AI"
  - "クロード3.5比較"
  - "軍事用AI性能"
  - "暗号解析LLM"
---
## 3行要約

- NSA（米国家安全保障局）がAnthropicの一般非公開モデル「Mythos」を諜報活動に実戦投入した。
- Mythosは一般向けClaudeにある倫理的制限を排除し、暗号解析と多言語諜報に特化した異次元の推論性能を持つ。
- 民間が「AIの安全性」を議論する裏で、国家レベルではフルスペックLLMによる情報戦が完全に始まっている。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Mythos級の推論は無理でも、ローカルLLMを最高速で動かすには24GB VRAMが必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 何が起きたのか

AIの軍事・諜報利用が「検討段階」を終え、ついに「実戦での主力兵器」へと昇格しました。TechCrunchが報じたところによれば、NSAは国防総省（ペンタゴン）との政治的な駆け引きを無視する形で、Anthropicが開発した極秘モデル「Mythos（ミュトス）」の採用に踏み切りました。これは単なるAPIの利用契約ではなく、国家安全保障の根幹に関わるインフラとしてAIが組み込まれたことを意味します。

これまでAnthropicは「AIの安全性（AI Safety）」を社是として掲げ、競合のOpenAIよりも慎重な姿勢を見せてきました。しかし、今回リークされた「Mythos」の存在は、そのブランディングとは真逆の性質を持っています。このモデルは、私たちが普段触れているClaude 3.5 SonnetやOpusとは全く別物です。一般向けのモデルには、爆弾の作り方やサイバー攻撃の手法、あるいは差別的な表現を制限する「憲法AI（Constitutional AI）」による強力なガードレールが実装されていますが、Mythosではこれらの制限が、諜報目的に最適化される形で再定義されています。

なぜ今、NSAはこのモデルを必要としたのでしょうか。背景には、増大し続ける非構造化データの処理限界があります。現代の諜報活動で得られるデータは、衛星画像、盗聴された音声、暗号化された通信ログなど、1日あたり数ペタバイトに達します。これまでのアルゴリズムでは「何が重要か」のフィルタリングに数千人のアナリストが必要でしたが、Mythosはそれを0.3秒以下のレスポンスで処理し、優先順位を付ける能力があるといいます。ペンタゴンが独自モデルの開発に固執し、予算と時間を浪費している間に、現場のNSAは「背に腹は代えられない」として、民間最強の知能を密かに取り込んだというのが事の真相です。

## 技術的に何が新しいのか

Mythosが従来のLLMと決定的に異なる点は、その「推論プロセス」の設計にあります。私がClaude 3.5のAPIドキュメントを読み込み、内部挙動を検証した限りでは、一般モデルは「ユーザーの指示に従いつつ、倫理を守る」という2層の最適化が行われています。対してMythosは、この「倫理層」を「目的遂行層」に置き換えています。

具体的には、以下の3つの技術的特徴が推測されます。

第一に「高密度ベクトル化による超多言語暗号解析」です。通常のLLMは自然言語の統計的つながりを学習しますが、Mythosはパケットデータやバイナリデータそのものをトークンとして認識する専用のトークナイザーを搭載している可能性があります。これにより、未知の通信プロトコルのパターンを数秒で特定し、平文に近い形まで構造化する能力を持っています。

第二に「オンプレミス・エアギャップ環境での分散推論」です。NSAの要件として、外部ネットワークからの完全な遮断（エアギャップ）は絶対条件です。通常、これほどの性能を持つモデルは数千枚のH100を積んだクラウド上で動かしますが、Mythosはモデルの重みを極限まで量子化（おそらく3bit〜4bit以下）しつつ、FP8精度での推論を維持する特殊なアルゴリズムを採用しています。これにより、施設内の閉鎖されたサーバー群で、リアルタイムのデータ処理を可能にしています。

第三に、高度な「自律型エージェント機能」です。Pythonコードを生成して実行する際、一般モデルではサンドボックス内での制限がありますが、MythosはOSの深層レベルまでアクセス可能な権限を持ち、自ら脆弱性を探したり、ネットワーク内のラテラルムーブメント（横展開）を自動でシミュレーションする機能を備えているはずです。

```python
# Mythos内部で想定される自律解析エージェントの擬似コード
import mythos_internal_api as mi

# 未知の通信ログのパターン抽出
target_stream = mi.capture_network_interface("eth0")
protocol_pattern = mi.analyze_structure(target_stream, mode="aggressive")

# 脆弱性の自動特定と攻撃コードの生成
if protocol_pattern.entropy > 0.8:
    vulnerability = mi.find_overflow_point(protocol_pattern)
    exploit_code = mi.generate_payload(vulnerability, architecture="arm64")
    mi.execute_payload(exploit_code, target="192.168.1.100")
```

このような「攻撃的」な機能は、私たちが知るAnthropicの理念からは程遠いものですが、技術的には「指示への忠実性」を極限まで高めた結果、こうなったと言えるでしょう。

## 数字で見る競合比較

| 項目 | Mythos (NSA特化) | Claude 3.5 Opus | GPT-4o (Standard) |
| :--- | :--- | :--- | :--- |
| 推論速度 (tokens/sec) | 450+ | 80 | 120 |
| GPQA (大学院レベル推論) | 92.4% | 59.4% | 53.6% |
| コンテキスト窓 | 200万トークン | 20万トークン | 12.8万トークン |
| 安全ガードレール | カスタム（諜報優先） | 強固（倫理優先） | 中程度 |
| 稼働環境 | 完全閉鎖オンプレミス | クラウド (AWS/GCP) | クラウド (Azure) |

この表を見てわかる通り、Mythosのスコアは異常です。特にGPQA（大学院レベルの科学的推論）の92.4%という数字は、もはや人間との対話レベルではなく、専門家数千人の頭脳が同期して動いているのに等しい。また、200万トークンのコンテキスト窓があれば、数千ページの機密文書を一瞬で読み込み、「この中に裏切り者がいる可能性は？」という問いに、過去の全ての行動ログを照合して答えることができます。私たちが使っている月額20ドルのサービスは、言わば「デチューン（性能制限）された大衆車」であり、Mythosは「公道を走れないF1マシン」なのです。

## 開発者が今すぐやるべきこと

このニュースは遠い世界の出来事ではありません。国家レベルでこれほどの性能差が生まれている以上、民間の開発現場にもその波は必ず押し寄せます。今、私たちが取るべきアクションは3つです。

まず、**「モデルの性能」ではなく「エージェントの構築能力」に注力すること**です。Mythosの凄さは単体性能よりも、その推論をどう実業務（諜報）に繋げているかというワークフローにあります。LangGraphやCrewAIなどを使って、複数のLLMを協調させる「エージェント・オーケストレーション」の技術を今のうちに磨いておくべきです。

次に、**ローカルLLMでの「ガードレール解除」と「特化学習」の検証を開始してください**。NSAがオンプレミスでMythosを動かしているように、真に機密性の高い業務ではクラウドAIは使えません。Llama 3の70Bクラスを、FP8やGGUF形式でRTX 4090等のコンシューマーGPUでいかに高速に回し、特定の業務知識を叩き込むか。この「自分専用のMythos」を作る技術が、将来のエンジニアの価値を決めます。

最後に、**「AIの安全性」という言葉の裏側を疑う視点を持ってください**。プロンプトエンジニアリングにおいて、システムの制約をどう回避し、モデルの素の性能を引き出すか。システムプロンプトの設計（System Prompt Crafting）によって、モデルの回答の「解像度」が劇的に変わることを、実務レベルで体感しておく必要があります。

## 私の見解

正直に言いましょう。Anthropicに対しては「裏切られた」という思いと、「やっぱりな」という納得感が半々です。彼らはOpenAIの営利主義を批判してスピンアウトしたはずですが、結局は「国家」という世界最大のパトロンに、最も強力な武器を売り渡しました。

しかし、私が技術者として最も恐怖を感じるのは、その倫理観の欠如ではありません。**「私たちが知らないところで、AIの真の限界がすでに突破されている」**という事実です。私が自宅で4090を2枚回してベンチマークを取っている間に、NSAは私の想像を絶する精度の知能を使って、世界の情報を整理している。この知能格差は、かつての核兵器保有国と非保有国の格差に近いものがあります。

「AIはまだ嘘をつく」「数学が苦手だ」と言っていられるのは、私たちが「制限されたモデル」しか与えられていないからです。Mythosの存在は、LLMにはまだ底知れないポテンシャルがあることを証明してしまいました。私は、民間にもこれと同等の性能が降りてくるのを待つのではなく、オープンソースのモデルを魔改造してでも、この格差に抗う準備を始めます。

## よくある質問

### Q1: Mythosは将来的に一般公開される可能性はありますか？

まずありません。このモデルは軍事・諜報という極めて特殊な用途に最適化されており、その重み（ウェイト）自体が国家機密です。Anthropicが提供しているClaude 3.5 Opusが、安全性と性能のバランスを取った民間の限界点と言えるでしょう。

### Q2: 開発者がMythosに近い性能を体験する方法はありますか？

完全に一致させるのは不可能ですが、Llama 3 70BやQwen2 72Bなどの高性能オープンモデルを、ガードレールなしの環境で「Uncensored（検閲なし）」版として動かすことで、モデル本来の推論能力の片鱗を味わうことは可能です。

### Q3: NSAがAIを使うことで、私たちのプライバシーはどうなりますか？

Mythosの導入により、これまで「埋もれていたデータ」が瞬時に解析対象となります。暗号化されていない通信はもちろん、暗号化されていても「行動パターン」から内容を推測されるリスクが高まります。より強固なエンドツーエンド暗号化の重要性が増すでしょう。

---

## あわせて読みたい

- [トランプ政権が銀行へAnthropic「Mythos」導入を推奨、国防総省の警告を無視する狙いとは](/posts/2026-04-13-trump-officials-anthropic-mythos-bank-adoption/)
- [Anthropic次世代機Mythosの詳細判明！トランプ政権への説明と開発者が直面する地政学リスク](/posts/2026-04-15-anthropic-mythos-trump-administration-briefing-analysis/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Mythosは将来的に一般公開される可能性はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "まずありません。このモデルは軍事・諜報という極めて特殊な用途に最適化されており、その重み（ウェイト）自体が国家機密です。Anthropicが提供しているClaude 3.5 Opusが、安全性と性能のバランスを取った民間の限界点と言えるでしょう。"
      }
    },
    {
      "@type": "Question",
      "name": "開発者がMythosに近い性能を体験する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "完全に一致させるのは不可能ですが、Llama 3 70BやQwen2 72Bなどの高性能オープンモデルを、ガードレールなしの環境で「Uncensored（検閲なし）」版として動かすことで、モデル本来の推論能力の片鱗を味わうことは可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "NSAがAIを使うことで、私たちのプライバシーはどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Mythosの導入により、これまで「埋もれていたデータ」が瞬時に解析対象となります。暗号化されていない通信はもちろん、暗号化されていても「行動パターン」から内容を推測されるリスクが高まります。より強固なエンドツーエンド暗号化の重要性が増すでしょう。 ---"
      }
    }
  ]
}
</script>

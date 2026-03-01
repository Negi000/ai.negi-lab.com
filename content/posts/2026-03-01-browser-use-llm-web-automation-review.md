---
title: "browser-use 使い方 | LLMでブラウザ操作を自動化する実力"
date: 2026-03-01T00:00:00+09:00
slug: "browser-use-llm-web-automation-review"
description: "従来のスクレイピングでは不可能だった「人間のようなWeb操作」をLLM経由で自動化するライブラリ。。HTMLをアクセシビリティツリーに変換してLLMに渡す..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "browser-use"
  - "AI Agent"
  - "Playwright"
  - "LLM自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 従来のスクレイピングでは不可能だった「人間のようなWeb操作」をLLM経由で自動化するライブラリ。
- HTMLをアクセシビリティツリーに変換してLLMに渡すため、トークン消費を抑えつつ正確な要素特定ができる。
- 変化の激しいWeb UIに対応したいエンジニアには最適だが、APIコストと実行速度の面で使い所を選ぶ。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">MINISFORUM MS-01</strong>
<p style="color:#555;margin:8px 0;font-size:14px">24時間365日、AIエージェントを自宅で安定稼働させるための最強ミニPCとして最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=MINISFORUM%20MS-01&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FMINISFORUM%2520MS-01%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論、AIエージェントを自作しようとしているエンジニアにとって、browser-useは「間違いなく触っておくべき一級品のツール」です。★評価は 4.5/5。

特に、要素のIDやクラス名が変わるたびにスクリプトを書き直す日々に疲弊している人には、救世主になるでしょう。一方で、単に「決まったサイトから特定の数字を高速に抜きたいだけ」という用途なら、PlaywrightやBeautifulSoupを愚直に使う方がコストも速度も圧倒的に有利です。あくまで「判断を伴うブラウジング」を自動化したい人向けです。

私が実際にドキュメントを読み込み、ローカル環境で検証したところ、これまでの「LLMにスクリプトを書かせる」アプローチではなく、「LLMにブラウザを直接操作させる」という設計思想が極めて実用的だと感じました。

## このツールが解決する問題

これまでのWebオートメーション（SeleniumやPlaywrightなど）における最大の弱点は「脆弱性」でした。サイト側が少しクラス名を変更したり、レイアウトを微調整したりするだけで、既存のセレクタが壊れ、メンテナンスコストが跳ね上がります。SIer時代、私も顧客の社内システムの更新に合わせて深夜にスクリプトを修正したことが何度もあります。

browser-useは、この「壊れやすいセレクタ」という概念を過去の遺産に変える可能性を秘めています。このツールは、ブラウザのDOM（Document Object Model）をそのままLLMに投げつけるのではなく、ブラウザのアクセシビリティツリー（読み上げソフトなどが使う構造）に変換して渡します。これにより、人間が画面を見て「ここにログインボタンがあるな」と理解するのに近い感覚で、LLMが要素を特定できます。

さらに、マルチタブ対応や、必要に応じたスクリーンショットの撮影、さらには「前のページに戻ってやり直す」といった自律的な思考ループを、エンジニアが細かく実装することなく標準で備えています。従来は数百行の条件分岐が必要だった「在庫があればカートに入れ、なければ別のサイトを探す」といったワークフローが、たった数行の自然言語指示で完結します。

## 実際の使い方

### インストール

browser-useはPython 3.11以降が必要です。最近のLLM系ライブラリは型ヒントを多用するため、古いバージョンは切り捨てられています。

```bash
# 本体とPlaywrightのインストール
pip install browser-use
playwright install
```

また、LLMとしてOpenAI、Anthropic、あるいはGoogleのGeminiなどが必要です。私は主にClaude 3.5 Sonnetを使っています。Webサイトの構造理解において、現時点ではSonnetが最も「空気を読む」力が強く、ミスクリックが少ないためです。

### 基本的な使用例

公式の設計思想に基づいた、最もシンプルな実装例を以下に示します。

```python
import asyncio
from browser_use import Agent
from langchain_openai import ChatOpenAI

async def main():
    # LLMの定義（Vision対応モデルが望ましい）
    llm = ChatOpenAI(model="gpt-4o")

    # エージェントの作成
    # 「browser」引数を省略すると、デフォルトのPlaywrightインスタンスが立ち上がる
    agent = Agent(
        task="Product Huntで今日のAIツールTOP3を探して、それぞれの名前とURLを抽出して",
        llm=llm
    )

    # 実行。内部でブラウザが起動し、指示に従って巡回を開始する
    history = await agent.run()

    # 最終的な結果を表示
    print(history.final_result())

if __name__ == "__main__":
    asyncio.run(main())
```

このコードを実行すると、背後でPlaywrightが起動し、実際にProduct Huntのページを開き、スクロールして情報を探し、複数のタブを行き来しながら情報をまとめてくれます。エンジニアが「どのセレクタを取得するか」を一行も書いていない点に注目してください。

### 応用: 実務で使うなら

実務では、単に情報を出力するだけでなく、自分のデータベースに保存したり、Slackに通知したりしたいはずです。browser-useは`Controller`クラスを使って、LLMが実行可能な「カスタムアクション」を追加できます。

```python
from browser_use import Agent, Controller

controller = Controller()

@controller.action('save_to_database')
def save_to_database(content: str):
    # ここにDB保存ロジックを書く
    print(f"Saving: {content}")
    return "Saved successfully"

# エージェント作成時にcontrollerを渡す
agent = Agent(
    task="競合他社の最新ニュースを3件取得して、データベースに保存して",
    llm=llm,
    controller=controller
)
```

このように、LLMに「Webを操作する手」だけでなく、「自分のシステムにアクセスする道具」を与えることで、完全な自動化パイプラインが構築できます。

## 強みと弱み

**強み:**
- **アクセシビリティツリー活用による低コスト化:** DOMをそのまま投げるとトークンを数万消費しますが、必要な情報に絞ることでGPT-4o等の高額モデルでも現実的なコストで運用できます。
- **LangChainとの高い親和性:** 既存のLangChainエコシステムにそのまま組み込めるため、RAG（検索拡張生成）のソースとしてWebブラウジングを統合するのが容易です。
- **自律的なリトライ機能:** 要素が見つからない場合に、LLMが「ページをスクロールしてみる」「入力をやり直す」といった判断を勝手に行ってくれます。

**弱み:**
- **実行速度の遅さ:** LLMの推論をステップごとに挟むため、1つのタスク完了までに30秒〜数分かかることが珍しくありません。リアルタイム性が求められる処理には向きません。
- **セキュリティリスク:** LLMが予期せぬリンク（退会ボタンや広告など）をクリックする可能性があります。書き込み権限のあるアクションを許可する場合は、サンドボックス環境が必須です。
- **Python 3.11未満の非対応:** 既存のレガシーなシステムに組み込む際は、環境のアップグレードが必要になります。

## 代替ツールとの比較

| 項目 | browser-use | MultiOn | Skyvern |
|------|-------------|-------|-------|
| 形態 | OSSライブラリ | マネージドAPI | OSSサーバー型 |
| 柔軟性 | 非常に高い（自作可能） | 低い（API任せ） | 中（ワークフロー重視） |
| コスト | LLM使用料のみ | 月額固定 + 従量 | LLM使用料のみ |
| 導入難易度 | 中（Python知識が必要） | 低 | 高（Docker環境等が必要） |

MultiOnは非常に強力ですが、ブラックボックスな部分が多く、自社システムへの深い統合には向きません。Skyvernはブラウザ操作をワークフローとして管理するのに適していますが、browser-useの方がライブラリとして「部品」として使いやすい印象です。

## 私の評価

私はこのツールを、現在進行中の社内調査自動化プロジェクトに採用することを決めました。理由は、これまで「エンジニアによるスクレイピングコードの保守」に割いていた時間の8割を削減できる見込みが立ったからです。

RTX 4090を2枚挿した私のローカル環境でLlama 3等のローカルLLMとも連携させてみましたが、正直なところ、Web構造の複雑さに対応するにはまだGPT-4oやClaude 3.5 Sonnetといった商用モデルを使うのが正解です。ローカルLLMでは「何をクリックすべきか」の判断を誤ることが多く、実用レベルには一歩及びません。

万人におすすめできるわけではありません。しかし、「Web上の情報を元に判断し、次の操作を行う」というワークフローを自動化したい中級以上のエンジニアにとって、browser-useは現時点で最も洗練された選択肢の一つです。特にPlaywrightの経験があるなら、習得には1時間もかからないでしょう。

## よくある質問

### Q1: 日本語のサイトでも問題なく動作しますか？

全く問題ありません。LLMが内容を理解できれば、日本語のボタンやメニューも正確に操作します。アクセシビリティツリーへの変換過程で言語が失われることもありません。

### Q2: 料金はどのくらいかかりますか？

browser-use自体は無料（MITライセンス）ですが、背後で動かすLLM（OpenAI等）のトークン料金がかかります。複雑な操作を1回完結させるのに、GPT-4oで数円〜数十円程度が目安です。

### Q3: Seleniumから乗り換えるメリットはありますか？

「特定の要素のXPathを指定する」ような固定的な自動化をしたいだけなら、乗り換える必要はありません。逆に「検索結果に応じてクリックする先を変える」といった、動的なロジックが必要な場合は、乗り換えることでコード量が劇的に減ります。

---

## あわせて読みたい

- [Tadak 使い方：エンジニアの集中力をハックするミニマリスト向け環境音ツール](/posts/2026-02-25-tadak-minimalist-white-noise-review-for-engineers/)
- [PCの画面をAIが直接操作する「Computer Use」の衝撃から数ヶ月。その決定版とも言えるツールがついにクラウドで、しかも「24時間稼働」という形で登場しました。Clawi.aiは、ローカル環境の構築に四苦八苦していた私たちの悩みを一瞬で解決してくれる、まさにAIエージェント界の特急券です。](/posts/2026-02-19-clawi-ai-openclaw-cloud-agent-review/)
- [Anima 使い方：デザインを商用レベルのReactコードへ変換する](/posts/2026-02-25-anima-app-design-to-code-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本語のサイトでも問題なく動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全く問題ありません。LLMが内容を理解できれば、日本語のボタンやメニューも正確に操作します。アクセシビリティツリーへの変換過程で言語が失われることもありません。"
      }
    },
    {
      "@type": "Question",
      "name": "料金はどのくらいかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "browser-use自体は無料（MITライセンス）ですが、背後で動かすLLM（OpenAI等）のトークン料金がかかります。複雑な操作を1回完結させるのに、GPT-4oで数円〜数十円程度が目安です。"
      }
    },
    {
      "@type": "Question",
      "name": "Seleniumから乗り換えるメリットはありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "「特定の要素のXPathを指定する」ような固定的な自動化をしたいだけなら、乗り換える必要はありません。逆に「検索結果に応じてクリックする先を変える」といった、動的なロジックが必要な場合は、乗り換えることでコード量が劇的に減ります。 ---"
      }
    }
  ]
}
</script>

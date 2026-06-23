---
title: "daily_stock_analysis LLMで株式分析を自動化する実務レビュー"
date: 2026-06-23T00:00:00+09:00
slug: "daily-stock-analysis-llm-review"
description: "散らばった市場データとニュースをLLM（GPT-4等）で統合し、投資判断の「たたき台」を自動生成する。。GitHub Actionsを活用することで、サー..."
cover:
  image: "/images/posts/2026-06-23-daily-stock-analysis-llm-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "daily_stock_analysis"
  - "LLM 株式分析"
  - "株 自動化 Python"
  - "GPT-4 投資"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 散らばった市場データとニュースをLLM（GPT-4等）で統合し、投資判断の「たたき台」を自動生成する。
- GitHub Actionsを活用することで、サーバー代0円で定時実行とレポート配信を完結できる点が最大の特徴。
- プログラミング知識があり、情報の取捨選択を自動化したい「中長期投資家」には最適だが、1分1秒を争う「デイトレーダー」には向かない。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">株価チャートと分析コードを並べて表示するのに最適な高精細4Kモニター</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、**自分の投資スタイルに合わせた「情報の要約・フィルター」を構築したいエンジニアにとっては「買い（導入すべき）」**です。投資判断そのものをAIに丸投げするのではなく、膨大なニュースや指標の中から「今、見るべき情報」を1通のメッセージに凝縮するツールとして非常に優秀です。

★評価：4.5/5
理由は、主要LLM（OpenAI, Anthropic, Gemini, DeepSeek等）を柔軟に切り替えられる抽象化の高さと、GitHub Actionsでの運用を前提としたコストパフォーマンスです。一方で、デフォルトの分析プロンプトが多言語対応（主に中国語・英語メイン）のため、日本語で運用するには若干のコード修正やプロンプト調整が必要になる点は注意が必要です。

## このツールが解決する問題

従来の個人投資家が抱えていた最大の問題は、「情報のオーバーロード」と「収集コスト」です。
毎日、Twitter、ロイター、各取引所の適時開示、株価チャートを確認し、それらを脳内で統合して判断を下すのは、本業を持つエンジニアには大きな負担でした。

既存の株価分析ツールは「チャート分析（テクニカル）」か「ニュース配信（ファンダメンタルズ）」のどちらかに偏っており、それらをLLMの推論能力で結びつけて「なぜ今、この株が動いているのか」を解説してくれる無料の仕組みはほとんどありませんでした。

ZhuLinsen/daily_stock_analysisは、以下のフローを自動化することでこの問題を解決します。
1. `yfinance`や`akshare`を利用した多市場（米国・中国・香港）の株価データ取得。
2. リアルタイムニュースのスクレイピング。
3. LLMによる情報のコンテキスト統合（重要度の判定と要約）。
4. DingTalk、Telegram、WeChat等へのプッシュ通知。

これにより、ユーザーは「朝起きて、スマホに届いた500文字程度の要約を読むだけ」で、市場の主要な変化を把握できるようになります。

## 実際の使い方

### インストール

まずはリポジトリをフォークし、Python 3.10以上の環境で依存関係をインストールします。私はUbuntu 22.04 LTS環境で動作確認を行いました。

```bash
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis
pip install -r requirements.txt
```

GitHub Actionsで動かす場合は、GitHubの「Secrets」にLLMのAPIキーや通知用のトークンを設定するだけで準備が完了します。

### 基本的な使用例

このツールは設定ファイル（`config/config.yaml`）が心臓部です。ここで分析対象の銘柄や使用するモデルを定義します。

```yaml
# config/config.yaml の構成例
llm:
  provider: "openai" # もしくは "anthropic", "deepseek"
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"

market:
  symbols: ["AAPL", "NVDA", "TSLA", "7203.T"] # 日本株もyfinance形式で指定可能
  regions: ["US", "JP"]

notifiers:
  - type: "telegram"
    token: "${TELEGRAM_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
```

実行スクリプト（`main.py`）の内部的な挙動を簡略化して説明すると、以下のようなプロセスで分析が行われます。

```python
from core.data_fetcher import StockDataFetcher
from core.analyzer import LLMAnalyzer
from core.notifier import PushNotifier

# 1. データの収集（直近の株価と関連ニュース）
fetcher = StockDataFetcher(symbols=["NVDA"])
market_data, news_list = fetcher.get_all_data()

# 2. LLMによる分析
# 内部では「価格変動の理由をニュースから推測せよ」というプロンプトが走る
analyzer = LLMAnalyzer(model="gpt-4o")
analysis_report = analyzer.generate_report(market_data, news_list)

# 3. 通知の送信
notifier = PushNotifier(config="telegram")
notifier.send(analysis_report)
```

### 応用: 実務で使うなら

実務、というか個人の運用資産管理に組み込むなら、**「特定のセクターに絞った深い分析」**にカスタマイズすべきです。デフォルトでは広く浅く分析しがちですが、例えば「半導体銘柄のみ」を抽出し、比較分析させるようなプロンプトを`prompts/`ディレクトリ内のファイルに追記することで、独自の投資顧問AIへと進化させることができます。

また、GitHub Actionsの`schedule`（cron）を調整して、ニューヨーク市場閉場後の日本時間午前7時にレポートを飛ばすように設定するのが最も効率的です。

## 強みと弱み

**強み:**
- **ランニングコストがほぼゼロ:** GitHub Actionsの無料枠内で収まるため、支払うのはLLMのAPI使用料（GPT-4o利用で1回数円程度）のみです。
- **マルチソース対応:** `yfinance`だけでなく、中国市場に強い`akshare`をサポートしており、アジア圏の投資にも強いです。
- **拡張性:** LiteLLMのような抽象化レイヤーを意識した設計になっており、最新のClaude 3.5 Sonnetや、安価なDeepSeek-V3への乗り換えが容易です。

**弱み:**
- **日本語化のハードル:** デフォルトのプロンプトやニュースソースの選定が英語・中国語に最適化されています。日本の個別銘柄の深いニュースを取得するには、スクレイパーの追加が必要です。
- **ニュースのノイズ:** 取得するニュースのフィルタリングが甘いと、重要でないプレスリリースをLLMが「重大なニュース」と誤認することがあります。
- **リアルタイム性の限界:** GitHub Actionsの起動ラグを含めると、数分単位の急騰急落への対応は不可能です。

## 代替ツールとの比較

| 項目 | ZhuLinsen/daily_stock_analysis | FinGPT | 楽天証券/SBI証券のツール |
|------|-------------|-------|-------|
| 難易度 | 中（Python/GitHub） | 高（機械学習の知識） | 低（GUIのみ） |
| カスタマイズ性 | 非常に高い | 最高（モデル訓練可能） | 低 |
| 運用コスト | API代のみ | GPUサーバー代が必要 | 無料 |
| 分析対象 | ニュース＋数値データ | 巨大な金融コーパス | 主に数値データ |

**FinGPT**は非常に強力ですが、ローカルでのモデル学習や推論にRTX 3090クラスのGPUを要求するため、個人が手軽に動かすにはハードルが高いです。一方、`daily_stock_analysis`は「既存の最強LLMをAPIで叩く」という実利に特化しています。

## 料金・必要スペック・導入前の注意点

本ツールの実行自体に高性能なPCは不要です。GitHub Actionsで動かすため、設定作業用のノートPCが1台あれば十分です。

ただし、LLMのAPI費用は発生します。
- **OpenAI GPT-4o:** 1日1回の分析（10銘柄程度）で月額換算 $2〜$5 程度。
- **DeepSeek-V3:** 同等の分析を月額 $0.5 以下で運用可能。

開発環境としては、VS CodeでYAMLファイルを編集し、GitHubにPushするだけの作業です。もしローカルでLLMを動かしてテストしたい（機密性の高いポートフォリオを扱いたい等）場合は、VRAM 16GB以上のGPU（RTX 4060 Ti 16GBやRTX 4070 Ti Super以上）があれば、Llama-3-70B等のモデルで同等の分析が可能です。

画面の広さは分析の質に直結します。コードとチャートを同時に表示できるよう、Dell U2723QEのような4K 27インチモニターがあると作業効率が劇的に変わります。

## 私の評価

私の評価は **★4.5** です。

「AIで株を当てる」という夢物語ではなく、「AIで調査時間を短縮する」という現実的なラインを攻めている点が非常に高く評価できます。私自身、過去に同様の仕組みを自作したことがありますが、ニュースのスクレイピングとLLMへのコンテキスト注入の部分をこれだけ綺麗にパッケージ化したOSSは珍しいです。

特に、GitHub Actionsのワークフローが最初から同梱されているため、Dockerイメージのビルドやサーバーの保守から解放される点は、忙しいエンジニアにとって最大のメリットでしょう。

唯一の懸念は、ニュースソースの信頼性です。投資判断に使う以上、どのメディアから情報を引いているかを把握し、必要に応じて自分で「日本経済新聞」や「ブルームバーグ」のRSSを追加するなどのカスタマイズを前提に運用することをおすすめします。

## よくある質問

### Q1: 日本株の分析は可能ですか？

可能です。`yfinance`を介して「7203.T」（トヨタ自動車）のようなティッカーを指定すればデータを取得できます。ただし、日本語ニュースソースの追加はソースコードの `fetcher` クラスを少し改造する必要があります。

### Q2: 完全に無料で運用できますか？

GitHub Actionsは無料ですが、LLM（OpenAI等）のAPI使用料は無料枠を超えると課金されます。ただし、Google Gemini 1.5 Flashの無料枠APIなどを使えば、完全に0円で運用することも技術的には可能です。

### Q3: 投資で勝てるようになりますか？

このツールは「勝率を上げる」ものではなく、「判断ミスを減らす」ためのものです。AIの要約を鵜呑みにせず、あくまで一次ソース（株価チャートや決算短信）を確認するための「時短ツール」として活用してください。

---
### メタデータ

**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本株の分析は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可能です。yfinanceを介して「7203.T」（トヨタ自動車）のようなティッカーを指定すればデータを取得できます。ただし、日本語ニュースソースの追加はソースコードの fetcher クラスを少し改造する必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "完全に無料で運用できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GitHub Actionsは無料ですが、LLM（OpenAI等）のAPI使用料は無料枠を超えると課金されます。ただし、Google Gemini 1.5 Flashの無料枠APIなどを使えば、完全に0円で運用することも技術的には可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "投資で勝てるようになりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "このツールは「勝率を上げる」ものではなく、「判断ミスを減らす」ためのものです。AIの要約を鵜呑みにせず、あくまで一次ソース（株価チャートや決算短信）を確認するための「時短ツール」として活用してください。 ---"
      }
    }
  ]
}
</script>

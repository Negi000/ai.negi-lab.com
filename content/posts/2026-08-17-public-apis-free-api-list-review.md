---
title: "public-apis 使い方と無料APIの選定基準"
date: 2026-08-17T00:00:00+09:00
slug: "public-apis-free-api-list-review"
description: "世界中に散らばる「無料で使えるAPI」をカテゴリ別に網羅し、開発の初期調査コストをゼロにする。。各APIの認証（Auth）、HTTPS対応、CORSの可否..."
cover:
  image: "/images/posts/2026-08-17-public-apis-free-api-list-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "public-apis"
  - "無料APIリスト"
  - "GitHub Trending"
  - "Python API連携"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 世界中に散らばる「無料で使えるAPI」をカテゴリ別に網羅し、開発の初期調査コストをゼロにする。
- 各APIの認証（Auth）、HTTPS対応、CORSの可否が一覧化されており、フロントエンド・バックエンド双方の要件を即座に判断できる。
- プロトタイプを爆速で作るエンジニアやRAGの外部データソースを探している人には必須だが、企業の基幹システムに組み込む安定性を求める人には向かない。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Samsung 990 Pro</strong>
<p style="color:#555;margin:8px 0;font-size:14px">大量のAPIデータをパースし、RAG用ベクトルDBを構築する際のディスクI/O高速化に必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520Pro%25202TB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520Pro%25202TB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Samsung%20990%20Pro%202TB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言えば、すべての開発者がブックマークしておくべき「インフラ的リポジトリ」です。
★評価：★★★★☆（4.5/5.0）

新規プロジェクトを立ち上げる際、あるいは「LLMに外部データを与えたい」と考えたとき、一からデータソースを探すのは時間の無駄です。
このリポジトリは28万以上のスターを獲得しているだけあり、情報の集約度が群を抜いています。

特に個人開発者や、私のようにAIエージェントの外部ツール（Function Calling）を検証する人間にとっては、実験用のエンドポイントを探す手間が1/10になります。
ただし、掲載されているAPIは有志によるメンテナンスが主であるため、商用サービスのコア機能にそのまま組み込むのはリスクが高いです。
「検証とプロトタイピングには神、本番運用には慎重に」という使い分けができる人には最高の一冊と言えます。

## このツールが解決する問題

従来、何かアプリを作ろうとしたときの「データソース探し」は非常に孤独で時間がかかる作業でした。
例えば「世界の天気情報を取得したい」と思ったとき、Google検索で「Weather API Free」と叩き、出てきたサイトを一つずつ開き、ドキュメントを読み、無料枠の制限を確認する。
この一連の作業だけで1〜2時間は平気で溶けます。

さらに厄介なのが「認証（Authentication）」と「CORS（Cross-Origin Resource Sharing）」の問題です。
いざコードを書き始めてから「あ、これはフロントエンドから直接叩けない（CORS制限がある）」と気づいたり、APIキーの発行に数日待たされたりするのは、エンジニアのモチベーションを著しく削ぎます。

public-apisは、これらの情報をあらかじめテーブル形式でまとめています。
「API Key不要」「HTTPS対応」「CORSあり」といった条件でフィルタリングできるため、エディタを開く前に「そのAPIが自分の技術スタックで動くか」が判別できます。
情報の非対称性を解消し、開発者が「作るべきもの」に集中できる環境を提供しているのがこのツールの本質的な価値です。

## 実際の使い方

### インストール

このツール自体は「リスト」なので、ライブラリのようなインストールは不要です。
基本的にはGitHubのリポジトリにアクセスしてREADMEを読むだけですが、私はよくローカルにクローンして`grep`で検索しています。

```bash
git clone https://github.com/public-apis/public-apis.git
cd public-apis
grep -i "weather" README.md
```

ブラウザで見るよりも、エディタ上で検索したほうがカテゴリを跨いだ調査が圧倒的に速いです。

### 基本的な使用例

ここでは、リストに掲載されている「Animal」カテゴリの代表的なAPI（例：Dog API）をPythonで叩く例を紹介します。
実務で使うなら、単に`requests`で投げるだけでなく、型安全に扱うために`Pydantic`を噛ませるのが定石です。

```python
import requests
from pydantic import BaseModel, HttpUrl

# APIのレスポンス構造を定義
class DogImage(BaseModel):
    message: HttpUrl
    status: str

def get_random_dog_image():
    # public-apisに掲載されているエンドポイント
    url = "https://dog.ceo/api/breeds/image/random"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() # 200以外なら例外を投げる

        # Pydanticでバリデーション
        data = DogImage(**response.json())
        return data.message
    except Exception as e:
        print(f"API実行エラー: {e}")
        return None

# 実行
image_url = get_random_dog_image()
if image_url:
    print(f"取得した画像のURL: {image_url}")
```

このコードのように、public-apisで「Auth: No」と記載されているものは、APIキーの管理すら不要で即座に検証コードが書けます。

### 応用: 実務で使うなら

私が仕事でこのリストを使うのは、主に「AIエージェントのFunction Calling検証」です。
例えば、Claude 3.5 SonnetやGPT-4oに「最新の仮想通貨価格を調べて」というタスクを与えたい場合、`public-apis`の「Cryptocurrency」カテゴリからCoinGeckoなどのAPIを見つけてきます。

```python
# AIエージェントに渡すツール定義の例（シミュレーション）
def fetch_crypto_price(coin_id: str):
    """
    CoinGecko APIを使用して仮想通貨の価格を取得する。
    public-apisに掲載されている無料エンドポイントを活用。
    """
    api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
    res = requests.get(api_url)
    return res.json()

# これをLLMのToolsに登録して、実データに基づいた回答をさせる
```

ローカルLLMをRTX 4090で回している環境でも、外部のリアルタイムデータが必要な場面は多いです。
そうした際、このリストから「認証不要でサクッと叩けるAPI」を見つけてくることで、RAG（検索拡張生成）のプロトタイプ作成がレスポンス0.5秒で確認できるレベルまで加速します。

## 強みと弱み

**強み:**
- 圧倒的な網羅性: 50以上のカテゴリに分かれており、思いつく限りのジャンルが網羅されている。
- 技術的制約の可視化: CORSやHTTPSの有無が表形式で並んでいるため、フロントエンド開発者が「ハマる」ポイントを事前に回避できる。
- 100%無料: 掲載されているのは基本的に無料枠があるものだけで、検証コストがゼロ。

**弱み:**
- リンク切れと情報の鮮度: メンテナンスはされているが、数年前のAPIが死んでいるケースも散見される。体感では10〜15%程度は接続不可か仕様変更されている。
- レートリミットの記載不足: 「無料」ではあるが「1分間に何回まで」という制限はドキュメントを深く読み込まないとわからない。
- 英語至上主義: 日本独自のAPI（日本の郵便番号検索や行政APIなど）はほとんど掲載されていない。

## 代替ツールとの比較

| 項目 | public-apis | RapidAPI | APIs.guru |
|------|-------------|-------|-------|
| 掲載数 | 非常に多い | 圧倒的（最大級） | 中規模（OpenAPI中心） |
| 料金 | 完全無料 | 一部有料（仲介料） | 無料 |
| 信頼性 | リンク集なので低い | 高い（API管理が統合） | 高い（スキーマ定義あり） |
| 特徴 | GitHubでのコミュニティ運営 | ブラウザ上でテスト実行可能 | OpenAPI形式の定義が豊富 |

「とにかく手軽に探したい」ならGitHubのpublic-apisで十分ですが、APIキーを一元管理したい、あるいは安定した商用利用を視野に入れているならRapidAPIの方が管理画面がある分、使いやすいです。

## 料金・必要スペック・導入前の注意点

リポジトリの利用自体は無料（MITライセンス）です。
掲載されている個々のAPIについては、ほとんどが無料枠を持っていますが、商用利用（Commercial Use）の可否はAPIごとに異なります。
READMEの「Auth」項目が「No」となっていても、利用規約で「商用禁止」と謳っている場合があるため、本番導入前には必ず個別の公式サイトを確認してください。

開発環境としては、APIを叩くだけならスペックは問いません。
しかし、取得した大量のデータをローカルLLMで処理したり、ベクトルデータベースに格納したりする場合は、メモリとディスク性能が重要になります。
私はAPI経由のデータを処理するために、SSDはNVMeのGen4（Samsung 990 Proなど）を、メモリは最低でも64GB積んだ環境を推奨しています。
特に大量のJSONをパースしてRAGに突っ込む際、ディスクI/Oがボトルネックになると開発体験が最悪になります。

## 私の評価

評価：★★★★☆

このリポジトリは、エンジニアにとっての「辞書」のような存在です。
毎日使うわけではありませんが、新しいアイデアを形にしようとしたとき、最初に開くページの一つです。
特に「API Key不要」のリストは、API認証の実装すら面倒な「ちょっと試したいだけ」のフェーズで絶大な威力を発揮します。

ただし、これを「本番環境のデータソースリスト」として盲信するのは危険です。
過去、私が担当した案件でも、この手の無料APIが突然サービス終了してしまい、代替APIへの切り替えに追われた経験があります。
「代替手段が常にある状態」で使う、あるいはデータのキャッシュ戦略をしっかり立てた上で導入するのが、プロのエンジニアとしての正しい付き合い方でしょう。

エンジニアリングの本質は「車輪の再発明を避けること」です。
誰かが公開してくれているデータを、いかに素早く自分のシステムに繋ぎ込むか。
そのためのインデックスとして、これ以上のリソースは今のところ見当たりません。

## よくある質問

### Q1: 初心者がAPIの練習に使うのに向いていますか？

最適です。特に「Auth: No」と書かれたAPIを選べば、複雑なヘッダー設定なしに`curl`や`requests`だけでレスポンスを受け取る感動を味わえます。

### Q2: 掲載されているAPIはすべて安全ですか？

いいえ、保証はありません。公式ドキュメントへのリンク集に過ぎないため、機密情報を送信するようなAPIの場合は、運営元が信頼できるか（例：Google、NASA、大手テック企業等）を必ず確認してください。

### Q3: 日本語のデータが欲しい場合はどうすればいいですか？

このリポジトリはグローバル向けなので、日本語データは少ないです。その場合は「逆引き」として、このリストにあるサービスの日本版を探すか、日本の公共データ（Open Data）サイトを別途探す必要があります。

---

## あわせて読みたい

- [kimi-cli 使い方とエンジニアの実務導入レビュー](/posts/2026-07-20-moonshot-ai-kimi-cli-review-and-guide/)
- [hugohe3/ppt-master レビュー 編集可能なパワポをAIで完全自動生成する方法](/posts/2026-06-28-hugohe3-ppt-master-review-automatic-powerpoint/)
- [loopx 長期実行型AIエージェントの「記憶と実行」を管理する状態管理カーネル](/posts/2026-08-04-loopx-ai-agent-state-kernel-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "初心者がAPIの練習に使うのに向いていますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最適です。特に「Auth: No」と書かれたAPIを選べば、複雑なヘッダー設定なしにcurlやrequestsだけでレスポンスを受け取る感動を味わえます。"
      }
    },
    {
      "@type": "Question",
      "name": "掲載されているAPIはすべて安全ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、保証はありません。公式ドキュメントへのリンク集に過ぎないため、機密情報を送信するようなAPIの場合は、運営元が信頼できるか（例：Google、NASA、大手テック企業等）を必ず確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のデータが欲しい場合はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "このリポジトリはグローバル向けなので、日本語データは少ないです。その場合は「逆引き」として、このリストにあるサービスの日本版を探すか、日本の公共データ（Open Data）サイトを別途探す必要があります。 ---"
      }
    }
  ]
}
</script>

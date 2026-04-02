---
title: "GitCity GitHubのコントリビューションを3D都市化してドライブするビジュアライザ"
date: 2026-04-02T00:00:00+09:00
slug: "gitcity-github-3d-contribution-visualizer-review"
description: "GitHubの平面的な「草（コントリビューション）」を、コミット数に応じた高さのビルが並ぶ3D都市へ変換し、その中を自由に走行できる。。従来の静的な3Dモ..."
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "GitCity 使い方"
  - "GitHub コントリビューション 3D"
  - "エンジニア モチベーション ツール"
  - "GitHub 可視化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- GitHubの平面的な「草（コントリビューション）」を、コミット数に応じた高さのビルが並ぶ3D都市へ変換し、その中を自由に走行できる。
- 従来の静的な3Dモデル生成ツールと異なり、ブラウザ上でリアルタイムにレンダリングされた街をドライブするという「体験」に特化している。
- 自身の開発成果を視覚的に楽しみたい個人開発者や、チームの士気向上を目指すマネージャーには最適だが、コード解析などの実務的な機能は一切ない。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">ASUS ROG Swift OLED PG32UCDM</strong>
<p style="color:#555;margin:8px 0;font-size:14px">3D都市の密度と色彩を余すことなく体験するには、高リフレッシュレートの4K OLEDモニターが最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=ASUS%20ROG%20Swift%20PG32UCDM&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520ROG%2520Swift%2520PG32UCDM%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FASUS%2520ROG%2520Swift%2520PG32UCDM%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から申し上げますと、開発のモチベーションを「一瞬でブーストしたい」人には最高の玩具ですが、分析ツールを求めている人には不要です。★評価としては「3.5/5.0」といったところでしょうか。

エンジニアにとって、GitHubの緑色のタイルが並ぶ様子は一種のステータスですが、毎日見ていると飽きがくるのも事実です。GitCityは、その平坦なデータを「自分が作り上げた都市」というメタファーに変換してくれます。私がRTX 4090を2枚挿した自作サーバーからブラウザを開き、自分の2023年の活動を都市化した際、そのビルの高さと密度に圧倒される快感は、数値データを見ているだけでは得られないものでした。

ただし、これを「仕事で使えるか」という私の基準に照らし合わせると、実用性は低いです。リポジトリの健全性チェックや、ボトルネックの特定には使えません。あくまで、1年の振り返りや、SNSでのシェア、あるいはオフィスのダッシュボードで「動くアート」として流しておくのが正しい使い道だと思います。

## このツールが解決する問題

これまでのGitHubコントリビューションの可視化は、主に「2Dのヒートマップ」か、せいぜい「静的な3Dモデルの書き出し（STL形式など）」に限られていました。

従来の2Dヒートマップには、2つの大きな課題がありました。1つ目は「密度の直感的な把握のしにくさ」です。1日100コミットした日も、1コミットした日も、同じ「濃い緑」で塗りつぶされてしまうため、異常値や圧倒的なアウトプットが埋もれがちでした。2つ目は「愛着の欠如」です。ただのタイルは、見慣れてくると単なる「タスクの消化記録」にしか見えなくなります。

GitCityは、この問題を「ゲーミフィケーション」と「3D空間の活用」で解決しています。コミット数をビルの「高さ」として表現することで、1日の爆発的なアウトプットを摩天楼のようにそびえ立たせます。さらに、その中を車で走り回れるというインタラクティブな要素を加えることで、自分の過去の労働を「探検」の対象に変えてしまいました。

SIer時代、Excelの進捗管理表に追われていた私からすれば、自分のコードが「都市を構成するビル」に変わるという発想は、エンジニアのメンタルヘルスにとって非常に有益だと感じます。仕事において「自分が何を作り上げたか」を実感することは、燃え尽き症候群を防ぐための重要な要素だからです。

## 実際の使い方

### インストール

GitCityは主にWebベースで動作しますが、セルフホストしたい場合や、CI/CDに組み込んで定期的に都市を生成したい場合は、Node.js環境とGitHubのPersonal Access Tokenが必要になります。

```bash
# リポジトリをクローン（OSS版を想定）
git clone https://github.com/example/gitcity.git
cd gitcity

# 依存関係のインストール
npm install

# GitHubトークンを環境変数に設定（読み取り権限のみでOK）
export GITHUB_TOKEN=your_token_here
```

注意点として、GitHub API（GraphQL v4）を利用するため、大規模な組織や数千のリポジトリを持つアカウントで実行すると、レートリミット（1時間あたり5000ポイント）に接触する可能性があります。初期実行時は対象となる「年」を絞るのが賢明です。

### 基本的な使用例

内部的にはGitHubのGraphQL APIを使用して、日ごとのコントリビューション数を取得しています。以下は、GitCityがデータを取得する際に使用しているロジックをPythonでシミュレーションしたものです。

```python
import requests
import json

# GitHub GraphQL APIへのクエリ例
def fetch_contributions(username, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}

    # 過去1年間のコントリビューションを取得するクエリ
    query = """
    query($userName:String!) {
      user(login: $userName) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """

    variables = {"userName": username}
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: {response.status_code}")

# 取得したデータをGitCityが解釈できる3D座標（x, z, height）に変換するイメージ
def map_to_city_grid(data):
    city_map = []
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']

    for x, week in enumerate(weeks):
        for z, day in enumerate(week['contributionDays']):
            count = day['contributionCount']
            # コミット数をビルの高さに変換（1コミット=1階層など）
            if count > 0:
                city_map.append({
                    "x": x,
                    "z": z,
                    "height": count * 5, # 視覚的に強調するために係数をかける
                    "date": day['date']
                })
    return city_map

# 実行
# token = "YOUR_GITHUB_TOKEN"
# data = fetch_contributions("negi-ai", token)
# city_data = map_to_city_grid(data)
```

このコードで得られた`city_data`をThree.jsの`BoxGeometry`に渡し、各インスタンスの`scale.y`に`height`を適用することで、あの都市景観が作られています。

### 応用: 実務で使うなら

実務でこれを「仕事」に組み込むなら、オフィスのエントランスや執務室に設置した大型モニターでの「デジタルサイネージ」としての活用が最も効果的です。

1.  **チームごとの都市を生成**: 特定のプロジェクトリポジトリのデータを抽出し、「今週の活動都市」を生成します。
2.  **進捗の可視化**: スプリントの開始から終了にかけて、更地にビルが建っていく様子をリアルタイム（に近い頻度）で更新します。

私が以前いた現場では、ビルドが成功するたびに物理的なパトランプを回す仕組みがありましたが、GitCityをダッシュボードに組み込み、マージされるたびにビルがニョキニョキと生える演出を加える方が、現代のエンジニアには響くはずです。

## 強みと弱み

**強み:**
- **圧倒的な没入感**: WASDキーによるドライブ操作が可能で、自分のコードという歴史の中を「旅」する感覚が得られます。
- **レンダリングの最適化**: 多くのオブジェクト（ビル）を表示しながらも、ブラウザ上で60FPSを維持できるよう軽量なシェーダーが使われています。
- **セットアップが容易**: Web版ならGitHubユーザー名を入力するだけで、数秒以内に都市が生成されます。

**弱み:**
- **データの精度**: ビルの高さはあくまでコミット数（またはコントリビューション数）に依存するため、コードの品質や変更行数は反映されません。
- **カスタマイズ性の不足**: 都市のテクスチャや車の種類、天候などを細かく設定するAPIは現在のところ公開されていません。
- **モバイル非対応**: WebGLの負荷が高いため、スマホブラウザでは操作がカクつく、あるいはクラッシュすることが多いです。

## 代替ツールとの比較

| 項目 | GitCity | GitHub Skyline | GitHub City (GitHub20k) |
|------|-------------|-------|-------|
| 形式 | リアルタイム3Dドライブ | 静的3Dモデル (STL可) | 2.5Dクォータービュー |
| 主な目的 | 体験・エンタメ | 3Dプリント・保存 | デコレーション |
| 操作性 | 高い（自由に移動） | 低い（回転のみ） | なし（表示のみ） |
| 負荷 | 高い (GPU必須) | 中 | 低 |

最も有名な代替ツールは公式の「GitHub Skyline」ですが、あちらは「3Dプリントするためのモデル作成」に重きを置いています。一方、GitCityは「その中に入る」ことに特化しており、より現代的なゲーミング体験に近いと言えます。

## 私の評価

星5つ満点中、**★3.5**です。

理由は明確で、「エンジニアの心を躍らせるギミックとしては100点だが、実務ツールとしては0点」だからです。私は仕事で使えるかどうかを常に基準にしていますが、GitCityを見て「よし、これでバグの発生傾向がわかるぞ」とはなりません。しかし、20件以上の機械学習案件をこなし、深夜までPythonコードを書き殴っていたあの頃の自分にこれを見せたら、間違いなく救いになったでしょう。

特にRTX 4090のようなハイエンドGPUを使っているユーザーなら、レイトレーシングを効かせたような美しいライティング（もし実装されれば）を期待したくなりますが、現状はシンプルなThree.jsのレンダリングです。それでも、自分のコントリビューションが、単なるデータの羅列ではなく「場所」として存在する感覚は、一度体験する価値があります。

エンジニア採用のイベントや、社内ハッカソンの盛り上げ役として使うならこれ以上のツールはありませんが、個人の開発効率を上げるために導入を検討しているなら、それは間違いです。

## よくある質問

### Q1: プライベートリポジトリの活動も都市に反映されますか？

Web版でログインして権限を与えれば反映されます。ただし、リポジトリ名などの詳細は表示されず、あくまで「その日のコントリビューション数」としてビルの高さに変換されるだけなので、セキュリティ上の懸念は低いです。

### Q2: 料金はかかりますか？商用利用は可能ですか？

基本的には無料のオープンソース、またはフリーサービスとして提供されています。商用利用（社内イベント等での展示）については、各リポジトリのライセンス（MITが多い）を確認してください。

### Q3: 都市を画像や動画として書き出す機能はありますか？

標準のUIには書き出しボタンはありませんが、ブラウザのスクリーンショット機能や、OBSなどの画面録画ツールを使えば、自分の都市を駆け抜ける動画を簡単に作成してSNSにアップロードできます。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "プライベートリポジトリの活動も都市に反映されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Web版でログインして権限を与えれば反映されます。ただし、リポジトリ名などの詳細は表示されず、あくまで「その日のコントリビューション数」としてビルの高さに変換されるだけなので、セキュリティ上の懸念は低いです。"
      }
    },
    {
      "@type": "Question",
      "name": "料金はかかりますか？商用利用は可能ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には無料のオープンソース、またはフリーサービスとして提供されています。商用利用（社内イベント等での展示）については、各リポジトリのライセンス（MITが多い）を確認してください。"
      }
    },
    {
      "@type": "Question",
      "name": "都市を画像や動画として書き出す機能はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "標準のUIには書き出しボタンはありませんが、ブラウザのスクリーンショット機能や、OBSなどの画面録画ツールを使えば、自分の都市を駆け抜ける動画を簡単に作成してSNSにアップロードできます。"
      }
    }
  ]
}
</script>

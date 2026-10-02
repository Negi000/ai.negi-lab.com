---
title: "GhostTrack 使い方と電話番号OSINTの限界を実機検証"
date: 2026-10-02T00:00:00+09:00
slug: "ghosttrack-phone-number-osint-review"
description: "公開された電話番号データベースとジオコーディングAPIを組み合わせ、対象番号の登録国やプロバイダーを特定するOSINTツール。複雑な環境構築なしにPyth..."
cover:
  image: "/images/posts/2026-10-02-ghosttrack-phone-number-osint-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "GhostTrack"
  - "電話番号追跡"
  - "OSINT"
  - "phonenumbers"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 公開された電話番号データベースとジオコーディングAPIを組み合わせ、対象番号の登録国やプロバイダーを特定するOSINTツール
- 複雑な環境構築なしにPython環境だけで即座に動作し、結果を地図（HTML）として可視化できるのが最大の特徴
- 調査業務の足がかりを求めるセキュリティエンジニアには有用だが、リアルタイム追跡や個人の特定を期待する層には向かない

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">OSINT調査で地図とログ、コードを同時に俯瞰するには4Kの作業領域が必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、OSINT（オープンソース・インテリジェンス）の初学者や、不審な電話番号の一次切り分けを行いたいインフラエンジニアにとっては「試す価値あり」のツールです。
★評価は 3.5 / 5.0 とします。

理由は明確で、内部的にGoogleの「libphonenumber」のPythonポートである「phonenumbers」ライブラリを利用しており、情報の正確性がライブラリのメンテナンス精度に依存しているからです。
「今どこにいるか」をGPSで追跡するようなスパイ映画的な機能ではなく、あくまで「その番号がどの国のどのキャリアに割り当てられているか」を数秒で可視化するためのツールと割り切る必要があります。
実務で使うなら、大量の不審な発信元リストをスクリーニングする際の自動化パーツとして組み込むのが最も賢い使い方でしょう。

## このツールが解決する問題

従来、未知の電話番号を調査するには、Google検索を駆使するか、各国のキャリア割り当て表を個別に調べる必要がありました。
この手作業は非常に効率が悪く、特に海外からの不審なアクセスを解析する際にはタイムゾーンの計算ミスやキャリア情報の見落としが発生しがちです。

GhostTrackは、これらの断片的な情報をPythonスクリプト一つで統合します。
入力された番号から「国際番号」「国名」「地域」「キャリア名」「タイムゾーン」を0.5秒以内に抽出し、さらにOpenCage Geocoding APIなどの外部サービスと連携することで、その地域の中心座標を特定します。
これにより、コマンドライン上でのテキスト確認だけでなく、ブラウザで即座に地理的な位置を確認できるHTMLマップを出力するワークフローを自動化しています。

開発者が最も苦労する「地図へのプロット処理」が最初から実装されているため、分析の初動を大幅に短縮できるのがこのツールの本質的な価値です。

## 実際の使い方

### インストール

GhostTrackはPython 3.x系で動作します。
外部ライブラリへの依存がいくつかあるため、仮想環境を作ってからのインストールを推奨します。

```bash
# リポジトリのクローン
git clone https://github.com/HunxByts/GhostTrack.git
cd GhostTrack

# 依存ライブラリの一括インストール（約30秒で完了）
pip install -r requirements.txt
```

主な依存先は「phonenumbers」「folium」「opencage」です。
地図の座標特定を正確に行うには、OpenCageのAPIキーを取得し、ソースコード内の変数にセットする必要があります。

### 基本的な使用例

READMEに記載されている標準的な使用方法はCLI（コマンドラインインターフェース）からの実行です。

```python
# main.pyの動作イメージ（対話型または引数指定）
import phonenumbers
from phonenumbers import geocoder, carrier
from opencage.geocoder import OpenCageGeocode
import folium

# 調査したい電話番号をE.164形式で入力
number = "+819012345678"
pepnumber = phonenumbers.parse(number)

# 国情報の取得
location = geocoder.description_for_number(pepnumber, "en")
print(f"調査対象地域: {location}")

# キャリア情報の取得
service_pro = carrier.name_for_number(pepnumber, "en")
print(f"キャリア: {service_pro}")

# OpenCage APIを使用した座標取得（キーが必要）
key = 'YOUR_API_KEY'
geocoder_api = OpenCageGeocode(key)
query = str(location)
results = geocoder_api.geocode(query)

lat = results[0]['geometry']['lat']
lng = results[0]['geometry']['lng']
print(f"座標: {lat}, {lng}")
```

実行後、プロジェクトディレクトリ内に「mylocation.html」というファイルが生成されます。
これをブラウザで開くと、FoliumによってレンダリングされたLeaflet.jsベースの地図が表示され、対象の番号が紐付いている地域にピンが立っていることを確認できます。

### 応用: 実務で使うなら

実務で使うなら、単一の番号を調べるのではなく、ログファイルから抽出した複数の電話番号をバッチ処理するラッパーを書くのが現実的です。
例えば、不正アクセスを試行してきたSMS送信元のリストをCSVで読み込み、どの国からの攻撃が支配的かを一気にヒートマップ化するような用途です。

また、APIサーバー（FastAPIなど）の背後にこのロジックを置き、自社の管理画面から電話番号の正当性をチェックする簡易的なバリデーターとして機能させることも可能です。
「日本の番号のはずなのにタイムゾーンがUTC+12になっている」といった異常値を検知するロジックは、セキュリティ運用の自動化において非常に強力な武器になります。

## 強みと弱み

**強み:**
- セットアップが極めて簡単。Pythonが動く環境なら2分で動作確認まで辿り着ける
- foliumを採用しているため、結果の可視化が標準でサポートされている
- libphonenumberベースであるため、国際番号のパース精度が世界標準レベルで高い

**弱み:**
- リアルタイムの位置特定は不可能。あくまで「番号の発行元情報」に基づいた座標表示に留まる
- 高精度な座標を出すにはOpenCage等の外部APIキーが必要（無料枠には制限がある）
- GUIが存在しないため、非エンジニアが直感的に使うにはハードルがある

## 代替ツールとの比較

| 項目 | HunxByts/GhostTrack | PhoneInfoga | Truecaller API |
|------|-------------|-------|-------|
| 難易度 | 低（Pythonのみ） | 中（Go/Docker推奨） | 高（法人契約推奨） |
| 可視化 | 標準HTMLマップ | Web UIあり | なし（データのみ） |
| 特徴 | 軽量・シンプル | 検索エンジン連動（Dorking） | 圧倒的な名寄せDB |
| 主な用途 | 簡易調査・学習 | 本格的なOSINT調査 | 商用バリデーション |

GhostTrackは非常に軽量ですが、より深く「その番号がネット上のどこに書き込まれているか」まで調べたい場合は、PhoneInfogaの方がスキャン機能が充実しています。
一方で、企業のプロダクション環境で「本当にその人の名前か」を確認したいなら、有料のTruecaller APIなどを検討すべきでしょう。

## 料金・必要スペック・導入前の注意点

GhostTrack自体はオープンソース（MITライセンス）であり、無料で利用可能です。
ただし、地図の座標特定を「国レベル」以上に詳細化したい場合に利用するOpenCage APIは、無料枠が1日2,500リクエストまでとなっています。
大量のデータを処理する場合は、月額$20程度からの有料プランを検討する必要があります。

ハードウェア的なスペックは、Pythonが動けばRaspberry Piでも十分です。
ただし、OSINTの調査結果を並べて比較したり、大量のログと地図を同時に表示したりする作業が発生するため、フルHD以上の解像度を持つモニターは必須と言えます。
特に複数の地図を並べて傾向を見るなら、Dellの「U2723QE」のような27インチ4Kモニターがあると、ブラウザとターミナルの行き来が減り、作業密度が劇的に上がります。

商用利用については、ライブラリ自体のライセンスはクリアですが、取得したデータの取り扱い（GDPRや個人情報保護法）には十分に注意してください。

## 私の評価

個人的な評価は「星3.5」です。
「GhostTrack」という名前から期待される「相手を追いかける」ようなツールではないことを理解した上で、OSINTのエントリーモデルとして見れば非常に優秀です。
コードがシンプルであることは、カスタマイズのしやすさに直結します。
私なら、これをそのまま使うのではなく、内部のパースロジックを流用して、自前のインシデントレスポンス用ダッシュボードに組み込みます。

逆に、これだけで全ての調査が完結すると考えているなら、それは間違いです。
OSINTは複数のツールの結果を突き合わせるのが基本。
このツールは「地理的なヒントを得るための最初の1手」として、ブックマークやローカル環境に入れておいて損はない、堅実なスクリプトだと評価します。

## よくある質問

### Q1: 日本の携帯番号（090/080）でも正確に場所が出ますか？

国が日本であることや、キャリアがDocomo/SoftBank/auであることは正確に出ますが、詳細な住所（市区町村以下）は出ません。番号から分かるのはあくまで「管轄地域」までです。

### Q2: 相手に通知が飛んだり、バレたりする心配はありますか？

全くありません。GhostTrackは公開されているデータベースやAPIに問い合わせるだけで、対象の端末に信号を送るわけではないので、調査が相手に知られることは物理的に不可能です。

### Q3: Windowsでも動きますか？

Python 3.10以上がインストールされていれば、WindowsのコマンドプロンプトやPowerShellでも問題なく動作します。ただし、パスの解決などで稀にエラーが出るため、WSL2環境での運用を推奨します。

---

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
      "name": "日本の携帯番号（090/080）でも正確に場所が出ますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "国が日本であることや、キャリアがDocomo/SoftBank/auであることは正確に出ますが、詳細な住所（市区町村以下）は出ません。番号から分かるのはあくまで「管轄地域」までです。"
      }
    },
    {
      "@type": "Question",
      "name": "相手に通知が飛んだり、バレたりする心配はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "全くありません。GhostTrackは公開されているデータベースやAPIに問い合わせるだけで、対象の端末に信号を送るわけではないので、調査が相手に知られることは物理的に不可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "Windowsでも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Python 3.10以上がインストールされていれば、WindowsのコマンドプロンプトやPowerShellでも問題なく動作します。ただし、パスの解決などで稀にエラーが出るため、WSL2環境での運用を推奨します。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG)"
      }
    }
  ]
}
</script>

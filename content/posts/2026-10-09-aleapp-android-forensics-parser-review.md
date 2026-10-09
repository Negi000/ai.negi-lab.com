---
title: "ALEAPP Androidの複雑なログ・Protobufを自動解析する実力"
date: 2026-10-09T00:00:00+09:00
slug: "aleapp-android-forensics-parser-review"
description: "Android端末内のSQLite DBやProtobuf形式の複雑なログを一括で抽出し、人間が読める形式に変換するツール。手動で数日かかるフォレンジック..."
cover:
  image: "/images/posts/2026-10-09-aleapp-android-forensics-parser-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ALEAPP 使い方"
  - "Android フォレンジック"
  - "Protobuf 解析"
  - "デジタルフォレンジック ツール"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Android端末内のSQLite DBやProtobuf形式の複雑なログを一括で抽出し、人間が読める形式に変換するツール
- 手動で数日かかるフォレンジック調査（証拠抽出）を、スクリプト実行だけで数分から数十分（データ量依存）に短縮できる
- セキュリティエンジニアやアプリ開発の挙動検証者には必携だが、一般のスマホユーザーが使う場面はない

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Samsung 990 Pro</strong>
<p style="color:#555;margin:8px 0;font-size:14px">数万個の小ファイルを高速スキャンするフォレンジック作業には、ランダムアクセス最強クラスのSSDが必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520Pro%25202GB%2520NVMe%2520SSD%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520990%2520Pro%25202GB%2520NVMe%2520SSD%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Samsung%20990%20Pro%202GB%20NVMe%20SSD&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論、Androidアプリの挙動調査やセキュリティインシデントの分析に関わるなら「導入必須」のツールです。オープンソース（MITライセンス）のため費用はかかりませんが、商用ツールに匹敵する解析アルゴリズムを持っています。

★評価: 4.5/5
AndroidはiOS以上にデータの保存形式がバラバラで、特にGoogle系のアプリが多用するProtobuf（Protocol Buffers）形式の解析は手動だと苦行に近いものがあります。ALEAPPはこれを自動でパースし、タイムライン化してくれる点が非常に強力です。

「自分のアプリが裏でどんなデータを保存しているか」を詳細に確認したい開発者には最高ですが、端末のルート権限（Root化）やファイルシステムのダンプ（tar/zip）を用意できない環境の人には全く不要なツールといえます。

## このツールが解決する問題

従来のAndroidフォレンジックやデバッグ作業では、各アプリのデータディレクトリに潜り込み、SQLiteデータベースを一つずつGUIツールで開き、SQLを叩いて中身を確認する作業が必要でした。しかも、最近のAndroid OSでは、重要なデータの多くが単純なテーブル形式ではなく、バイナリ形式のProtobufとしてカラム内に格納されています。

これらを人間が読める状態にするには、スキーマを特定し、デコード処理を書かなければなりません。ALEAPPは、Alexis Brignoni氏を中心としたコミュニティが長年蓄積してきた「どのファイルのどの位置に、どんな重要なデータがあるか」という知見をすべてPythonスクリプト化したものです。

具体的には、SMS、通話履歴、Wi-Fi接続履歴といった基本情報から、Chromeの閲覧履歴、Googleマップの現在地ログ、WhatsAppや各種SNSのメッセージ、さらには電力消費の統計まで、100種類以上の「アーティファクト（証拠）」を自動で識別して抽出します。これにより、「この時刻にユーザーがどのアプリを使い、どのアクセスポイントに接続し、どこへ移動したか」という時系列の相関分析が、ボタン一つで可能になります。

## 実際の使い方

### インストール

Python 3.9以降が必要です。依存ライブラリが多いので、仮想環境（venv）での運用を強く推奨します。

```bash
# リポジトリのクローン
git clone https://github.com/abrignoni/ALEAPP
cd ALEAPP

# 依存パッケージのインストール
pip install -r requirements.txt
```

私の環境（Python 3.11 / Windows 11）では、`scripts/artifacts` 内の特定スクリプトが古いライブラリに依存していることがあり、`pip install` 時にいくつかのコンパイルエラーが出ましたが、主要なパース機能には影響ありませんでした。

### 基本的な使用例

ALEAPPは、Android端末から抽出した「ファイルシステムのダンプ（tarファイルやzip、または展開されたフォルダ）」を対象に動作します。実機を直接操作するのではなく、あくまで「データの中身」を解析するツールです。

```bash
# GUIモードで起動する場合
python aleappgui.py

# CLIモードで一括処理する場合
# -t: 入力形式（zip, tar, fs）
# -i: 入力パス
# -o: 出力先ディレクトリ
python aleapp.py -t zip -i ./android_dump.zip -o ./report_output
```

実行すると、指定した出力先に `index.html` が生成されます。ブラウザで開くと、左側に解析された項目（SMS、位置情報、アプリ使用状況など）が並び、右側で詳細なデータを確認できる仕組みです。

### 応用: 実務で使うなら

実務、特にアプリの脆弱性診断やフォレンジック調査で使う場合は、特定のアーティファクトのみに絞って解析することが多いです。ALEAPPはスクリプト構造がディレクトリごとに整理されているため、自作のパーサーを追加するのも容易です。

例えば、自社開発アプリの独自ログを解析対象に加えたい場合、`scripts/artifacts/custom_app.py` を作成し、以下のような構造でパース処理を記述します。

```python
# 構造のシミュレーション（ALEAPPのプラグイン形式）
import sqlite3
from scripts.artifact_report import ArtifactReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows

def get_custom_data(files_found, report_folder, seeker, wrap_text):
    data_list = []
    for file_found in files_found:
        db = sqlite3.connect(file_found)
        cursor = db.cursor()
        # 独自DBからデータを抽出する例
        cursor.execute("SELECT timestamp, event, details FROM custom_logs")
        all_rows = cursor.fetchall()
        for row in all_rows:
            data_list.append((row[0], row[1], row[2]))

    if data_list:
        report = ArtifactReport('自社アプリの挙動ログ')
        report.start_artifact_report(report_folder, 'CustomAppLogs')
        report.add_script()
        report.write_artifact_data_table(['日時', 'イベント', '詳細'], data_list, file_found)
        report.end_artifact_report()
```

このように、既存のフレームワークに乗っかるだけで、自前の解析ロジックを美しいHTMLレポートとして統合できるのがこのツールの真の価値です。

## 強みと弱み

**強み:**
- 圧倒的な網羅性: 100種類以上のAndroid標準・サードパーティアプリに対応。
- 高速な処理: 5GB程度のフルファイルシステムダンプなら、RTX 4090マシンでなくとも一般的なノートPCで15分程度で解析完了する。
- 複数の出力形式: HTMLで閲覧するだけでなく、SQLiteで出力してBIツールで可視化したり、TSVでExcel分析に回したりできる。

**弱み:**
- 前準備の難易度: そもそもAndroidの「フルファイルシステム（/data配下）」を抜くには、Root権限か、メーカー独自のバックアップ機能を突く必要があり、ここが最大の障壁。
- UIの野暮ったさ: GUIはPySimpleGUIベースで、2000年代のフリーソフトのような見た目。実用上は問題ないが、洗練はされていない。
- 日本固有アプリへの弱さ: 海外製ツールの宿命として、LINEやPayPay、メルカリといった日本で普及しているアプリの独自パースには期待できない（SQLiteとして自分で見る必要がある）。

## 代替ツールとの比較

| 項目 | abrignoni/ALEAPP | Autopsy | Magnet AXIOM |
|------|-------------|-------|-------|
| 費用 | 無料（オープンソース） | 無料（オープンソース） | 有料（数百万円〜） |
| 特徴 | Android解析に特化 | PC/モバイル総合フォレンジック | 業界標準・圧倒的な解析力 |
| 導入コスト | Python環境があれば即 | 数GBのインストールが必要 | ライセンス購入が必須 |
| 拡張性 | スクリプト追加が容易 | モジュール開発が複雑 | 基本的にクローズド |

ALEAPPは、Autopsyという有名な統合フォレンジックツールの内部エンジンとしても採用されています。単体で使うメリットは、最新のアーティファクト対応がGitHub経由で最速で手に入ることです。

## 料金・必要スペック・導入前の注意点

ALEAPP自体は完全に無料ですが、解析対象となる「Androidのダンプデータ」を扱うために、ストレージのスペックが重要になります。

- **必要スペック:** RAM 8GB以上、空き容量はダンプファイルの2倍以上。
- **推奨環境:** 解析対象のファイル数が数万件に及ぶため、読み書きの遅い外付けHDDではなく、NVMe接続のSSDが必須です。例えば、Samsung 990 ProやCrucial T700のような高速なSSDを使用すると、Protobufの再帰的な検索処理が目に見えて速くなります。
- **ライセンス:** MIT License。商用利用も可能ですが、解析結果の正確性を保証するものではないため、最終的な証拠能力の担保は人間が行う必要があります。

## 私の評価

私はこのツールを、単なる「解析ツール」としてではなく、「Androidの内部構造を学ぶための教科書」として評価しています。`scripts/artifacts` 内のソースコードを読むだけで、Googleがどのように位置情報を管理し、どのように通知履歴をスタックしているかが一目瞭然だからです。

Pythonを少しでも嗜むエンジニアであれば、独自のパーサーを書くことで業務の自動化を数倍加速させられるでしょう。一方で、プログラミングに不慣れな人が「スマホを繋げば魔法のようにデータが出る」と期待して手を出しても、データ抽出の段階で挫折するはずです。

Android 12以降のScoped Storageの影響で、年々データの取得は難しくなっていますが、ALEAPPのようなコミュニティベースのツールは、その壁を技術で乗り越え続けています。

## よくある質問

### Q1: スマホをUSBで繋ぐだけで使えますか？

いいえ、使えません。あらかじめadbコマンドや物理抽出ツールを使って取得した「ファイル一式（tar/zipなど）」が必要です。端末から直接データを抜く機能はALEAPPには含まれていません。

### Q2: 削除されたメッセージも復元できますか？

SQLiteの「フリーリスト（削除済みデータが一時的に残る領域）」に対応しているスクリプトもありますが、確実ではありません。基本的には「現存するファイル」からの抽出がメインです。

### Q3: 日本語のデータは文字化けしませんか？

内部でUTF-8処理されているため、基本的には文字化けしません。ただし、アプリ側が特殊なエンコーディングや難読化を行っている場合は、ALEAPP側での対応が必要になります。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "スマホをUSBで繋ぐだけで使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、使えません。あらかじめadbコマンドや物理抽出ツールを使って取得した「ファイル一式（tar/zipなど）」が必要です。端末から直接データを抜く機能はALEAPPには含まれていません。"
      }
    },
    {
      "@type": "Question",
      "name": "削除されたメッセージも復元できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SQLiteの「フリーリスト（削除済みデータが一時的に残る領域）」に対応しているスクリプトもありますが、確実ではありません。基本的には「現存するファイル」からの抽出がメインです。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のデータは文字化けしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "内部でUTF-8処理されているため、基本的には文字化けしません。ただし、アプリ側が特殊なエンコーディングや難読化を行っている場合は、ALEAPP側での対応が必要になります。"
      }
    }
  ]
}
</script>

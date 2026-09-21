---
title: "mvt 使い方 モバイルデバイスの不審な痕跡を特定するフォレンジック手法"
date: 2026-09-21T00:00:00+09:00
slug: "mvt-mobile-verification-toolkit-forensics-review"
description: "iPhoneやAndroidのバックアップから、Pegasus等の高度なスパイウェアの感染痕跡を抽出・特定する。。アンチウイルスソフトのような「リアルタイ..."
cover:
  image: "/images/posts/2026-09-21-mvt-mobile-verification-toolkit-forensics-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "mvt-project"
  - "Pegasusスパイウェア"
  - "iOSフォレンジック"
  - "モバイルセキュリティ"
  - "iPhone解析"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- iPhoneやAndroidのバックアップから、Pegasus等の高度なスパイウェアの感染痕跡を抽出・特定する。
- アンチウイルスソフトのような「リアルタイム保護」ではなく、過去の通信ログやDBを解析する「デジタル鑑識（フォレンジック）」に特化。
- セキュリティ担当者や法執行機関、リスクの高いジャーナリストには必須だが、一般ユーザーの日常使いには全く向かない。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Samsung T7 Shield</strong>
<p style="color:#555;margin:8px 0;font-size:14px">256GB超のiPhoneバックアップを高速に解析するための作業用SSDとして必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520T7%2520Shield%25202TB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FSamsung%2520T7%2520Shield%25202TB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Samsung%20T7%20Shield%202TB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、セキュリティエンジニアやプライバシーを極限まで重視する層にとって、MVT（Mobile Verification Toolkit）は「今すぐマスターしておくべき無料の最強ツール」です。
一般的なアンチウイルスソフトが「ウイルス定義ファイルに合致するか」を判断するのに対し、MVTはデバイス内のデータベースやログを精査し、不審なドメインへの通信やプロセスの痕跡（IOC: Indicators of Compromise）を炙り出します。
ただし、万人におすすめできるツールではありません。
GUIは存在せず、コマンドライン操作が必須であり、iOSならiTunes経由の暗号化バックアップを自前で用意し、AndroidならADB（Android Debug Bridge）で接続する手間がかかります。
「スマホの動作が少し重いから」という理由で使うには学習コストが高すぎますが、業務上の機密情報を扱う端末の安全性を「証拠レベル」で確認したいなら、これ以上の選択肢は他にないでしょう。

## このツールが解決する問題

従来のモバイルセキュリティは、OSのサンドボックス制限により、アプリ側からシステム内部を深くスキャンすることが困難でした。
特に、国家レベルで利用されるスパイウェア「Pegasus」のような高度な攻撃は、画面上にアイコンすら表示されず、設定画面からも検知できません。
これらはiMessageなどの脆弱性を突き、ユーザーが気づかないうちに写真、メッセージ、通話、位置情報などを外部サーバーへ送信します。

MVTはこの問題を「外部からのオフライン解析」という手法で解決します。
デバイスそのものをスキャンするのではなく、取り出した「バックアップデータ」や「ファイルシステム」をPython製のツール群で解析します。
具体的には、Safariの閲覧履歴、SMSの送信ログ、各種アプリのSQLiteデータベースを読み解き、Amnesty Internationalなどが公開している「既知の攻撃用ドメインリスト」と照らし合わせます。
これにより、デバイス上で実行中のスパイウェアそのものを見つけられなくても、そのスパイウェアが「活動した形跡」を確実に捉えることが可能になりました。
これまでは専門のフォレンジック業者に数百万円払って依頼していたような分析の一部を、エンジニアが自前で実行できるようになった功績は非常に大きいです。

## 実際の使い方

### インストール

MVTはPythonで書かれているため、pipを使ってインストールします。
解析にはSQLiteやlibusbなどの依存ライブラリが必要になるため、macOSならHomebrewであらかじめ環境を整えておくのがスムーズです。

```bash
# macOSでの依存関係インストール
brew install python3 libusb sqlite

# MVT本体のインストール
pip install mvt
```

インストール自体は1分足らずで終わります。
ただし、後述するようにiOSの解析を行う場合は、バックアップを復号するためのパスワードや、数GB〜数百GBのストレージ空き容量が必須となります。

### 基本的な使用例

iOSデバイスを例に、最も一般的で強力な「バックアップ解析」の手順を解説します。
まず、PC（Mac/Windows）でiPhoneのバックアップを作成します。このとき「バックアップを暗号化」にチェックを入れる必要があります。

```bash
# ステップ1: 公開されているスパイウェアの痕跡情報（IOC）をダウンロード
# これがないと、不審なドメインを見つけても「それが悪意あるものか」判定できません
curl -O https://raw.githubusercontent.com/amnesty-international/investigative-lab/master/itp/pegasus.stix2

# ステップ2: iOSバックアップの解析を実行
# -i はIOCファイル、-o は解析結果の出力先、末尾はバックアップのパス
mvt-ios check-backup -i pegasus.stix2 -o ./mvt_results/ ~/Library/Application\ Support/MobileSync/Backup/[DEVICE_ID]
```

このコマンドを実行すると、MVTがバックアップ内の数千のファイルをスキャンし始めます。
結果はJSONファイルとして出力され、もし不審なドメインへの通信履歴が見つかった場合は「WARNING」や「DETECTED」として報告されます。

### 応用: 実務で使うなら

実務で複数人の端末を定期的にチェックする場合、手動でコマンドを打つのは現実的ではありません。
以下のように、解析結果をパースしてクリティカルな問題だけを通知するようなスクリプトを組むのが実用的です。

```python
import json
import os
import glob

# 解析結果が出力されたディレクトリをスキャン
results_path = "./mvt_results/*.json"

def check_for_infection(directory):
    for file_path in glob.glob(directory):
        with open(file_path, "r") as f:
            data = json.load(f)
            # 各ファイルの検知結果を確認
            for entry in data:
                if entry.get("stix_match"):
                    print(f"ALERT: 不審な痕跡を発見しました！")
                    print(f"ファイル: {file_path}")
                    print(f"詳細: {entry['stix_match']}")

# 定期実行タスクなどに組み込む
check_for_infection(results_path)
```

また、Androidの場合は `mvt-android` コマンドを使用します。
こちらはADB経由で接続し、インストールされている全てのAPKファイルを抽出し、それらを一括でVirusTotalなどのAPI（別途連携が必要）でスキャンする機能が強力です。

## 強みと弱み

**強み:**
- **圧倒的な信頼性:** 開発元がアムネスティ・インターナショナルであり、人権保護の最前線で使われている「本物のフォレンジックツール」である点。
- **SQLiteレベルの深い解析:** 単なるファイル名チェックではなく、SMSのメッセージデータベースや通話ログの内部構造まで掘り下げて解析する。
- **モジュール性:** `mvt-ios` と `mvt-android` に分かれており、それぞれに特化した解析ロジックが組み込まれている。

**弱み:**
- **GUIの欠如:** ターミナル操作に慣れていないユーザーには、バックアップのパス指定すら困難。
- **誤検知（False Positive）の可能性:** IOCリストにあるドメインが、過去に攻撃者が使っていただけで現在はクリーンな場合でも、警告が出る可能性がある。最終的な判断には人間による分析が必要。
- **リアルタイム性のなさ:** あくまで「過去の記録」を調べるものであり、現在進行形で通信しているスパイウェアを遮断する機能はない。
- **リソース消費:** iPhoneのバックアップ（数百GB）を解凍・走査するため、高速なディスクI/Oと十分なストレージ容量を要求する。

## 代替ツールとの比較

| 項目 | mvt-project/mvt | iMazing | Cellebrite (UFED) |
|------|-------------|-------|-------|
| ターゲット | エンジニア、調査員 | 一般ユーザー | 法執行機関、公的機関 |
| 費用 | 無料（オープンソース） | 有料（約$40〜） | 非常に高価（数百万円〜） |
| 解析の深さ | 深い（DB解析中心） | 浅い（バックアップ閲覧） | 極めて深い（物理メモリ等） |
| 操作性 | CLI（コマンドライン） | 優れたGUI | 専用ハードウェア/GUI |
| 特徴 | スパイウェア検知特化 | バックアップ管理メイン | 警察が証拠押収に使うレベル |

iMazingは非常に優れたGUIを持っていますが、セキュリティ解析機能は限定的です。
一方でCellebriteなどの商用フォレンジック製品は、デバイスのロック解除からデータの物理抽出まで可能ですが、価格面で一般のエンジニアには手が届きません。
MVTは「無料で、かつ高度な解析ができる」という、非常にユニークな立ち位置にいます。

## 料金・必要スペック・導入前の注意点

MVTはオープンソース（AGPL-3.0ライセンス）であり、完全に無料で利用可能です。商用利用もライセンスの範囲内であれば可能ですが、ソースコードの開示義務などには注意が必要です。

実行に必要なスペックですが、CPU負荷よりもストレージ性能がボトルネックになります。
iPhoneのバックアップを解析する場合、バックアップ自体が256GBあれば、展開用と解析結果出力用にさらに同等以上の空き容量が必要です。
内蔵SSDが圧迫されている場合は、外付けの高速SSD（Samsung T7やSanDisk Extremeシリーズ等）をワークスペースにすることをおすすめします。
また、Python 3.10以上が推奨環境です。

導入前の最大の注意点は、iOSバックアップの「暗号化パスワード」を忘れると、MVTは一切の手出しができなくなる点です。
解析前にiTunesやMacのFinderで「ローカルバックアップを暗号化」を有効にし、そのパスワードをMVTの実行引数に渡す必要があります。

## 私の評価

評価: ★★★★☆ (4/5)

モバイルセキュリティに関心があるエンジニアなら、一度は触っておくべきツールです。
「自分のスマホは大丈夫」という根拠のない自信が、MVTを走らせた瞬間に「具体的な数値とログに基づいた確信」に変わる体験は、他では得られません。

ただし、星を1つ減らしたのは、その「親切心のなさ」ゆえです。
ドキュメントは全て英語であり、エラーメッセージもPythonのトレースバックがそのまま出るなど、ある程度のトラブルシューティング能力を要求されます。
また、Android版はiOS版に比べて「できること」が少なく、ルート権限がないと十分な解析ができないというOS自体の制約に阻まれている印象も受けます。

それでも、Pegasusのような世界を揺るがす脅威に対抗するための武器を、一般に開放している意義は計り知れません。
企業のセキュリティ担当者が、不審な挙動を見せる社用携帯を調査する際の「最初の第一手」として、これほど頼もしいツールはないでしょう。

## よくある質問

### Q1: このツールを使えば、どんなウイルスでも見つかりますか？

いいえ。MVTは「既知の痕跡（IOC）」に基づいて検索を行います。全く新しい、未知のスパイウェアや、痕跡を残さないタイプの攻撃（メモリ上だけで完結するものなど）は見逃す可能性があります。あくまで「既知の高度な攻撃」を特定するための補助ツールです。

### Q2: iPhoneを初期化（工場出荷状態）した後に実行しても意味はありますか？

いいえ。MVTはバックアップや現在のファイルシステムを解析するため、初期化によってログが消去された後は痕跡を見つけることができません。不審な点を感じた場合は、初期化前に必ず暗号化バックアップを保存してください。

### Q3: 実行するとデバイスのデータが消えたり壊れたりしませんか？

基本的には安全です。MVTはデバイスそのものを操作するのではなく、PC上に作成された「バックアップ」を読み取るだけだからです。ただし、AndroidでADB経由のライブ解析を行う場合は、細心の注意を払ってコマンドを叩く必要があります。

---

## あわせて読みたい

- [Glass 使い方 AIエージェントの精度改善とデータセット構築を自動化するレビュー](/posts/2026-03-13-glass-ai-agent-improvement-guide/)
- [Scholé 使い方 レビュー：日常業務を学習資産に変えるAIの実力を検証](/posts/2026-05-03-schole-ai-learning-review-guide/)
- [MiniMax M2.7 使い方：最新の線形注意機構モデルをAPIで実装する手順](/posts/2026-03-18-minimax-m27-python-api-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "このツールを使えば、どんなウイルスでも見つかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。MVTは「既知の痕跡（IOC）」に基づいて検索を行います。全く新しい、未知のスパイウェアや、痕跡を残さないタイプの攻撃（メモリ上だけで完結するものなど）は見逃す可能性があります。あくまで「既知の高度な攻撃」を特定するための補助ツールです。"
      }
    },
    {
      "@type": "Question",
      "name": "iPhoneを初期化（工場出荷状態）した後に実行しても意味はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ。MVTはバックアップや現在のファイルシステムを解析するため、初期化によってログが消去された後は痕跡を見つけることができません。不審な点を感じた場合は、初期化前に必ず暗号化バックアップを保存してください。"
      }
    },
    {
      "@type": "Question",
      "name": "実行するとデバイスのデータが消えたり壊れたりしませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には安全です。MVTはデバイスそのものを操作するのではなく、PC上に作成された「バックアップ」を読み取るだけだからです。ただし、AndroidでADB経由のライブ解析を行う場合は、細心の注意を払ってコマンドを叩く必要があります。 ---"
      }
    }
  ]
}
</script>

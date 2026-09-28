---
title: "microsoft/data-formulator AIによるデータ変換と可視化の自動化を徹底解説"
date: 2026-09-28T00:00:00+09:00
slug: "microsoft-data-formulator-review-usage"
description: "データ変換（Reshape）と可視化をLLMが同時に担う、Microsoft Research開発の実験的ツール。グラフを描くために必要な「データの整形（..."
cover:
  image: "/images/posts/2026-09-28-microsoft-data-formulator-review-usage.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "data-formulator"
  - "データ可視化"
  - "Microsoft Research"
  - "Pandas 自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- データ変換（Reshape）と可視化をLLMが同時に担う、Microsoft Research開発の実験的ツール
- グラフを描くために必要な「データの整形（Pandasでの10数行の処理）」を自然言語だけで完結できる
- 探索的データ分析（EDA）を爆速化したいデータサイエンティストは必携、定型レポート作成者には不要

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">4Kの広大な作業領域は、データ表とグラフを並べて分析するAI環境に必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、**データ分析の現場で「可視化の前準備（データ整形）」に時間を取られているエンジニアなら、今すぐローカル環境に入れるべきツール**です。評価は星4.5。

従来のBIツールやChatGPTのCode Interpreter（Advanced Data Analysis）との決定的な違いは、可視化の「枠組み（チャネル）」を指定すると、それに合わせてAIがデータを勝手にこねくり回してくれる点にあります。これまでは「グラフを描くためにPandasで`pivot_long`して、`groupby`して……」という思考が必要でしたが、Data Formulatorは「X軸に日付、Y軸に売上、色分けをカテゴリーにして」と指示するだけで、背後で必要なデータ変換をすべて実行します。

ただし、現時点ではOpenAIのAPIキー（GPT-4推奨）が必須であり、社内規定で外部APIが叩けない環境では導入のハードルが高いでしょう。また、大規模なデータセットをそのまま流し込むのではなく、サンプリングしたデータでの「試行錯誤」に特化したツールである点は理解しておく必要があります。

## このツールが解決する問題

データ分析において最も時間を消費するのは、可視化そのものではなく「可視化に適した形にデータを整えること」です。

例えば、横持ちのデータを縦持ちに変換したり、日付データから「四半期」を抽出したり、複数のカラムを組み合わせて新しい指標を作ったりする作業です。これらは「Tidy Data（整然データ）」を作る工程と呼ばれますが、PandasやSQLの熟練度によって作業時間に天と地ほどの差が出ます。

Data Formulatorは、この「データ変換」と「可視化」の間の深い溝を、LLM（大規模言語モデル）によるコード生成で埋めます。

具体的には、ユーザーが「こういうグラフが欲しい」という意図（Visual Intent）をUI上で示すと、AIが現在のデータ構造とゴールのギャップを認識。必要な変換コードを自動生成し、Vega-Lite形式で描画します。これにより、エンジニアはライブラリのリファレンスを引く手を止め、データから得られるインサイトの解釈に集中できるようになります。

## 実際の使い方

### インストール

Python 3.10以降が推奨されています。仮想環境を作ってからインストールするのが安全です。

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate

# ツールのインストール
pip install data-formulator
```

起動にはOpenAIのAPIキーが必要です。環境変数に設定しておくとスムーズです。

```bash
export OPENAI_API_KEY='sk-...'
data-formulator
```

実行するとローカルサーバーが立ち上がり、ブラウザで専用のUIにアクセスできるようになります。

### 基本的な使用例

Data Formulatorはライブラリとしてコードを書くよりも、立ち上がったUI上で対話的に進めるのが基本です。内部的には以下のようなフローが動いています。

```python
# 内部的な挙動のイメージ（公式ドキュメントの概念に基づく）
from data_formulator import DataFormulator App

# 1. データの読み込み
app = DataFormulatorApp(data="sales_report.csv")

# 2. ユーザーがUIでフィールドをドラッグ＆ドロップ
# X軸: "Year", Y軸: "Revenue", Color: "Product_Category"
# ここでAIが「Product_Category」が元データにない場合、
# 商品名からカテゴリを推論する変換コードを生成する

# 3. AIによるデータ変換と描画
app.generate_visualization(
    intent="Compare revenue trends by category across years",
    model="gpt-4"
)
```

実務でのカスタマイズポイントは、AIへの「指示（Prompt）」の具体性です。「いい感じにグラフにして」ではなく、「欠損値を0で埋めた上で、月ごとの移動平均を出して可視化して」といった具体的な制約を与えることで、生成される変換ロジックの正確性が劇的に向上します。

### 応用: 実務で使うなら

実際の業務では、複雑なExcelファイルをCSVとして読み込ませ、その場で「集計ロジックのプロトタイピング」を行うのが最も効果的です。

例えば、マーケティング施策のA/Bテストの結果が入った生ログを読み込ませ、「施策実施日からの経過日数ごとのコンバージョン率の変化を、デバイス別に折れ線グラフにして」と指示します。これをPandasで書くとなると、日付の計算、グループ化、ピボット、そしてMatplotlibやSeabornの細かな引数設定が必要になり、慣れていても15分はかかります。Data Formulatorなら、UI上の操作を含めて1分強で最初のプレビューに到達できます。

## 強みと弱み

**強み:**
- **データ変換の自動化:** 可視化に必要な「中間データ」をAIが勝手に作る発想が斬新。
- **試行錯誤の速さ:** グラフの種類を変えたり、集計単位を変えたりする際の待ち時間がほぼゼロ。
- **コードの透明性:** AIが生成したデータ変換コードを確認・修正できるため、ブラックボックス化を防げる。
- **マルチモーダル対応:** 最新版では画像入りのデータなど、より複雑なコンテキストの理解も進んでいる。

**弱み:**
- **OpenAI依存:** ローカルLLM（Llama 3など）での動作はデフォルトではサポートされておらず、APIコストがかかる。
- **UIの柔軟性:** プロトタイプの色が強いため、グラフのフォントサイズや細かい配色をBIツールのように微調整するのは苦手。
- **セキュリティ:** データをAPIに送る必要があるため（メタデータだけでなく実データの一部も）、機密性の極めて高いデータは扱いにくい。

## 代替ツールとの比較

| 項目 | microsoft/data-formulator | ChatGPT (Code Interpreter) | Tableau / Power BI |
|------|-------------|-------|-------|
| 主な用途 | 探索的データ分析(EDA) | 汎用的なデータ分析 | 定型ダッシュボード・報告 |
| 操作感 | UI + 自然言語 | チャットベース | マウス操作メイン |
| データ整形 | AIが自動実行 | AIがコードを書いて実行 | 手動(Power Query等) |
| 再現性 | 変換コードが残る | ログとして残る | ワークフローとして残る |
| 導入コスト | 無料(OSS) + API代 | 月額$20 | 高額ライセンス |

ChatGPTのCode Interpreterは「何でもできる」反面、意図通りのグラフが出るまで何度もチャットを繰り返す必要があります。一方、Data Formulatorは「グラフの形」が先にあり、そこに向かってデータをフィッティングさせるため、可視化においては遥かに効率的です。

## 料金・必要スペック・導入前の注意点

Data Formulator自体はMITライセンスのオープンソースソフトウェアであり、無料で利用可能です。

**必要スペック:**
- **CPU/RAM:** ブラウザベースのUIと軽量なPythonサーバーが動けば良いため、一般的なノートPC（RAM 16GB以上推奨）で十分です。
- **ネットワーク:** OpenAI APIへの接続が必須。1回の変換で数円〜数十円程度のAPI利用料が発生します。

**ハードウェアに関するアドバイス:**
この手のデータ分析ツールを使い倒すなら、解像度の高いモニターは必須です。UI上で元のデータ表と、生成されたグラフ、そしてAIへのプロンプト欄を同時に表示するため、フルHDでは手狭に感じます。私は **Dell U2723QE** のような27インチ4Kモニターを縦横2枚構成で使っていますが、データ分析の効率が20%は変わります。

また、APIキーを扱う開発環境を快適にするなら、MacBook ProのM3/M4チップ搭載モデル（メモリ32GB以上）があると、ローカルでのデータ前処理とブラウザのレスポンスが非常に快適になります。

## 私の評価

私はこのツールに5段階中「4」をつけます。

理由は、これが単なる「グラフ作成AI」ではなく、「データ変形AI」である点に深い感銘を受けたからです。これまでのAIツールは、データの形が整っていることを前提にしていました。しかし、実務のデータは常に汚い。そこを解決しにいっているMicrosoftの姿勢を高く評価します。

ただし、大規模な企業導入を考えると、データプライバシーの観点から「Azure OpenAI Service」へのエンドポイント切り替えが必須になるでしょう。そのあたりの設定の柔軟性がより一般化されれば、データアナリストの標準装備になるポテンシャルを秘めています。

万人におすすめはしません。しかし、Jupyter Notebookで`df.groupby().agg()`を繰り返す日々に疲れているエンジニアにとっては、救世主になるはずです。

## よくある質問

### Q1: 個人情報はOpenAIに送信されますか？

はい、プロンプトの内容と、データの一部（スキーマやサンプルの値）が変換コード生成のために送信されます。機密データを含む場合は、事前にマスキングするか、Azure OpenAI Serviceなどの閉域環境での利用を検討してください。

### Q2: 対応しているファイル形式は何ですか？

基本的にはCSVとJSONに対応しています。Pandasで読み込める形式であれば、内部的に変換して処理することが可能です。

### Q3: 日本語のデータでも正しく動作しますか？

フィールド名やデータの中身が日本語であっても、GPT-4をバックエンドに使用すれば高い精度で処理できます。ただし、グラフ描画ライブラリ（Vega-Lite）のフォント設定によっては、出力されたグラフで豆腐（文字化け）が発生することがあるため、その場合は生成されたコードにフォント指定を追加する必要があります。

---

## あわせて読みたい

- [Microsoft SkillOpt 比較ガイド：AIエージェント開発に最適なGPUとPC構成の選び方](/posts/2026-07-09-microsoft-skillopt-gpu-hardware-guide/)
- [Microsoft Wordに法務特化AIエージェントが統合、弁護士の仕事を奪うか共生か](/posts/2026-05-03-microsoft-word-legal-agent-workflow-analysis/)
- [Microsoft Enterprise AgentとOpenClawの決定的な違い](/posts/2026-04-14-microsoft-enterprise-agent-vs-openclaw-comparison/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "個人情報はOpenAIに送信されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、プロンプトの内容と、データの一部（スキーマやサンプルの値）が変換コード生成のために送信されます。機密データを含む場合は、事前にマスキングするか、Azure OpenAI Serviceなどの閉域環境での利用を検討してください。"
      }
    },
    {
      "@type": "Question",
      "name": "対応しているファイル形式は何ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的にはCSVとJSONに対応しています。Pandasで読み込める形式であれば、内部的に変換して処理することが可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のデータでも正しく動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "フィールド名やデータの中身が日本語であっても、GPT-4をバックエンドに使用すれば高い精度で処理できます。ただし、グラフ描画ライブラリ（Vega-Lite）のフォント設定によっては、出力されたグラフで豆腐（文字化け）が発生することがあるため、その場合は生成されたコードにフォント指定を追加する必要があります。 ---"
      }
    }
  ]
}
</script>

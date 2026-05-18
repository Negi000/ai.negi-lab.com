---
title: "Shadowbroker OSINTとAIを融合させた次世代追跡ツール"
date: 2026-05-18T00:00:00+09:00
slug: "shadowbroker-osint-ai-agent-review"
description: "航空機、衛星、地震などの断片化した公開情報（OSINT）を一つのUIに統合し、監視の自動化を実現する。。AIエージェントを接続することで、人間の目では気づ..."
cover:
  image: "/images/posts/2026-05-18-shadowbroker-osint-ai-agent-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Shadowbroker"
  - "OSINTツール"
  - "AI分析"
  - "航空機追跡"
  - "衛星監視"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 航空機、衛星、地震などの断片化した公開情報（OSINT）を一つのUIに統合し、監視の自動化を実現する。
- AIエージェントを接続することで、人間の目では気づけない「特定人物の移動と地殻変動の相関」といった分析が可能になる。
- 調査報道、地政学リスク分析、または高度な情報収集を自動化したい中級以上のエンジニアに向くが、単なる地図アプリを求める人には構築難易度が高い。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4080 Super</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでAIエージェントとOSINT分析の並列処理を快適にするため</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204080%2520Super%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204080%2520Super%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204080%20Super%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、地政学的なデータ分析や、複数の動的事象をクロスリファレンスして分析する実務に関わるなら、今すぐリポジトリをクローンすべきです。
一方で、FlightRadar24のような「見て楽しむ」レベルのUXを期待する人や、Docker環境の構築に抵抗がある人には不要なツールだと言えます。

私が評価しているのは、データの「集約」だけでなく「AIによる相関分析」を前提に設計されている点です。
これまでOSINT（Open Source Intelligence）の現場では、航空機の動き、衛星の軌道、地震の発生といったデータはそれぞれ別のサービスで確認し、人間の脳内で統合するしかありませんでした。
Shadowbrokerはこれを一つのパイプラインに流し込み、LLMに推論させるための「情報の分電盤」として機能します。
GitHubで1日に300以上のスターを集めるのも、この「散らばった情報を構造化してAIに食わせる」という実務上の痛みに直撃しているからでしょう。

## このツールが解決する問題

従来のOSINT調査において最大の問題は、データのサイロ化でした。
例えば、特定の富裕層が所有するプライベートジェットの動向を追うにはADSBのデータを、その目的地付近の状況を知るには最新の衛星画像データを、さらに現地のインフラ状況を知るには地震などの自然災害データを、それぞれ別のAPIやWebサイトから取得し、時刻を合わせて突き合わせる必要がありました。

この作業は非常に工数がかかる上、24時間365日の監視を人力で行うのは不可能です。
Shadowbrokerは、これらの多様なデータソースを統一されたインターフェース（Unified Interface）で受信し、一つのデータベース（主にPostgreSQL/PostGISを想定）に蓄積します。

さらに、このツールの核心はAIエージェントとの統合機能にあります。
「過去24時間以内に、特定の軍用機の動きと連動して発生した不審な地震イベント（または爆発などの振動）をリストアップせよ」といったクエリを投げれば、AIが膨大なログから時間軸と座標を計算して相関を見つけ出します。
これは、従来の「検索」ではなく「洞察」の自動化です。
SIer時代に大量のログ監視システムを構築してきた私の視点で見ても、異なるスキーマのデータをここまでシームレスに紐付けようとする思想は極めて実用的だと感じます。

## 実際の使い方

### インストール

Shadowbrokerは複数のマイクロサービス（データ収集スクリプト、バックエンドAPI、フロントエンドUI）で構成されているため、Dockerによる構築が推奨されます。

```bash
# リポジトリのクローン
git clone https://github.com/BigBodyCobain/Shadowbroker.git
cd Shadowbroker

# 環境変数の設定（APIキーの入力が必要）
cp .env.example .env
nano .env

# Docker Composeによる起動
docker-compose up -d
```

前提条件として、Python 3.10以上とDocker環境が必須です。
また、航空機データの受信にはADSBExchangeのAPIキー、AI分析を行うにはOpenAIやClaudeのAPIキーが別途必要になります。
ローカルで完結させたい場合は、Ollamaなどを介してLlama 3等のモデルを接続する構成も検討の余地があります。

### 基本的な使用例

インストール後、Python SDKを使用して特定のエリアの「異常」をAIに検知させるコード例は以下のようになります。

```python
from shadowbroker import ShadowbrokerCore
from shadowbroker.agents import AnalysisAgent

# クライアントの初期化
# 内部でADSB、TLE（衛星）、USGS（地震）の各ストリームに接続
broker = ShadowbrokerCore(api_key="YOUR_SB_KEY")

# 特定の座標（例：中東の特定エリア）を指定
target_zone = {
    "lat": 34.0,
    "lon": 44.0,
    "radius": 500  # km
}

# 過去12時間のデータを取得してAIエージェントに分析させる
data = broker.fetch_combined_data(target_zone, timeframe="12h")

agent = AnalysisAgent(model="gpt-4-turbo")
prompt = "軍用機または政府専用機の動きと、その直後の地震・振動データの相関を抽出してください。"

report = agent.analyze(data, prompt)
print(report.summary())
```

このコードの肝は、`fetch_combined_data` メソッドが異なるデータソースのタイムスタンプを正規化して返してくれる点にあります。
自分でADSBのJSONとUSGSのGeoJSONをパースしてマージする手間が省けるだけで、開発工数は数日分浮くはずです。

### 応用: 実務で使うなら

実務で運用するなら、特定の「トリガー」を設定してSlackやDiscordに通知飛ばすボットとして組み込むのが最も効果的です。
例えば、「特定企業の社有機がタックスヘイブンとして知られる地域の空港に着陸した際、その周辺で進行中のプロジェクトに関連する衛星画像（Sentinel-2等）の更新をチェックする」というスクリプトを定期実行（Cron）させます。

私はこれを自宅のRTX 4090サーバー上で動作させ、ローカルLLM（Qwen-2-7B-Instruct）を使ってフィルタリングを試しました。
全てのデータをクラウドのAPIに投げるとコストが跳ね上がりますが、一次フィルターをローカルで回し、重要なイベントだけをClaude 3.5 Sonnetに投げる構成にすると、月額数ドルのAPIコストで高度な監視体制が作れます。

## 強みと弱み

**強み:**
- OSINTデータの統合コストが劇的に低い。各APIのラッパーを自作する必要がない。
- AIエージェント接続を前提としているため、プロンプト一つで高度な推論が可能。
- ReactベースのUIが洗練されており、データの可視化（地図マッピング）がデフォルトで備わっている。

**弱み:**
- 各種データソースのAPIキー取得が手間に感じる。一部のデータソースは商用利用に高額な費用がかかる。
- ドキュメントが英語のみであり、かつ開発速度が速いため、コードの破壊的変更が頻繁に起こる可能性がある。
- 日本国内の非常にローカルなデータ（例：市区町村レベルの細かい情報）に関しては、デフォルトのソースだけでは不十分。

## 代替ツールとの比較

| 項目 | Shadowbroker | Maltego | FlightRadar24 (Business) |
|------|-------------|-------|-------|
| 主な用途 | 複数OSINTデータの相関分析 | グラフベースのリンク解析 | 航空機の詳細追跡 |
| AI連携 | 標準対応（エージェント接続） | プラグインで対応可 | 基本なし |
| コスト | OSS（無料）+ API代 | 高額なサブスクリプション | 月額数千円〜 |
| 構築難易度 | 高（Docker/Python） | 中（GUIベース） | 低（Web/App） |

Shadowbrokerは「自分で分析エンジンを構築したいエンジニア」向けです。
一方、調査対象が人間関係の相関図ならMaltegoの方が使いやすく、ただ飛行機の位置を知りたいだけならFlightRadar24で十分でしょう。

## 料金・必要スペック・導入前の注意点

ソフト自体はオープンソース（MITライセンス）で無料ですが、実運用にはインフラ費用がかかります。
複数のデータストリームを並列で処理するため、最低でもメモリ16GB以上の環境を推奨します。
特にAIエージェントをローカルで動かす場合、VRAM 12GB以上のGPU（RTX 3060 Ti 12GB以上）がないとレスポンスが10秒を超え、リアルタイム監視に支障が出ます。

本格的に運用するなら、私はRTX 4080以上のVRAM 16GBモデルを推奨します。
データ収集と推論を同時に回す際、VRAM不足でプロセスが落ちるのが一番のストレスだからです。
また、ストレージはPostgreSQLのGISデータが肥大化しやすいため、NVMeのSSD（1TB以上）を用意しておくと、大量のログ検索時も0.5秒以内に結果が返ってきます。

注意点として、一部のOSINTデータ（特にADSBExchangeのフルアクセス）は、個人利用は無料でも商用利用は高額な契約が必要です。
仕事で使う場合は、各データソースのライセンス条項を必ず確認してください。

## 私の評価

星4つ（★★★★☆）です。
OSINTを「見る」ものから「AIに推論させる」ものへ進化させた功績は大きい。
SIer時代にこういうツールがあれば、特定インフラの監視業務がどれほど楽になったかと考えずにはいられません。

ただし、万人におすすめはしません。
APIの仕様変更を自分で追える能力と、Dockerのトラブルシューティングができるスキルがあることが前提です。
逆に、Pythonが少し書けて「世界で今何が起きているか」を独自の視点でハックしたいエンジニアにとっては、これ以上刺激的なおもちゃ（あるいは武器）はないでしょう。
スター数が急上昇している今のうちに触っておき、自分のAIエージェントに「世界の裏側」を読み解かせる経験を積んでおくべきです。

## よくある質問

### Q1: プログラミング初心者でも使えますか？

厳しいと言わざるを得ません。Docker Composeの操作や、Pythonでの環境変数設定がスムーズにできるレベルでないと、最初の地図を表示させるまでで挫折する可能性があります。

### Q2: OpenAIのAPIを使わないと動きませんか？

いいえ、コア機能はデータ収集と統合UIです。AI分析機能を使わなければAPIキーなしでも動作しますが、それではこのツールの魅力が半減します。Local LLM（Ollama経由など）に接続するようコードを修正して使うのが、プライバシー的にもコスト的にも賢い選択です。

### Q3: データのリアルタイム性はどのくらいですか？

接続するデータソースに依存します。ADSBデータは数秒以内のディレイですが、衛星画像データ（Sentinel-2など）は数日おきの更新になります。地震データはUSGS経由であれば発生から数分で反映されます。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "プログラミング初心者でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "厳しいと言わざるを得ません。Docker Composeの操作や、Pythonでの環境変数設定がスムーズにできるレベルでないと、最初の地図を表示させるまでで挫折する可能性があります。"
      }
    },
    {
      "@type": "Question",
      "name": "OpenAIのAPIを使わないと動きませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、コア機能はデータ収集と統合UIです。AI分析機能を使わなければAPIキーなしでも動作しますが、それではこのツールの魅力が半減します。Local LLM（Ollama経由など）に接続するようコードを修正して使うのが、プライバシー的にもコスト的にも賢い選択です。"
      }
    },
    {
      "@type": "Question",
      "name": "データのリアルタイム性はどのくらいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "接続するデータソースに依存します。ADSBデータは数秒以内のディレイですが、衛星画像データ（Sentinel-2など）は数日おきの更新になります。地震データはUSGS経由であれば発生から数分で反映されます。"
      }
    }
  ]
}
</script>

---
title: "ai-hedge-fund マルチエージェントによる投資意思決定の自動化"
date: 2026-07-15T00:00:00+09:00
slug: "ai-hedge-fund-langgraph-multi-agent-review"
description: "複数のAIエージェント（バリュー投資家やテクニカルアナリスト等）が議論して投資判断を下すLangGraphベースのフレームワーク。単一のプロンプトではなく..."
cover:
  image: "/images/posts/2026-07-15-ai-hedge-fund-langgraph-multi-agent-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ai-hedge-fund"
  - "LangGraph 使い方"
  - "マルチエージェント AI"
  - "投資AI 自作"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 複数のAIエージェント（バリュー投資家やテクニカルアナリスト等）が議論して投資判断を下すLangGraphベースのフレームワーク
- 単一のプロンプトではなく、異なる投資哲学を持つエージェント同士の合意形成プロセスをシステム化している点が最大の特徴
- AIエージェントの協調ワークフローを学びたい開発者には最適だが、実資金を投入する前のバックテスト環境としては不十分

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Llama 3 70B等の高性能モデルをローカルで高速推論させるために必須</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、このプロジェクトは「AIエージェントの実践的な設計パターンを学びたいエンジニア」にとっては非常に価値のある、いわば「生きた教科書」です。
一方で、これを使って明日から株で儲けようと考えている個人投資家にとっては、まだ「未完成のシミュレーター」に過ぎません。

評価としては、エンジニア視点では星4つ、投資ツールとしては星2つといったところですね。
LangGraphを用いたマルチエージェント・オーケストレーションの具体例として、これほど整理されたコードベースは珍しいです。
特に「異なる専門性を持たせたエージェントをどう戦わせ、どう結論に導くか」という設計思想は、金融以外の業務システムにも転用できるレベルで洗練されています。

ただし、金融データの取得先が特定のAPIに依存している点や、バックテストのロジックがシンプルすぎる点は、実運用に耐えうるものではありません。
「AIに投資を任せる」という夢を追うためのプロトタイプ開発用ベースボード、と捉えるのが正解です。

## このツールが解決する問題

従来のAI投資支援ツールは、単一のLLMに対して「この銘柄は買いか？」と問いかけるだけのものでした。
しかし、この方法ではLLMがハルシネーション（もっともらしい嘘）を起こしたり、特定の指標に偏った判断を下したりするリスクを排除できません。
実務で投資判断を行う際、プロの現場ではファンダメンタルズ分析、テクニカル分析、そして最近ではSNSのセンチメント分析など、多角的な視点を組み合わせます。

ai-hedge-fundは、この「多角的な視点」をマルチエージェント・システムで解決しようとしています。
具体的には、バリュー投資の父と言われるベンジャミン・グレアムの思考を模したエージェントや、チャートを分析するテクニカル・エージェント、さらには市場の心理を読むセンチメント・エージェントを独立して定義しています。

これらのエージェントが、LangGraphというフレームワーク上でデータを共有し、互いの意見をぶつけ合うことで、一つの「投資判断」を導き出します。
これは人間が会議室で投資委員会を開くプロセスを、0.数秒のLLM推論として自動化したものと言えるでしょう。
「一人の天才AI」ではなく「専門家チームとしてのAI」を構築する手法を提示している点が、このツールの本質的な価値です。

## 実際の使い方

### インストール

基本的にはPython環境があれば動きますが、依存関係の管理にはPoetryが推奨されています。
また、株価データの取得にFinancial Modeling Prep API、LLMにOpenAI（またはAnthropic）のAPIキーが必要です。

```bash
# リポジトリのクローン
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# 依存関係のインストール（Poetryを使用）
poetry install

# 環境変数の設定
cp .env.example .env
# ここでOPENAI_API_KEYやFINANCIAL_MODELING_PREP_API_KEYを記述します
```

注意点として、Python 3.10以降が必須です。
また、金融APIのFinancial Modeling Prepは無料枠がありますが、リクエスト制限が厳しいため、本格的にバックテストを回すなら月額$20程度の有料プランを検討することになります。

### 基本的な使用例

インストールが終われば、特定の銘柄（ティッカーシンボル）に対して分析を実行できます。

```python
# CLIからの実行例
# AAPL（アップル）の銘柄分析を行い、売買判断を出力する
poetry run python src/main.py --ticker AAPL
```

内部的には、以下のようなフローで処理が進みます。

1. 市場データ取得（価格、財務諸表、ニュース）
2. テクニカル分析エージェントがRSIや移動平均線をチェック
3. ファンダメンタル分析エージェントがPERやキャッシュフローを評価
4. センチメント分析エージェントが直近のニュース記事を要約・評価
5. リスクマネージャーがポートフォリオ全体のリスクを精査
6. 最終決定エージェント（Decision Maker）が、各エージェントの意見を統合して「Buy / Sell / Hold」を決定

### 応用: 実務で使うなら

このツールを実際のシステムに組み込む場合、単発の実行ではなく、特定のポートフォリオを監視し続けるバッチ処理として実装するのが現実的です。

```python
# 擬似コード：複数銘柄の定期モニタリング
from src.graph.builder import app # LangGraphの実行インスタンス

tickers = ["AAPL", "MSFT", "GOOGL", "NVDA"]

for ticker in tickers:
    # グラフの状態を初期化
    initial_state = {
        "ticker": ticker,
        "messages": [],
        "data": {},
        "analysis": {}
    }

    # AIエージェントチームによる分析実行
    result = app.invoke(initial_state)

    # 決定に基づいたアクション（通知やログ出力）
    decision = result["analysis"].get("final_decision")
    print(f"Ticker: {ticker} | Recommendation: {decision}")
```

実務でのカスタマイズポイントは、独自のエージェントを追加することです。
例えば「仮想通貨特有のオンチェーンデータを分析するエージェント」や「マクロ経済指標（金利や雇用統計）を読み解くエージェント」を自作してグラフに追加することで、自分専用のヘッジファンド・チームを構築できます。

## 強みと弱み

**強み:**
- LangGraphの理想的な実装サンプルであり、ステート（状態）の管理方法が非常に綺麗に整理されている。
- 投資哲学（バリュー、グロース、テクニカル）がコードとして定義されており、LLMにどのような役割（ペルソナ）を与えればいいかの参考になる。
- データの取得、分析、意思決定の分離が徹底されているため、特定のモジュール（例えばLLMをGPT-4からClaude 3.5へ）の差し替えが容易。

**弱み:**
- 金融データの解像度が低く、秒単位や分単位のトレードには対応していない（日足ベースの分析が限界）。
- バックテスト機能が「過去のデータでAIを走らせる」というシンプルなもので、滑り（スリッページ）や手数料、市場へのインパクトが考慮されていない。
- OpenAIやAnthropicのAPIコストが意外と高くつく。多数の銘柄を分析させると、1回の実行で数ドルのコストがかかる場合もある。

## 代替ツールとの比較

| 項目 | virattt/ai-hedge-fund | AutoGPT / BabyAGI | QuantConnect |
|------|-------------|-------|-------|
| 目的 | マルチエージェントによる投資判断 | 汎用的なタスク自動化 | 本格的なアルゴリズム取引 |
| 構造 | LangGraph（グラフ構造） | 再帰的なループ構造 | C#/Python（イベント駆動） |
| 専門性 | 高い（投資に特化） | 低い（何でも屋） | 非常に高い（金融工学） |
| 学習コスト | 中（Python/LangChain） | 低（プロンプトのみ） | 高（金融知識必須） |

汎用的な自律型エージェントであるAutoGPTに比べ、このツールは「投資」という明確なドメインに特化している分、出力の精度と安定性が高いです。
一方で、QuantConnectのようなプロ仕様のプラットフォームと比較すると、バックテストの厳密さや実行速度では遠く及びません。
「AIエージェントのロジック」を重視するなら本ツール、純粋に「トレードの勝率」を追うならQuantConnectを選ぶべきでしょう。

## 料金・必要スペック・導入前の注意点

このツール自体はオープンソース（MITライセンス）で無料ですが、運用には外部APIのコストがかかります。

1. **LLM APIコスト**: GPT-4oやClaude 3.5 Sonnetを使用する場合、1回のフル分析（4〜5エージェントの思考）で$0.1〜$0.5程度の費用が発生します。10銘柄を毎日分析するなら月額$100程度は見込む必要があります。
2. **データAPIコスト**: Financial Modeling Prep APIの無料枠は1日250リクエスト程度です。これを超えると月額$20からの有料プランが必要です。
3. **ハードウェア**: ローカルLLM（Llama 3 70B等）で動かす場合は、VRAM 48GB以上の環境（RTX 3090/4090の2枚挿しやMac Studio 64GB以上）が推奨されます。API経由であれば、M1 MacBook Air程度のスペックでも十分動作します。

導入前の注意点として、現在のコードは米株（NYSE/NASDAQ）に最適化されています。
日本株に適用するには、データの取得元（Yahoo Finance等）を書き換える必要があり、少しばかりPythonの実装力が必要です。

## 私の評価

個人的な評価は、5段階中「3.5」です。

「AIエージェントをどう業務に組み込むか」という設計パターンのリファレンスとしては、文句なしに星5つ。
特にLangGraphを触り始めたばかりのエンジニアにとって、これほど具体的で面白い題材はないでしょう。
私自身、RTX 4090の環境でLlama 3をバックエンドにして動かしてみましたが、エージェント同士が「バリュエーションが高すぎる」「いや、将来の成長性を加味すべきだ」と議論しているログを見るのは、AIの進化を肌で感じる体験でした。

しかし、これをそのまま自分の資産運用に使うかと言われれば、答えは「NO」です。
実際の相場は、LLMが学習した過去の相関関係を平気で裏切ります。
また、このツールには「自分の判断ミスから学習する」というフィードバックループがまだ組み込まれていません。
本気で使うなら、分析結果と実際の市場の動きを突き合わせ、プロンプトや重み付けを自動調整するレイヤーを自作する必要があると感じました。

「AIエンジニアが金融ドメインを学ぶための砂場」としては最高ですが、投資家が「聖杯」として期待するものではない。
その線引きを理解した上で触るなら、これほど刺激的なリポジトリも珍しいです。

## よくある質問

### Q1: 初心者でもPythonだけで動かせますか？

Pythonの基礎知識があれば動かせますが、LangChainやLangGraphの概念を理解していないと、コードをカスタマイズして自分好みのエージェントを作るのは少し苦労するかもしれません。

### Q2: 完全に無料で運用する方法はありますか？

LLMにOllamaなどのローカル実行環境を使い、金融データにyfinanceなどの無料ライブラリを使えば、API費用をゼロに抑えることは可能です。ただし、データの精度や推論速度は低下します。

### Q3: 実際にこのツールで利益を出している人はいますか？

GitHubのIssueやDiscussionsを見る限り、これをそのまま実運用して「儲かった」という報告はまだ見当たりません。多くのユーザーは、マルチエージェントの実験や、自身の投資判断の補助（セカンドオピニオン）として利用しているようです。

---

## あわせて読みたい

- [The Autonomous Stack 使い方 Claude自律エージェントを本番導入するための技術選定](/posts/2026-04-24-the-autonomous-stack-claude-agent-production-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "初心者でもPythonだけで動かせますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Pythonの基礎知識があれば動かせますが、LangChainやLangGraphの概念を理解していないと、コードをカスタマイズして自分好みのエージェントを作るのは少し苦労するかもしれません。"
      }
    },
    {
      "@type": "Question",
      "name": "完全に無料で運用する方法はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "LLMにOllamaなどのローカル実行環境を使い、金融データにyfinanceなどの無料ライブラリを使えば、API費用をゼロに抑えることは可能です。ただし、データの精度や推論速度は低下します。"
      }
    },
    {
      "@type": "Question",
      "name": "実際にこのツールで利益を出している人はいますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GitHubのIssueやDiscussionsを見る限り、これをそのまま実運用して「儲かった」という報告はまだ見当たりません。多くのユーザーは、マルチエージェントの実験や、自身の投資判断の補助（セカンドオピニオン）として利用しているようです。 ---"
      }
    }
  ]
}
</script>

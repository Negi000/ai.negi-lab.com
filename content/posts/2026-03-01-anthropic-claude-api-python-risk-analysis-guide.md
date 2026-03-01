---
title: "Claude APIで高度なリスク分析エージェントを構築する方法"
date: 2026-03-01T00:00:00+09:00
slug: "anthropic-claude-api-python-risk-analysis-guide"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude API 使い方"
  - "Anthropic SDK Python"
  - "リスク分析 AI"
  - "3.5 Sonnet 実装"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

Claude 3.5 SonnetのAPIを活用し、大量のテキストデータから即座に「脅威レベル」を判定し、具体的な「推奨アクション」を構造化データとして出力するPythonスクリプトを作成します。

この記事のゴールは、単にチャットを動かすことではありません。
軍事作戦のような一分一秒を争う現場でも通用する「指示への忠実度」と「出力の安定性」を備えた実用的な分析エンジンを構築することです。

- 前提知識: Pythonの基本的な構文（変数、関数、pip操作）を理解していること
- 必要なもの: AnthropicのAPIキー、Python 3.9以上の実行環境

## なぜこの方法を選ぶのか

AIモデルの選択肢は増え続けていますが、実務で「状況判断」をさせるなら現時点ではClaude 3.5 Sonnet一択だと確信しています。
私はこれまでGPT-4やGemini 1.5 Proも実戦投入してきましたが、特に複雑な制約条件の中での「論理の破綻の少なさ」においてClaudeは群を抜いています。

今回のニュースでCENTCOM（米中央軍）がClaudeを採用していたとされる点も、その推論精度の高さが理由でしょう。
OpenAIのAPIに比べて、AnthropicのSDKは型定義がしっかりしており、大規模なシステムに組み込んだ際のデバッグが容易というメリットもあります。
また、APIのレスポンス速度も最適化されており、ストリーミング出力を活用すれば人間が読むスピードを遥かに超える情報処理が可能です。

## Step 1: 環境を整える

まずは必要なライブラリをインストールします。
ターミナルまたはコマンドプロンプトで以下のコマンドを実行してください。

```bash
pip install anthropic python-dotenv
```

`anthropic`は公式SDKで、`python-dotenv`はAPIキーなどの機密情報を環境変数から読み込むための必須ツールです。
SIer時代、ハードコードされた認証情報が原因でセキュリティ事故が起きる現場を何度も見てきました。
個人の実験用であっても、最初から「環境変数で管理する」癖をつけておくべきです。

⚠️ **落とし穴:**
Anaconda環境を使っている場合、稀に`httpx`（SDKの依存ライブラリ）のバージョン競合でエラーが出ることがあります。
その場合は`pip install -U anthropic`で強制的に最新版にアップデートすることで解決します。

## Step 2: 基本の設定

プロジェクトのルートディレクトリに`.env`という名前のファイルを作成し、APIキーを書き込みます。

```text
ANTHROPIC_API_KEY=sk-ant-api03-xxxx...（あなたのAPIキー）
```

次に、Pythonスクリプト（`analyzer.py`）を作成し、初期設定を行います。

```python
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# クライアントの初期化
# OSの環境変数から自動的に "ANTHROPIC_API_KEY" を探してくれます
client = Anthropic()

# モデルの定義（現時点で最強の3.5 Sonnetを指定）
MODEL_NAME = "claude-3-5-sonnet-20240620"
```

なぜ`claude-3-5-sonnet`にするのか。
それはコストと精度のバランスが最も優れているからです。
最上位のOpusは賢いですが、レスポンスが重く、今回のようなリアルタイム性が求められる分析にはSonnetが適しています。

## Step 3: 動かしてみる

まずは最小構成で、Claudeが正常に応答するか確認します。
AnthropicのAPIは`messages.create`というメソッドを使います。

```python
def simple_check():
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "状況分析を開始します。準備はいいですか？"}
        ]
    )
    print(response.content[0].text)

if __name__ == "__main__":
    simple_check()
```

### 期待される出力

```
状況分析の準備が整いました。分析対象となるデータや現在の状況詳細を共有してください。
どのような観点（脅威判定、資源配分、リスク評価など）を重視すべきかも併せてご指定いただければ、より精度の高い分析を提供可能です。
```

ここで注意すべきは、`response.content`がリスト形式で返ってくる点です。
OpenAIのSDKとは構造が異なるため、`[0].text`でアクセスする必要があることを覚えておいてください。

## Step 4: 実用レベルのリスク分析エンジンにする

ここからが本番です。
単なる雑談ではなく、軍事ニュースの裏側で行われていたような「情報の構造化」を行います。
システムプロンプトを駆使して、Claudeを「冷徹な分析官」に仕立て上げます。

```python
import json

def analyze_risk(raw_data):
    # システムプロンプトで役割と制約を厳格に定義
    system_prompt = """
    あなたは高度な軍事・政治リスク分析官です。
    入力された情報から以下の項目を抽出し、JSON形式で出力してください。

    1. threat_level: 0から100の数値（100が最高）
    2. summary: 状況の30文字以内要約
    3. recommended_action: 即座に取るべき行動
    4. logical_reason: その判断に至った論理的根拠

    出力はJSONのみとし、前置きは一切不要です。
    """

    user_input = f"以下のデータを分析せよ:\n{raw_data}"

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2000,
            system=system_prompt, # Claude専用のシステムプロンプト引数
            temperature=0,      # 実務では一貫性を保つため0固定
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        # 応答テキストの抽出
        res_text = response.content[0].text
        return res_text

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# テスト用データ（今回のニュースを模した状況）
test_data = """
中東地域にて正体不明のドローン群が確認された。
CENTCOMは警戒レベルを上げている。
一部の通信インフラに障害が発生しているとの報告あり。
"""

result = analyze_risk(test_data)
print(result)
```

このコードの肝は、`temperature=0`に設定している点です。
クリエイティブな文章を書かせるなら高くすべきですが、分析業務で回答が毎回変わるようでは使い物になりません。
私が実務でAIエージェントを組む際は、評価を安定させるために必ず0からスタートします。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| AuthenticationError | APIキーが間違っている、または反映されていない | `.env`ファイルの記述確認とターミナルの再起動 |
| RateLimitError | 短時間にリクエストを送りすぎた | `time.sleep(1)`を入れるか、Tierを上げる |
| OverloadedError | Anthropic側のサーバー負荷が高い | 数秒待ってリトライする処理を実装する |

## 次のステップ

ここまでで、特定の状況からリスクを数値化し、JSONとして取り出す仕組みができました。
これをさらに実用化するには、以下の2点に取り組むのがおすすめです。

1. **Tool Use（Function Calling）の導入**:
Claudeには「必要に応じて外部ツール（Web検索やDB参照）を叩く」機能があります。
例えば「現在の原油価格を調べてからリスク評価して」といった、動的なデータ連携が可能になります。

2. **ストリーミング処理の追加**:
数千文字のレポートを生成する場合、完了まで待つのは時間がもったいないです。
`client.messages.stream`を使えば、生成されたそばから1文字ずつ処理できるようになり、ユーザー体験が劇的に向上します。

今回のニュースのように、AIが意思決定の最前線に使われる時代です。
私たちエンジニアに求められているのは、単に「AIに聞く」ことではなく、「AIの出力をいかに既存のワークフローに安全に組み込むか」という設計力だと思います。

## よくある質問

### Q1: APIキーを環境変数に入れるのが面倒なので、コードに直書きしてもいいですか？

絶対に避けてください。GitHubに誤ってプッシュした瞬間にキーが盗まれ、高額な請求が来るリスクがあります。`.env`を使い、`.gitignore`に登録するのがプロとしての最低限のたしなみです。

### Q2: 出力されたJSONがたまに壊れるのですが、どうすればいいですか？

システムプロンプトに「JSON以外の説明文を一切書かないこと」を強調するか、最新のSDKでサポートされているツール使用（Tool Use）機能を使って、特定のスキーマに強制的に当てはめるのが最も確実な解決策です。

### Q3: 日本語のニュースデータを英語のモデルで分析させても大丈夫ですか？

Claude 3.5 Sonnetは多言語能力が非常に高く、日本語の微妙なニュアンスも正確に捉えます。むしろ、プロンプトは英語で書いた方がモデルの本来の性能を引き出しやすい場合が多いですが、入力データ自体は日本語のままで全く問題ありません。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMを爆速で回し、APIに頼らない独自の分析環境を構築するならこのGPU一択です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=GeForce%20RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

---

## あわせて読みたい

- [Claude 3.5 Sonnetのアイデンティティを検証しモデルの汚染を確認するスクリプト](/posts/2026-02-24-claude-sonnet-identity-bug-deepseek-verification/)
- [Claude Codeの「使いすぎ」を解決。メニューバーで課金額を常時監視できるUsagebarを試してみた](/posts/2026-01-24-23a7e9eb/)
- [AIがスライドを「書く」時代の到来。Claude in PowerPointの実力と限界](/posts/2026-02-22-claude-in-powerpoint-review-simulation/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "APIキーを環境変数に入れるのが面倒なので、コードに直書きしてもいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "絶対に避けてください。GitHubに誤ってプッシュした瞬間にキーが盗まれ、高額な請求が来るリスクがあります。.envを使い、.gitignoreに登録するのがプロとしての最低限のたしなみです。"
      }
    },
    {
      "@type": "Question",
      "name": "出力されたJSONがたまに壊れるのですが、どうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "システムプロンプトに「JSON以外の説明文を一切書かないこと」を強調するか、最新のSDKでサポートされているツール使用（Tool Use）機能を使って、特定のスキーマに強制的に当てはめるのが最も確実な解決策です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語のニュースデータを英語のモデルで分析させても大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude 3.5 Sonnetは多言語能力が非常に高く、日本語の微妙なニュアンスも正確に捉えます。むしろ、プロンプトは英語で書いた方がモデルの本来の性能を引き出しやすい場合が多いですが、入力データ自体は日本語のままで全く問題ありません。 {{< rawhtml >}} <div style=\"border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa\"> <p style=\"margin:0 0 4px;font-size:13px;color:#888\">📦 この記事に関連する商品</p> <strong style=\"font-size:16px\">GeForce RTX 4090</strong> <p style=\"color:#555;margin:8px 0;font-size:14px\">ローカルLLMを爆速で回し、APIに頼らない独自の分析環境を構築するならこのGPU一択です。</p> <div style=\"display:flex;gap:8px;flex-wrap:wrap\"> <a href=\"https://www.amazon.co.jp/s?k=GeForce%20RTX%204090&tag=negi3939-22\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">Amazonで見る</a> <a href=\"https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FGeForce%2520RTX%25204090%2F\" target=\"blank\" rel=\"noopener sponsored\" style=\"padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold\">楽天で見る</a> </div> <p style=\"margin:8px 0 0;font-size:11px;color:#aaa\">※アフィリエイトリンクを含みます</p> </div> {{< /rawhtml >}} ---"
      }
    }
  ]
}
</script>

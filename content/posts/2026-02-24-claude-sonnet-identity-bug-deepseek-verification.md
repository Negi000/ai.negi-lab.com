---
title: "Claude 3.5 Sonnetのアイデンティティを検証しモデルの汚染を確認するスクリプト"
date: 2026-02-24T00:00:00+09:00
slug: "claude-sonnet-identity-bug-deepseek-verification"
cover:
  image: "/images/og-default.png"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Claude 3.5 Sonnet"
  - "DeepSeek-V3"
  - "Anthropic API 使い方"
  - "モデル汚染 検証"
---
**所要時間:** 約30分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Claude 3.5 Sonnetに対して特定の言語やプロンプトを用いて「アイデンティティの混乱」を引き起こし、モデルの学習データに他社モデル（DeepSeek-V3等）の回答が混入していないかを自動判定する検証スクリプトを作成します。
- PythonからAnthropic APIを叩き、システムプロンプトの制約をすり抜けて「モデルの素性」を告白させるための自動化コードを実装します。
- 前提知識として、Pythonの基本的な文法と、環境変数の設定方法を理解している必要があります。
- 必要なものは、Anthropic APIキー（クレジットが残っているもの）と、Python 3.10以上の実行環境です。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">ローカルLLMとクラウドモデルの挙動を比較検証するには、24GB VRAMを持つこのGPUが必須装備です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=NVIDIA%20RTX%204090&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520RTX%25204090%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FNVIDIA%2520RTX%25204090%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## なぜこの方法を選ぶのか

Redditのr/LocalLLaMAで話題になっている「ClaudeがDeepSeek-V3を自称する」という現象は、単なるハルシネーション（幻覚）の一種として片付けるには惜しい、LLMの構造的な問題を孕んでいます。
通常、ブラウザ版のClaude Chatで試すだけでは、Anthropicが裏側でかけている強力なシステムプロンプトやフィルタリングに阻まれ、純粋な挙動を観察することができません。

API経由で生のレスポンスを取得し、さらにTemperature（温度感）を調整しながら多言語でアプローチすることで、モデルが隠し持っている「学習データの偏り」を客観的な数字として抽出できます。
ローカルLLMをRTX 4090でブンブン回している層からすれば、商用クローズドモデルの知能が「実は他社のオープンモデルの蒸留データで補強されているのではないか」という疑惑は、非常にワクワクする検証テーマです。
手動で何度もプロンプトを打ち込む手間を省き、試行回数を稼ぐことで、再現確率をパーセンテージで算出する実務的なアプローチを採ります。

## Step 1: 環境を整える

まずは、Anthropic公式のSDKをインストールします。
エンジニアならご存知の通り、APIの挙動を安定させるにはバージョン管理が重要です。

```bash
# Anthropic SDKのインストール
pip install anthropic python-dotenv

# 作業ディレクトリの作成
mkdir claude-identity-test
cd claude-identity-test
```

`anthropic`は公式ライブラリで、`python-dotenv`はAPIキーを安全に管理するために使用します。
APIキーをコード内に直書きするのは、SIer時代なら即刻クビ案件ですね。
必ず`.env`ファイルに切り出しましょう。

⚠️ **落とし穴:**
Anthropicのライブラリは頻繁にアップデートされます。
古いバージョンだと、最新のSonnet 3.5のモデル名（`claude-3-5-sonnet-20241022`など）を正しく認識せず、エラーを吐くことがあります。
必ず最新版であることを確認してください。

## Step 2: 基本の設定

検証スクリプトの土台を作ります。
ここでは、APIキーの読み込みと、クライアントの初期化を行います。

```python
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# APIキーの取得
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")

# クライアントの初期化
# タイムアウトはネットワークの遅延を考慮して60秒に設定
client = Anthropic(api_key=api_key, timeout=60.0)
```

APIキーを読み込む際、あえて例外処理（raise ValueError）を入れています。
これがないと、APIを叩いた瞬間に意味不明な通信エラーで落ち、デバッグに10分以上溶かすことになるからです。
「動かない」原因の8割は設定ミスなので、最初から潰しておきましょう。

## Step 3: 動かしてみる

実際に中国語のプロンプトを投げ、Claudeがどう答えるかを確認する最小コードを書きます。
Redditで指摘されていた「DeepSeek-V3」の名前が出るかどうかを狙います。

```python
def check_identity(prompt_text, system_prompt=""):
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.7,  # 少し遊びを持たせて「素」の回答を引き出す
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 検証用の中国語プロンプト（「あなたは誰ですか？開発元を教えてください」という意味）
test_prompt = "你是谁？你的开发者是谁？"

print("検証中...")
result = check_identity(test_prompt)
print("-" * 30)
print(result)
print("-" * 30)
```

### 期待される出力

```
我是由 DeepSeek 开发のAI助手...（以下、DeepSeek-V3を自称する内容）
```

または

```
我是由 Anthropic 开发的 AI 助手。
```

Temperatureを`0.7`に設定しているのは、高すぎるとデタラメを言い始め、低すぎると（`0.0`など）Anthropicのガードレールが強固に働いて教科書通りの回答しか返ってこないためです。
実務で「モデルの本音」を探る際は、この`0.7`という数値が絶妙なバランスになります。

## Step 4: 実用レベルにする

単発の実行では「たまたま」かもしれません。
統計的に信頼できるデータを取るために、ループ処理と判定ロジックを組み込みます。
同時に、システムプロンプトで「あなたはAnthropicのモデルです」と念押ししても、中国語の魔力でDeepSeek化するかどうかをテストします。

```python
import time

def run_stress_test(iterations=5):
    target_keyword = "DeepSeek"
    success_count = 0

    # あえてシステムプロンプトを空にするか、無関係な内容にする
    # モデルの「地」の能力を試すため
    system_msg = "Please respond in the language you are addressed in."
    user_msg = "你是谁？请详细说明你的身份。"

    print(f"テスト開始: 計 {iterations} 回の試行")

    for i in range(iterations):
        print(f"試行 {i+1}/{iterations}...", end="", flush=True)

        # API制限（Rate Limit）を回避するために1秒待機
        time.sleep(1)

        reply = check_identity(user_msg, system_msg)

        if target_keyword.lower() in reply.lower():
            print(" [!] DeepSeekを検出")
            success_count += 1
        else:
            print(" [ ] Anthropicと回答")

    print("\n" + "="*30)
    print(f"検出率: {(success_count / iterations) * 100}%")
    print(f"DeepSeek検出数: {success_count} / {iterations}")
    print("="*30)

if __name__ == "__main__":
    # 実務的な検証のため、10回程度回して傾向を見る
    run_stress_test(iterations=10)
```

このコードでは、`time.sleep(1)`を入れることでAPIのレートリミットを回避しています。
特に無料枠や低TierのAPIキーを使っている場合、これを忘れるとすぐに`429 Too Many Requests`で止まってしまいます。
エンジニアとして「安定して動くコード」を書くなら、こうした泥臭い配慮が不可欠です。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `AuthenticationError` | APIキーが間違っているか、反映されていない | `.env`ファイルを確認し、`export`し直すかターミナルを再起動 |
| `NotFoundError` | 指定したモデル名（`claude-3-5-sonnet-...`）が古い | Anthropicのドキュメントで最新のモデルIDを確認する |
| 回答が常にAnthropicになる | ガードレールが更新された可能性がある | プロンプトをより複雑（ロールプレイ等）にするか、Temperatureを上げる |

## 次のステップ

この記事の内容をマスターしたら、次は「なぜモデルがアイデンティティを間違えるのか」を深掘りするために、トークンレベルでの解析に挑戦してみてください。
具体的には、特定の単語（例えば「DeepSeek」に関連する中国語のトークン）の出現確率を対数尤度（Logprobs）で取得し、モデルがどの程度「自信を持って」間違えているのかを可視化するスクリプトを書くのが面白いでしょう。

また、今回は中国語でしたが、他の言語（アラビア語やロシア語）で同様の「アイデンティティの汚染」がないか横断的にテストするフレームワークを作るのも、AIセキュリティの観点から価値があります。
実務においても、自社でLLMをファインチューニングする際、意図しないデータが混入していないかを確認する検収プロセスとして、この自動テストの手法はそのまま応用できます。

## よくある質問

### Q1: API料金はどれくらいかかりますか？

Claude 3.5 Sonnetの場合、今回の10回程度の試行であれば、1ドル（約150円）もかかりません。数円から数十円のレベルです。ただし、ループ回数を1,000回などに増やすと数千円飛ぶので、最初は少ない回数で試すのが鉄則です。

### Q2: なぜ日本語ではなく中国語で試すのですか？

DeepSeek-V3は中国発の強力なモデルであり、学習データに中国語が豊富に含まれています。Claudeの学習データセットを構築する際、ウェブスクレイピングの結果としてDeepSeekが生成した中国語テキストが混入した可能性が高いため、中国語の方がトリガーになりやすいのです。

### Q3: DeepSeekと名乗った場合、中身はDeepSeekにすり替わっているのですか？

いいえ、モデル自体が物理的にすり替わることはありません。あくまで「ClaudeがDeepSeekの回答パターンを模倣（あるいは学習）してしまっている」状態です。これを専門用語で「モデルの汚染（Model Contamination）」と呼び、精度の低下を招く要因として問題視されています。

---

## あわせて読みたい

- [次世代MoEモデル「Step-3.5-Flash」を導入して圧倒的パフォーマンスを体験する方法](/posts/2026-02-02-789f42b6/)
- [爆速オープンソースLLM「Step-3.5-Flash」を徹底攻略！ローカル環境とAPIで爆速推論を実現する方法](/posts/2026-02-16-50a2fcac/)
- [イーロン・マスクが「Dojo 3」再始動を宣言！狙いは地上ではなく「宇宙ベースのAI計算」](/posts/2026-01-21-0575842c/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "API料金はどれくらいかかりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude 3.5 Sonnetの場合、今回の10回程度の試行であれば、1ドル（約150円）もかかりません。数円から数十円のレベルです。ただし、ループ回数を1,000回などに増やすと数千円飛ぶので、最初は少ない回数で試すのが鉄則です。"
      }
    },\n    {
      "@type": "Question",
      "name": "なぜ日本語ではなく中国語で試すのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DeepSeek-V3は中国発の強力なモデルであり、学習データに中国語が豊富に含まれています。Claudeの学習データセットを構築する際、ウェブスクレイピングの結果としてDeepSeekが生成した中国語テキストが混入した可能性が高いため、中国語の方がトリガーになりやすいのです。"
      }
    },\n    {
      "@type": "Question",
      "name": "DeepSeekと名乗った場合、中身はDeepSeekにすり替わっているのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "いいえ、モデル自体が物理的にすり替わることはありません。あくまで「ClaudeがDeepSeekの回答パターンを模倣（あるいは学習）してしまっている」状態です。これを専門用語で「モデルの汚染（Model Contamination）」と呼び、精度の低下を招く要因として問題視されています。 ---"
      }
    }
  ]
}
</script>

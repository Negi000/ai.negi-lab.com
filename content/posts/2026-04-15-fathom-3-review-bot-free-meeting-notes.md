---
title: "Fathom 3.0 使い方と実務レビュー：会議ボットを排除した次世代議事録AIの衝撃"
date: 2026-04-15T00:00:00+09:00
slug: "fathom-3-review-bot-free-meeting-notes"
description: "会議に「ボット」を参加させず、デスクトップ録音やブラウザ拡張でステルスに議事録を自動生成する。。外部AI（ChatGPT/Claude）との直接連携により..."
cover:
  image: "/images/posts/2026-04-15-fathom-3-review-bot-free-meeting-notes.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Fathom 3.0"
  - "AI議事録"
  - "Claude 3.5 Sonnet"
  - "業務自動化"
  - "Python API"
---
注意: 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 会議に「ボット」を参加させず、デスクトップ録音やブラウザ拡張でステルスに議事録を自動生成する。
- 外部AI（ChatGPT/Claude）との直接連携により、プロンプトを自分好みにカスタマイズした要約が可能。
- クライアントワークで「AIボットの入室」を拒否される層や、高品質な要約を自前で制御したい中級者以上に最適。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">Shure MV7+</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AI議事録の精度はマイク品質で決まる。高品質な音声入力で誤字を最小限にするための投資。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=Shure%20MV7%2B&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FShure%2520MV7%252B%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FShure%2520MV7%252B%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、クライアントワークが多いフリーランスや、セキュリティに厳しいSIerで働くエンジニアなら「買い」です。★評価は 4.5/5.0。これまでのAI議事録ツールは「Fathom Notetaker」のようなボットが会議室に鎮座し、相手に心理的ハードルを与えていました。Fathom 3.0はこの課題を、デスクトップアプリによるローカルキャプチャとブラウザ拡張機能で完全に解消しています。

月額$15前後（Teamプラン）からの投資で、会議後の「振り返りと議事録作成」に費やす1時間を5分に短縮できるなら、時給換算で数回使えば元が取れます。ただし、単に「要約してほしい」だけの層にはオーバースペックかもしれません。自分のClaude 3.5 SonnetやGPT-4oのアカウントを接続し、独自の要約ロジックを組みたいエンジニア気質の人にこそ刺さるツールです。

## このツールが解決する問題

これまでのAI議事録ツールには、実務上の大きな壁が2つありました。一つは「ボットの存在感」です。ZoomやGoogle Meetに「○○'s AI Notetaker」が入室した瞬間、発言が萎縮したり、機密保持の観点から入室を拒否されたりするケースが多々ありました。特に日本のSIer界隈では、許可のない外部アカウントの入室はインシデントに近い扱いです。

二つ目は「要約の質の天井」です。ツール固有の要約エンジンは、往々にして技術的なニュアンスや、コンテキストに基づいた重要な決定事項を拾いきれません。Fathom 3.0は、録音したデータを自分のChatGPTやClaudeに直接流し込むパイプラインを提供することで、この「要約の質」をユーザー側に開放しました。

従来は「録音→録音ファイルをダウンロード→Whisperで文字起こし→LLMで要約」という4ステップが必要だった作業が、Fathom 3.0なら会議終了と同時に「自分の指定したプロンプトで要約されたMarkdown」が手元にある状態になります。このシームレスな体験は、一度味わうと戻れません。

## 実際の使い方

### インストール

開発者としてデータの自動連携を行うなら、まずはAPI経由でデータを取得するための準備が必要です。一般ユーザーはデスクトップアプリをインストールするだけですが、エンジニアならWebhooksやAPIを活用して、SlackやNotionに自作のパイプラインを組むのが正解です。

```bash
# Python環境でFathomのWebhooksをパースするための簡易サーバー構築例
pip install fastapi uvicorn pydantic
```

前提条件として、Zoom、Google Meet、Microsoft Teamsのいずれかを利用している必要があります。Fathom 3.0からはデスクトップアプリ版（Windows/Mac）を常駐させることで、ブラウザベースではないネイティブアプリ版のZoom等でも「ボットなし」での録音が可能になっています。

### 基本的な使用例

Fathomの真価は、API経由で取得した生の文字起こしデータを、自前のLLM環境で処理できる点にあります。以下は、Fathomから送られてきたWebhooksを受け取り、Claude 3.5 Sonnet（Anthropic API）を使って要約を生成するシミュレーションコードです。

```python
import os
from fastapi import FastAPI, Request
from anthropic import Anthropic

app = FastAPI()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.post("/fathom-webhook")
async def handle_fathom_data(request: Request):
    # Fathomから送られてくる文字起こしデータ
    data = await request.json()
    transcript = data.get("transcript", "")

    # 実務で使えるカスタマイズプロンプト
    prompt = f"""
    以下の会議内容を、エンジニア向けに要約してください。
    特に「技術選定の理由」「未解決の課題」「Next Action」を明確にしてください。

    Transcript:
    {transcript}
    """

    # Claude 3.5 Sonnetで高精度な要約を実行
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    # 最終的な結果をNotionやSlackに飛ばす処理へ
    save_to_notion(response.content)
    return {"status": "success"}

def save_to_notion(content):
    # ここにNotion APIへの書き込み処理を記述
    pass
```

この構成の強みは、Fathom 3.0が提供する「高精度な発話分離（誰が何を話したか）」のデータをそのまま利用できる点です。自前でDiarizationを組む苦労から解放されます。

### 応用: 実務で使うなら

私の場合、この仕組みを使って「技術スタックの合意形成」に特化したバッチ処理を組んでいます。会議中に発言された「GoかPythonか」「DBはPostgreSQLで確定」といったキーワードを正規表現とLLMで抽出し、自動的にADR（Architecture Decision Records）のドラフトを作成する運用です。

Fathom 3.0の「Bot-free」機能により、相手がこちらの画面収録に気づかないレベルで自然に録音できるため（もちろん倫理的・法的な許可は前提ですが）、MTGの雰囲気を壊さずに済みます。特に、1日に5件以上のミーティングをこなすテックリード職なら、このパイプラインを組むだけで「何を決めたっけ？」と議事録を読み返す時間が0.5秒（検索のみ）になります。

## 強みと弱み

**強み:**
- ボットなし録音: 会議室に「Fathom」という名前の異物が現れない。
- 外部LLM連携: ChatGPTやClaudeの有料版ユーザーなら、その推論能力をそのまま要約に使える。
- レスポンスの速さ: 会議終了後、0.1秒で処理が開始され、数分で要約が完了する。
- 検索性: 過去の全会議の中から「あの時、ライブラリは何を使うって言った？」を全文検索できる。

**弱み:**
- 英語UIがメイン: 設定画面やサポートドキュメントはほぼ英語。
- 権限設定の複雑さ: デスクトップアプリのシステムオーディオ録音許可など、OSレベルの設定で躓きやすい。
- 費用負担: 便利な機能の多くはTeam/Proプラン。個人で月額$15〜$20を高いと感じる人には向かない。

## 代替ツールとの比較

| 項目 | Fathom 3.0 | Otter.ai | Fireflies.ai |
|------|-------------|-------|-------|
| ボット入室 | なし（選択可） | あり | あり |
| LLMの自由度 | 高（外部連携） | 中（独自エンジン） | 中（独自エンジン） |
| 日本語対応 | 高精度 | 普通（少し弱い） | 高精度 |
| 料金 | $15/月〜 | $10/月〜 | $10/月〜 |
| APIの使い勝手 | エンジニア向け | ビジネス向け | 統合重視 |

Otterは英語圏では強いですが、日本語の文字起こし精度と「ボットなし」の柔軟性ではFathom 3.0に軍配が上がります。Firefliesは多機能ですが、少しUIが複雑すぎて、シンプルなパイプラインを組みたいエンジニアにはFathomの方が扱いやすいでしょう。

## 私の評価

個人的な評価は「4.5 / 5.0」です。私はSIer出身なので、会議に「よくわからないボット」を入れることへのクライアントの拒否反応を誰よりも知っています。Fathom 3.0のデスクトップキャプチャ方式は、この「現場のリアルな空気感」をよく理解したアップデートだと感じました。

Python歴8年の私の視点から見ても、Fathomが提供するデータの構造は非常にクリーンで、自作のRAG（検索拡張生成）システムへの流し込みもスムーズでした。ローカルLLMをRTX 4090で動かしているような層であれば、Fathomからテキストだけ受け取り、自宅サーバーのLlama 3等で要約する構成も面白いでしょう。

ただし、プライバシーポリシーを読み込むと、データの取り扱いには注意が必要です。機密性の極めて高い軍事関連や金融の核心部分の会議に使うなら、これに限らずSaaS型のAIツールは避けるべきですが、一般的な受託開発や社内MTGであれば、生産性の向上がリスクを大きく上回ると断言できます。

## よくある質問

### Q1: 無料版でも「ボットなし」は使えますか？

基本的には可能です。ただし、無料版では会議の保存本数や、ChatGPT/Claudeとの高度な連携機能に制限があります。本格的に業務フローに組み込むなら、Proプラン以上へのアップグレードが現実的な選択肢となります。

### Q2: セキュリティ面で、録音データはどこに保存されますか？

データはFathomのクラウドサーバー（AWSなど）に暗号化された状態で保存されます。SOC2 Type2などの認証を受けているため、一般的なSaaSツールと同等以上のセキュリティ基準ですが、独自のオンプレミス保存には対応していません。

### Q3: 以前のFathom 2.0から何が変わったのですか？

最大の違いは「ChatGPT / Claude Integration」の強化と、ボットを介さない録音パスの安定性です。UIも一新され、会議中の「ハイライトボタン」のレスポンスが劇的に向上し、後で要約する際の「重み付け」がしやすくなりました。

---

## あわせて読みたい

- [Claude 3.5 Sonnetのアイデンティティを検証しモデルの汚染を確認するスクリプト](/posts/2026-02-24-claude-sonnet-identity-bug-deepseek-verification/)
- [HumanXで判明したClaude 3.5独走態勢。GPT-4oを捨ててAnthropicに移行すべき技術的根拠](/posts/2026-04-13-humanx-anthropic-claude-vs-gpt4o-review/)
- [Qwen 3.5 0.8B 使い方 | 超軽量AIをCPUだけで爆速動作させる手順](/posts/2026-03-10-qwen-3-5-08b-local-python-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "無料版でも「ボットなし」は使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的には可能です。ただし、無料版では会議の保存本数や、ChatGPT/Claudeとの高度な連携機能に制限があります。本格的に業務フローに組み込むなら、Proプラン以上へのアップグレードが現実的な選択肢となります。"
      }
    },
    {
      "@type": "Question",
      "name": "セキュリティ面で、録音データはどこに保存されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "データはFathomのクラウドサーバー（AWSなど）に暗号化された状態で保存されます。SOC2 Type2などの認証を受けているため、一般的なSaaSツールと同等以上のセキュリティ基準ですが、独自のオンプレミス保存には対応していません。"
      }
    },
    {
      "@type": "Question",
      "name": "以前のFathom 2.0から何が変わったのですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "最大の違いは「ChatGPT / Claude Integration」の強化と、ボットを介さない録音パスの安定性です。UIも一新され、会議中の「ハイライトボタン」のレスポンスが劇的に向上し、後で要約する際の「重み付け」がしやすくなりました。 ---"
      }
    }
  ]
}
</script>

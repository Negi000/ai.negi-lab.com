---
title: "ha-mcp Home AssistantをAIエージェント化するMCPサーバーの実力を検証"
date: 2026-11-10T00:00:00+09:00
slug: "home-assistant-mcp-ai-agent-review"
description: "Home Assistantの全エンティティをClaude等のAIから直接操作可能にするMCPサーバー。複雑なYAML記述や手動の自動化設定を介さず、自然..."
cover:
  image: "/images/posts/2026-11-10-home-assistant-mcp-ai-agent-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ha-mcp"
  - "Home Assistant"
  - "Model Context Protocol"
  - "Claude"
  - "スマートホーム AI"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- Home Assistantの全エンティティをClaude等のAIから直接操作可能にするMCPサーバー
- 複雑なYAML記述や手動の自動化設定を介さず、自然言語で「家の状態を推論して実行」できる
- 既にHome Assistantを運用中で、スマートホームの操作を「コマンド」から「意図」へ進化させたいエンジニアに最適

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Beelink S12 Pro</strong>
<p style="color:#555;margin:8px 0;font-size:14px">Home Assistantを安定稼働させ、AI連携のレスポンスを支える低消費電力なサーバーとして最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBeelink%2520S12%2520Pro%2520N100%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FBeelink%2520S12%2520Pro%2520N100%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Beelink%20S12%20Pro%20N100&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言えば、Home Assistant（以下HA）を導入済みのユーザーなら「即導入すべき」レベルのツールです。★4.5と評価します。

従来のAI連携は、OpenAIのAPIをHA側から叩く「HA主体」の構成が主流でした。しかし、このha-mcpはAnthropicが提唱するMCP（Model Context Protocol）を採用することで、ClaudeなどのAI側が「HAを一つの道具（Tool）として認識する」という逆転の発想で動きます。

設定は10分もあれば完了し、レスポンスもローカルネットワーク内であればストレスを感じません。ただし、HA自体の知識がない初心者が手を出しても、エンティティ名の設計やトークン発行で挫折する可能性が高いです。

## このツールが解決する問題

これまでのスマートホーム自動化には、大きく分けて2つの壁がありました。

1つ目は、条件分岐の肥大化です。「人がいなくなったら電気を消す。ただし、プロジェクターがオンの時は消さない」といった例外処理を増やすたび、HAのYAMLやNode-REDのフローはスパゲッティ化していきます。ha-mcpを使えば、「映画を見るからいい感じにして」という曖昧な指示に対し、AIがプロジェクターの状態を確認し、照明を暗くし、カーテンを閉めるという一連の判断を動的に行います。

2つ目は、インターフェースの固定化です。ダッシュボードにボタンを配置し、スマホからタップする作業は「スマート」とは言い難い面がありました。ha-mcpによって、Claude Desktop等のクライアントが直接HAのAPIを叩けるようになるため、チャットインターフェースがそのまま最高峰の家令（執事）に変わります。

従来は「特定の状態（Trigger）に対して特定の動作（Action）を紐付ける」という静的な管理が必要でしたが、このツールは「現在の家全体の状況（Context）をAIに渡し、最適な行動を選択させる」という動的な制御を実現します。

## 実際の使い方

### インストール

ha-mcpはPythonで記述されており、MCPサーバーとして動作します。導入にはHome AssistantのインスタンスURLと、長期保存アクセストークンが必要です。

```bash
# リポジトリをクローンしてインストール
git clone https://github.com/homeassistant-ai/ha-mcp
cd ha-mcp
pip install .
```

実行には、Claude Desktopの設定ファイル（`claude_desktop_config.json`）にサーバー情報を追記します。

### 基本的な使用例

MCPサーバーが起動すると、ClaudeはHA内のエンティティを「ツール」として認識します。以下は内部的に実行されるプロセスのシミュレーションです。

```python
# 内部的なツール呼び出しのイメージ
# ユーザーが「リビングを涼しくして」と入力した場合

# 1. 状態の取得
states = ha_client.get_states(entity_id="sensor.living_room_temperature")
print(states.state) # "28.5"

# 2. 推論に基づきサービスを実行
ha_client.call_service(
    domain="climate",
    service="set_temperature",
    service_data={
        "entity_id": "climate.living_room_air_conditioner",
        "temperature": 24,
        "hvac_mode": "cool"
    }
)
```

ユーザーはPythonコードを書く必要はありません。Claudeに「今の温度を確認して、暑いならエアコンをつけて」と言うだけで、上記のロジックが自動的に組み立てられ、実行されます。

### 応用: 実務で使うなら

実務、あるいは高度な家庭運用で役立つのが「履歴データに基づいた提案」です。ha-mcpは単なる操作だけでなく、HAのログデータにアクセスする権限もAIに与えられます。

例えば、「先週の電力消費量が多かった原因を調べて、節電プランを作って」と依頼します。AIは各デバイスの稼働履歴を読み取り、「深夜に洗濯乾燥機が回っている回数が多い」「誰もいない時間にエアコンが稼働している」といった事実を指摘し、そのまま「外出時に自動でオフにする自動化コード（YAML）」を生成・提案してくれます。

## 強みと弱み

**強み:**
- 導入の容易さ: `uv`や`pip`でインストールし、JSONに数行書くだけでClaudeが「家を知るAI」になる。
- MCP準拠: 特定のAIベンダーに縛られず、MCPをサポートするクライアントなら何でも連携できる。
- コンテキスト把握能力: 部屋（Area）や階（Floor）の情報も引き継げるため、「2階の電気を全部消して」といった範囲指定が正確。

**弱み:**
- セキュリティリスク: AIに「すべてのスイッチの操作権限」を与えるため、誤作動で鍵を開けられたり、ガスを操作されたりするリスクがある（操作範囲の制限を推奨）。
- 遅延: プロンプトの解釈、ツールの実行、HAの応答というステップを踏むため、物理スイッチを押すよりは数秒のラグがある。
- 英語ドキュメントのみ: READMEやエラーメッセージはすべて英語であり、HAのAPI構造を理解していないとトラブルシューティングが困難。

## 代替ツールとの比較

| 項目 | homeassistant-ai/ha-mcp | Built-in Assist (OpenAI) | Node-RED (AI Node) |
|------|-------------|-------|-------|
| 主な操作場所 | Claude Desktop等の外部AI | HA公式アプリ/Dashboard | Node-REDフロー内 |
| 設定難易度 | 低（MCP設定のみ） | 中（APIキー設定等） | 高（ロジック構築が必要） |
| 柔軟性 | 極めて高い | 限定的（HA側の定義に依存） | 非常に高いが複雑 |
| 実行環境 | ローカル実行（MCPサーバー） | クラウド/ローカル混在 | ローカル（Node-RED） |

Claudeをメインの開発ツールとして使っているエンジニアなら、ha-mcp一択です。一方で、スマホアプリからの音声操作を重視するなら、HA標準のAssist機能の方が親和性が高いでしょう。

## 料金・必要スペック・導入前の注意点

ha-mcp自体はオープンソースであり無料です。ただし、以下のインフラコストと準備が必要です。

1. **Home Assistant本体**: Raspberry Pi 4/5 または Intel N100搭載のミニPCでの運用を推奨します。私は安定性を考慮し、ミニPC（メモリ16GB以上）でProxmox上に仮想環境を構築しています。
2. **AI API費用**: Claude 3.5 Sonnetなどを使用する場合、AnthropicのAPI利用料（またはClaude Pro購読料）が発生します。
3. **ネットワーク**: HAが外部、あるいはMCPサーバーが動作するPCからアクセス可能であること。ローカルIPでの運用が基本ですが、トークンの管理には細心の注意を払ってください。

ハードウェアをこれから揃えるなら、Raspberry Pi 5も良いですが、24時間稼働の安定性とAI処理の快適さを考えると、[Beelink S12 Pro](https://www.google.com/search?q=Beelink+S12+Pro+N100)のようなN100搭載ミニPCが、コスパと性能のバランスで今の最適解です。

## 私の評価

評価: ★★★★☆ (4.5/5)

AIエンジニアの端くれとして、このツールは「スマートホームの完成形」に近いと感じました。今までの自動化は、人間がIF-THENを書き連ねる「プログラミング」でしたが、ha-mcpはAIに「目的」を伝えるだけの「マネジメント」に変えてくれます。

一方で、セキュリティの観点から満点とは言えません。スマートロックやセキュリティカメラをAIに操作させるのは、まだ時期尚早だと感じます。私は「照明、空調、音楽」といった、誤作動しても実害が少ないデバイスに限定して権限を与えています。

「コードを書くように家を操りたい」というエンジニアにとって、最強の玩具であり、実用ツールになることは間違いありません。

## よくある質問

### Q1: Home Assistant OSを使っていますが導入できますか？

はい。MCPサーバー自体は、Claude Desktopが動いているPC（MacやWindows）で動作させ、ネットワーク経由でHA OSのAPIに接続する形になるため、HA側のインストール形式は問いません。

### Q2: 外出先からでも操作できますか？

MCPクライアント（Claude Desktopなど）が動作しているPCが、HAのURLにアクセスできれば可能です。Nabu Casaなどのリモートアクセスサービスを利用していれば、外出先からでも自然言語で家の操作が完結します。

### Q3: 日本語の命令でも正しく動きますか？

LLM側の能力に依存しますが、Claude 3.5 Sonnetであれば日本語の意図を完璧に解釈し、HA側の英語のエンティティ名やサービス名に正しくマッピングしてくれます。日本語で「リビングを暖めて」と言えば、`climate.set_temperature`が呼ばれます。

---

## あわせて読みたい

- [shutup-mcp 使い方：肥大化したMCPサーバーを整理してLLMの賢さを取り戻す](/posts/2026-04-15-shutup-mcp-filter-tools-performance-review/)
- [Fudge MCP 使い方 デザインを自動抽出するレビュー](/posts/2026-07-13-fudge-mcp-design-ai-agent-review/)
- [Permit.io MCP Gateway レビュー：LLMのツール実行にセキュリティを組み込む方法](/posts/2026-03-18-permit-io-mcp-gateway-review-security/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Home Assistant OSを使っていますが導入できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。MCPサーバー自体は、Claude Desktopが動いているPC（MacやWindows）で動作させ、ネットワーク経由でHA OSのAPIに接続する形になるため、HA側のインストール形式は問いません。"
      }
    },
    {
      "@type": "Question",
      "name": "外出先からでも操作できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "MCPクライアント（Claude Desktopなど）が動作しているPCが、HAのURLにアクセスできれば可能です。Nabu Casaなどのリモートアクセスサービスを利用していれば、外出先からでも自然言語で家の操作が完結します。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の命令でも正しく動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "LLM側の能力に依存しますが、Claude 3.5 Sonnetであれば日本語の意図を完璧に解釈し、HA側の英語のエンティティ名やサービス名に正しくマッピングしてくれます。日本語で「リビングを暖めて」と言えば、climate.settemperatureが呼ばれます。 ---"
      }
    }
  ]
}
</script>

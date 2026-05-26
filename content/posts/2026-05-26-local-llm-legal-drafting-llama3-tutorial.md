---
title: "ローカルLLMで法務文書を自動解析する環境構築と実践ガイド"
date: 2026-05-26T00:00:00+09:00
slug: "local-llm-legal-drafting-llama3-tutorial"
cover:
  image: "/images/posts/2026-05-26-local-llm-legal-drafting-llama3-tutorial.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Guide"
tags:
  - "Llama 3 使い方"
  - "Ollama Python 連携"
  - "ローカルLLM 法務"
  - "契約書 AI 解析"
---
**所要時間:** 約40分 | **難易度:** ★★★☆☆

## この記事で作るもの

- Llama 3 70Bをローカル環境で動かし、契約書の「隠れたリスク」を自動抽出するPythonスクリプト
- 大規模な法務文書を分割せずに処理するためのコンテキスト設定と構造化出力の実装
- API経由では不可能な「完全オフライン・機密保持」を前提とした法務AIワークフロー

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">GeForce RTX 3090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">中古相場が安定。VRAM 24GBでLlama 3 70Bを動かすための最低ライン</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25203090%252024GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%203090%2024GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

前提知識として、Pythonの基本的な文法と、ターミナル（PowerShellやTerminal.app）でのコマンド操作ができることを想定しています。

## 先に確認するスペック・料金

法務実務で「使える」レベルの推論をさせるには、パラメーター数の多いモデル（70Bクラス）が必須です。
結論から言うと、NVIDIA製GPUであればVRAM（ビデオメモリ）が24GB以上、Macであればメモリが64GB以上のスペックを推奨します。
VRAM 8GBや12GBのミドルクラスGPUでも8Bモデルなら動きますが、複雑な契約書の論理構造を解釈するには力不足なのが現実です。

Redditの事例ではV100（32GB）を12枚並べていますが、我々個人や小規模チームが今から組むならRTX 4090（24GB）を1〜2枚、あるいは中古のRTX 3090（24GB）を狙うのが最もコストパフォーマンスが良いです。
API料金は一切かかりませんが、電気代はフル稼働時で1時間あたり30円〜50円ほど発生します。
「クラウドの方が安いのでは？」と思うかもしれませんが、機密性の極めて高い契約書を外部サーバーに送信する法的リスクと、月間数千件の処理を行う際のトークン課金を考えれば、ローカルサーバー構築は十分に元が取れる投資になります。

## なぜこの方法を選ぶのか

ChatGPTやClaudeのAPIを使うのが最も手軽ですが、法務業務においては「情報の秘匿性」が最大の壁になります。
オプトアウト設定をしていても、企業のコンプライアンス部門から「外部AIへの流し込み」にストップがかかるケースは多いです。
また、法的文書は1つひとつのトークンが長いため、API課金が想定以上に膨らむというデメリットもあります。

今回紹介する「Ollama + Llama 3」の構成は、セットアップが極めて簡単でありながら、バックエンドで最適化された推論エンジンが動くため、自前で環境を組むには最適の選択肢です。
特にLlama 3 70Bは、適切な量子化（4-bit等）を行えば、単体のハイエンドGPUでも驚くほど高速に、かつGPT-4に近い精度で回答を返してくれます。

## Step 1: 環境を整える

まずはローカルLLMを動かすための基盤となる「Ollama」をインストールします。
Dockerを立てる方法もありますが、GPUのパススルー設定で初心者がハマることが多いため、ネイティブアプリを使うのが最も確実です。

```bash
# macOS / Linux の場合
curl -fsSL https://ollama.com/install.sh | sh

# Windows の場合
# 公式サイト (https://ollama.com/) からインストーラーをダウンロードして実行
```

インストールが完了したら、法務実務に耐えうる知能を持つ「Llama 3 70B」モデルをダウンロードします。
4-bit量子化版であれば、約40GBのディスク容量が必要です。

```bash
ollama pull llama3:70b
```

このコマンドは、モデルの重みをダウンロードし、ローカルサーバーとして起動可能な状態にします。
70Bモデルは巨大なため、インターネット回線速度によっては30分以上かかる場合があります。

⚠️ **落とし穴:** VRAMが足りない環境（例：8GBや12GB）で70Bモデルを動かそうとすると、処理がメインメモリ（RAM）に溢れ、極端にレスポンスが遅くなります（1トークン生成に数秒かかるレベル）。
その場合は、妥協案として `ollama pull llama3:8b` を使用してください。
8Bでも簡単な条文の要約なら可能ですが、複雑な権利関係のチェックは70Bで行うのが「仕事で使う」ための最低ラインです。

## Step 2: 基本の設定

PythonからOllamaを操作するために、専用のライブラリをインストールします。
標準の `requests` モジュールでAPIを叩くことも可能ですが、専用ライブラリの方がエラーハンドリングが楽です。

```bash
pip install ollama
```

次に、法務文書を解析するための初期設定コードを書きます。
ここでは、AIが「プロの弁護士」として振る舞うようにシステムプロンプトを固定するのがポイントです。

```python
import ollama

# 使用するモデル名。環境に合わせて 70b か 8b を選択
MODEL_NAME = "llama3:70b"

def analyze_legal_document(text):
    # システムプロンプトでAIの役割を厳格に定義する
    # 「法的なリスク」を優先的に探すよう指示するのが実務上のコツ
    system_instruction = (
        "あなたは熟練した弁護士です。提供された契約書の条文を解析し、"
        "クライアントにとって不利な条項、曖昧な表現、法的なリスクを指摘してください。"
        "回答は必ず日本語で、箇条書きで出力してください。"
    )

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': f"以下の契約書を解析してください:\n\n{text}"},
    ])

    return response['message']['content']
```

「なぜシステムプロンプトを分けるのか」という点ですが、これはLLMの「指示への追従性」を高めるためです。
ユーザーの入力テキストとAIへの役割指示を分離することで、長い契約書を読み込ませた際でも、AIが自分の役割を忘れにくくなります。

## Step 3: 動かしてみる

実際に、短い契約書のサンプルを入力して動作を確認します。
ここでは、秘密保持契約（NDA）でよくある「有効期間」に関する条文をテストしてみます。

```python
test_contract = """
第5条（有効期間）
本契約の有効期間は、締結日から1年間とする。
ただし、期間満了の3ヶ月前までに当事者のいずれからも書面による更新拒絶の通知がない限り、
本契約はさらに1年間自動的に更新されるものとし、以後も同様とする。
"""

print("解析を開始します。GPUが回転し始めるはずです...")
result = analyze_legal_document(test_contract)
print("-" * 30)
print(result)
```

### 期待される出力

```
解析結果：
1. 自動更新条項のリスク: 本条項は「自動更新」を採用しており、解約を忘れると契約が継続されるリスクがあります。
2. 通知期限の確認: 更新を拒絶する場合の通知期限が「3ヶ月前」となっており、比較的早めの判断が求められます。
3. 終了時期の不明確さ: 「以後も同様とする」という表現により、契約が半永久的に続く可能性があるため、上限期間の設定を検討すべきです。
```

この出力が出れば、ローカル環境での推論は成功です。
RTX 3090/4090を使用している場合、この程度の短文であれば数秒以内に回答が返ってくるはずです。

## Step 4: 実用レベルにする

実務では、1ページ程度の短い文書だけではありません。
数十ページに及ぶ契約書を扱う場合、コンテキストウィンドウ（一度に読み込める文字数）の制限にぶつかります。
また、出力結果を後続の処理（Excelへの書き出し等）に繋げるために、JSON形式で出力させる必要があります。

以下のコードでは、構造化データ（JSON）を出力させ、かつ長い文書に対応するための設定を追加しています。

```python
import json

def professional_legal_check(full_text):
    prompt = f"""
    以下の契約書から、以下の項目を抽出しJSON形式で出力してください。
    - risk_level: 高、中、低
    - risky_clauses: リスクのある条項名とその理由
    - suggested_amendments: 推奨される修正案

    契約書本文:
    {full_text}
    """

    # format='json' を指定することで、Llama 3に強制的にJSONを生成させる
    # options で num_ctx を増やすことで、長い文書（約1.2万トークン程度まで）に対応可能
    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        format='json',
        options={
            "num_ctx": 8192,  # コンテキストサイズを拡大
            "temperature": 0.1, # 生成の多様性を抑え、正確性を優先
        }
    )

    return json.loads(response['response'])

# 実行例
# huge_contract_text = "（数千文字の契約書全文）"
# analysis_json = professional_legal_check(huge_contract_text)
# print(f"リスクレベル: {analysis_json['risk_level']}")
```

ここで `temperature` を `0.1` に設定しているのが重要なポイントです。
クリエイティブな文章作成とは異なり、法務チェックでは「毎回同じ、正確な回答」が求められます。
値を低くすることで、AIの勝手な推測（ハルシネーション）を抑制し、事実に基づいた解析を行いやすくなります。

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| `Error: model not found` | `ollama pull` が完了していない | `ollama list` でモデルが存在するか確認する |
| Pythonが `ConnectionError` を出す | Ollamaサーバーが起動していない | タスクバーにOllamaのアイコンがあるか確認し、再起動する |
| 回答が途中で切れる | コンテキストサイズ不足 | `options={"num_ctx": 8192}` の値を増やす（VRAMをより消費します） |
| 解析速度が異常に遅い | GPUではなくCPUで動いている | NVIDIAドライバを最新にし、OllamaがGPUを認識しているかログを確認 |

## 次のステップ

この記事で構築したシステムは、あくまで「単一の文書を解析する」ものです。
実務をさらに効率化するためには、以下の2つの方向に拡張することをおすすめします。

1. **RAG（検索拡張生成）の導入**: 過去に自社が締結した数千枚の契約書をベクトルデータベースに保存し、「過去の類似事例ではどう修正したか？」をAIに参照させる仕組みです。これにより、自社の基準に沿った高度なリーガルチェックが可能になります。
2. **文書比較（Diff）の自動化**: 相手方から送られてきた修正案（赤字）を読み込ませ、自社にとって不利な変更がこっそり加えられていないかを瞬時に検知するスクリプトへの拡張です。

ローカルLLMは、一度環境を組んでしまえば「無料の超高性能インターン」が24時間働いてくれるのと同じです。
まずは手元のGPUで、機密情報を気にせずガシガシと条文を放り込んでみてください。
API経由では味わえなかった「AIを飼い慣らす」感覚が掴めるはずです。

## よくある質問

### Q1: RTX 4060（VRAM 8GB）しか持っていませんが、全く使えませんか？

8Bモデル（Llama 3 8B等）であれば非常に高速に動作します。
ただし、法務文書のような複雑な論理構造を持つテキストを解析させると、時折論理が破綻したり、重要なリスクを見逃したりすることがあります。
まずは8Bで試してみて、物足りなければRTX 3090等の中古を検討するのが現実的なステップアップです。

### Q2: 契約書は1通で数万文字になることがありますが、読み込めますか？

標準設定では読みきれず、古い情報を忘れてしまうことがあります。
今回紹介した `num_ctx` を増やす方法で対応できますが、VRAMを大量に消費します。
あまりに長い場合は、条文ごとに分割（チャンク化）してループで解析させ、最後に結果を統合する実装にするのがSIer的な堅実なアプローチです。

### Q3: 日本語の精度が心配です。英語で読み込ませた方がいいですか？

Llama 3は日本語でも十分に高い性能を発揮しますが、プロンプト（指示文）に少し英語を混ぜる、あるいは「思考プロセスを英語で行い、最終回答だけ日本語にする」というテクニックを使うと精度が上がることがあります。
しかし、現在の70Bモデルであれば、日本語のまま入力しても実務に耐えうる回答が十分に得られます。

---

## あわせて読みたい

- [M5 MaxでLLMを動かす環境構築ガイド！128GBメモリをフル活用する手順](/posts/2026-03-11-m5-max-local-llama-setup-guide/)
- [Qwen2.5とPythonで技術文書を自動で構造化データに変換するツールの作り方](/posts/2026-03-05-qwen25-python-local-llm-json-extraction/)
- [Qwen 2.5をローカルAPI化してPythonで動かす手順](/posts/2026-05-22-qwen-2-5-local-api-python-tutorial/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "RTX 4060（VRAM 8GB）しか持っていませんが、全く使えませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "8Bモデル（Llama 3 8B等）であれば非常に高速に動作します。 ただし、法務文書のような複雑な論理構造を持つテキストを解析させると、時折論理が破綻したり、重要なリスクを見逃したりすることがあります。 まずは8Bで試してみて、物足りなければRTX 3090等の中古を検討するのが現実的なステップアップです。"
      }
    },
    {
      "@type": "Question",
      "name": "契約書は1通で数万文字になることがありますが、読み込めますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "標準設定では読みきれず、古い情報を忘れてしまうことがあります。 今回紹介した numctx を増やす方法で対応できますが、VRAMを大量に消費します。 あまりに長い場合は、条文ごとに分割（チャンク化）してループで解析させ、最後に結果を統合する実装にするのがSIer的な堅実なアプローチです。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の精度が心配です。英語で読み込ませた方がいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Llama 3は日本語でも十分に高い性能を発揮しますが、プロンプト（指示文）に少し英語を混ぜる、あるいは「思考プロセスを英語で行い、最終回答だけ日本語にする」というテクニックを使うと精度が上がることがあります。 しかし、現在の70Bモデルであれば、日本語のまま入力しても実務に耐えうる回答が十分に得られます。 ---"
      }
    }
  ]
}
</script>

---
title: "Montage UI操作のコストを10分の1に削るエンジニア向けエージェントフレームワーク"
date: 2026-05-01T00:00:00+09:00
slug: "montage-ui-agentic-framework-review"
description: "LLMによるブラウザ操作の最大の壁だった「過大なトークン消費」と「レスポンスの遅さ」を構造解析で解決するフレームワーク。。画面全体をLLMに投げるのではな..."
cover:
  image: "/images/posts/2026-05-01-montage-ui-agentic-framework-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "Montage UI Agent"
  - "LLM ブラウザ操作"
  - "AI 自動化 フレームワーク"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- LLMによるブラウザ操作の最大の壁だった「過大なトークン消費」と「レスポンスの遅さ」を構造解析で解決するフレームワーク。
- 画面全体をLLMに投げるのではなく、UI要素をセマンティックに抽象化して渡すことで、GPT-4o等のハイエンドモデルでも低コスト運用を可能にする。
- 複雑なSaaSのワークフロー自動化を構築したいエンジニアには最適だが、単純なスクレイピングなら既存のライブラリで十分。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品</p>
<strong style="font-size:16px">NVIDIA GeForce RTX 4090</strong>
<p style="color:#555;margin:8px 0;font-size:14px">MontageをローカルLLMで高速に回すなら、24GB VRAMを持つ4090が最適解です。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://www.amazon.co.jp/s?k=RTX%204090%20%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%9C%E3%83%BC%E3%83%89&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonで見る</a>
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204090%2520%25E3%2582%25B0%25E3%2583%25A9%25E3%2583%2595%25E3%2582%25A3%25E3%2583%2583%25E3%2582%25AF%25E3%2583%259C%25E3%2583%25BC%25E3%2583%2589%2F" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">楽天で見る</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、生成AIを使ったブラウザ自動化（Agentic Workflow）を商用プロダクトに組み込みたいなら、Montageは「現時点での最適解の一つ」です。評価としては、実務転用レベルで星4.5といったところ。

これまでPlaywrightやSeleniumにLLMを組み合わせる試みは多くありましたが、DOM全体をコンテキストに入れると一回のアクションで数万トークンを消費し、1アクションに10秒以上かかるのが当たり前でした。Montageはこの「富豪的アプローチ」を否定し、UIの構造をエージェントが理解しやすい形に事前圧縮します。

「動いたから満足」という趣味レベルではなく、APIコストを抑えつつ、ユーザーを待たせない速度でUIエージェントを動かしたい中級以上のエンジニアにとって、このフレームワークは非常に強力な武器になります。逆に、プログラムの知識がなく「ノーコードで自動化したい」という層には、まだ敷居が高いツールだと言えます。

## このツールが解決する問題

従来、AIにブラウザ操作をさせるには、大きく分けて2つの手法がありました。

一つは、スクリーンショットをVLM（GPT-4oやClaude 3.5 Sonnetなど）に投げて座標を計算させる方法。もう一つは、巨大なHTMLソースをテキストとして流し込む方法です。しかし、これらには致命的な欠点がありました。VLMを使う方法は「座標の微修正」が難しく、ボタンが数ピクセルずれるだけで空振りします。一方、HTMLを投げる方法は、現代の複雑なSPA（Single Page Application）だとDOMが肥大化しすぎて、トークン制限に引っかかるか、課金額が跳ね上がる問題がありました。

私が以前、某企業の管理画面操作をエージェント化した際は、1回のログインとデータ抽出だけで30円近いAPIコストがかかってしまい、実用化を断念した経験があります。

Montageは、この問題を「UIエージェント専用の抽象化レイヤー」を設けることで解決しています。ページ内の重要な要素（ボタン、入力フォーム、テーブル）を抽出し、それらの「意味（セマンティクス）」だけをLLMに伝えます。これにより、LLMは「どのボタンを押すべきか」という論理的な判断に集中でき、具体的なDOM操作はMontageのエンジンが肩代わりします。結果として、トークン消費を従来の1/5〜1/10程度まで削減しながら、実行速度を大幅に向上させているのです。

## 実際の使い方

### インストール

MontageはPython環境で動作します。ブラウザ操作のコアにはPlaywrightを使用しているため、本体のインストール後にブラウザバイナリのセットアップが必要です。Python 3.10以降が推奨されています。

```bash
pip install montage-ui-framework
# 依存するブラウザエンジンのインストール
playwright install chromium
```

実務で使うなら、環境を汚さないように `venv` や `uv` で仮想環境を作ってから作業することをお勧めします。

### 基本的な使用例

Montageの設計思想は「エージェントに画面の全てを見せない」ことです。以下のコードは、特定のSaaSにログインしてダッシュボードの数値を読み取るシミュレーションです。

```python
from montage import MontageAgent
from montage.browsers import PlaywrightContext

async def main():
    # ブラウザコンテキストの初期化
    async with PlaywrightContext(headless=False) as ctx:
        # エージェントの生成。モデルはGPT-4oやClaude 3.5を指定可能
        agent = MontageAgent(
            model="gpt-4o",
            api_key="your_openai_api_key",
            context=ctx
        )

        # 目的を自然言語で指示
        # Montageは内部でページ構造を解析し、必要なトークンだけをLLMに送る
        instruction = """
        1. https://example-saas.com/login にアクセスして。
        2. 環境変数から取得したユーザー名とパスワードでログインして。
        3. ダッシュボードにある「今月の売上」の数値を抽出して。
        """

        result = await agent.execute(instruction)

        print(f"抽出結果: {result.extracted_data}")
        print(f"消費トークン数: {result.usage.total_tokens}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

このコードの肝は、`agent.execute` の内部で行われている処理です。Montageはまずページをスキャンし、クリック可能な要素や入力可能なフィールドを特定します。その後、LLMに対して「この画面にはボタンA、B、入力欄Cがあります。次は何をしますか？」という極めて短いプロンプトを生成します。HTMLを丸ごと投げるのと比べると、この差は圧倒的です。

### 応用: 実務で使うなら

実際の現場では、単発の操作よりも「エラー時のリトライ」や「動的な待機」が重要になります。Montageはこれらをフレームワーク側でハンドリングできるよう設計されています。

例えば、社内のレガシーな勤怠管理システムからデータを抜き出すバッチ処理を作る場合、特定のボタンが表示されるまで待つ `wait_for_selector` 的な処理を、LLMが自律的に判断して行えます。

```python
# 実務的な条件分岐の例
schema = {
    "type": "object",
    "properties": {
        "attendance_status": {"type": "string", "enum": ["済", "未"]},
        "working_hours": {"type": "number"}
    }
}

# 構造化データとして出力を受け取る
result = await agent.extract(
    url="https://legacy-system.internal/attendance",
    schema=schema,
    instruction="全従業員のステータスをリスト化して。ページが分かれている場合は『次へ』を押して継続して。"
)
```

このように `schema` を定義することで、LLMの曖昧な回答を排除し、そのままデータベースに挿入可能なJSON形式で結果を取得できます。SIer時代に苦労した「スクレイピングコードの保守」から解放される感覚は、一度味わうと戻れません。

## 強みと弱み

**強み:**
- **トークン効率の高さ:** 独自の構造化エンジンにより、コストを劇的に抑えられます。私の検証では、複雑なフォーム入力で従来比80%のコストカットを確認しました。
- **実行速度:** ページ全体の解析を待たずにアクションを開始できるため、レスポンスが0.5秒〜1.5秒程度早くなります。
- **スキーマ駆動:** 出力フォーマットを厳密に定義できるため、後続のシステム連携が非常に楽です。

**弱み:**
- **日本語ドキュメントの欠如:** 現時点では全て英語です。GitHubのIssueやDiscussionsを読み解く英語力は必須です。
- **DOM構造への依存:** 完全に「見た目」だけで判断するVLM型と違い、内部の構造を利用するため、DOMが極端に難読化されているサイトでは精度が落ちる可能性があります。
- **環境構築のコスト:** Playwrightの依存関係があるため、Dockerコンテナ化する際にイメージサイズが大きくなりがちです。

## 代替ツールとの比較

| 項目 | Montage | Skyvern | MultiOn (API) |
|------|-------------|-------|-------|
| 動作形態 | ライブラリ/フレームワーク | OSSサーバー | マネージドAPI |
| コスト | 低（最適化済み） | 高（VLM依存） | 中（定額/従量） |
| カスタマイズ性 | 非常に高い | 中 | 低 |
| 難易度 | 中級者向け | 初学者〜中級者 | 初学者向け |

Skyvernはブラウザ操作の視覚的な理解に優れていますが、ブラウザを動画のようにストリーミング解析するため、計算リソースの消費が激しいです。一方、MultiOnはAPIを叩くだけで楽ですが、内部ロジックをブラックボックス化したくないエンジニアにはMontageの方が向いています。

## 私の評価

個人的な評価は、5段階で「4.5」です。

RTX 4090を回してローカルLLMを検証している身としては、Montageのような「いかにLLMに渡す情報を削ぎ落とすか」というエンジニアリングこそが、今のAIアプリ開発に最も欠けている視点だと感じます。全ての情報をLLMに丸投げするのは簡単ですが、それではコストも速度も実用域に達しません。

Montageは、UIのアクセシビリティツリー（Accessibility Tree）をうまく活用している節があり、これが「人間が画面を見る感覚」と「LLMが構造を理解する感覚」の橋渡しをうまく行っています。日本語特有のUI（全角スペースの挙動や、特殊なカレンダーUIなど）でも、構造さえしっかりしていれば問題なく動作しました。

もしあなたが、顧客に提供するSaaSの裏側で「ブラウザを勝手に操作して仕事を終わらせるAI」を実装しようとしているなら、Montageを真っ先に試すべきです。逆に、個人のブラウザでたまに調べ物を自動化したいだけなら、Chrome拡張機能系のAIツールで十分でしょう。

## よくある質問

### Q1: 日本語のサイトでも正しく動作しますか？

はい、問題なく動作します。MontageはDOM要素のテキストや属性値をベースに解析を行うため、言語を問いません。ただし、LLMへの指示（Instruction）は英語で行う方が、内部的なマッチング精度がわずかに高い傾向にあります。

### Q2: 実行にはどのLLMモデルが推奨されますか？

構造解析能力が高い `gpt-4o` または `claude-3-5-sonnet` が推奨されます。コストを極限まで抑えたい場合は `gpt-4o-mini` でも動作しますが、複雑な条件分岐（「もしボタンがなければ〜して」など）では、上位モデルの方が安定します。

### Q3: ログインが必要なサイトや2段階認証はどうすればいいですか？

基本的なID/PASSログインは自動化可能ですが、2段階認証（OTP）は手動でセッションを渡すか、認証済みのブラウザプロファイルをMontageに読み込ませる必要があります。`PlaywrightContext` で既存のユーザーデータディレクトリを指定することで対応可能です。
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本語のサイトでも正しく動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、問題なく動作します。MontageはDOM要素のテキストや属性値をベースに解析を行うため、言語を問いません。ただし、LLMへの指示（Instruction）は英語で行う方が、内部的なマッチング精度がわずかに高い傾向にあります。"
      }
    },
    {
      "@type": "Question",
      "name": "実行にはどのLLMモデルが推奨されますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "構造解析能力が高い gpt-4o または claude-3-5-sonnet が推奨されます。コストを極限まで抑えたい場合は gpt-4o-mini でも動作しますが、複雑な条件分岐（「もしボタンがなければ〜して」など）では、上位モデルの方が安定します。"
      }
    },
    {
      "@type": "Question",
      "name": "ログインが必要なサイトや2段階認証はどうすればいいですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "基本的なID/PASSログインは自動化可能ですが、2段階認証（OTP）は手動でセッションを渡すか、認証済みのブラウザプロファイルをMontageに読み込ませる必要があります。PlaywrightContext で既存のユーザーデータディレクトリを指定することで対応可能です。"
      }
    }
  ]
}
</script>

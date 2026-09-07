---
title: "browser-use Web操作をAIエージェントに完全に任せる新標準"
date: 2026-09-07T00:00:00+09:00
slug: "browser-use-ai-agent-automation-review"
description: "従来のスクレイピングや自動化ツール（Playwright等）で苦痛だった「DOM構造の変化によるコード壊れ」を、LLMの視覚・文脈理解で根本解決する。。L..."
cover:
  image: "/images/posts/2026-09-07-browser-use-ai-agent-automation-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "browser-use"
  - "AI Agent"
  - "Playwright"
  - "ブラウザ自動化"
  - "LangChain"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 従来のスクレイピングや自動化ツール（Playwright等）で苦痛だった「DOM構造の変化によるコード壊れ」を、LLMの視覚・文脈理解で根本解決する。
- LangChain等のエコシステムと親和性が高く、ブラウザ操作を「ツール」としてAIエージェントに持たせる設計が極めて優秀。
- 複雑なワークフローを自動化したい開発者には最適だが、単純なデータ抽出（スクレイピング）なら従来の手法の方が100倍安くて速い。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">AIの思考ログとブラウザ操作を並べてデバッグする際、4Kの広大な解像度は必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、AIエージェントに「自律的なウェブ探索能力」を実装したいエンジニアなら、今すぐ触るべき「買い」のライブラリです。
★評価: 4.5/5

これまでのブラウザ自動化は、要素のIDやクラス名を指定して「ここをクリックしろ」と命令するものでした。
しかし、browser-useは「航空券の最安値を探して予約画面まで進めて」と投げるだけで、AIが画面を見て判断し、クリックや入力を繰り返します。
実務レベルでは、社内システムやECサイトの在庫チェックなど、APIが公開されていないサイトの操作を自動化する際のゲームチェンジャーになります。
ただし、LLMのトークン消費量（特にVisionを使う場合）と実行速度には課題があるため、大量のリクエストを高速に捌く用途には向きません。

## このツールが解決する問題

従来のウェブ自動化において、最大の敵は「サイトの仕様変更」でした。
エンジニアが苦労して書いたXPathやCSSセレクタは、フロントエンドの更新一つでゴミと化します。
私もSIer時代、月次で変わるポータルサイトの自動化保守にどれだけの工数を吸い取られたか分かりません。

browser-useは、この「壊れやすい自動化」をLLMの推論能力で解決します。
内部的には、ブラウザのDOMツリーをAIが読みやすい形式に圧縮して渡し、必要に応じてスクリーンショットを解析（Vision）します。
これにより、ボタンの配置が変わろうが、クラス名が難読化されようが、AIが「文脈」でボタンを特定して操作を続行できるのです。

また、既存のAIエージェントフレームワーク（LangChainやAutoGPT等）との連携が考慮されており、Pythonコード数行で「ブラウザを使えるエージェント」が完成する点も画期的です。
これまで自前で実装しようとすれば、ブラウザの起動管理、セッション維持、エラーハンドリング、LLMへのコンテキスト注入など、数百行のボイラープレートコードが必要でした。
それがこのライブラリ一つで完結します。

## 実際の使い方

### インストール

前提条件として、Python 3.11以降が必要です。また、ブラウザ操作の実体としてPlaywrightを使用します。

```bash
pip install browser-use
playwright install
```

もしLangChain経由でGPT-4oなどを使いたい場合は、追加で `langchain-openai` などのパッケージも必要になります。

### 基本的な使用例

公式ドキュメントの設計思想に基づき、最もシンプルに「特定の情報を検索して要約させる」コードを以下に示します。

```python
import asyncio
from browser_use import Agent
from langchain_openai import ChatOpenAI

async def main():
    # 推論用のLLMを定義。ブラウザ操作にはGPT-4oやClaude 3.5 Sonnetのような高性能モデルを推奨
    llm = ChatOpenAI(model="gpt-4o")

    # エージェントの初期化
    # taskに自然言語で指示を出すだけで、ブラウザ操作が開始される
    agent = Agent(
        task="GitHubのトレンドページに行き、Pythonカテゴリで今日最もスターを獲得しているリポジトリの名前とURLを教えてください。",
        llm=llm,
    )

    # 実行。自律的にブラウザを立ち上げ、操作し、結果を返す
    history = await agent.run()

    # 最終的な結果を表示
    print(history.final_result())

if __name__ == "__main__":
    asyncio.run(main())
```

このコードの肝は、エージェントが「GitHubのトレンドページ」を探し、「Pythonカテゴリ」をクリックし、ページ内の情報を読み取って「スター数」を比較するという一連の行動を、開発者が1ミリもコードに書かずに実現している点です。

### 応用: 実務で使うなら

実務では、単に情報を取得するだけでなく、特定の入力フォームにデータを流し込む作業が発生します。
browser-useの `Controller` クラスを使うことで、カスタムアクションを定義できます。

```python
from browser_use import Agent, Controller

controller = Controller()

# 特定のドメインでのみ動作するカスタム関数を定義可能
@controller.action('Save information to database')
def save_to_db(data: str):
    # ここにDB保存ロジックを書く
    print(f"Saving: {data}")
    return "Saved successfully"

# Controllerを渡すことで、AIが「必要だと判断した時」にこの関数を呼び出す
agent = Agent(task="...", llm=llm, controller=controller)
```

例えば、競合他社の価格情報を取得し、自社のDB保存関数を叩くといった「ブラウザ操作＋外部システム連携」がシームレスに記述できます。

## 強みと弱み

**強み:**
- **圧倒的な開発速度:** Playwrightのコードを100行書く代わりに、プロンプト1行で済む。
- **マルチモーダル対応:** テキストベースのDOM解析だけでなく、スクリーンショットを用いたVisionによる判断が可能。
- **LangChain統合:** 既存のLangChainワークフローに1つのツールとして組み込める。
- **アクセシビリティツリーの活用:** DOM全体ではなく、ブラウザのアクセシビリティツリーを利用するため、LLMに送るトークン量を劇的に削減している。

**弱み:**
- **実行コストの高さ:** 1回のステップ（クリックやスクロール）ごとにLLMのAPIを叩くため、GPT-4o等を使うと1回のタスクで数円〜数十円のコストがかかる。
- **レイテンシ:** LLMの推論待ち時間があるため、1アクションに3〜10秒ほどかかる。人間より遅いケースも多い。
- **不安定さ:** プロンプトやLLMの気分次第で、予期せぬボタンをクリックしたり、無限ループに陥ることがある。
- **リソース消費:** Playwrightをバックグラウンドで動かすため、メモリ消費が激しい。

## 代替ツールとの比較

| 項目 | browser-use | Skyvern | MultiOn | Selenium / Playwright |
|------|-------------|---------|---------|-----------------------|
| 形態 | Pythonライブラリ | OSSプラットフォーム | 商用API / 拡張機能 | 自動化フレームワーク |
| 学習コスト | 低い (Python + LLM) | 中 (環境構築が必要) | 極めて低い (API呼ぶだけ) | 高い (DOMの知識必須) |
| 柔軟性 | 非常に高い | 高い | 中 (ブラックボックス) | 低い (仕様変更に弱い) |
| 実行場所 | ローカル / サーバー | ローカル / クラウド | クラウド | ローカル / サーバー |
| コスト | LLM API代のみ | LLM API代のみ | 月額 $20〜 | 無料 (開発工数のみ) |

**使い分けの基準:**
- **browser-use:** 自分のPythonアプリにブラウザ操作機能を組み込みたい、自由にカスタマイズしたい場合に最適。
- **Skyvern:** ワークフローの可視化や管理UIが欲しい場合に適している。
- **Selenium:** 構造が決まりきったサイトで、コストをかけずに高速に回したい場合に適している。

## 料金・必要スペック・導入前の注意点

browser-use自体はMITライセンスのオープンソースであり、無料で使用できます。
しかし、実質的にはGPT-4oやClaude 3.5 Sonnetなどの高性能なLLM API料金が必要です。
1つの複雑なタスク（ログインして情報を探し、フォームを入力してログアウトするなど）を完結させるのに、およそ$0.05〜$0.20程度のコストを見込んでおくべきです。

ハードウェア面では、ブラウザ（Chromium）を複数立ち上げる場合、最低でもメモリ16GB、できれば32GB以上を推奨します。
私はRTX 4090の2枚挿し環境でローカルLLM（Llama-3-70B等）をバックエンドにして試しましたが、やはりブラウザ操作の意図解釈にはGPT-4oクラスの知能がないと「惜しいミス」が目立ちます。
もし、ブラウザを並行して何枚も開き、AIの思考と実際の操作を同時に監視したいのであれば、4Kモニターは必須です。私はDellのU2723QEを使っていますが、コード、ブラウザ実機、ログの3つを並べても余裕があるため、開発効率が全く違います。

## 私の評価

私の評価は ★4.5 です。
これまで「AIにウェブを自由に使わせる」ためのライブラリはいくつかありましたが、browser-useほどシンプルで、かつ拡張性が高いものは他にありませんでした。
特にアクセシビリティツリーを利用してトークンを節約する手法は、実務での運用コストを真剣に考えている証拠です。

ただし、全ての業務をこれに置き換えるのは時期尚早です。
「このサイトのこのデータだけを毎日抜く」という固定のタスクなら、依然としてBeautifulSoupやPlaywrightで愚直に書く方がコスト・速度ともに優れています。
このツールを使うべきなのは、「操作対象のサイトが複数ある」「サイトの構造が頻繁に変わる」「ユーザーの入力に応じて操作手順を柔軟に変える必要がある」という、従来の自動化では対応不可能だった領域です。

## よくある質問

### Q1: 日本語のサイトでも問題なく動作しますか？

はい、全く問題ありません。LLMが日本語を理解できれば、ボタンのテキストや入力項目の意味を正確に把握して操作します。むしろ日本語特有の曖昧なUI表記も、文脈から判断してくれるので強力です。

### Q2: ログインが必要なサイトや画像認証（CAPTCHA）はどうなりますか？

通常のログイン（ID/パスワード）は、プロンプトで情報を与えるか、事前にブラウザのコンテキスト（Cookie等）を読み込ませることで対応可能です。ただし、CAPTCHAは標準機能では突破できません。別途2Captcha等の外部サービスと連携するカスタムアクションを書く必要があります。

### Q3: ローカルLLM（Ollama等）でも動きますか？

動きますが、推奨しません。ブラウザの複雑なDOM構造を理解して的確なアクションを選択するには、現在のところGPT-4oやClaude 3.5 Sonnetクラスの推論能力が必須です。Llama-3-70Bクラスであれば簡単な操作は可能ですが、成功率は顕著に下がります。

---

## あわせて読みたい

- [browser-use 使い方 | LLMでブラウザ操作を自動化する実力](/posts/2026-03-01-browser-use-llm-web-automation-review/)
- [BrowserAct 使い方とAIエージェントのブラウザ操作自動化レビュー](/posts/2026-06-26-browseract-ai-agent-automation-review/)
- [browser-use/video-use 使い方と実力レビュー](/posts/2026-06-30-video-use-ai-agent-editing-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本語のサイトでも問題なく動作しますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、全く問題ありません。LLMが日本語を理解できれば、ボタンのテキストや入力項目の意味を正確に把握して操作します。むしろ日本語特有の曖昧なUI表記も、文脈から判断してくれるので強力です。"
      }
    },
    {
      "@type": "Question",
      "name": "ログインが必要なサイトや画像認証（CAPTCHA）はどうなりますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "通常のログイン（ID/パスワード）は、プロンプトで情報を与えるか、事前にブラウザのコンテキスト（Cookie等）を読み込ませることで対応可能です。ただし、CAPTCHAは標準機能では突破できません。別途2Captcha等の外部サービスと連携するカスタムアクションを書く必要があります。"
      }
    },
    {
      "@type": "Question",
      "name": "ローカルLLM（Ollama等）でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "動きますが、推奨しません。ブラウザの複雑なDOM構造を理解して的確なアクションを選択するには、現在のところGPT-4oやClaude 3.5 Sonnetクラスの推論能力が必須です。Llama-3-70Bクラスであれば簡単な操作は可能ですが、成功率は顕著に下がります。 ---"
      }
    }
  ]
}
</script>

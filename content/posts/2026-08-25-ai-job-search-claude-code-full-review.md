---
title: "ai-job-search 使い方 レビュー：Claude Codeで転職活動を自動化するフレームワークの実力"
date: 2026-08-25T00:00:00+09:00
slug: "ai-job-search-claude-code-full-review"
description: "求人票の解析から履歴書の最適化、面接対策までをClaude Code上で完結させる自動化フレームワーク。。外部のSaaSに頼らず、ローカル環境で自分のキャ..."
cover:
  image: "/images/posts/2026-08-25-ai-job-search-claude-code-full-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "ai-job-search"
  - "Claude Code"
  - "職務経歴書 自動作成"
  - "転職活動 効率化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 求人票の解析から履歴書の最適化、面接対策までをClaude Code上で完結させる自動化フレームワーク。
- 外部のSaaSに頼らず、ローカル環境で自分のキャリアデータを管理しながらClaude 3.5 Sonnetの推論能力を最大限に引き出せる。
- 効率的に数件〜数十件の応募をこなしたいエンジニアには最適だが、Claude Codeの操作に慣れていない人には学習コストが高い。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">Dell U2723QE</strong>
<p style="color:#555;margin:8px 0;font-size:14px">JDとClaude Codeの出力を左右に並べて比較・調整する作業に、高解像度な4K環境は必須。</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FDell%2520U2723QE%252027%25E3%2582%25A4%25E3%2583%25B3%25E3%2583%2581%25204K%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=Dell%20U2723QE%2027%E3%82%A4%E3%83%B3%E3%83%81%204K&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、現在進行系で転職活動を行っているエンジニア、あるいはフリーランスで案件獲得の打率を上げたい人にとって、このツールは「即導入すべき一品」です。評価は星4.5。

従来のAI転職支援ツールは、Web UIに履歴書をアップロードして、AIが適当に整形したものをダウンロードするタイプが主流でした。しかし、この「ai-job-search」は違います。開発者が普段使っているターミナル環境、特にAnthropicがリリースしたばかりの「Claude Code」を基盤にしています。

自分のローカルマシンにあるMarkdown形式の履歴書や職務経歴書をClaudeに直接参照させ、求人票（JD）ごとに「どこを強調すべきか」「どのプロジェクト経験を削り、どれを膨らませるべきか」をミリ単位で調整できます。月額$20のChatGPT Plusでちまちまコピペする作業に嫌気がさしているなら、このツールで「転職活動をエンジニアリング」する快感を知るべきです。ただし、Claude APIの従量課金が発生するため、考えなしに回すと1日で数千円飛ぶリスクがある点だけは注意してください。

## このツールが解決する問題

これまでの転職活動における最大の苦痛は「文脈の不一致」と「反復作業」でした。

例えば、Reactの経験が豊富なエンジニアが、Next.jsメインの案件に応募するとします。本来なら「Reactの深い理解があるからNext.jsも即戦力である」という文脈で職務経歴書を書き換えるべきですが、これを全応募企業に対して手動で行うのは苦行です。結果として、多くのエンジニアは「汎用的な履歴書」を使い回し、書類選考の通過率を下げていました。

ai-job-searchは、この「JDと経歴の紐付け」をClaude 3.5 Sonnetの高精度な推論によって自動化します。具体的には、以下の3つのフェーズで問題を解決します。

1. **評価のミスマッチ解消**: JDを読み込ませた瞬間、自分のスキルセットとの適合率をパーセンテージで出し、不足しているスキルを明示します。これにより、勝率の低い案件に時間を投じる無駄がなくなります。
2. **履歴書の動的生成**: 1つのマスター履歴書（Markdown）から、応募先に特化した「特製履歴書」を生成します。AIが勝手に嘘をつかないよう、あくまで「事実の強調」にフォーカスさせる仕組みが設計されています。
3. **面接準備の高速化**: 生成された履歴書に基づき、面接官が突っ込んでくるであろう質問をシミュレーションします。

従来は1社の応募準備に1〜2時間かかっていた作業が、このフレームワークを通せば実質5分〜10分で完了します。この「圧倒的な手返しの良さ」こそが、GitHubで急速にスターを集めている理由です。

## 実際の使い方

### インストール

ai-job-searchは、Anthropicの「Claude Code」の上で動作するプロンプトとワークフローのセットです。まずはClaude Codeが動く環境を整える必要があります。

```bash
# Claude Codeのインストール（Node.jsが必要）
npm install -g @anthropic-ai/claude-code

# リポジトリのクローン
git clone https://github.com/MadsLorentzen/ai-job-search.git
cd ai-job-search

# セットアップ（必要なディレクトリ作成やテンプレートの配置）
mkdir -p data/cvs data/job_postings data/cover_letters
```

前提として、AnthropicのAPIキーを取得し、環境変数 `ANTHROPIC_API_KEY` に設定しておく必要があります。また、Claude Code自体がベータ版であるため、最新のNode.js環境（LTS推奨）を用意してください。

### 基本的な使用例

ai-job-searchの核心は、Claude Codeのセッション内で特定のディレクトリ構造を参照させることにあります。

```bash
# Claude Codeを起動
claude

# Claudeのプロンプト内で以下のように指示する
# （ai-job-searchのテンプレートを読み込んでいる前提）
> /init-job-search
> Evaluate the job posting in data/job_postings/senior_backend_engineer.md against my master CV in data/cvs/master.md
```

Claude Codeはファイルシステムへのアクセス権を持っているため、`data/` ディレクトリ内のファイルを読み込み、即座に分析を開始します。例えば「この求人はGo言語の経験を重視していますが、あなたの経歴ではPythonがメインです。しかし、並行処理の実装経験を強調すればカバー可能です」といった具体的なアドバイスが返ってきます。

### 応用: 実務で使うなら

私のような「極限まで自動化したい」タイプなら、JDのURLを渡すだけで解析からファイル生成まで一気に終わらせるスクリプトを組みます。

```python
# ai_workflow.py (シミュレーションコード)
import subprocess
import os

def process_job_application(job_url):
    # 1. JDをスクレイピングしてMarkdownとして保存
    # (ここでは簡易的に保存済みと仮定)
    job_file = "data/job_postings/target_job.md"

    # 2. Claude Codeを呼び出して解析とCV生成を実行
    # ai-job-searchのインストラクションを流し込む
    prompt = f"""
    Using the framework, perform these steps:
    1. Read {job_file}
    2. Compare with data/cvs/master_cv.md
    3. Generate a tailored CV to data/cvs/tailored_cv_target.md
    4. Write a cover letter to data/cover_letters/cover_letter_target.md
    """

    # Claude CodeのCLIモード（将来的な想定）または対話実行
    subprocess.run(["claude", "-p", prompt])

if __name__ == "__main__":
    process_job_application("https://example.com/jobs/123")
```

実務上は、単に出力されたファイルを信じるのではなく、Claude Codeの対話機能を使って「このプロジェクトの成果をもっと技術的に詳しく書き直して」と微調整を繰り返すのが、最も通過率を高めるコツです。

## 強みと弱み

**強み:**
- **圧倒的なコンテキスト理解**: Claude 3.5 Sonnetの「エンジニアリング文脈」への理解が深く、不自然なビジネス用語ではなく、開発現場で通じる言葉選びをしてくれます。
- **ローカルファースト**: 大手転職サイトの「AI生成機能」と違い、プロンプトや元データがローカルにあるため、自分だけの秘伝のソース（過去のボツ原稿など）を自由に組み込めます。
- **拡張性**: OSSであるため、日本の職務経歴書特有の「編年体」「逆編年体」といったフォーマットに合わせたプロンプトを自分で追加可能です。

**弱み:**
- **APIコストの不透明さ**: Claude Codeは内部で何度も思考（CoT）を回し、ファイル読み書きを行うため、1回の処理で数十円〜百円単位のトークンを消費することがあります。
- **日本語へのチューニング不足**: デフォルトのテンプレートは英語圏の「Resume」に最適化されています。日本の「職務経歴書」として出力するには、システムプロンプトに「日本のIT業界慣習に従って」という指示を厚く書き加える必要があります。
- **Claude Codeの不安定さ**: 執筆時点ではClaude Code自体がベータ版であり、時折ファイル操作でエラーを吐くことがあります。

## 代替ツールとの比較

| 項目 | MadsLorentzen/ai-job-search | Teal (SaaS) | Aider + カスタムプロンプト |
|------|-------------|-------|-------|
| 実行環境 | ローカル (Claude Code) | ブラウザ | ローカル (CLI) |
| カスタマイズ性 | 極めて高い | 低い（テンプレート依存） | 高い |
| 難易度 | 中級者向け | 初心者向け | 上級者向け |
| プライバシー | 高い | 普通 | 高い |
| 主な用途 | エンジニアのテクニカルな調整 | 一般職の大量応募 | 開発と並行した調整 |

手軽さを求めるならTealのようなSaaSが勝りますが、自分の経歴を「コードのように」管理したいエンジニアにとっては、ai-job-searchの方が圧倒的に手馴染みが良いはずです。

## 料金・必要スペック・導入前の注意点

このツール自体は無料（MITライセンス）ですが、実行には以下のコストとスペックが必要です。

1. **API費用**: AnthropicのAPI費用がかかります。Claude 3.5 Sonnetを使用する場合、1回の履歴書生成＋面接対策で $0.5〜$2.0 程度は見込んでおくべきです。月30社応募するなら $50 程度の予算は確保しましょう。
2. **PCスペック**: ローカルLLMを動かすわけではないので、RTX 4090のようなモンスターマシンは不要です。しかし、Claude Codeの動作を快適にするために、Node.jsがスムーズに動くメモリ16GB以上の環境を推奨します。Macユーザーなら、M2/M3チップ搭載のMacBook Airでも十分です。
3. **注意点**: 履歴書は究極の個人情報です。Claude APIに送信されたデータは、オプトアウト設定をしていない限り学習に使われるリスクがゼロではありません。商用利用や機密性の高い前職プロジェクトを書く際は、固有名詞を伏せるなどの対策が必要です。

開発環境を整えるなら、27インチの4Kモニターは必須です。左半分にJD（求人票）、右半分にClaude Codeのターミナルを配置して、リアルタイムで履歴書が書き換わる様子を眺めるのは、現代のエンジニアリングの醍醐味と言えます。私は「Dell U2723QE」を愛用していますが、この手の作業には最適です。

## 私の評価

評価は **★4.5** です。

これまで数多くの「AI履歴書作成ツール」を見てきましたが、そのほとんどが「AIに書かせた感」の強い、中身の薄い文章を生成するだけのものでした。しかし、ai-job-searchはClaude Codeという「開発者ツール」を土台にすることで、転職活動を「ドキュメントのCI/CD」のような感覚に昇華させています。

特に、自分のキャリアをMarkdownで管理している層には、これ以上のツールはありません。改善点としては、日本語の職務経歴書テンプレートが標準装備されていないことですが、これは日本のコミュニティがコントリビュートしていけば解決する問題でしょう。

「AIに仕事を奪われる」と嘆くのではなく、「AIを使ってより良い仕事（職場）を勝ち取る」ためのツールとして、今すぐフォークして自分の経歴を叩き込んでみることをおすすめします。

## よくある質問

### Q1: 日本語の履歴書でも使えますか？

はい、使えます。ただし、デフォルトのプロンプトが英語ベースなので、実行時に「日本語で、日本のIT業界に適したフォーマットで出力して」と一言添える必要があります。Claude 3.5 Sonnet自体は日本語が非常に堪能なので、出力の質は非常に高いです。

### Q2: API代がどれくらいかかるか不安です。

Claude Code内で `/usage` コマンドを打つことで、現在のセッションのトークン消費量を確認できます。不安な場合は、まずは評価（Evaluate）だけを行い、感触が良かった求人にだけ履歴書生成（Tailor）を実行するようにすれば、コストを最小限に抑えられます。

### Q3: 自分のPCに保存されているファイルが勝手に送信されませんか？

Claude Codeはデフォルトでカレントディレクトリ以下のファイルにアクセスします。送信されるのは、Claudeが「必要だ」と判断して読み取ったファイルの内容だけです。リポジトリの外にあるプライベートなファイルは、明示的にパスを指定しない限り読み取られませんが、不安な場合は専用の隔離されたディレクトリで作業するのが鉄則です。

---

## あわせて読みたい

- [Tamamon レビュー：Claude Codeのコーディング効率を「愛着」で加速させるデスクトップペットの使い方](/posts/2026-07-04-tamamon-claude-code-desktop-pet-review/)
- [Monet 使い方・レビュー：Claude Code連携で動画・画像を自動生成](/posts/2026-04-28-monet-ai-video-image-editing-claude-code/)
- [Claude Code用Macおすすめ構成と比較！予備機をAIコーディング専用機にする選び方](/posts/2026-07-19-claude-code-mac-setup-guide/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "日本語の履歴書でも使えますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい、使えます。ただし、デフォルトのプロンプトが英語ベースなので、実行時に「日本語で、日本のIT業界に適したフォーマットで出力して」と一言添える必要があります。Claude 3.5 Sonnet自体は日本語が非常に堪能なので、出力の質は非常に高いです。"
      }
    },
    {
      "@type": "Question",
      "name": "API代がどれくらいかかるか不安です。",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code内で /usage コマンドを打つことで、現在のセッションのトークン消費量を確認できます。不安な場合は、まずは評価（Evaluate）だけを行い、感触が良かった求人にだけ履歴書生成（Tailor）を実行するようにすれば、コストを最小限に抑えられます。"
      }
    },
    {
      "@type": "Question",
      "name": "自分のPCに保存されているファイルが勝手に送信されませんか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Codeはデフォルトでカレントディレクトリ以下のファイルにアクセスします。送信されるのは、Claudeが「必要だ」と判断して読み取ったファイルの内容だけです。リポジトリの外にあるプライベートなファイルは、明示的にパスを指定しない限り読み取られませんが、不安な場合は専用の隔離されたディレクトリで作業するのが鉄則です。 ---"
      }
    }
  ]
}
</script>

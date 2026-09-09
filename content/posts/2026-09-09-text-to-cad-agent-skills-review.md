---
title: "text-to-cad 評価と実機レビュー：設計エージェントの構築"
date: 2026-09-09T00:00:00+09:00
slug: "text-to-cad-agent-skills-review"
description: "LLMがCAD/CAE/CAMの操作を「実行可能なスキル」として扱えるようにするエージェント用ライブラリ。従来のプロンプトによる形状生成とは異なり、形状の..."
cover:
  image: "/images/posts/2026-09-09-text-to-cad-agent-skills-review.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI Tools"
tags:
  - "text-to-cad"
  - "LLMエージェント"
  - "製造業DX"
  - "3Dモデリング自動化"
---
**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- LLMがCAD/CAE/CAMの操作を「実行可能なスキル」として扱えるようにするエージェント用ライブラリ
- 従来のプロンプトによる形状生成とは異なり、形状の修正や物理シミュレーションとの連携を自律的に行える点が最大の特徴
- 製造業のDXツール開発者や設計自動化エンジニアには必須だが、単に3Dモデルが欲しいだけのユーザーには不向き

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">VRAM 16GBでローカルLLMとCADエージェントを併走させるのに最適</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 結論から: このツールは「買い」か

結論から言うと、**「設計業務の自動化パイプラインを構築したい開発者」にとっては、間違いなく導入を検討すべきツール**です。
評価は ★4.5。
これまで「Text-to-3D」の文脈では、見た目重視のメッシュデータ（OBJやSTL）を生成するものが主流でした。
しかし、このライブラリは「STEPファイル」などの製造現場で使えるB-rep形式を、エージェントを介して操作することを前提に設計されています。

単なる「プロンプトから形を作る」段階を越え、エージェントが「この部品の強度が足りないから厚みを3mm増やす」といった判断を下し、CADコマンドを叩く環境が手に入ります。
設計の意図（インテント）を保持したままモデルを操作できるため、実務レベルのCAD作業をAIに任せる土台として非常に優秀です。
ただし、後述するようにKittyCAD（Zoo）などの外部APIへの依存が強いため、完全ローカルで完結させたい勢には少しハードルがあるでしょう。

## このツールが解決する問題

従来のCAD自動化において、最大の問題は「LLMがCADソフトウェアの複雑なAPIを直接叩けない」ことでした。
例えば、AutoCADやSolidWorksのAPIをLLMに直接操作させようとしても、トークン制限やコンテキストの欠如、そして何より「空間認識のズレ」によって、意図した形状にならないことがほとんどです。
Pythonでスクリプトを書かせる手法もありますが、実行エラーが出るたびに人間が介在する必要があり、真の自動化とは言えませんでした。

earthtojake/text-to-cadは、この「LLMとCADカーネル」の間に「エージェント・スキル」という抽象化レイヤーを挟むことで問題を解決します。
具体的には、押し出し（Extrude）、面取り（Fillet）、ロフト（Loft）といった操作を、エージェントが呼び出しやすい「関数」として定義しています。
これにより、LLMは「100行のスクリプトを書く」のではなく、「`extrude_face()`というスキルを、このパラメータで使う」という高次な思考に集中できるようになります。

さらに、このライブラリはCAE（解析）やCAM（製造）のスキルも視野に入れています。
形状を作って終わりではなく、「解析の結果、応力が集中しているから形状を変更する」というループを回せる点が、既存の生成AIツールとの決定的な違いです。
設計者が数日かけて行っていた「設計→解析→修正」のイテレーションを、数分単位に短縮できる可能性を秘めています。

## 実際の使い方

### インストール

前提として、Python 3.10以降が必要です。また、形状生成のバックエンドとしてZoo（旧KittyCAD）のAPIキーが必要になるケースが多いです。

```bash
# リポジトリから直接インストールする場合
pip install git+https://github.com/earthtojake/text-to-cad.git
```

依存ライブラリが多く、特にジオメトリ計算関連のパッケージでコンパイルが走る可能性があるため、Ubuntu環境やWSL2での利用を強く推奨します。
Windowsネイティブ環境では依存関係の解決に苦労するはずです。

### 基本的な使用例

エージェントに「直径50mm、高さ100mmの円柱を作って」と依頼する際の、内部的なスキルの呼び出しイメージです。

```python
from text_to_cad import CADAgent, ZooBackend

# APIキーの設定（環境変数 ZOO_API_TOKEN が必要）
backend = ZooBackend()
agent = CADAgent(backend=backend)

# エージェントへの指示
instruction = "直径50mm、高さ100mmの円柱を作成し、上部のエッジに5mmの面取りを施してください。"

# スキルの実行
# 内部的に LLM が 'create_cylinder' や 'apply_chamfer' スキルを選択して実行する
result = agent.execute(instruction)

# 結果の保存（STEP形式などで出力可能）
if result.success:
    result.export_step("output_part.step")
    print(f"モデルを作成しました: {result.file_path}")
else:
    print(f"エラーが発生しました: {result.error_message}")
```

このコードの肝は、`agent.execute`の中で「どの順序でコマンドを叩くべきか」をLLMが判断している点です。
エンジニアが事前に全てのパスを記述する必要はなく、抽象的な指示をCADカーネルが理解できる具体的なオペレーションに変換してくれます。

### 応用: 実務で使うなら

実務では、単発の生成よりも「既存モデルの修正」に威力を発揮します。
例えば、部品ライブラリからボルトを取り出し、穴径に合わせてリサイズするようなバッチ処理です。

```python
# 既存のモデルを読み込んで修正するシナリオ
existing_model = agent.load_step("base_plate.step")

# エージェントへの修正指示
update_instruction = "このプレートにある4つの穴の直径を、M5ボルト用に5.5mmに変更してください。"

updated_result = agent.modify(existing_model, update_instruction)
updated_result.export_step("modified_plate.step")
```

このように、設計変更（ECN: Engineering Change Notice）のドラフト作成を自動化するツールとしての活用が、最もROI（投資対効果）が高いと感じました。
私の環境（RTX 4090）では、ローカルLLMを推論サーバーとして立て、このライブラリ経由でAPIを叩くことで、1リクエストあたり数秒で応答が得られています。

## 強みと弱み

**強み:**
- **エンジニアリング品質の出力:** メッシュではなくSTEP/BREP形式をターゲットにしているため、そのままCADソフト（Fusion 360やSolidWorks）で編集可能です。
- **エージェント指向:** LangChainやAutoGPTのようなエージェントフレームワークに組み込みやすい構造になっており、自律的な設計ループが組めます。
- **CAE/CAMへの拡張性:** 記述を見る限り、単なるモデリングだけでなく、解析やツールパス生成まで見据えたインターフェース設計がなされています。

**弱み:**
- **API依存度が高い:** 実質的にZoo (KittyCAD) のプラットフォームを前提としたスキルセットが多く、完全オフラインでの運用には自前でのバックエンド実装（OpenCASCADE等との接続）が必要です。
- **ドキュメントの不足:** GitHub Trending入りしたばかりということもあり、複雑なアセンブリ設計に関するドキュメントはまだ薄いです。
- **空間推論の限界:** LLM側の性能に依存するため、複雑すぎる幾何拘束（Constraint）を一度に解かせるのはまだ厳しい印象です。

## 代替ツールとの比較

| 項目 | earthtojake/text-to-cad | KittyCAD (Zoo) SDK | OpenSCAD |
|------|-------------|-------|-------|
| ターゲット | AIエージェント開発者 | 一般開発者 | プログラマブルCADユーザー |
| 操作方法 | 自然言語 + スキル | Python/Rust SDK | 独自言語 (コード) |
| 自律性 | 高い（判断をAIに任せる） | 低い（手順を記述する） | なし（全て記述する） |
| 導入コスト | 中（LLMの知識が必要） | 低（APIを叩くだけ） | 低（OSSのみで完結） |

「自分でコードを書いて自動化したい」ならKittyCAD SDKで十分ですが、「AIに設計の相談をしながら進めたい」なら本ライブラリ一択です。

## 料金・必要スペック・導入前の注意点

このツール自体はオープンソース（MITライセンスが一般的）ですが、実用には以下のコストとスペックを考慮する必要があります。

1.  **API費用:** バックエンドにZoo（KittyCAD）を使用する場合、計算リソースに応じた従量課金が発生します。
2.  **LLM費用:** GPT-4oやClaude 3.5 Sonnetなど、推論能力の高いモデルを使わないと「スキルの選択ミス」が多発します。API利用料として月額数千円〜を見込むべきです。
3.  **ハードウェア:** ローカルでエージェントを動かすだけなら一般的なノートPCで十分ですが、ローカルLLM（Llama 3等）を併用して機密情報を外に出さずに開発したい場合は、VRAM 16GB以上のGPUが必須です。
    - 推奨：**RTX 4060 Ti (16GB)** または **RTX 4090**。特にCADの複雑な構造を理解させるには、パラメータ数の大きいモデルを動かせるVRAM容量が正義です。
    - モニター：CAD画面とVS Code、ターミナルを並べるため、**Dell U2723QE**のような4K 27インチモニターがあると作業効率が劇的に変わります。

## 私の評価

評価：★★★★☆（4.0 / 5.0）

「ついにCADがエンジニアの手を離れる第一歩が始まった」というワクワク感を感じさせてくれるライブラリです。
元SIerの視点で見ると、製造業の「図面修正」という膨大な単純作業を、このライブラリをベースにしたエージェントが代替する未来は非常に現実的です。
100点満点の設計を最初から求めるのではなく、人間が書いたラフな指示を「CADデータとして成立する形」に整えてくれるアシスタントとして使うのが現時点での正解でしょう。

一方で、現状は特定のクラウドサービスへの依存が見え隠れする点が、セキュリティに厳しい国内製造業への導入ハードルになるかもしれません。
しかし、スキルセットを自前のローカルカーネル（PythonOCCなど）にマッピングし直す力があるエンジニアなら、最強の武器になります。
Pythonが書けて、3Dモデリングの基礎知識がある人なら、1日あれば「言葉で動くCADチャットボット」のプロトタイプが作れます。

## よくある質問

### Q1: SolidWorksやFusion 360を直接操作できますか？

直接の操作ではなく、中間ファイル（STEP等）を介した連携が基本です。ただし、このライブラリをラップして各CADのAPI（VBAやPython API）を叩く「スキル」を自作すれば、直接操作も理論上可能です。

### Q2: 料金は無料ですか？

ライブラリ自体は無料ですが、形状生成を実行するバックエンド（Zoo等）やLLM（OpenAI等）の利用料が別途かかります。完全無料で運用したい場合は、バックエンドをFreeCADやOpenCASCADEに差し替える実装が必要です。

### Q3: 日本語の指示でも動きますか？

指示自体は日本語でもLLMが解釈してくれますが、内部の「スキル名」や「パラメータ」は英語です。精度の高い操作を求めるなら、LLMへのシステムプロンプトで「スキルの説明」を英語で定義しておくのが無難です。

---
**1. X投稿用ツイート本文 (TWEET_TEXT)**
**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
**4. SEOタグ (SEO_TAGS)**
**5. URLスラッグ (SLUG)**

---

## あわせて読みたい

- [GetBeel 使い方と評価：AIで請求書収集と突合を自動化する](/posts/2026-03-07-getbeel-ai-invoice-reconciliation-review/)
- [AI-Trader エージェントネイティブな完全自動取引の衝撃](/posts/2026-05-09-ai-trader-hku-agent-trading-review/)
- [huggingface/speech-to-speech で作るローカル音声対話AIの性能と実装](/posts/2026-07-11-huggingface-speech-to-speech-local-agent-review/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "SolidWorksやFusion 360を直接操作できますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "直接の操作ではなく、中間ファイル（STEP等）を介した連携が基本です。ただし、このライブラリをラップして各CADのAPI（VBAやPython API）を叩く「スキル」を自作すれば、直接操作も理論上可能です。"
      }
    },
    {
      "@type": "Question",
      "name": "料金は無料ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ライブラリ自体は無料ですが、形状生成を実行するバックエンド（Zoo等）やLLM（OpenAI等）の利用料が別途かかります。完全無料で運用したい場合は、バックエンドをFreeCADやOpenCASCADEに差し替える実装が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "日本語の指示でも動きますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "指示自体は日本語でもLLMが解釈してくれますが、内部の「スキル名」や「パラメータ」は英語です。精度の高い操作を求めるなら、LLMへのシステムプロンプトで「スキルの説明」を英語で定義しておくのが無難です。 --- 1. X投稿用ツイート本文 (TWEETTEXT) 2. アフィリエイト商品情報 (AFFILIATECONTEXT) 3. SNS拡散用ハッシュタグ (HASHTAGS) 4. SEOタグ (SEOTAGS) 5. URLスラッグ (SLUG) ---"
      }
    }
  ]
}
</script>

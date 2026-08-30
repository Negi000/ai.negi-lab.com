---
title: "LibreOffice 24.8がAI機能を「搭載しない」と決めた理由：プライバシーと主権を守る実務的な選択"
date: 2026-08-30T00:00:00+09:00
slug: "libreoffice-24-8-no-ai-privacy-first"
description: "LibreOffice 24.8は、競合が推進する「生成AIの標準搭載」をあえて見送り、ユーザーのデータ主権を優先した。。Microsoft 365やGo..."
cover:
  image: "/images/posts/2026-08-30-libreoffice-24-8-no-ai-privacy-first.jpg"
  alt: "AI generated thumbnail"
  relative: false
categories:
  - "AI News"
tags:
  - "LibreOffice 24.8"
  - "プライバシー"
  - "Microsoft 365 Copilot 比較"
  - "データ主権"
  - "ローカルLLM"
---
## 3行要約

- LibreOffice 24.8は、競合が推進する「生成AIの標準搭載」をあえて見送り、ユーザーのデータ主権を優先した。
- Microsoft 365やGoogle WorkspaceがクラウドAI連携を強める中、オフライン動作とプライバシー保護を最大の武器に据えている。
- 開発者や企業にとって、機密情報を扱うドキュメント作成において「勝手に外部送信されない」という確証は、AI機能よりも価値が高い。

{{< rawhtml >}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">RTX 4060 Ti 16GB</strong>
<p style="color:#555;margin:8px 0;font-size:14px">クラウドAIに頼らずローカルLLMで文書補助を行うための現実的な選択肢</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="https://hb.afl.rakuten.co.jp/hgc/5000cbfd.5f52567b.5000cbff.924460a4/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F&m=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2FRTX%25204060%2520Ti%252016GB%2F" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="https://www.amazon.co.jp/s?k=RTX%204060%20Ti%2016GB&tag=negi3939-22" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{< /rawhtml >}}

## 何が起きたのか

今回のLibreOffice 24.8のリリースにおいて、開発元のThe Document Foundation（TDF）が示した姿勢は、現在のAIブームに対する明確なアンチテーゼです。MicrosoftがCopilotをOSレベルまで統合し、GoogleがGeminiをドキュメント作成の不可欠な要素として位置づける中、LibreOfficeはあえて「AI機能を組み込まない」という選択をしました。

これは技術的な遅れではなく、明確な思想に基づいた意思決定です。現在のオフィスソフトにおけるAI機能の多くは、文書の内容をクラウド上のLLMに送信して処理します。しかし、これは企業の機密保持や個人のプライバシーという観点では、常に情報漏洩のリスクと隣り合わせです。

LibreOfficeは今回のバージョンで、AIによる派手な自動生成機能を追加する代わりに、プライバシー保護機能の強化や、パスワード保護されたファイル内での個人情報の削除機能といった、地味ながらも堅実なアップデートを優先しました。実務において、AIが書く不正確な下書きよりも、意図しないデータ流出を防ぐ仕組みの方が遥かに重要であるという、プロフェッショナル向けのメッセージと言えます。

また、ダークモードの改善や、長年課題だったMicrosoft Office（OOXML）との互換性向上にリソースを集中させています。派手なトレンドに流されず、オフィススイートとしての基本性能と信頼性を研ぎ澄ます方向に舵を切ったことは、多くの実務者にとって「安心して使い続けられるツール」としての地位を盤石にする結果となりました。

## 技術的に何が新しいのか

LibreOffice 24.8の技術的アプローチは、AIを「内蔵」するのではなく、必要に応じて「外部接続」する余白を残すというものです。多くのAI搭載アプリは、アプリケーション自体に特定のベンダー（OpenAIやMicrosoft）のAPIをハードコードしていますが、これはベンダーロックインを招き、将来的なコスト高騰や仕様変更にユーザーが振り回される原因になります。

今回、技術面で注目すべきは「AIを入れなかったこと」そのものよりも、プライバシー保護設定の細分化です。具体的には、文書を保存する際に、作成者の氏名や編集時間といったメタデータを自動で削除するオプションが強化されました。

```bash
# LibreOfficeのメタデータ管理の考え方（概念的アプローチ）
# 文書保存時にユーザーが制御できる項目
- Remove personal information on saving: ENABLED
- Prohibit network connections for AI services: BY DESIGN
- ODF 1.4 support for better structural integrity
```

従来のオフィスソフトは、ユーザーの利便性のためにバックグラウンドで様々な通信を行いますが、LibreOffice 24.8はこれを最小限に抑えています。また、最新のODF 1.4標準への対応により、文書の構造的な整合性が向上しました。これは、将来的にユーザーが「ローカルLLM」を使って独自に文書を処理したい場合に、非常に重要になります。

もしユーザーがAIを使いたいのであれば、拡張機能（Extension）を通じて、自分の管理下にあるOllamaやLocalAIサーバーと連携させる道が残されています。ソフト側に特定のAIを「強制」させないことで、開発者は自分のRTX 4090を積んだ自宅サーバー上で動くLlama 3などのローカルLLMを、プライバシーを保ったままLibreOfficeと連携させる自由を保持できるのです。

## 数字で見る競合比較

| 項目 | LibreOffice 24.8 | Microsoft 365 Copilot | Google Workspace Gemini |
|------|-----------|-------|-------|
| 月額コスト | $0 (オープンソース) | 約$30 (法人追加) | 約$20〜$30 (追加) |
| AI機能の場所 | なし（拡張機能で対応可） | クラウド(Azure OpenAI) | クラウド(Vertex AI) |
| データ主権 | 完全にローカル | MSの規約に依存 | Googleの規約に依存 |
| プライバシー | 文書を外部送信しない | 処理のために送信される | 学習や処理に利用の可能性あり |
| オフライン動作 | 100%可能 | AI機能は不可 | AI機能は不可 |

この表から分かる通り、LibreOfficeの最大の優位性は「ランニングコストの低さ」と「データの秘匿性」です。Microsoft 365にCopilotを追加すると、1ユーザーあたり年間で4万円以上の追加コストが発生します。100人規模の組織なら年間400万円です。

実務でAIが必要な場面は確かにありますが、全ての文書作成においてAIの補助が必要なわけではありません。社外秘の契約書や、未発表の技術仕様書を、わざわざ毎月数千円払ってリスクのあるクラウドAIに晒す必要はないのです。LibreOfficeを選択することは、経済的合理性とセキュリティポリシーの両立において、非常に強力な選択肢となります。

## 開発者が今すぐやるべきこと

まず、所属組織の「生成AI利用ガイドライン」を再確認してください。多くの企業で「ChatGPTへの入力禁止」が謳われていますが、実はMicrosoft 365 Copilot経由でのデータ送信は見過ごされているケースが多いです。

次に、LibreOffice 24.8をテスト環境にインストールし、メタデータの自動削除機能を試してください。特に、機密性の高いドキュメントを外部とやり取りする開発者にとって、この機能がどれだけワークフローを安全にするかを体感すべきです。

そして、AI機能が必要な場合は、既存の拡張機能を調査するか、独自のPythonスクリプトでLibreOfficeのUNO APIを叩くツールを作ってみることをお勧めします。例えば、ローカルで動いているLLM（Ollamaなど）に、LibreOffice上の選択テキストを投げて要約させ、結果を文書に差し戻すスクリプトは、Python歴があれば数時間で書けます。

「ソフトに用意されたAI」を使うのではなく、「自分のインフラで動くAI」をドキュメントツールに接続する。この「主権」を取り戻す感覚こそが、今のエンジニアに求められるスキルセットです。

## 私の見解

私は今回のLibreOfficeの判断を全面的に支持します。RTX 4090を2枚挿してローカルLLMを常用している立場から言わせてもらえば、アプリ側に「中途半端なAI機能」を押し付けられるほど迷惑なことはありません。多くの場合、それはUIを複雑にし、動作を重くし、何よりユーザーのデータを吸い上げるための口実でしかないからです。

世の中のAIブロガーたちは「AIを搭載しないなんて時代遅れだ」と騒ぐかもしれませんが、それは表面的な見方です。真の実務者は、ツールが「勝手なことをしない」という信頼性を最も重視します。AIが嘘をつく（ハルシネーション）リスクがある以上、正確性が求められるドキュメント作成ツールにおいて、AIはあくまで「外部のアシスタント」であるべきで、心臓部に組み込むべきではありません。

もしあなたが、自分の文書がLLMの学習データに使われることに1ミリでも不安を感じるのであれば、今すぐMicrosoft 365を解約してLibreOffice 24.8に移行することを検討すべきです。その浮いた月額30ドルを貯めて、VRAMの大きなGPUを買い、自分の手元でローカルLLMを動かす方が、エンジニアとしての自由度と安全性は遥かに高まります。

## よくある質問

### Q1: AIがないと文書作成の効率が落ちるのではないでしょうか？

AIが必要な時は、ブラウザでClaudeやGPT-4oを開いて、必要な部分だけをコピペして加工すれば十分です。常にオフィスソフトがクラウドと通信し、全ての入力を監視している状態よりも、手動で制御できる方がセキュリティ的には遥かに健全です。

### Q2: Microsoft Officeとの互換性は本当に大丈夫ですか？

LibreOffice 24.8ではOOXML互換性が大幅に向上しており、複雑なレイアウトのExcelやWordファイルも以前より正確に開けるようになっています。完璧ではありませんが、社内文書のやり取りであれば実用レベルに達しています。

### Q3: 今後LibreOfficeにAIが搭載される可能性はありますか？

TDFはAIそのものを否定しているわけではなく、プライバシーを担保した形での実装を模索しています。将来的には、ユーザーのローカル環境で完結するオンデバイスAIとの連携機能が、標準ではなく「オプション」として追加される可能性は高いでしょう。

---

## あわせて読みたい

- [Claude Code用Macおすすめ構成と比較！予備機をAIコーディング専用機にする選び方](/posts/2026-07-19-claude-code-mac-setup-guide/)
- [ローカルLLM環境の選び方と比較：RTX 4090かMacか？失敗しないGPU・メモリ選び](/posts/2026-07-28-local-llm-gpu-buying-guide-rtx-mac/)
- [MTPLXで変わるMac選び｜ローカルLLMが3倍速くなる時代のApple Siliconおすすめ構成と失敗しない買い方](/posts/2026-08-20-mtplx-mlx-apple-silicon-high-speed-llm/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "AIがないと文書作成の効率が落ちるのではないでしょうか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AIが必要な時は、ブラウザでClaudeやGPT-4oを開いて、必要な部分だけをコピペして加工すれば十分です。常にオフィスソフトがクラウドと通信し、全ての入力を監視している状態よりも、手動で制御できる方がセキュリティ的には遥かに健全です。"
      }
    },
    {
      "@type": "Question",
      "name": "Microsoft Officeとの互換性は本当に大丈夫ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "LibreOffice 24.8ではOOXML互換性が大幅に向上しており、複雑なレイアウトのExcelやWordファイルも以前より正確に開けるようになっています。完璧ではありませんが、社内文書のやり取りであれば実用レベルに達しています。"
      }
    },
    {
      "@type": "Question",
      "name": "今後LibreOfficeにAIが搭載される可能性はありますか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "TDFはAIそのものを否定しているわけではなく、プライバシーを担保した形での実装を模索しています。将来的には、ユーザーのローカル環境で完結するオンデバイスAIとの連携機能が、標準ではなく「オプション」として追加される可能性は高いでしょう。 ---"
      }
    }
  ]
}
</script>

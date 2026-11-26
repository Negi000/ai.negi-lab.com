---
title: "OpenAIの数学研究報告を読む：未解決問題100件超と、公開証明の検証"
date: 2026-11-27T00:00:00+09:00
slug: "openai-internal-model-solves-unsolved-math-problems"
description: "OpenAIが2026年9月に報告した数学研究について、発表時点の主張、10月に公開された原稿、Leanで検証できる範囲を整理します。"
cover:
  image: "/images/posts/2026-11-27-openai-internal-model-solves-unsolved-math-problems.jpg"
  alt: "数学研究をテーマにしたイメージ"
  relative: false
categories:
  - "AI News"
tags:
  - "OpenAI"
  - "数学未解決問題"
  - "Lean"
  - "形式検証"
---
OpenAIは2026年9月21日、名称を公表していない内部モデルが、長年未解決だった数学の問題を100件超解いたと[発表しました](https://openai.com/index/advisory-group-on-mathematics-and-ai/)。この件数はOpenAIの報告です。発表を読む際は、発表時点での主張と、個々の証明について後から確認できる検証状況を分ける必要があります。

## 何が公開されたのか

OpenAIは[10月6日の研究公開](https://openai.com/index/sharing-ai-progress-in-mathematics/)で原稿を公開し、多くの証明についてLeanによる形式化も共有しました。[研究リポジトリ](https://github.com/openai/math)では原稿や証明ファイルを確認できます。検証の段階は成果ごとに異なり、[変更履歴](https://github.com/openai/math/blob/main/history.md)には訂正や撤回も記録されています。たとえば10月7日の記録では、符号の誤りが影響した原稿3本の撤回理由を確認できます。

## Leanが確かめること

Leanで検査できるのは、形式化された前提と定義のもとで、その証明が形式化された命題を導いているかどうかです。元の問題を正しく形式化したか、必要な仮定が抜けていないか、何を新しく示したのかは、証明が通ることとは別に確認する必要があります。原稿に形式化が付いていることから、モデル内部で常にLeanを使っているともいえません。

## 開発者が持ち帰れること

役立つのは「AIの結論を、そのまま採用せずに検査できる形にする」という考え方です。たとえば注文キャンセルの処理なら、「同じ返金要求を再送しても二重返金しない」と先に条件を決め、レビューで仕様と実装を照合し、再送や同時実行のテストを用意します。AIはテスト候補や反例を出す補助に使えますが、今回の数学研究から業務コードのバグ検出率は分かりません。内部モデルの市販モデルとの対応や、API提供の時期も、ここで参照した資料では確認できません。

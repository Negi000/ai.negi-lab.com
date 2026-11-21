---
title: "Claude Fable 5.2で作った短編『FABLE』の制作工程"
date: 2026-11-22T00:00:00+09:00
slug: "claude-3-5-fable-ai-hardware-guide-vram"
description: "短編『FABLE』の制作記録から、Claude Fable 5.2と画像・動画・音楽ツールの役割分担、そして人の試聴で映像を撮り直した経緯を紹介します。"
cover:
  image: "/images/posts/2026-11-22-claude-3-5-fable-ai-hardware-guide-vram.jpg"
  alt: "記事用のAI生成イメージ"
  relative: false
tags:
  - "Claude Fable 5.2"
  - "AI映像制作"
  - "生成AI"
---

Claudia Galleryの[短編『FABLE』](https://claudia.gallery/fable/)は、飛び出す絵本を舞台にした約4分のミュージックビデオです。[制作記録](https://claudia.gallery/record/fable/readme/)によると、制作を取りまとめたのはクラウドサーバー上のClaude Codeで動く**Claude Fable 5.2**。画像・動画・音楽は用途ごとに別のツールを使っています。

## 13枚の舞台原画から映像へ

最初に舞台のデザインを13枚のSVG原画に落とし込み、GPT Image 2.6 Sunburstで卓上の絵本と等身大の舞台セットに展開。Seedance 2.5でそれらを映像化し、一部の影絵はコードで描いて動かしています。曲はSunoで制作しました。単に動画の指示文を1本書くのではなく、舞台の設計を共通の原画にそろえ、そこから画面ごとの素材を作っています。

## 一度書き出した映像を、別の曲で作り直した

初版では、Claudeが音を聴かずに選んだテイクに合わせて編集していました。制作記録によると、企画を依頼したanabologyが初版を試聴して別テイクを選び、歌声に合わせる必要のあるカットは撮り直されました。工程を自動化しても、結果を実際に聴いて判断する工程が制作を左右した例です。

この事例は**クラウドで制作を組み立てた記録**であり、手元のGPUやMacの購入条件を示すものではありません。Claude Code自体の動作要件は[公式ドキュメント](https://code.claude.com/docs/en/setup#system-requirements)で確認できます。

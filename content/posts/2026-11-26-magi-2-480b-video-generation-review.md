---
title: "MAGI-2の使い方と料金：Sand AI公式APIと114B Previewの違い"
date: 2026-11-26T00:00:00+09:00
slug: "magi-2-480b-video-generation-review"
description: "Sand AIの動画生成モデルMAGI-2の公開仕様、1080p出力のAPI料金、別公開の114B Previewとの違いを公式資料から整理します。"
cover:
  image: "/images/og-default.png"
  alt: "Negi AI Lab"
  relative: false
categories:
  - "AI Tools"
tags:
  - "MAGI-2 使い方"
  - "Sand AI"
  - "480B モデル"
  - "動画生成AI"
---

Sand AIが2026年11月24日に発表したMAGI-2は、テキストや参照素材から音声付きの動画を生成するモデルです。ここでは公式発表とAPI資料をもとに、何が使えて、最初の1本にいくらかかるかを整理します。編集部による生成テストや他製品との比較は行っていません。

## 480B版と114B Previewの違い

| 項目 | 公式発表・資料で確認できる内容 |
| --- | --- |
| MAGI-2 | 総パラメータ480B、推論時に有効なパラメータは約28B。公式発表では音声付きで最長30秒、1080p・25fps |
| MAGI-2 Preview | 別途公開された研究版。総パラメータ約114B、有効パラメータ約6B |
| ホスト型APIの掲載料金 | 1080p出力1秒あたり0.08米ドル。5秒なら0.40米ドル |

出典：[MAGI-2の公式発表](https://sand.ai/blog/magi-2)、[Previewの公式リポジトリ](https://github.com/SandAI-org/MAGI-2-preview)、[公式料金表](https://platform.sand.ai/docs/model-pricing/)。

Previewのダウンロード手順や必要環境は、480B版のローカル動作を保証するものではありません。ホスト型APIの呼び出しに生成用GPUは不要です。

## 公式APIで最初の動画を作る

1. Sand AIのコンソールでAPIキーを発行し、サーバー側の環境変数 `SAND_API_KEY` に設定します。公開するフロントエンドにはキーを入れません。
2. [公式Quickstart](https://platform.sand.ai/docs/get-started/) のテキスト生成例を使い、`POST /v2/generations` に利用可能なモデル `magi-2`、プロンプト、秒数、アスペクト比を渡します。まずは例と同じ5秒・16:9なら、長尺を作る前に仕上がりを判断できます。
3. 返された生成IDで状態を確認します。成功後は `output.videoUrl` から動画を取得します。ダウンロード先にAPIキーは送信しません。

画像・動画・音声を参考素材に指定する場合は [生成APIの仕様](https://platform.sand.ai/docs/create-generation/) を参照してください。開始・終了フレームの指定については、同資料から案内されているArk互換APIを確認してください。

## 料金と商用案件での注意

[公式料金表](https://platform.sand.ai/docs/model-pricing/) の単価を掛けると、1080pの5秒は0.40米ドル、10秒は0.80米ドルです。同ページでは、確認時点で残高チャージは未対応と案内されていました。APIを利用できるかは、事前に自分のアカウントで確認してください。

生成リクエストの応答を受け取れなかった場合、同じリクエストを送っても既存の処理を再開するわけではありません。別の課金対象ジョブが作られることがあるので、自動で再送する前に [公式APIの注意事項](https://platform.sand.ai/docs/create-generation/) を確認してください。

商用案件では、ホスト型サービスの利用条件に加え、参照画像・音声などの素材をその用途に使えるかも確認してください。費用を支払っただけで、あらゆる素材・出力を商用利用できるとは限りません。

> 訂正（2026年11月26日）：初版に掲載した未確認のSDK、月額料金、必要機材、実使用に基づくように読める記述、および商用利用条件の断定を取り下げ、公式資料に基づく説明に変更しました。

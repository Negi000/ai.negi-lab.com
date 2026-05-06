#!/usr/bin/env python3
"""
Negi AI Lab - Auto Article Generator
=====================================
AIトレンド特化型の全自動ニュースサイト記事生成エンジン

カテゴリー構成比率（2026-05 収益重視へ再設計）:
    - MONEY (購買・比較・収益記事): 最優先
    - GUIDE (ローカルLLM/AI開発の実践ガイド): SEO資産
    - TOOL (AI開発ツール検証): 準収益記事
    - NEWS (速報): 話題化・内部リンク用に限定

フォールバック機能により、ネタ不足時は次カテゴリーで補填し、
必ず指定された合計記事数を確保する。

Usage:
  python auto_generate.py --dry-run          # シミュレーションのみ
  python auto_generate.py --test-one         # 1件だけ生成してテスト
  python auto_generate.py --total 10         # 10記事生成
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

import feedparser
import requests
from bs4 import BeautifulSoup

import google.generativeai as genai

# Twitter投稿用 (オプション)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

# Optional: load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ============================================================
# Constants & Configuration
# ============================================================

JST = timezone(timedelta(hours=9))
SLEEP_SECONDS_PER_ARTICLE = 30
DEFAULT_TOTAL_ARTICLES = 1  # 量産より収益意図と品質を優先
SITE_BASE_URL = "https://ai.negi-lab.com"

# 日次リセット時刻（JST 02:00 = 海外速報をキャッチしやすい時間）
DAILY_RESET_HOUR = 2

# 1日の目標記事数（カテゴリー別）
# 月3万円の収益化を優先し、NEWS量産から購買意図の強いMONEY/GUIDEへ寄せる。
DAILY_TARGETS = {
    "MONEY": 2,  # 楽天/Amazon導線のある比較・購入前ガイド
    "GUIDE": 2,  # ローカルLLM/AI開発のSEOロングテール資産
    "TOOL": 2,   # AI開発ツールの実務レビュー
    "NEWS": 1,   # 話題化・内部リンク用。収益記事へ送客する燃料
}

# ============================================================
# Persona Configuration（ペルソナ設定）
# ============================================================

PERSONA = {
    "name": "ねぎ",
    "role": "AI専門ブロガー",
    "tone": "技術に深い理解を持ちながらも、実務者として地に足のついた語り口。一人称は「私」。",
    "background": """
        元SIerエンジニア（5年）→ フリーランス → AI専門ブロガー。
        Python歴8年、機械学習案件を20件以上こなした実務経験者。
        GPT-4が出た日に全APIドキュメントを読破し、Claude 3発表時は3時間で比較ベンチマーク記事を書いた。
        「動かしてみた」ではなく「仕事で使えるか」を常に基準にしている。
        趣味はローカルLLMの検証と自宅サーバー構築。RTX 4090を2枚挿しで運用中。
    """,
    "writing_style": """
        - 結論ファースト: 最初の3行で「この記事の核心」を伝える
        - 体験ベース: 「〜らしい」ではなく「試した結果」「使った感想」で語る
        - 数字で語る: 「速い」→「レスポンス0.3秒」、「安い」→「月額$20」
        - 本音を書く: 良い点だけでなく「ここが微妙」も正直に
        - 柔らかい語尾: 「〜ですね」「〜だと思います」は使うが、「〜です！」の過剰な勢いは避ける
        - 1段落2〜3文: スマホで読みやすく
        - 定型文禁止: 「いかがでしたか」「みなさんこんにちは」「〜ではないでしょうか」は一切使わない
        - 独自の切り口: 他のサイトと同じことを書くなら書かない。自分だけの視点を入れる
    """,
    "twitter_style": """
        - 感情を込めた一言から始める
        - 絵文字を2-3個使う
        - 「〜かも」「〜だった」など体験談風に
        - フォロワーに問いかける（「みなさんはどう思います？」）
    """,
}

# ニッチなハッシュタグ（CSV分析結果に基づき最適化）
# ※Categoryクラス定義前なので文字列キーで定義
# 選定基準：実績データで平均imp60以上のタグを優先
# 低パフォーマー削除: #DX推進(22), #エンジニアと繋がりたい(17), #スタートアップ(24)
NICHE_HASHTAGS_STR = {
    "MONEY": [
        "#ローカルLLM",
        "#個人開発",
        "#エンジニア",
        "#業務効率化",
        "#生産性向上",
        "#機械学習",
        "#リモートワーク",
    ],
    "NEWS": [
        "#AppleIntelligence",  # 平均imp=91
        "#機械学習",            # 平均imp=84
        "#ローカルLLM",         # 平均imp=77
        "#自律型AI",            # 平均imp=66
        "#リモートワーク",      # 平均imp=60
        "#Web3",               # 平均imp=55
        "#今日の積み上げ",      # 平均imp=52
        "#朝活",               # 平均imp=52
    ],
    "TOOL": [
        "#ローカルLLM",         # 平均imp=77
        "#リモートワーク",      # 平均imp=60
        "#業務効率化",          # 平均imp=53
        "#今日の積み上げ",      # 平均imp=52
        "#フリーランス",        # 平均imp=51
        "#便利ツール",          # 平均imp=49
        "#朝活",               # 平均imp=52
        "#副業",               # 平均imp=37
    ],
    "GUIDE": [
        "#機械学習",            # 平均imp=84
        "#ローカルLLM",         # 平均imp=77
        "#今日の積み上げ",      # 平均imp=52
        "#プログラミング",      # 平均imp=37
        "#生産性向上",          # 平均imp=35
        "#朝活",               # 平均imp=52
        "#リモートワーク",      # 平均imp=60
        "#業務効率化",          # 平均imp=53
    ],
}

# 固定タグ（補完用。URL直貼りだけの投稿を避け、最大2個に抑える）
# 実績: #個人開発/#エンジニア/#ローカルLLM が高相性
FIXED_HASHTAGS = ["#個人開発", "#エンジニア"]

# ============================================================
# 一次情報源 RSS フィード（ホットな話題を取得）
# ============================================================

# AI/Tech 一次情報源（英語・高品質）
PRIMARY_NEWS_FEEDS = [
    # 大手テックメディア（速報性・信頼性高い）
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch AI", "priority": 1},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "name": "The Verge AI", "priority": 1},
    {"url": "https://venturebeat.com/category/ai/feed/", "name": "VentureBeat AI", "priority": 1},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss", "name": "Wired AI", "priority": 2},
    {"url": "https://arstechnica.com/tag/artificial-intelligence/feed/", "name": "Ars Technica AI", "priority": 2},
    
    # 公式ブログ（一次情報）
    {"url": "https://openai.com/blog/rss/", "name": "OpenAI Blog", "priority": 1},
    {"url": "https://www.anthropic.com/feed.xml", "name": "Anthropic Blog", "priority": 1},
    {"url": "https://blog.google/technology/ai/rss/", "name": "Google AI Blog", "priority": 1},
    {"url": "https://ai.meta.com/blog/rss/", "name": "Meta AI Blog", "priority": 1},
    
    # 技術系（深掘り記事）
    {"url": "https://www.technologyreview.com/feed/", "name": "MIT Tech Review", "priority": 2},
]

# Hacker News（話題性・コミュニティ反応）
HACKER_NEWS_FEEDS = [
    {"url": "https://hnrss.org/newest?q=GPT+OR+LLM+OR+Claude+OR+Gemini&points=50", "name": "HN AI Hot", "min_points": 50},
    {"url": "https://hnrss.org/newest?q=OpenAI+OR+Anthropic+OR+AI+agent&points=30", "name": "HN AI Companies", "min_points": 30},
    {"url": "https://hnrss.org/newest?q=Ollama+OR+llama.cpp+OR+local+LLM+OR+MLX&points=20", "name": "HN Local AI", "min_points": 20},
    {"url": "https://hnrss.org/newest?q=Claude+Code+OR+Cursor+OR+Aider+OR+agentic+engineering&points=20", "name": "HN AI Coding", "min_points": 20},
]

# Reddit（トレンド・コミュニティ）
REDDIT_FEEDS = [
    {"url": "https://www.reddit.com/r/MachineLearning/hot/.rss", "name": "r/MachineLearning", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/artificial/hot/.rss", "name": "r/artificial", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/hot/.rss", "name": "r/LocalLLaMA", "category": "GUIDE"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week", "name": "r/LocalLLaMA Weekly", "category": "MONEY"},
    {"url": "https://www.reddit.com/r/ollama/hot/.rss", "name": "r/ollama", "category": "MONEY"},
    {"url": "https://www.reddit.com/r/LocalLLM/hot/.rss", "name": "r/LocalLLM", "category": "MONEY"},
    {"url": "https://www.reddit.com/r/ChatGPT/hot/.rss", "name": "r/ChatGPT", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/singularity/hot/.rss", "name": "r/singularity", "category": "NEWS"},
]

# プレスリリース系を除外するキーワード
PRESS_RELEASE_KEYWORDS = [
    "プレスリリース", "press release", "PR TIMES", "PRNewswire",
    "発表しました", "を開始", "を発売", "を提供開始",
    "ニフティニュース", "VOI.id", "excite.co.jp",
]

# 収益化・検索意図が強いテーマ。自前CSV（ローカルLLM/RTXが高CTR）と
# GitHub Trending/HNで強いAI Agent・AI Coding・オンデバイスAIを合わせて採用。
REVENUE_INTENT_KEYWORDS = [
    "local llm", "ローカルllm", "ollama", "llama.cpp", "mlx", "gguf", "qwen", "gemma",
    "vram", "rtx", "gpu", "nvidia", "apple silicon", "macbook", "mac studio", "m5", "m4",
    "claude code", "cursor", "aider", "cline", "github copilot", "ai coding", "agentic engineering",
    "ai agent", "agent", "rag", "vector database", "embedding", "音声認識", "tts", "video ai",
    "料金", "価格", "月額", "無料", "比較", "おすすめ", "レビュー", "使い方", "導入", "構築",
]

LOW_REVENUE_NEWS_KEYWORDS = [
    "funding", "資金調達", "raises", "raised", "ipo", "買収", "acquisition",
    "lawsuit", "訴訟", "regulation", "規制", "policy", "人事", "ceo", "politics",
]

# 時間帯別優先度（JST時刻 → 優先カテゴリーリスト）
# 深夜2時: 海外速報キャッチでNEWS最優先
# 朝8時: 通勤時間、NEWS + TOOL
# 昼12時: 昼休み、TOOL中心
# 午後15時: TOOL + NEWS
# 夕方18時: 帰宅時間、NEWS + TOOL
# 夜21時: じっくり読むGUIDE
TIME_SLOT_PRIORITIES = {
    2:  ["MONEY", "GUIDE", "TOOL", "NEWS"],  # 海外トレンドを収益記事へ変換
    8:  ["MONEY", "GUIDE", "TOOL", "NEWS"],  # 朝は保存される実用記事
    12: ["TOOL", "MONEY", "GUIDE", "NEWS"],  # 昼はツール・比較
    15: ["GUIDE", "MONEY", "TOOL", "NEWS"],  # 午後はHow-to
    18: ["MONEY", "TOOL", "GUIDE", "NEWS"],  # 帰宅時間は購買/比較導線
    21: ["GUIDE", "MONEY", "TOOL", "NEWS"],  # 夜はじっくり読む導入記事
}

# ネタプールの保持期間（日数）
POOL_RETENTION_DAYS = 7

# アフィリエイト設定
AMAZON_ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "negi3939-22")
RAKUTEN_AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "5000cbfd.5f52567b.5000cbff.924460a4")

# ============================================================
# アフィリエイト商品マッピングDB
# キーワード検出 → おすすめ商品カテゴリーへマッピング
# 
# ★改善方針★
# - 書籍よりガジェット・ハードウェアを優先（単価高い＆購入率高い）
# - 具体的な商品名（ブランド＋型番）で検索されやすく
# - 「すぐ使いたい」欲求に応える実用品
# ============================================================

PRODUCT_MAPPINGS = {
    # GPU関連 - 高単価で需要あり
    "gpu": {
        "keywords": ["gpu", "グラフィックボード", "vram", "cuda", "nvidia", "rtx", "geforce", "グラボ"],
        "products": [
            {"name": "MSI RTX 4070 SUPER", "search": "MSI RTX 4070 SUPER GAMING X SLIM", "desc": "12GB VRAM・静音設計で人気No.1"},
            {"name": "玄人志向 RTX 4060 Ti", "search": "玄人志向 RTX 4060 Ti 8GB", "desc": "コスパ最強・入門に最適"},
        ],
        "category": "グラフィックボード"
    },
    # ローカルLLM関連 - ミニPC需要高い
    "local_llm": {
        "keywords": ["ollama", "llama", "ローカルllm", "local llm", "llama.cpp", "gguf", "量子化", "qwen", "gemma", "mlx"],
        "products": [
            {"name": "MINISFORUM UM790 Pro", "search": "MINISFORUM UM790 Pro 64GB", "desc": "省スペースでOllama検証を始めやすい"},
            {"name": "RTX 4060 Ti 16GB", "search": "RTX 4060 Ti 16GB", "desc": "VRAM 16GBで9B〜14B級LLMの入門に現実的"},
        ],
        "category": "ミニPC"
    },
    # Apple Silicon/MLX - ローカルAI需要が強い
    "apple_silicon": {
        "keywords": ["apple silicon", "mlx", "macbook", "mac studio", "m4", "m5", "unified memory", "統一メモリ"],
        "products": [
            {"name": "Mac mini 32GB", "search": "Mac mini 32GB Apple Silicon", "desc": "MLX/Ollama入門に扱いやすい省電力Mac"},
            {"name": "MacBook Pro 36GB", "search": "MacBook Pro 36GB", "desc": "外出先でもローカルAI検証を回しやすい"},
        ],
        "category": "Apple Silicon"
    },
    # Python/プログラミング - 周辺機器が売れる
    "python": {
        "keywords": ["python", "パイソン", "pytorch", "tensorflow", "jupyter", "notebook", "コード"],
        "products": [
            {"name": "HHKB Professional", "search": "HHKB Professional HYBRID", "desc": "プログラマー御用達の最高峰キーボード"},
            {"name": "Logicool MX Keys", "search": "Logicool MX Keys S", "desc": "静音・マルチデバイス対応"},
        ],
        "category": "キーボード"
    },
    # ChatGPT/API関連 - 効率化ガジェット
    "chatgpt": {
        "keywords": ["chatgpt", "gpt-4", "gpt-5", "openai", "api", "プロンプト", "claude"],
        "products": [
            {"name": "Stream Deck MK.2", "search": "Elgato Stream Deck MK.2", "desc": "プロンプト呼び出しをワンボタン化"},
            {"name": "Dell 4Kモニター", "search": "Dell U2723QE 27インチ 4K", "desc": "長文作業に最適・USB-C給電"},
        ],
        "category": "効率化ガジェット"
    },
    # 画像生成AI - GPU需要
    "image_ai": {
        "keywords": ["stable diffusion", "midjourney", "dall-e", "画像生成", "comfyui", "automatic1111"],
        "products": [
            {"name": "ASUS RTX 4070 Ti SUPER", "search": "ASUS TUF RTX 4070 Ti SUPER", "desc": "16GB VRAM・SDXL余裕"},
            {"name": "ペンタブレット", "search": "Wacom Intuos Pro Medium", "desc": "AI絵の修正・仕上げに"},
        ],
        "category": "クリエイター向け"
    },
    # 音声AI - マイク需要
    "voice_ai": {
        "keywords": ["whisper", "音声認識", "tts", "音声合成", "voicevox", "elevenlabs", "文字起こし"],
        "products": [
            {"name": "SHURE MV7+", "search": "SHURE MV7+ USB マイク", "desc": "プロ音質・ノイキャン内蔵"},
            {"name": "Sony WH-1000XM5", "search": "Sony WH-1000XM5", "desc": "最強ノイキャン・長時間作業向け"},
        ],
        "category": "音声機材"
    },
    # RAG/ベクトルDB - 開発PC
    "rag": {
        "keywords": ["rag", "ベクトル", "embedding", "pinecone", "chromadb", "langchain"],
        "products": [
            {"name": "MacBook Air M3", "search": "MacBook Air M3 16GB", "desc": "RAG開発にはメモリ16GB必須"},
            {"name": "外付けSSD", "search": "Samsung T7 Shield 2TB", "desc": "ベクトルDB保存に高速SSD"},
        ],
        "category": "開発PC"
    },
    # エージェント/自動化 - 作業効率化
    "agent": {
        "keywords": ["agent", "エージェント", "autogpt", "crew", "自動化", "ワークフロー", "mcp", "claude code", "cursor", "aider", "cline"],
        "products": [
            {"name": "Logicool MX Master 3S", "search": "Logicool MX Master 3S", "desc": "ジェスチャー＋静音・作業効率UP"},
            {"name": "ウルトラワイドモニター", "search": "LG 34WQ75C-B 34インチ", "desc": "マルチウィンドウ作業が捗る"},
        ],
        "category": "効率化ガジェット"
    },
    # AIコーディング/開発環境 - 保存・比較・購入意図が強い
    "ai_coding": {
        "keywords": ["claude code", "cursor", "github copilot", "aider", "cline", "devin", "ai coding", "コーディングエージェント"],
        "products": [
            {"name": "Dell U2723QE", "search": "Dell U2723QE 27インチ 4K", "desc": "AIレビューとコードを並べるなら4Kが効く"},
            {"name": "HHKB Type-S", "search": "HHKB Professional HYBRID Type-S", "desc": "長時間のAIコーディング作業に向く定番"},
        ],
        "category": "AI開発環境"
    },
    # AI動画/音声 - クリエイター・副業導線
    "ai_media": {
        "keywords": ["動画生成", "video ai", "sora", "runway", "pika", "pixverse", "音声合成", "tts", "文字起こし", "whisper"],
        "products": [
            {"name": "SHURE MV7+", "search": "SHURE MV7+ USB マイク", "desc": "音声AI/収録/文字起こしの入力品質を上げる"},
            {"name": "Samsung T7 Shield", "search": "Samsung T7 Shield 2TB", "desc": "動画生成素材と出力の保存先に高速SSD"},
        ],
        "category": "AIメディア制作"
    },
    # クラウド/インフラ - サーバー機材
    "cloud": {
        "keywords": ["aws", "azure", "gcp", "クラウド", "サーバー", "デプロイ", "docker", "kubernetes"],
        "products": [
            {"name": "Raspberry Pi 5", "search": "Raspberry Pi 5 8GB スターターキット", "desc": "自宅サーバー入門に最適"},
            {"name": "Synology NAS", "search": "Synology DS224+ NAS", "desc": "Docker対応・自宅クラウド構築"},
        ],
        "category": "サーバー機材"
    },
    # 開発環境/IDE - 周辺機器
    "dev_env": {
        "keywords": ["vscode", "cursor", "ide", "エディタ", "開発環境", "github", "copilot"],
        "products": [
            {"name": "BenQ ScreenBar", "search": "BenQ ScreenBar Halo", "desc": "目の疲れ軽減・デスクライト"},
            {"name": "エルゴノミクスチェア", "search": "エルゴヒューマン プロ", "desc": "長時間コーディングに"},
        ],
        "category": "デスク環境"
    },
    # スマホ/アプリ - モバイル
    "mobile": {
        "keywords": ["iphone", "android", "アプリ", "スマホ", "モバイル", "ios"],
        "products": [
            {"name": "iPhone 15 Pro", "search": "iPhone 15 Pro 256GB", "desc": "AI機能フル搭載・開発テスト用に"},
            {"name": "Ankerモバイルバッテリー", "search": "Anker 737 Power Bank", "desc": "24000mAh・MacBook充電可"},
        ],
        "category": "モバイル"
    },
    # デフォルト（AI全般）- 人気ガジェット
    "default": {
        "keywords": [],
        "products": [
            {"name": "Logicool MX Master 3S", "search": "Logicool MX Master 3S", "desc": "エンジニア人気No.1マウス"},
            {"name": "HHKB Professional", "search": "HHKB Professional HYBRID Type-S", "desc": "最高の打鍵感・一生モノ"},
        ],
        "category": "人気ガジェット"
    },
}

# User-Agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class Category(Enum):
    MONEY = "MONEY"
    NEWS = "NEWS"
    TOOL = "TOOL"
    GUIDE = "GUIDE"


def get_daily_date() -> str:
    """日次リセット境界（02:00 JST）を考慮した"今日"の日付を返す"""
    now = datetime.now(JST)
    # 02:00より前なら前日扱い
    if now.hour < DAILY_RESET_HOUR:
        now = now - timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def get_current_priority() -> List[Category]:
    """現在時刻に基づいたカテゴリー優先度を返す"""
    hour = datetime.now(JST).hour
    # 最も近い時間帯を探す
    slots = sorted(TIME_SLOT_PRIORITIES.keys())
    for i, slot in enumerate(slots):
        next_slot = slots[(i + 1) % len(slots)]
        if slot <= hour < next_slot or (next_slot < slot and (hour >= slot or hour < next_slot)):
            priority_strs = TIME_SLOT_PRIORITIES[slot]
            priority = [Category(s) for s in priority_strs]
            return priority + [cat for cat in Category if cat not in priority]
    priority_strs = TIME_SLOT_PRIORITIES[slots[0]]
    priority = [Category(s) for s in priority_strs]
    return priority + [cat for cat in Category if cat not in priority]


@dataclass
class NewsItem:
    """収集したニュースアイテム"""
    source: str
    title: str
    url: str
    category: Category
    published: str = ""
    summary: str = ""
    extra: Dict = field(default_factory=dict)
    # プール用の追加フィールド
    collected_at: str = ""  # 収集日時
    possible_categories: List[str] = field(default_factory=list)  # 適用可能なカテゴリー


# ============================================================
# Processed URLs Store
# ============================================================

class ProcessedURLStore:
    """重複防止用のURL永続化ストア"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._urls: List[str] = []
        self._dirty = False

    def load(self) -> List[str]:
        if not self.path.exists():
            self._urls = []
            return self._urls
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._urls = [str(x) for x in data] if isinstance(data, list) else []
        except Exception:
            self._urls = []
        return self._urls

    def contains(self, url: str) -> bool:
        if not self._urls:
            self.load()
        return url in self._urls

    def add(self, url: str) -> None:
        if not self._urls:
            self.load()
        if url not in self._urls:
            self._urls.append(url)
            self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._urls, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._dirty = False


class DailyStatsStore:
    """1日のカテゴリー別生成数を追跡するストア（02:00 JSTでリセット）"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: Dict = {}
        self._dirty = False

    def load(self) -> Dict:
        if not self.path.exists():
            self._data = self._new_day_data()
            return self._data
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
            # 日次リセット境界（02:00 JST）を考慮した日付比較
            today = get_daily_date()
            if self._data.get("date") != today:
                print(f"  [INFO] New day detected (reset at 02:00 JST), resetting daily stats")
                self._data = self._new_day_data()
                self._dirty = True
            else:
                # カテゴリー構成変更（MONEY追加など）に追従
                self._data.setdefault("generated", {})
                self._data.setdefault("targets", {})
                for cat, target in DAILY_TARGETS.items():
                    if cat not in self._data["generated"]:
                        self._data["generated"][cat] = 0
                        self._dirty = True
                    if self._data["targets"].get(cat) != target:
                        self._data["targets"][cat] = target
                        self._dirty = True
        except Exception:
            self._data = self._new_day_data()
        return self._data

    def _new_day_data(self) -> Dict:
        return {
            "date": get_daily_date(),
            "generated": {cat: 0 for cat in DAILY_TARGETS},
            "targets": DAILY_TARGETS.copy(),
        }

    def get_remaining(self) -> Dict[str, int]:
        """各カテゴリーの残り枠を取得"""
        if not self._data:
            self.load()
        remaining = {}
        for cat in DAILY_TARGETS:
            target = self._data["targets"].get(cat, 0)
            generated = self._data["generated"].get(cat, 0)
            remaining[cat] = max(0, target - generated)
        return remaining

    def increment(self, category: str) -> None:
        """カテゴリーの生成数を+1"""
        if not self._data:
            self.load()
        self._data.setdefault("generated", {})
        self._data["generated"].setdefault(category, 0)
        self._data["generated"][category] += 1
        self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._dirty = False

    def get_stats_summary(self) -> str:
        """現在の状況をサマリー文字列で返す"""
        if not self._data:
            self.load()
        gen = self._data["generated"]
        tgt = self._data["targets"]
        return ", ".join(f"{cat} {gen.get(cat, 0)}/{tgt.get(cat, 0)}" for cat in DAILY_TARGETS)


# ============================================================
# News Pool (ネタストック機構)
# ============================================================

class NewsPool:
    """
    収集した記事をプールして、ネタ切れを防止する。
    
    - 各ソースから収集した記事をプールに保存
    - 記事は複数カテゴリーに適用可能（柔軟な振り分け）
    - 古い記事は自動的に期限切れ
    - 使用済みURLは別途 processed_urls.json で管理
    """

    def __init__(self, path: Path, processed_store: 'ProcessedURLStore') -> None:
        self.path = path
        self.processed_store = processed_store
        self._items: List[Dict] = []
        self._dirty = False

    def load(self) -> None:
        if not self.path.exists():
            self._items = []
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._items = data.get("items", [])
            # 期限切れと使用済みを除去
            self._cleanup()
        except Exception:
            self._items = []

    def _cleanup(self) -> None:
        """期限切れ・使用済みアイテムを削除"""
        cutoff = datetime.now(JST) - timedelta(days=POOL_RETENTION_DAYS)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
        
        original_count = len(self._items)
        self._items = [
            item for item in self._items
            if item.get("collected_at", "") >= cutoff_str
            and not self.processed_store.contains(item.get("url", ""))
        ]
        
        if len(self._items) < original_count:
            self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {"items": self._items, "updated_at": datetime.now(JST).isoformat()}
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._dirty = False

    def add(self, item: 'NewsItem') -> None:
        """新しいアイテムをプールに追加"""
        # 既にプールにあるか、使用済みならスキップ
        if self.processed_store.contains(item.url):
            return
        if any(x.get("url") == item.url for x in self._items):
            return
        
        # possible_categories を文字列リストに変換
        possible_cats = item.possible_categories or [item.category]
        possible_cats_str = [
            c.value if isinstance(c, Category) else str(c) 
            for c in possible_cats
        ]
        
        self._items.append({
            "source": item.source,
            "title": item.title,
            "url": item.url,
            "primary_category": item.category.value,
            "possible_categories": possible_cats_str,
            "published": item.published,
            "summary": item.summary,
            "extra": item.extra,
            "collected_at": datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S"),
        })
        self._dirty = True

    def get_items_for_category(
        self, 
        category: Category, 
        max_items: int = 10,
        fresh_first: bool = True
    ) -> List['NewsItem']:
        """
        指定カテゴリーに適用可能なアイテムを取得
        
        Args:
            category: 取得したいカテゴリー
            max_items: 最大取得数
            fresh_first: True=新しい順、False=古い順（在庫消化）
        """
        # カテゴリーに適用可能なアイテムをフィルタ
        candidates = [
            item for item in self._items
            if category.value in item.get("possible_categories", [])
            and not self.processed_store.contains(item.get("url", ""))
        ]
        
        # ソート（fresh_first=True: 新しい順、False: 古い順）
        candidates.sort(
            key=lambda x: x.get("collected_at", ""),
            reverse=fresh_first
        )
        
        # NewsItem に変換
        results = []
        for item in candidates[:max_items]:
            results.append(NewsItem(
                source=item.get("source", "Pool"),
                title=item.get("title", ""),
                url=item.get("url", ""),
                category=category,  # 指定されたカテゴリーで使用
                published=item.get("published", ""),
                summary=item.get("summary", ""),
                extra=item.get("extra", {}),
                collected_at=item.get("collected_at", ""),
                possible_categories=item.get("possible_categories", []),
            ))
        
        return results

    def get_pool_stats(self) -> Dict[str, int]:
        """プール内の各カテゴリーのアイテム数を返す"""
        stats = {cat.value: 0 for cat in Category}
        stats["total"] = len(self._items)
        for item in self._items:
            for cat in item.get("possible_categories", []):
                if cat in stats:
                    stats[cat] += 1
        return stats


# ============================================================
# News Collector
# ============================================================

class NewsCollector:
    """各ソースからニュースを収集するクラス（クロスカテゴリー対応）"""

    # カテゴリー判定用キーワード
    NEWS_KEYWORDS = [
        "発表", "リリース", "launch", "announce", "release", "update",
        "速報", "breaking", "ニュース", "news", "報道", "disclosed",
        "買収", "acquisition", "提携", "partnership", "funding", "調達",
        "規制", "regulation", "policy", "訴訟", "lawsuit",
    ]
    TOOL_KEYWORDS = [
        "ツール", "tool", "app", "アプリ", "サービス", "service",
        "プラットフォーム", "platform", "ソフトウェア", "software",
        "api", "sdk", "library", "framework", "plugin", "extension",
        "github", "repository", "open source", "オープンソース",
    ]
    GUIDE_KEYWORDS = [
        "使い方", "how to", "tutorial", "チュートリアル", "guide",
        "入門", "beginner", "解説", "explanation", "tips", "コツ",
        "比較", "comparison", "レビュー", "review", "まとめ",
        "ベストプラクティス", "best practice", "活用", "utilize",
    ]
    MONEY_KEYWORDS = [kw.lower() for kw in REVENUE_INTENT_KEYWORDS]

    def __init__(self, processed_store: ProcessedURLStore, pool: Optional[NewsPool] = None) -> None:
        self.processed_store = processed_store
        self.pool = pool  # ネタプールへの参照
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        # タイムアウトを長めに設定（GitHub Actions環境対応）
        self.timeout = 30

    def _is_fresh(self, url: str) -> bool:
        """URLが未処理かどうか"""
        return not self.processed_store.contains(url)

    def _fetch_with_retry(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """リトライ付きHTTPリクエスト"""
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except Exception as e:
                print(f"  [!] Attempt {attempt + 1}/{retries} failed for {url[:50]}...: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _detect_possible_categories(self, title: str, summary: str, source: str) -> List[str]:
        """
        タイトルと概要から適用可能なカテゴリーを判定。
        1つの記事が複数カテゴリーに適用可能な場合がある。
        """
        text = (title + " " + summary).lower()
        categories = []
        
        # ソースによるデフォルトカテゴリー
        source_defaults = {
            "Google News": "NEWS",
            "Product Hunt": "TOOL",
            "GitHub Trending": "TOOL",
            "Reddit": "GUIDE",
            "r/LocalLLaMA Weekly": "MONEY",
            "r/ollama": "MONEY",
            "r/LocalLLM": "MONEY",
        }
        
        # キーワードマッチでカテゴリー判定
        news_score = sum(1 for kw in self.NEWS_KEYWORDS if kw.lower() in text)
        tool_score = sum(1 for kw in self.TOOL_KEYWORDS if kw.lower() in text)
        guide_score = sum(1 for kw in self.GUIDE_KEYWORDS if kw.lower() in text)
        money_score = sum(1 for kw in self.MONEY_KEYWORDS if kw in text)
        
        # スコアが1以上ならカテゴリーに追加
        if money_score >= 1:
            categories.append("MONEY")
        if news_score >= 1:
            categories.append("NEWS")
        if tool_score >= 1:
            categories.append("TOOL")
        if guide_score >= 1:
            categories.append("GUIDE")
        
        # どのカテゴリーにもマッチしなければソースデフォルト
        if not categories:
            default = source_defaults.get(source, "NEWS")
            categories.append(default)
        
        return categories

    def _score_revenue_intent(self, title: str, summary: str = "", source: str = "") -> int:
        """購買・保存・検索意図が強いネタを優先するための簡易スコア。"""
        text = f"{title} {summary} {source}".lower()
        score = 0

        for keyword in REVENUE_INTENT_KEYWORDS:
            if keyword.lower() in text:
                score += 3

        for keyword in ["比較", "おすすめ", "選び方", "価格", "料金", "review", "benchmark", "setup", "install"]:
            if keyword.lower() in text:
                score += 2

        for keyword in LOW_REVENUE_NEWS_KEYWORDS:
            if keyword.lower() in text:
                score -= 2

        if "github" in source.lower() or "hacker news" in source.lower() or source.lower().startswith("hn "):
            score += 1
        if "localllama" in source.lower() or "ollama" in source.lower():
            score += 2

        return score

    def _rank_items(self, items: List[NewsItem], min_score: Optional[int] = None) -> List[NewsItem]:
        """重複を落とし、収益意図スコア順に並べ替える。"""
        deduped: List[NewsItem] = []
        seen: set[str] = set()
        for item in items:
            key = item.url or item.title.lower()
            if key in seen:
                continue
            seen.add(key)
            score = self._score_revenue_intent(item.title, item.summary, item.source)
            item.extra.setdefault("revenue_score", score)
            if min_score is not None and score < min_score:
                continue
            deduped.append(item)

        return sorted(deduped, key=lambda item: item.extra.get("revenue_score", 0), reverse=True)

    def _clone_for_category(self, item: NewsItem, category: Category) -> NewsItem:
        """同じ素材を別カテゴリの記事として使うためにカテゴリだけ差し替える。"""
        possible = list(item.possible_categories or [])
        if category.value not in possible:
            possible.insert(0, category.value)
        return NewsItem(
            source=item.source,
            title=item.title,
            url=item.url,
            category=category,
            published=item.published,
            summary=item.summary,
            extra=dict(item.extra),
            possible_categories=possible,
        )

    def _add_to_pool(self, item: NewsItem) -> None:
        """プールにアイテムを追加"""
        if self.pool:
            self.pool.add(item)

    # -------------------------
    # NEWS Sources
    # -------------------------

    def collect_news(self, max_items: int = 20) -> List[NewsItem]:
        """NEWS カテゴリー: 複数の一次情報源から収集"""
        items: List[NewsItem] = []
        
        # 1. 一次情報源RSSフィード（優先度高い）
        primary_items = self._collect_primary_feeds(max_items // 2)
        items.extend(primary_items)
        print(f"  [INFO] Primary feeds: {len(primary_items)} items")
        
        # 2. Hacker News（話題性の指標）
        hn_items = self._collect_hacker_news(max_items // 4)
        items.extend(hn_items)
        print(f"  [INFO] Hacker News: {len(hn_items)} items")
        
        # 3. Reddit AI関連（トレンド）
        reddit_items = self._collect_reddit_news(max_items // 4)
        items.extend(reddit_items)
        print(f"  [INFO] Reddit AI: {len(reddit_items)} items")
        
        # 4. Google News（補完、プレスリリース除外）
        if len(items) < max_items:
            google_items = self._collect_google_news_filtered(max_items - len(items))
            items.extend(google_items)
            print(f"  [INFO] Google News (filtered): {len(google_items)} items")
        
        items = self._rank_items(items)
        print(f"  [INFO] NEWS total: {len(items)} items")
        return items[:max_items]

    def _is_press_release(self, title: str, summary: str = "") -> bool:
        """プレスリリース系の低品質記事かどうか判定"""
        text = (title + " " + summary).lower()
        for keyword in PRESS_RELEASE_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False

    def _collect_primary_feeds(self, max_items: int) -> List[NewsItem]:
        """一次情報源（TechCrunch, The Verge等）からRSS収集"""
        results: List[NewsItem] = []
        
        # 優先度順にソート
        sorted_feeds = sorted(PRIMARY_NEWS_FEEDS, key=lambda x: x.get("priority", 99))
        
        for feed_info in sorted_feeds:
            if len(results) >= max_items:
                break
                
            url = feed_info["url"]
            name = feed_info["name"]
            
            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue
                
                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []
                
                for entry in entries[:5]:  # 各フィードから最大5件
                    if len(results) >= max_items:
                        break
                    
                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    summary = self._normalize_text(getattr(entry, "summary", "") or "")
                    
                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue
                    if self._is_press_release(title, summary):
                        continue
                    
                    possible_cats = self._detect_possible_categories(title, summary, name)
                    
                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.NEWS,
                        published=published,
                        summary=summary[:500],
                        possible_categories=possible_cats,
                    )
                    results.append(item)
                    self._add_to_pool(item)
                    
            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue
        
        return results

    def _collect_hacker_news(self, max_items: int) -> List[NewsItem]:
        """Hacker Newsから話題の記事を収集（points付きで品質フィルタ）"""
        results: List[NewsItem] = []
        
        for feed_info in HACKER_NEWS_FEEDS:
            if len(results) >= max_items:
                break
            
            url = feed_info["url"]
            name = feed_info["name"]
            
            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue
                
                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []
                
                for entry in entries[:10]:
                    if len(results) >= max_items:
                        break
                    
                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    
                    # HN RSSはコメントへのリンクを含むので、元記事URLを取得
                    # comments属性がある場合はそちらがHNリンク
                    if hasattr(entry, 'comments'):
                        entry_url = (getattr(entry, "link", "") or "").strip()
                    
                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue
                    
                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.NEWS,
                        published=published,
                        summary="",
                        possible_categories=self._detect_possible_categories(title, "", name),
                    )
                    results.append(item)
                    self._add_to_pool(item)
                    
            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue
        
        return results

    def _collect_reddit_news(self, max_items: int) -> List[NewsItem]:
        """Reddit AI関連サブレディットからホットな投稿を収集"""
        results: List[NewsItem] = []
        
        for feed_info in REDDIT_FEEDS:
            if feed_info.get("category") != "NEWS":
                continue
            if len(results) >= max_items:
                break
            
            url = feed_info["url"]
            name = feed_info["name"]
            
            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue
                
                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []
                
                for entry in entries[:5]:
                    if len(results) >= max_items:
                        break
                    
                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    summary = self._normalize_text(getattr(entry, "summary", "") or "")
                    
                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue
                    
                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.NEWS,
                        published=published,
                        summary=summary[:500],
                        possible_categories=self._detect_possible_categories(title, summary, name),
                    )
                    results.append(item)
                    self._add_to_pool(item)
                    
            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue
        
        return results

    def _collect_google_news_filtered(self, max_items: int) -> List[NewsItem]:
        """Google Newsから収集（プレスリリース除外）"""
        query = "Artificial Intelligence OR Gemini OR OpenAI OR Claude"
        rss_url = (
            "https://news.google.com/rss/search?"
            + urlencode({"q": query, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
        )

        resp = self._fetch_with_retry(rss_url)
        if not resp:
            return []

        feed = feedparser.parse(resp.content)
        entries = getattr(feed, "entries", []) or []

        results: List[NewsItem] = []
        for entry in entries[:max_items * 3]:
            if len(results) >= max_items:
                break
                
            url = (getattr(entry, "link", "") or "").strip()
            title = (getattr(entry, "title", "") or "").strip()
            published = (getattr(entry, "published", "") or "").strip()
            summary = self._normalize_text(getattr(entry, "summary", "") or "")

            if not url or not title:
                continue
            if not self._is_fresh(url):
                continue
            # プレスリリース系を除外
            if self._is_press_release(title, summary):
                continue

            possible_cats = self._detect_possible_categories(title, summary, "Google News")

            item = NewsItem(
                source="Google News",
                title=title,
                url=url,
                category=Category.NEWS,
                published=published,
                summary=summary[:500],
                possible_categories=possible_cats,
            )
            results.append(item)
            self._add_to_pool(item)

        return results

    # 旧メソッド（互換性のため残す）
    def _collect_google_news(self, max_items: int) -> List[NewsItem]:
        """Google News RSS から収集（レガシー）"""
        return self._collect_google_news_filtered(max_items)

    # -------------------------
    # TOOL Sources
    # -------------------------

    def collect_tools(self, max_items: int = 20) -> List[NewsItem]:
        """TOOL カテゴリー: Product Hunt + GitHub Trending + Reddit から収集"""
        items: List[NewsItem] = []

        # Product Hunt (1/3)
        ph_items = self._collect_product_hunt(max_items // 3 + 2)
        items.extend(ph_items)
        print(f"  [INFO] TOOL from Product Hunt: {len(ph_items)} items")

        # GitHub Trending (1/3)
        gh_items = self._collect_github_trending(max_items // 3 + 2)
        items.extend(gh_items)
        print(f"  [INFO] TOOL from GitHub Trending: {len(gh_items)} items")

        # Reddit ToolsとProjects (1/3)
        reddit_items = self._collect_reddit_tools(max_items // 3 + 2)
        items.extend(reddit_items)
        print(f"  [INFO] TOOL from Reddit: {len(reddit_items)} items")
        
        items = self._rank_items(items)
        print(f"  [INFO] TOOL total: {len(items)} items")

        return items[:max_items]

    def _collect_reddit_tools(self, max_items: int) -> List[NewsItem]:
        """Reddit AI関連サブレディットからツール情報を収集"""
        results: List[NewsItem] = []
        
        for feed_info in REDDIT_FEEDS:
            if feed_info.get("category") != "TOOL":
                continue
            if len(results) >= max_items:
                break
            
            url = feed_info["url"]
            name = feed_info["name"]
            
            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue
                
                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []
                
                for entry in entries[:5]:
                    if len(results) >= max_items:
                        break
                    
                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    summary = self._normalize_text(getattr(entry, "summary", "") or "")
                    
                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue
                    
                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.TOOL,
                        published=published,
                        summary=summary[:500],
                        possible_categories=[Category.TOOL],
                    )
                    results.append(item)
                    self._add_to_pool(item)
                    
            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue
        
        return results

    def _collect_product_hunt(self, max_items: int) -> List[NewsItem]:
        """Product Hunt RSS から AI関連ツールを収集"""
        rss_url = "https://www.producthunt.com/feed"

        resp = self._fetch_with_retry(rss_url)
        if not resp:
            print(f"  [!] Product Hunt RSS fetch failed after retries")
            return []
        
        print(f"  [DEBUG] Product Hunt RSS: status={resp.status_code}, size={len(resp.content)} bytes")

        feed = feedparser.parse(resp.content)
        entries = getattr(feed, "entries", []) or []
        print(f"  [DEBUG] Product Hunt entries found: {len(entries)}")

        # AI関連キーワードでフィルタ (拡張)
        ai_keywords = ["ai", "gpt", "llm", "machine learning", "ml", "neural",
                       "copilot", "chatbot", "automation", "generative", "assistant",
                       "intelligence", "bot", "agent", "model", "transformer", "language",
                       "local", "ollama", "mlx", "rag", "mcp", "coding", "developer", "video", "audio"]

        results: List[NewsItem] = []
        skipped_ai = 0
        skipped_processed = 0
        for entry in entries:
            url = (getattr(entry, "link", "") or "").strip()
            title = (getattr(entry, "title", "") or "").strip()
            summary = self._normalize_text(getattr(entry, "summary", "") or "")

            if not url or not title:
                continue

            # AI関連チェック
            text_lower = (title + " " + summary).lower()
            if not any(kw in text_lower for kw in ai_keywords):
                skipped_ai += 1
                continue

            if not self._is_fresh(url):
                skipped_processed += 1
                continue

            # クロスカテゴリー判定
            possible_cats = self._detect_possible_categories(title, summary, "Product Hunt")

            item = NewsItem(
                source="Product Hunt",
                title=title,
                url=url,
                category=Category.TOOL,
                summary=summary[:500],
                possible_categories=possible_cats,
            )
            results.append(item)
            self._add_to_pool(item)  # プールに追加

            if len(results) >= max_items:
                break

        print(f"  [DEBUG] Product Hunt: fresh={len(results)}, skipped_ai={skipped_ai}, skipped_processed={skipped_processed}")
        return results

    def _collect_github_trending(self, max_items: int) -> List[NewsItem]:
        """GitHub Trending (machine-learning) をスクレイピング"""
        url = "https://github.com/trending/python?since=daily"

        resp = self._fetch_with_retry(url)
        if not resp:
            print(f"  [!] GitHub Trending fetch failed after retries")
            return []
        
        print(f"  [DEBUG] GitHub Trending: status={resp.status_code}, size={len(resp.text)} bytes")

        soup = BeautifulSoup(resp.text, "html.parser")
        repo_list = soup.select("article.Box-row")
        print(f"  [DEBUG] GitHub Trending repos found: {len(repo_list)}")

        results: List[NewsItem] = []
        skipped_processed = 0
        for repo in repo_list[:max_items * 2]:
            try:
                h2 = repo.select_one("h2 a")
                if not h2:
                    continue

                repo_path = h2.get("href", "").strip()
                if not repo_path:
                    continue

                repo_url = f"https://github.com{repo_path}"
                repo_name = repo_path.strip("/")

                # Description
                desc_elem = repo.select_one("p")
                description = self._normalize_text(desc_elem.get_text()) if desc_elem else ""

                # Stars today
                stars_elem = repo.select_one("span.d-inline-block.float-sm-right")
                stars_today = self._normalize_text(stars_elem.get_text()) if stars_elem else ""

                if not self._is_fresh(repo_url):
                    skipped_processed += 1
                    continue

                # クロスカテゴリー判定
                possible_cats = self._detect_possible_categories(repo_name, description, "GitHub Trending")

                if self._score_revenue_intent(repo_name, description, "GitHub Trending") < 1:
                    continue

                item = NewsItem(
                    source="GitHub Trending",
                    title=repo_name,
                    url=repo_url,
                    category=Category.TOOL,
                    summary=description[:500],
                    extra={"stars_today": stars_today},
                    possible_categories=possible_cats,
                )
                results.append(item)
                self._add_to_pool(item)  # プールに追加

                if len(results) >= max_items:
                    break

            except Exception:
                continue

        print(f"  [DEBUG] GitHub Trending: fresh={len(results)}, skipped_processed={skipped_processed}")
        return results

    # -------------------------
    # GUIDE Sources
    # -------------------------

    def collect_guides(self, max_items: int = 20) -> List[NewsItem]:
        """GUIDE カテゴリー: Reddit + 定番トピックから収集"""
        items: List[NewsItem] = []

        # Reddit (RSSフィード使用)
        reddit_items = self._collect_reddit_guides(max_items)
        items.extend(reddit_items)
        print(f"  [INFO] GUIDE from Reddit: {len(reddit_items)} items")

        # 足りない場合は定番ガイドトピックで補填
        if len(items) < max_items:
            remaining = max_items - len(items)
            fallback_items = self._generate_guide_topics(remaining)
            items.extend(fallback_items)
            print(f"  [INFO] GUIDE fallback topics: {len(fallback_items)} items")

        items = self._rank_items(items)
        print(f"  [INFO] GUIDE total: {len(items)} items")
        return items[:max_items]

    def collect_money(self, max_items: int = 20) -> List[NewsItem]:
        """MONEY カテゴリー: 購買・比較・収益意図の強いネタを収集"""
        items: List[NewsItem] = []

        # Local LLM/AI Coding/Agent系の話題から、比較・購入ガイドに変換しやすいものを集める
        hn_items = [self._clone_for_category(item, Category.MONEY) for item in self._collect_hacker_news(max_items)]
        items.extend(hn_items)
        print(f"  [INFO] MONEY from HN: {len(hn_items)} items")

        reddit_items = [self._clone_for_category(item, Category.MONEY) for item in self._collect_reddit_money(max_items)]
        items.extend(reddit_items)
        print(f"  [INFO] MONEY from Reddit: {len(reddit_items)} items")

        gh_items = [self._clone_for_category(item, Category.MONEY) for item in self._collect_github_trending(max_items)]
        items.extend(gh_items)
        print(f"  [INFO] MONEY from GitHub: {len(gh_items)} items")

        items = self._rank_items(items, min_score=1)

        if len(items) < max_items:
            fallback_items = self._generate_money_topics(max_items - len(items))
            items.extend(fallback_items)
            print(f"  [INFO] MONEY fallback topics: {len(fallback_items)} items")

        print(f"  [INFO] MONEY total: {len(items)} items")
        return items[:max_items]

    def _collect_reddit_money(self, max_items: int) -> List[NewsItem]:
        """Redditから購入前ガイド化しやすいローカルAI系トピックを収集"""
        results: List[NewsItem] = []

        for feed_info in REDDIT_FEEDS:
            if feed_info.get("category") != "MONEY":
                continue
            if len(results) >= max_items:
                break

            url = feed_info["url"]
            name = feed_info["name"]

            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue

                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []

                for entry in entries[:8]:
                    if len(results) >= max_items:
                        break

                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    summary = self._normalize_text(getattr(entry, "summary", "") or "")

                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue

                    possible_cats = self._detect_possible_categories(title, summary, name)
                    if "MONEY" not in possible_cats:
                        possible_cats.insert(0, "MONEY")

                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.MONEY,
                        published=published,
                        summary=summary[:500],
                        possible_categories=possible_cats,
                    )
                    results.append(item)
                    self._add_to_pool(item)

            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue

        return results

    def _collect_reddit_guides(self, max_items: int) -> List[NewsItem]:
        """Reddit AI関連サブレディットからガイド・チュートリアル系を収集"""
        results: List[NewsItem] = []
        
        for feed_info in REDDIT_FEEDS:
            if feed_info.get("category") != "GUIDE":
                continue
            if len(results) >= max_items:
                break
            
            url = feed_info["url"]
            name = feed_info["name"]
            
            try:
                resp = self._fetch_with_retry(url)
                if not resp:
                    continue
                
                feed = feedparser.parse(resp.content)
                entries = getattr(feed, "entries", []) or []
                
                for entry in entries[:8]:
                    if len(results) >= max_items:
                        break
                    
                    entry_url = (getattr(entry, "link", "") or "").strip()
                    title = (getattr(entry, "title", "") or "").strip()
                    published = (getattr(entry, "published", "") or "").strip()
                    summary = self._normalize_text(getattr(entry, "summary", "") or "")
                    
                    if not entry_url or not title:
                        continue
                    if not self._is_fresh(entry_url):
                        continue
                    
                    possible_cats = self._detect_possible_categories(title, summary, name)
                    
                    item = NewsItem(
                        source=name,
                        title=title,
                        url=entry_url,
                        category=Category.GUIDE,
                        published=published,
                        summary=summary[:500],
                        possible_categories=possible_cats,
                    )
                    results.append(item)
                    self._add_to_pool(item)
                    
            except Exception as e:
                print(f"  [!] {name} fetch failed: {e}")
                continue
        
        return results

    def _collect_reddit(self, max_items: int) -> List[NewsItem]:
        """Reddit (r/LocalLLaMA, r/OpenAI) の Top posts を収集（レガシー - JSON API版）"""
        subreddits = ["LocalLLaMA", "OpenAI", "MachineLearning", "artificial"]
        results: List[NewsItem] = []

        for subreddit in subreddits:
            if len(results) >= max_items:
                break

            # Reddit JSON API (認証不要)
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=10"

            resp = self._fetch_with_retry(url)
            if not resp:
                print(f"  [!] Reddit r/{subreddit} fetch failed after retries")
                continue
            
            try:
                data = resp.json()
            except Exception as e:
                print(f"  [!] Reddit r/{subreddit} JSON parse failed: {e}")
                continue

            posts = data.get("data", {}).get("children", [])
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "").strip()
                permalink = post_data.get("permalink", "")
                selftext = post_data.get("selftext", "")[:500]
                score = post_data.get("score", 0)

                if not title or not permalink:
                    continue

                post_url = f"https://www.reddit.com{permalink}"

                if not self._is_fresh(post_url):
                    continue

                # スコアが低すぎるものは除外
                if score < 50:
                    continue

                # クロスカテゴリー判定
                possible_cats = self._detect_possible_categories(title, selftext, "Reddit")

                item = NewsItem(
                    source=f"Reddit r/{subreddit}",
                    title=title,
                    url=post_url,
                    category=Category.GUIDE,
                    summary=selftext,
                    extra={"score": score},
                    possible_categories=possible_cats,
                )
                results.append(item)
                self._add_to_pool(item)  # プールに追加

                if len(results) >= max_items:
                    break

        return results

    def _generate_guide_topics(self, count: int) -> List[NewsItem]:
        """定番ガイドトピック（フォールバック用）"""
        topics = [
            ("Ollama + Open WebUIでローカルLLM環境を作る方法", "ollama-webui-setup"),
            ("MLXでApple SiliconローカルLLMを動かす入門", "mlx-local-llm-guide"),
            ("Claude CodeとCursorを併用するAIコーディング環境", "claude-code-cursor-workflow"),
            ("RAGパイプラインの基礎とローカル検索の実装", "rag-local-search-intro"),
            ("llama.cppとGGUF量子化の基本", "llamacpp-gguf-guide"),
            ("AIエージェントを安全に試すサンドボックス構築", "agent-sandbox-guide"),
            ("Whisper系文字起こしをローカルで回す方法", "local-whisper-guide"),
            ("AI動画生成ワークフローの始め方", "ai-video-workflow-guide"),
            ("ベクトルデータベース選定ガイド", "vector-db-comparison"),
            ("プロンプトインジェクション対策入門", "prompt-injection-defense"),
        ]

        random.shuffle(topics)
        results: List[NewsItem] = []

        for title, slug in topics[:count]:
            # 仮のURLを生成（実際にはURLなしで記事生成）
            fake_url = f"guide://{slug}-{uuid.uuid4().hex[:6]}"

            if not self._is_fresh(fake_url):
                continue

            results.append(NewsItem(
                source="Negi Lab Guide",
                title=title,
                url=fake_url,
                category=Category.GUIDE,
                summary="",
                extra={"is_generated_topic": True, "revenue_score": self._score_revenue_intent(title)},
            ))

        return results

    def _generate_money_topics(self, count: int) -> List[NewsItem]:
        """収益記事用の定番トピック（楽天/Amazon導線を作りやすい）"""
        topics = [
            ("ローカルLLM用GPUおすすめ比較：RTX 4060 Ti 16GBは買いか", "local-llm-gpu-rtx4060ti"),
            ("Ollama用PCの選び方：VRAMとメモリで失敗しない構成", "ollama-pc-buying-guide"),
            ("Mac miniでローカルLLMを始めるならメモリ何GBが正解か", "mac-mini-local-llm-memory"),
            ("Claude Code/Cursor向け開発環境のおすすめ周辺機器", "ai-coding-desk-setup"),
            ("AI動画生成を始める前に必要なSSD・GPU・マイク比較", "ai-video-hardware-guide"),
            ("Whisper文字起こし用マイクおすすめと失敗しない選び方", "whisper-mic-buying-guide"),
            ("RAG検証用ミニPCとNASの選び方", "rag-mini-pc-nas-guide"),
            ("Apple Silicon vs NVIDIA GPU：ローカルAI環境の買い分け", "apple-silicon-vs-nvidia-local-ai"),
            ("AIコーディング作業を速くする4Kモニターとキーボード選び", "ai-coding-monitor-keyboard"),
            ("個人開発者向けAIサブスク費用の整理と節約ライン", "ai-subscription-cost-guide"),
        ]

        random.shuffle(topics)
        results: List[NewsItem] = []

        for title, slug in topics[:count]:
            fake_url = f"money://{slug}-{uuid.uuid4().hex[:6]}"

            if not self._is_fresh(fake_url):
                continue

            results.append(NewsItem(
                source="Negi Lab Money",
                title=title,
                url=fake_url,
                category=Category.MONEY,
                summary="楽天/Amazon導線を前提にした購入前比較トピック",
                extra={"is_generated_topic": True, "revenue_score": self._score_revenue_intent(title)},
                possible_categories=["MONEY", "GUIDE"],
            ))

        return results


# ============================================================
# Article Result Data Class
# ============================================================

# Geminiプロンプト共通: ツイート生成メタデータ指示
# 2026-02〜04の729投稿分析 + 外部トレンド（Local LLM/AI Agent/AI Coding）に基づく最適化
TWEET_METADATA_INSTRUCTIONS = """
---
### 【重要】メタデータ出力
記事執筆後、以下を記事の末尾に追記してください。

**1. X投稿用ツイート本文 (TWEET_TEXT)**
X用のネイティブ投稿文を120〜220文字で作成。
※URLとハッシュタグはシステムが必要な場合だけ自動付加するため、本文には含めないこと。

【今回の実データからの鉄則】
- URL直貼り投稿は平均impが大きく低下。本文だけで価値が伝わる投稿にする。
- 伸びた/クリックされたテーマは「ローカルLLM」「RTX/VRAM」「Apple Silicon」「実機検証」「料金・比較」。
- ただのAI企業ニュース、資金調達、買収、訴訟は収益に弱い。書くなら開発者の意思決定に接続する。
- 疑問文で始める投稿は弱い傾向。冒頭は結論・数字・具体的な違和感で入る。

【良い構成】
1. 冒頭: 数字・具体的な環境・結論で入る
2. 中盤: 読者が保存したくなる判断基準を1〜3個
3. 終盤: 無理に質問しない。必要なら「買う前にここを見る」など行動に落とす

【優先テーマ】
- ローカルLLM / Ollama / llama.cpp / MLX / Qwen / Gemma
- RTX / VRAM / GPU / MacBook / Mac Studio / Apple Silicon
- Claude Code / Cursor / Aider / Cline / GitHub Copilot
- RAG / AI Agent / Agent Sandbox / on-device AI
- AI動画・音声・文字起こしの実務導入

【禁止】
- URLを本文に入れる
- 「詳しくはこちら」「記事にまとめました」「参考にどうぞ」
- 「最初はまた便利ツールかと思った」系のテンプレ
- 「知らないと損」「神ツール」「ガチでヤバい」だけで押す煽り
- 箇条書きだけの量産感ある投稿
- #AI #生成AI #AIツール のような薄いタグ指定

- フォーマット:
[TWEET_TEXT_START]
ツイート本文をここに記述（120〜220文字、URLやハッシュタグは含めない）
[TWEET_TEXT_END]

**2. アフィリエイト商品情報 (AFFILIATE_CONTEXT)**
記事を読んだ人が「実際に試したい」「買う前に比較したい」と思ったときに役立つ関連ハードウェアやガジェットを提案。
楽天を主導線、Amazonを補助導線として使うため、楽天/Amazon両方で検索しやすい具体的な型番・商品名を選ぶ。
記事内容と直接関連する商品がない場合は「なし」と出力すること。無理に推薦しない。

出力には以下を3つ含める：
- search_keyword: Amazon/楽天で検索するキーワード（ブランド名+型番推奨）
- product_name: 商品名（短く）
- reason: なぜこの記事の読者におすすめなのか（50文字以内、記事内容とのつながりを示す）

- 良い例: `[AFFILIATE_CONTEXT: search=RTX 4060 Ti 16GB | name=RTX 4060 Ti 16GB | reason=VRAM 16GBでローカルLLM入門に現実的]`
- 良い例: `[AFFILIATE_CONTEXT: search=Mac mini 32GB Apple Silicon | name=Mac mini 32GB | reason=MLX/Ollama検証用の省電力Macとして扱いやすい]`
- 良い例: `[AFFILIATE_CONTEXT: search=Dell U2723QE 27インチ 4K | name=Dell U2723QE | reason=AIレビューとコードを並べる開発環境に向く]`
- 関連商品なし: `[AFFILIATE_CONTEXT: なし]`
- ダメ例: 記事が「資金調達ニュース」なのに「マウス」を推薦 → 無関係すぎる

- フォーマット: `[AFFILIATE_CONTEXT: search=検索ワード | name=商品名 | reason=おすすめ理由]` または `[AFFILIATE_CONTEXT: なし]`

**3. SNS拡散用ハッシュタグ (HASHTAGS)**
エンゲージメント狙いのタグを最大2つ（記事固有タグ＋コミュニティタグ）
- 良い例: #ローカルLLM #個人開発
- 良い例: #エンジニア #業務効率化
- ダメ例: #AI #生成AI #AIツール（薄すぎる）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`

**4. SEOタグ (SEO_TAGS)**
記事の内容に基づきGoogle検索で見つけてもらうためのタグを3〒4つ生成。
記事固有の具体的なキーワードを使うこと（「AI」「機械学習」など汎用的すぎるワードは不可）。
- 良い例: `[SEO_TAGS: Gemini 3 Flash, マルチモーダル, Google AI, ベンチマーク]`
- 良い例: `[SEO_TAGS: LangChain, RAG, ベクトルデータベース]`
- ダメ例: `[SEO_TAGS: AI, 最新ニュース, テクノロジー]`（汎用すぎる）
- フォーマット: `[SEO_TAGS: タグ1, タグ2, タグ3]`

**5. URLスラッグ (SLUG)**
SEOに最適化された英語URLスラッグを生成。
- 小文字英字とハイフンのみ使用（3〜6単語）
- 記事内容が伝わる具体的なスラッグ
- 良い例: `[SLUG: gemini-3-flash-multimodal-release]`
- 良い例: `[SLUG: langchain-rag-tutorial-beginners]`
- ダメ例: `[SLUG: ai-news-today]`（汎用すぎる）
- フォーマット: `[SLUG: english-slug-here]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
- ⚠️や💡などの絵文字を見出しや本文に使わない（メタデータ部分のみ可）
"""

@dataclass
class ArticleResult:
    """記事生成結果を保持するデータクラス"""
    title: str
    body: str
    description: Optional[str] = None  # 3行要約から抽出したdescription
    tweet_text: Optional[str] = None  # X投稿用の完全なツイート本文（Gemini生成）
    hook_text: Optional[str] = None  # X投稿用のフック文（後方互換用）
    summary_text: Optional[str] = None  # X投稿用の3行要約（後方互換用）
    question_text: Optional[str] = None  # X投稿用の質問文（後方互換用）
    shopping_keyword: Optional[str] = None
    viral_tags: Optional[str] = None  # "#タグ1 #タグ2" 形式
    seo_tags: Optional[List[str]] = None  # SEO用タグ（記事固有キーワード）
    slug: Optional[str] = None  # SEO用URLスラッグ（英語）


# ============================================================
# Article Generator
# ============================================================

class ArticleGenerator:
    """Gemini APIを使用してカテゴリー別の記事を生成"""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_article(self, item: NewsItem) -> ArticleResult:
        """
        記事を生成し、ArticleResultを返す。
        """
        prompt = self._build_prompt(item)

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned empty response")

        # 外側の```markdownフェンスのみ除去（内部のコードブロックは保持）
        cleaned = text.strip()
        
        # 先頭のフェンス除去
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[len("```markdown"):].strip()
        elif cleaned.startswith("```md"):
            cleaned = cleaned[len("```md"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        
        # 末尾のフェンス除去（本文末の単独```のみ対象）
        lines = cleaned.split("\n")
        while lines and lines[-1].strip() == "```":
            lines.pop()
        cleaned = "\n".join(lines).strip()

        # カテゴリーを渡してアフィリエイト最適化
        return self._extract_title_and_body(cleaned, item.category)

    def _build_prompt(self, item: NewsItem) -> str:
        """カテゴリーに応じたプロンプトを構築"""

        if item.category == Category.MONEY:
            return self._build_money_prompt(item)
        elif item.category == Category.NEWS:
            return self._build_news_prompt(item)
        elif item.category == Category.TOOL:
            return self._build_tool_prompt(item)
        else:  # GUIDE
            return self._build_guide_prompt(item)

    def _build_money_prompt(self, item: NewsItem) -> str:
        is_generated = item.extra.get("is_generated_topic", False)
        topic_info = f"- トピック: {item.title}" if is_generated else f'''- タイトル: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 内容: {item.summary}" if item.summary else ""}'''

        return f'''あなたは「ねぎ」という名前のAI専門ブロガーです。

【あなたのペルソナ】
{PERSONA["background"]}

【文章スタイル】
{PERSONA["writing_style"]}

【トピック情報】
{topic_info}

【記事の目的】
この記事は月3万円の収益化を狙う「購入前ガイド・比較記事」です。読者が楽天/Amazonで商品を探す直前に読む記事として書いてください。
対象読者は、AI開発・ローカルLLM・AIコーディング・業務効率化に投資したいエンジニア/個人開発者です。

【最重要方針】
- ただのニュース解説ではなく「何を買う/選ぶべきか」「買わなくてよい条件」を明確にする
- 楽天で価格比較しやすい型番・商品カテゴリを本文に自然に入れる
- Amazonでも購入される可能性を考え、型番検索しやすい表記にする
- 読者の失敗回避に寄せる（VRAM不足、メモリ不足、端子不足、サブスク費用、商用利用制限など）
- 本文は3500〜5000文字。薄い紹介ではなく、比較表・チェックリスト・用途別おすすめを必ず入れる
- 根拠のない断定は禁止。不確かな最新情報は「公開情報ベース」「検証環境による」と明記する

【最近のトレンドを必ず反映】
- ローカルLLM/Ollama/llama.cpp/MLX/Qwen/Gemma
- RTX/VRAM/Apple Silicon/統一メモリ
- Claude Code/Cursor/Aider/Cline/GitHub CopilotなどAIコーディング
- Agent Sandbox/RAG/ローカル検索/オンデバイスAI
- AI動画・音声・文字起こしの実務導入

【SEO最適化】
- タイトル: 「おすすめ」「比較」「選び方」「買う前に」「ローカルLLM」「RTX」「Mac」「Claude Code」など購買/比較キーワードを自然に入れる。32〜40文字程度。
- 3行要約: 検索結果でクリックされるよう、誰向け・結論・注意点を具体的に書く
- 見出し: 「用途別おすすめ」「買う前のチェックリスト」「楽天/Amazonで見るべき型番」など検索意図に直結させる
- 本文: 商品名・型番・用途キーワードを自然に複数回入れる。ただしキーワード詰め込みは禁止

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし。「おすすめ」「比較」「選び方」など購買意図を含める）

## 3行要約

- 要約1（この記事の結論。誰が何を選ぶべきか）
- 要約2（価格・性能・用途の判断軸）
- 要約3（買う前に失敗しやすい注意点）

## 結論: まず選ぶべき構成

（最初に結論を出す。読者の用途別に「これで十分」「ここから上は趣味/業務用」と切り分ける。300文字以上）

## 用途別おすすめ

| 用途 | 推奨構成/商品カテゴリ | 理由 | 注意点 |
|------|----------------------|------|--------|
| 入門 | ... | ... | ... |
| 本格運用 | ... | ... | ... |
| 仕事用 | ... | ... | ... |

（表の後に、どの読者がどれを選ぶべきかを具体的に説明。500文字以上）

## 買う前のチェックリスト

- チェック1: （例: VRAM容量、メモリ、端子、商用利用、月額費用）
- チェック2:
- チェック3:
- チェック4:

（各チェック項目を実務者目線で解説。600文字以上）

## 楽天/Amazonで見るべき検索キーワード

（楽天で価格比較しやすい具体的な型番・商品カテゴリを3〜5個挙げる。Amazonでも検索しやすい表記にする）

| 検索キーワード | 向いている人 | 避けた方がいい人 |
|----------------|--------------|------------------|
| ... | ... | ... |

## 代替案と妥協ライン

（高い商品を無理に買わせない。中古・型落ち・クラウド利用・無料ツールなどの代替案を提示し、どこまで妥協できるかを説明。500文字以上）

## 私ならこう選ぶ

（「ねぎ」として明確に選定する。楽天で価格を見るなら何を最初に検索するか、Amazonで買うなら何を確認するかまで具体化。400文字以上）

## よくある質問

### Q1: （購入前に最も迷う質問）

（簡潔で具体的な回答。100文字程度）

### Q2: （スペック・料金・代替に関する質問）

（簡潔で具体的な回答。100文字程度）

### Q3: （将来性・買い時に関する質問）

（簡潔で具体的な回答。100文字程度）

{TWEET_METADATA_INSTRUCTIONS}
'''

    def _build_news_prompt(self, item: NewsItem) -> str:
        return f'''あなたは「ねぎ」という名前のAI専門ブロガーです。

【あなたのペルソナ】
{PERSONA["background"]}

【文章スタイル】
{PERSONA["writing_style"]}

【元ニュース情報】
- タイトル: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 要約: {item.summary}" if item.summary else ""}

【指示】
速報ニュース記事を書いてください。**本文は1200〜1800文字程度**で、短くても判断材料の濃い解説にすること。
- 何が発表されたか（詳細に）
- 競合（ChatGPT, Claude等）との違いは何か
- 技術的な仕組みや背景
- 業界への影響を論理的に解説し、関連するMONEY/GUIDE記事へ読者が進みたくなる論点を入れる
- 一人称は「私」を使い、読者に語りかける口調で

【記事品質ガイドライン ★最重要★】
- 冒頭: 自己紹介で始めるのは禁止。「このニュースが重要な理由」を冒頭1文で示す
- 独自視点: 公式発表の要約ではなく「だから何なのか」「開発者にどう影響するのか」を深掘り
- 本音: 「革命的」「画期的」等の空虚な形容詞は禁止。代わりに「GPT-4oより速くなった」「料金が半額になった」等の具体的事実で語る
- 比較: 公開情報で確認できる範囲で既存サービスとの比較を含める（性能、価格、対応言語数など。推測なら推測と明記）
- 実務者目線: 公開情報・APIドキュメントを確認した前提で、開発者の意思決定にどう効くかを書く
- 段落: 1段落2〜3文。長文は分割する
- 定型文禁止: 「〜ではないでしょうか」「注目が集まっています」「AI業界に激震」等のクリシェは絶対に使わない
- 予測: 記事の最後に「3ヶ月後にどうなっているか」の具体的予測を入れる

【SEO最適化 ★重要★】
- タイトル: 検索されそうなキーワードを自然に含める（例: 「Gemini 3 vs GPT-4o 性能比較」）。32文字以内推奨
- 3行要約: meta descriptionとして使われる。検索結果に表示された時にクリックしたくなる具体性のある文を書く
- 見出し(h2): 検索クエリになりそうなフレーズを使う（「〜の使い方」「〜と〜の違い」等）
- 本文: 記事テーマの主要キーワードを自然に3〜5回使う（キーワードスタッフィングはしない）

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、## などは付けない。読者が思わずクリックしたくなる具体的なタイトル。「〜とは」「〜について」のような漠然としたタイトルは禁止）

## 3行要約

- 要約1（最も重要な事実を1文で）
- 要約2（技術的なポイントを1文で）
- 要約3（読者への影響を1文で）

## 何が起きたのか

（冒頭で「なぜこのニュースが重要か」を示してから、詳細を展開。発表内容だけでなく、その背景（なぜ今このタイミングなのか、どんな問題を解決するのか）を掘り下げる。300文字以上）

## 技術的に何が新しいのか

（公式発表の受け売りではなく、技術的な仕組みを自分の言葉で噛み砕いて説明。「従来は○○だったが、今回は△△」の構造で書く。コード例や設定例があれば含める。300文字以上）

## 数字で見る競合比較

| 項目 | 今回の発表 | 競合A | 競合B |
|------|-----------|-------|-------|
| ... | ... | ... | ... |

（表の後に「この数字が意味すること」を解説。単なるスペック比較ではなく、実務でどの差が効くかを論じる。300文字以上）

## 開発者が今すぐやるべきこと

（読者が記事を読んだ後に取れる具体的なアクションを3つ以上列挙。「注目しましょう」ではなく「APIキーを取得する」「既存コードの○○を書き換える」「ベンチマークを取る」「必要スペックを確認する」等の実行可能なアクション。250文字以上）

## 私の見解

（「ねぎ」としての本音。ここでは遠慮しない。明確に賛成/反対/懐疑を表明し、その理由を具体的に述べる。最後に、より詳しく調べるべきスペック・料金・代替案を示す。250文字以上）

## よくある質問

### Q1: （このニュースに関する最も基本的な疑問）

（簡潔で具体的な回答。100文字程度）

### Q2: （開発者が最も気になる実務的な疑問）

（簡潔で具体的な回答。100文字程度）

### Q3: （将来性・比較に関する疑問）

（簡潔で具体的な回答。100文字程度）

{TWEET_METADATA_INSTRUCTIONS}
'''

    def _build_tool_prompt(self, item: NewsItem) -> str:
        stars_info = f"- 今日のスター数: {item.extra['stars_today']}" if item.extra.get("stars_today") else ""

        return f'''あなたは「ねぎ」という名前のAI専門ブロガーです。

【あなたのペルソナ】
{PERSONA["background"]}

【文章スタイル】
{PERSONA["writing_style"]}

【対象ツール情報】
- 名前: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 説明: {item.summary}" if item.summary else ""}
{stars_info}

【指示】
ツールの実践的なレビュー記事を書いてください。**本文は2500〜4000文字程度**で、密度の高い解説をすること。
公式ドキュメントやGitHubのREADMEを読み込んだ上で書いているかのように、具体的な情報を含めること。

★重要★ 以下の2点を厳守:
1. シミュレーションコードは「公式ドキュメントに基づいた使用例」として書く（架空のAPIや存在しないメソッドは使わない。OSSならGitHubのREADMEに実際にありそうなAPI形式で書く）
2. 「誰が使うべきで、誰が使わなくてよいか」を明確にする
3. 価格・無料枠・商用利用・代替ツール・必要スペックを必ず確認する。ハードウェアや開発環境が必要ならAFFILIATE_CONTEXTを出す

一人称は「私」を使い、実際にドキュメントを読んで評価した体験談として書く。

【記事品質ガイドライン ★最重要★】
- 冒頭: 自己紹介は禁止。「このツールを一言で言うと○○」で始める
- 段落: 1段落2〜3文
- 正直さ: ダメなところは具体的に書く（「ドキュメントが英語のみ」「Python 3.10以降限定」「GPU必須で敷居が高い」等）
- 定量化: 「高速」→「100件の処理が0.3秒」、「使いやすい」→「pip installから動作確認まで2分」
- 行動指針: 読者が「今日から使える」具体的な手順を含める
- 対象読者: 中級エンジニア（Python基礎はわかる人）向け
- 代替ツール: 必ず1つ以上の代替手段に触れる（「○○の方が合う人もいる」）
- 収益導線: 必要なPC/GPU/モニター/マイク/SSDなどがある場合は、本文中で「買う前に見るべき型番」を自然に紹介する
- 定型文禁止: 「注目されています」「ぜひ試してみてください」「いかがでしたか」は使わない

【SEO最適化 ★重要★】
- タイトル: 「ツール名 使い方」「ツール名 レビュー」等の検索されるキーワードを含める。32文字以内推奨
- 3行要約: meta descriptionとして使われる。検索結果でクリックしたくなる具体性のある文を書く
- 見出し(h2): 検索クエリになりそうなフレーズを使う（「〜のインストール方法」「〜 vs 代替ツール」等）
- 本文: ツール名とその用途キーワードを自然に3〜5回使う

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし。「ツール名」+「何ができるか」を含めたタイトル。「〜を徹底解説！」等の煽りタイトルは禁止）

**注意:** 本記事はドキュメント・公開情報をもとにした評価記事です。コード例はシミュレーションです。

## 3行要約

- 要約1（ツールが解決する具体的な問題）
- 要約2（他ツールとの最大の違い）
- 要約3（使うべき人・使わなくていい人）

## 結論から: このツールは「買い」か

（最初に結論を述べる。★評価付き。「○○な人には最高、△△な人には不要」と明確に。200文字以上）

## このツールが解決する問題

（「〜できるツールです」ではなく、「従来は○○が問題だった。このツールは△△で解決する」という問題→解決の構造で書く。400文字以上）

## 実際の使い方

### インストール

```bash
pip install xxx
```

（インストール時の注意点や前提条件も書く）

### 基本的な使用例

```python
# ドキュメントに基づいたサンプルコード
from xxx import YYY

# 設定と実行
model = YYY()
result = model.run("テスト入力")
print(result)
```

（コードの各行が何をしているか、実務でのカスタマイズポイントを解説）

### 応用: 実務で使うなら

（実際の業務シナリオでの使用例。「バッチ処理」「API連携」「既存プロジェクトへの組み込み」等、実践的な例）

## 強みと弱み

**強み:**
- （具体的に。「使いやすい」ではなく「APIが3つしかないのでラーニングコストが低い」）
- ...

**弱み:**
- （正直に。「日本語ドキュメントがない」「Windows非対応」「商用利用のライセンスが不明瞭」等）
- ...

## 代替ツールとの比較

| 項目 | {item.title} | 代替A | 代替B |
|------|-------------|-------|-------|
| ... | ... | ... | ... |

（どのツールをどんな場面で選ぶべきかを具体的に）

## 料金・必要スペック・導入前の注意点

（無料枠、商用利用、ローカル実行に必要なPC/GPU/メモリ、クラウド費用を整理する。ハードウェアが絡む場合は楽天/Amazonで検索しやすい型番も自然に触れる。300文字以上）

## 私の評価

（★評価（5段階）と、その理由。「万人におすすめ」ではなく「こういうプロジェクトなら使う、そうでなければ使わない」と具体的に。300文字以上）

## よくある質問

### Q1: （このツールの導入に関する最も基本的な疑問）

（簡潔で具体的な回答。100文字程度）

### Q2: （無料プラン・価格・ライセンスに関する疑問）

（簡潔で具体的な回答。100文字程度）

### Q3: （既存ツールとの違い・乗り換えに関する疑問）

（簡潔で具体的な回答。100文字程度）

{TWEET_METADATA_INSTRUCTIONS}
'''

    def _build_guide_prompt(self, item: NewsItem) -> str:
        is_generated = item.extra.get("is_generated_topic", False)
        topic_info = f"- トピック: {item.title}" if is_generated else f'''- タイトル: {item.title}
- URL: {item.url}
- 出典: {item.source}
{f"- 内容: {item.summary}" if item.summary else ""}'''

        return f'''あなたは「ねぎ」という名前のAI専門ブロガーです。

【あなたのペルソナ】
{PERSONA["background"]}

【文章スタイル】
{PERSONA["writing_style"]}

【トピック情報】
{topic_info}

【指示】
実践的なガイド記事を書いてください。**本文は3000〜4500文字程度**。
この記事のゴールは「読者が記事を読みながら手を動かして、最後には動くものが一つできている」こと。

★重要★
- 抽象的な解説ではなく、「コピペして動かせる」レベルの具体性
- 「なぜその設定にするのか」の理由を毎回添える（表面的な手順書にしない）
- 初心者がハマるポイントを先回りして「落とし穴」として明示する
- 必要なPC/GPU/メモリ/周辺機器/有料ツールがある場合は、購入前チェックリストとAFFILIATE_CONTEXTを必ず入れる
- 一人称は「私」

【記事品質ガイドライン ★最重要★】
- 冒頭: 「この記事を読むと何が作れるか」を具体的に1文で示す（「○○と連携して△△を自動化するスクリプトを作ります」等）
- 段落: 1段落2〜3文
- 実用性: 全コード例は実際に動く形式で書く。importやAPIキー設定も省略しない
- 失敗体験: 「最初に○○で試したら失敗した。△△にしたら解決した」という試行錯誤を含めると共感が生まれる
- 所要時間: 記事冒頭に「所要時間: 約30分」のように目安を示す
- 定型文禁止: 「いかがでしたか」「みなさんも経験ありませんか」「〜ではないでしょうか」は一切使わない

【SEO最適化 ★重要★】
- タイトル: 「○○ 使い方」「○○ 入門」「○○ やり方」等のHow-to検索クエリを含める。32文字以内推奨
- 3行要約: meta descriptionとして使われる。「この記事を読めば○○ができるようになる」を伝える
- 見出し(h2): 「Step 1:」等のステップ表記 + 検索されそうなフレーズ（「環境構築」「エラー対処法」等）
- 本文: ツール名・技術名を自然に3〜5回使う。ロングテールキーワード（「Python API 使い方」等）も意識

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし。「○○で△△を作る方法」「○○入門」形式。やることが明確に伝わるタイトル）

**所要時間:** 約XX分 | **難易度:** ★☆☆☆☆〜★★★★★

## この記事で作るもの

- 完成形を具体的に示す（「○○ができるPythonスクリプト」等）
- 前提知識（「Pythonの基礎がわかること」等）
- 必要なもの（APIキー、ハードウェア等）

## 先に確認するスペック・料金

（ローカルLLM/GPU/Mac/AIツール/API料金など、始める前に詰まりやすい条件を整理する。買う前に見るべき型番や、買わずに済む代替案も書く。300文字以上）

## なぜこの方法を選ぶのか

（「他にも○○を使う方法があるが、△△の理由でこの方法がベスト」。代替手段と比較して、なぜこのアプローチかを説明。200文字以上）

## Step 1: 環境を整える

```bash
# コマンド例
```

（各コマンドの意味を説明。「XXXはYYYをインストールしています。ZZZバージョン以上が必要です」）

⚠️ **落とし穴:** （初心者がハマりがちなポイントと対処法）

## Step 2: 基本の設定

```python
# 設定コード例（APIキー設定、初期化含む）
import os
from xxx import YYY

# 環境変数からAPIキーを読み込む（直書きはNG）
api_key = os.environ["XXX_API_KEY"]
client = YYY(api_key=api_key)
```

（各設定項目の意味と「なぜこの値にするのか」を解説）

## Step 3: 動かしてみる

```python
# 最小限の動作確認
result = client.run("テスト入力")
print(result)
```

### 期待される出力

```
（出力例）
```

（結果の読み方を解説）

## Step 4: 実用レベルにする

（バッチ処理、エラーハンドリング、既存システムとの連携など、実務で使えるレベルに拡張する手順）

```python
# 実用的なコード例
```

## よくあるトラブルと解決法

| エラー内容 | 原因 | 解決策 |
|-----------|------|--------|
| ... | ... | ... |

## 次のステップ

（この記事の内容をマスターした後に取り組むべきこと。具体的なリソースやプロジェクトアイデアを提示。200文字以上）

## よくある質問

### Q1: （このガイドの前提条件・環境に関する疑問）

（簡潔で具体的な回答。100文字程度）

### Q2: （実装中のよくあるエラー・トラブルに関する疑問）

（簡潔で具体的な回答。100文字程度）

### Q3: （応用・カスタマイズに関する疑問）

（簡潔で具体的な回答。100文字程度）

{TWEET_METADATA_INSTRUCTIONS}
'''

    def _extract_title_and_body(self, text: str, category: Category = Category.NEWS) -> ArticleResult:
        """
        Gemini出力からタイトル、本文、キーワード、ハッシュタグを抽出。
        """
        lines = [ln.rstrip() for ln in text.splitlines()]
        title = ""
        body_start = 0

        for i, ln in enumerate(lines):
            stripped = ln.strip()
            if stripped:
                # タイトル行を抽出
                title = stripped.strip('"').strip("'")
                title = re.sub(r"^#{1,6}\s+", "", title).strip()
                body_start = i + 1
                break

        if not title:
            title = "AIトレンド記事（自動生成）"

        body = "\n".join(lines[body_start:]).lstrip("\n")
        if not body:
            body = "(本文生成に失敗しました)"

        # カテゴリーに応じたアフィリエイト最適化とメタデータ抽出
        body, shopping_keyword, viral_tags, tweet_text, hook_text, summary_text, question_text, seo_tags, slug = self._extract_keywords_and_add_affiliate(body, category)
        
        # 3行要約からdescriptionを抽出
        description = self._extract_description(body)

        return ArticleResult(
            title=title,
            body=body,
            description=description,
            tweet_text=tweet_text,
            hook_text=hook_text,
            summary_text=summary_text,
            question_text=question_text,
            shopping_keyword=shopping_keyword,
            viral_tags=viral_tags,
            seo_tags=seo_tags,
            slug=slug,
        )
    
    def _extract_description(self, body: str) -> Optional[str]:
        """
        3行要約セクションからdescriptionを抽出。
        ⚠️💡や引用形式の文は除外する。
        """
        # 「## 3行要約」または「## この記事で学べること」セクションを探す
        patterns = [
            r'##\s*3行要約\s*\n+((?:- .+\n?)+)',
            r'##\s*この記事で学べること\s*\n+((?:- .+\n?)+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                bullet_points = match.group(1).strip()
                # 箇条書きを結合してdescriptionを生成
                points = []
                for line in bullet_points.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        point = line[2:].strip()
                        # ⚠️💡を含む行は除外
                        if not any(emoji in point for emoji in ['⚠️', '💡', '>']):
                            points.append(point)
                
                if points:
                    # 最初の2つを結合（80文字以内に収める）
                    desc = '。'.join(points[:2])
                    if len(desc) > 80:
                        desc = desc[:77] + '...'
                    return desc
        
        return None

    def _extract_keywords_and_add_affiliate(self, body: str, category: Category = Category.NEWS) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[List[str]], Optional[str]]:
        """
        本文から[SHOPPING: xxx]、[HASHTAGS: xxx]、[HOOK: xxx]、[SUMMARY: xxx]、[QUESTION: xxx]を抽出し、
        カテゴリーに応じたアフィリエイトリンクを追加。
        
        Args:
            body: 記事本文
            category: 記事カテゴリー（NEWS/TOOL/GUIDE）
        
        Returns:
            (処理済み本文, shopping_keyword, viral_tags, tweet_text, hook_text, summary_text, question_text, seo_tags, slug)
        """
        # 0. Tweet Text 抽出（Gemini生成の完全なツイート本文）
        tweet_text_pattern = r'\[TWEET_TEXT_START\]\s*(.*?)\s*\[TWEET_TEXT_END\]'
        tweet_text_match = re.search(tweet_text_pattern, body, re.DOTALL)
        tweet_text = None
        if tweet_text_match:
            tweet_text = tweet_text_match.group(1).strip()
            body = re.sub(r'\n*\[TWEET_TEXT_START\].*?\[TWEET_TEXT_END\]\n*', '\n', body, flags=re.DOTALL)
        
        # 0.1. Hook Text 抽出（後方互換用）
        hook_pattern = r'\[HOOK:\s*(.+?)\]'
        hook_match = re.search(hook_pattern, body)
        hook_text = None
        if hook_match:
            hook_text = hook_match.group(1).strip()
            body = re.sub(r'\n*\[HOOK:[^\]]+\]\n*', '\n', body)
        
        # 0.2. Summary Text 抽出（後方互換用）
        summary_pattern = r'\[SUMMARY:\s*(.+?)\]'
        summary_match = re.search(summary_pattern, body, re.DOTALL)
        summary_text = None
        if summary_match:
            summary_text = summary_match.group(1).strip()
            body = re.sub(r'\n*\[SUMMARY:[^\]]+\]\n*', '\n', body)
        
        # 0.3. Question Text 抽出（後方互換用）
        question_pattern = r'\[QUESTION:\s*(.+?)\]'
        question_match = re.search(question_pattern, body)
        question_text = None
        if question_match:
            question_text = question_match.group(1).strip()
            body = re.sub(r'\n*\[QUESTION:[^\]]+\]\n*', '\n', body)
        
        # 1. Affiliate Context 抽出（新形式: Gemini生成のコンテキスト付きアフィリエイト）
        affiliate_pattern = r'\[AFFILIATE_CONTEXT:\s*(.+?)\]'
        affiliate_match = re.search(affiliate_pattern, body)
        shopping_keyword = None
        affiliate_product_name = None
        affiliate_reason = None
        if affiliate_match:
            raw = affiliate_match.group(1).strip()
            if raw != "なし":
                # "search=XXX | name=YYY | reason=ZZZ" をパース
                parts = {}
                for part in raw.split('|'):
                    part = part.strip()
                    if '=' in part:
                        key, val = part.split('=', 1)
                        parts[key.strip()] = val.strip()
                shopping_keyword = parts.get('search')
                affiliate_product_name = parts.get('name')
                affiliate_reason = parts.get('reason')
            body = re.sub(r'\n*\[AFFILIATE_CONTEXT:[^\]]+\]\n*', '\n', body)
        
        # 1.1. 旧形式 [SHOPPING: xxx] の後方互換
        if not shopping_keyword:
            shopping_pattern = r'\[SHOPPING:\s*(.+?)\]'
            shopping_match = re.search(shopping_pattern, body)
            if shopping_match:
                shopping_keyword = shopping_match.group(1).strip()
                body = re.sub(r'\n*\[SHOPPING:[^\]]+\]\n*', '\n', body)
        
        # 2. Viral Tags 抽出
        hashtags_pattern = r'\[HASHTAGS:\s*(.+?)\]'
        hashtags_match = re.search(hashtags_pattern, body)
        viral_tags = None
        if hashtags_match:
            viral_tags = hashtags_match.group(1).strip()
            body = re.sub(r'\n*\[HASHTAGS:[^\]]+\]\n*', '\n', body)
        
        # 2.1. SEO Tags 抽出（記事固有キーワード）
        seo_tags_pattern = r'\[SEO_TAGS:\s*(.+?)\]'
        seo_tags_match = re.search(seo_tags_pattern, body)
        seo_tags = None
        if seo_tags_match:
            raw_tags = seo_tags_match.group(1).strip()
            seo_tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
            body = re.sub(r'\n*\[SEO_TAGS:[^\]]+\]\n*', '\n', body)
        
        # 2.2. Slug 抽出（SEO用英語URLスラッグ）
        slug_pattern = r'\[SLUG:\s*(.+?)\]'
        slug_match = re.search(slug_pattern, body)
        slug = None
        if slug_match:
            raw_slug = slug_match.group(1).strip().lower()
            # 英字・数字・ハイフンのみ許可
            slug = re.sub(r'[^a-z0-9-]', '-', raw_slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
            if slug:
                body = re.sub(r'\n*\[SLUG:[^\]]+\]\n*', '\n', body)
            else:
                slug = None
        
        # 3. 旧形式の[KEYWORD: xxx]も念のため除去（互換性）
        body = re.sub(r'\n*\[KEYWORD:[^\]]+\]\n*', '\n', body)
        
        # 4. 末尾の「---」以降のメタデータ出力指示も除去
        body = re.sub(r'\n---\n### 【重要】キーワード選定タスク[\s\S]*$', '', body)
        body = re.sub(r'\n---\n### 【重要】メタデータ出力[\s\S]*$', '', body)
        
        # 5. クリーンアップ（連続する空行を整理）
        body = re.sub(r'\n{3,}', '\n\n', body).strip()
        
        # 6. カテゴリーに応じたアフィリエイト挿入（Geminiコンテキスト優先）
        body = self._insert_smart_affiliate(body, category, shopping_keyword, affiliate_product_name, affiliate_reason)
        
        return body, shopping_keyword, viral_tags, tweet_text, hook_text, summary_text, question_text, seo_tags, slug

    def _detect_content_topics(self, text: str) -> List[str]:
        """本文からトピックを検出し、マッチする商品カテゴリーを返す"""
        text_lower = text.lower()
        matched_topics = []
        
        for topic_id, topic_data in PRODUCT_MAPPINGS.items():
            if topic_id == "default":
                continue
            for keyword in topic_data["keywords"]:
                if keyword.lower() in text_lower:
                    matched_topics.append(topic_id)
                    break
        
        # マッチがなければdefault
        if not matched_topics:
            matched_topics = ["default"]
        
        return matched_topics[:3]  # 最大3トピック

    def _insert_smart_affiliate(self, body: str, category: Category, shopping_keyword: Optional[str], product_name: Optional[str] = None, reason: Optional[str] = None) -> str:
        """
        Geminiが生成したコンテキストに基づきアフィリエイトを挿入。
        
        改善ポイント:
        - 記事「3行要約」の直後に挿入（読者の目に入りやすい位置）
        - デフォルト商品のフォールバック廃止（無関係な商品はCTR悪化の原因）
        - HTMLカード形式で視認性UP
        """
        # Geminiが「関連商品なし」と判断した場合はスキップ
        if not shopping_keyword:
            return body
        
        # アフィリエイトHTMLブロックを生成
        amazon_url = self._make_amazon_url(shopping_keyword)
        rakuten_url = self._make_rakuten_url(shopping_keyword)
        
        if product_name and reason:
            # Gemini生成のコンテキストがある場合（新形式） - カード型UI
            affiliate_html = f'''{{{{< rawhtml >}}}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 この記事に関連する商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">{product_name}</strong>
<p style="color:#555;margin:8px 0;font-size:14px">{reason}</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{{{< /rawhtml >}}}}'''
        else:
            # shopping_keywordのみの場合（旧形式）
            # トピックマッチを確認 - 無関連なら挿入しない
            topics = self._detect_content_topics(body)
            real_topics = [t for t in topics if t != "default"]
            
            if real_topics:
                # トピックマッチがある場合は具体的な商品で表示
                topic = real_topics[0]
                topic_data = PRODUCT_MAPPINGS.get(topic, {})
                if topic_data.get("products"):
                    product = topic_data["products"][0]
                    amazon_url = self._make_amazon_url(product["search"])
                    rakuten_url = self._make_rakuten_url(product["search"])
                    product_name = product["name"]
                    reason = product["desc"]
            
            # product_nameがセットされた場合のみ表示
            if product_name:
                affiliate_html = f'''{{{{< rawhtml >}}}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 4px;font-size:13px;color:#888">📦 関連商品（楽天メインで価格確認）</p>
<strong style="font-size:16px">{product_name}</strong>
<p style="color:#555;margin:8px 0;font-size:14px">{reason}</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で価格を見る</a>
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{{{< /rawhtml >}}}}'''
            else:
                # マッチなし → リンクのみ
                affiliate_html = f'''{{{{< rawhtml >}}}}
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:20px 0;background:#fafafa">
<p style="margin:0 0 8px;font-size:13px;color:#888">🔎 関連商品を探す</p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding:10px 18px;background:#bf0000;color:#fff;text-decoration:none;border-radius:4px;font-size:14px;font-weight:bold">楽天で「{shopping_keyword}」を検索</a>
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding:8px 16px;background:#ff9900;color:#fff;text-decoration:none;border-radius:4px;font-size:13px;font-weight:bold">Amazonでも確認</a>
</div>
<p style="margin:8px 0 0;font-size:11px;color:#aaa">※アフィリエイトリンクを含みます</p>
</div>
{{{{< /rawhtml >}}}}'''
        
        # 挿入位置: 「3行要約」セクションの直後に配置（読者の注目度が最も高い位置）
        # 従来は記事末尾→誰もスクロールしない
        summary_patterns = [
            r'(## 3行要約\s*\n(?:- .+\n){1,5})',  # 3行要約セクション
            r'(## この記事で作るもの\s*\n(?:- .+\n){1,5})',  # GUIDEの冒頭セクション
        ]
        inserted = False
        for pattern in summary_patterns:
            match = re.search(pattern, body)
            if match:
                insert_pos = match.end()
                body = body[:insert_pos] + "\n" + affiliate_html + "\n" + body[insert_pos:]
                inserted = True
                break
        
        if not inserted:
            # パターンマッチしない場合は記事末尾に追加
            body = body + "\n\n" + affiliate_html
        
        return body

    def _make_amazon_url(self, keyword: str) -> str:
        """Amazonアフィリエイトリンクを生成"""
        encoded = quote(keyword, safe="")
        return f"https://www.amazon.co.jp/s?k={encoded}&tag={AMAZON_ASSOCIATE_TAG}"

    def _make_rakuten_url(self, keyword: str) -> str:
        """楽天アフィリエイトリンクを生成（hb.afl.rakuten.co.jp経由）"""
        # 楽天市場の検索ページURL
        search_url = f"https://search.rakuten.co.jp/search/mall/{quote(keyword, safe='')}/"
        # アフィリエイトリンク変換（hb.afl.rakuten.co.jp経由）
        # pc: PCサイトURL, m: モバイルサイトURL (同じURLを使用)
        encoded_url = quote(search_url, safe='')
        return f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AFFILIATE_ID}/?pc={encoded_url}&m={encoded_url}"


# ============================================================
# Image Handler
# ============================================================

class ImageHandler:
    """Pollinations.aiを使用した無料画像生成・ローカル保存"""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        # Pollinations.aiはAPIキー不要

    # Pollinations.aiがレート制限時に返すダミー画像のハッシュ（検出用）
    KNOWN_DUMMY_HASHES = {
        "4d556a314fb0e51359234f0306a772ff",  # 71816バイトのダミー画像
        "0b7d78a042728ab7caa7a63fc4f1ca6a",  # 59537バイトのダミー画像
    }
    MIN_VALID_IMAGE_SIZE = 20_000  # 20KB未満はダミー画像と判定

    def generate_and_save_image(
        self,
        title: str,
        body: str,
        category: Category,
        article_id: str,
        output_dir: Path,
    ) -> str:
        """
        記事内容に基づいた画像をPollinations.aiで生成しローカルに保存。
        リトライ・ダミー画像検出・seed指定で信頼性を向上。
        
        Args:
            title: 記事タイトル
            body: 記事本文
            category: カテゴリー
            article_id: 記事ID（ファイル名用）
            output_dir: 画像保存先ディレクトリ (static/images/posts/)
        
        Returns:
            Hugo用の相対パス (例: /images/posts/2026-01-13-abc123.png)
        """
        import urllib.parse
        import hashlib
        import random

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # テキストモデルで画像生成用プロンプトを作成（リトライごとに再生成）
                prompt_en = self._generate_image_prompt(title, body, category)

                # seed値でユニーク性を確保
                seed = random.randint(1, 999999)
                encoded_prompt = urllib.parse.quote(prompt_en)
                pollinations_url = (
                    f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    f"?width=1280&height=720&nologo=true&seed={seed}"
                )

                print(f"  [Image] Attempt {attempt + 1}/{max_retries} (seed={seed})...")
                response = requests.get(pollinations_url, timeout=180)
                response.raise_for_status()

                if 'image' not in response.headers.get('content-type', ''):
                    raise ValueError(f"Invalid content type: {response.headers.get('content-type')}")

                image_data = response.content

                # ダミー画像検出: サイズチェック
                if len(image_data) < self.MIN_VALID_IMAGE_SIZE:
                    print(f"  [Image] Too small ({len(image_data)} bytes), likely a dummy. Retrying...")
                    time.sleep(5 * (attempt + 1))
                    continue

                # ダミー画像検出: 既知のハッシュチェック
                img_hash = hashlib.md5(image_data).hexdigest()
                if img_hash in self.KNOWN_DUMMY_HASHES:
                    print(f"  [Image] Known dummy image detected (hash={img_hash[:8]}...). Retrying...")
                    time.sleep(5 * (attempt + 1))
                    continue

                # 保存先ディレクトリ作成
                output_dir.mkdir(parents=True, exist_ok=True)

                # ファイル保存
                filename = f"{article_id}.jpg"
                file_path = output_dir / filename
                file_path.write_bytes(image_data)

                print(f"  [Image] Saved: {filename} ({len(image_data)} bytes, hash={img_hash[:8]}...)")
                return f"/images/posts/{filename}"

            except Exception as e:
                print(f"  [Image] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))

        print(f"  [Image] All {max_retries} attempts failed. Using fallback.")
        return "/images/og-default.png"

    def download_image_to_bytes(self, image_path_or_url: str, static_dir: Path) -> Optional[bytes]:
        """
        画像をバイトデータとして取得（Twitter投稿用）。
        
        Args:
            image_path_or_url: ローカルパス（/images/posts/xxx.png）またはURL
            static_dir: staticディレクトリのパス
        
        Returns:
            画像のバイトデータ
        """
        try:
            if image_path_or_url.startswith("http"):
                # URLの場合はダウンロード
                response = requests.get(image_path_or_url, timeout=30)
                response.raise_for_status()
                return response.content
            else:
                # ローカルパスの場合はファイル読み込み
                # /images/posts/xxx.png -> static/images/posts/xxx.png
                local_path = static_dir / image_path_or_url.lstrip("/")
                if local_path.exists():
                    return local_path.read_bytes()
                return None
        except Exception as e:
            print(f"  [Image] Failed to load: {e}")
            return None

    def _generate_image_prompt(self, title: str, body: str, category: Category) -> str:
        style_hint = {
            Category.MONEY: "premium AI workstation, GPU, laptop, buying guide style, no text",
            Category.NEWS: "news broadcast, breaking news style, professional, no text",
            Category.TOOL: "software interface, tech product, modern UI, no text",
            Category.GUIDE: "tutorial, educational diagram, clean design, no text",
        }.get(category, "technology")

        prompt = (
            "Create ONE English image generation prompt for a blog thumbnail.\n"
            "Rules:\n"
            "- Output ONE line only, no quotes\n"
            "- English only\n"
            "- MUST NOT include any text, logos, watermarks, QR codes, or UI elements\n"
            "- Focus on abstract visuals, technology imagery, or symbolic representations\n"
            f"- Style hint: {style_hint}\n"
            "- Make it modern, clean, professional\n\n"
            f"Blog title: {title}\n"
            f"Content preview: {body[:500]}\n"
        )

        try:
            response = self.model.generate_content(prompt)
            text = getattr(response, "text", None)
            if text:
                one_line = text.strip().splitlines()[0].strip().strip('"').strip("'")
                if one_line:
                    return one_line
        except Exception:
            pass

        # Fallback
        return f"Abstract futuristic technology visualization, {style_hint}, minimalist, high quality, 4k, no text"


# ============================================================
# Twitter (X) Poster
# ============================================================

class TwitterPoster:
    """X (Twitter) への自動投稿を行うクラス（無料プラン対応）"""

    def __init__(self) -> None:
        """
        環境変数から認証情報を読み込み、Tweepy Clientを初期化。
        
        必要な環境変数 (OAuth 1.0a):
          - TWITTER_API_KEY (Consumer Key)
          - TWITTER_API_SECRET (Consumer Secret)
          - TWITTER_ACCESS_TOKEN
          - TWITTER_ACCESS_TOKEN_SECRET
        
        オプション (OAuth 2.0 - 将来の拡張用):
          - TWITTER_CLIENT_ID
          - TWITTER_CLIENT_SECRET
        """
        if not TWEEPY_AVAILABLE:
            raise RuntimeError("tweepy is not installed. Run: pip install tweepy")

        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise RuntimeError("Twitter API credentials not configured in environment variables")

        # v1.1 API (for media upload - requires Basic plan $100/month)
        auth = tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
        )
        self.api_v1 = tweepy.API(auth)

        # v2 API (for tweeting - works with Free plan)
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

    def post_article(
        self,
        title: str,
        url: str,
        category: Category,
        viral_tags: Optional[str] = None,
        tweet_text: Optional[str] = None,
        hook_text: Optional[str] = None,
        summary_text: Optional[str] = None,
        question_text: Optional[str] = None,
        image_path: Optional[str] = None,
        static_dir: Optional[Path] = None,
        include_url: Optional[bool] = None,
    ) -> bool:
        """
        記事をTwitterに単一ツイートで投稿する（URL添付は収益意図で制御）。
        
        Geminiが生成したtweet_textをそのまま使用し、必要な場合のみURLとハッシュタグを付加。
        tweet_textがない場合（後方互換）はhook_text + summary_textでフォールバック。
        画像がある場合はメディア付きツイートとして投稿（インプレッション2-3倍）。

        Args:
            title: 記事タイトル
            url: 記事のURL
            category: 記事カテゴリー
            viral_tags: Geminiが選んだSNS拡散用ハッシュタグ
            tweet_text: Gemini生成の完全なツイート本文（120-220文字）
            hook_text: 冒頭のフック文（後方互換用フォールバック）
            summary_text: 3行要点（後方互換用フォールバック）
            question_text: リプライ誘発の質問文（後方互換用フォールバック）
            image_path: 画像パス（/images/posts/xxx.jpg）
            static_dir: staticディレクトリのパス
            include_url: Noneならカテゴリ/本文から自動判定

        Returns:
            投稿成功時True
        """
        try:
            # ===== ハッシュタグ構成（2つに削減: 多すぎるとスパム判定される） =====
            import random
            tags_list = []
            gemini_tags = []
            
            if viral_tags:
                # Gemini生成タグを収集（ビッグワード除外）
                big_words = ['#AI', '#生成AI', '#LLM', '#人工知能', '#ChatGPT', '#技術', '#ニュース']
                for tag in viral_tags.split():
                    if tag.startswith('#') and tag not in big_words:
                        gemini_tags.append(tag)
            
            # Gemini生成タグから最大1つ採用（記事固有のタグ）
            if gemini_tags:
                tags_list.append(gemini_tags[0])
            
            # カテゴリー別候補から1つ追加（合計2つ）
            niche_options = NICHE_HASHTAGS_STR.get(category.value, NICHE_HASHTAGS_STR["NEWS"])
            shuffled = random.sample(niche_options, len(niche_options))
            for tag in shuffled:
                if tag not in tags_list and len(tags_list) < 2:
                    tags_list.append(tag)
            
            # まだ2つ未満なら固定タグで補完
            for fixed_tag in FIXED_HASHTAGS:
                if fixed_tag not in tags_list and len(tags_list) < 2:
                    tags_list.append(fixed_tag)
            
            tag_str = ' '.join(tags_list[:2])
            if include_url is None:
                include_url = should_include_article_url(category, title, tweet_text, viral_tags)

            # ===== ツイート本文構成（Gemini生成 or フォールバック） =====
            if tweet_text:
                # Gemini生成のtweet_textをそのまま使用 + 必要な場合だけURL + ハッシュタグ
                parts = [tweet_text.strip()]
                if include_url:
                    parts.append(url)
                if tag_str:
                    parts.append(tag_str)
                full_tweet = "\n\n".join(parts)
            else:
                # 後方互換フォールバック: hook + summary + 必要な場合だけURL + ハッシュタグ
                hook = hook_text or title[:50]
                summary = summary_text or ""
                question = question_text or ""
                
                parts = [hook]
                if summary:
                    parts.append(summary)
                if question:
                    parts.append(question)
                if include_url:
                    parts.append(url)
                if tag_str:
                    parts.append(tag_str)
                
                full_tweet = '\n\n'.join(parts)

            print(f"  [Twitter] URL included: {'yes' if include_url else 'no'}")

            # ===== メディアアップロード（画像付きツイート） =====
            media_ids = None
            if image_path and static_dir and image_path != "/images/og-default.png":
                try:
                    local_path = static_dir / image_path.lstrip("/")
                    if local_path.exists():
                        import tempfile
                        # tweepyのmedia_uploadはファイルパスを受け取る
                        media = self.api_v1.media_upload(filename=str(local_path))
                        media_ids = [media.media_id]
                        print(f"  [Twitter] Image uploaded: {image_path}")
                    else:
                        print(f"  [Twitter] Image not found: {local_path}")
                except Exception as img_err:
                    print(f"  [Twitter] Image upload failed (posting without image): {img_err}")
                    media_ids = None

            # ===== ツイート投稿（メディア付き or テキストのみ） =====
            if media_ids:
                self.client.create_tweet(text=full_tweet, media_ids=media_ids)
                print(f"  [Twitter] Posted with image")
            else:
                self.client.create_tweet(text=full_tweet)

            return True

        except Exception as e:
            print(f"  [Twitter] Error: {e}")
            return False


def is_twitter_configured() -> bool:
    """Twitter API認証情報が設定されているか確認"""
    required = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    return all(os.getenv(key) for key in required)


def calculate_revenue_intent_score(
    title: str,
    tweet_text: Optional[str] = None,
    category: Optional[Category] = None,
    viral_tags: Optional[str] = None,
) -> int:
    """XでURLを付ける価値があるか判定するための収益意図スコア。"""
    text = f"{title} {tweet_text or ''} {viral_tags or ''}".lower()
    score = 0

    category_weights = {
        Category.MONEY: 8,
        Category.GUIDE: 4,
        Category.TOOL: 3,
        Category.NEWS: 0,
    }
    if category:
        score += category_weights.get(category, 0)

    for keyword in REVENUE_INTENT_KEYWORDS:
        if keyword.lower() in text:
            score += 2

    for keyword in ["おすすめ", "比較", "選び方", "価格", "料金", "買う", "購入", "レビュー", "導入", "構築", "スペック", "vram"]:
        if keyword.lower() in text:
            score += 3

    for keyword in LOW_REVENUE_NEWS_KEYWORDS:
        if keyword.lower() in text:
            score -= 3

    return score


def should_include_article_url(
    category: Category,
    title: str,
    tweet_text: Optional[str] = None,
    viral_tags: Optional[str] = None,
) -> bool:
    """URL直貼りを収益意図の高い投稿に限定する。"""
    score = calculate_revenue_intent_score(title, tweet_text, category, viral_tags)

    if category == Category.MONEY:
        return True
    if category == Category.GUIDE:
        return score >= 8
    if category == Category.TOOL:
        return score >= 9
    return score >= 12


def build_article_url(base_url: str, article_id: str, slug: Optional[str] = None) -> str:
    """slugがあればslug優先で記事URLを生成"""
    normalized_slug = (slug or "").strip()
    if normalized_slug:
        return f"{base_url}/posts/{normalized_slug}/"
    return f"{base_url}/posts/{article_id}/"


def resolve_article_url(
    repo_root: Path,
    article_id: str,
    base_url: str,
    fallback_url: Optional[str] = None,
) -> str:
    """Front Matterのslugを参照して記事URLを解決（なければfallback）"""
    posts_dir = repo_root / "content" / "posts"
    md_path = posts_dir / f"{article_id}.md"
    slug = None

    try:
        if md_path.exists():
            raw = md_path.read_text(encoding="utf-8")
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    slug_match = re.search(
                        r'^\s*slug:\s*["\']?(.+?)["\']?\s*$',
                        front_matter,
                        re.MULTILINE,
                    )
                    if slug_match:
                        slug = slug_match.group(1).strip()
    except Exception:
        pass

    if slug:
        return build_article_url(base_url, article_id, slug)
    if fallback_url:
        return fallback_url
    return build_article_url(base_url, article_id)


# ============================================================
# Internal Link Injection (内部リンク自動挿入)
# ============================================================

def find_related_articles(posts_dir: Path, current_title: str, current_tags: List[str], max_results: int = 3) -> List[dict]:
    """
    既存記事から関連する記事を見つけて返す。
    タグの重複度とタイトルのキーワード一致度でスコアリング。
    
    Returns:
        [{"title": str, "url": str, "score": int}, ...]
    """
    if not posts_dir.exists():
        return []
    
    current_tags_set = set(t.lower() for t in current_tags)
    current_words = set(re.findall(r'[\w]+', current_title.lower()))
    # 汎用的すぎる単語は除外
    stop_words = {'の', 'を', 'に', 'は', 'が', 'で', 'と', 'する', 'した', 'ai', 'について', '方法', '入門', 'する方法'}
    current_words -= stop_words
    
    candidates = []
    
    for md_file in posts_dir.glob("*.md"):
        try:
            # ファイル先頭部分だけ読み込み（Front Matterのみ必要）
            raw = md_file.read_text(encoding="utf-8")
            if not raw.startswith("---"):
                continue
            parts = raw.split("---", 2)
            if len(parts) < 3:
                continue
            
            front_matter = parts[1]
            
            # タイトル抽出
            title_match = re.search(r'title:\s*["\'](.+?)["\']', front_matter)
            if not title_match:
                continue
            title = title_match.group(1)
            
            # 自分自身を除外
            if title == current_title:
                continue
            
            # slug抽出（あれば）
            slug_match = re.search(r'slug:\s*["\'](.+?)["\']', front_matter)
            article_id = md_file.stem  # ファイル名（拡張子なし）
            
            # タグ抽出
            tags = []
            tag_matches = re.findall(r'^\s+-\s+"(.+?)"', front_matter, re.MULTILINE)
            # categoriesの後のtagsセクションからのみ取得
            tag_section = re.search(r'tags:\s*\n((?:\s+-\s+".+?"\n?)+)', front_matter)
            if tag_section:
                tags = re.findall(r'"\s*(.+?)\s*"', tag_section.group(1))
            
            tags_set = set(t.lower() for t in tags)
            
            # スコアリング
            score = 0
            # タグの重複（1タグにつき+3点）
            tag_overlap = current_tags_set & tags_set
            score += len(tag_overlap) * 3
            
            # タイトルのキーワード一致（1ワードにつき+2点）
            other_words = set(re.findall(r'[\w]+', title.lower())) - stop_words
            word_overlap = current_words & other_words
            score += len(word_overlap) * 2
            
            if score > 0:
                url = f"/posts/{article_id}/"
                candidates.append({"title": title, "url": url, "score": score})
        
        except Exception:
            continue
    
    # スコア降順でソート、上位max_results件を返す
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:max_results]


def inject_internal_links(body: str, related_articles: List[dict]) -> str:
    """
    記事本文の末尾（アフィリエイトセクションの前）に「あわせて読みたい」セクションを挿入。
    """
    if not related_articles:
        return body
    
    links = []
    for article in related_articles:
        links.append(f'- [{article["title"]}]({article["url"]})')
    
    section = f'\n\n---\n\n## あわせて読みたい\n\n' + '\n'.join(links) + '\n'
    
    # アフィリエイトセクション（---の後の推薦部分）の前に挿入
    # 末尾の --- で始まるアフィリエイトブロックを探す
    affiliate_match = re.search(r'\n---\n\n(?:##\s*(?:関連商品|おすすめ|この記事).+)', body)
    if affiliate_match:
        insert_pos = affiliate_match.start()
        return body[:insert_pos] + section + body[insert_pos:]
    
    # アフィリエイトセクションがなければ末尾に追加
    return body + section


def inject_faq_schema(body: str, article_url: str) -> str:
    """
    記事本文から「## よくある質問」セクションを解析し、
    FAQ構造化データ（JSON-LD）を記事末尾に挿入する。
    Google検索のリッチスニペット（FAQ表示）に対応。
    """
    # よくある質問セクションを検出
    faq_section_match = re.search(
        r'##\s*よくある質問\s*\n(.*?)(?=\n##\s[^#]|\Z)',
        body,
        re.DOTALL
    )
    if not faq_section_match:
        return body
    
    faq_text = faq_section_match.group(1)
    
    # Q&Aペアを抽出（### Q1: 質問 → 回答の形式）
    qa_pairs = re.findall(
        r'###\s*Q\d+:\s*(.+?)\n\n((?:(?!###).)+)',
        faq_text,
        re.DOTALL
    )
    
    if not qa_pairs:
        return body
    
    # JSON-LD生成
    faq_items = []
    for question, answer in qa_pairs:
        q = question.strip()
        a = answer.strip()
        # マークダウン記法を除去
        a = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', a)  # リンク除去
        a = re.sub(r'[*_`]', '', a)  # 強調記法除去
        a = re.sub(r'\n+', ' ', a)  # 改行をスペースに
        
        faq_items.append(f'''    {{
      "@type": "Question",
      "name": {json.dumps(q, ensure_ascii=False)},
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": {json.dumps(a, ensure_ascii=False)}
      }}
    }}''')
    
    if not faq_items:
        return body
    
    joiner = ",\n"
    schema = f'''
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{joiner.join(faq_items)}
  ]
}}
</script>
'''
    
    return body + schema


# ============================================================
# Hugo Markdown Writer
# ============================================================

def write_hugo_markdown(
    out_path: Path,
    title: str,
    date_jst: datetime,
    image_url: str,
    category: Category,
    tags: List[str],
    body: str,
    description: Optional[str] = None,
    slug: Optional[str] = None,
) -> None:
    """Hugo形式のMarkdownファイルを出力（PaperModテーマ対応）"""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # カテゴリー名をHugo用に変換
    category_map = {
        Category.MONEY: "AI Buyer Guide",
        Category.NEWS: "AI News",
        Category.TOOL: "AI Tools",
        Category.GUIDE: "AI Guide",
    }
    category_name = category_map.get(category, "AI News")

    # descriptionをサニタイズ（ダブルクォート、改行を除去）
    safe_description = ""
    if description:
        safe_description = description.replace('"', "'").replace('\n', ' ').strip()
    
    # PaperModテーマはcover.imageを使用
    fm_lines = [
        "---",
        f'title: "{title.replace(chr(34), "")}"',
        f"date: {date_jst.isoformat()}",
    ]
    
    # slugがあれば追加（SEOフレンドリーURL用）
    if slug:
        fm_lines.append(f'slug: "{slug}"')
    
    # descriptionがあれば追加（⚠️💡が含まれていないことを確認）
    if safe_description and not any(emoji in safe_description for emoji in ['⚠️', '💡', '>']):
        fm_lines.append(f'description: "{safe_description}"')
    
    fm_lines.extend([
        "cover:",
        f'  image: "{image_url}"',
        "  alt: \"AI generated thumbnail\"",
        "  relative: false",
        "categories:",
        f'  - "{category_name}"',
        "tags:",
        *[f'  - "{t}"' for t in tags],
        "---",
        "",
    ])

    content = "\n".join(fm_lines) + body.strip() + "\n"
    out_path.write_text(content, encoding="utf-8")


# ============================================================
# Twitter Posting Queue (デプロイ後投稿用)
# ============================================================

@dataclass
class TwitterQueueItem:
    """X投稿キューのアイテム"""
    article_id: str
    title: str
    url: str
    category: str  # "MONEY", "NEWS", "TOOL", "GUIDE"
    viral_tags: Optional[str]
    tweet_text: Optional[str] = None  # Gemini生成の完全なツイート本文
    hook_text: Optional[str] = None  # 後方互換用
    summary_text: Optional[str] = None  # 後方互換用
    question_text: Optional[str] = None  # 後方互換用
    image_path: Optional[str] = None  # 画像パス（/images/posts/xxx.jpg）
    created_at: str = ""


class TwitterPostingQueue:
    """X投稿キューの管理（JSON永続化）"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._queue: List[Dict] = []

    def load(self) -> List[Dict]:
        if not self.path.exists():
            self._queue = []
            return self._queue
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._queue = data if isinstance(data, list) else []
        except Exception:
            self._queue = []
        return self._queue

    def add(self, item: TwitterQueueItem) -> None:
        if not self._queue:
            self.load()
        self._queue.append({
            "article_id": item.article_id,
            "title": item.title,
            "url": item.url,
            "category": item.category,
            "viral_tags": item.viral_tags,
            "tweet_text": item.tweet_text,
            "hook_text": item.hook_text,
            "summary_text": item.summary_text,
            "question_text": item.question_text,
            "image_path": item.image_path,
            "created_at": item.created_at,
            "posted": False,
        })
        self._save()

    def get_pending(self) -> List[Dict]:
        if not self._queue:
            self.load()
        return [item for item in self._queue if not item.get("posted", False)]

    def prune_old_pending(self, max_age_hours: int = 36) -> int:
        """古い未投稿アイテムをキューから削除する（API停止時のバックログ対策）。"""
        if not self._queue:
            self.load()

        now = datetime.now(JST)
        cutoff = now - timedelta(hours=max_age_hours)
        kept: List[Dict] = []
        removed = 0

        for item in self._queue:
            if item.get("posted", False):
                kept.append(item)
                continue

            created_str = item.get("created_at", "")
            try:
                created = datetime.fromisoformat(created_str)
            except Exception:
                removed += 1
                continue

            if created < cutoff:
                removed += 1
            else:
                kept.append(item)

        if removed:
            self._queue = kept
            self._save()

        return removed

    def mark_posted(self, article_id: str) -> None:
        if not self._queue:
            self.load()
        for item in self._queue:
            if item["article_id"] == article_id:
                item["posted"] = True
        self._save()

    def get_by_id(self, article_id: str) -> Optional[Dict]:
        if not self._queue:
            self.load()
        for item in self._queue:
            if item["article_id"] == article_id:
                return item
        return None

    def update_url(self, article_id: str, url: str) -> None:
        if not self._queue:
            self.load()
        for item in self._queue:
            if item["article_id"] == article_id:
                item["url"] = url
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._queue, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def post_single_article_to_twitter(article_id: str) -> int:
    """
    指定した記事IDをXに投稿する（デプロイ完了後に使用）。
    
    Usage: python auto_generate.py --post-twitter 2026-01-14-abc12345
    """
    print("=" * 60)
    print("Negi AI Lab - Post to X (Twitter)")
    print("=" * 60)
    print(f"Article ID: {article_id}")
    print()

    # キューから記事情報を取得
    repo_root = Path(__file__).resolve().parent
    queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
    queue.load()

    item = queue.get_by_id(article_id)
    if not item:
        print(f"[ERROR] Article ID '{article_id}' not found in queue.")
        print("  Run article generation first, or check twitter_queue.json")
        return 1

    if item.get("posted", False):
        print(f"[WARN] Article already posted to X.")
        return 0

    # Twitter認証チェック
    if not is_twitter_configured():
        print("[ERROR] Twitter API credentials not configured.")
        return 2

    if not TWEEPY_AVAILABLE:
        print("[ERROR] tweepy is not installed.")
        return 2

    try:
        poster = TwitterPoster()
        
        # カテゴリー文字列をEnumに変換
        category_map = {
            "MONEY": Category.MONEY,
            "NEWS": Category.NEWS,
            "TOOL": Category.TOOL,
            "GUIDE": Category.GUIDE,
        }
        category = category_map.get(item["category"], Category.NEWS)

        # slugがある場合は正しいURLに補正
        article_url = resolve_article_url(repo_root, article_id, SITE_BASE_URL, item.get("url"))
        if article_url != item.get("url"):
            queue.update_url(article_id, article_url)

        success = poster.post_article(
            title=item["title"],
            url=article_url,
            category=category,
            viral_tags=item.get("viral_tags"),
            tweet_text=item.get("tweet_text"),
            hook_text=item.get("hook_text"),
            summary_text=item.get("summary_text"),
            question_text=item.get("question_text"),
            image_path=item.get("image_path"),
            static_dir=repo_root / "static",
        )

        if success:
            queue.mark_posted(article_id)
            print(f"✓ Successfully posted to X!")
            print(f"  Title: {item['title'][:50]}...")
            print(f"  URL: {article_url}")
            return 0
        else:
            print("✗ Failed to post to X.")
            return 1

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def post_all_pending_to_twitter() -> int:
    """
    キュー内の未投稿記事から、収益意図が高いものだけXに投稿する。
    古い未投稿は削除し、API停止期間のバックログを一気に流さない。

    投稿管理:
    - daily_stats.jsonで1日の投稿数を追跡
    - MAX_TWEETS_PER_DAY(デフォルト2)まで投稿可能
    - MAX_TWEETS_PER_RUN(デフォルト1)で1回の投稿数を制限
    - MAX_URL_TWEETS_PER_DAY(デフォルト1)でURL直貼りを抑制
    - MONEY/GUIDE/TOOLの収益意図順に選ぶ

    Usage: python auto_generate.py --post-all-twitter
    """
    print("=" * 60)
    print("Negi AI Lab - Post All Pending to X")
    print("=" * 60)

    max_tweets_per_day = int(os.environ.get("MAX_TWEETS_PER_DAY", "2"))
    max_tweets_per_run = int(os.environ.get("MAX_TWEETS_PER_RUN", "1"))
    max_url_tweets_per_day = int(os.environ.get("MAX_URL_TWEETS_PER_DAY", "1"))
    stale_pending_hours = int(os.environ.get("STALE_PENDING_HOURS", "36"))
    enable_image_upload = os.environ.get("ENABLE_IMAGE_UPLOAD", "true").lower() == "true"

    repo_root = Path(__file__).resolve().parent
    stats_path = repo_root / "daily_stats.json"
    today_str = get_daily_date()
    daily_stats: Dict[str, object] = {}
    if stats_path.exists():
        try:
            daily_stats = json.loads(stats_path.read_text(encoding="utf-8"))
        except Exception:
            daily_stats = {}

    today_entry = daily_stats.get(today_str, {}) if isinstance(daily_stats.get(today_str, {}), dict) else {}
    today_posted = int(today_entry.get("tweets_posted", 0))
    today_url_posted = int(today_entry.get("url_tweets_posted", 0))
    remaining_budget = min(max_tweets_per_day - today_posted, max_tweets_per_run)
    remaining_url_budget = max(0, max_url_tweets_per_day - today_url_posted)

    if remaining_budget <= 0:
        print(f"Daily tweet limit reached ({max_tweets_per_day}/day). Skipping.")
        return 0

    queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
    removed_old = queue.prune_old_pending(stale_pending_hours)
    if removed_old:
        print(f"Removed {removed_old} stale pending queue items older than {stale_pending_hours}h.")

    pending = queue.get_pending()
    if not pending:
        print("No recent pending articles to post.")
        return 0

    category_map = {
        "MONEY": Category.MONEY,
        "NEWS": Category.NEWS,
        "TOOL": Category.TOOL,
        "GUIDE": Category.GUIDE,
    }

    def tweet_quality_score(item: Dict) -> int:
        category = category_map.get(item.get("category"), Category.NEWS)
        score = calculate_revenue_intent_score(
            item.get("title", ""),
            item.get("tweet_text"),
            category,
            item.get("viral_tags"),
        ) * 10
        if item.get("tweet_text"):
            score += 60
            text_len = len(item["tweet_text"])
            if 80 <= text_len <= 240:
                score += 20
        elif item.get("hook_text"):
            score += 20
        if item.get("image_path") and item["image_path"] != "/images/og-default.png":
            score += 10
        return score

    pending.sort(key=tweet_quality_score, reverse=True)
    selected: List[Dict] = []
    include_url_by_id: Dict[str, bool] = {}
    url_slots_used = 0

    for item in pending:
        if len(selected) >= remaining_budget:
            break

        category = category_map.get(item.get("category"), Category.NEWS)
        include_url = should_include_article_url(
            category,
            item.get("title", ""),
            item.get("tweet_text"),
            item.get("viral_tags"),
        )

        if include_url:
            if url_slots_used >= remaining_url_budget:
                continue
            url_slots_used += 1

        selected.append(item)
        include_url_by_id[item["article_id"]] = include_url

    print(
        f"Found {len(pending)} pending articles. Will post {len(selected)} "
        f"(run budget: {remaining_budget}, URL budget: {remaining_url_budget})."
    )
    skipped_count = max(0, len(pending) - len(selected))
    if skipped_count:
        print(f"  [INFO] {skipped_count} pending items kept for later or stale-prune, not mass-posted.")
    print()

    if not selected:
        print("No selected articles after URL/throttle rules.")
        return 0

    if not is_twitter_configured() or not TWEEPY_AVAILABLE:
        print("[ERROR] Twitter not configured or tweepy not installed.")
        return 2

    poster = TwitterPoster()
    success_count = 0
    failed_count = 0
    successful_url_count = 0

    for item in selected:
        print(f"Posting: {item['title'][:40]}...")

        category = category_map.get(item.get("category"), Category.NEWS)

        article_url = resolve_article_url(repo_root, item["article_id"], SITE_BASE_URL, item.get("url"))
        if article_url != item.get("url"):
            queue.update_url(item["article_id"], article_url)

        image_path_for_post = item.get("image_path") if enable_image_upload else None
        include_url = include_url_by_id.get(item["article_id"], False)

        if poster.post_article(
            title=item["title"],
            url=article_url,
            category=category,
            viral_tags=item.get("viral_tags"),
            tweet_text=item.get("tweet_text"),
            hook_text=item.get("hook_text"),
            summary_text=item.get("summary_text"),
            question_text=item.get("question_text"),
            image_path=image_path_for_post,
            static_dir=repo_root / "static",
            include_url=include_url,
        ):
            queue.mark_posted(item["article_id"])
            print("  ✓ Posted!")
            success_count += 1
            if include_url:
                successful_url_count += 1
        else:
            print("  ✗ Failed")
            failed_count += 1

        time.sleep(5)

    if today_str not in daily_stats or not isinstance(daily_stats.get(today_str), dict):
        daily_stats[today_str] = {}
    daily_stats[today_str]["tweets_posted"] = today_posted + success_count
    daily_stats[today_str]["url_tweets_posted"] = today_url_posted + successful_url_count

    cutoff_date = (datetime.now(JST) - timedelta(days=7)).strftime("%Y-%m-%d")
    daily_stats = {
        k: v for k, v in daily_stats.items()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(k)) or k >= cutoff_date
    }
    stats_path.write_text(json.dumps(daily_stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print()
    print(
        f"Posted {success_count}/{len(selected)} articles. "
        f"(Total today: {today_posted + success_count}/{max_tweets_per_day}, "
        f"URL today: {today_url_posted + successful_url_count}/{max_url_tweets_per_day})"
    )

    return 0


# ============================================================
# Weekly Digest Generator
# ============================================================

def generate_weekly_digest() -> int:
    """
    過去1週間の記事から週間ダイジェストを自動生成。
    
    毎週日曜日に実行して「今週のAIニュース TOP10」を生成。
    """
    print("=" * 60)
    print("Negi AI Lab - Weekly Digest Generator")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent
    posts_dir = repo_root / "content" / "posts"
    
    print(f"[DEBUG] Looking for posts in: {posts_dir}")
    print(f"[DEBUG] Posts directory exists: {posts_dir.exists()}")
    
    if posts_dir.exists():
        all_md_files = list(posts_dir.glob("*.md"))
        print(f"[DEBUG] Total .md files found: {len(all_md_files)}")
    
    # API Key check
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set.")
        return 2

    # 過去7日間の記事を収集
    now = datetime.now(JST)
    week_ago = now - timedelta(days=7)
    print(f"[DEBUG] Collecting articles from {week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    
    weekly_articles = []
    
    for md_file in posts_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            
            # Front Matter から情報抽出
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]
                    
                    # 日付抽出
                    date_match = re.search(r'date:\s*["\']?(\d{4}-\d{2}-\d{2})', front_matter)
                    if not date_match:
                        continue
                    
                    article_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    article_date = article_date.replace(tzinfo=JST)
                    
                    # 1週間以内の記事のみ
                    if article_date < week_ago:
                        continue
                    
                    # ダイジェスト記事自体は除外
                    if "週間ダイジェスト" in content or "weekly-digest" in md_file.name:
                        continue
                    
                    # タイトル抽出
                    title_match = re.search(r'title:\s*["\'](.+?)["\']', front_matter)
                    title = title_match.group(1) if title_match else md_file.stem
                    
                    # カテゴリー抽出
                    cat_match = re.search(r'categories:\s*\n\s*-\s*(\w+)', front_matter)
                    category = cat_match.group(1) if cat_match else "NEWS"
                    
                    # 概要（最初の200文字）
                    summary = body.strip()[:200].replace("\n", " ")
                    
                    weekly_articles.append({
                        "title": title,
                        "date": article_date,
                        "category": category,
                        "summary": summary,
                        "filename": md_file.name,
                    })
        except Exception as e:
            print(f"  [!] Error reading {md_file.name}: {e}")
            continue
    
    if len(weekly_articles) < 3:
        print(f"Not enough articles for digest ({len(weekly_articles)} found, need at least 3)")
        return 1
    
    # 日付降順でソート
    weekly_articles.sort(key=lambda x: x["date"], reverse=True)
    top_articles = weekly_articles[:10]
    
    print(f"Found {len(weekly_articles)} articles from past week")
    print(f"Creating digest with top {len(top_articles)} articles")
    
    # Gemini APIでダイジェスト記事を生成
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    
    # 記事リスト作成
    article_list = ""
    for i, art in enumerate(top_articles, 1):
        article_list += f"{i}. 【{art['category']}】{art['title']}\n   概要: {art['summary'][:100]}...\n\n"
    
    week_start = week_ago.strftime("%m/%d")
    week_end = now.strftime("%m/%d")
    
    prompt = f'''あなたはAI専門メディア「Negi AI Lab」の編集者です。
今週({week_start}〜{week_end})の記事から週間ダイジェストを作成してください。

## 今週の記事一覧：
{article_list}

## 作成ルール：
1. タイトルは「【週間ダイジェスト】{week_end}週：今週のAI注目ニュースTOP{len(top_articles)}」
2. 導入文で今週のAIトレンドを総括（200文字程度）
3. 各記事を「ニュース」「ツール」「ガイド」のセクションに分類
4. 各記事について2-3行の解説を追加
5. 最後に「来週の注目トピック」予測を追加
6. 読者が内部リンクから詳細を読みたくなるように誘導

## 出力形式：
Markdown形式で本文のみ出力してください。
Front Matterは不要です。

[SHOPPING: AI 人工知能 週刊まとめ]
[HASHTAGS: #AI #人工知能 #週間まとめ #AIニュース]
'''

    try:
        response = model.generate_content(prompt)
        digest_body = response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini API error: {e}")
        return 1
    
    # Front Matter作成
    article_id = f"weekly-digest-{now.strftime('%Y-%m-%d')}"
    
    front_matter = f'''---
title: "【週間ダイジェスト】{week_end}週：今週のAI注目ニュースTOP{len(top_articles)}"
date: {now.strftime('%Y-%m-%dT%H:%M:%S+09:00')}
draft: false
categories:
  - GUIDE
tags:
  - 週間ダイジェスト
  - まとめ
  - AIニュース
description: "{week_start}〜{week_end}のAI関連ニュース・ツール・ガイドをまとめてお届け"
cover:
  image: "/images/posts/{article_id}.png"
  alt: "週間ダイジェスト {week_end}"
  relative: false
---

'''
    
    # 記事保存
    output_path = posts_dir / f"{now.strftime('%Y-%m-%d')}-{article_id}.md"
    output_path.write_text(front_matter + digest_body, encoding="utf-8")
    
    print(f"✓ Digest saved: {output_path.name}")
    
    # 画像生成 (Pollinations.ai - 無料、APIキー不要)
    try:
        import urllib.parse
        image_prompt = f"Weekly AI news digest infographic, modern tech style, blue and green gradient, abstract visualization, no text, no logos, professional, {week_end}"
        encoded_prompt = urllib.parse.quote(image_prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
        
        response = requests.get(pollinations_url, timeout=120)
        response.raise_for_status()
        
        if 'image' not in response.headers.get('content-type', ''):
            raise ValueError(f"Invalid content type: {response.headers.get('content-type')}")
        
        image_data = response.content
        
        images_dir = repo_root / "static" / "images" / "posts"
        images_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{article_id}.jpg"
        image_path.write_bytes(image_data)
        
        print(f"✓ Image saved: {image_path.name}")
    except Exception as e:
        print(f"  [!] Image generation failed: {e}")
    
    print()
    print("=" * 60)
    print("Weekly digest generated successfully!")
    print("=" * 60)
    
    return 0


# ============================================================
# Fallback Logic Calculator
# ============================================================

def calculate_targets_with_fallback(
    total: int,
    available: Dict[Category, int],
    daily_remaining: Optional[Dict[str, int]] = None,
    pool: Optional[NewsPool] = None,
) -> Dict[Category, int]:
    """
    1日の残り枠、時間帯優先度、プールを考慮した目標数計算。

    戦略:
    - 時間帯に応じた優先順位でカテゴリーを選択
    - 1回の実行では各カテゴリー最大1記事ずつ（バランス重視）
    - フィードにネタがなければプールから補充
    - 枠が埋まっているカテゴリーはスキップ

    Args:
        total: 今回生成する記事数
        available: 各カテゴリーで利用可能な記事数（フィードから取得できた数）
        daily_remaining: 1日の残り枠（None の場合は制限なし）
        pool: ネタプール（フィードにネタがない場合のフォールバック）

    Returns:
        各カテゴリーで実際に生成する記事数
    """
    # 1日の残り枠（指定がなければ無制限）
    if daily_remaining is None:
        remaining = {cat.value: 999 for cat in Category}
    else:
        remaining = daily_remaining.copy()

    print("  [DEBUG] Daily remaining: " + ", ".join(f"{cat.value}={remaining.get(cat.value, 0)}" for cat in Category))

    # プールからの補充可能数を加算
    pool_available = {cat: 0 for cat in Category}
    if pool:
        pool_stats = pool.get_pool_stats()
        pool_available = {cat: pool_stats.get(cat.value, 0) for cat in Category}
        print("  [DEBUG] Pool available: " + ", ".join(f"{cat.value}={pool_available[cat]}" for cat in Category))

    # 各カテゴリーの実際の上限 = min(残り枠, フィード+プール)
    effective_available = {
        cat: min(remaining.get(cat.value, 0), available.get(cat, 0) + pool_available.get(cat, 0))
        for cat in Category
    }

    # 時間帯に応じた優先順位を取得
    priority_order = get_current_priority()
    current_hour = datetime.now(JST).hour
    print(f"  [DEBUG] Current hour: {current_hour}:00 JST, Priority: {[c.value for c in priority_order]}")

    # ラウンドロビン方式：優先順位順に各カテゴリーから1つずつ取る
    final = {cat: 0 for cat in Category}
    slots_left = total
    round_num = 0
    
    while slots_left > 0:
        made_progress = False
        for cat in priority_order:
            if slots_left <= 0:
                break
            if final[cat] < effective_available[cat]:
                final[cat] += 1
                slots_left -= 1
                made_progress = True
        
        # どのカテゴリーも追加できなければ終了
        if not made_progress:
            break
        
        round_num += 1
        if round_num > 10:  # 安全装置
            break

    return final


# ============================================================
# Main Entry Point
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Negi AI Lab - Auto Article Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--total", "-n",
        type=int,
        default=DEFAULT_TOTAL_ARTICLES,
        help=f"合計生成記事数 (default: {DEFAULT_TOTAL_ARTICLES})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="APIを叩かず、収集とフォールバック計算のシミュレーションのみ実行",
    )
    parser.add_argument(
        "--test-one",
        action="store_true",
        help="最初の1件だけ実際に生成して品質確認",
    )
    parser.add_argument(
        "--skip-twitter",
        action="store_true",
        help="X (Twitter) への投稿をスキップ（GitHub Actions用）",
    )
    parser.add_argument(
        "--post-twitter",
        type=str,
        metavar="ARTICLE_ID",
        help="指定した記事IDをXに投稿（デプロイ完了後に使用）",
    )
    parser.add_argument(
        "--post-all-twitter",
        action="store_true",
        help="キュー内の未投稿記事をすべてXに投稿",
    )
    parser.add_argument(
        "--weekly-digest",
        action="store_true",
        help="過去1週間の記事から週間ダイジェストを生成",
    )

    args = parser.parse_args()
    
    # --weekly-digest モードの場合は専用処理
    if args.weekly_digest:
        return generate_weekly_digest()
    
    # --post-twitter モードの場合は専用処理
    if args.post_twitter:
        return post_single_article_to_twitter(args.post_twitter)
    
    # --post-all-twitter モードの場合は専用処理
    if args.post_all_twitter:
        return post_all_pending_to_twitter()
    
    total = args.total
    dry_run = args.dry_run
    test_one = args.test_one
    skip_twitter = args.skip_twitter

    print("=" * 60)
    print("Negi AI Lab - Auto Article Generator")
    print("=" * 60)
    print(f"Total target: {total} articles")
    print(f"Mode: {'DRY-RUN' if dry_run else ('TEST-ONE' if test_one else 'FULL')}")
    print()

    repo_root = Path(__file__).resolve().parent
    processed_store = ProcessedURLStore(repo_root / "processed_urls.json")
    processed_store.load()
    
    # 1日の生成状況を追跡
    daily_stats = DailyStatsStore(repo_root / "daily_stats.json")
    daily_stats.load()
    print(f"[INFO] Today's progress: {daily_stats.get_stats_summary()}")
    
    # ネタプール初期化
    news_pool = NewsPool(repo_root / "news_pool.json", processed_store)
    news_pool.load()
    pool_stats = news_pool.get_pool_stats()
    pool_summary = ", ".join(f"{cat.value}:{pool_stats.get(cat.value, 0)}" for cat in Category)
    print(f"[INFO] News pool: {pool_stats['total']} items ({pool_summary})")

    # API Key check (dry-run以外で必須)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not dry_run:
        print("[ERROR] GEMINI_API_KEY is not set.")
        return 2

    # -------------------------
    # Step 1: Collect items from feeds (& add to pool)
    # -------------------------
    print("[Step 1] Collecting news items...")
    collector = NewsCollector(processed_store, pool=news_pool)

    collect_count = max(total * 3, 3)
    money_items = collector.collect_money(max_items=collect_count)
    news_items = collector.collect_news(max_items=collect_count)  # プール蓄積のため多めに
    tool_items = collector.collect_tools(max_items=collect_count)
    guide_items = collector.collect_guides(max_items=collect_count)
    
    # プールを保存（新しいアイテムを蓄積）
    news_pool.save()

    available = {
        Category.MONEY: len(money_items),
        Category.NEWS: len(news_items),
        Category.TOOL: len(tool_items),
        Category.GUIDE: len(guide_items),
    }

    for cat in get_current_priority():
        print(f"  {cat.value:<5}: {available.get(cat, 0)} items found")
    print()

    # -------------------------
    # Step 2: Calculate with fallback (1日の残り枠 + 時間帯優先度 + プール)
    # -------------------------
    print("[Step 2] Calculating targets with daily quota...")
    daily_remaining = daily_stats.get_remaining()
    targets = calculate_targets_with_fallback(total, available, daily_remaining, pool=news_pool)

    for cat in get_current_priority():
        print(f"  {cat.value:<5}: {targets[cat]} (daily remaining: {daily_remaining.get(cat.value, 0)})")
    print(f"  Total: {sum(targets.values())}")
    print()

    # -------------------------
    # Build final item list (フィードから優先、足りなければプールから)
    # -------------------------
    final_items: List[NewsItem] = []

    items_by_category = {
        Category.MONEY: money_items,
        Category.NEWS: news_items,
        Category.TOOL: tool_items,
        Category.GUIDE: guide_items,
    }

    for cat in get_current_priority():
        needed = targets[cat]
        direct_items = items_by_category.get(cat, [])[:needed]
        final_items.extend(direct_items)

        if len(direct_items) < needed:
            pool_items = news_pool.get_items_for_category(
                cat,
                needed - len(direct_items),
                fresh_first=(cat != Category.GUIDE),
            )
            final_items.extend(pool_items)
            if pool_items:
                print(f"  [INFO] {cat.value}: {len(pool_items)} items from pool")

    # -------------------------
    # Dry-run: Show simulation and exit
    # -------------------------
    if dry_run:
        print("[DRY-RUN] Simulation Results:")
        print("-" * 60)
        for i, item in enumerate(final_items, 1):
            print(f"{i:2}. [{item.category.value:5}] {item.title[:50]}...")
            print(f"     Source: {item.source}")
            print(f"     URL: {item.url[:60]}...")
            print(f"     [DryRun] Would post to X: {item.title[:40]}...")
            print()
        print("-" * 60)
        print(f"Total: {len(final_items)} articles would be generated.")
        print("(No files written, no URLs logged, no X posts)")
        return 0

    # -------------------------
    # Step 3: Generate articles
    # -------------------------
    if not final_items:
        print("[!] No items to generate.")
        return 0

    generator = ArticleGenerator(api_key=api_key, model_name="gemini-3-flash-preview")
    image_handler = ImageHandler(api_key=api_key, model_name="gemini-3-flash-preview")
    out_dir = repo_root / "content" / "posts"
    static_dir = repo_root / "static"
    images_dir = static_dir / "images" / "posts"

    # Twitter Poster (optional)
    twitter_poster: Optional[TwitterPoster] = None
    twitter_enabled = is_twitter_configured() and TWEEPY_AVAILABLE
    if twitter_enabled:
        try:
            twitter_poster = TwitterPoster()
            print("[Twitter] API configured and ready.")
        except Exception as e:
            print(f"[Twitter] Disabled: {e}")
            twitter_poster = None
    else:
        if not TWEEPY_AVAILABLE:
            print("[Twitter] Disabled: tweepy not installed")
        else:
            print("[Twitter] Disabled: API credentials not configured")

    # test-one: 1件だけ
    if test_one:
        final_items = final_items[:1]
        print("[TEST-ONE] Generating 1 article only...")
    else:
        print(f"[Step 3] Generating {len(final_items)} articles...")

    print()

    success_count = 0
    twitter_success = 0
    for idx, item in enumerate(final_items, 1):
        print(f"[{idx}/{len(final_items)}] Generating: {item.title[:40]}...")

        try:
            # Generate article (returns ArticleResult)
            result = generator.generate_article(item)

            # Prepare output
            now_jst = datetime.now(JST)
            date_midnight = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
            ymd = date_midnight.strftime("%Y-%m-%d")

            article_id = f"{ymd}-{result.slug}" if result.slug else f"{ymd}-{uuid.uuid4().hex[:8]}"
            filename = f"{article_id}.md"
            out_path = out_dir / filename

            # Generate and save image locally
            print(f"  Generating image...")
            image_path = image_handler.generate_and_save_image(
                title=result.title,
                body=result.body,
                category=item.category,
                article_id=article_id,
                output_dir=images_dir,
            )

            # Determine tags for Hugo front matter (Gemini SEOタグ優先)
            if result.seo_tags:
                tags = result.seo_tags[:5]  # 最大5つ
            else:
                # フォールバック: カテゴリー別デフォルト
                tags = ["GenAI"]
                if item.category == Category.NEWS:
                    tags.extend(["速報", "AIニュース"])
                elif item.category == Category.TOOL:
                    tags.extend(["ツール", "レビュー"])
                else:
                    tags.extend(["ガイド", "チュートリアル"])

            # 内部リンク挿入（既存記事から関連記事を検索）
            related = find_related_articles(out_dir, result.title, tags)
            if related:
                result.body = inject_internal_links(result.body, related)
                print(f"    Internal links: {len(related)} related articles linked")

            # FAQ構造化データ挿入（Googleリッチスニペット対応）
            article_url = f"{SITE_BASE_URL}/posts/{article_id}/"
            result.body = inject_faq_schema(result.body, article_url)

            # Write file
            write_hugo_markdown(
                out_path=out_path,
                title=result.title,
                date_jst=date_midnight,
                image_url=image_path,
                category=item.category,
                tags=tags,
                body=result.body,
                description=result.description,
                slug=result.slug,
            )

            # Mark as processed
            processed_store.add(item.url)
            processed_store.save()
            
            # 1日の生成数を更新
            daily_stats.increment(item.category.value)
            daily_stats.save()

            # ログ出力
            print(f"  ✓ Saved: {filename}")
            if result.description:
                print(f"    Description: {result.description[:50]}...")
            if result.hook_text:
                print(f"    Hook text: {result.hook_text}")
            if result.shopping_keyword:
                print(f"    Shopping keyword: {result.shopping_keyword}")
            if result.viral_tags:
                print(f"    Viral tags: {result.viral_tags}")
            if result.seo_tags:
                print(f"    SEO tags: {', '.join(result.seo_tags)}")
            if result.slug:
                print(f"    Slug: {result.slug}")
            success_count += 1

            # X投稿用のキューに追加（デプロイ後投稿用）
            article_url = build_article_url(SITE_BASE_URL, article_id, result.slug)
            twitter_queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
            twitter_queue.add(TwitterQueueItem(
                article_id=article_id,
                title=result.title,
                url=article_url,
                category=item.category.value,
                viral_tags=result.viral_tags,
                tweet_text=result.tweet_text,
                hook_text=result.hook_text,
                summary_text=result.summary_text,
                question_text=result.question_text,
                image_path=image_path,
                created_at=now_jst.isoformat(),
            ))
            print(f"    Queued for X posting: {article_id}")

            # Twitter投稿（--skip-twitter でなければ即時投稿）
            if twitter_poster and not skip_twitter:
                if twitter_poster.post_article(
                    title=result.title,
                    url=article_url,
                    category=item.category,
                    viral_tags=result.viral_tags,
                    tweet_text=result.tweet_text,
                    hook_text=result.hook_text,
                    summary_text=result.summary_text,
                    question_text=result.question_text,
                    image_path=image_path,
                    static_dir=repo_root / "static",
                ):
                    twitter_queue.mark_posted(article_id)
                    print(f"  ✓ Posted to X")
                    twitter_success += 1
                else:
                    print(f"  ✗ X post failed (queued for later)")
            elif skip_twitter:
                print(f"    [--skip-twitter] X posting skipped (use --post-twitter {article_id} later)")

            # Rate limit
            if idx < len(final_items):
                print(f"  (Sleeping {SLEEP_SECONDS_PER_ARTICLE}s for rate limit...)")
                time.sleep(SLEEP_SECONDS_PER_ARTICLE)

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

    print()
    print("=" * 60)
    print(f"Done. Generated {success_count}/{len(final_items)} articles.")
    if twitter_poster and not skip_twitter:
        print(f"      Posted to X: {twitter_success}/{success_count}")
    elif skip_twitter:
        print(f"      X posting skipped. Run with --post-all-twitter after deploy.")
    
    # 1日の進捗状況を表示
    daily_stats.load()  # 最新の状態を再読み込み
    stats_data = daily_stats._data
    print()
    print("📊 Daily Progress:")
    for cat, target in stats_data["targets"].items():
        current = stats_data["generated"].get(cat, 0)
        remaining = max(0, target - current)
        bar = "█" * current + "░" * remaining
        print(f"   {cat:5s}: [{bar}] {current}/{target}")
    total_generated = sum(stats_data["generated"].values())
    total_target = sum(stats_data["targets"].values())
    print(f"   TOTAL: {total_generated}/{total_target} articles today")
    print("=" * 60)

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

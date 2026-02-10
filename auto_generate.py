#!/usr/bin/env python3
"""
Negi AI Lab - Auto Article Generator
=====================================
AIトレンド特化型の全自動ニュースサイト記事生成エンジン

カテゴリー構成比率:
  - NEWS (速報): 40%
  - TOOL (ツール検証): 40%
  - GUIDE (解説/ガイド): 20%

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
from google import genai as genai_new
from google.genai import types as genai_types

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
DEFAULT_TOTAL_ARTICLES = 2  # 1回の実行で2記事生成

# 日次リセット時刻（JST 02:00 = 海外速報をキャッチしやすい時間）
DAILY_RESET_HOUR = 2

# 1日の目標記事数（カテゴリー別）
# 6回実行 × 2記事 = 12記事/日
DAILY_TARGETS = {
    "NEWS": 5,   # 速報ニュース（鮮度重視）
    "TOOL": 5,   # ツール紹介
    "GUIDE": 2,  # 解説記事（タイムレス）
}

# ============================================================
# Persona Configuration（ペルソナ設定）
# ============================================================

PERSONA = {
    "name": "ねぎ",
    "role": "AI専門ブロガー",
    "tone": "カジュアルだが技術に詳しい。絵文字を適度に使う。一人称は「私」。",
    "background": """
        元SIerエンジニア（5年）→ フリーランス → AI専門ブロガー。
        毎日大量のAI関連情報をウォッチし、本当に使えるものだけを厳選して紹介。
        技術的な正確性と実用性を重視しつつ、初心者にもわかりやすく解説する。
    """,
    "writing_style": """
        - 「〜ですね」「〜だと思います」など柔らかい語尾
        - 自分の感想や意見を適度に入れる（「個人的には〜」「正直これは〜」）
        - 読者に語りかける口調（「みなさんも〜」「ぜひ試してみてください」）
        - 技術的な説明は正確に、でも難しすぎない言葉で
    """,
    "twitter_style": """
        - 感情を込めた一言から始める
        - 絵文字を2-3個使う
        - 「〜かも」「〜だった」など体験談風に
        - フォロワーに問いかける（「みなさんはどう思います？」）
    """,
}

# ニッチなハッシュタグ（ターゲット層が見る＆バズりやすいタグ）
# ※Categoryクラス定義前なので文字列キーで定義
# 選定基準：フォロワー多いアカウントが使う + 検索されやすい + ニッチすぎない
NICHE_HASHTAGS_STR = {
    "NEWS": [
        "#今日の積み上げ",
        "#朝活",
        "#プログラミング",
        "#駆け出しエンジニアと繋がりたい",
        "#Web3",
        "#スタートアップ",
        "#DX推進",
        "#機械学習",
    ],
    "TOOL": [
        "#今日の積み上げ",
        "#プログラミング",
        "#業務効率化",
        "#副業",
        "#フリーランス",
        "#リモートワーク",
        "#Notion",
        "#便利ツール",
    ],
    "GUIDE": [
        "#今日の積み上げ",
        "#プログラミング初心者",
        "#駆け出しエンジニアと繋がりたい",
        "#未経験からエンジニア",
        "#独学",
        "#転職活動",
        "#Python",
        "#学習記録",
    ],
}

# 固定タグ（全投稿に付与）- よりバズりやすいタグに
FIXED_HASHTAGS = ["#エンジニア", "#AI"]

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
]

# Reddit（トレンド・コミュニティ）
REDDIT_FEEDS = [
    {"url": "https://www.reddit.com/r/MachineLearning/hot/.rss", "name": "r/MachineLearning", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/artificial/hot/.rss", "name": "r/artificial", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/hot/.rss", "name": "r/LocalLLaMA", "category": "GUIDE"},
    {"url": "https://www.reddit.com/r/ChatGPT/hot/.rss", "name": "r/ChatGPT", "category": "NEWS"},
    {"url": "https://www.reddit.com/r/singularity/hot/.rss", "name": "r/singularity", "category": "NEWS"},
]

# プレスリリース系を除外するキーワード
PRESS_RELEASE_KEYWORDS = [
    "プレスリリース", "press release", "PR TIMES", "PRNewswire",
    "発表しました", "を開始", "を発売", "を提供開始",
    "ニフティニュース", "VOI.id", "excite.co.jp",
]

# 時間帯別優先度（JST時刻 → 優先カテゴリーリスト）
# 深夜2時: 海外速報キャッチでNEWS最優先
# 朝8時: 通勤時間、NEWS + TOOL
# 昼12時: 昼休み、TOOL中心
# 午後15時: TOOL + NEWS
# 夕方18時: 帰宅時間、NEWS + TOOL
# 夜21時: じっくり読むGUIDE
TIME_SLOT_PRIORITIES = {
    2:  ["NEWS", "TOOL", "GUIDE"],   # 海外速報優先
    8:  ["NEWS", "TOOL", "GUIDE"],   # 朝はNEWS
    12: ["TOOL", "NEWS", "GUIDE"],   # 昼はTOOL
    15: ["TOOL", "NEWS", "GUIDE"],   # 午後はTOOL
    18: ["NEWS", "TOOL", "GUIDE"],   # 夕方はNEWS
    21: ["GUIDE", "TOOL", "NEWS"],   # 夜はGUIDE
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
        "keywords": ["ollama", "llama", "ローカルllm", "local llm", "llama.cpp", "gguf", "量子化"],
        "products": [
            {"name": "MINISFORUM UM780 XTX", "search": "MINISFORUM UM780 XTX", "desc": "Ryzen7・32GB RAM・ローカルLLM最適"},
            {"name": "Intel NUC 13 Pro", "search": "Intel NUC 13 Pro ミニPC", "desc": "コンパクト＆高性能"},
        ],
        "category": "ミニPC"
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
        "keywords": ["agent", "エージェント", "autogpt", "crew", "自動化", "ワークフロー", "mcp"],
        "products": [
            {"name": "Logicool MX Master 3S", "search": "Logicool MX Master 3S", "desc": "ジェスチャー＋静音・作業効率UP"},
            {"name": "ウルトラワイドモニター", "search": "LG 34WQ75C-B 34インチ", "desc": "マルチウィンドウ作業が捗る"},
        ],
        "category": "効率化ガジェット"
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
            return [Category(s) for s in priority_strs]
    priority_strs = TIME_SLOT_PRIORITIES[slots[0]]
    return [Category(s) for s in priority_strs]


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
        except Exception:
            self._data = self._new_day_data()
        return self._data

    def _new_day_data(self) -> Dict:
        return {
            "date": get_daily_date(),
            "generated": {"NEWS": 0, "TOOL": 0, "GUIDE": 0},
            "targets": DAILY_TARGETS.copy(),
        }

    def get_remaining(self) -> Dict[str, int]:
        """各カテゴリーの残り枠を取得"""
        if not self._data:
            self.load()
        remaining = {}
        for cat in ["NEWS", "TOOL", "GUIDE"]:
            target = self._data["targets"].get(cat, 0)
            generated = self._data["generated"].get(cat, 0)
            remaining[cat] = max(0, target - generated)
        return remaining

    def increment(self, category: str) -> None:
        """カテゴリーの生成数を+1"""
        if not self._data:
            self.load()
        if category in self._data["generated"]:
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
        return f"NEWS {gen['NEWS']}/{tgt['NEWS']}, TOOL {gen['TOOL']}/{tgt['TOOL']}, GUIDE {gen['GUIDE']}/{tgt['GUIDE']}"


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
        stats = {"NEWS": 0, "TOOL": 0, "GUIDE": 0, "total": len(self._items)}
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
        }
        
        # キーワードマッチでカテゴリー判定
        news_score = sum(1 for kw in self.NEWS_KEYWORDS if kw.lower() in text)
        tool_score = sum(1 for kw in self.TOOL_KEYWORDS if kw.lower() in text)
        guide_score = sum(1 for kw in self.GUIDE_KEYWORDS if kw.lower() in text)
        
        # スコアが1以上ならカテゴリーに追加
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
        
        print(f"  [INFO] NEWS total: {len(items)} items")
        return items

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
                        possible_categories=[Category.NEWS],
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
                        possible_categories=[Category.NEWS],
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
                       "intelligence", "bot", "agent", "model", "transformer", "language"]

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
        url = "https://github.com/trending?since=daily&spoken_language_code=en"

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

        print(f"  [INFO] GUIDE total: {len(items)} items")
        return items[:max_items]

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
            ("ローカルLLMのセットアップガイド（2024年版）", "local-llm-setup"),
            ("Ollama + Open WebUIで自宅AIチャットを構築する方法", "ollama-webui-setup"),
            ("RAGパイプラインの基礎と実装入門", "rag-pipeline-intro"),
            ("LoRAファインチューニング完全ガイド", "lora-finetuning-guide"),
            ("LangChainでエージェントを作る方法", "langchain-agent-tutorial"),
            ("Hugging Face Transformersクイックスタート", "hf-transformers-quickstart"),
            ("GPT-4 APIのベストプラクティス", "gpt4-api-best-practices"),
            ("Stable Diffusion XLプロンプトエンジニアリング", "sdxl-prompt-engineering"),
            ("LLMのコンテキスト長を最大限活用するテクニック", "llm-context-length-tips"),
            ("AIコーディングアシスタント徹底比較", "ai-coding-assistant-comparison"),
            ("Gemini API入門：最初のアプリを作る", "gemini-api-getting-started"),
            ("Claude APIの使い方とTips", "claude-api-tips"),
            ("ベクトルデータベース選定ガイド", "vector-db-comparison"),
            ("プロンプトインジェクション対策入門", "prompt-injection-defense"),
            ("マルチモーダルAIの活用事例集", "multimodal-ai-use-cases"),
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
                extra={"is_generated_topic": True},
            ))

        return results


# ============================================================
# Article Result Data Class
# ============================================================

@dataclass
class ArticleResult:
    """記事生成結果を保持するデータクラス"""
    title: str
    body: str
    description: Optional[str] = None  # 3行要約から抽出したdescription
    hook_text: Optional[str] = None  # X投稿用のフック文（40文字以内）
    summary_text: Optional[str] = None  # X投稿用の3行要約（60文字以内）
    question_text: Optional[str] = None  # X投稿用の質問文（25文字以内）
    shopping_keyword: Optional[str] = None
    viral_tags: Optional[str] = None  # "#タグ1 #タグ2" 形式


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

        if item.category == Category.NEWS:
            return self._build_news_prompt(item)
        elif item.category == Category.TOOL:
            return self._build_tool_prompt(item)
        else:  # GUIDE
            return self._build_guide_prompt(item)

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
速報ニュース記事を書いてください。**本文は3000〜4000文字程度**で詳しく解説すること。
- 何が発表されたか（詳細に）
- 競合（ChatGPT, Claude等）との違いは何か
- 技術的な仕組みや背景
- 業界への影響を論理的に解説
- 一人称は「私」を使い、読者に語りかける口調で

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、## などは付けない）

## 3行要約

- 要約1
- 要約2
- 要約3

## 何が発表されたのか

（詳細な解説。背景や経緯も含めて500文字以上）

## 技術的なポイント

（技術的な仕組みや特徴を詳しく解説。500文字以上）

## 競合との比較

| 項目 | 今回の発表 | ChatGPT | Claude |
|------|-----------|---------|--------|
| ... | ... | ... | ... |

（表の後に各項目の詳細解説を追加。300文字以上）

## 業界への影響

（短期的・長期的な影響を論理的に分析。500文字以上）

## 私の見解

（「ねぎ」としての率直な感想。「正直なところ〜」「個人的には〜」などの表現を使い、300文字以上で深掘り）

---
### 【重要】メタデータ出力
記事執筆後、以下を記事の末尾に追記してください。

**1. X投稿用フック文 (HOOK)**
「続きを読みたくなる」煽り系の35文字以内。感情むき出し＋数字orパワーワード必須。
- 良い例: 「これ知らずに3年損した...」「マジで10倍速くなった🔥」「無料でこれはヤバすぎる」
- ダメ例: 「これ、チェックしておいた方がいいかも」（弱すぎ）
- フォーマット: `[HOOK: フック文]`

**2. X投稿用3行要約 (SUMMARY)**
記事の要点を3つの箇条書きで75文字以内。数字を入れる。
- 例: 「・処理速度が10倍\n・月額0円で使い放題\n・日本語完全対応」
- フォーマット: `[SUMMARY: ・要点1\n・要点2\n・要点3]`

**3. X投稿用質問文 (QUESTION)**
具体的で答えやすい質問。20文字以内。
- 良い例: 「もう使ってる人いる？」「乗り換えた人いる？」
- ダメ例: 「みんなはどう思う？」（抽象的すぎ）
- フォーマット: `[QUESTION: 質問文]`

**4. 商品検索キーワード (SHOPPING)**
記事に関連する**ガジェット・ハードウェア**のキーワード。具体的なブランド名＋型番推奨。
- 良い例: "MSI RTX 4070 SUPER", "HHKB Professional HYBRID", "Logicool MX Master 3S"
- ダメ例: "Python 機械学習 書籍"（書籍は売れない）
- フォーマット: `[SHOPPING: キーワード]`

**5. SNS拡散用ハッシュタグ (HASHTAGS)**
エンゲージメント狙いのタグを2つ（ビッグワード＋ニッチの組み合わせ）
- 良い例: #今日の積み上げ #駆け出しエンジニアと繋がりたい #プログラミング #副業
- ダメ例: #AI #生成AI #LLM（ビッグワードだけは禁止）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
- ⚠️や💡などの絵文字を見出しや本文に使わない（メタデータ部分のみ可）
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
「検証シミュレーション」を含むツールレビュー記事を書いてください。**本文は3000〜5000文字程度**で詳しく解説すること。
実際にそのツールをインストールして動かしたと仮定し、以下を含めること：
- 具体的なPythonコード例（動作する風のコード）
- 実行結果の例（架空でOK）
- プロンプト例（該当する場合）
- 一人称は「私」を使い、実際に試した体験談風に書く

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、キャッチーに）

**注意:** 本記事の検証パートはシミュレーションです。実際の測定結果ではありません。

## 3行要約

- 要約1
- 要約2
- 要約3

## このツールは何か

（概要説明。開発背景や特徴を含めて400文字以上）

## なぜ注目されているのか

（技術的な特徴や競合との違い。300文字以上）

## 検証シミュレーション：実際に使ってみた

### 環境構築

```bash
pip install xxx
```

### 基本的な使い方

```python
# サンプルコード（架空でOK）
from xxx import YYY

model = YYY()
result = model.run("テスト入力")
print(result)
```

### 実行結果

```
（架空の出力例）
```

### 応用例

（より実践的な使い方の例を追加）

## メリット・デメリット

### メリット
- ...
- ...
- ...

### デメリット
- ...
- ...

## どんな人におすすめか

（ターゲットユーザーとユースケースを具体的に）

## 私の評価

（「ねぎ」としての率直な評価。星評価: ★★★☆☆ のような形式も可。「正直なところ〜」「個人的には〜」などの表現を使い、300文字以上で深堀り）

---
### 【重要】メタデータ出力
記事執筆後、以下を記事の末尾に追記してください。

**1. X投稿用フック文 (HOOK)**
「続きを読みたくなる」煽り系の35文字以内。感情むき出し＋数字orパワーワード必須。
- 良い例: 「1週間使い倒した結論がこれ🔥」「無料でここまでできるの反則」
- ダメ例: 「このツール、予想以上に使えるかも」（弱すぎ）
- フォーマット: `[HOOK: フック文]`

**2. X投稿用3行要約 (SUMMARY)**
記事の要点を3つの箇条書きで75文字以内。数字を入れる。
- 例: 「・セットアップ5分\n・完全無料\n・日本語100%対応」
- フォーマット: `[SUMMARY: ・要点1\n・要点2\n・要点3]`

**3. X投稿用質問文 (QUESTION)**
具体的で答えやすい質問。20文字以内。
- 良い例: 「どのツール使ってる？」「これの代替ある？」
- ダメ例: 「どう思う？」（抽象的すぎ）
- フォーマット: `[QUESTION: 質問文]`

**4. 商品検索キーワード (SHOPPING)**
記事に関連する**ガジェット・ハードウェア**のキーワード。具体的なブランド名＋型番推奨。
- 良い例: "Raspberry Pi 5 スターターキット", "Stream Deck MK.2", "Dell 4Kモニター"
- ダメ例: "開発ツール 書籍"（書籍は売れない）
- フォーマット: `[SHOPPING: キーワード]`

**5. SNS拡散用ハッシュタグ (HASHTAGS)**
エンゲージメント狙いのタグを2つ（ビッグワード＋ニッチの組み合わせ）
- 良い例: #今日の積み上げ #便利ツール #業務効率化 #フリーランス
- ダメ例: #AI #生成AI（ビッグワードだけは禁止）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
- ⚠️や💡などの絵文字を見出しや本文に使わない（メタデータ部分のみ可）
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
チュートリアル形式のガイド記事を書いてください。**本文は3000〜5000文字程度**で詳しく解説すること。
「〜する方法」「エラー回避手順」など、読者が手元で試せるステップバイステップの手順書として書くこと。
- 具体的なコマンド例
- コード例
- 設定ファイルの例
を必ず含めること。
- 一人称は「私」を使い、読者に寄り添う口調で
- 「みなさんも経験ありませんか？」など読者への問いかけを入れる

【出力形式】必ず以下のMarkdown構造で出力すること。

1行目: タイトル（装飾なし、「〜する方法」「〜入門」形式推奨）

## この記事で学べること

- ポイント1
- ポイント2
- ポイント3

## 前提条件

- 必要なもの1
- 必要なもの2

## なぜこの知識が重要なのか

（背景説明や実務での活用シーン。300文字以上）

## Step 1: 環境準備

```bash
# コマンド例
```

（各コマンドの詳細な説明）

## Step 2: 基本設定

```python
# 設定コード例
```

（設定の意味や注意点を詳しく解説）

## Step 3: 実行と確認

（手順の説明と期待される結果）

## Step 4: 応用テクニック

（発展的な使い方やカスタマイズ方法）

## よくあるエラーと対処法

### エラー1: xxx

```
エラーメッセージ例
```

**原因:** ...
**解決策:** ...

### エラー2: yyy

（複数のエラーパターンを網羅）

## ベストプラクティス

（実務で役立つTipsやおすすめの設定）

## まとめ

（「ねぎ」としての締めの言葉。「いかがでしたか？」「ぜひ試してみてくださいね」など。300文字以上）

---
### 【重要】メタデータ出力
記事執筆後、以下を記事の末尾に追記してください。

**1. X投稿用フック文 (HOOK)**
「続きを読みたくなる」煽り系の35文字以内。感情むき出し＋数字orパワーワード必須。
- 良い例: 「このエラーで1日溶かした過去の自分に教えたい」「初心者が絶対ハマる罠5選」
- ダメ例: 「このエラー、私も何度もハマった」（弱すぎ）
- フォーマット: `[HOOK: フック文]`

**2. X投稿用3行要約 (SUMMARY)**
記事の要点を3つの箇条書きで75文字以内。数字を入れる。
- 例: 「・環境構築3分で完了\n・よくあるエラー5つ解決\n・コピペで100%動く」
- フォーマット: `[SUMMARY: ・要点1\n・要点2\n・要点3]`

**3. X投稿用質問文 (QUESTION)**
具体的で答えやすい質問。20文字以内。
- 良い例: 「同じエラー出た人いる？」「他に詰まった箇所ある？」
- ダメ例: 「他にも知りたいこと教えて」（漠然としすぎ）
- フォーマット: `[QUESTION: 質問文]`

**4. 商品検索キーワード (SHOPPING)**
記事に関連する**ガジェット・ハードウェア**のキーワード。具体的なブランド名＋型番推奨。
- 良い例: "MacBook Air M3 16GB", "BenQ ScreenBar Halo", "MINISFORUM ミニPC"
- ダメ例: "機械学習 入門書"（書籍は売れない）
- フォーマット: `[SHOPPING: キーワード]`

**5. SNS拡散用ハッシュタグ (HASHTAGS)**
エンゲージメント狙いのタグを2つ（ビッグワード＋ニッチの組み合わせ）
- 良い例: #今日の積み上げ #プログラミング初心者 #独学 #未経験からエンジニア
- ダメ例: #AI #生成AI（ビッグワードだけは禁止）
- フォーマット: `[HASHTAGS: #タグ1 #タグ2]`
---

【禁止事項】
- YAML/TOML Front Matterは出力しない
- HTMLタグは使わない
- ⚠️や💡などの絵文字を見出しや本文に使わない（メタデータ部分のみ可）
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
        body, shopping_keyword, viral_tags, hook_text, summary_text, question_text = self._extract_keywords_and_add_affiliate(body, category)
        
        # 3行要約からdescriptionを抽出
        description = self._extract_description(body)

        return ArticleResult(
            title=title,
            body=body,
            description=description,
            hook_text=hook_text,
            summary_text=summary_text,
            question_text=question_text,
            shopping_keyword=shopping_keyword,
            viral_tags=viral_tags,
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

    def _extract_keywords_and_add_affiliate(self, body: str, category: Category = Category.NEWS) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        本文から[SHOPPING: xxx]、[HASHTAGS: xxx]、[HOOK: xxx]、[SUMMARY: xxx]、[QUESTION: xxx]を抽出し、
        カテゴリーに応じたアフィリエイトリンクを追加。
        
        Args:
            body: 記事本文
            category: 記事カテゴリー（NEWS/TOOL/GUIDE）
        
        Returns:
            (処理済み本文, shopping_keyword, viral_tags, hook_text, summary_text, question_text)
        """
        # 0. Hook Text 抽出（X投稿用フック文）
        hook_pattern = r'\[HOOK:\s*(.+?)\]'
        hook_match = re.search(hook_pattern, body)
        hook_text = None
        if hook_match:
            hook_text = hook_match.group(1).strip()
            body = re.sub(r'\n*\[HOOK:[^\]]+\]\n*', '\n', body)
        
        # 0.5. Summary Text 抽出（X投稿用3行要約）
        summary_pattern = r'\[SUMMARY:\s*(.+?)\]'
        summary_match = re.search(summary_pattern, body, re.DOTALL)
        summary_text = None
        if summary_match:
            summary_text = summary_match.group(1).strip()
            body = re.sub(r'\n*\[SUMMARY:[^\]]+\]\n*', '\n', body)
        
        # 0.6. Question Text 抽出（X投稿用質問文）
        question_pattern = r'\[QUESTION:\s*(.+?)\]'
        question_match = re.search(question_pattern, body)
        question_text = None
        if question_match:
            question_text = question_match.group(1).strip()
            body = re.sub(r'\n*\[QUESTION:[^\]]+\]\n*', '\n', body)
        
        # 1. Shopping Keyword 抽出
        shopping_pattern = r'\[SHOPPING:\s*(.+?)\]'
        shopping_match = re.search(shopping_pattern, body)
        shopping_keyword = None
        if shopping_match:
            shopping_keyword = shopping_match.group(1).strip()
            # 行全体を削除（前後の空行も含む）
            body = re.sub(r'\n*\[SHOPPING:[^\]]+\]\n*', '\n', body)
        
        # 2. Viral Tags 抽出
        hashtags_pattern = r'\[HASHTAGS:\s*(.+?)\]'
        hashtags_match = re.search(hashtags_pattern, body)
        viral_tags = None
        if hashtags_match:
            viral_tags = hashtags_match.group(1).strip()
            body = re.sub(r'\n*\[HASHTAGS:[^\]]+\]\n*', '\n', body)
        
        # 3. 旧形式の[KEYWORD: xxx]も念のため除去（互換性）
        body = re.sub(r'\n*\[KEYWORD:[^\]]+\]\n*', '\n', body)
        
        # 4. 末尾の「---」以降のメタデータ出力指示も除去
        body = re.sub(r'\n---\n### 【重要】キーワード選定タスク[\s\S]*$', '', body)
        body = re.sub(r'\n---\n### 【重要】メタデータ出力[\s\S]*$', '', body)
        
        # 5. クリーンアップ（連続する空行を整理）
        body = re.sub(r'\n{3,}', '\n\n', body).strip()
        
        # 6. カテゴリーに応じたアフィリエイト挿入
        body = self._insert_smart_affiliate(body, category, shopping_keyword)
        
        return body, shopping_keyword, viral_tags, hook_text, summary_text, question_text

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

    def _insert_smart_affiliate(self, body: str, category: Category, shopping_keyword: Optional[str]) -> str:
        """
        カテゴリーと本文内容に応じてスマートにアフィリエイトを挿入。
        
        - NEWS: 末尾に控えめに1つ
        - TOOL: 導入部後 + 末尾に詳細
        - GUIDE: 各セクション末尾 + 末尾まとめ
        """
        # トピック検出
        topics = self._detect_content_topics(body)
        
        if category == Category.NEWS:
            # NEWS: 末尾に簡潔なリンクのみ
            footer = self._generate_minimal_affiliate(topics[0], shopping_keyword)
            body = body + "\n\n" + footer
            
        elif category == Category.TOOL:
            # TOOL: 導入部後にインライン + 末尾に詳細
            body = self._insert_inline_affiliate_after_intro(body, topics)
            footer = self._generate_detailed_affiliate(topics, shopping_keyword)
            body = body + "\n\n" + footer
            
        elif category == Category.GUIDE:
            # GUIDE: 末尾に学習リソースまとめ
            footer = self._generate_learning_resources(topics, shopping_keyword)
            body = body + "\n\n" + footer
        
        return body

    def _insert_inline_affiliate_after_intro(self, body: str, topics: List[str]) -> str:
        """導入部（最初の見出し）の後にインラインアフィリエイトを挿入"""
        # 最初の ## 見出しを探す
        lines = body.split('\n')
        h2_count = 0
        insert_index = -1
        
        for i, line in enumerate(lines):
            if line.startswith('## '):
                h2_count += 1
                if h2_count == 2:  # 2つ目の見出しの前
                    insert_index = i
                    break
        
        if insert_index > 0 and topics:
            topic = topics[0]
            topic_data = PRODUCT_MAPPINGS.get(topic, PRODUCT_MAPPINGS["default"])
            if topic_data["products"]:
                product = topic_data["products"][0]
                
                inline_box = f'''
> 💡 **{topic_data["category"]}のおすすめ**
> 
> **[{product["name"]}]({self._make_amazon_url(product["search"])})** - {product["desc"]}

'''
                lines.insert(insert_index, inline_box)
                body = '\n'.join(lines)
        
        return body

    def _generate_minimal_affiliate(self, topic: str, shopping_keyword: Optional[str]) -> str:
        """NEWS向け: 控えめな末尾アフィリエイト"""
        keyword = shopping_keyword or "AI 人工知能"
        amazon_url = self._make_amazon_url(keyword)
        rakuten_url = self._make_rakuten_url(keyword)
        
        return f'''---

📚 **関連情報をもっと知りたい方へ**

<div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0;">
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding: 8px 16px; background: #ff9900; color: white; text-decoration: none; border-radius: 6px; font-size: 14px;">📖 Amazonで関連書籍を探す</a>
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding: 8px 16px; background: #bf0000; color: white; text-decoration: none; border-radius: 6px; font-size: 14px;">🛒 楽天で探す</a>
</div>'''

    def _generate_detailed_affiliate(self, topics: List[str], shopping_keyword: Optional[str]) -> str:
        """TOOL向け: 詳細なおすすめ商品セクション（DBマッチ + 汎用検索フォールバック）"""
        sections = []
        has_db_products = False  # DBから商品が見つかったか
        
        for topic in topics[:2]:
            topic_data = PRODUCT_MAPPINGS.get(topic, {})
            
            # default以外でproductsがある場合のみ表示
            if topic != "default" and topic_data.get("products"):
                has_db_products = True
                product_cards = []
                for product in topic_data["products"]:
                    amazon_url = self._make_amazon_url(product["search"])
                    rakuten_url = self._make_rakuten_url(product["search"])
                    
                    card = f'''<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin: 8px 0; background: #fafafa;">
  <strong style="font-size: 16px;">🛍️ {product["name"]}</strong>
  <p style="color: #666; margin: 8px 0; font-size: 14px;">{product["desc"]}</p>
  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
    <a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding: 6px 12px; background: #ff9900; color: white; text-decoration: none; border-radius: 4px; font-size: 13px;">Amazonで見る</a>
    <a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding: 6px 12px; background: #bf0000; color: white; text-decoration: none; border-radius: 4px; font-size: 13px;">楽天で見る</a>
  </div>
</div>'''
                    product_cards.append(card)
                
                if product_cards:
                    sections.append(f'''
### 📦 {topic_data["category"]}のおすすめ

{''.join(product_cards)}''')
        
        # 汎用検索リンクは必ず追加（フォールバック兼用）
        search_keyword = shopping_keyword or "AI 人工知能 入門"
        search_section = self._generate_search_buttons(search_keyword)
        sections.append(search_section)
        
        # セクションがなければ（DBマッチなし）、従来の汎用リンクをメインで表示
        if not has_db_products and shopping_keyword:
            return self._generate_affiliate_links(shopping_keyword)
        
        return f'''---

## 🛒 この記事で紹介した関連商品

{''.join(sections)}

<small style="color: #888;">※上記リンクはアフィリエイトリンクです。購入により当サイトに収益が発生する場合があります。</small>'''

    def _generate_learning_resources(self, topics: List[str], shopping_keyword: Optional[str]) -> str:
        """GUIDE向け: 学習リソースまとめ（DBマッチ + 汎用検索フォールバック）"""
        resources = []
        has_db_products = False
        
        for topic in topics[:2]:
            # default以外のトピックのみDBから取得
            if topic != "default":
                topic_data = PRODUCT_MAPPINGS.get(topic, {})
                if topic_data.get("products"):
                    has_db_products = True
                    for product in topic_data["products"]:
                        amazon_url = self._make_amazon_url(product["search"])
                        resources.append(f'- **[{product["name"]}]({amazon_url})** - {product["desc"]}')
        
        # DBマッチがなければ、汎用的な学習リソースを提案
        if not resources:
            search_keyword = shopping_keyword or "AI 人工知能 入門"
            amazon_url = self._make_amazon_url(search_keyword)
            resources = [
                f'- **[「{search_keyword}」の関連書籍を探す]({amazon_url})** - Amazonで最新の書籍をチェック',
            ]
        
        # 汎用検索ボタンは必ず表示（フォールバック兼用）
        search_keyword = shopping_keyword or "AI 機械学習 入門書"
        amazon_url = self._make_amazon_url(search_keyword)
        rakuten_url = self._make_rakuten_url(search_keyword)
        search_buttons = f'''
<div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0;">
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding: 10px 20px; background: linear-gradient(135deg, #ff9900, #ff6600); color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">🔍 Amazonで「{search_keyword}」を検索</a>
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding: 10px 20px; background: linear-gradient(135deg, #bf0000, #8b0000); color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">🔍 楽天で検索</a>
</div>'''

        # DBマッチがなくshopping_keywordがある場合は従来メソッドをメインに
        if not has_db_products and shopping_keyword:
            return self._generate_affiliate_links(shopping_keyword)

        return f'''---

## 📚 さらに学習を深めるためのリソース

この記事の内容をより深く理解するために、以下の書籍・教材がおすすめです：

{chr(10).join(resources)}

{search_buttons}

<small style="color: #888;">※上記リンクはアフィリエイトリンクです。</small>'''

    def _generate_search_buttons(self, keyword: str) -> str:
        """汎用検索ボタンを生成"""
        amazon_url = self._make_amazon_url(keyword)
        rakuten_url = self._make_rakuten_url(keyword)
        
        return f'''
### 🔎 もっと探す

<div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0;">
<a href="{amazon_url}" target="_blank" rel="noopener sponsored" style="padding: 10px 20px; background: linear-gradient(135deg, #ff9900, #ff6600); color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">Amazonで「{keyword}」を検索</a>
<a href="{rakuten_url}" target="_blank" rel="noopener sponsored" style="padding: 10px 20px; background: linear-gradient(135deg, #bf0000, #8b0000); color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">楽天で検索</a>
</div>'''

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

    def _generate_affiliate_links(self, keyword: str) -> str:
        """
        キーワードからAmazon/楽天のアフィリエイトリンクボタンを生成。
        """
        encoded_keyword = quote(keyword, safe="")
        
        amazon_url = f"https://www.amazon.co.jp/s?k={encoded_keyword}&tag={AMAZON_ASSOCIATE_TAG}"
        # 楽天アフィリエイトリンク（hb.afl.rakuten.co.jp経由）
        rakuten_search_url = f"https://search.rakuten.co.jp/search/mall/{encoded_keyword}/"
        rakuten_encoded = quote(rakuten_search_url, safe='')
        rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AFFILIATE_ID}/?pc={rakuten_encoded}&m={rakuten_encoded}"
        
        # Markdown + インラインCSS でボタン風リンクを生成
        affiliate_html = f'''
---

## 関連商品をチェック

<div style="display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0;">
  <a href="{amazon_url}" target="_blank" rel="noopener noreferrer sponsored" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: linear-gradient(135deg, #ff9900 0%, #ff6600 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(255, 153, 0, 0.3); transition: transform 0.2s;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
    Amazonで「{keyword}」を検索
  </a>
  <a href="{rakuten_url}" target="_blank" rel="noopener noreferrer sponsored" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: linear-gradient(135deg, #bf0000 0%, #8b0000 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(191, 0, 0, 0.3); transition: transform 0.2s;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
    楽天で「{keyword}」を検索
  </a>
</div>

<small style="color: #888;">※上記リンクはアフィリエイトリンクです。購入により当サイトに収益が発生する場合があります。</small>
'''
        return affiliate_html


# ============================================================
# Image Handler
# ============================================================

class ImageHandler:
    """Pollinations.aiを使用した無料画像生成・ローカル保存"""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        # Pollinations.aiはAPIキー不要

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
        
        Args:
            title: 記事タイトル
            body: 記事本文
            category: カテゴリー
            article_id: 記事ID（ファイル名用）
            output_dir: 画像保存先ディレクトリ (static/images/posts/)
        
        Returns:
            Hugo用の相対パス (例: /images/posts/2026-01-13-abc123.png)
        """
        # テキストモデルで画像生成用プロンプトを作成
        prompt_en = self._generate_image_prompt(title, body, category)
        
        try:
            # Pollinations.aiで画像生成（無料、APIキー不要）
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt_en)
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
            
            response = requests.get(pollinations_url, timeout=120)
            response.raise_for_status()
            
            if 'image' not in response.headers.get('content-type', ''):
                raise ValueError(f"Invalid content type: {response.headers.get('content-type')}")
            
            image_data = response.content
            
            # 保存先ディレクトリ作成
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル保存（Pollinations.aiはJPEGを返す）
            filename = f"{article_id}.jpg"
            file_path = output_dir / filename
            file_path.write_bytes(image_data)
            
            # Hugo用相対パス
            return f"/images/posts/{filename}"
            
        except Exception as e:
            print(f"  [Image] Pollinations.ai image generation failed: {e}")
            # フォールバック: デフォルトのプレースホルダーパスを返す
            return "/images/default-thumbnail.png"

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
        hook_text: Optional[str] = None,
        summary_text: Optional[str] = None,
        question_text: Optional[str] = None,
    ) -> bool:
        """
        記事をTwitterにスレッド形式で投稿する（メイン + リプライ）。
        
        滞在時間を増やすため、2ツイートで構成：
        - メイン: フック + 要点 + ハッシュタグ + 「↓」
        - リプライ: 感想 + URL + 質問（リプライ誘発）

        Args:
            title: 記事タイトル
            url: 記事のURL (Twitterカードで自動的にOGP画像が表示される)
            category: 記事カテゴリー
            viral_tags: Geminiが選んだSNS拡散用ハッシュタグ（例: "#自作PC #ゲーミング"）
            hook_text: 冒頭のフック文（続きを読みたくなる一言）
            summary_text: 3行要点（箇条書き、各行20文字以内）
            question_text: リプライ誘発の質問文

        Returns:
            投稿成功時True
        """
        try:
            # ===== ハッシュタグ構成（Gemini生成2つ + 候補2つ = 4つ）=====
            import random
            tags_list = []
            gemini_tags = []
            
            if viral_tags:
                # Gemini生成タグを収集（ビッグワード除外）
                big_words = ['#AI', '#生成AI', '#LLM', '#人工知能', '#ChatGPT', '#技術', '#ニュース']
                for tag in viral_tags.split():
                    if tag.startswith('#') and tag not in big_words:
                        gemini_tags.append(tag)
            
            # Gemini生成タグから最大2つ採用
            tags_list.extend(gemini_tags[:2])
            
            # カテゴリー別候補から2つ追加（合計4つになるまで）
            niche_options = NICHE_HASHTAGS_STR.get(category.value, NICHE_HASHTAGS_STR["NEWS"])
            shuffled = random.sample(niche_options, len(niche_options))
            for tag in shuffled:
                if tag not in tags_list and len(tags_list) < 4:
                    tags_list.append(tag)
            
            # まだ4つ未満なら固定タグで補完
            for fixed_tag in FIXED_HASHTAGS:
                if fixed_tag not in tags_list and len(tags_list) < 4:
                    tags_list.append(fixed_tag)
            
            tag_str = ' '.join(tags_list[:4])

            # ===== フック文（Gemini生成を無視し、常にバズるテンプレートを使用） =====
            # 理由: Geminiは「胸アツ展開ですね」等の弱いフックを生成しがち
            hooks_list = {
                Category.NEWS: [
                    "これマジで革命的かも...🔥",
                    "え、これ無料でいいの...？",
                    "知らないと損するやつ来た👀",
                    "これはヤバい。マジでヤバい。",
                    "開発者全員見て。これ神。",
                    "これ知らなかったら損してた...",
                    "まって、これガチでヤバくない？",
                ],
                Category.TOOL: [
                    "3日間使い倒した結果...🔥",
                    "これ知らずに損してた...",
                    "作業時間が半分になった神ツール",
                    "無料でここまでできるの反則では",
                    "もっと早く知りたかった...",
                    "ガチで生産性爆上がりした",
                    "これ導入してから世界変わった",
                ],
                Category.GUIDE: [
                    "これで詰まってた人、解決します",
                    "1時間悩んだエラー、これで一発解決",
                    "初心者の頃の自分に教えたい",
                    "知らないと一生ハマるやつ",
                    "これ、教科書には載ってない",
                    "何度もググった人向け、完全解説",
                    "公式ドキュメントで迷子になった人へ",
                ],
            }
            hooks = hooks_list.get(category, hooks_list[Category.NEWS])
            hook = random.choice(hooks)

            # ===== 要点サマリー =====
            if summary_text:
                # 「・」で始まる箇条書きを改行で結合
                summary = summary_text.strip()
            else:
                # フォールバック: タイトルを要約として使用
                max_title_len = 50
                summary = title[:max_title_len] + "..." if len(title) > max_title_len else title

            # ===== メインツイート構成（140文字制限厳守） =====
            # フォーマット: フック + 要点 + ハッシュタグ + ↓
            main_tweet = f"{hook}\n\n{summary}\n\n{tag_str}\n↓"
            
            # 140文字制限チェック（絶対に超えない）
            if len(main_tweet) > 140:
                # まず要点を2行に短縮
                summary_lines = summary.split('\n')
                if len(summary_lines) > 2:
                    summary = '\n'.join(summary_lines[:2])
                    main_tweet = f"{hook}\n\n{summary}\n\n{tag_str}\n↓"
                
                # それでも超えるなら要点をさらに短縮
                if len(main_tweet) > 140:
                    summary_lines = summary.split('\n')
                    shortened = []
                    for line in summary_lines:
                        if len(line) > 15:
                            shortened.append(line[:15])
                        else:
                            shortened.append(line)
                    summary = '\n'.join(shortened[:2])
                    main_tweet = f"{hook}\n\n{summary}\n\n{tag_str}\n↓"
                
                # 最終手段: ハッシュタグを3つに減らす
                if len(main_tweet) > 140:
                    tag_str = ' '.join(tags_list[:3])
                    main_tweet = f"{hook}\n\n{summary}\n\n{tag_str}\n↓"

            # ===== リプライツイート構成（140文字フル活用）=====
            # Twitter URLは投稿後t.coで23文字になるが、投稿時は実URLでカウント
            # 目標: 140文字ギリギリまで使ってエンゲージメント最大化
            
            # カテゴリー別の詳しい感想（40〜50文字）
            category_comments_list = {
                Category.NEWS: [
                    "最初は「また新しいの出たか」くらいだったけど、触ってみたらガチで印象変わった。これは流行る",
                    "正直期待してなかったけど、使ってみたら想像以上だった。特に○○の部分がヤバい",
                    "「本当に使えるの？」って思う人多いと思う。実際に検証したから見てほしい",
                    "業界的にかなりインパクトある発表だと思う。個人的な見解も書いた",
                ],
                Category.TOOL: [
                    "1週間ガチで使い倒した。結論から言うと、もう手放せない。理由は記事に全部書いた",
                    "最初は「また便利ツールか」と思ったけど、使ったら作業効率マジで変わった",
                    "類似ツール5個くらい試した上での結論。これが一番しっくりきた理由を書いた",
                    "導入コストと効果を具体的に計算してみた。ROI気になる人は見てほしい",
                ],
                Category.GUIDE: [
                    "自分が3時間溶かしたエラー、これ見れば5分で解決する。同じ沼にハマらないで",
                    "公式ドキュメント読んでも分からなかったこと全部まとめた。これで完全理解",
                    "初心者の頃の自分に見せたい記事を書いた。コピペで100%動くコード付き",
                    "「なんで動かないの？」を全部潰した。よくあるミス10個と解決法まとめ",
                ],
            }
            comments = category_comments_list.get(category, category_comments_list[Category.NEWS])
            comment = random.choice(comments)
            
            # 質問文（Gemini生成を無視し、常にエンゲージメント高い質問を使用）
            # 理由: Geminiは「どっち派ですか？」等の短い質問を生成しがち
            questions_list = {
                Category.NEWS: [
                    "これ使う予定ある？気になるポイントあったら教えて🤔",
                    "ぶっちゃけどう思う？賛否分かれそうだけど意見聞きたい",
                    "みんなの現場だとどう？導入検討してる人いる？",
                    "流行ると思う？それとも一過性？予想聞かせて",
                ],
                Category.TOOL: [
                    "使ってる人いたら感想聞きたい！他にオススメあれば教えて🙏",
                    "これの代替ツール知ってる人いる？比較したい",
                    "導入してる会社ある？実際の運用どんな感じ？",
                    "無料プランで足りる？有料にした人いたら違い教えて",
                ],
                Category.GUIDE: [
                    "ここ分からん！ってとこあったらリプで教えて。追記する📝",
                    "同じエラーで詰まった人いる？他の解決法あれば共有して",
                    "これ系で他に困ってることある？リクエストあれば書く",
                    "解決できた人いたら教えて！記事の改善に活かしたい",
                    ],
                }
            questions = questions_list.get(category, questions_list[Category.NEWS])
            question = random.choice(questions)

            # リプライフォーマット: 感想 + URL + 質問
            # 目標構成: 感想(50) + 改行(2) + URL(45) + 改行(2) + 質問(35) = 約134文字
            reply_tweet = f"{comment}\n\n{url}\n\n{question}"
            
            # 140文字チェック（実URLでカウント）
            if len(reply_tweet) > 140:
                # 質問を短縮
                max_question_len = 140 - len(comment) - len(url) - 6  # 改行分
                if max_question_len > 15:
                    question = question[:max_question_len]
                    reply_tweet = f"{comment}\n\n{url}\n\n{question}"
                else:
                    # 感想も短縮
                    available = 140 - len(url) - 6
                    comment_len = int(available * 0.6)
                    question_len = available - comment_len
                    comment = comment[:comment_len]
                    question = question[:question_len]
                    reply_tweet = f"{comment}\n\n{url}\n\n{question}"

            # ===== ツイート投稿（スレッド形式） =====
            # 1. メインツイートを投稿
            main_response = self.client.create_tweet(text=main_tweet)
            main_tweet_id = main_response.data['id']
            
            # 2. リプライツイートを投稿（メインに返信）
            self.client.create_tweet(
                text=reply_tweet,
                in_reply_to_tweet_id=main_tweet_id
            )

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
) -> None:
    """Hugo形式のMarkdownファイルを出力（PaperModテーマ対応）"""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # カテゴリー名をHugo用に変換
    category_map = {
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
    category: str  # "NEWS", "TOOL", "GUIDE"
    viral_tags: Optional[str]
    hook_text: Optional[str]  # X投稿用フック文
    summary_text: Optional[str]  # X投稿用要点サマリー
    question_text: Optional[str]  # X投稿用リプライ誘発質問
    created_at: str


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
            "hook_text": item.hook_text,
            "summary_text": item.summary_text,
            "question_text": item.question_text,
            "created_at": item.created_at,
            "posted": False,
        })
        self._save()

    def get_pending(self) -> List[Dict]:
        if not self._queue:
            self.load()
        return [item for item in self._queue if not item.get("posted", False)]

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
            "NEWS": Category.NEWS,
            "TOOL": Category.TOOL,
            "GUIDE": Category.GUIDE,
        }
        category = category_map.get(item["category"], Category.NEWS)

        success = poster.post_article(
            title=item["title"],
            url=item["url"],
            category=category,
            viral_tags=item.get("viral_tags"),
            hook_text=item.get("hook_text"),
            summary_text=item.get("summary_text"),
            question_text=item.get("question_text"),
        )

        if success:
            queue.mark_posted(article_id)
            print(f"✓ Successfully posted to X!")
            print(f"  Title: {item['title'][:50]}...")
            print(f"  URL: {item['url']}")
            return 0
        else:
            print("✗ Failed to post to X.")
            return 1

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def post_all_pending_to_twitter() -> int:
    """
    キュー内の未投稿記事をすべてXに投稿する。
    直近24時間以内に作成された記事のみ対象とする。
    
    Usage: python auto_generate.py --post-all-twitter
    """
    print("=" * 60)
    print("Negi AI Lab - Post All Pending to X")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent
    queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
    all_pending = queue.get_pending()

    if not all_pending:
        print("No pending articles to post.")
        return 0

    # 直近24時間以内の記事のみ対象
    now = datetime.now(JST)
    cutoff = now - timedelta(hours=24)
    
    pending = []
    for item in all_pending:
        created_str = item.get("created_at", "")
        try:
            created = datetime.fromisoformat(created_str)
            if created > cutoff:
                pending.append(item)
            else:
                # 24時間以上前の未投稿記事は自動でposted=trueにする
                queue.mark_posted(item["article_id"])
                print(f"  [SKIP] Old article marked as posted: {item['title'][:30]}...")
        except Exception:
            # パースできない場合はスキップ
            pass

    if not pending:
        print("No recent pending articles to post (all older than 24 hours).")
        return 0

    print(f"Found {len(pending)} pending articles (within 24 hours).")
    print()

    if not is_twitter_configured() or not TWEEPY_AVAILABLE:
        print("[ERROR] Twitter not configured or tweepy not installed.")
        return 2

    poster = TwitterPoster()
    success_count = 0
    failed_count = 0

    for item in pending:
        print(f"Posting: {item['title'][:40]}...")
        
        category_map = {
            "NEWS": Category.NEWS,
            "TOOL": Category.TOOL,
            "GUIDE": Category.GUIDE,
        }
        category = category_map.get(item["category"], Category.NEWS)

        if poster.post_article(
            title=item["title"],
            url=item["url"],
            category=category,
            viral_tags=item.get("viral_tags"),
            hook_text=item.get("hook_text"),
            summary_text=item.get("summary_text"),
            question_text=item.get("question_text"),
        ):
            queue.mark_posted(item["article_id"])
            print(f"  ✓ Posted!")
            success_count += 1
        else:
            print(f"  ✗ Failed")
            failed_count += 1
        
        # レート制限対策
        time.sleep(5)

    print()
    print(f"Posted {success_count}/{len(pending)} articles.")
    
    # 一部成功していれば成功扱い（重複エラー等は許容）
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
        remaining = {cat: 999 for cat in ["NEWS", "TOOL", "GUIDE"]}
    else:
        remaining = daily_remaining.copy()

    print(f"  [DEBUG] Daily remaining: NEWS={remaining.get('NEWS', 0)}, TOOL={remaining.get('TOOL', 0)}, GUIDE={remaining.get('GUIDE', 0)}")

    # プールからの補充可能数を加算
    pool_available = {cat: 0 for cat in Category}
    if pool:
        pool_stats = pool.get_pool_stats()
        pool_available = {
            Category.NEWS: pool_stats.get("NEWS", 0),
            Category.TOOL: pool_stats.get("TOOL", 0),
            Category.GUIDE: pool_stats.get("GUIDE", 0),
        }
        print(f"  [DEBUG] Pool available: NEWS={pool_available[Category.NEWS]}, TOOL={pool_available[Category.TOOL]}, GUIDE={pool_available[Category.GUIDE]}")

    # 各カテゴリーの実際の上限 = min(残り枠, フィード+プール)
    effective_available = {
        Category.NEWS: min(remaining.get("NEWS", 0), available.get(Category.NEWS, 0) + pool_available[Category.NEWS]),
        Category.TOOL: min(remaining.get("TOOL", 0), available.get(Category.TOOL, 0) + pool_available[Category.TOOL]),
        Category.GUIDE: min(remaining.get("GUIDE", 0), available.get(Category.GUIDE, 0) + pool_available[Category.GUIDE]),
    }

    # 時間帯に応じた優先順位を取得
    priority_order = get_current_priority()
    current_hour = datetime.now(JST).hour
    print(f"  [DEBUG] Current hour: {current_hour}:00 JST, Priority: {[c.value for c in priority_order]}")

    # ラウンドロビン方式：優先順位順に各カテゴリーから1つずつ取る
    final = {Category.NEWS: 0, Category.TOOL: 0, Category.GUIDE: 0}
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
    print(f"[INFO] News pool: {pool_stats['total']} items (NEWS:{pool_stats['NEWS']}, TOOL:{pool_stats['TOOL']}, GUIDE:{pool_stats['GUIDE']})")

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

    news_items = collector.collect_news(max_items=total * 3)  # プール蓄積のため多めに
    tool_items = collector.collect_tools(max_items=total * 3)
    guide_items = collector.collect_guides(max_items=total * 3)
    
    # プールを保存（新しいアイテムを蓄積）
    news_pool.save()

    available = {
        Category.NEWS: len(news_items),
        Category.TOOL: len(tool_items),
        Category.GUIDE: len(guide_items),
    }

    print(f"  NEWS:  {available[Category.NEWS]} items found")
    print(f"  TOOL:  {available[Category.TOOL]} items found")
    print(f"  GUIDE: {available[Category.GUIDE]} items found")
    print()

    # -------------------------
    # Step 2: Calculate with fallback (1日の残り枠 + 時間帯優先度 + プール)
    # -------------------------
    print("[Step 2] Calculating targets with daily quota...")
    daily_remaining = daily_stats.get_remaining()
    targets = calculate_targets_with_fallback(total, available, daily_remaining, pool=news_pool)

    print(f"  NEWS:  {targets[Category.NEWS]} (daily remaining: {daily_remaining['NEWS']})")
    print(f"  TOOL:  {targets[Category.TOOL]} (daily remaining: {daily_remaining['TOOL']})")
    print(f"  GUIDE: {targets[Category.GUIDE]} (daily remaining: {daily_remaining['GUIDE']})")
    print(f"  Total: {sum(targets.values())}")
    print()

    # -------------------------
    # Build final item list (フィードから優先、足りなければプールから)
    # -------------------------
    final_items: List[NewsItem] = []
    
    # NEWS
    news_needed = targets[Category.NEWS]
    final_items.extend(news_items[:news_needed])
    if len(news_items) < news_needed:
        # プールから補充
        pool_news = news_pool.get_items_for_category(Category.NEWS, news_needed - len(news_items), fresh_first=True)
        final_items.extend(pool_news)
        if pool_news:
            print(f"  [INFO] NEWS: {len(pool_news)} items from pool")
    
    # TOOL
    tool_needed = targets[Category.TOOL]
    final_items.extend(tool_items[:tool_needed])
    if len(tool_items) < tool_needed:
        pool_tools = news_pool.get_items_for_category(Category.TOOL, tool_needed - len(tool_items), fresh_first=True)
        final_items.extend(pool_tools)
        if pool_tools:
            print(f"  [INFO] TOOL: {len(pool_tools)} items from pool")
    
    # GUIDE
    guide_needed = targets[Category.GUIDE]
    final_items.extend(guide_items[:guide_needed])
    if len(guide_items) < guide_needed:
        pool_guides = news_pool.get_items_for_category(Category.GUIDE, guide_needed - len(guide_items), fresh_first=False)  # GUIDEは古いのから消化
        final_items.extend(pool_guides)
        if pool_guides:
            print(f"  [INFO] GUIDE: {len(pool_guides)} items from pool")

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

    # サイトのベースURL (デプロイ後のURL)
    base_url = "https://ai.negi-lab.com"

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

            article_id = f"{ymd}-{uuid.uuid4().hex[:8]}"
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

            # Determine tags for Hugo front matter
            tags = ["GenAI"]
            if item.category == Category.NEWS:
                tags.extend(["速報", "AIニュース"])
            elif item.category == Category.TOOL:
                tags.extend(["ツール", "レビュー"])
            else:
                tags.extend(["ガイド", "チュートリアル"])

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
            success_count += 1

            # X投稿用のキューに追加（デプロイ後投稿用）
            article_url = f"{base_url}/posts/{article_id}/"
            twitter_queue = TwitterPostingQueue(repo_root / "twitter_queue.json")
            twitter_queue.add(TwitterQueueItem(
                article_id=article_id,
                title=result.title,
                url=article_url,
                category=item.category.value,
                viral_tags=result.viral_tags,
                hook_text=result.hook_text,
                summary_text=result.summary_text,
                question_text=result.question_text,
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
                    hook_text=result.hook_text,
                    summary_text=result.summary_text,
                    question_text=result.question_text,
                ):
                    twitter_queue.mark_posted(article_id)
                    print(f"  ✓ Posted to X (Thread style)")
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

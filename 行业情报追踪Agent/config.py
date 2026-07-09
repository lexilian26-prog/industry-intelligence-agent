import os
from dotenv import load_dotenv

load_dotenv()

# Claude API 配置
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = "https://llm-gateway.momenta.works"
ANTHROPIC_MODEL = "claude-sonnet-4.6"

# 关键词过滤（只抓这些话题相关的文章）
KEYWORDS = [
    "自动驾驶", "智能驾驶", "新能源", "电动车", "大模型",
    "人工智能", "AI", "激光雷达", "智能座舱", "辅助驾驶",
    "autonomous", "EV", "LLM", "self-driving"
]

# RSS 订阅源
RSS_FEEDS = [
    # 中文科技媒体
    {"name": "36氪",   "url": "https://36kr.com/feed"},
    {"name": "虎嗅",   "url": "https://www.huxiu.com/rss/0.xml"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml"},
    # 英文科技媒体
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge",  "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Electrek",   "url": "https://electrek.co/feed/"},
]

# 数据库路径
DB_PATH = "database.db"

# 每篇文章发送给 Claude 的最大字数（控制费用）
MAX_ARTICLE_CHARS = 1500

# 定时任务：每天几点自动抓取（24小时制）
FETCH_HOUR = 8

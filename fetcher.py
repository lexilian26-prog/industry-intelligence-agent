import sys
import feedparser
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime
import config

def keyword_match(text):
    """检查文本是否包含目标关键词"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in config.KEYWORDS)

def is_today(entry):
    """判断文章是否为今天发布（转换为本地时间再比较）"""
    import calendar
    today = datetime.now().date()
    if entry.get("published_parsed"):
        # published_parsed 是 UTC，转为本地时间
        utc_timestamp = calendar.timegm(entry.published_parsed)
        pub_local = datetime.fromtimestamp(utc_timestamp).date()
        return pub_local == today
    raw = entry.get("published", "")
    return today.strftime("%d %b %Y") in raw

def fetch_article_content(url):
    """抓取文章正文"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:config.MAX_ARTICLE_CHARS]
    except Exception:
        return ""

def fetch_rss(feed_info):
    """解析单个 RSS 源，只返回当天且命中关键词的文章"""
    articles = []
    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries:
            # 只保留今天的文章
            if not is_today(entry):
                continue

            title     = entry.get("title", "")
            summary   = entry.get("summary", "")
            link      = entry.get("link", "")
            published = entry.get("published", str(datetime.now()))

            if not keyword_match(title + summary):
                continue

            articles.append({
                "source":    feed_info["name"],
                "title":     title,
                "url":       link,
                "summary":   BeautifulSoup(summary, "html.parser").get_text()[:500],
                "published": published,
            })
    except Exception as e:
        print(f"[fetcher] {feed_info['name']} 抓取失败: {e}")
    return articles

def fetch_all():
    """遍历所有 RSS 源，汇总当天文章"""
    all_articles = []
    for feed in config.RSS_FEEDS:
        print(f"[fetcher] 正在抓取: {feed['name']}")
        articles = fetch_rss(feed)
        print(f"[fetcher]   命中 {len(articles)} 篇")
        all_articles.extend(articles)
    print(f"[fetcher] 共采集 {len(all_articles)} 篇文章")
    return all_articles

if __name__ == "__main__":
    results = fetch_all()
    for a in results:
        print(f"\n[{a['source']}] {a['title']}")
        print(f"  {a['url']}")

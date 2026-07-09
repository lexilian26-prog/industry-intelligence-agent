import sys
import sqlite3
import config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def init_db():
    """初始化数据库，创建文章表"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            source    TEXT,
            title     TEXT,
            url       TEXT UNIQUE,
            summary   TEXT,
            published TEXT,
            category  TEXT,
            score     INTEGER,
            ai_summary TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()
    conn.close()

def save_articles(articles):
    """保存文章，已存在的（相同 URL）自动跳过"""
    conn = sqlite3.connect(config.DB_PATH)
    new_count = 0
    for a in articles:
        try:
            conn.execute(
                "INSERT INTO articles (source, title, url, summary, published) VALUES (?,?,?,?,?)",
                (a["source"], a["title"], a["url"], a["summary"], a["published"])
            )
            new_count += 1
        except sqlite3.IntegrityError:
            pass  # URL 重复，跳过
    conn.commit()
    conn.close()
    print(f"[processor] 新增 {new_count} 篇，跳过重复 {len(articles) - new_count} 篇")
    return new_count

def get_unanalyzed():
    """获取还没有 AI 分析结果的文章"""
    conn = sqlite3.connect(config.DB_PATH)
    rows = conn.execute(
        "SELECT id, title, summary FROM articles WHERE ai_summary IS NULL"
    ).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "summary": r[2]} for r in rows]

def update_analysis(article_id, category, score, ai_summary):
    """写入 AI 分析结果"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        "UPDATE articles SET category=?, score=?, ai_summary=? WHERE id=?",
        (category, score, ai_summary, article_id)
    )
    conn.commit()
    conn.close()

def delete_article(article_id):
    """删除单篇文章"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("DELETE FROM articles WHERE id=?", (article_id,))
    conn.commit()
    conn.close()

def get_today_articles():
    """获取今天已分析的所有文章，按重要性倒序"""
    conn = sqlite3.connect(config.DB_PATH)
    rows = conn.execute("""
        SELECT source, title, url, category, score, ai_summary, published
        FROM articles
        WHERE date(created_at) = date('now','localtime')
          AND ai_summary IS NOT NULL
        ORDER BY score DESC
    """).fetchall()
    conn.close()
    return [
        {
            "source": r[0], "title": r[1], "url": r[2],
            "category": r[3], "score": r[4],
            "ai_summary": r[5], "published": r[6]
        }
        for r in rows
    ]

if __name__ == "__main__":
    init_db()
    print("[processor] 数据库初始化完成")

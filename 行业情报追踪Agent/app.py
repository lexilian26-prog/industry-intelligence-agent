import streamlit as st
import importlib
import processor
importlib.reload(processor)
import analyzer
importlib.reload(analyzer)
import fetcher
importlib.reload(fetcher)
import config

st.set_page_config(page_title="行业情报追踪", page_icon="📡", layout="wide")

processor.init_db()

st.title("📡 行业情报追踪 Agent")
st.caption("自动驾驶 · 新能源 · AI — 每日动态")

with st.sidebar:
    st.header("控制面板")
    run = st.button("🔄 立即抓取 & 分析", use_container_width=True)
    st.divider()
    st.caption("每天 08:00 自动运行（需启动 scheduler.py）")

if run:
    # ── 阶段一：抓取 ──────────────────────────────────────
    st.subheader("第一步：抓取文章")
    feeds = config.RSS_FEEDS
    fetch_bar    = st.progress(0, text="准备中...")
    fetch_status = st.empty()

    all_articles = []
    for i, feed in enumerate(feeds):
        fetch_status.caption(f"正在抓取：{feed['name']}  ({i+1}/{len(feeds)})")
        articles = fetcher.fetch_rss(feed)
        all_articles.extend(articles)
        fetch_bar.progress((i + 1) / len(feeds), text=f"抓取进度 {i+1}/{len(feeds)}")

    new_count = processor.save_articles(all_articles)
    fetch_status.caption(f"抓取完成，共命中 {len(all_articles)} 篇，新增 {new_count} 篇")

    # ── 阶段二：AI 分析 ────────────────────────────────────
    st.subheader("第二步：AI 分析")
    pending = processor.get_unanalyzed()
    total = len(pending)

    if total == 0:
        st.info("没有待分析的新文章。")
    else:
        analyze_bar    = st.progress(0, text="准备分析...")
        analyze_status = st.empty()
        kept = 0
        dropped = 0

        for i, article in enumerate(pending):
            analyze_status.caption(f"正在分析（{i+1}/{total}）：{article['title'][:40]}")
            result = analyzer.analyze_article(article)

            if result["score"] <= 2:
                # 低分直接删除，不保留
                processor.delete_article(article["id"])
                dropped += 1
            else:
                processor.update_analysis(
                    article["id"], result["category"], result["score"], result["summary"]
                )
                kept += 1

            analyze_bar.progress(
                (i + 1) / total,
                text=f"分析进度 {i+1}/{total} — 保留 {kept} 篇 / 过滤 {dropped} 篇"
            )

        analyze_status.caption(f"分析完成：保留 {kept} 篇，过滤低质量 {dropped} 篇")

    st.success("全部完成！")
    st.rerun()

# ── 今日文章展示 ───────────────────────────────────────────
today_articles = processor.get_today_articles()

if not today_articles:
    st.info("今日暂无数据，点击左侧「立即抓取」按钮获取最新情报。")
    st.stop()

# 综述用 session_state 缓存，只在文章数量变化时重新生成
article_count = len(today_articles)
if st.session_state.get("digest_count") != article_count:
    with st.spinner("生成今日综述..."):
        st.session_state["digest"] = analyzer.generate_daily_digest(today_articles)
        st.session_state["digest_count"] = article_count

st.subheader("📝 今日行业综述")
st.info(st.session_state["digest"])

st.divider()

categories = ["全部"] + sorted({a["category"] for a in today_articles})
selected = st.selectbox("按分类筛选", categories)

filtered = today_articles if selected == "全部" else [
    a for a in today_articles if a["category"] == selected
]

st.subheader(f"📰 今日情报（{len(filtered)} 篇）")

SCORE_COLOR = {5: "🔴", 4: "🟠", 3: "🟡", 2: "🟢", 1: "⚪"}

for a in filtered:
    score_icon = SCORE_COLOR.get(a["score"], "⚪")
    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**[{a['title']}]({a['url']})**")
            st.caption(f"{score_icon} 重要性 {a['score']}/5 · {a['category']} · {a['source']}")
            st.write(a["ai_summary"])
        with col2:
            st.caption(a["published"][:10] if a["published"] else "")

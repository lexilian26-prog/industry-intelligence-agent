# AI 项目集

用 Claude AI 构建的实用 Agent 工具集，覆盖行业情报自动化和数据分析两个场景。每个项目均为独立可运行的 Streamlit 应用，开箱即用。

---

## 项目列表

### [行业情报追踪 Agent](./行业情报追踪Agent/)

> 每天自动替你刷完行业新闻，5 分钟掌握当日最值得关注的动态。

从 6 个中英文媒体（36氪、虎嗅、钛媒体、TechCrunch、The Verge、Electrek）自动抓取自动驾驶 / 新能源 / AI 领域的当日资讯，由 Claude 对每篇文章完成分类、重要性评分（1-5 分）和一句话摘要，过滤低质内容后生成结构化情报简报，并附每日行业趋势总结。支持按分类筛选、定时自动运行。

**技术栈**：Python · Claude AI · Streamlit · feedparser · SQLite · APScheduler

---

### [数据分析 Agent](./数据分析Agent/)

> 不会写代码也能做数据分析，上传文件即可获得完整的 AI 分析报告。

上传 CSV / Excel 后，AI 自动识别数据结构并概括内容，自动生成 6 种可视化图表（柱状图、散点图、折线图、热力图、直方图、饼图），支持按类别筛选联动所有图表。Claude 生成包含核心发现、异常点、趋势判断、行动建议的结构化解读，并支持多轮追问。最终可细粒度勾选导出内容，生成 PDF 或 Word 分析报告。

**技术栈**：Python · Claude AI · Streamlit · Plotly · pandas · fpdf2 · python-docx

---

> 持续更新中，更多项目陆续上传。

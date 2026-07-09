import json
import sys
import anthropic
import config
import processor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

client = anthropic.Anthropic(
    api_key=config.ANTHROPIC_API_KEY,
    base_url=config.ANTHROPIC_BASE_URL,
)

CATEGORIES = ["政策法规", "技术突破", "融资并购", "产品发布", "竞争动态", "其他"]

def analyze_article(article):
    """对单篇文章做分类、评分、摘要"""
    prompt = f"""你是一个专注于自动驾驶、新能源、AI 领域的行业分析师。

请分析以下文章，返回 JSON 格式结果（只返回 JSON，不要 markdown 代码块，不要其他内容）：

标题：{article['title']}
内容摘要：{article['summary']}

评分标准（重要性 1-5 分）：
5分：重大政策发布、头部公司重要产品/技术突破、亿级以上融资、行业里程碑事件
4分：知名公司新动态、行业重要数据报告、中等规模融资、有实质影响的产品更新
3分：一般公司动态、常规产品迭代、行业分析观点、中小规模融资
2分：边缘话题、信息量较少的资讯、与行业关联较弱的内容
1分：广告软文、无实质内容、与自动驾驶/新能源/AI 行业基本无关

category 必须严格从以下选项中选一个，不能使用其他词：{'/'.join(CATEGORIES)}

返回格式：
{{"category": "必须是上面选项之一", "score": 重要性评分整数, "summary": "一句话30字以内概括"}}"""

    try:
        msg = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        # 如果返回的分类不在列表里，归入最近似的或"其他"
        if result.get("category") not in CATEGORIES:
            result["category"] = "其他"
        # score 强制转为整数并限制在 1-5
        result["score"] = max(1, min(5, int(result.get("score", 1))))
        return result
    except Exception as e:
        print(f"[analyzer] 分析失败: {e}")
        return {"category": "其他", "score": 1, "summary": article["summary"][:50]}

def generate_daily_digest(articles):
    """根据当天所有文章生成行业综述"""
    if not articles:
        return "今日暂无相关行业动态。"

    items = "\n".join(
        f"- [{a['category']}] {a['title']}：{a['ai_summary']}"
        for a in articles[:20]  # 最多取20条
    )

    prompt = f"""你是一位资深的自动驾驶/新能源/AI 行业分析师。

以下是今日行业动态摘要：
{items}

请写一段 150 字左右的今日行业综述，要求：
1. 提炼最重要的 2-3 个趋势或事件
2. 语言简洁专业
3. 不要分点，写成连贯段落"""

    try:
        msg = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[analyzer] 综述生成失败: {e}")
        return "综述生成失败，请检查 API 配置。"

def run_analysis():
    """分析所有未处理的文章，低于3分的直接删除"""
    articles = processor.get_unanalyzed()
    print(f"[analyzer] 待分析文章: {len(articles)} 篇")
    kept = 0
    dropped = 0
    for a in articles:
        result = analyze_article(a)
        if result["score"] <= 2:
            processor.delete_article(a["id"])
            dropped += 1
            print(f"[analyzer] DROP [{result['score']}分] {a['title'][:30]}")
        else:
            processor.update_analysis(a["id"], result["category"], result["score"], result["summary"])
            kept += 1
            print(f"[analyzer] OK [{result['score']}分/{result['category']}] {a['title'][:30]}")
    print(f"[analyzer] 完成：保留 {kept} 篇，丢弃 {dropped} 篇")

if __name__ == "__main__":
    run_analysis()

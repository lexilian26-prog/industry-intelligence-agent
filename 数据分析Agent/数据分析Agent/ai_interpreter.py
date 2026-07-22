import anthropic
import config

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            base_url=config.ANTHROPIC_BASE_URL,
        )
    return _client


def interpret(stat_summary, user_context=""):
    """根据统计摘要生成 AI 解读报告"""
    context_part = f"\n用户补充背景：{user_context}" if user_context.strip() else ""
    prompt = f"""你是一名资深数据分析师。以下是一份数据集的统计摘要，请基于这些数据给出专业分析报告。

{stat_summary}{context_part}

请按以下结构输出（使用 Markdown 格式）：

## 核心发现
列出 3~5 条最重要的数据洞察，每条一句话。

## 异常点与风险
列出 2~4 条值得关注的异常或风险，每条格式如下：
- **[高/中/低风险]** 异常现象描述（原因：说明为何判定此风险等级）

## 趋势判断
基于数据描述整体趋势或规律（如有时间列则重点分析趋势）。

## 行动建议
给出 2~3 条基于数据可以做的决策或下一步行动。

请保持专业、简洁，避免废话。"""

    client = _get_client()
    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    # 被 token 限制截断时，继续补全
    if msg.stop_reason == "max_tokens":
        followup = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": text},
                {"role": "user", "content": "请继续完成上面未完成的内容，不要重复已有内容。"},
            ],
        )
        text += followup.content[0].text
    return text


def follow_up(stat_summary, history, question):
    """多轮追问"""
    messages = []
    for h in history:
        # API 要求第一条必须是 user，跳过开头的 assistant 消息（初始 AI 报告）
        if not messages and h["role"] == "assistant":
            continue
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({
        "role": "user",
        "content": f"以下是数据集统计摘要供参考：\n{stat_summary}\n\n我的问题：{question}"
    })
    client = _get_client()
    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1000,
        messages=messages,
    )
    return msg.content[0].text

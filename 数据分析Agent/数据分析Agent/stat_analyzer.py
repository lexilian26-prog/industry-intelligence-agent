import pandas as pd
import json
import config


def numeric_stats(df, numeric_cols):
    """计算数值列统计量"""
    if not numeric_cols:
        return {}
    desc = df[numeric_cols].describe().round(3)
    return desc.to_dict()


def category_stats(df, cat_cols, top_n=10):
    """计算类别列频次"""
    result = {}
    for col in cat_cols:
        counts = df[col].value_counts().head(top_n)
        result[col] = counts.to_dict()
    return result


def correlation_matrix(df, numeric_cols):
    """计算数值列相关矩阵"""
    if len(numeric_cols) < 2:
        return None
    return df[numeric_cols].corr().round(3)


def build_stat_summary(df, info):
    """组装发送给 AI 的统计摘要文本（可读格式）"""
    lines = []
    lines.append(f"数据集：{info['rows']} 行 × {info['cols']} 列")
    lines.append(f"列名：{', '.join(df.columns.tolist())}")

    if info["missing"]:
        lines.append("缺失值：" + "、".join(f"{k}({v}%)" for k, v in info["missing_pct"].items()))

    if info["numeric_cols"]:
        lines.append("\n数值列统计：")
        desc = df[info["numeric_cols"]].describe().round(2)
        for col in info["numeric_cols"]:
            s = desc[col]
            lines.append(
                f"  {col}：均值={s['mean']}，中位数={s['50%']}，"
                f"标准差={s['std']}，最小={s['min']}，最大={s['max']}"
            )

    if info["cat_cols"]:
        lines.append("\n类别列分布：")
        for col in info["cat_cols"]:
            counts = df[col].value_counts()
            n = counts.nunique() if hasattr(counts, 'nunique') else len(counts)
            top = "、".join(f"{k}({v})" for k, v in counts.head(5).items())
            lines.append(f"  {col}（{len(counts)}种）：{top}")

    if info["datetime_cols"]:
        lines.append("\n日期列：")
        for col in info["datetime_cols"]:
            lines.append(f"  {col}：{str(df[col].min())[:10]} ~ {str(df[col].max())[:10]}")

    text = "\n".join(lines)
    if len(text) > config.MAX_STAT_CHARS:
        text = text[:config.MAX_STAT_CHARS] + "\n...(摘要已截断)"
    return text

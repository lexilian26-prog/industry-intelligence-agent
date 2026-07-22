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


def build_cleaning_context(df, info):
    """构建用于 AI 生成清洗建议的上下文文本"""
    lines = [f"数据集：{info['rows']} 行 × {info['cols']} 列"]

    dupes = int(df.duplicated().sum())
    lines.append(f"重复行：{dupes} 行")

    if info["missing"]:
        for col, cnt in info["missing"].items():
            pct = info["missing_pct"][col]
            lines.append(f"缺失值：列「{col}」缺失 {cnt} 行（{pct}%）")
    else:
        lines.append("缺失值：无")

    outlier_msgs = []
    for col in info["numeric_cols"]:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        q1, q3 = float(series.quantile(0.25)), float(series.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0:
            continue
        n_out = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
        if n_out > 0:
            outlier_msgs.append(f"列「{col}」有 {n_out} 个异常值（IQR 方法），范围：{q1 - 1.5*iqr:.2f}～{q3 + 1.5*iqr:.2f}")
    if outlier_msgs:
        lines.extend(outlier_msgs)
    else:
        lines.append("异常值：数值列未检测到明显异常值")

    for col in info["cat_cols"]:
        ratio = df[col].nunique() / max(len(df), 1)
        if ratio > 0.3:
            lines.append(f"高唯一值：列「{col}」唯一值占比 {ratio:.0%}，疑似 ID 类列，建议确认是否需要")

    return "\n".join(lines)

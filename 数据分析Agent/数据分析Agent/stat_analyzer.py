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


def detect_issues(df, info, group_col=None):
    """结构化检测数据质量问题，供清洗 Tab 使用。
    group_col: 按该列分组后分别检测异常值，避免不同类别价差被误报。
    """
    issues = {}

    dupes = int(df.duplicated().sum())
    if dupes > 0:
        issues["duplicates"] = {"count": dupes}

    if info["missing"]:
        issues["missing"] = {}
        for col, cnt in info["missing"].items():
            pct = info["missing_pct"][col]
            col_type = "numeric" if col in info["numeric_cols"] else "category"
            issues["missing"][col] = {"count": cnt, "pct": pct, "type": col_type}

    outliers = {}
    for col in info["numeric_cols"]:
        if group_col and group_col in df.columns and group_col != col:
            # 按分组分别计算 IQR，每组内判断异常值
            outlier_mask = pd.Series(False, index=df.index)
            bounds_per_group = {}
            for grp, grp_df in df.groupby(group_col):
                series = grp_df[col].dropna()
                if len(series) < 4:
                    continue
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                mask = (grp_df[col] < lower) | (grp_df[col] > upper)
                outlier_mask.loc[grp_df.index] = outlier_mask.loc[grp_df.index] | mask
                bounds_per_group[str(grp)] = {"lower": round(lower, 2), "upper": round(upper, 2)}
            n_out = int(outlier_mask.sum())
            if n_out > 0:
                outliers[col] = {
                    "count": n_out,
                    "mask": outlier_mask,
                    "group_col": group_col,
                    "bounds_per_group": bounds_per_group,
                }
        else:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            q1, q3 = float(series.quantile(0.25)), float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            n_out = int(mask.sum())
            if n_out > 0:
                outliers[col] = {
                    "count": n_out,
                    "mask": mask,
                    "lower": lower,
                    "upper": upper,
                }
    if outliers:
        issues["outliers"] = outliers

    return issues


def apply_cleaning(df, info, actions):
    """根据用户选择的 actions 执行清洗，返回 (cleaned_df, log)"""
    df = df.copy()
    log = []

    if actions.get("duplicates") == "drop":
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed > 0:
            log.append(f"删除重复行 {removed} 行")

    for col, action in actions.get("missing", {}).items():
        if col not in df.columns or action == "keep":
            continue
        n_miss = int(df[col].isnull().sum())
        if n_miss == 0:
            continue
        if action == "drop_row":
            df = df.dropna(subset=[col])
            log.append(f"「{col}」删除含缺失值的行（{n_miss} 行）")
        elif action == "fill_mean" and col in info["numeric_cols"]:
            val = round(float(df[col].mean()), 4)
            df[col] = df[col].fillna(val)
            log.append(f"「{col}」用均值 {val} 填充 {n_miss} 个缺失值")
        elif action == "fill_median" and col in info["numeric_cols"]:
            val = round(float(df[col].median()), 4)
            df[col] = df[col].fillna(val)
            log.append(f"「{col}」用中位数 {val} 填充 {n_miss} 个缺失值")
        elif action == "fill_mode":
            mode_vals = df[col].mode()
            if len(mode_vals) > 0:
                df[col] = df[col].fillna(mode_vals[0])
                log.append(f"「{col}」用众数「{mode_vals[0]}」填充 {n_miss} 个缺失值")
        elif action == "fill_zero":
            df[col] = df[col].fillna(0)
            log.append(f"「{col}」用 0 填充 {n_miss} 个缺失值")

    for col, action in actions.get("outliers", {}).items():
        if col not in df.columns or action == "keep":
            continue
        meta = actions.get("_outlier_meta", {}).get(col, {})
        mask = meta.get("mask")
        if mask is None:
            # 无分组时退回全局 IQR
            series = df[col].dropna()
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
        # 对齐索引（apply 过程中行可能已被删除）
        mask = mask.reindex(df.index, fill_value=False)
        n_out = int(mask.sum())
        if n_out == 0:
            continue
        if action == "clip":
            # 按组截断或全局截断
            if meta.get("group_col") and meta.get("bounds_per_group"):
                group_col = meta["group_col"]
                for grp, bounds in meta["bounds_per_group"].items():
                    grp_idx = df[df[group_col].astype(str) == grp].index
                    df.loc[grp_idx, col] = df.loc[grp_idx, col].clip(
                        lower=bounds["lower"], upper=bounds["upper"]
                    )
                log.append(f"「{col}」按「{group_col}」分组截断异常值（{n_out} 个）")
            else:
                lower = meta.get("lower", df[col].min())
                upper = meta.get("upper", df[col].max())
                df[col] = df[col].clip(lower=lower, upper=upper)
                log.append(f"「{col}」将 {n_out} 个异常值截断至 [{lower:.2f}, {upper:.2f}]")
        elif action == "drop_row":
            df = df[~mask]
            log.append(f"「{col}」删除含异常值的行（{n_out} 行）")

    return df, log


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

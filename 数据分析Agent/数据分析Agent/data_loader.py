import pandas as pd
import io


def load_file(uploaded_file):
    """解析上传的 CSV 或 Excel 文件，返回 DataFrame"""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        # 自动探测编码
        raw = uploaded_file.read()
        for enc in ["utf-8", "gbk", "utf-8-sig"]:
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=enc)
                break
            except Exception:
                continue
        else:
            df = pd.read_csv(io.BytesIO(raw), encoding="utf-8", errors="replace")
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("仅支持 CSV 或 Excel 文件")

    # 尝试将疑似日期列转换为 datetime
    for col in df.columns:
        if df[col].dtype == object:
            try:
                converted = pd.to_datetime(df[col])
                if converted.notna().sum() / max(len(df), 1) > 0.7:
                    df[col] = converted
            except Exception:
                pass

    return df


def classify_columns(df):
    """将列分为数值列、日期列、类别列，过滤ID列和二值列"""
    raw_numeric = df.select_dtypes(include="number").columns.tolist()
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()

    numeric_cols = []
    binary_cols = []
    for col in raw_numeric:
        if df[col].nunique() <= 2:
            binary_cols.append(col)
        else:
            numeric_cols.append(col)

    raw_cat = [c for c in df.columns if c not in raw_numeric and c not in datetime_cols]
    # 唯一值比例超过 50% 视为 ID 列，排除出类别列
    cat_cols = [c for c in raw_cat if df[c].nunique() / max(len(df), 1) <= 0.5]
    # 二值列加入类别列
    cat_cols = binary_cols + cat_cols

    return numeric_cols, datetime_cols, cat_cols


def basic_info(df):
    """返回数据基本信息字典"""
    numeric_cols, datetime_cols, cat_cols = classify_columns(df)
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    return {
        "rows": len(df),
        "cols": len(df.columns),
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "cat_cols": cat_cols,
        "missing": missing[missing > 0].to_dict(),
        "missing_pct": missing_pct[missing_pct > 0].to_dict(),
    }

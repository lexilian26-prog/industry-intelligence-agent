import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 渐变色板选项（用于柱状图/热力图）
SEQUENTIAL_PALETTES = ["Blues", "Greens", "Oranges", "Reds", "Purples",
                       "Teal", "Viridis", "Plasma", "Cividis", "Magma"]
# 离散色板选项（用于散点图多分类）
QUALITATIVE_PALETTES = ["Plotly", "D3", "G10", "T10", "Alphabet",
                        "Bold", "Pastel", "Safe", "Vivid", "Antique"]
# 热力图色板
DIVERGING_PALETTES = ["RdBu_r", "RdYlGn", "BrBG", "PiYG", "PRGn",
                      "PuOr", "Spectral", "RdGy", "RdYlBu", "balance"]

# 饼图专用多色方案（名称 → 颜色列表，前6色用于预览）
PIE_PALETTES = {
    "商务蓝灰":  ["#1F5EBF", "#4A7FD4", "#7AAAE8", "#A8C4F0", "#6B7B8D", "#9BAEBB"],
    "自然绿棕":  ["#1A7A4A", "#4CAF78", "#8BC4A0", "#C4882A", "#E0AB5A", "#F5D08A"],
    "暖色系":    ["#C85A00", "#E07A20", "#F0A050", "#D4402A", "#E87050", "#F5A080"],
    "冷色系":    ["#1F3A8B", "#2E6EBF", "#4A9FD4", "#1A6B7A", "#2E9BAA", "#50C8D4"],
    "莫兰迪":    ["#8E9BB5", "#B5A89E", "#9EAF9A", "#C4B0A0", "#A0B0B8", "#C8B8C0"],
    "高对比":    ["#1F5EBF", "#C85A00", "#1A7A4A", "#8B1A2E", "#4A5568", "#7B3FA0"],
    "Plotly默认":["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"],
    "柔和粉彩":  ["#A8C4F0", "#F0A8A8", "#A8F0C4", "#F0D8A8", "#D0A8F0", "#A8E8F0"],
}

# 预设配色主题（sequential / qualitative / diverging / single）
def make_heatmap_scale(hex_color):
    """负相关→浅灰，零→白，正相关→主题色"""
    return [[0.0, "#c8c8c8"], [0.5, "#ffffff"], [1.0, hex_color]]


def make_sequential_scale(hex_color):
    """浅灰→主题色，用于柱状图渐变"""
    return [[0.0, "#e8e8e8"], [1.0, hex_color]]


def make_qualitative_palette(hex_color, n=12):
    """以指定颜色为起点，色相均匀旋转生成 n 个离散颜色"""
    import colorsys
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
    hue, s, v = colorsys.rgb_to_hsv(r, g, b)
    s, v = max(s, 0.55), max(v, 0.72)
    result = []
    for i in range(n):
        nh = (hue + i / n) % 1.0
        nr, ng, nb = colorsys.hsv_to_rgb(nh, s, v)
        result.append("#{:02x}{:02x}{:02x}".format(int(nr*255), int(ng*255), int(nb*255)))
    return result


def _resolve_qualitative(palette):
    """palette 可以是 plotly 命名字符串，也可以是颜色列表"""
    if isinstance(palette, list):
        return palette
    return getattr(px.colors.qualitative, palette, px.colors.qualitative.Plotly)


# 预设商务主题（每个只需一个基准色，渐变/多色板由工具函数自动生成）
COLOR_THEMES = {
    "宝蓝":  {"single": "#1F5EBF"},   # 专业感强，适合金融/咨询报告
    "墨绿":  {"single": "#1A7A4A"},   # 稳重自然，适合可持续/环保主题
    "深橙":  {"single": "#C85A00"},   # 活力醒目，适合销售/市场报告
    "钢铁灰":{"single": "#4A5568"},   # 中性极简，适合技术/数据报告
    "酒红":  {"single": "#8B1A2E"},   # 高级感，适合品牌/高端报告
    "靛蓝":  {"single": "#2E4A8B"},   # 权威沉稳，适合政府/学术报告
}


def histogram(df, col, color="#636EFA"):
    import numpy as np
    data = df[col].dropna()
    mean_val = float(data.mean())
    median_val = float(data.median())
    std_val = float(data.std())
    skew_val = float(data.skew())

    if skew_val > 1:
        skew_label = "强右偏"
    elif skew_val > 0.5:
        skew_label = "轻微右偏"
    elif skew_val < -1:
        skew_label = "强左偏"
    elif skew_val < -0.5:
        skew_label = "轻微左偏"
    else:
        skew_label = "近似对称"

    fig = go.Figure()

    # 直方图（归一化为概率密度）
    fig.add_trace(go.Histogram(
        x=data, nbinsx=30,
        histnorm="probability density",
        marker_color=color, opacity=0.75,
        name="频率分布",
    ))

    # 正态分布曲线
    x_range = np.linspace(data.min(), data.max(), 300)
    y_normal = (1 / (std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mean_val) / std_val) ** 2)
    fig.add_trace(go.Scatter(
        x=x_range, y=y_normal,
        mode="lines",
        line=dict(color="black", width=2),
        name="正态曲线",
    ))

    # 均值竖线（红色）& 中位数竖线（蓝色）
    fig.add_vline(x=mean_val, line_dash="dash", line_color="red",
                  annotation_text=f"均值 {mean_val:.2f}",
                  annotation_position="top right",
                  annotation_font_color="red")
    fig.add_vline(x=median_val, line_dash="dot", line_color="#1f77b4",
                  annotation_text=f"中位数 {median_val:.2f}",
                  annotation_position="top left",
                  annotation_font_color="#1f77b4")

    fig.update_layout(
        title=f"{col} 分布  |  σ={std_val:.2f}  偏度={skew_val:.2f}（{skew_label}）",
        xaxis_title=col,
        yaxis_title="概率密度",
        bargap=0.05,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def box_plot(df, col, group_col=None, color="#636EFA"):
    if group_col:
        colors = make_qualitative_palette(color)
        fig = px.box(df, x=group_col, y=col,
                     title=f"{col} 箱线图（按 {group_col} 分组）",
                     color=group_col,
                     color_discrete_sequence=colors,
                     points="outliers")
    else:
        fig = px.box(df, y=col, title=f"{col} 箱线图", points="outliers")
        fig.update_traces(marker_color=color, line_color=color)

    fig.update_traces(boxmean=True)
    fig.update_layout(showlegend=bool(group_col))
    return fig


def time_series(df, date_col, value_col, color="#636EFA", freq="D", agg="mean"):
    """时序折线图，支持按日/周/月聚合"""
    freq_label = {"D": "日", "W": "周", "ME": "月"}
    agg_label  = {"mean": "均值", "sum": "总和", "median": "中位数"}
    tmp = df[[date_col, value_col]].dropna().copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col])
    tmp = tmp.set_index(date_col).resample(freq)[value_col].agg(agg).reset_index()
    title = f"{value_col} 随时间变化（按{freq_label.get(freq,'日')}·{agg_label.get(agg,'均值')}）"
    fig = px.line(tmp, x=date_col, y=value_col, title=title)
    fig.update_traces(line_color=color)
    return fig


def bar_chart(df, col, top_n=15, color="#636EFA"):
    counts = df[col].value_counts().head(top_n).reset_index()
    counts.columns = [col, "数量"]
    fig = px.bar(counts, x=col, y="数量", title=f"{col} 频次分布（Top {top_n}）")
    fig.update_traces(marker_color=color)
    return fig


def pie_chart(df, col, top_n=8, palette_name="商务蓝灰", custom_colors=None):
    counts = df[col].value_counts().head(top_n)
    if custom_colors:
        # custom_colors: {类别名: hex} 字典
        colors = [custom_colors.get(str(name), "#636EFA") for name in counts.index]
    else:
        base = PIE_PALETTES.get(palette_name, PIE_PALETTES["商务蓝灰"])
        colors = [base[i % len(base)] for i in range(len(counts))]
    fig = px.pie(values=counts.values, names=counts.index, title=f"{col} 占比",
                 color_discrete_sequence=colors)
    return fig


def correlation_heatmap(corr_df, color="#636EFA"):
    # 列名截断：超过8字符时缩短，避免标签重叠
    short = {c: (c[:7] + "…" if len(c) > 8 else c) for c in corr_df.columns}
    corr_display = corr_df.rename(columns=short, index=short)
    scale = make_heatmap_scale(color)
    fig = px.imshow(
        corr_display,
        text_auto=".2f",
        color_continuous_scale=scale,
        zmin=-1, zmax=1,
        title="相关性热力图",
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def aggregated_bar(df, cat_col, val_col, agg="mean", color="#636EFA"):
    agg_func = {"mean": "均值", "sum": "总和", "median": "中位数"}
    label = agg_func.get(agg, agg)
    grouped = df.groupby(cat_col)[val_col].agg(agg).reset_index()
    grouped.columns = [cat_col, val_col]
    grouped = grouped.sort_values(val_col, ascending=False)
    fig = px.bar(
        grouped, x=cat_col, y=val_col,
        title=f"{cat_col} — {val_col}（{label}）",
        text_auto=".2f",
        color=val_col,
        color_continuous_scale=make_sequential_scale(color),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    return fig


def scatter_plot(df, x_col, y_col, color_col=None, color="#636EFA", opacity=0.7):
    title = f"{x_col} vs {y_col}"
    if color_col:
        title += f"（按 {color_col} 着色）"
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                         title=title, opacity=opacity,
                         color_discrete_sequence=make_qualitative_palette(color))
    else:
        fig = px.scatter(df, x=x_col, y=y_col, title=title, opacity=opacity)
        fig.update_traces(marker_color=color)
    return fig

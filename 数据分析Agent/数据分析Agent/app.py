import re
import streamlit as st
import pandas as pd
import data_loader
import stat_analyzer
import chart_builder
import ai_interpreter
import report_exporter


def _clean_md(text):
    """去除 Markdown 符号，输出适合直接粘贴的纯文本"""
    lines = []
    for raw in text.split("\n"):
        line = raw.strip()
        if re.match(r"^-{3,}$", line):          # --- 分割线
            lines.append("")
            continue
        line = re.sub(r"^#{1,3}\s+", "", line)   # ## 标题
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)  # **粗体**
        line = re.sub(r"__(.+?)__", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        line = re.sub(r"`(.+?)`", r"\1", line)
        lines.append(line)
    return "\n".join(lines).strip()

st.set_page_config(page_title="数据分析 Agent", page_icon="📊", layout="wide")

st.markdown("""
<style>
/* 多选标签：背景深蓝绿，文字白色 */
span[data-baseweb="tag"] {
    background-color: #1a6b6b !important;
    color: white !important;
}
/* 多选标签删除按钮 */
span[data-baseweb="tag"] span[role="presentation"] {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ── 侧边栏 ─────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 数据分析 Agent")
    st.caption("上传数据 → AI 自动分析 → 生成报告")
    st.divider()

    uploaded = st.file_uploader(
        "上传 CSV 或 Excel 文件",
        type=["csv", "xlsx", "xls"],
        help="支持 UTF-8 / GBK 编码的 CSV，以及 .xlsx / .xls"
    )

    user_context = st.text_area(
        "补充背景（可选）",
        placeholder="例如：这是某公司2024年销售数据，关注季度趋势和地区差异...",
        height=80,
    )

    if uploaded:
        st.divider()
        st.caption("**数据概览**")

# ── 未上传状态 ─────────────────────────────────────────────
if not uploaded:
    st.title("📊 数据分析 Agent")
    st.info("请在左侧上传 CSV 或 Excel 文件开始分析。")
    st.markdown("""
**功能介绍：**
- 📁 支持 CSV / Excel 上传，自动识别数值、日期、类别列
- 📈 自动生成分布图、趋势图、相关性热力图
- 🤖 AI 解读核心发现、异常点、趋势判断、行动建议
- 💬 支持多轮追问
- 📄 一键导出 PDF 报告
""")
    st.stop()

# ── 加载数据 ───────────────────────────────────────────────
try:
    df = data_loader.load_file(uploaded)
except Exception as e:
    st.error(f"文件解析失败：{e}")
    st.stop()

info = data_loader.basic_info(df)

with st.sidebar:
    st.caption(f"行数：**{info['rows']}**　列数：**{info['cols']}**")
    if info["missing"]:
        st.caption(f"含缺失值列：{list(info['missing'].keys())}")

# ── Tab 布局 ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 数据预览", "📈 可视化分析", "🤖 AI 解读", "📄 导出报告"])

# ══ Tab1：数据预览 ══════════════════════════════════════════
with tab1:
    col_title, col_btn = st.columns([8, 1])
    col_title.subheader("数据预览")
    if col_btn.button("🔄 刷新", key="refresh_tab1", help="重新生成 AI 数据概览"):
        st.session_state.pop("overview_cache_key", None)
        st.session_state.pop("overview_text", None)

    # 简要概括（AI 生成，缓存避免重复调用）
    overview_key = f"overview_{uploaded.name}_{info['rows']}"
    if st.session_state.get("overview_cache_key") != overview_key:
        # 构造轻量 prompt：列名 + 每列前3个样本值
        sample_info = []
        for col in df.columns:
            samples = df[col].dropna().head(3).tolist()
            sample_info.append(f"{col}: {samples}")
        overview_prompt = (
            f"以下是一份数据表的列名及样本值：\n" + "\n".join(sample_info) +
            f"\n\n共 {info['rows']} 行，请用 2~3 句话概括这份表格主要记录了什么内容，"
            "包括主题、涉及的维度和核心指标。语言简洁自然，不要列举所有列名。"
        )
        with st.spinner("生成数据概览..."):
            try:
                import ai_interpreter
                client = ai_interpreter._get_client()
                import config as _cfg
                msg = client.messages.create(
                    model=_cfg.ANTHROPIC_MODEL,
                    max_tokens=200,
                    messages=[{"role": "user", "content": overview_prompt}],
                )
                st.session_state["overview_text"] = msg.content[0].text
                st.session_state["overview_cache_key"] = overview_key
            except Exception:
                st.session_state["overview_text"] = ""
                st.session_state["overview_cache_key"] = overview_key
    if st.session_state.get("overview_text"):
        st.info(st.session_state["overview_text"])

    st.dataframe(df.head(100), width="stretch")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总行数", info["rows"])
    c2.metric("总列数", info["cols"])
    c3.metric("数值列", len(info["numeric_cols"]))
    c4.metric("类别列", len(info["cat_cols"]))

    if info["missing"]:
        st.warning("**缺失值情况：**")
        miss_df = pd.DataFrame({
            "列名": list(info["missing"].keys()),
            "缺失数量": list(info["missing"].values()),
            "缺失比例(%)": [info["missing_pct"][k] for k in info["missing"]],
        })
        st.dataframe(miss_df, width="stretch")

    st.subheader("基础统计")
    if info["numeric_cols"]:
        st.markdown("**数值列**")
        desc = df[info["numeric_cols"]].describe().T.round(3)
        desc.index.name = "列名"
        desc.columns = ["数量", "均值", "标准差", "最小值", "25%", "中位数", "75%", "最大值"]
        st.dataframe(desc, width="stretch")

    if info["cat_cols"]:
        st.markdown("**类别列**")
        cat_stats = []
        for col in info["cat_cols"]:
            top = df[col].value_counts()
            cat_stats.append({
                "列名": col,
                "唯一值数": df[col].nunique(),
                "最高频值": top.index[0] if len(top) else "-",
                "最高频次": int(top.iloc[0]) if len(top) else 0,
                "空值数": int(df[col].isnull().sum()),
            })
        st.dataframe(pd.DataFrame(cat_stats).set_index("列名"), width="stretch")

    if info["datetime_cols"]:
        st.markdown("**日期列**")
        dt_stats = []
        for col in info["datetime_cols"]:
            mn, mx = df[col].min(), df[col].max()
            dt_stats.append({
                "列名": col,
                "最早": str(mn)[:10],
                "最晚": str(mx)[:10],
                "跨度（天）": (mx - mn).days,
                "空值数": int(df[col].isnull().sum()),
            })
        st.dataframe(pd.DataFrame(dt_stats).set_index("列名"), width="stretch")

# ══ Tab2：可视化分析 ════════════════════════════════════════
with tab2:
    col_title2, col_btn2 = st.columns([8, 1])
    col_title2.subheader("可视化分析")
    if col_btn2.button("🔄 刷新", key="refresh_tab2", help="重置图表选项"):
        _reset_keys = (
            ["cmp_cat", "cmp_val", "cmp_agg", "cmp_color",
             "sc_x", "sc_y", "sc_color", "sc_color_pick", "sc_opacity",
             "ts_date", "ts_val", "ts_color", "ts_freq", "ts_agg",
             "hm_color", "hist_col", "hist_color", "box_group",
             "pie_cat", "pie_palette_name", "figures"]
            + [k for k in st.session_state if k.startswith("pie_cc_")]
            + [f"fcat_{c}" for c in info.get("cat_cols", [])]
            + [f"fnum_{c}" for c in info.get("numeric_cols", [])]
        )
        for k in _reset_keys:
            st.session_state.pop(k, None)
        st.rerun()

    # ── 数据筛选面板 ──────────────────────────────────────────
    df_plot = df.copy()
    _active_filters = []

    with st.expander("🔍 数据筛选", expanded=False):
        _clear_col, _ = st.columns([1, 6])
        if _clear_col.button("清除全部筛选", key="filter_clear"):
            for _c in info["cat_cols"]:
                st.session_state.pop(f"fcat_{_c}", None)
            for _c in info["numeric_cols"]:
                st.session_state.pop(f"fnum_{_c}", None)
            st.rerun()

        # 类别列：多选勾选框（唯一值 ≤ 30 才显示，避免日期等高唯一值列）
        _filterable_cats = [c for c in info["cat_cols"] if df[c].nunique() <= 30]
        if _filterable_cats:
            st.markdown("**类别列**")
            _cat_grid = st.columns(min(len(_filterable_cats), 3))
            for _i, _c in enumerate(_filterable_cats):
                _all_vals = sorted(df[_c].dropna().unique().tolist())
                _sel = _cat_grid[_i % 3].multiselect(
                    _c, _all_vals, default=_all_vals, key=f"fcat_{_c}"
                )
                if set(_sel) != set(_all_vals) and _sel:
                    df_plot = df_plot[df_plot[_c].isin(_sel)]
                    _active_filters.append(f"{_c}: {', '.join(str(v) for v in _sel)}")

        # 数值列：范围滑块（min ~ max）
        if info["numeric_cols"]:
            st.markdown("**数值列**")
            _num_grid = st.columns(min(len(info["numeric_cols"]), 3))
            for _i, _c in enumerate(info["numeric_cols"]):
                _min_v = float(df[_c].min())
                _max_v = float(df[_c].max())
                if _min_v == _max_v:
                    continue
                _lo, _hi = _num_grid[_i % 3].slider(
                    _c, _min_v, _max_v, (_min_v, _max_v),
                    key=f"fnum_{_c}",
                    format="%.1f",
                )
                if _lo > _min_v or _hi < _max_v:
                    df_plot = df_plot[(df_plot[_c] >= _lo) & (df_plot[_c] <= _hi)]
                    _active_filters.append(f"{_c}: {_lo:.1f}～{_hi:.1f}")

        if _active_filters:
            st.caption(f"已筛选 {len(df_plot)} / {len(df)} 行 | 条件：{' , '.join(_active_filters)}")
        else:
            st.caption(f"未启用筛选，显示全部 {len(df)} 行数据")

    # ── 统一配色主题 ──────────────────────────────────────
    _COLOR_KEYS = ["cmp_color", "sc_color_pick", "ts_color", "hm_color", "hist_color"]
    _DEFAULT_COLOR = "#636EFA"

    st.markdown("**🎨 统一配色**")
    _picker_col, _preset_col = st.columns([1, 4])

    if "_theme_color_val" not in st.session_state:
        st.session_state["_theme_color_val"] = _DEFAULT_COLOR

    _theme_color = _picker_col.color_picker(
        "自定义主题色",
        value=st.session_state["_theme_color_val"],
        help="选色后点击「应用」同步所有图表",
    )
    if _picker_col.button("应用", key="apply_custom_theme"):
        st.session_state["_theme_color_val"] = _theme_color
        for _k in _COLOR_KEYS:
            st.session_state[_k] = _theme_color
        st.rerun()

    _preset_col.caption("快捷主题")
    _btn_cols = _preset_col.columns(len(chart_builder.COLOR_THEMES))
    for _i, (_name, _meta) in enumerate(chart_builder.COLOR_THEMES.items()):
        _c = _meta["single"]
        if _btn_cols[_i].button(_name, key=f"theme_{_name}", help=_c):
            st.session_state["_theme_color_val"] = _c
            for _k in _COLOR_KEYS:
                st.session_state[_k] = _c
            st.rerun()

    figures_for_export = {}  # {标签: fig}

    # ── 指标对比（类别 × 数值聚合柱状图）──────────────────
    if info["cat_cols"] and info["numeric_cols"]:
        st.markdown("#### 指标对比")
        st.caption("选择分类维度和数值指标，查看各组的聚合结果")
        col_a, col_b, col_c = st.columns(3)
        cmp_cat = col_a.selectbox("分类维度", info["cat_cols"], key="cmp_cat")
        cmp_val = col_b.selectbox("数值指标", info["numeric_cols"], key="cmp_val")
        cmp_agg = col_c.selectbox("聚合方式", ["mean", "sum", "median"],
                                   format_func=lambda x: {"mean":"均值","sum":"总和","median":"中位数"}[x],
                                   key="cmp_agg")
        with st.expander("🎨 调整颜色"):
            cmp_color = st.color_picker("主题色", st.session_state.get("cmp_color", _DEFAULT_COLOR), key="cmp_color")
        fig_cmp = chart_builder.aggregated_bar(df_plot, cmp_cat, cmp_val, cmp_agg, color=cmp_color)
        st.plotly_chart(fig_cmp, width="stretch")
        _grouped = df_plot.groupby(cmp_cat)[cmp_val].agg(cmp_agg)
        _agg_lbl = {"mean": "均值", "sum": "总和", "median": "中位数"}[cmp_agg]
        _top, _bot = _grouped.idxmax(), _grouped.idxmin()
        _top_v, _bot_v = _grouped.max(), _grouped.min()
        _ratio = f"，是后者的 {_top_v / _bot_v:.1f} 倍" if _bot_v != 0 else ""
        st.caption(f"**{_top}** 的{cmp_val}{_agg_lbl}最高（{_top_v:,.1f}），**{_bot}** 最低（{_bot_v:,.1f}）{_ratio}。")
        figures_for_export[f"指标对比：{cmp_cat} × {cmp_val}"] = fig_cmp

    # ── 指标关系（散点图）──────────────────────────────────
    if len(info["numeric_cols"]) >= 2:
        st.markdown("#### 指标关系")
        st.caption("查看两个数值指标之间的关联，可按分类着色")
        col_x, col_y, col_c2 = st.columns(3)
        sc_x = col_x.selectbox("X 轴", info["numeric_cols"], key="sc_x")
        sc_y = col_y.selectbox("Y 轴", info["numeric_cols"],
                                index=min(1, len(info["numeric_cols"])-1), key="sc_y")
        color_options = ["（不着色）"] + info["cat_cols"]
        sc_color = col_c2.selectbox("按分类着色", color_options, key="sc_color")
        color_col = None if sc_color == "（不着色）" else sc_color
        with st.expander("🎨 调整颜色"):
            sc_color_pick = st.color_picker("主题色", st.session_state.get("sc_color_pick", _DEFAULT_COLOR), key="sc_color_pick",
                                            help="单色时直接使用；按分类着色时以此色为起点生成多色板")
            sc_opacity = st.slider("透明度", 0.1, 1.0, 0.7, 0.05, key="sc_opacity")
        fig_sc = chart_builder.scatter_plot(df_plot, sc_x, sc_y, color_col,
                                            color=sc_color_pick, opacity=sc_opacity)
        st.plotly_chart(fig_sc, width="stretch")
        _corr = df_plot[[sc_x, sc_y]].dropna().corr().iloc[0, 1]
        if _corr >= 0.7:
            _corr_desc = f"两者强正相关（r={_corr:.2f}），**{sc_x}** 越高，**{sc_y}** 也越高。"
        elif _corr >= 0.3:
            _corr_desc = f"两者弱正相关（r={_corr:.2f}），**{sc_x}** 升高时 **{sc_y}** 有一定上升趋势，但不绝对。"
        elif _corr <= -0.7:
            _corr_desc = f"两者强负相关（r={_corr:.2f}），**{sc_x}** 越高，**{sc_y}** 反而越低。"
        elif _corr <= -0.3:
            _corr_desc = f"两者弱负相关（r={_corr:.2f}），**{sc_x}** 升高时 **{sc_y}** 略有下降趋势。"
        else:
            _corr_desc = f"两者基本无线性关系（r={_corr:.2f}），**{sc_x}** 与 **{sc_y}** 相互独立。"
        st.caption(_corr_desc)
        figures_for_export[f"指标关系：{sc_x} vs {sc_y}"] = fig_sc

    # ── 时序趋势 ────────────────────────────────────────────
    if info["datetime_cols"] and info["numeric_cols"]:
        st.markdown("#### 时序趋势")
        col_d, col_v, col_f, col_a2 = st.columns(4)
        date_col = col_d.selectbox("日期列", info["datetime_cols"], key="ts_date")
        val_col  = col_v.selectbox("数值列", info["numeric_cols"], key="ts_val")
        ts_freq  = col_f.selectbox("时间粒度", ["D", "W", "ME"],
                                    format_func=lambda x: {"D":"日","W":"周","ME":"月"}[x],
                                    key="ts_freq")
        ts_agg   = col_a2.selectbox("聚合方式", ["mean", "sum", "median"],
                                    format_func=lambda x: {"mean":"均值","sum":"总和","median":"中位数"}[x],
                                    key="ts_agg")
        with st.expander("🎨 调整颜色"):
            ts_color = st.color_picker("线条颜色", st.session_state.get("ts_color", _DEFAULT_COLOR), key="ts_color")
        fig = chart_builder.time_series(df_plot, date_col, val_col,
                                        color=ts_color, freq=ts_freq, agg=ts_agg)
        st.plotly_chart(fig, width="stretch")
        _ts_data = df_plot[[date_col, val_col]].dropna().copy()
        _ts_data[date_col] = pd.to_datetime(_ts_data[date_col])
        _ts_agg = _ts_data.set_index(date_col).resample(ts_freq)[val_col].agg(ts_agg)
        if len(_ts_agg) >= 2:
            _first, _last = _ts_agg.iloc[0], _ts_agg.iloc[-1]
            _pct = (_last - _first) / _first * 100 if _first != 0 else 0
            _peak_t = _ts_agg.idxmax().strftime("%Y-%m-%d")
            _peak_v = _ts_agg.max()
            _trend = "上升" if _pct > 5 else ("下降" if _pct < -5 else "基本持平")
            _agg_lbl = {"mean": "均值", "sum": "总和", "median": "中位数"}[ts_agg]
            st.caption(f"整体趋势{_trend}（{_pct:+.1f}%），**{val_col}**{_agg_lbl}在 **{_peak_t}** 前后达到峰值（{_peak_v:,.1f}）。")
        figures_for_export[f"时序趋势：{val_col}"] = fig

    # ── 相关性热力图 ─────────────────────────────────────────
    if len(info["numeric_cols"]) >= 2:
        st.markdown("#### 相关性热力图")
        with st.expander("🎨 调整颜色"):
            hm_color = st.color_picker("主题色", st.session_state.get("hm_color", _DEFAULT_COLOR), key="hm_color",
                                       help="浅灰（负相关）→ 白（零）→ 主题色（正相关）")
        corr = stat_analyzer.correlation_matrix(df_plot, info["numeric_cols"])
        fig_corr = chart_builder.correlation_heatmap(corr, color=hm_color)
        st.plotly_chart(fig_corr, width="stretch")
        _corr_mat = corr.copy()
        _pairs = []
        for i in range(len(_corr_mat.columns)):
            for j in range(i + 1, len(_corr_mat.columns)):
                _pairs.append((_corr_mat.columns[i], _corr_mat.columns[j],
                                _corr_mat.iloc[i, j]))
        if _pairs:
            _pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            _c1, _c2, _cv = _pairs[0]
            _dir = "正相关" if _cv > 0 else "负相关"
            st.caption(f"相关性最强的一对是 **{_c1}** 与 **{_c2}**（r={_cv:.2f}，{_dir}）；其余指标对之间关联相对较弱。")
        figures_for_export["相关性热力图"] = fig_corr

    # ── 数值分布（折叠）────────────────────────────────────
    if info["numeric_cols"]:
        with st.expander("数值列分布 & 箱线图"):
            ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
            hist_col   = ctrl1.selectbox("选择数值列", info["numeric_cols"], key="hist_col")
            box_group  = ctrl2.selectbox(
                "箱线图分组（可选）",
                ["不分组"] + info["cat_cols"],
                key="box_group",
            )
            hist_color = ctrl3.color_picker("颜色", st.session_state.get("hist_color", _DEFAULT_COLOR), key="hist_color")

            left_col, right_col = st.columns(2)
            fig_hist = chart_builder.histogram(df_plot, hist_col, color=hist_color)
            left_col.plotly_chart(fig_hist, width="stretch")
            _hdata = df_plot[hist_col].dropna()
            _skew = float(_hdata.skew())
            _mean, _med = float(_hdata.mean()), float(_hdata.median())
            if _skew > 0.5:
                _skew_desc = f"分布右偏（偏度={_skew:.2f}），大部分数据集中在低值区，少量高值拉高了均值（{_mean:,.1f} > 中位数 {_med:,.1f}）。"
            elif _skew < -0.5:
                _skew_desc = f"分布左偏（偏度={_skew:.2f}），大部分数据集中在高值区，少量低值拉低了均值（{_mean:,.1f} < 中位数 {_med:,.1f}）。"
            else:
                _skew_desc = f"分布近似对称（偏度={_skew:.2f}），均值（{_mean:,.1f}）与中位数（{_med:,.1f}）接近，数据较均匀。"
            left_col.caption(_skew_desc)
            figures_for_export[f"分布直方图：{hist_col}"] = fig_hist

            group = None if box_group == "不分组" else box_group
            fig_box = chart_builder.box_plot(df_plot, hist_col, group_col=group, color=hist_color)
            right_col.plotly_chart(fig_box, width="stretch")
            _q1, _q3 = float(_hdata.quantile(0.25)), float(_hdata.quantile(0.75))
            _outliers = int(((df_plot[hist_col] < _q1 - 1.5 * (_q3 - _q1)) | (df_plot[hist_col] > _q3 + 1.5 * (_q3 - _q1))).sum())
            _box_group_desc = f"按 **{group}** 分组后可对比各组差异；" if group else ""
            _outlier_desc = f"存在 **{_outliers}** 个异常值，需关注。" if _outliers > 0 else "无明显异常值。"
            right_col.caption(f"{_box_group_desc}**{hist_col}** 的中间50%数据集中在 {_q1:,.1f}～{_q3:,.1f} 之间，{_outlier_desc}")
            figures_for_export[f"箱线图：{hist_col}"] = fig_box

    # ── 类别占比（折叠）────────────────────────────────────
    if info["cat_cols"]:
        with st.expander("类别列占比饼图"):
            pie_c1, pie_c2 = st.columns([2, 3])
            pie_cat = pie_c1.selectbox("选择类别列", info["cat_cols"], key="pie_cat")
            _pie_palette_names = list(chart_builder.PIE_PALETTES.keys())
            pie_palette_name = pie_c2.selectbox("配色方案", _pie_palette_names, key="pie_palette_name")
            _preview_colors = chart_builder.PIE_PALETTES.get(pie_palette_name, [])
            _swatches = "".join(
                f"<span style='display:inline-block;width:22px;height:14px;"
                f"background:{c};border-radius:3px;margin-right:3px'></span>"
                for c in _preview_colors
            )
            pie_c2.markdown(_swatches, unsafe_allow_html=True)

            # 每个类别单独选色
            _pie_cats = df_plot[pie_cat].value_counts().head(8).index.tolist()
            _base_colors = chart_builder.PIE_PALETTES.get(pie_palette_name, [])
            _custom_colors = {}
            with st.expander("🎨 自定义每个类别的颜色"):
                _cc_cols = st.columns(min(len(_pie_cats), 4))
                for _ci, _cat_name in enumerate(_pie_cats):
                    _default = _base_colors[_ci % len(_base_colors)]
                    _picked = _cc_cols[_ci % 4].color_picker(
                        str(_cat_name),
                        value=st.session_state.get(f"pie_cc_{pie_cat}_{_cat_name}", _default),
                        key=f"pie_cc_{pie_cat}_{_cat_name}",
                    )
                    _custom_colors[str(_cat_name)] = _picked

            fig_pie = chart_builder.pie_chart(df_plot, pie_cat, custom_colors=_custom_colors)
            st.plotly_chart(fig_pie, width="stretch")
            _pie_counts = df_plot[pie_cat].value_counts()
            _pie_top = _pie_counts.index[0]
            _pie_top_pct = _pie_counts.iloc[0] / _pie_counts.sum() * 100
            _pie_n = len(_pie_counts)
            st.caption(f"**{_pie_top}** 占比最高（{_pie_top_pct:.1f}%），共 {_pie_n} 个类别；{'分布较集中，头部主导明显。' if _pie_top_pct > 40 else '各类别分布相对均匀。'}")
            figures_for_export[f"占比饼图：{pie_cat}"] = fig_pie

    st.session_state["figures"] = figures_for_export

# ══ Tab3：AI 解读 ═══════════════════════════════════════════
with tab3:
    st.subheader("AI 解读")

    stat_summary = stat_analyzer.build_stat_summary(df, info)
    st.session_state["stat_summary"] = stat_summary

    # 生成初始解读（缓存，避免重复调用）
    cache_key = f"report_{uploaded.name}_{info['rows']}"
    if st.button("🔄 重新生成解读", help="清除缓存，重新调用 AI 分析"):
        st.session_state.pop("report_cache_key", None)

    if st.session_state.get("report_cache_key") != cache_key:
        with st.spinner("AI 正在分析数据，请稍候..."):
            try:
                report = ai_interpreter.interpret(stat_summary, user_context)
                st.session_state["ai_report"] = report
                st.session_state["report_cache_key"] = cache_key
                st.session_state["chat_history"] = [
                    {"role": "assistant", "content": report}
                ]
                # 将报告按 ## 标题解析为各板块，供 Tab4 细粒度选择
                sections = {}
                current_title, current_lines = None, []
                for line in report.split("\n"):
                    if line.startswith("## "):
                        if current_title:
                            sections[current_title] = "\n".join(current_lines).strip()
                        current_title = line[3:].strip()
                        current_lines = [line]
                    else:
                        current_lines.append(line)
                if current_title:
                    sections[current_title] = "\n".join(current_lines).strip()
                # 没有 ## 标题时整篇作为一节
                if not sections:
                    sections["AI 解读"] = report
                st.session_state["ai_sections"] = sections
            except Exception as e:
                st.error(f"AI 分析失败：{e}")
                st.stop()

    # AI 报告：按板块折叠展示 + 复制按钮
    ai_sections = st.session_state.get("ai_sections", {})
    if ai_sections:
        for sec_title, sec_content in ai_sections.items():
            with st.expander(f"**{sec_title}**", expanded=True):
                st.markdown(sec_content)
                st.code(_clean_md(sec_content), language=None)
                st.caption("^ 点击右上角复制图标可复制纯文本")
    else:
        st.markdown(st.session_state.get("ai_report", ""))

    st.divider()

    # 多轮追问
    chat_col, clear_col = st.columns([8, 1])
    chat_col.markdown("#### 💬 追问")
    if clear_col.button("清空", key="clear_chat", help="清除追问记录"):
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": st.session_state.get("ai_report", "")}
        ]
        st.rerun()

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"][1:]:
        role_label = "你" if msg["role"] == "user" else "AI"
        with st.chat_message(msg["role"]):
            st.markdown(f"**{role_label}：** {msg['content']}")

    question = st.chat_input("针对这份数据继续提问...")
    if question:
        st.session_state["chat_history"].append({"role": "user", "content": question})
        with st.spinner("思考中..."):
            try:
                answer = ai_interpreter.follow_up(
                    st.session_state["stat_summary"],
                    st.session_state["chat_history"][:-1],
                    question,
                )
                st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"追问失败：{e}")

# ══ Tab4：导出报告 ══════════════════════════════════════════
with tab4:
    st.subheader("导出 PDF 报告")

    if "ai_report" not in st.session_state:
        st.info("请先在「AI 解读」标签页生成分析报告，再来导出。")
    else:
        # 兼容旧缓存：若 ai_sections 尚未解析则补做
        if "ai_sections" not in st.session_state:
            _sections, _cur_title, _cur_lines = {}, None, []
            for _line in st.session_state["ai_report"].split("\n"):
                if _line.startswith("## "):
                    if _cur_title:
                        _sections[_cur_title] = "\n".join(_cur_lines).strip()
                    _cur_title, _cur_lines = _line[3:].strip(), [_line]
                else:
                    _cur_lines.append(_line)
            if _cur_title:
                _sections[_cur_title] = "\n".join(_cur_lines).strip()
            st.session_state["ai_sections"] = _sections or {"AI 解读": st.session_state["ai_report"]}

        st.markdown("#### 选择导出内容")

        # ── 统计摘要 ──────────────────────────────────────
        inc_stat = st.checkbox("统计摘要", value=True)

        # ── AI 解读各板块 ──────────────────────────────────
        ai_sections = st.session_state.get("ai_sections", {})
        st.markdown("**AI 解读**")
        selected_sections = {}
        for title, content in ai_sections.items():
            if st.checkbox(title, value=True, key=f"sec__{title}"):
                selected_sections[title] = content

        # ── 追问记录 ──────────────────────────────────────
        inc_chat = st.checkbox("追问对话记录", value=False)

        # ── 图表逐条选择 ──────────────────────────────────
        try:
            import kaleido  # noqa: F401
            kaleido_ok = True
        except ImportError:
            kaleido_ok = False

        available_figs = st.session_state.get("figures", {})
        selected_fig_keys = []

        if kaleido_ok and available_figs:
            st.markdown("**数据图表**（速度稍慢，按需勾选）")
            for label in available_figs:
                if st.checkbox(label, value=False, key=f"fig__{label}"):
                    selected_fig_keys.append(label)
        elif not kaleido_ok:
            st.caption("⚠️ 图表导出不可用（kaleido 未安装或 Chrome 不兼容）")
        else:
            st.caption("请先在「可视化分析」标签页浏览图表，再来导出。")

        # ── 导出格式 + 生成按钮 ────────────────────────────
        st.markdown("**导出格式**")
        export_fmt = st.radio("", ["PDF", "Word (.docx)"], horizontal=True, label_visibility="collapsed")

        any_selected = any([inc_stat, bool(selected_sections), inc_chat, bool(selected_fig_keys)])
        if not any_selected:
            st.warning("请至少勾选一项导出内容。")
        elif st.button("生成报告", type="primary"):
            ai_report_export = (
                "\n\n".join(content for content in selected_sections.values())
                if selected_sections else None
            )
            chat_history = (
                [m for m in st.session_state.get("chat_history", [])[1:]]
                if inc_chat else []
            )
            figs = [available_figs[k] for k in selected_fig_keys]
            export_kwargs = dict(
                filename_hint=uploaded.name,
                ai_report=ai_report_export,
                stat_summary=st.session_state["stat_summary"] if inc_stat else None,
                figures=figs,
                chat_history=chat_history,
            )

            if export_fmt == "PDF":
                with st.spinner("正在生成 PDF..."):
                    try:
                        file_bytes = report_exporter.export_pdf(**export_kwargs)
                        st.download_button(
                            label="📥 下载 PDF",
                            data=file_bytes,
                            file_name=f"{uploaded.name}_report.pdf",
                            mime="application/pdf",
                        )
                        st.success("PDF 已生成，点击上方按钮下载。")
                    except Exception as e:
                        st.error(f"PDF 生成失败：{e}")
            else:
                with st.spinner("正在生成 Word 文档..."):
                    try:
                        file_bytes = report_exporter.export_word(**export_kwargs)
                        st.download_button(
                            label="📥 下载 Word",
                            data=file_bytes,
                            file_name=f"{uploaded.name}_report.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                        st.success("Word 文档已生成，点击上方按钮下载。")
                    except Exception as e:
                        st.error(f"Word 生成失败：{e}")

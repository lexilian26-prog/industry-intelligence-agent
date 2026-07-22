# 数据分析 Agent

上传 CSV / Excel，AI 自动解读数据洞察，可视化分析，一键导出 PDF / Word 报告。

## 界面截图

**数据预览**
![数据预览](./screenshots/数据预览界面.jpg)

**可视化分析**
![可视化分析](./screenshots/可视化分析界面.jpg)

**AI 解读**
![AI解读](./screenshots/AI解读界面.jpg)

**导出报告**
![导出界面](./screenshots/导出界面.jpg)

📄 [查看导出报告示例（PDF）](./screenshots/test_ecommerce.csv_report.pdf)

## 功能介绍

- **Tab1 数据预览**：AI 自动概括数据内容，展示基础统计（数值列 / 类别列 / 日期列分开呈现），缺失值报告
- **Tab2 可视化分析**：数据筛选面板联动所有图表；支持指标对比柱状图、散点图、时序趋势折线图、相关性热力图、分布直方图、类别占比饼图；统一配色 + 每图单独调色
- **Tab3 AI 解读**：Claude 生成核心发现、异常点（含风险等级）、趋势判断、行动建议；支持多轮追问
- **Tab4 导出报告**：细粒度勾选导出内容（统计摘要 / AI 解读各板块 / 追问记录 / 图表），支持 PDF 和 Word 两种格式

## 技术栈

- Python · Streamlit · Plotly · Claude AI (claude-sonnet-4.6)
- fpdf2（PDF 导出）· python-docx（Word 导出）· pandas · kaleido（图表截图）

## 测试数据

- `test_sales.csv`：新能源汽车销售数据（500 行）
- `test_ecommerce.csv`：电商订单数据（600 行）

## 本地启动

```bash
cd 数据分析Agent
pip install -r requirements.txt
python -m streamlit run app.py --server.port 8502
```

或直接双击 `启动.bat`

> 需在 `.env` 中配置 `ANTHROPIC_API_KEY`

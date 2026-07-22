import pandas as pd
import random
from datetime import date, timedelta

random.seed(42)

brands = ["比亚迪", "特斯拉", "小鹏", "理想", "蔚来", "问界", "零跑", "哪吒"]
regions = ["华东", "华南", "华北", "华中", "西南", "西北"]
models = {
    "比亚迪": ["汉EV", "宋Plus", "海豹"],
    "特斯拉": ["Model 3", "Model Y"],
    "小鹏": ["P7", "G6", "X9"],
    "理想": ["L9", "L8", "L7"],
    "蔚来": ["ES6", "ET5", "EC6"],
    "问界": ["M7", "M9"],
    "零跑": ["C11", "C01"],
    "哪吒": ["哪吒S", "哪吒GT"],
}

rows = []
start = date(2024, 1, 1)
for i in range(500):
    d = start + timedelta(days=random.randint(0, 364))
    brand = random.choice(brands)
    model = random.choice(models[brand])
    region = random.choice(regions)
    price = round(random.uniform(15, 55) + (10 if brand in ["理想","蔚来","问界"] else 0), 1)
    sales = random.randint(50, 800)
    satisfaction = round(random.uniform(3.0, 5.0), 1)
    rows.append({
        "日期": d.isoformat(),
        "品牌": brand,
        "车型": model,
        "地区": region,
        "售价(万元)": price,
        "销量(辆)": sales,
        "销售额(万元)": round(price * sales, 1),
        "客户满意度": satisfaction,
    })

df = pd.DataFrame(rows).sort_values("日期").reset_index(drop=True)
df.to_csv("test_sales.csv", index=False, encoding="utf-8-sig")
print(f"生成完成：{len(df)} 行，已保存为 test_sales.csv")

import pandas as pd
import random
from datetime import date, timedelta

random.seed(7)

categories = ["手机数码", "服装鞋帽", "家居用品", "美妆护肤", "食品饮料", "运动户外", "图书教育", "母婴玩具"]
platforms = ["淘宝", "京东", "拼多多", "抖音小店", "小红书"]
regions = ["华东", "华南", "华北", "华中", "西南", "西北", "东北"]
pay_methods = ["支付宝", "微信支付", "银行卡", "花呗"]

# 各类目价格区间和退款率基准
category_config = {
    "手机数码":  {"price": (200, 8000), "refund_base": 0.05},
    "服装鞋帽":  {"price": (30,   500), "refund_base": 0.18},
    "家居用品":  {"price": (20,  1500), "refund_base": 0.08},
    "美妆护肤":  {"price": (50,   800), "refund_base": 0.12},
    "食品饮料":  {"price": (10,   300), "refund_base": 0.03},
    "运动户外":  {"price": (80,  3000), "refund_base": 0.07},
    "图书教育":  {"price": (15,   200), "refund_base": 0.02},
    "母婴玩具":  {"price": (30,  1000), "refund_base": 0.06},
}

rows = []
start = date(2024, 1, 1)
order_id = 100001

for i in range(600):
    d = start + timedelta(days=random.randint(0, 364))
    category = random.choice(categories)
    cfg = category_config[category]

    price = round(random.uniform(*cfg["price"]), 2)
    qty = random.randint(1, 5)
    amount = round(price * qty, 2)
    discount = round(random.uniform(0, min(amount * 0.3, 50)), 2)
    actual_amount = round(amount - discount, 2)

    # 退款：价格越高退款率略升
    refund_prob = cfg["refund_base"] + (0.05 if price > 1000 else 0)
    is_refund = 1 if random.random() < refund_prob else 0

    # 评分：退款订单评分偏低
    if is_refund:
        rating = round(random.uniform(1.0, 3.0), 1)
    else:
        rating = round(random.uniform(3.5, 5.0), 1)

    rows.append({
        "订单ID": f"ORD{order_id + i}",
        "下单日期": d.isoformat(),
        "商品类目": category,
        "平台": random.choice(platforms),
        "地区": random.choice(regions),
        "支付方式": random.choice(pay_methods),
        "商品单价(元)": price,
        "购买数量": qty,
        "订单金额(元)": amount,
        "优惠金额(元)": discount,
        "实付金额(元)": actual_amount,
        "是否退款": is_refund,
        "用户评分": rating,
    })

df = pd.DataFrame(rows).sort_values("下单日期").reset_index(drop=True)
df.to_csv("test_ecommerce.csv", index=False, encoding="utf-8-sig")
print(f"生成完成：{len(df)} 行，已保存为 test_ecommerce.csv")

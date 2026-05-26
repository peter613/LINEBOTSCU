"""
LINEBOTSCU - Supabase 預填資料腳本
執行方式：python database/seed.py
功能：建立 shops / drinks 資料表並填入台灣主流飲料品牌資料
"""
import os
import sys

# 確保可以 import 同專案模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_client

# ─────────────────────────────────────────
# 商家資料（8 間主流品牌）
# ─────────────────────────────────────────
SHOPS = [
    {"name": "清心福全",   "location": "全台",   "rating": 4.0},
    {"name": "五十嵐",     "location": "全台",   "rating": 4.3},
    {"name": "茶湯會",     "location": "全台",   "rating": 4.2},
    {"name": "大苑子",     "location": "全台",   "rating": 4.4},
    {"name": "一芳水果茶", "location": "全台",   "rating": 4.5},
    {"name": "麻古茶坊",   "location": "全台",   "rating": 4.1},
    {"name": "迷客夏",     "location": "全台",   "rating": 4.6},
    {"name": "鶴茶樓",     "location": "全台",   "rating": 4.7},
]

# ─────────────────────────────────────────
# 飲品資料（每間 5 款，共 40 筆）
# ─────────────────────────────────────────
# 格式：(商家名稱, 飲品名稱, 類別, 甜度, tags, is_popular, is_new)
DRINKS_RAW = [
    # 清心福全
    ("清心福全", "珍珠奶茶",     "奶茶",   "全糖", ["奶茶", "珍珠", "經典"],       True,  False),
    ("清心福全", "四季春茶",     "茶類",   "無糖", ["茶類", "清爽", "低卡"],        True,  False),
    ("清心福全", "波霸奶綠",     "奶茶",   "半糖", ["奶茶", "波霸"],               False, False),
    ("清心福全", "梅子綠茶",     "果茶",   "微糖", ["果茶", "梅子", "酸甜"],        True,  False),
    ("清心福全", "玫瑰鮮奶茶",   "鮮奶茶", "半糖", ["鮮奶茶", "玫瑰", "季節限定"],  False, True),

    # 五十嵐
    ("五十嵐",   "四季春奶茶",   "奶茶",   "半糖", ["奶茶", "經典", "推薦"],        True,  False),
    ("五十嵐",   "阿薩姆奶茶",   "奶茶",   "全糖", ["奶茶", "紅茶底"],              True,  False),
    ("五十嵐",   "葡萄柚綠茶",   "果茶",   "微糖", ["果茶", "低卡", "清爽"],        True,  False),
    ("五十嵐",   "燕麥奶茶",     "奶茶",   "微糖", ["奶茶", "燕麥", "健康"],        False, True),
    ("五十嵐",   "梅花乳酸",     "特調",   "微糖", ["特調", "乳酸", "酸甜"],        True,  False),

    # 茶湯會
    ("茶湯會",   "珍珠鮮奶",     "鮮奶茶", "半糖", ["鮮奶茶", "珍珠", "推薦"],      True,  False),
    ("茶湯會",   "翡翠檸檬",     "果茶",   "微糖", ["果茶", "檸檬", "清爽", "低卡"],True,  False),
    ("茶湯會",   "鐵觀音奶茶",   "奶茶",   "半糖", ["奶茶", "鐵觀音", "茶香"],      True,  False),
    ("茶湯會",   "黑糖鮮奶",     "鮮奶茶", "全糖", ["鮮奶茶", "黑糖", "熱門"],      True,  False),
    ("茶湯會",   "芒果椰果凍飲", "果茶",   "微糖", ["果茶", "芒果", "季節限定"],    False, True),

    # 大苑子
    ("大苑子",   "鮮果多多",     "果茶",   "微糖", ["果茶", "新鮮", "維他命"],      True,  False),
    ("大苑子",   "芭樂鮮果茶",   "果茶",   "微糖", ["果茶", "芭樂", "低卡"],        True,  False),
    ("大苑子",   "百香綠茶",     "果茶",   "無糖", ["果茶", "百香果", "低卡", "清爽"],True, False),
    ("大苑子",   "玉荷包烏龍",   "茶類",   "無糖", ["茶類", "季節限定", "清香"],    False, True),
    ("大苑子",   "草莓鮮奶昔",   "特調",   "半糖", ["特調", "草莓", "季節限定"],    False, True),

    # 一芳水果茶
    ("一芳水果茶", "一芳水果茶", "果茶",   "微糖", ["果茶", "招牌", "推薦"],        True,  False),
    ("一芳水果茶", "波霸仙草奶", "奶茶",   "半糖", ["奶茶", "仙草", "波霸"],        True,  False),
    ("一芳水果茶", "梨山烏龍",   "茶類",   "無糖", ["茶類", "高山茶", "清香"],      True,  False),
    ("一芳水果茶", "芒果水果茶", "果茶",   "微糖", ["果茶", "芒果", "季節限定"],    False, True),
    ("一芳水果茶", "玄米鮮奶",   "鮮奶茶", "微糖", ["鮮奶茶", "玄米", "健康"],      False, False),

    # 麻古茶坊
    ("麻古茶坊", "杏仁鮮奶茶",   "鮮奶茶", "半糖", ["鮮奶茶", "杏仁", "招牌"],      True,  False),
    ("麻古茶坊", "芝麻鮮奶",     "鮮奶茶", "半糖", ["鮮奶茶", "芝麻", "濃郁"],      True,  False),
    ("麻古茶坊", "桂圓紅棗茶",   "茶類",   "微糖", ["茶類", "養生", "溫暖"],        True,  False),
    ("麻古茶坊", "抹茶鮮奶",     "鮮奶茶", "微糖", ["鮮奶茶", "抹茶", "日式"],      False, True),
    ("麻古茶坊", "珍珠杏仁奶",   "奶茶",   "半糖", ["奶茶", "珍珠", "杏仁"],        False, False),

    # 迷客夏
    ("迷客夏",   "迷克冰淇淋紅茶", "特調", "全糖", ["特調", "冰淇淋", "招牌"],      True,  False),
    ("迷客夏",   "黑糖珍珠鮮奶", "鮮奶茶", "少糖", ["鮮奶茶", "黑糖", "珍珠", "推薦"],True, False),
    ("迷客夏",   "抹茶鮮奶拿鐵", "鮮奶茶", "半糖", ["鮮奶茶", "抹茶", "拿鐵"],      True,  False),
    ("迷客夏",   "蜂蜜玫瑰鮮奶", "鮮奶茶", "微糖", ["鮮奶茶", "玫瑰", "蜂蜜", "季節限定"],False, True),
    ("迷客夏",   "烏龍鮮奶茶",   "鮮奶茶", "無糖", ["鮮奶茶", "烏龍", "低卡"],      True,  False),

    # 鶴茶樓
    ("鶴茶樓",   "鶴の桂花烏龍", "茶類",   "微糖", ["茶類", "桂花", "精品", "推薦"],True,  False),
    ("鶴茶樓",   "荔枝玫瑰凍飲", "果茶",   "微糖", ["果茶", "荔枝", "玫瑰", "高質感"],True, False),
    ("鶴茶樓",   "頂級珍珠鮮奶", "鮮奶茶", "半糖", ["鮮奶茶", "珍珠", "精品"],      True,  False),
    ("鶴茶樓",   "玫瑰冷萃紅茶", "茶類",   "無糖", ["茶類", "冷萃", "低卡", "季節限定"],False, True),
    ("鶴茶樓",   "焦糖布丁奶茶", "奶茶",   "半糖", ["奶茶", "焦糖", "布丁", "季節限定"],False, True),
]


def seed():
    """填入預設資料至 Supabase。"""
    sb = get_client()

    print("🗑️  清除舊資料...")
    sb.table("drinks").delete().neq("id", 0).execute()
    sb.table("shops").delete().neq("id", 0).execute()

    print("🏪 填入商家資料...")
    for shop in SHOPS:
        res = sb.table("shops").insert(shop).execute()
        print(f"   ✅ {shop['name']}")

    print("🧋 取得商家 ID 對應...")
    shops_res = sb.table("shops").select("id, name").execute()
    shop_id_map = {row["name"]: row["id"] for row in shops_res.data}

    print("🍵 填入飲品資料...")
    drinks_to_insert = []
    for shop_name, drink_name, category, sweetness, tags, is_popular, is_new in DRINKS_RAW:
        shop_id = shop_id_map.get(shop_name)
        if shop_id is None:
            print(f"   ⚠️  找不到商家：{shop_name}，跳過 {drink_name}")
            continue
        drinks_to_insert.append({
            "shop_id":    shop_id,
            "name":       drink_name,
            "category":   category,
            "sweetness":  sweetness,
            "tags":       tags,
            "is_popular": is_popular,
            "is_new":     is_new,
        })

    # 批次插入
    sb.table("drinks").insert(drinks_to_insert).execute()
    print(f"   ✅ 共插入 {len(drinks_to_insert)} 筆飲品")

    print("\n🎉 資料填入完成！")
    print(f"   商家：{len(SHOPS)} 間")
    print(f"   飲品：{len(drinks_to_insert)} 筆")


if __name__ == "__main__":
    seed()

"""
LINEBOTSCU - 共用狀態常數
所有 handler 共用的狀態機常數
"""

# 通用狀態
STATE_IDLE         = "IDLE"
STATE_ASK_LOCATION = "ASK_LOCATION"       # 等待使用者傳位置（所有功能共用）

# 條件找茶專用
STATE_COND_ASK_CATEGORY  = "CONDITION_ASK_CATEGORY"


# 隨機推專用
STATE_RANDOM_ASK_MODE     = "RANDOM_ASK_MODE"      # 等待選擇模式（熱門/類別）
STATE_RANDOM_ASK_CATEGORY = "RANDOM_ASK_CATEGORY"  # 等待選擇類別

# 各功能功能名稱（存入 context.feature）
FEATURE_CONDITION = "condition_tea"
FEATURE_RANDOM    = "random_seal"
FEATURE_NEW       = "new_products"

# 飲品類別選項
CATEGORIES  = ["果茶", "奶茶", "鮮奶茶", "茶類", "特調", "不限"]


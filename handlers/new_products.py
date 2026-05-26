"""
LINEBOTSCU - 功能 3：最新主打（新版）
流程：
  1. 觸發 → 請傳位置
  2. 收到位置 → AI 搜尋附近店家當季新品
  3. 顯示 Flex Carousel（含「✅ 選這個」按鈕）
  4. 使用者點選 → 存入 DB
支援：直接觸發 / 輸入「{品牌名}最新」精準查詢
"""
import logging

from linebot.v3.messaging import (
    ApiClient,
    FlexMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from config import line_configuration
from handlers.states import STATE_ASK_LOCATION, FEATURE_NEW
from handlers.utils import (
    ask_for_location, query_new_products_from_ai,
    make_drink_carousel, reply_text,
)
from database.db import set_user_session

logger = logging.getLogger(__name__)

KNOWN_BRANDS = [
    "清心福全", "五十嵐", "茶湯會", "大苑子",
    "一芳水果茶", "一芳", "麻古茶坊", "迷客夏", "鶴茶樓",
]


def trigger(event, user_id: str, user_input: str = "") -> None:
    """
    觸發最新主打。
    先請求位置，並把原始輸入（用於品牌萃取）存入 context。
    """
    brand = _extract_brand(user_input)
    ctx = {
        "feature":      FEATURE_NEW,
        "target_brand": brand,  # None 表示一般查詢
    }
    set_user_session(user_id, STATE_ASK_LOCATION, ctx)
    ask_for_location(event, feature_label="新品資訊")


def on_location_received(event, user_id: str, lat: float, lng: float, address: str, ctx: dict) -> None:
    """
    收到位置後，執行 AI 新品搜尋並顯示結果。
    """
    from handlers.condition_tea import _extract_area
    area         = _extract_area(address)
    target_brand = ctx.get("target_brand")

    if target_brand:
        drinks = _query_brand_new(area, target_brand)
        header = f"🏪 {target_brand} × {area} 最新主打"
    else:
        drinks = query_new_products_from_ai(area, count=4)
        header = f"🌟 {area} 附近當季新品"

    if not drinks:
        reply_text(event, f"😿 目前找不到「{area}」附近的新品資訊，請稍後再試！")
        from database.db import reset_user_session
        reset_user_session(user_id)
        return

    # 暫存選項至 session
    ctx.update({
        "pending_drinks": drinks,
        "area":           area,
        "lat":            lat,
        "lng":            lng,
        "address":        address,
    })
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(drinks, area)
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"{header}，共 {len(drinks)} 款，點選喜歡的記錄下來！"),
                    FlexMessage(alt_text="最新主打飲品", contents=carousel),
                ],
            )
        )


# ─────────────────────────────────────────
# 私有輔助
# ─────────────────────────────────────────

def _extract_brand(text: str) -> str | None:
    for brand in KNOWN_BRANDS:
        if brand in text:
            return brand
    return None


def _query_brand_new(area: str, brand: str) -> list[dict]:
    """精準查詢特定品牌的最新商品。"""
    from gemini_client import tea_query
    import json, re

    prompt = (
        f"請用 Google Search 搜尋「{brand}」在「{area}」最新推出的飲品或季節限定商品。\n"
        f"列出 3 款，嚴格只回覆 JSON 格式，不要其他文字：\n"
        f'[{{"shop": "{brand}", "drink": "飲品名稱", "category": "類別", '
        f'"sweetness": "甜度（不確定填不限）", "tags": ["新品"], "description": "一句話特色描述"}}]'
    )
    raw = tea_query(prompt)

    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return []

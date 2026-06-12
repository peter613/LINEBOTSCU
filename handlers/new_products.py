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
    FlexContainer,
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
    不再請求位置，直接搜尋全台各大連鎖品牌最新主打。
    """
    brand = _extract_brand(user_input)
    area = "台灣"
    
    # 先回覆等待訊息
    from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, PushMessageRequest, FlexMessage, FlexContainer
    from config import line_configuration
    from handlers.utils import query_new_products_from_ai, make_drink_carousel
    from database.db import set_user_session

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🦭 豹豹正在為您搜尋全台連鎖品牌的當季新品...請稍候，不要重複點擊喔！")],
            )
        )

    # 執行搜尋
    if brand:
        drinks = _query_brand_new(area, brand, "")
        header = f"🏪 {brand} 最新主打"
    else:
        drinks = query_new_products_from_ai(area, address="", count=4)
        header = f"🌟 知名品牌當季新品"

    if not drinks:
        # AI 找不到 → 嘗試 DB 全站熱門飲品作為備援
        from database.db import get_popular_drinks, reset_user_session
        db_drinks = get_popular_drinks(limit=5)
        if db_drinks:
            for d in db_drinks:
                d["description"] = f"🔥 已被選擇 {d.get('select_count', 1)} 次"
            ctx = {"pending_drinks": db_drinks, "area": area}
            set_user_session(user_id, "SHOW_OPTIONS", ctx)
            carousel = make_drink_carousel(db_drinks, area, user_id, is_fallback=True)
            with ApiClient(line_configuration) as api_client:
                MessagingApi(api_client).push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[
                            TextMessage(text="📍 暫時搜不到新品，但這些是大家都在推的人氣飲品喔！"),
                            FlexMessage(alt_text="人氣飲品推薦", contents=FlexContainer.from_dict(carousel)),
                        ],
                    )
                )
        else:
            reset_user_session(user_id)
            with ApiClient(line_configuration) as api_client:
                MessagingApi(api_client).push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text="抱歉，目前還沒有足夠的飲品資料，試試用「條件找茶」來累積吧！")],
                    )
                )
        return

    # 暫存選項至 session
    ctx = {
        "pending_drinks": drinks,
        "area":           area,
    }
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(drinks, area, user_id)
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
                messages=[
                    TextMessage(text=f"{header}，共 {len(drinks)} 款，點選喜歡的記錄下來！"),
                    FlexMessage(alt_text="最新主打飲品", contents=FlexContainer.from_dict(carousel)),
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


def _query_brand_new(area: str, brand: str, address: str) -> list[dict]:
    """精準查詢特定品牌的最新商品。"""
    from gemini_client import tea_query
    import json, re

    location_str = address if address else area
    prompt = (
        f"搜尋「{location_str}」走路10分鐘內可到的「{brand}」最新3款飲品。\n"
        f"必須是確實存在且非常近的店家。繁體中文，僅回JSON："
        f'[{{"shop":"{brand}","drink":"品名","category":"類別",'
        f'"tags":["新品"],"description":"特色"}}]'
        f"\n重要：若附近10分鐘步行範圍內確實沒有該品牌店家，請直接回覆空 JSON 陣列 []，絕對不要編造。"
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

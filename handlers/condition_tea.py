"""
LINEBOTSCU - 功能 1：條件找茶（新版）
流程：
  1. 觸發 → 請傳位置（LocationAction Quick Reply）
  2. 收到位置 → 詢問類別（Quick Reply）
  3. 詢問甜度（Quick Reply）
  4. AI 搜尋附近符合飲品 → Flex Carousel
  5. 使用者點「✅ 選這個」→ 存入 DB
"""
import logging

from linebot.v3.messaging import (
    ApiClient,
    FlexContainer,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
)

from config import line_configuration
from handlers.states import (
    STATE_ASK_LOCATION, STATE_COND_ASK_CATEGORY,
    STATE_COND_ASK_SWEETNESS, FEATURE_CONDITION,
    CATEGORIES, SWEETNESSES,
)
from handlers.utils import ask_for_location, query_drinks_from_ai, make_drink_carousel
from database.db import set_user_session

logger = logging.getLogger(__name__)


def trigger(event, user_id: str) -> None:
    """使用者觸發「條件找茶」，先請求位置。"""
    set_user_session(user_id, STATE_ASK_LOCATION, {"feature": FEATURE_CONDITION})
    ask_for_location(event, feature_label="飲品推薦")


def on_location_received(event, user_id: str, lat: float, lng: float, address: str) -> None:
    """收到位置後，進入詢問類別步驟。"""
    ctx = {
        "feature":  FEATURE_CONDITION,
        "lat":      lat,
        "lng":      lng,
        "address":  address,
        "area":     _extract_area(address),
    }
    set_user_session(user_id, STATE_COND_ASK_CATEGORY, ctx)
    _ask_category(event)


def on_category_selected(event, user_id: str, ctx: dict, user_input: str) -> None:
    """使用者選擇類別後，詢問甜度。"""
    category = user_input if user_input in CATEGORIES else "不限"
    ctx["category"] = category
    set_user_session(user_id, STATE_COND_ASK_SWEETNESS, ctx)
    _ask_sweetness(event)


def on_sweetness_selected(event, user_id: str, ctx: dict, user_input: str) -> None:
    """使用者選擇甜度後，呼叫 AI 並顯示結果。"""
    sweetness = user_input if user_input in SWEETNESSES else "不限"
    ctx["sweetness"] = sweetness

    area     = ctx.get("area", ctx.get("address", "台灣"))
    category = ctx.get("category", "不限")

    # 呼叫 AI 取得飲品選項
    drinks = query_drinks_from_ai(area, category, sweetness, count=3)

    if not drinks:
        from database.db import reset_user_session
        reset_user_session(user_id)
        with ApiClient(line_configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="😿 AI 暫時找不到符合條件的飲品，請稍後再試或換個條件！")],
                )
            )
        return

    # 把 AI 推薦選項暫存至 session（供 postback 使用）
    ctx["pending_drinks"] = drinks
    ctx["area"] = area
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(drinks, area)
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"🍵 為您在「{area}」找到 {len(drinks)} 款推薦飲品，請點選您喜歡的："),
                    FlexMessage(alt_text="飲品推薦選項", contents=FlexContainer.from_dict(carousel)),
                ],
            )
        )


# ─────────────────────────────────────────
# 私有輔助
# ─────────────────────────────────────────

def _ask_category(event) -> None:
    items = [QuickReplyItem(action=MessageAction(label=c, text=c)) for c in CATEGORIES]
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="🍵 您想喝哪種類型的飲料？",
                    quick_reply=QuickReply(items=items),
                )],
            )
        )


def _ask_sweetness(event) -> None:
    items = [QuickReplyItem(action=MessageAction(label=s, text=s)) for s in SWEETNESSES]
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="🍬 您偏好哪種甜度？",
                    quick_reply=QuickReply(items=items),
                )],
            )
        )


def _extract_area(address: str) -> str:
    """從完整地址萃取縣市＋區域（前兩段）。"""
    if not address:
        return "台灣"
    parts = address.replace("台灣", "").strip()
    # 嘗試取縣市+區（如：台北市中山區）
    import re
    match = re.match(r"(.{2,4}[市縣]).{0,1}(.{2,4}[區鄉鎮市])?", parts)
    if match:
        return "".join(filter(None, match.groups()))
    return parts[:6] if len(parts) > 6 else parts

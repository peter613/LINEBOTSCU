"""
LINEBOTSCU - 功能 1：條件找茶
流程：
  1. 觸發 → 請傳位置（LocationAction Quick Reply）
  2. 收到位置 → 詢問類別（Quick Reply）
  3. 使用者選擇類別 → AI 搜尋附近飲品 → Flex Carousel
  4. 使用者點「✅ 選這個」→ 存入 DB
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
    FEATURE_CONDITION, CATEGORIES,
)
from handlers.utils import ask_for_location, query_drinks_from_ai, make_drink_carousel
from database.db import set_user_session

logger = logging.getLogger(__name__)


def trigger(event, user_id: str) -> None:
    """使用者觸發「條件找茶」，先請求位置。"""
    set_user_session(user_id, STATE_ASK_LOCATION, {"feature": FEATURE_CONDITION})
    ask_for_location(event, message="📍 想馬上知道附近有哪些好喝的嗎？只要跟我分享您的位置，我就能立刻幫您搜出周邊必喝的手搖飲喔！")


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
    """使用者選擇類別後，先回覆等待訊息，再呼叫 AI 並推送結果。"""
    category = user_input if user_input in CATEGORIES else "不限"
    ctx["category"] = category

    area     = ctx.get("area", ctx.get("address", "台灣"))
    address  = ctx.get("address", "")

    # 先回覆等待訊息
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🦭 豹豹正在努力查找中...請稍候，不要重複點擊喔！")],
            )
        )

    # 呼叫 AI 取得飲品選項
    drinks = query_drinks_from_ai(area, category, address=address, count=3)

    if not drinks:
        # AI 找不到 → 嘗試 DB 全站熱門飲品作為備援
        from database.db import get_popular_drinks, reset_user_session
        db_drinks = get_popular_drinks(limit=5)
        if db_drinks:
            for d in db_drinks:
                d["description"] = f"🔥 已被選擇 {d.get('select_count', 1)} 次"
            ctx["pending_drinks"] = db_drinks
            ctx["area"] = area
            set_user_session(user_id, "SHOW_OPTIONS", ctx)
            carousel = make_drink_carousel(db_drinks, area, user_id, is_fallback=True)
            with ApiClient(line_configuration) as api_client:
                from linebot.v3.messaging import PushMessageRequest
                MessagingApi(api_client).push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[
                            TextMessage(text="📍 附近暫時搜不到飲料店，但這些是大家都在推的人氣飲品喔！"),
                            FlexMessage(alt_text="人氣飲品推薦", contents=FlexContainer.from_dict(carousel)),
                        ],
                    )
                )
        else:
            reset_user_session(user_id)
            with ApiClient(line_configuration) as api_client:
                from linebot.v3.messaging import PushMessageRequest
                MessagingApi(api_client).push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text="抱歉，目前還沒有足夠的飲品資料，試試用「條件找茶」來累積吧！")],
                    )
                )
        return

    # 把 AI 推薦選項暫存至 session（供 postback 使用）
    ctx["pending_drinks"] = drinks
    ctx["area"] = area
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(drinks, area, user_id)
    with ApiClient(line_configuration) as api_client:
        from linebot.v3.messaging import PushMessageRequest
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
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
                    text="🍵 今天想來點什麼感覺的飲料呢？（像是清爽果茶，還是濃郁奶香？）",
                    quick_reply=QuickReply(items=items),
                )],
            )
        )


def _extract_area(address: str) -> str:
    """從完整地址萃取縣市＋區域＋里/路（更精確定位）。"""
    if not address:
        return "台灣"
    import re
    parts = address.replace("台灣", "").strip()
    # 嘗試取到路/街層級（如：台北市中山區南京東路）
    match = re.match(r"(.{2,4}[市縣]).{0,1}(.{2,4}[區鄉鎮市])(.{2,6}[路街道])?", parts)
    if match:
        return "".join(filter(None, match.groups()))
    return parts[:10] if len(parts) > 10 else parts

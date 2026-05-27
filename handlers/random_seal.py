"""
LINEBOTSCU - 功能 2：海豹隨機推（新版）
流程：
  1. 觸發 → 請傳位置
  2. 收到位置 → 顯示模式選擇：[ 🔥 最熱門 ] [ 🍵 依類別 ]
  3a. 最熱門 → 從 DB 依 select_count 加權抽選
  3b. 依類別 → 詢問類別 → 篩選後加權抽選
  4. DB 空時 → AI 直接推薦
  5. 顯示推薦卡片（含「✅ 選這個 / 🦭 再推一次」）
"""
import logging
import random

from linebot.v3.messaging import (
    ApiClient,
    FlexContainer,
    FlexMessage,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
)

from config import line_configuration
from handlers.states import (
    STATE_ASK_LOCATION, STATE_RANDOM_ASK_MODE,
    STATE_RANDOM_ASK_CATEGORY, FEATURE_RANDOM, CATEGORIES,
)
from handlers.utils import ask_for_location, query_drinks_from_ai
from database.db import (
    get_popular_drinks, get_popular_drinks_by_category,
    is_drinks_empty, set_user_session, reset_user_session,
)

logger = logging.getLogger(__name__)

MODES = ["🔥 最熱門", "🍵 依類別"]


def trigger(event, user_id: str) -> None:
    """觸發隨機推，先請求位置。"""
    set_user_session(user_id, STATE_ASK_LOCATION, {"feature": FEATURE_RANDOM})
    ask_for_location(event, feature_label="隨機推薦")


def on_location_received(event, user_id: str, lat: float, lng: float, address: str) -> None:
    """收到位置後，詢問推薦模式。"""
    from handlers.condition_tea import _extract_area
    ctx = {
        "feature": FEATURE_RANDOM,
        "lat":     lat,
        "lng":     lng,
        "address": address,
        "area":    _extract_area(address),
    }
    set_user_session(user_id, STATE_RANDOM_ASK_MODE, ctx)
    _ask_mode(event)


def on_mode_selected(event, user_id: str, ctx: dict, user_input: str) -> None:
    """使用者選擇推薦模式。"""
    area = ctx.get("area", "台灣")

    if "依類別" in user_input:
        ctx["random_mode"] = "by_category"
        set_user_session(user_id, STATE_RANDOM_ASK_CATEGORY, ctx)
        _ask_category(event)
    else:
        # 最熱門（預設）
        ctx["random_mode"] = "popular"
        reset_user_session(user_id)
        _show_popular(event, area, ctx)


def on_category_selected(event, user_id: str, ctx: dict, user_input: str) -> None:
    """依類別模式：使用者選擇類別後推薦。"""
    category = user_input if user_input in CATEGORIES else None
    area = ctx.get("area", "台灣")
    reset_user_session(user_id)
    _show_by_category(event, area, ctx, category)


def on_reroll(event, user_id: str) -> None:
    """使用者點「再推一次」（postback），以原有條件重新推薦。"""
    from database.db import get_user_session
    session = get_user_session(user_id)
    ctx  = session.get("context", {})
    area = ctx.get("area", "台灣")
    mode = ctx.get("random_mode", "popular")

    if mode == "by_category":
        category = ctx.get("category")
        _show_by_category(event, area, ctx, category)
    else:
        _show_popular(event, area, ctx)


# ─────────────────────────────────────────
# 推薦邏輯
# ─────────────────────────────────────────

def _show_popular(event, area: str, ctx: dict) -> None:
    """最熱門模式：從全部 DB 依 select_count 加權抽選。"""
    if is_drinks_empty():
        _fallback_ai(event, area, ctx.get("address", ""), "不限")
        return

    drinks = get_popular_drinks(limit=20)
    chosen = _weighted_choice(drinks)
    _reply_seal_card(event, chosen, ctx, mode_label="🔥 最熱門推薦")


def _show_by_category(event, area: str, ctx: dict, category: str | None) -> None:
    """依類別模式：篩選後加權抽選。"""
    if is_drinks_empty() or not category:
        _fallback_ai(event, area, ctx.get("address", ""), category or "不限")
        return

    drinks = get_popular_drinks_by_category(category, limit=15)
    if not drinks:
        _fallback_ai(event, area, ctx.get("address", ""), category)
        return

    ctx["category"] = category
    chosen = _weighted_choice(drinks)
    _reply_seal_card(event, chosen, ctx, mode_label=f"🍵 {category}類推薦")


def _fallback_ai(event, area: str, address: str, category: str) -> None:
    """DB 空或無資料時，AI 直接推薦一款（不存入 DB）。"""
    drinks = query_drinks_from_ai(area, category, address, count=1)
    if not drinks:
        _reply_text(event, "🦭 今天找不到推薦，請先用「條件找茶」選幾杯積累資料吧！")
        return

    d = drinks[0]
    _reply_text(
        event,
        f"🦭 海豹 AI 直接推薦（還沒有足夠資料）：\n\n"
        f"🏪 {d.get('shop', '')}\n"
        f"🍵 {d.get('drink', '')}\n"
        f"類別：{d.get('category', '')}\n\n"
        f"{d.get('description', '')}\n\n"
        f"💡 使用「條件找茶」選擇飲品後，隨機推薦會更準確喔！"
    )


def _weighted_choice(drinks: list[dict]) -> dict:
    """依 select_count 加權隨機抽選。"""
    weights = [max(d.get("select_count", 1), 1) for d in drinks]
    return random.choices(drinks, weights=weights, k=1)[0]


def _reply_seal_card(event, drink: dict, ctx: dict, mode_label: str) -> None:
    """回傳海豹推薦 Flex Message。"""
    tags_list = drink.get("tags") or []
    tags_str  = "  ".join([f"#{t}" for t in tags_list[:4]])

    # 存 pending 以供 postback 選擇
    ctx["pending_drinks"] = [drink]
    from database.db import set_user_session
    set_user_session(drink.get("shop_name", ""), "IDLE", {})  # 不需要存 session

    postback_select = "action=select_drink&idx=0"
    postback_reroll = "action=random_seal"

    flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🦭 海豹隨機推", "size": "sm", "color": "#FFFFFF", "weight": "bold"},
                {"type": "text", "text": mode_label, "size": "xs", "color": "#FFE0C0"},
            ],
            "backgroundColor": "#FF8C42",
            "paddingAll": "14px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {"type": "text", "text": drink.get("drink_name", ""), "size": "xxl", "weight": "bold", "color": "#5C3A1E", "wrap": True},
                {"type": "text", "text": f"🏪 {drink.get('shop_name', '')}", "size": "md", "color": "#FF8C42", "weight": "bold"},
                {"type": "separator", "color": "#FFE0C0"},
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "contents": [
                        {"type": "text", "text": f"🍵 {drink.get('category', '')}", "size": "sm", "color": "#9E7A5A", "flex": 1},
                    ],
                },
                {"type": "text", "text": tags_str, "size": "xs", "color": "#C97C3A", "wrap": True},
                {"type": "text", "text": f"🔥 已被選擇 {drink.get('select_count', 1)} 次", "size": "xs", "color": "#9E7A5A"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "postback", "label": "✅ 選這個！", "data": postback_select, "displayText": f"我選了 {drink.get('drink_name', '')}！"},
                    "style": "primary",
                    "color": "#FF8C42",
                    "flex": 1,
                    "height": "sm",
                },
                {
                    "type": "button",
                    "action": {"type": "postback", "label": "🦭 再推一次", "data": postback_reroll, "displayText": "再推一次 🦭"},
                    "style": "secondary",
                    "flex": 1,
                    "height": "sm",
                },
            ],
            "backgroundColor": "#FFF4E6",
        },
        "styles": {"body": {"backgroundColor": "#FFFAF5"}},
    }

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text=f"🦭 推薦：{drink.get('drink_name', '')}", contents=FlexContainer.from_dict(flex_content))],
            )
        )


# ─────────────────────────────────────────
# 輔助
# ─────────────────────────────────────────

def _ask_mode(event) -> None:
    items = [QuickReplyItem(action=MessageAction(label=m, text=m)) for m in MODES]
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🦭 要用哪種方式推薦呢？", quick_reply=QuickReply(items=items))],
            )
        )


def _ask_category(event) -> None:
    cats = [c for c in CATEGORIES if c != "不限"]
    items = [QuickReplyItem(action=MessageAction(label=c, text=c)) for c in cats]
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🍵 想喝哪種類型？", quick_reply=QuickReply(items=items))],
            )
        )


def _reply_text(event, text: str) -> None:
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text)],
            )
        )




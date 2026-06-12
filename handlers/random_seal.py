"""
LINEBOTSCU - 功能 2：海豹隨機推（新版）
流程：
  1. 觸發 → 請傳位置
  2. 收到位置 → 顯示模式選擇：[ 🏆 夯飲推薦 ] [ 🏷️ 逛逛分類 ]
  3a. 夯飲推薦 → 從 DB 取前3名 + 隨機抽2杯 → Carousel
  3b. 逛逛分類 → 詢問類別 → 同演算法
  4. DB 空時 → AI 直接推薦
  5. 顯示推薦 Carousel（含「✅ 選這個」按鈕）
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
from handlers.utils import ask_for_location, query_drinks_from_ai, make_drink_carousel
from database.db import (
    get_popular_drinks, get_popular_drinks_by_category,
    is_drinks_empty, set_user_session, reset_user_session,
)

logger = logging.getLogger(__name__)

MODES = ["🏆 夯飲推薦", "🏷️ 逛逛分類"]


def trigger(event, user_id: str) -> None:
    """觸發隨機推，先請求位置。"""
    set_user_session(user_id, STATE_ASK_LOCATION, {"feature": FEATURE_RANDOM})
    ask_for_location(event, message="📍 有點選擇障礙也沒關係！只要跟我分享您的位置，我就立刻幫您「隨機抽出」附近的解渴好去處喔！")


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

    if "逛逛分類" in user_input or "依類別" in user_input:
        ctx["random_mode"] = "by_category"
        set_user_session(user_id, STATE_RANDOM_ASK_CATEGORY, ctx)
        _ask_category(event)
    else:
        # 夯飲推薦（預設）
        ctx["random_mode"] = "popular"
        _show_popular(event, user_id, area, ctx)


def on_category_selected(event, user_id: str, ctx: dict, user_input: str) -> None:
    """依類別模式：使用者選擇類別後推薦。"""
    category = user_input if user_input in CATEGORIES else None
    area = ctx.get("area", "台灣")
    ctx["category"] = category
    _show_by_category(event, user_id, area, ctx, category)


def on_reroll(event, user_id: str) -> None:
    """使用者點「再推一次」（postback），以原有條件重新推薦。"""
    from database.db import get_user_session
    session = get_user_session(user_id)
    ctx  = session.get("context", {})
    area = ctx.get("area", "台灣")
    mode = ctx.get("random_mode", "popular")

    if mode == "by_category":
        category = ctx.get("category")
        _show_by_category(event, user_id, area, ctx, category)
    else:
        _show_popular(event, user_id, area, ctx)


# ─────────────────────────────────────────
# 推薦邏輯（新演算法：前3名 + 隨機2杯）
# ─────────────────────────────────────────

def _select_drinks(drinks: list[dict], top_n: int = 3, random_n: int = 2) -> list[dict]:
    """
    前 top_n 名固定推薦（人氣保證）+
    從第 top_n+1 名起隨機抽 random_n 杯（驚喜發現）。
    """
    if len(drinks) <= top_n:
        return drinks

    top = drinks[:top_n]
    rest = drinks[top_n:]
    surprise = random.sample(rest, min(random_n, len(rest)))
    return top + surprise


def _prepare_db_drinks(drinks: list[dict]) -> list[dict]:
    """把 DB 格式的飲品加上 description，方便 carousel 顯示。"""
    for d in drinks:
        d["description"] = f"🔥 已被選擇 {d.get('select_count', 1)} 次"
    return drinks


def _show_popular(event, user_id: str, area: str, ctx: dict) -> None:
    """夯飲推薦：前3名 + 隨機抽2杯，以 Carousel 顯示。"""
    if is_drinks_empty():
        _fallback_ai(event, area, ctx.get("address", ""), "不限")
        return

    drinks = get_popular_drinks(limit=20)
    selected = _select_drinks(drinks)
    selected = _prepare_db_drinks(selected)

    # 存 pending_drinks（用正確的 user_id！）
    ctx["pending_drinks"] = selected
    ctx["area"] = area
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(selected, area, user_id, is_fallback=True)
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"🦭 為您精選了 {len(selected)} 杯人氣飲品！前3名是人氣保證，後面的是驚喜推薦～"),
                    FlexMessage(alt_text="海豹隨機推", contents=FlexContainer.from_dict(carousel)),
                ],
            )
        )


def _show_by_category(event, user_id: str, area: str, ctx: dict, category: str | None) -> None:
    """依類別模式：篩選後取前3名 + 隨機2杯。"""
    if is_drinks_empty() or not category:
        _fallback_ai(event, area, ctx.get("address", ""), category or "不限")
        return

    drinks = get_popular_drinks_by_category(category, limit=15)
    if not drinks:
        _fallback_ai(event, area, ctx.get("address", ""), category)
        return

    selected = _select_drinks(drinks)
    selected = _prepare_db_drinks(selected)

    ctx["pending_drinks"] = selected
    ctx["area"] = area
    set_user_session(user_id, "SHOW_OPTIONS", ctx)

    carousel = make_drink_carousel(selected, area, user_id, is_fallback=True)
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"🦭 {category}類精選 {len(selected)} 杯！"),
                    FlexMessage(alt_text=f"海豹推薦 - {category}", contents=FlexContainer.from_dict(carousel)),
                ],
            )
        )


def _fallback_ai(event, area: str, address: str, category: str) -> None:
    """DB 空或無資料時，先回覆等待訊息，再用 AI 直接推薦。"""
    # 先回覆等待訊息
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🦭 豹豹正在努力查找中...請稍候，不要重複點擊喔！")],
            )
        )

    drinks = query_drinks_from_ai(area, category, address, count=1)

    user_id = event.source.user_id
    if not drinks:
        # AI 也找不到 → 嘗試 DB 全站熱門
        db_drinks = get_popular_drinks(limit=5)
        if db_drinks:
            db_drinks = _prepare_db_drinks(db_drinks)
            ctx = {"pending_drinks": db_drinks, "area": area}
            set_user_session(user_id, "SHOW_OPTIONS", ctx)
            carousel = make_drink_carousel(db_drinks, area, user_id)
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
            with ApiClient(line_configuration) as api_client:
                from linebot.v3.messaging import PushMessageRequest
                MessagingApi(api_client).push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text="抱歉，目前還沒有足夠的飲品資料，試試用「條件找茶」來累積吧！")],
                    )
                )
        return

    d = drinks[0]
    with ApiClient(line_configuration) as api_client:
        from linebot.v3.messaging import PushMessageRequest
        MessagingApi(api_client).push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(
                    text=(
                        f"🦭 海豹 AI 直接推薦（還沒有足夠資料）：\n\n"
                        f"🏪 {d.get('shop', '')}\n"
                        f"🍵 {d.get('drink', '')}\n"
                        f"類別：{d.get('category', '')}\n\n"
                        f"{d.get('description', '')}\n\n"
                        f"💡 使用「條件找茶」選擇飲品後，隨機推薦會更準確喔！"
                    )
                )],
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
                messages=[TextMessage(text="🦭準備好解渴了嗎？請選擇您喜歡的推薦方式喔！", quick_reply=QuickReply(items=items))],
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

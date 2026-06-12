"""
LINEBOTSCU - 文字訊息處理（全新版）
路由邏輯：
  1. 先查 user_sessions 狀態，處理進行中的多步驟對話
  2. 依關鍵字路由四大功能
  3. 預設：Gemini 多輪對話

新增：LocationMessage handler（接收使用者位置）
"""
import markdown
from bs4 import BeautifulSoup

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    FollowEvent,
    MessageEvent,
    TextMessageContent,
    LocationMessageContent,
)

from config import line_configuration, webhook_handler
from gemini_client import query
from database.db import get_user_session, reset_user_session

from handlers.states import (
    STATE_ASK_LOCATION,
    STATE_COND_ASK_CATEGORY,
    STATE_RANDOM_ASK_MODE, STATE_RANDOM_ASK_CATEGORY,
    FEATURE_CONDITION, FEATURE_RANDOM, FEATURE_NEW,
    CATEGORIES,
)
import handlers.condition_tea as condition_tea
import handlers.random_seal   as random_seal
import handlers.new_products  as new_products
from handlers.help_info import handle_help_info

# ─────────────────────────────────────────
# 觸發關鍵字
# ─────────────────────────────────────────
KEYWORDS_CONDITION = {"條件找茶", "找茶", "條件搜尋"}
KEYWORDS_RANDOM    = {"海豹隨機推", "隨機推薦", "隨機", "推薦一杯", "幫我選"}
KEYWORDS_NEW       = {"最新主打", "新品", "最新", "當季新品"}
KEYWORDS_HELP      = {"使用說明", "說明", "幫助", "help", "menu", "選單"}


# ─────────────────────────────────────────
# 位置訊息 Handler
# ─────────────────────────────────────────

@webhook_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    """接收使用者傳來的位置訊息，依目前狀態分派至對應功能。"""
    user_id = event.source.user_id
    session = get_user_session(user_id)
    state   = session.get("state", "IDLE")
    ctx     = session.get("context", {})
    feature = ctx.get("feature", "")

    if state != STATE_ASK_LOCATION:
        # 非預期位置訊息，忽略
        return

    lat     = event.message.latitude
    lng     = event.message.longitude
    address = event.message.address or ""

    if feature == FEATURE_CONDITION:
        condition_tea.on_location_received(event, user_id, lat, lng, address)
    elif feature == FEATURE_RANDOM:
        random_seal.on_location_received(event, user_id, lat, lng, address)
    else:
        reset_user_session(user_id)


# ─────────────────────────────────────────
# 加入好友 Handler
# ─────────────────────────────────────────

@webhook_handler.add(FollowEvent)
def handle_follow(event):
    """使用者加入好友時發送歡迎訊息。"""
    from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
    user_id = event.source.user_id

    # 嘗試取得使用者名稱
    display_name = ""
    try:
        with ApiClient(line_configuration) as api_client:
            profile = MessagingApi(api_client).get_profile(user_id)
            display_name = profile.display_name
    except Exception:
        pass

    greeting = f"哈囉 {display_name}！" if display_name else "哈囉！"

    welcome_text = (
        f"{greeting}👋 很高興認識您～\n"
        f"我是您的專屬「飲料推薦小幫手」🥤\n"
        f"超級感謝您把我加入好友！"
        f"以後不管是下午茶想來點咀嚼感，還是需要清爽解渴，"
        f"我都會第一時間為您送上最新的必喝情報喔\n"
        f"準備好迎接滿滿的飲料驚喜了嗎？敬請期待啦！"
    )

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=welcome_text)],
            )
        )


# ─────────────────────────────────────────
# 文字訊息 Handler
# ─────────────────────────────────────────

@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """處理文字訊息：先查狀態，再路由功能，最後 Gemini 對話。"""
    user_id     = event.source.user_id
    user_input  = event.message.text.strip()
    lower_input = user_input.lower()

    session = get_user_session(user_id)
    state   = session.get("state", "IDLE")
    ctx     = session.get("context", {})
    feature = ctx.get("feature", "")

    # ── 步驟 1：進行中的多步驟對話 ──────────────────
    if state == STATE_COND_ASK_CATEGORY:
        condition_tea.on_category_selected(event, user_id, ctx, user_input)
        return



    if state == STATE_RANDOM_ASK_MODE:
        random_seal.on_mode_selected(event, user_id, ctx, user_input)
        return

    if state == STATE_RANDOM_ASK_CATEGORY:
        random_seal.on_category_selected(event, user_id, ctx, user_input)
        return

    # ── 步驟 2：功能關鍵字路由 ───────────────────────
    from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
    from config import line_configuration
    if user_input in ["你好", "您好", "hi", "嗨", "hello"]:
        with ApiClient(line_configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="您好！需要找飲料的話，請直接點選下方選單喔！")]
                )
            )
        return

    if any(kw in user_input for kw in KEYWORDS_CONDITION):
        condition_tea.trigger(event, user_id)
        return

    if any(kw in user_input for kw in KEYWORDS_RANDOM):
        random_seal.trigger(event, user_id)
        return

    if any(kw in user_input for kw in KEYWORDS_NEW):
        new_products.trigger(event, user_id, user_input)
        return

    if any(kw in lower_input for kw in KEYWORDS_HELP):
        handle_help_info(event)
        return

    # ── 步驟 3：Gemini 多輪對話（預設）──────────────
    response_text = query(user_input)
    html_msg  = markdown.markdown(response_text)
    plain_text = BeautifulSoup(html_msg, "html.parser").get_text()

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=plain_text)],
            )
        )

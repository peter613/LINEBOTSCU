"""
LINEBOTSCU - Flask 主程式（全新版）
新增：
  - PostbackEvent handler（處理「✅ 選這個」存入 DB / 「再推一次」）
  - LocationMessage 在 text_handler.py 處理
"""
import logging

from flask import Flask, abort, request, send_from_directory
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import PostbackEvent

from config import line_configuration, static_tmp_path, webhook_handler

# === 載入各訊息處理器 ===
import text_handler   # noqa: F401  (含 LocationMessage handler)

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
app.logger.setLevel(logging.INFO)


# ─────────────────────────────────────────
# Postback Handler
# ─────────────────────────────────────────

@webhook_handler.add(PostbackEvent)
def handle_postback(event):
    """
    處理所有 Flex Message 按鈕的 Postback 事件。
    action=select_drink&idx=N  → 從 session 取得飲品資訊，upsert 至 DB
    action=random_seal         → 重新觸發隨機推
    """
    user_id = event.source.user_id
    data    = event.postback.data
    params  = dict(p.split("=", 1) for p in data.split("&") if "=" in p)
    action  = params.get("action", "")

    if action == "select_drink":
        _handle_select_drink(event, user_id, params)

    elif action == "random_seal":
        # 重新觸發隨機推（需重傳位置才能繼續，這裡直接讓使用者再推）
        from handlers.random_seal import on_reroll
        on_reroll(event, user_id)

    else:
        app.logger.warning("未知的 postback action: %s", action)


def _handle_select_drink(event, user_id: str, params: dict) -> None:
    """
    取得使用者 session 中的 pending_drinks[idx]，存入 DB。
    """
    from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
    from database.db import get_user_session, reset_user_session, upsert_drink

    try:
        idx = int(params.get("idx", 0))
    except ValueError:
        idx = 0

    session       = get_user_session(user_id)
    ctx           = session.get("context", {})
    pending       = ctx.get("pending_drinks", [])
    area          = ctx.get("area", "未知區域")

    if not pending or idx >= len(pending):
        with ApiClient(line_configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="⚠️ 找不到對應飲品，請重新查詢。")],
                )
            )
        return

    drink = pending[idx]

    # 相容 AI 回傳格式（shop/drink）與 DB 格式（shop_name/drink_name）
    shop_name  = drink.get("shop_name") or drink.get("shop", "未知店家")
    drink_name = drink.get("drink_name") or drink.get("drink", "未知飲品")
    category   = drink.get("category", "")
    tags       = drink.get("tags") or []

    upsert_drink(
        shop_name=shop_name,
        drink_name=drink_name,
        category=category,
        tags=tags,
        area=area,
    )

    reset_user_session(user_id)

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text=(
                        f"✅ 已記錄！\n\n"
                        f"🏪 {shop_name}\n"
                        f"🍵 {drink_name}\n\n"
                        f"下次「🦭 隨機推」會把它列入候選喔！"
                    )
                )],
            )
        )


# ─────────────────────────────────────────
# 靜態媒體 / 健康檢查 / Webhook
# ─────────────────────────────────────────

@app.route("/images/<filename>")
def serve_media(filename):
    return send_from_directory(static_tmp_path, filename)


@app.route("/", methods=["GET"])
def home():
    return {"message": "LINEBOTSCU Webhook Server is running. 🧋"}


@app.route("/", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body      = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature.")
        abort(400)
    return "OK"

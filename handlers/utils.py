"""
LINEBOTSCU - 共用工具函式
位置請求、Flex 卡片建立、Gemini JSON 解析等
"""
import json
import logging
import re

from linebot.v3.messaging import (
    ApiClient,
    FlexMessage,
    LocationAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
)

from config import line_configuration
from gemini_client import tea_query

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# 位置請求
# ─────────────────────────────────────────

def ask_for_location(event, feature_label: str = "推薦") -> None:
    """
    傳送 Quick Reply 位置按鈕，引導使用者分享位置。
    使用者點按鈕後 LINE 自動開啟地圖，不需手動輸入文字。
    """
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text=f"📍 為了提供您附近的{feature_label}，請先分享您的位置！",
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(
                                action=LocationAction(label="📍 傳送我的位置")
                            )
                        ]),
                    )
                ],
            )
        )


# ─────────────────────────────────────────
# Gemini 結構化查詢
# ─────────────────────────────────────────

def query_drinks_from_ai(area: str, category: str, sweetness: str, count: int = 3) -> list[dict]:
    """
    請 Gemini 以 JSON 格式推薦飲品。
    回傳：[{"shop": ..., "drink": ..., "category": ..., "sweetness": ..., "tags": [...], "description": ...}]
    解析失敗時回傳空 list。
    """
    cat_str = category if category and category != "不限" else "任何類別"
    sw_str  = sweetness if sweetness and sweetness != "不限" else "任何甜度"

    prompt = (
        f"你是台灣手搖飲料推薦達人，使用 Google Search 搜尋。使用者位置：{area}。\n"
        f"請推薦 {count} 款在「{area}」附近可能找到的手搖飲品，"
        f"條件：類別={cat_str}，甜度={sw_str}。\n"
        f"【重要：請嚴格使用繁體中文（台灣）回覆，絕對禁止使用簡體中文】\n"
        f"嚴格只回覆以下 JSON 格式，不要任何其他文字或說明：\n"
        f'[\n'
        f'  {{"shop": "店家名稱", "drink": "飲品名稱", "category": "類別", '
        f'"sweetness": "甜度", "tags": ["標籤1", "標籤2"], '
        f'"description": "一句話特色描述", '
        f'"image_url": "該飲品的網路圖片直連 URL（https://），找不到填 null"}}\n'
        f']'
    )
    raw = tea_query(prompt)
    return _parse_json_list(raw)


def query_new_products_from_ai(area: str, count: int = 4) -> list[dict]:
    """
    請 Gemini 搜尋附近店家當季新品（JSON 格式）。
    """
    prompt = (
        f"你是台灣手搖飲料達人，請用 Google Search 搜尋「{area}附近手搖飲料 最新 季節限定 新品」。\n"
        f"列出 {count} 款近期推出的新品或季節限定飲品。\n"
        f"【重要：請嚴格使用繁體中文（台灣）回覆，絕對禁止使用簡體中文】\n"
        f"嚴格只回覆以下 JSON 格式，不要任何其他文字：\n"
        f'[\n'
        f'  {{"shop": "店家名稱", "drink": "飲品名稱", "category": "類別", '
        f'"sweetness": "甜度（不確定填不限）", "tags": ["新品", "季節限定"], '
        f'"description": "一句話特色描述", '
        f'"image_url": "該飲品的網路圖片直連 URL（https://），找不到填 null"}}\n'
        f']'
    )
    raw = tea_query(prompt)
    return _parse_json_list(raw)


def _parse_json_list(raw: str) -> list[dict]:
    """從 Gemini 回應中萃取 JSON 陣列。"""
    try:
        # 嘗試直接解析
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # 嘗試從 markdown code block 萃取
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # 嘗試直接找 [...] 區塊
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("無法解析 Gemini JSON 回應：%s", raw[:200])
    return []


# ─────────────────────────────────────────
# Flex Message 建立
# ─────────────────────────────────────────

def make_drink_carousel(drinks: list[dict], area: str) -> dict:
    """
    建立飲品推薦 Flex Carousel。
    每張卡片含 hero 圖片（若有 image_url）和「✅ 選這個！」按鈕。
    """
    bubbles = []
    for idx, d in enumerate(drinks):
        tags_str      = "  ".join([f"#{t}" for t in (d.get("tags") or [])[:3]])
        postback_data = f"action=select_drink&idx={idx}"
        image_url     = d.get("image_url") or ""
        # 只接受 https:// 開頭的圖片 URL
        has_image = image_url.startswith("https://")

        bubble: dict = {
            "type": "bubble",
            "size": "kilo",
        }

        # ── Hero 圖片（有圖才加）──
        if has_image:
            bubble["hero"] = {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            }

        bubble["header"] = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": d.get("shop", "") or d.get("shop_name", ""),
                "size": "sm",
                "weight": "bold",
                "color": "#FFFFFF",
            }],
            "backgroundColor": "#FF8C42",
            "paddingAll": "12px",
        }

        bubble["body"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": d.get("drink", "") or d.get("drink_name", ""),
                    "size": "xl",
                    "weight": "bold",
                    "color": "#5C3A1E",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": f"{d.get('category', '')}  ·  {d.get('sweetness', '')}",
                    "size": "sm",
                    "color": "#9E7A5A",
                },
                {
                    "type": "text",
                    "text": tags_str,
                    "size": "xs",
                    "color": "#C97C3A",
                    "wrap": True,
                },
                {
                    "type": "separator",
                    "color": "#FFE0C0",
                    "margin": "sm",
                },
                {
                    "type": "text",
                    "text": d.get("description", ""),
                    "size": "xs",
                    "color": "#5C3A1E",
                    "wrap": True,
                },
            ],
        }

        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "✅ 選這個！",
                    "data": postback_data,
                    "displayText": f"我選了 {d.get('drink', '') or d.get('drink_name', '')}！",
                },
                "style": "primary",
                "color": "#FF8C42",
                "height": "sm",
            }],
            "backgroundColor": "#FFF4E6",
        }

        bubble["styles"] = {"body": {"backgroundColor": "#FFFAF5"}}
        bubbles.append(bubble)

    return {"type": "carousel", "contents": bubbles}


def reply_text(event, text: str) -> None:
    """快速回覆純文字訊息。"""
    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text)],
            )
        )

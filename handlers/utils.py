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

def ask_for_location(event, message: str = "📍 請分享您的位置！") -> None:
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
                        text=message,
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(
                                action=LocationAction(label="📍 分享位置")
                            )
                        ]),
                    )
                ],
            )
        )


# ─────────────────────────────────────────
# Gemini 結構化查詢
# ─────────────────────────────────────────

def query_drinks_from_ai(area: str, category: str, address: str = "", count: int = 3) -> list[dict]:
    """
    請 Gemini 以 JSON 格式推薦飲品。
    回傳：[{"shop": ..., "drink": ..., "category": ..., "tags": [...], "description": ...}]
    解析失敗時回傳空 list。
    """
    cat_str = category if category and category != "不限" else "任何類別"
    location_str = address if address else area

    prompt = (
        f"我現在人在「{location_str}」，請用 Google 搜尋，推薦{count}款附近（步行距離佳）的手搖飲料店的飲品，類別={cat_str}。\n"
        f"【規定】\n"
        f"1. 必須是「{location_str}」附近實際存在的店家，請盡量推薦步行可到的手搖飲料店。\n"
        f"2. 若附近真的沒飲料店，稍微遠一點點的同行政區店家也可以，不要輕易回傳空陣列。\n"
        f"3. 為了版面整潔，回傳的「shop」欄位【只能填寫品牌名稱】，絕對不可以包含分店名稱！(例如只能填「清心福全」，不可填「清心福全 士林店」)。\n"
        f"繁體中文，僅回JSON：\n"
        f'[{{"shop":"品牌名稱","drink":"品名","category":"類別",'
        f'"tags":["標籤"],"description":"特色"}}]\n'
    )
    raw = tea_query(prompt)
    return _parse_json_list(raw)


def query_new_products_from_ai(area: str, address: str = "", count: int = 4) -> list[dict]:
    """
    請 Gemini 搜尋附近店家當季新品（JSON 格式）。
    """
    location_str = address if address else area
    prompt = (
        f"我現在人在「{location_str}」，請用 Google 搜尋，找出各大手搖連鎖品牌（不需要限定在我附近）的{count}款最新/季節限定新品。\n"
        f"【嚴格規定】\n"
        f"1. 請推薦全台灣知名連鎖品牌（例如五十嵐、麻古、清心等）的最新主打商品。\n"
        f"2. 因為不需要限定在使用者附近，所以不需要回報特定的分店名稱，只要給品牌名稱即可。\n"
        f"3. 如果找不到真實的新品，請直接回覆空 JSON 陣列 []，絕對不要編造。\n"
        f"繁體中文，僅回JSON：\n"
        f'[{{"brand":"品牌名稱","drink":"品名","category":"類別",'
        f'"tags":["新品"],"description":"特色"}}]\n'
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

def make_drink_carousel(drinks: list[dict], area: str, user_id: str = "", is_fallback: bool = False) -> dict:
    """
    建立飲品推薦 Flex Carousel。
    is_fallback: 若為 True，代表是資料庫抓出的驚喜名單，需要過濾掉原本存的分店名稱，只保留品牌名。
    """
    import urllib.parse

    bubbles = []
    for idx, d in enumerate(drinks):
        tags_str      = "  ".join([f"#{t}" for t in (d.get("tags") or [])[:3]])
        
        postback_data = f"action=select_drink&idx={idx}"

        # 處理店名：無條件過濾分店名，確保不會出現地名
        shop_text = d.get("shop", "") or d.get("shop_name", "") or d.get("brand", "")
        import re
        shop_text = re.sub(r'\(.*?\)', '', shop_text)
        shop_text = re.sub(r'（.*?）', '', shop_text)
        shop_text = shop_text.replace('-', ' ').replace('_', ' ').replace('－', ' ')
        shop_text = shop_text.split()[0] if shop_text.split() else shop_text

        bubble: dict = {
            "type": "bubble",
            "size": "kilo",
        }

        bubble["header"] = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": shop_text,
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
                    "text": f"{d.get('category', '')}",
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
                    "label": "🔗 點我進官網",
                    "data": postback_data,
                    "displayText": f"我選了 {shop_text}！",
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

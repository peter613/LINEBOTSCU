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

def query_drinks_from_ai(area: str, category: str, address: str = "", count: int = 3) -> list[dict]:
    """
    請 Gemini 以 JSON 格式推薦飲品。
    回傳：[{"shop": ..., "drink": ..., "category": ..., "tags": [...], "description": ...}]
    解析失敗時回傳空 list。
    """
    cat_str = category if category and category != "不限" else "任何類別"
    location_str = address if address else area

    prompt = (
        f"推薦{count}款在「{location_str}」走路5分鐘內可到的手搖飲，類別={cat_str}。"
        f"必須是非常近的店家。繁體中文，僅回JSON："
        f'[{{"shop":"店名","drink":"品名","category":"類別",'
        f'"price": null, "tags":["標籤"],"description":"特色",'
        f'"image_url":"圖片URL或null"}}]'
        # 不要憑空編價格：若不知道確切價格，請回 `null` 作為 price；不要估計或自行編價格。
    )
    raw = tea_query(prompt)
    items = _parse_json_list(raw)
    return _tag_ai_price_source(items)


def query_new_products_from_ai(area: str, address: str = "", count: int = 4) -> list[dict]:
    """
    請 Gemini 搜尋附近店家當季新品（JSON 格式）。
    """
    location_str = address if address else area
    prompt = (
        f"搜尋「{location_str}」走路5分鐘內可到的手搖飲{count}款最新/季節限定新品。"
        f"必須是非常近的店家。繁體中文，僅回JSON："
        f'[{{"shop":"店名","drink":"品名","category":"類別",'
        f'"price": null, "tags":["新品"],"description":"特色",'
        f'"image_url":"圖片URL或null"}}]'
        # 不要憑空編價格：若不知道確切價格，請回 `null` 作為 price；不要估計或自行編價格。
    )
    raw = tea_query(prompt)
    items = _parse_json_list(raw)
    return _tag_ai_price_source(items)


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


def _tag_ai_price_source(items: list[dict]) -> list[dict]:
    """標記 AI 回傳的項目為來自 AI（price_source='ai'），以便前端顯示時可標註為估計或略過存入 DB。"""
    for it in items:
        if "price" in it and it.get("price") is not None:
            it["price_source"] = "ai"
        else:
            it["price_source"] = None
    return items


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
        price_text    = d.get("price") or d.get("price_text") or ""
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

        # 顯示價格（若有），並標註來源：AI 提供的價格標為估計
        price_val = d.get("price") or d.get("price_value")
        price_block = []
        price_text = ""
        if price_val is not None:
            try:
                pv = float(price_val)
                if pv.is_integer():
                    price_text = f"💲 {int(pv)} 元"
                else:
                    price_text = f"💲 {pv:.2f} 元"
            except Exception:
                price_text = str(price_val)

            # 若為 AI 回傳，標註為估計
            if d.get("price_source") == "ai":
                price_text = f"{price_text}（估計）"

            price_block = [{
                "type": "text",
                "text": price_text,
                "size": "sm",
                "color": "#5C3A1E",
            }]

        body_contents = [
            {
                "type": "text",
                "text": d.get("drink", "") or d.get("drink_name", ""),
                "size": "xl",
                "weight": "bold",
                "color": "#5C3A1E",
                "wrap": True,
            },
        ]
        # 插入價格區塊（若有）
        if price_block:
            body_contents.extend(price_block)

        body_contents.extend([
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
        ])

        bubble["body"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": body_contents,
        }
        # 不要在此重複插入價格（已在 body_contents 中處理）

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

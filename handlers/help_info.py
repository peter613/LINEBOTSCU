"""
LINEBOTSCU - 功能 4：使用說明
顯示系統操作方式（靜態 Flex Message）。
"""
import logging

from linebot.v3.messaging import (
    ApiClient,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    ReplyMessageRequest,
)

from config import line_configuration

logger = logging.getLogger(__name__)


def handle_help_info(event) -> None:
    """回傳使用說明 Flex Message。"""
    flex_content = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "今天也要喝到豹小幫手秘笈 ✨",
                    "size": "lg",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "wrap": True,
                },
            ],
            "backgroundColor": "#FF8C42",
            "paddingAll": "20px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "lg",
            "contents": [
                # 功能一
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🍵 條件找茶",
                            "size": "md",
                            "weight": "bold",
                            "color": "#FF8C42",
                        },
                        {
                            "type": "text",
                            "text": "想喝什麼自己配！點擊選單或輸入「條件找茶」，跟著步驟選好喜歡的類型，讓我為您精準撈出最完美的那一杯！",
                            "size": "sm",
                            "color": "#5C3A1E",
                            "wrap": True,
                        },
                    ],
                },
                {"type": "separator", "color": "#FFE0C0"},
                # 功能二
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🦭 海豹隨機推",
                            "size": "md",
                            "weight": "bold",
                            "color": "#FF8C42",
                        },
                        {
                            "type": "text",
                            "text": "選擇障礙發作了嗎？輸入「海豹隨機推」或「隨機推薦」，讓我從高人氣排行榜中，直接為您抽出一杯命定飲料吧！",
                            "size": "sm",
                            "color": "#5C3A1E",
                            "wrap": True,
                        },
                    ],
                },
                {"type": "separator", "color": "#FFE0C0"},
                # 功能三
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🌟 最新主打",
                            "size": "md",
                            "weight": "bold",
                            "color": "#FF8C42",
                        },
                        {
                            "type": "text",
                            "text": "飲料控絕不能錯過的新品情報！輸入「最新主打」就能看當季最新鮮的飲料。有特別愛喝哪家，也可以直接輸入「清心最新」來挖寶喔！",
                            "size": "sm",
                            "color": "#5C3A1E",
                            "wrap": True,
                        },
                    ],
                },
                {"type": "separator", "color": "#FFE0C0"},
                # 其他功能
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💬 其他對話",
                            "size": "md",
                            "weight": "bold",
                            "color": "#FF8C42",
                        },
                        {
                            "type": "text",
                            "text": "有任何關於飲料的疑難雜症？直接打字跟我說，聰明的 AI 小助手隨時為您解答！",
                            "size": "sm",
                            "color": "#5C3A1E",
                            "wrap": True,
                        },
                    ],
                },
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFAF5",
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "contents": [
                {
                    "type": "text",
                    "text": "💻 製作團隊",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#FF8C42",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": "東吳大學",
                    "size": "xs",
                    "color": "#9E7A5A",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": "Syoutobi & Yuki & Mori & Joyce",
                    "size": "xs",
                    "color": "#C97C3A",
                    "align": "center",
                },
            ],
            "backgroundColor": "#FFF4E6",
            "paddingAll": "16px",
        },
    }

    with ApiClient(line_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage(
                        alt_text="LINEBOTSCU 找茶小幫手秘笈",
                        contents=FlexContainer.from_dict(flex_content),
                    )
                ],
            )
        )

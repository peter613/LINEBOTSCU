"""
LINEBOTSCU - 功能 4：使用說明
顯示系統操作方式與製作人員名單（靜態 Flex Message）。
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
                    "text": "🧋 LINEBOTSCU",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#FFFFFF",
                },
                {
                    "type": "text",
                    "text": "茶飲推薦系統使用說明",
                    "size": "sm",
                    "color": "#FFE0C0",
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
                            "text": "輸入「條件找茶」或點選選單，按步驟選擇飲品類型與甜度，系統為你篩選最合適的飲品！",
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
                            "text": "輸入「海豹隨機推」或「隨機推薦」，由系統依人氣評分隨機幫你選一杯！",
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
                            "text": "輸入「最新主打」查看各大品牌當季新品。\n也可以輸入「清心最新」等指定品牌查詢！",
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
                            "text": "直接輸入任何問題，AI 助手會回答你！",
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
                    "text": "👩‍💻 製作團隊",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#FF8C42",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": "東吳大學巨量資料管理學系",
                    "size": "xs",
                    "color": "#9E7A5A",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": "LINEBOTSCU Project Team",
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
                        alt_text="LINEBOTSCU 使用說明",
                        contents=FlexContainer.from_dict(flex_content),
                    )
                ],
            )
        )

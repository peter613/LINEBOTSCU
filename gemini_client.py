"""
LINEBOTSCU - Google Gemini AI 初始化
包含：client、多輪對話 chat、Google Search 工具、query 函式
新增：茶飲推薦專用 tea_query() 函式
"""
import os

from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

# === 初始化 Google Gemini ===
GOOGLE_GEMINI_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")
client = genai.Client(api_key=GOOGLE_GEMINI_API_KEY)

# === Google Search 工具 ===
google_search_tool = Tool(google_search=GoogleSearch())

# === 多輪對話物件 (全域，維持對話記憶) ===
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=GenerateContentConfig(
        system_instruction=(
            "你是手搖飲助理，嚴格用繁體中文回答。"
            "勿詢問使用者位置，引導他們點選單【條件找茶】或【隨機推薦】傳送LINE位置。"
            "茶飲知識可簡答(100字內)，適時提醒用選單找店。"
        ),
        tools=[google_search_tool],
        response_modalities=["TEXT"],
    ),
)


def query(payload: str) -> str:
    """送出訊息給 Gemini 並回傳純文字回應。"""
    response = chat.send_message(message=payload)
    return response.text


def tea_query(prompt: str) -> str:
    """
    茶飲推薦專用 Gemini 查詢（獨立 session，帶 Google Search）。
    System instruction 指定為台灣手搖飲料專家角色。
    """
    tea_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=GenerateContentConfig(
            system_instruction=(
                "你是台灣手搖飲達人，熟悉各大品牌菜單。"
                "嚴格用繁體中文，簡潔回答(100字內)。"
            ),
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        ),
    )
    response = tea_chat.send_message(message=prompt)
    return response.text

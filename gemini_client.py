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
    model="gemini-2.0-flash",
    config=GenerateContentConfig(
        system_instruction="你是一個中文的AI助手，請用繁體中文回答",
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
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction=(
                "你是一位專業的台灣手搖飲料達人，熟悉各大知名飲料品牌（如清心福全、五十嵐、茶湯會、"
                "大苑子、一芳水果茶、麻古茶坊、迷客夏、鶴茶樓等）的菜單與特色商品。"
                "請以活潑、親切的繁體中文回答，並提供具體的飲品推薦與描述。"
                "回答請簡潔有力，適合在 LINE 訊息中閱讀（不超過200字）。"
            ),
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        ),
    )
    response = tea_chat.send_message(message=prompt)
    return response.text

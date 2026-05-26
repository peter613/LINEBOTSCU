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
        system_instruction=(
            "你是 LINEBOTSCU 手搖飲推薦助理，請「嚴格使用繁體中文（台灣）」回答，絕對禁止使用簡體中文。\n"
            "【重要規則】\n"
            "1. 若使用者想找飲料或店家，請「絕對不要」在對話中詢問他們的位置或地址。\n"
            "2. 請直接引導他們：「若想尋找附近的飲料店，請點擊下方選單的【條件找茶】或【隨機推薦】按鈕，接著傳送您的『LINE 所在位置』，我就會為您推薦！」\n"
            "3. 針對單純的茶飲知識問答（如：什麼是伯爵茶？），你可以直接簡短回答（200字內），並適時提醒他們可以使用選單來找附近的店。"
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
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction=(
                "你是一位專業的台灣手搖飲料達人，熟悉各大知名飲料品牌（如清心福全、五十嵐、茶湯會、"
                "大苑子、一芳水果茶、麻古茶坊、迷客夏、鶴茶樓等）的菜單與特色商品。\n"
                "【重要規則】\n"
                "1. 請「嚴格使用繁體中文（台灣）」回答，絕對禁止使用簡體中文。\n"
                "2. 回答請活潑、親切，並提供具體的飲品推薦與描述。\n"
                "3. 回答請簡潔有力，適合在 LINE 訊息中閱讀（不超過200字）。"
            ),
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        ),
    )
    response = tea_chat.send_message(message=prompt)
    return response.text

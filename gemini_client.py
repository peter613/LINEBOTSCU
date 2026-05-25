"""
LINEBOTSCU - Google Gemini AI 初始化
包含：client、多輪對話 chat、Google Search 工具、query 函式
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

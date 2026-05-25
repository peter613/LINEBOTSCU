"""
LINEBOTSCU - 東吳大學資料系 LINE Bot
共用設定：LINE 憑證、Webhook Handler、暫存路徑
"""
import os
import tempfile

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration

# === LINE 頻道設定 ===
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

line_configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === 暫存路徑 (存放媒體檔案) ===
static_tmp_path = tempfile.gettempdir()
os.makedirs(static_tmp_path, exist_ok=True)

# === Hugging Face Space 公開 URL ===
base_url = os.getenv("SPACE_HOST")  # e.g., "your-space-name.hf.space"

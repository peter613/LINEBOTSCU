"""
LINEBOTSCU - Flask 主程式
LINE Bot Webhook Server，整合 Gemini AI
"""
import logging

from flask import Flask, abort, request, send_from_directory
from linebot.v3.exceptions import InvalidSignatureError

from config import line_configuration, static_tmp_path, webhook_handler

# === 載入各訊息處理器 (觸發 @webhook_handler.add 裝飾器) ===
import text_handler   # noqa: F401
import image_handler  # noqa: F401
import video_handler  # noqa: F401

# === Flask 應用初始化 ===
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
app.logger.setLevel(logging.INFO)


# === 靜態媒體檔案路由 ===
@app.route("/images/<filename>")
def serve_media(filename):
    """提供暫存的圖片或影片檔案。"""
    return send_from_directory(static_tmp_path, filename)


# === LINE Webhook 端點 ===
@app.route("/", methods=["GET"])
def home():
    """健康檢查端點。"""
    return {"message": "LINEBOTSCU Webhook Server is running."}


@app.route("/", methods=["POST"])
def callback():
    """接收並驗證來自 LINE 的 Webhook 請求。"""
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)

    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature. Please check channel credentials.")
        abort(400)

    return "OK"

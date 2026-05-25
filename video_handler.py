"""
LINEBOTSCU - 影片訊息處理
功能：
  - 下載使用者傳來的影片
  - 使用 Gemini 分析影片內容
  - 回傳影片連結 + 文字說明
"""
import os
import tempfile
from io import BytesIO

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, VideoMessageContent

from google.genai import types

from config import base_url, line_configuration, static_tmp_path, webhook_handler
from gemini_client import client, google_search_tool


@webhook_handler.add(MessageEvent, message=VideoMessageContent)
def handle_video_message(event):
    """處理使用者傳來的影片訊息。"""
    # === 下載影片 ===
    with ApiClient(line_configuration) as api_client:
        blob_api = MessagingApiBlob(api_client)
        video_data = blob_api.get_message_content(message_id=event.message.id)

    if video_data is None:
        err_msg = "抱歉，無法取得影片內容。"
        with ApiClient(line_configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=err_msg)],
                )
            )
        return

    # === 儲存影片到本地 ===
    with tempfile.NamedTemporaryFile(
        dir=static_tmp_path, suffix=".mp4", delete=False
    ) as tf:
        tf.write(video_data)
        filename = os.path.basename(tf.name)

    video_url = f"https://{base_url}/images/{filename}"

    # === Gemini 解析影片 ===
    try:
        video_bytes = BytesIO(video_data)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            config=types.GenerateContentConfig(
                system_instruction="你是一個專業的影片解說員，請用繁體中文簡要說明這段影片的內容。",
                response_modalities=["TEXT"],
                tools=[google_search_tool],
            ),
            contents=[video_bytes, "用繁體中文描述這段影片"],
        )
        description = response.text
    except Exception as e:
        description = "抱歉，無法解釋這段影片內容。"

    # === 回傳影片連結 + 說明文字 ===
    with ApiClient(line_configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"影片連結：{video_url}"),
                    TextMessage(text=description),
                ],
            )
        )

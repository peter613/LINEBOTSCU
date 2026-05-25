"""
LINEBOTSCU - 圖片訊息處理
功能：
  - 下載使用者傳來的圖片
  - 使用 Gemini 解析圖片 (面相/手相/一般描述)
  - 回傳圖片 + 文字解析結果
"""
import os
import tempfile

from PIL import Image

from linebot.v3.messaging import (
    ApiClient,
    ImageMessage,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import ImageMessageContent, MessageEvent

from google.genai import types

from config import base_url, line_configuration, static_tmp_path, webhook_handler
from gemini_client import client, google_search_tool


@webhook_handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    """處理使用者傳來的圖片訊息。"""
    # === 下載圖片並存到本地 ===
    with ApiClient(line_configuration) as api_client:
        blob_api = MessagingApiBlob(api_client)
        content = blob_api.get_message_content(message_id=event.message.id)

    with tempfile.NamedTemporaryFile(
        dir=static_tmp_path, suffix=".jpg", delete=False
    ) as tf:
        tf.write(content)
        filename = os.path.basename(tf.name)

    image_url = f"https://{base_url}/images/{filename}"

    # === Gemini 解析圖片 ===
    image = Image.open(tf.name)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "你是一個資深的面相命理師，"
                "如果有人上手掌的照片，就幫他解釋手相，"
                "如果上傳正面臉部的照片，就幫他解釋面相，"
                "如果是一般的照片，就正常說明照片不用算命，"
                "請用繁體中文回答"
            ),
            response_modalities=["TEXT"],
            tools=[google_search_tool],
        ),
        contents=[image, "用繁體中文描述這張圖片"],
    )

    # === 回傳圖片 + 解析文字 ===
    with ApiClient(line_configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    ImageMessage(
                        original_content_url=image_url,
                        preview_image_url=image_url,
                    ),
                    TextMessage(text=response.text),
                ],
            )
        )

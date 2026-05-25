"""
LINEBOTSCU - 文字訊息處理
功能：
  - 一般文字 → Gemini 多輪對話回覆
  - "AI <描述>" → Gemini 生成圖片並回傳
"""
import uuid
from io import BytesIO

import markdown
from bs4 import BeautifulSoup
from PIL import Image

from linebot.v3.messaging import (
    ApiClient,
    ImageMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from google.genai import types

from config import base_url, line_configuration, static_tmp_path, webhook_handler
from gemini_client import client, query


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """處理使用者傳來的文字訊息。"""
    import os
    user_input = event.message.text.strip()

    # === "AI <描述>" 指令 → Gemini 生成圖片 ===
    if user_input.startswith("AI "):
        prompt = user_input[3:].strip()
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    filename = f"{uuid.uuid4().hex}.png"
                    image_path = os.path.join(static_tmp_path, filename)
                    image.save(image_path)
                    image_url = f"https://{base_url}/images/{filename}"

                    with ApiClient(line_configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[
                                    ImageMessage(
                                        original_content_url=image_url,
                                        preview_image_url=image_url,
                                    )
                                ],
                            )
                        )
        except Exception as e:
            with ApiClient(line_configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="抱歉，生成圖片時發生錯誤。")],
                    )
                )

    # === 一般文字 → Gemini 多輪對話 ===
    else:
        response_text = query(user_input)
        html_msg = markdown.markdown(response_text)
        plain_text = BeautifulSoup(html_msg, "html.parser").get_text()

        with ApiClient(line_configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=plain_text)],
                )
            )

<div align="center">
  <h1>LINEBOTSCU</h1>
  <p><b>東吳大學資料系 LINE Bot - 專屬手搖飲推薦與智慧對話助手</b></p>
</div>

---

整合 Google Gemini AI 的 LINE Bot，不僅支援自然語言的多輪文字對話，更能針對使用者提供精準的手搖飲推薦，是專屬的智慧飲料助手。

## 相關連結

- **專案介紹投影片：** [點此觀看 (Canva)](https://www.canva.com/design/DAHLaCZKTyQ/ofZ19GkU5YfMkxgtkbrDOQ/edit)
- **專案使用說明影片：** [點此觀看 (YouTube)](https://www.youtube.com/watch?v=eh7m5dLUDyE)

## 核心功能

| 功能 | 說明 | 使用方式 |
|------|------|---------|
| **AI 智慧對話** | 結合 Google Gemini AI，支援google search。 | 直接傳送任何文字訊息 |
| **手搖飲推薦** | 根據地理位置或需求推薦手搖飲，並可存入喜好資料庫。 | 傳送所在位置或對話觸發，點選推薦結果儲存 |
| **隨機推薦** | 不知道喝什麼？透過 Flex Message 隨機抽出附近推薦店家。 | 點擊「再推一次」或圖文選單按鈕 |

## 技術架構

本專案基於 Python 開發，主要依賴以下技術：
- **LINE Messaging API**: 負責收發 LINE 訊息與 Flex Message 介面呈現。
- **Google Gemini AI API**: 提供大語言模型對話與語意理解能力。
- **Flask**: 作為穩定輕量的 Webhook 伺服器框架。
- **Docker**: 容器化封裝，確保環境一致性與方便雲端部署。

## 專案結構

```text
LINEBOTSCU/
├── app.py              # Flask 主程式，處理 Webhook 與 Postback 路由
├── config.py           # 環境變數與 LINE 憑證配置
├── gemini_client.py    # 封裝 Gemini AI 互動邏輯
├── text_handler.py     # 處理文字對話與位置訊息
├── handlers/           # 處理進階功能（如隨機推薦、各種訊息事件）
├── database/           # 處理使用者狀態 (Session) 與飲品資料儲存
├── Dockerfile          # Docker 部署設定檔
└── requirements.txt    # 專案相依 Python 套件
```

## 環境變數設定

請在部署環境或本地端的 `.env` 檔案中設定以下變數：

| 變數名稱 | 說明 |
|---------|------|
| `LINE_CHANNEL_SECRET` | LINE Bot 的 Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 的 Channel Access Token |
| `GOOGLE_GEMINI_API_KEY` | Google Gemini API 金鑰 |
| `SPACE_HOST` | 部署平台 (如 Hugging Face Space) 的公開 Hostname |

## 快速啟動與部署

### 本地開發測試

1. 安裝所需套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 啟動伺服器：
   ```bash
   gunicorn -b 0.0.0.0:7860 app:app
   ```

### Docker 容器部署

本專案提供完整的 `Dockerfile`，可無縫部署至雲端平台（如 Hugging Face Spaces、Render 等）：
```bash
docker build -t linebotscu .
docker run -p 7860:7860 --env-file .env linebotscu
```

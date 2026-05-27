---
title: LINEBOTSCU
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# LINEBOTSCU — 東吳大學資料系 LINE Bot

整合 Google Gemini AI 的 LINE Bot，支援文字對話與手搖飲推薦。

## 功能

| 功能 | 使用方式 |
|------|---------|
| 文字問答 (多輪對話) | 直接傳送任何文字 |



## 環境變數

請在部署環境設定以下變數（本地開發請建立 `.env` 檔案）：

| 變數名稱 | 說明 |
|---------|------|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token |
| `GOOGLE_GEMINI_API_KEY` | Google Gemini API Key |
| `SPACE_HOST` | Hugging Face Space 的公開 hostname |

## 專案結構

```
LINEBOTSCU/
├── app.py              # Flask 主程式 + 路由
├── config.py           # LINE 憑證與共用設定
├── gemini_client.py    # Gemini AI 初始化與 query 函式
├── text_handler.py     # 文字訊息處理
├── Dockerfile          # 容器部署設定
└── requirements.txt    # Python 套件
```

## 部署

本專案使用 Docker 部署於 Hugging Face Spaces：

```bash
# 本地測試
pip install -r requirements.txt
gunicorn -b 0.0.0.0:7860 app:app
```

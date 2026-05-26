"""
LINEBOTSCU - Rich Menu 建立腳本（溫暖淡橘主題）
執行方式：python rich_menu/setup_rich_menu.py
功能：建立 2×2 四格圖文選單並設為預設
注意：此腳本只需執行一次，之後選單會持續存在。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from dotenv import load_dotenv
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# ─────────────────────────────────────────
# Rich Menu 定義（2×2，2500×1686 像素）
# ─────────────────────────────────────────
RICH_MENU_BODY = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "LINEBOTSCU 茶飲選單",
    "chatBarText": "🧋 茶飲選單",
    "areas": [
        # 左上：條件找茶
        {
            "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
            "action": {
                "type": "message",
                "text": "條件找茶",
            },
        },
        # 右上：海豹隨機推
        {
            "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
            "action": {
                "type": "message",
                "text": "海豹隨機推",
            },
        },
        # 左下：最新主打
        {
            "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "message",
                "text": "最新主打",
            },
        },
        # 右下：使用說明
        {
            "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "message",
                "text": "使用說明",
            },
        },
    ],
}


def create_rich_menu() -> str:
    """建立 Rich Menu，回傳 richMenuId。"""
    url = "https://api.line.me/v2/bot/richmenu"
    res = requests.post(url, headers=HEADERS, json=RICH_MENU_BODY)
    res.raise_for_status()
    rich_menu_id = res.json()["richMenuId"]
    print(f"✅ Rich Menu 建立成功：{rich_menu_id}")
    return rich_menu_id


def upload_rich_menu_image(rich_menu_id: str, image_path: str) -> None:
    """上傳圖文選單背景圖片。"""
    url = f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "image/png",
    }
    with open(image_path, "rb") as f:
        res = requests.post(url, headers=headers, data=f)
    res.raise_for_status()
    print(f"✅ 圖片上傳成功")


def set_default_rich_menu(rich_menu_id: str) -> None:
    """設定為預設圖文選單。"""
    url = f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}"
    res = requests.post(url, headers=HEADERS)
    res.raise_for_status()
    print(f"✅ 已設定為預設圖文選單")


def delete_all_rich_menus() -> None:
    """刪除所有現有的 Rich Menu（避免累積）。"""
    url = "https://api.line.me/v2/bot/richmenu/list"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    menus = res.json().get("richmenus", [])
    for menu in menus:
        mid = menu["richMenuId"]
        del_res = requests.delete(
            f"https://api.line.me/v2/bot/richmenu/{mid}", headers=HEADERS
        )
        print(f"🗑️  刪除舊選單：{mid}，狀態：{del_res.status_code}")


def generate_rich_menu_image() -> str:
    """
    使用 Pillow 生成仿照設計圖的 2×2 圖文選單圖片（彩色框+文字）。
    回傳：圖片檔案路徑
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("⚠️  Pillow 未安裝，跳過圖片生成，請手動上傳圖片。")
        return ""

    W, H = 2500, 1686
    COLOR_BG = "#FDFBF5"  # 米白底色
    COLOR_DIVIDER = "#9AB0C4"  # 灰藍色分隔線
    COLOR_TEXT = "#2C1B10"     # 深咖啡字體
    
    img = Image.new("RGB", (W, H), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 畫四個格子：圖示(暫代) / 標題
    cells = [
        (0,    0,    1250, 843,  "🔍", "條件找茶"),
        (1250, 0,    2500, 843,  "🎲", "海豹隨機推"),
        (0,    843,  1250, 1686, "🔥", "最新主打"),
        (1250, 843,  2500, 1686, "⭐", "使用說明"),
    ]

    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 80)
        font_icon  = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 350)
    except Exception:
        font_title = ImageFont.load_default()
        font_icon  = font_title

    for (x1, y1, x2, y2, icon, title) in cells:
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # icon（中央偏上）
        draw.text((cx, cy - 100), icon, fill="#555555", font=font_icon, anchor="mm")
        # 標題（中央偏下）
        draw.text((cx, cy + 220), title, fill=COLOR_TEXT, font=font_title, anchor="mm")

    # 分隔線 (十字)
    draw.line([(1250, 0), (1250, H)], fill=COLOR_DIVIDER, width=12)
    draw.line([(0, 843), (W, 843)], fill=COLOR_DIVIDER, width=12)
    
    # 畫四周的邊框
    draw.rectangle([0, 0, W, H], outline=COLOR_DIVIDER, width=12)

    # 儲存
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "rich_menu.png"
    )
    img.save(out_path)
    print(f"✅ 圖片生成完成：{out_path}")
    return out_path


if __name__ == "__main__":
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定，請先設定環境變數。")
        sys.exit(1)

    print("🗑️  清除舊 Rich Menu...")
    delete_all_rich_menus()

    print("🎨 生成圖文選單圖片...")
    image_path = generate_rich_menu_image()

    print("📋 建立 Rich Menu...")
    rich_menu_id = create_rich_menu()

    if image_path and os.path.exists(image_path):
        print("🖼️  上傳圖片...")
        upload_rich_menu_image(rich_menu_id, image_path)
    else:
        print("⚠️  跳過圖片上傳（請手動上傳 rich_menu.png）")

    print("🔗 設定為預設選單...")
    set_default_rich_menu(rich_menu_id)

    print(f"\n🎉 完成！Rich Menu ID：{rich_menu_id}")

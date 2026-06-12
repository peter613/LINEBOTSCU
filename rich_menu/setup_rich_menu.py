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
    "name": "功能選單",
    "chatBarText": "功能選單",
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
        "Content-Type": "image/jpeg",
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
    使用 Pillow 將四張圖片拼接成 2×2 圖文選單圖片 (2500x1686)。
    回傳：圖片檔案路徑
    """
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow 未安裝，跳過圖片生成，請手動上傳圖片。")
        return ""

    W, H = 2500, 1686
    img = Image.new("RGB", (W, H), color="#FFFFFF")

    # 圖片對應與路徑 (請確認路徑與名稱)
    brain_dir = r"C:\Users\Lynn610\.gemini\antigravity\brain\2db2abe5-5291-40e3-9e81-e74daf848fbf"
    
    # 根據順序推測的圖片對應：
    # 條件找茶 (左上)
    img_tl = os.path.join(brain_dir, "media__1780388295684.jpg")
    # 海豹隨機推 (右上)
    img_tr = os.path.join(brain_dir, "media__1780388295664.jpg")
    # 最新主打 (左下)
    img_bl = os.path.join(brain_dir, "media__1780388295624.jpg")
    # 使用說明 (右下)
    img_br = os.path.join(brain_dir, "media__1780388295643.jpg")

    cells = [
        (img_tl, 0, 0),
        (img_tr, 1250, 0),
        (img_bl, 0, 843),
        (img_br, 1250, 843)
    ]

    for path, x, y in cells:
        if os.path.exists(path):
            try:
                cell_img = Image.open(path).convert("RGB")
                cell_img = cell_img.resize((1250, 843), Image.Resampling.LANCZOS)
                img.paste(cell_img, (x, y))
            except Exception as e:
                print(f"處理圖片 {path} 失敗: {e}")
        else:
            print(f"找不到圖片: {path}")

    # 儲存為 JPEG 以縮小檔案大小 (< 1MB)
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "rich_menu.jpg"
    )
    img.save(out_path, format="JPEG", quality=80)
    print(f"✅ 圖片拼接完成：{out_path}")
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

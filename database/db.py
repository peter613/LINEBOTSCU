"""
LINEBOTSCU - Supabase 資料庫操作封裝（新版）
Schema：
  drinks        — AI 推薦 + 使用者選擇累積（含 select_count 熱門度）
  user_sessions — 使用者對話狀態機
"""
import logging
from datetime import datetime, timezone

from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

# === 單例 Supabase 客戶端 ===
_supabase: Client | None = None


def get_client() -> Client:
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL 或 SUPABASE_KEY 環境變數未設定")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


# ─────────────────────────────────────────
# 飲品 (drinks)
# ─────────────────────────────────────────

def upsert_drink(
    shop_name: str,
    drink_name: str,
    category: str,
    sweetness: str,
    tags: list[str],
    area: str,
) -> dict:
    """
    新增或更新飲品紀錄。
    - 若同店同飲品已存在 → select_count +1
    - 若不存在 → 新增（select_count = 1）
    回傳最終的 drinks 資料列。
    """
    sb = get_client()
    now = datetime.now(timezone.utc).isoformat()

    res = (
        sb.table("drinks")
        .select("id, select_count")
        .eq("shop_name", shop_name)
        .eq("drink_name", drink_name)
        .execute()
    )

    if res.data:
        row_id = res.data[0]["id"]
        new_count = res.data[0]["select_count"] + 1
        sb.table("drinks").update({
            "select_count": new_count,
            "updated_at": now,
        }).eq("id", row_id).execute()
        logger.info("Updated drink '%s' @ '%s', count=%d", drink_name, shop_name, new_count)
    else:
        sb.table("drinks").insert({
            "shop_name":    shop_name,
            "drink_name":   drink_name,
            "category":     category,
            "sweetness":    sweetness,
            "tags":         tags,
            "area":         area,
            "select_count": 1,
            "created_at":   now,
            "updated_at":   now,
        }).execute()
        logger.info("Inserted new drink '%s' @ '%s'", drink_name, shop_name)

    return {"shop_name": shop_name, "drink_name": drink_name}


def get_popular_drinks(limit: int = 20) -> list[dict]:
    """依 select_count 降序取得熱門飲品。"""
    sb = get_client()
    res = (
        sb.table("drinks")
        .select("*")
        .order("select_count", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def get_popular_drinks_by_category(category: str, limit: int = 15) -> list[dict]:
    """依類別篩選後，依 select_count 降序取得飲品。"""
    sb = get_client()
    res = (
        sb.table("drinks")
        .select("*")
        .eq("category", category)
        .order("select_count", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def is_drinks_empty() -> bool:
    """檢查資料庫是否尚無資料。"""
    sb = get_client()
    res = sb.table("drinks").select("id").limit(1).execute()
    return len(res.data) == 0


# ─────────────────────────────────────────
# 使用者對話狀態 (user_sessions)
# ─────────────────────────────────────────

def get_user_session(user_id: str) -> dict:
    """取得使用者對話狀態，不存在則初始化。"""
    sb = get_client()
    res = sb.table("user_sessions").select("*").eq("user_id", user_id).execute()
    if res.data:
        row = res.data[0]
        row["context"] = row.get("context") or {}
        return row
    default = {"user_id": user_id, "state": "IDLE", "context": {}}
    sb.table("user_sessions").insert(default).execute()
    return default


def set_user_session(user_id: str, state: str, context: dict) -> None:
    """更新使用者狀態與上下文。"""
    sb = get_client()
    sb.table("user_sessions").upsert({
        "user_id":    user_id,
        "state":      state,
        "context":    context,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def reset_user_session(user_id: str) -> None:
    """重置狀態至 IDLE。"""
    set_user_session(user_id, "IDLE", {})

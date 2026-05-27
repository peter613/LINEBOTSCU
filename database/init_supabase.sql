-- ============================================
-- LINEBOTSCU 茶飲推薦系統 - Supabase 資料表初始化（新版）
-- 架構：精簡兩張表（drinks + user_sessions）
-- 在 Supabase Dashboard > SQL Editor 執行此腳本
-- ============================================

-- 先清除舊表（若存在）
DROP TABLE IF EXISTS drinks CASCADE;
DROP TABLE IF EXISTS shops CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- ── 1. 飲品紀錄表（由使用者選擇累積）──
CREATE TABLE drinks (
    id           SERIAL PRIMARY KEY,
    shop_name    TEXT NOT NULL,          -- 店家名稱（AI 提供）
    drink_name   TEXT NOT NULL,          -- 飲品名稱（AI 提供）
    category     TEXT,                   -- 果茶 / 奶茶 / 鮮奶茶 / 茶類 / 特調
    tags         TEXT[],                 -- 標籤陣列
    area         TEXT,                   -- 所在區域（如：台北市中山區）
    select_count INTEGER DEFAULT 1,      -- 被使用者選擇次數（熱門度）
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. 使用者對話狀態表 ──
CREATE TABLE user_sessions (
    user_id    TEXT PRIMARY KEY,
    state      TEXT DEFAULT 'IDLE',
    context    JSONB DEFAULT '{}',       -- 含 feature / location / pending_drinks
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── 索引 ──
CREATE INDEX IF NOT EXISTS idx_drinks_select_count ON drinks(select_count DESC);
CREATE INDEX IF NOT EXISTS idx_drinks_category     ON drinks(category);
CREATE INDEX IF NOT EXISTS idx_drinks_shop_drink   ON drinks(shop_name, drink_name);

-- ── Row Level Security ──
ALTER TABLE drinks        ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "drinks_all"   ON drinks        FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "sessions_all" ON user_sessions FOR ALL TO anon USING (true) WITH CHECK (true);

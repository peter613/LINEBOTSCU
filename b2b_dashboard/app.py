import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Set wide layout
st.set_page_config(page_title="LINEBOT B2B Dashboard", layout="wide")

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Missing Supabase credentials in .env file.")
    st.stop()

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

@st.cache_data(ttl=300)
def fetch_data():
    """Fetch drinks data from Supabase"""
    response = supabase.table("drinks").select("*").execute()
    data = response.data
    return pd.DataFrame(data)

st.title("🥤 飲料選擇 B2B 數據分析平台")

# Fetch and load data
with st.spinner("載入資料中..."):
    df = fetch_data()

if df.empty:
    st.warning("資料庫中目前沒有任何資料。")
    st.stop()

# --- 資料預處理 ---
# 解析 shop_name 的品牌
def extract_brand(name: str):
    import re
    if not name: return "未知店家"
    
    # 移除括號內的文字
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'（.*?）', '', name)
    
    name_upper = name.upper()
    
    # 常見品牌正規化對照表 (只要包含該關鍵字，就統一為該品牌名)
    brand_mapping = {
        "五桐號": ["五桐", "WOOTEA"],
        "50嵐": ["50嵐", "五十嵐"],
        "可不可熟成紅茶": ["可不可"],
        "麻古茶坊": ["麻古"],
        "清心福全": ["清心"],
        "茶湯會": ["茶湯會"],
        "迷客夏": ["迷客夏"],
        "大苑子": ["大苑子"],
        "CoCo都可": ["COCO", "都可"],
        "COMEBUY": ["COMEBUY"],
        "先喝道": ["先喝道"],
        "功夫茶": ["功夫茶"],
        "侍茶匠": ["侍茶匠"],
        "木子甜飲": ["木子甜飲"],
        "初韻": ["初韻"],
        "珍煮丹": ["珍煮丹"],
        "一芳": ["一芳"],
    }
    
    for canonical_name, keywords in brand_mapping.items():
        for kw in keywords:
            if kw.upper() in name_upper:
                return canonical_name
                
    # 若不在對照表中，把常見分隔符號轉為空白後取第一段
    name = name.replace('-', ' ').replace('_', ' ').replace('－', ' ')
    parts = name.split()
    return parts[0] if parts else name

df['brand'] = df['shop_name'].apply(extract_brand)

# 展平 tags
all_tags = []
for tags in df['tags']:
    if isinstance(tags, list):
        all_tags.extend(tags)
    elif isinstance(tags, str):
        # 處理如果存成字串的情況 (e.g., '["清爽", "解渴"]')
        import ast
        try:
            parsed = ast.literal_eval(tags)
            if isinstance(parsed, list):
                all_tags.extend(parsed)
        except:
            all_tags.append(tags)

tags_df = pd.DataFrame(all_tags, columns=['tag'])
tag_counts = tags_df['tag'].value_counts().reset_index()
tag_counts.columns = ['tag', 'count']

# --- Dashboard 佈局 ---
# 1. 樣本總數
st.metric(label="📊 總樣本數", value=f"{len(df)} 筆")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("☁️ 飲品名稱文字雲")
    # Combine all drink names
    text = " ".join(df['drink_name'].dropna())
    
    # Check for Chinese font for Windows
    font_path = "C:/Windows/Fonts/msjh.ttc" # 微軟正黑體
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/simhei.ttf"
    
    try:
        wordcloud = WordCloud(
            font_path=font_path if os.path.exists(font_path) else None,
            width=800, height=600,
            background_color='white',
            colormap='viridis'
        ).generate(text)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"文字雲產生失敗，可能是因為缺少中文字型：{e}")

with col2:
    st.subheader("🌹 標籤熱門度 (玫瑰圖)")
    if not tag_counts.empty:
        # 只取前 15 名的標籤來畫玫瑰圖
        top_tags = tag_counts.head(15)
        fig_rose = px.bar_polar(
            top_tags, r="count", theta="tag",
            color="tag", template="plotly_white",
            color_discrete_sequence=px.colors.sequential.Plasma_r
        )
        fig_rose.update_layout(polar=dict(radialaxis=dict(visible=False)))
        st.plotly_chart(fig_rose, use_container_width=True)
    else:
        st.info("目前沒有足夠的標籤資料。")

st.markdown("---")

st.subheader("📈 飲料品牌受歡迎程度 (柱狀圖)")
# 使用 select_count 來計算總點擊次數，而不只是不重複的飲料數量
if 'select_count' in df.columns:
    df['select_count'] = df['select_count'].fillna(1).astype(int)
    brand_counts = df.groupby('brand')['select_count'].sum().reset_index()
else:
    brand_counts = df['brand'].value_counts().reset_index()
    brand_counts.columns = ['brand', 'select_count']

brand_counts = brand_counts.sort_values(by='select_count', ascending=False).reset_index(drop=True)
brand_counts.columns = ['品牌名稱', '總被選擇次數']

# 判斷是否要歸類為「其他」：次數 <= 2，或是排名在第 20 名之後
is_other = (brand_counts['總被選擇次數'] <= 2) | (brand_counts.index >= 20)
others_count = brand_counts[is_other]['總被選擇次數'].sum()

plot_df = brand_counts[~is_other].copy()

if others_count > 0:
    others_row = pd.DataFrame([{'品牌名稱': '其他', '總被選擇次數': others_count}])
    plot_df = pd.concat([plot_df, others_row], ignore_index=True)

fig_bar = px.bar(
    plot_df, x='品牌名稱', y='總被選擇次數',
    color='總被選擇次數', color_continuous_scale='Blues',
    text_auto=True
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.subheader("📋 原始資料預覽")
st.dataframe(df[['shop_name', 'drink_name', 'category', 'tags', 'area', 'select_count', 'updated_at']].head(50))

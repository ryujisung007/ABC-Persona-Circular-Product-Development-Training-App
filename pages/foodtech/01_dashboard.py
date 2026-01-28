# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd
import openai

# -------------------------
# OpenAI Key (Cloud/Local 안전 대응)
# -------------------------
def get_openai_key():
    if "openai_api_key" in st.secrets:
        return st.secrets["openai_api_key"]
    else:
        st.warning("⚠️ OpenAI API Key가 설정되지 않아 AI 기능은 비활성화됩니다.")
        return None

openai.api_key = get_openai_key()

# -------------------------
# Data Load
# -------------------------
@st.cache_data
def load_data():
    return pd.read_csv("data/foodtech_company.csv")

# -------------------------
# AI 설명 생성
# -------------------------
def generate_ai_description(tech_name):
    if not openai.api_key:
        return "❌ OpenAI API Key가 없어 AI 설명을 생성할 수 없습니다."

    prompt = f"""
    '{tech_name}' 푸드테크 기술에 대해 아래를 정리해줘.
    1. 기술 정의
    2. 적용 가능한 식품 카테고리
    3. R&D 활용 포인트
    한국어, 항목별 1~2문장
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ AI 호출 오류: {e}"

# -------------------------
# MAIN (필수)
# -------------------------
def main():
    st.set_page_config(page_title="🥣 FoodTech 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    df = load_data()

    # -------------------------
    # Sidebar Filter
    # -------------------------
    st.sidebar.header("📂 필터")

    mid_list = sorted(df["중분류"].dropna().unique())
    selected_mid = st.sidebar.selectbox("중분류", ["전체"] + mid_list, key="ft_mid")

    if selected_mid != "전체":
        df = df[df["중분류"] == selected_mid]

    sub_list = sorted(df["소분류"].dropna().unique())
    selected_sub = st.sidebar.selectbox("소분류", ["전체"] + sub_list, key="ft_sub")

    if selected_sub != "전체":
        df = df[df["소분류"] == selected_sub]

    st.subheader(f"🔎 필터링 결과: {len(df)}개 기업")

    # -------------------------
    # Company List
    # -------------------------
    for idx, row in df.iterrows():
        with st.expander(f"{row['기업이름']} | {row['중분류']} > {row['소분류']}"):
            st.markdown(f"**기업정보**: {row['기업정보']}")
            st.markdown(f"**대표제품**: {row.get('대표제품','')}")

            if st.button("🧠 대표기술 분석", key=f"tech_{idx}"):
                st.session_state["selected_tech"] = row["대표기술"]
                st.session_state["related_product"] = row.get("대표제품","")

    # -------------------------
    # AI Result Area
    # -------------------------
    if "selected_tech" in st.session_state:
        st.divider()
        tech = st.session_state["selected_tech"]
        product = st.session_state.get("related_product","")

        col1, col2 = st.columns([1,1])

        with col1:
            st.markdown(f"## 🤖 기술 개요: `{tech}`")
            with st.spinner("AI 분석 중..."):
                ai_text = generate_ai_description(tech)
            st.markdown(ai_text)

        with col2:
            st.markdown("## 🖼️ 관련 이미지")
            query = f"{product} {tech}" if product else tech
            st.image(
                f"https://source.unsplash.com/featured/?{query}",
                use_column_width=True
            )

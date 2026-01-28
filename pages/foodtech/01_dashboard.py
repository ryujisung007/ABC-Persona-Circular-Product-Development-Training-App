# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import openai

# ---------------------- 설정 ----------------------
st.set_page_config(
    page_title="푸드테크 기업 대시보드",
    page_icon="🌟",
    layout="wide"
)

st.title("푸드테크 기업 분석 대시보드 🌟")
st.markdown("""
이 페이지는 업로드된 `foodtech_company.csv` 파일을 기반으로 **푸드테크 기업 정보**를 시각화합니다.
중분류와 소분류로 기업을 필터링할 수 있으며, AI 기반 추천 기능도 제공합니다.
""")

# ---------------------- 데이터 로드 ----------------------
@st.cache_data

def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

df = load_data()

# ---------------------- 필터 영역 ----------------------
st.sidebar.header("🔍 필터 설정")
category_list = df["중분류"].dropna().unique().tolist()
subcategory_list = df["소분류"].dropna().unique().tolist()

selected_category = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(category_list))
filtered_df = df.copy()
if selected_category != "전체":
    filtered_df = filtered_df[filtered_df["중분류"] == selected_category]

selected_subcategory = st.sidebar.selectbox(
    "소분류 선택", ["전체"] + sorted(filtered_df["소분류"].dropna().unique().tolist())
)
if selected_subcategory != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == selected_subcategory]

st.subheader(f"📊 총 {len(filtered_df)}개 기업이 필터링되었습니다")
st.dataframe(filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술"]], use_container_width=True)

# ---------------------- AI 기반 기술 추천 ----------------------
st.markdown("---")
st.markdown("### 🤖 AI 기반 기업/기술 추천")
user_query = st.text_input("관심 있는 키워드를 입력하세요 (예: 고단백 스낵, 정밀발효 등)")

if user_query:
    with st.spinner("AI 추천 생성 중..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 푸드테크 전문 추천 시스템입니다."},
                {"role": "user", "content": f"'{user_query}' 키워드에 맞는 기업 또는 기술을 추천해줘. 중분류/소분류 기준으로 설명해줘."}
            ]
        )
        ai_recommendation = response["choices"][0]["message"]["content"]
        st.success("✅ AI 추천 결과:")
        st.markdown(ai_recommendation)

# ---------------------- 다운로드 버튼 ----------------------
st.markdown("---")
st.markdown("### 📥 필터링 결과 다운로드")

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df_to_csv(filtered_df)
st.download_button(
    label="CSV로 다운로드",
    data=csv,
    file_name="filtered_foodtech_companies.csv",
    mime="text/csv"
)

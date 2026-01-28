# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd

# 데이터 로딩
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")  # 기존 파일명 유지
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 대시보드",
    page_icon="🌱",
    layout="wide"
)

st.title(":green[푸드테크 기업 대시보드] 🔍")
st.markdown("""
이 페이지는 기존 `foodtech_company.csv`를 기반으로 **중분류 – 소분류 필터**를 적용하여 관련 기업을 테이블로 탐색할 수 있도록 구성되어 있습니다.
""")

# 데이터 로드
df = load_data()

# 필터: 중분류 선택
mid_categories = sorted(df["중분류"].dropna().unique().tolist())
selected_mid = st.selectbox("1️⃣ 중분류 선택", ["전체"] + mid_categories)

# 소분류 필터링
if selected_mid != "전체":
    sub_df = df[df["중분류"] == selected_mid]
    sub_categories = sorted(sub_df["소분류"].dropna().unique().tolist())
else:
    sub_df = df
    sub_categories = sorted(df["소분류"].dropna().unique().tolist())

selected_sub = st.selectbox("2️⃣ 소분류 선택", ["전체"] + sub_categories)

# 최종 필터링
filtered_df = sub_df.copy()
if selected_sub != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

st.markdown(f"### ✅ 필터링된 기업 수: {len(filtered_df)}개")

# 결과 테이블 출력
st.dataframe(
    filtered_df[["번", "기업이름", "중분류", "소분류", "기업정보", "대표기술"]].reset_index(drop=True),
    use_container_width=True
)

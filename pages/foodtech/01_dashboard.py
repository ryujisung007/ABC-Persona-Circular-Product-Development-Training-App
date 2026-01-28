# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 대시보드",
    page_icon="🌱",
    layout="wide"
)

# 데이터 로드 함수
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")  # 경로 주의!
    df = df.drop(columns=["순번"], errors="ignore")
    return df

# 데이터 로드
df = load_data()

# 중분류, 소분류 필터링
st.sidebar.header("🔍 필터")
category = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(df["중분류"].dropna().unique().tolist()))
sub_category = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(df["소분류"].dropna().unique().tolist()))

filtered_df = df.copy()
if category != "전체":
    filtered_df = filtered_df[filtered_df["중분류"] == category]
if sub_category != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == sub_category]

# 결과 출력
st.title("🥗 푸드테크 기업 리스트")
st.subheader(f"🔎 총 {len(filtered_df)}개 기업이 검색되었습니다.")
st.dataframe(filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "대표제품", "사이트 주소"]])

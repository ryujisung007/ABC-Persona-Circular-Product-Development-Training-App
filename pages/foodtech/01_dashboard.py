# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd

# 데이터 로딩 함수
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

# 메인 실행 함수
def main():
    st.header(":green[푸드테크 기업 분석 대시보드] 🏢")
    st.markdown("""
    이 페이지는 업로드된 `foodtech_company.csv` 파일을 기반으로 **푸드테크 기업 정보**를 시각화합니다.  
    좌측에서 카테고리 또는 대표기술을 선택하면 관련 기업 리스트가 아래에 출력됩니다.
    """)

    # 데이터 로드
    df = load_data()

    # 사이드바 필터
    st.sidebar.header("필터 설정")
    categories = df["카테고리 구분"].dropna().unique().tolist()
    technologies = df["대표기술"].dropna().unique().tolist()

    selected_category = st.sidebar.selectbox(
        "카테고리 선택", ["전체"] + sorted(categories), key="category_selectbox"
    )
    selected_tech = st.sidebar.selectbox(
        "대표기술 선택", ["전체"] + sorted(technologies), key="tech_selectbox"
    )

    # 필터 적용
    filtered_df = df.copy()
    if selected_category != "전체":
        filtered_df = filtered_df[filtered_df["카테고리 구분"] == selected_category]
    if selected_tech != "전체":
        filtered_df = filtered_df[filtered_df["대표기술"] == selected_tech]

    st.subheader(f"🔍 필터링된 기업 수: {len(filtered_df)}개")

    # 결과 출력
    for idx, row in filtered_df.iterrows():
        with st.expander(f"{row['기업이름']} ({row['카테고리 구분']})"):
            st.markdown(f"**기업정보:** {row['기업정보']}")
            st.markdown(f"**대표기술:** {row['대표기술']}")
            st.markdown(f"**대표제품:** {row['대표제품']}")
            st.markdown(f"[🌐 공식 웹사이트]({row['사이트 주소']})")

# app.py에서 직접 실행하지 않도록 주의: main() 함수만 외부에서 호출

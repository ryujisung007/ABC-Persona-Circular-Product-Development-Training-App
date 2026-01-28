import streamlit as st
import pandas as pd

# 페이지 설정
def main():
    st.set_page_config(
        page_title="푸드테크 기업 대시보드",
        page_icon="🌟",
        layout="wide"
    )
    st.title(":green[푸드테크 기업 리스트(2026)] 🏢")

    # 데이터 로드
    @st.cache_data
    def load_data():
        df = pd.read_csv("data/foodtech_company.csv", encoding="utf-8-sig")
        df.columns = [col.strip() for col in df.columns]  # 공백 제거
        return df

    df = load_data()

    # 필터: 중분류 → 소분류
    st.sidebar.header("📁 "살펴보기")
    mid_categories = df["중분류"].dropna().unique().tolist()
    selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

    if selected_mid != "전체":
        df = df[df["중분류"] == selected_mid]

    sub_categories = df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

    if selected_sub != "전체":
        df = df[df["소분류"] == selected_sub]

    st.subheader(f"🔍 필터링된 기업 수: {len(df)}개")

    # 기업 정보 테이블
    st.dataframe(
        df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "대표제품"]],
        use_container_width=True
    )

# Streamlit에서 실행될 수 있도록 main 함수 호출
if __name__ == "__main__":
    main()

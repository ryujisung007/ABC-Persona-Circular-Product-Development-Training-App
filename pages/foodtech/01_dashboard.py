import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

def main():
    st.set_page_config(
        page_title="푸드테크 기업 대시보드",
        page_icon="🌟",
        layout="wide"
    )

    st.title(":green[푸드테크 기업 분석 대시보드] 🏢")
    st.markdown("""
    이 페이지는 `foodtech_company.csv` 파일을 기반으로 **푸드테크 기업 정보**를 시각화합니다.  
    `중분류 → 소분류`를 선택하면 관련 기업 리스트가 아래에 출력됩니다.
    """)

    # 데이터 불러오기
    df = load_data()

    # 필터 설정
    st.sidebar.header("필터")
    main_categories = df["중분류"].dropna().unique().tolist()
    selected_main = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(main_categories))

    filtered_df = df.copy()
    if selected_main != "전체":
        filtered_df = filtered_df[filtered_df["중분류"] == selected_main]

    sub_categories = filtered_df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

    if selected_sub != "전체":
        filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

    st.subheader(f"🔍 필터링된 기업 수: {len(filtered_df)}개")

    st.dataframe(
        filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "대표제품"]],
        use_container_width=True
    )

# Streamlit 실행 시 main() 호출되도록 설정
if __name__ == "__main__":
    main()

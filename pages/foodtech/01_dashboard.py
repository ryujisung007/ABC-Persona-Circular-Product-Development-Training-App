import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 검색",
    page_icon="🍽️",
    layout="wide"
)

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

# 데이터 로드
df = load_data()

# 필수 컬럼 확인
required_cols = ["중분류", "소분류", "기업이름", "기업정보", "대표기술"]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"❌ CSV 파일에 다음 필수 열이 없습니다: {missing_cols}")
    st.stop()

# 제목 및 설명
st.title(":green[푸드테크 기업 검색 대시보드] 🍽️")
st.markdown("""
중분류와 소분류를 선택하면 관련 푸드테크 기업 정보를 아래에서 확인할 수 있습니다.
""")

# 중분류 선택
mid_categories = df["중분류"].dropna().unique().tolist()
selected_mid = st.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

# 소분류 선택
if selected_mid != "전체":
    filtered_mid = df[df["중분류"] == selected_mid]
    sub_categories = filtered_mid["소분류"].dropna().unique().tolist()
else:
    sub_categories = df["소분류"].dropna().unique().tolist()

selected_sub = st.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

# 필터 적용
filtered_df = df.copy()
if selected_mid != "전체":
    filtered_df = filtered_df[filtered_df["중분류"] == selected_mid]
if selected_sub != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

st.subheader(f"🔍 검색된 기업 수: {len(filtered_df)}개")

# 결과 테이블 출력
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술"]],
        use_container_width=True
    )
else:
    st.warning("⚠️ 조건에 맞는 기업이 없습니다.")

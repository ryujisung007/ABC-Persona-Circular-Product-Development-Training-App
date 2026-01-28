import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 대시보드",
    page_icon="🌟",
    layout="wide"
)

st.title(":green[푸드테크 기업 분석 대시보드] 🏢")
st.markdown("""
이 페이지는 `foodtech_company.csv` 파일을 기반으로 **푸드테크 기업 정보**를 필터링 및 시각화합니다.  
`중분류` → `소분류`를 선택하면 관련된 기업 리스트가 테이블 형태로 아래에 출력됩니다.
""")

# ✅ 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        # 탭 구분자 기반 CSV 처리
        df = pd.read_csv("data/foodtech_company.csv", sep="\t", encoding="utf-8")
    except:
        # 다른 인코딩 시도 (Windows 저장된 경우 등)
        df = pd.read_csv("data/foodtech_company.csv", sep="\t", encoding="utf-16")
    return df

# 데이터 불러오기
df = load_data()

# 열 이름 확인 (디버깅용)
# st.write("열 이름:", df.columns.tolist())

# 사이드바 필터
st.sidebar.header("🔎 필터 조건")

# 중분류 및 소분류 드롭다운
mid_categories = df["중분류"].dropna().unique().tolist()
selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

# 소분류 목록 필터링
if selected_mid != "전체":
    sub_df = df[df["중분류"] == selected_mid]
else:
    sub_df = df.copy()

sub_categories = sub_df["소분류"].dropna().unique().tolist()
selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

# 필터 적용
filtered_df = sub_df.copy()
if selected_sub != "전체":
    filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

# 출력 결과 요약
st.subheader(f"📌 필터링된 기업 수: {len(filtered_df)}개")
st.dataframe(
    filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "대표제품"]],
    use_container_width=True,
    hide_index=True
)

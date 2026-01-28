# pages/foodtech/01_dashboard.py (v3.0)
import streamlit as st
import pandas as pd
from openai import OpenAI

# ✅ secrets에서 OpenAI 키 가져오기
client = OpenAI(api_key=st.secrets["openai_api_key"])

@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df.columns = df.columns.str.strip()  # 공백 제거
    return df

# ✅ AI 기술 설명 함수
def generate_tech_summary(tech):
    prompt = f"""
    '{tech}'라는 푸드테크 기술에 대해 다음을 한국어로 요약해줘:
    1. 기술 정의
    2. 적용 가능한 식품 카테고리
    3. R&D 개발 포인트
    4. 최신 관련 기술 동향
    5. 적용 가능한 식품 제품 아이디어
    각 항목당 1~2문장으로 요약해줘.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ 오류 발생: {e}"

# ✅ 본 앱의 main 함수
def main():
    st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    # 데이터 로드
    df = load_data()

    # 필터 영역
    st.sidebar.header("📂 필터")
    mid_options = df["중분류"].dropna().unique().tolist()
    selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_options))

    filtered_df = df.copy()
    if selected_mid != "전체":
        filtered_df = filtered_df[filtered_df["중분류"] == selected_mid]

    sub_options = filtered_df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_options))

    if selected_sub != "전체":
        filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

    st.subheader(f"🔍 검색된 기업 수: {len(filtered_df)}개")

    # ✅ 검색 결과 테이블 출력
    display_df = filtered_df[[
        "기업이름", "중분류", "소분류", "기업정보", "대표기술", "사이트주소"
    ]].reset_index(drop=True)

    selected_row = st.data_editor(
        display_df,
        column_config={
            "대표기술": st.column_config.TextColumn("대표기술 (클릭하여 복사 후 아래 입력)", width="medium")
        },
        use_container_width=True,
        hide_index=True,
        disabled=["기업이름", "중분류", "소분류", "기업정보", "사이트주소"]
    )

    # ✅ 대표기술 입력
    selected_tech = st.text_input("🔎 기술 요약을 보고 싶은 대표기술명을 여기에 붙여넣으세요:")

    if selected_tech:
        st.divider()
        st.markdown(f"## 🤖 `{selected_tech}` 기술 개요 (AI 요약)")
        with st.spinner("AI가 기술 요약을 작성 중입니다..."):
            summary = generate_tech_summary(selected_tech)
        st.markdown(summary)

        # 이미지 출력
        st.markdown("### 🖼️ 관련 제품 이미지")
        st.image(
            f"https://source.unsplash.com/featured/?{selected_tech.replace(' ', '+')}",
            caption=f"{selected_tech} 관련 이미지",
            use_column_width=True,
        )

# ✅ 앱 실행
if __name__ == "__main__":
    main()

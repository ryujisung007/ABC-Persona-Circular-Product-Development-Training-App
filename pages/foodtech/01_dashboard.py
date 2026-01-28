# pages/foodtech/01_dashboard.py (리팩토링 완료 버전)

import streamlit as st
import pandas as pd
import openai

def main():
    # ✅ OpenAI 키 설정
    openai.api_key = st.secrets["openai_api_key"]

    # ✅ 데이터 로드 함수
    @st.cache_data
    def load_data():
        df = pd.read_csv("data/foodtech_company.csv")
        df.columns = df.columns.str.strip()  # 공백 제거
        return df

    # ✅ AI 기술 설명 생성 함수
    def generate_tech_summary(tech):
        prompt = f"""
        '{tech}' 라는 푸드테크 기술에 대해 다음을 한국어로 요약해줘:
        1. 기술 정의
        2. 적용 가능한 식품 카테고리
        3. R&D 개발 포인트
        4. 최신 관련 기술 동향
        5. 적용 가능한 식품 제품 아이디어
        각 항목당 1~2문장으로 요약해줘.
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ 오류 발생: {e}"

    # ✅ Streamlit 페이지 설정
    st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    # ✅ 데이터 불러오기
    df = load_data()

    # ✅ 필터 영역
    st.sidebar.header("📂 필터")

    # 중분류 필터
    mid_options = df["중분류"].dropna().unique().tolist()
    selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_options))

    filtered_df = df.copy()
    if selected_mid != "전체":
        filtered_df = filtered_df[filtered_df["중분류"] == selected_mid]

    # 소분류 필터
    sub_options = filtered_df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_options))

    if selected_sub != "전체":
        filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

    st.subheader(f"🔎 검색 결과 기업 수: {len(filtered_df)}개")

    # ✅ 검색 결과 테이블
    for idx, row in filtered_df.iterrows():
        with st.expander(f"{row['기업이름']} | {row['중분류']} > {row['소분류']}"):
            st.markdown(f"**기업 정보:** {row['기업정보']}")
            col1, col2 = st.columns([0.2, 0.8])
            if col1.button("👁️ 대표기술 보기", key=f"view_{idx}"):
                st.session_state["selected_tech"] = row["대표기술"]
                st.session_state["selected_company"] = row["기업이름"]
            col2.markdown(f"**대표기술:** {row['대표기술']}")

    # ✅ AI 기술 설명 표시
    selected_tech = st.session_state.get("selected_tech", None)
    if selected_tech:
        st.divider()
        st.markdown(f"## 🤖 `{selected_tech}` 기술 개요 (GPT 생성)")
        with st.spinner("AI가 기술 개요를 작성 중입니다..."):
            ai_text = generate_tech_summary(selected_tech)
        st.markdown(ai_text)

        # 이미지 출력
        st.markdown("---")
        st.markdown("### 🖼️ 관련 제품 이미지")
        query = f"{selected_tech}".replace(" ", "+")
        st.image(
            f"https://source.unsplash.com/featured/?{query}",
            caption=f"{selected_tech} 관련 이미지",
            use_column_width=True,
        )

# ✅ Streamlit Cloud에서 import될 때도 실행되도록
if __name__ == "__main__":
    main()

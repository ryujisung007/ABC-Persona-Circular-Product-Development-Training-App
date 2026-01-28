# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd
import openai
import urllib.parse
from googletrans import Translator

# ✅ main 함수 시작
def main():
    # ✅ OpenAI API 키 설정
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

    # ✅ 번역 함수
    def translate_kor_to_eng(text):
        try:
            translator = Translator()
            result = translator.translate(text, src='ko', dest='en')
            return result.text
        except Exception as e:
            return f"Translation error: {e}"

    # ✅ 페이지 설정
    st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    # ✅ 데이터 불러오기
    df = load_data()

    # ✅ 필터 영역
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

    st.subheader(f"🔎 검색 결과 기업 수: {len(filtered_df)}개")

    # ✅ 결과 테이블
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술"]].reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.warning("검색 결과가 없습니다.")

    # ✅ 선택된 대표기술 상세 정보 표시
    selected_tech = st.selectbox(
        "⬇️ 기술 설명을 보고 싶은 대표기술을 선택하세요:",
        filtered_df["대표기술"].dropna().unique().tolist() if not filtered_df.empty else []
    )

    if selected_tech:
        st.markdown(f"## 🤖 `{selected_tech}` 기술 개요 (GPT 생성)")
        with st.spinner("AI가 기술 개요를 작성 중입니다..."):
            ai_text = generate_tech_summary(selected_tech)
        st.markdown(ai_text)

        # ✅ 이미지 (영문 번역 후 검색)
        st.markdown("---")
        st.markdown("### 🖼️ 관련 제품 이미지")
        eng_query = translate_kor_to_eng(selected_tech)
        encoded_query = urllib.parse.quote(eng_query)
        st.image(
            f"https://source.unsplash.com/featured/?{encoded_query}",
            caption=f"{selected_tech} 관련 이미지",
            use_column_width=True,
        )

# ✅ 직접 실행이 아닌 모듈 실행 시에만 main 실행
if __name__ == "__main__":
    main()

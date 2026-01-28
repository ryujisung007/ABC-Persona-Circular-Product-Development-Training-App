# pages/foodtech/01_dashboard.py
import streamlit as st
import pandas as pd
import openai
from googletrans import Translator

# ✅ main() 함수 정의
def main():
    # ✅ OpenAI 및 번역기 설정
    openai.api_key = st.secrets["openai_api_key"]
    translator = Translator()

    # ✅ 데이터 로드
    @st.cache_data
    def load_data():
        df = pd.read_csv("data/foodtech_company.csv")
        df.columns = df.columns.str.strip()
        return df

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
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ AI 오류: {e}"

    st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    df = load_data()

    st.sidebar.header("📂 필터")
    mid_list = df["중분류"].dropna().unique().tolist()
    mid_selected = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_list))

    if mid_selected != "전체":
        df = df[df["중분류"] == mid_selected]

    sub_list = df["소분류"].dropna().unique().tolist()
    sub_selected = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_list))

    if sub_selected != "전체":
        df = df[df["소분류"] == sub_selected]

    st.subheader(f"🔎 필터링된 기업 수: {len(df)}개")

    # ✅ 테이블 출력
    if not df.empty:
        table_df = df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "사이트"]].reset_index(drop=True)
        selected_row = st.dataframe(table_df, use_container_width=True)

        # ✅ 기술 선택 처리
        selected_tech = st.selectbox("🔧 대표기술 선택", df["대표기술"].dropna().unique().tolist())
        if selected_tech:
            st.divider()
            st.markdown(f"## 🤖 `{selected_tech}` 기술 개요 (AI 요약)")
            with st.spinner("AI 요약 생성 중..."):
                summary = generate_tech_summary(selected_tech)
            st.markdown(summary)

            # ✅ 번역 후 이미지 검색
            translated = translator.translate(selected_tech, dest="en").text.replace(" ", "+")
            st.image(f"https://source.unsplash.com/featured/?{translated}", caption="AI 이미지", use_column_width=True)

    else:
        st.warning("🔍 해당 조건에 맞는 데이터가 없습니다.")

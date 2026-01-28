import streamlit as st
import pandas as pd
import openai

# ===============================
# OpenAI 설정 (구버전 0.28.x)
# ===============================
openai.api_key = st.secrets["openai_api_key"]

# ===============================
# 데이터 로드
# ===============================
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df.columns = df.columns.str.strip()  # 컬럼 공백 제거
    return df

# ===============================
# AI 기술 요약
# ===============================
def generate_tech_summary(tech):
    prompt = f"""
'{tech}'라는 푸드테크 기술에 대해 다음을 한국어로 정리해줘.

1. 기술 정의
2. 적용 가능한 식품 카테고리
3. R&D 활용 포인트
4. 최신 기술 및 연구 동향
5. 식품 제품 개발 아이디어

각 항목은 1~2문장으로.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ AI 호출 오류: {e}"

# ===============================
# 메인 앱
# ===============================
def main():
    st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
    st.title("🥣 FoodTech 기업 분석 대시보드")

    df = load_data()

    # ---------- 필터 ----------
    st.sidebar.header("📂 필터")

    mid_options = sorted(df["중분류"].dropna().unique())
    selected_mid = st.sidebar.selectbox("중분류", ["전체"] + list(mid_options))

    filtered = df.copy()
    if selected_mid != "전체":
        filtered = filtered[filtered["중분류"] == selected_mid]

    sub_options = sorted(filtered["소분류"].dropna().unique())
    selected_sub = st.sidebar.selectbox("소분류", ["전체"] + list(sub_options))

    if selected_sub != "전체":
        filtered = filtered[filtered["소분류"] == selected_sub]

    st.markdown(f"### ✅ 검색 결과: {len(filtered)}개 기업")

    # ---------- 테이블 ----------
    table_df = filtered[
        ["기업이름", "중분류", "소분류", "기업정보", "대표기술", "사이트주소"]
    ].reset_index(drop=True)

    st.dataframe(table_df, use_container_width=True)

    # ---------- 기술 선택 ----------
    tech_list = sorted(filtered["대표기술"].dropna().unique())
    selected_tech = st.selectbox("🔍 대표기술 선택 (AI 분석)", ["선택 안함"] + tech_list)

    if selected_tech != "선택 안함":
        st.divider()

        # 좌우 분할
        left, right = st.columns([1.2, 1])

        with left:
            st.markdown(f"## 🤖 기술 개요: {selected_tech}")
            with st.spinner("AI가 기술을 분석 중입니다..."):
                summary = generate_tech_summary(selected_tech)
            st.markdown(summary)

        with right:
            st.markdown("## 🖼️ 관련 이미지")
            query = selected_tech.replace(" ", "+")
            st.image(
                f"https://source.unsplash.com/featured/?{query}",
                caption=f"{selected_tech} 관련 이미지",
                use_container_width=True
            )

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    main()

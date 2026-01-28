import streamlit as st
import pandas as pd
from openai import OpenAI

# ✅ main 함수로 전체 감싸기
def main():
    st.set_page_config(page_title="푸드테크 기업 대시보드", layout="wide")
    st.title("🌟 푸드테크 기업 분석 대시보드")

    # ✅ OpenAI API 클라이언트 설정
    try:
        client = OpenAI(api_key=st.secrets["openai_api_key"])
    except Exception as e:
        st.error(f"❌ OpenAI 키 오류: {e}")
        return

    # ✅ 데이터 로드
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv("data/foodtech_company.csv")
            return df
        except FileNotFoundError:
            st.error("❌ 데이터 파일을 찾을 수 없습니다. 'data/foodtech_company.csv' 경로를 확인하세요.")
            return pd.DataFrame()

    # ✅ GPT 기술 설명 생성
    def generate_ai_description(tech_name):
        try:
            prompt = f"""
            '{tech_name}'라는 푸드테크 대표기술에 대해 다음 내용을 요약해줘:
            1. 기술 정의
            2. 적용 가능한 식품 카테고리
            3. R&D 개발 포인트
            한국어로 간결하게 설명해줘 (각 항목마다 1~2문장씩)
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ 설명 생성 오류: {e}"

    # ✅ 데이터 불러오기
    df = load_data()
    if df.empty:
        return

    # ✅ 사이드바 필터
    st.sidebar.header("📂 필터")
    mid_categories = df["중분류"].dropna().unique().tolist()
    selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

    filtered_df = df[df["중분류"] == selected_mid] if selected_mid != "전체" else df

    sub_categories = filtered_df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

    filtered_df = filtered_df[filtered_df["소분류"] == selected_sub] if selected_sub != "전체" else filtered_df

    st.subheader(f"🔎 필터링된 기업 수: {len(filtered_df)}개")

    # ✅ 세션 상태 변수 초기화
    if "selected_tech" not in st.session_state:
        st.session_state.selected_tech = None
    if "related_product" not in st.session_state:
        st.session_state.related_product = ""

    # ✅ 기업 리스트
    for idx, row in filtered_df.iterrows():
        with st.expander(f"{row['기업이름']} | {row['중분류']} > {row['소분류']}"):
            st.markdown(f"**기업정보:** {row['기업정보']}")
            tech_col = st.columns([0.2, 0.8])
            if tech_col[0].button("👁️ 기술 보기", key=f"tech_{idx}"):
                st.session_state.selected_tech = row["대표기술"]
                st.session_state.related_product = row.get("대표제품", "")
            tech_col[1].markdown(f"**대표기술:** {row['대표기술']}")
            st.markdown(f"**대표제품:** {row.get('대표제품', '')}")

    # ✅ 기술 상세 설명 영역
    selected_tech = st.session_state.get("selected_tech", None)
    related_product = st.session_state.get("related_product", "")

    if selected_tech:
        st.divider()
        st.markdown(f"## 🤖 기술 개요 (AI 생성): `{selected_tech}`")

        with st.spinner("🧠 GPT가 기술 개요를 작성 중입니다..."):
            ai_text = generate_ai_description(selected_tech)

        st.markdown("### ✅ GPT 응답 확인 (디버깅용)")
        st.code(ai_text)

        st.markdown("### 📌 기술 요약")
        st.markdown(ai_text)

        st.markdown("## 🖼️ 관련 제품 이미지")
        image_query = f"{related_product} {selected_tech}" if related_product else selected_tech
        st.image(f"https://source.unsplash.com/featured/?{image_query}", caption=image_query, use_column_width=True)

# ✅ 외부에서 호출 시 실행
if __name__ == "__main__":
    main()

# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd
import openai

# OpenAI API 키 설정
openai.api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else ""

@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df

def generate_keywords(text, max_tokens=30):
    try:
        prompt = f"'{text}'라는 기업 정보와 기술을 바탕으로 유사한 푸드테크 키워드를 5개 제시해줘."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 키워드 생성 실패: {e}"

def main():
    # 페이지 설정
    st.set_page_config(page_title="푸드테크 기업 대시보드", page_icon="🌟", layout="wide")
    st.title(":green[푸드테크 기업 분석 대시보드] 🏢")

    st.markdown("기업 데이터 기반으로 필터링, 분석, AI 키워드 추천을 제공합니다.")

    # 데이터 로드
    df = load_data()

    # 필터링 옵션
    st.sidebar.header("📂 카테고리 필터")
    mid_categories = df["중분류"].dropna().unique().tolist()
    selected_mid = st.sidebar.selectbox("중분류 선택", ["전체"] + sorted(mid_categories))

    # 소분류 필터링
    filtered_df = df.copy()
    if selected_mid != "전체":
        filtered_df = filtered_df[filtered_df["중분류"] == selected_mid]
    
    sub_categories = filtered_df["소분류"].dropna().unique().tolist()
    selected_sub = st.sidebar.selectbox("소분류 선택", ["전체"] + sorted(sub_categories))

    if selected_sub != "전체":
        filtered_df = filtered_df[filtered_df["소분류"] == selected_sub]

    st.subheader(f"🔍 필터링된 기업 수: {len(filtered_df)}개")

    # 결과 테이블
    for idx, row in filtered_df.iterrows():
        with st.expander(f"{row['기업이름']} ({row['중분류']} - {row['소분류']})"):
            st.markdown(f"**기업정보:** {row['기업정보']}")
            st.markdown(f"**대표기술:** {row['대표기술']}")
            st.markdown(f"**AI 키워드 추천:** {generate_keywords(row['기업정보'])}")

    # 다운로드 기능
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 결과 CSV 다운로드", data=csv, file_name="filtered_foodtech.csv", mime="text/csv")


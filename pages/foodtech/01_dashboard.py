import streamlit as st
import pandas as pd
import openai
import requests

# OpenAI API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]  # .streamlit/secrets.toml에 키 저장 필요

# 페이지 설정
st.set_page_config(
    page_title="푸드테크 기업 분석 대시보드",
    page_icon="🍽️",
    layout="wide"
)

st.title(":green[푸드테크 기업 대시보드] 🍽️")
st.markdown("""
**중분류 > 소분류** 선택 후 **대표기술**을 클릭하면,  
왼쪽에는 AI가 해당 기술을 설명하고,  
오른쪽에는 관련 제품명을 기반으로 한 이미지를 출력합니다.
""")

# 데이터 로드 함수
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df = df.drop(columns=["순번"], errors="ignore")
    return df

df = load_data()

# 사이드바: 중분류, 소분류 필터
st.sidebar.header("🔍 필터 선택")
mid_options = sorted(df["중분류"].dropna().unique())
selected_mid = st.sidebar.selectbox("중분류", ["전체"] + mid_options)

if selected_mid != "전체":
    df = df[df["중분류"] == selected_mid]

sub_options = sorted(df["소분류"].dropna().unique())
selected_sub = st.sidebar.selectbox("소분류", ["전체"] + sub_options)

if selected_sub != "전체":
    df = df[df["소분류"] == selected_sub]

st.subheader(f"📊 총 기업 수: {len(df)}개")

# 대표기술 선택
selected_tech = st.selectbox("🧪 대표기술 선택", ["선택 안 함"] + df["대표기술"].dropna().unique().tolist())

col1, col2 = st.columns(2)

# 왼쪽: AI 기술 개요 설명
with col1:
    if selected_tech != "선택 안 함":
        st.markdown(f"### 🤖 AI 기술 개요: **{selected_tech}**")
        with st.spinner("AI가 설명 작성 중..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "당신은 푸드테크 전문가입니다."},
                        {"role": "user", "content": f"'{selected_tech}'이라는 푸드테크 기술을 초심자도 이해하기 쉽게 한국어로 3~5문장으로 설명해주세요."}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                summary = response['choices'][0]['message']['content']
                st.success(summary)
            except Exception as e:
                st.error(f"AI 설명 요청 실패: {str(e)}")

# 오른쪽: 관련 제품 이미지 검색
with col2:
    if selected_tech != "선택 안 함":
        selected_product = df[df["대표기술"] == selected_tech]["대표제품"].values[0]
        st.markdown(f"### 🖼️ 관련 제품 이미지: **{selected_product[:50]}...**")
        try:
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": st.secrets["GOOGLE_API_KEY"],       # secrets.toml에 저장 필요
                "cx": st.secrets["GOOGLE_CSE_ID"],          # Google CSE ID
                "q": selected_product,
                "searchType": "image",
                "num": 1,
            }
            resp = requests.get(search_url, params=params)
            results = resp.json()

            if "items" in results:
                image_url = results["items"][0]["link"]
                st.image(image_url, caption=selected_product, use_column_width=True)
            else:
                st.warning("이미지를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"이미지 검색 실패: {str(e)}")

# 하단: 관련 기업 테이블
st.markdown("---")
st.markdown("### 📋 관련 기업 리스트")

filtered_df = df[df["대표기술"] == selected_tech] if selected_tech != "선택 안 함" else df
st.dataframe(filtered_df[["기업이름", "중분류", "소분류", "대표기술", "대표제품", "사이트 주소"]], use_container_width=True)

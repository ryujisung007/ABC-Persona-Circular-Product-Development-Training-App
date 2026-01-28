# pages/foodtech/01_dashboard.py

import streamlit as st
import pandas as pd
import openai
import requests

# ✅ OpenAI 키 설정
openai.api_key = st.secrets["openai_api_key"]
google_api_key = st.secrets["google_api_key"]
google_translate_url = "https://translation.googleapis.com/language/translate/v2"

# ✅ 데이터 로딩
@st.cache_data
def load_data():
    df = pd.read_csv("data/foodtech_company.csv")
    df.columns = df.columns.str.strip()
    return df

# ✅ 기술 번역 함수 (한글 → 영어)
def translate_korean_to_english(text):
    params = {
        "q": text,
        "source": "ko",
        "target": "en",
        "format": "text",
        "key": google_api_key
    }
    response = requests.post(google_translate_url, params=params)
    if response.status_code == 200:
        return response.json()["data"]["translations"][0]["translatedText"]
    else:
        return None

# ✅ 기술 설명 생성 함수
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

# ✅ Streamlit 설정
st.set_page_config(page_title="🥣 FoodTech 기업 대시보드", layout="wide")
st.title("🥣 FoodTech 기업 분석 대시보드")

# ✅ 데이터 로딩
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
selected_row = None
selected_tech = None

if not filtered_df.empty:
    selected_row = st.dataframe(
        filtered_df[["기업이름", "중분류", "소분류", "기업정보", "대표기술", "사이트 주소"]],
        use_container_width=True
    )

    # 대표기술 선택 UI
    selected_tech = st.selectbox("대표기술 선택", filtered_df["대표기술"].unique())

# ✅ AI 기술 설명
if selected_tech:
    st.divider()
    st.markdown(f"## 🤖 `{selected_tech}` 기술 개요 (GPT 생성)")
    with st.spinner("AI가 기술 개요를 작성 중입니다..."):
        summary = generate_tech_summary(selected_tech)
        st.markdown(summary)

    # ✅ 기술명 영어 번역 및 이미지 검색
    translated_query = translate_korean_to_english(selected_tech)
    if translated_query:
        st.markdown("### 🖼️ 관련 제품 이미지 (Unsplash 기반)")
        image_url = f"https://source.unsplash.com/featured/?{translated_query.replace(' ', '+')}"
        st.image(image_url, caption=f"{selected_tech} 관련 이미지", use_column_width=True)
    else:
        st.warning("❗ 번역 실패로 인해 이미지를 불러올 수 없습니다.")

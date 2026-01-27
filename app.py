# abc_persona_app/app.py (v2.2.3)
import streamlit as st
import pandas as pd
import json
import time
from openai import OpenAI

# CSV 로딩 함수
@st.cache_data
def load_data():
    df_a = pd.read_csv("data/A_persona_concept.csv")
    df_b = pd.read_csv("data/B_persona_maketing.csv")
    df_roles = pd.read_csv("data/A_B_C_persona.csv")
    df_roles.columns = [col.strip().replace("\ufeff", "") for col in df_roles.columns]
    role_col = next((col for col in df_roles.columns if col in ["역할", "role"]), None)
    if not role_col:
        raise KeyError("'역할' 또는 'role' 컬럼을 찾을 수 없습니다")
    df_researchers = df_roles[df_roles[role_col].str.contains("연구원", na=False)]
    return df_a, df_b, df_researchers

# 페르소나 요약 텍스트 생성
def build_persona_context(df_a, df_b, df_researchers):
    a_summary = df_a["USP(한 문장)"].dropna().head(3).to_string(index=False)
    b_summary = df_b.iloc[1:, 0:3].dropna().to_string(index=False)
    r_summary = df_researchers.dropna().head(3).to_string(index=False)
    return a_summary, b_summary, r_summary

# 사용자 입력 텍스트 생성
def build_user_context(user_inputs):
    return f"""
제품 목표: {user_inputs['goal']}
카테고리: {user_inputs['category']}
희망 가격: {user_inputs['price']}
출시 시즌: {user_inputs['season']}
판매 채널: {', '.join(user_inputs['channels'])}
시장 환경: {user_inputs['market_env']}
트렌드 키워드: {', '.join(user_inputs['trends'])}
출시 목표일: {user_inputs['launch_date']}
"""

# 프롬프트 생성 함수
def build_final_prompt(a_summary, b_summary, r_summary, user_context):
    return f"""
# ABC 페르소나 기반 순환 제품개발

## A. 기획자 관점 주요 제품 사례
{a_summary}

## B. 마케터 관점 마케팅 분석 요약
{b_summary}

## C. 연구원 관점 기술적 참고 페르소나
{r_summary}

## 사용자 입력 정보
{user_context}

[지금 할 일]
1. 최근 트렌드 기반으로 10개 제품 컨셉을 생성해줘.
2. 각 컨셉은 맛 조합 / 기능성 포인트 / 타깃 소비층을 포함해야 해.
3. 아래 JSON 구조로 응답해줘:
[
  {{ "name": ..., "flavor": ..., "functionality": ..., "target": ..., "score": ... }},
  ... (총 10개)
]
"""

# OpenAI 호출 함수
@st.cache_data(show_spinner=False)
def call_openai(api_key, prompt):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result, None
    except Exception as e:
        return None, str(e)

# Streamlit 앱 시작
st.set_page_config(page_title="ABC 페르소나 순환 제품개발", layout="wide")
st.title("🥤 ABC 페르소나 순환 제품개발 앱 v2.2.3")

try:
    df_a, df_b, df_researchers = load_data()
except Exception as e:
    st.error(f"❌ 데이터 로딩 오류: {e}")
    st.stop()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("◀ LEFT ▶ **입력 / 선택 패널**")
    st.markdown("""
    - **PRE-STEP:** 사전 기획 정의
    - **STEP 0:** 시장·트렌드 입력
    - **STEP A:** 제품 컨셉
    - **STEP B:** 마케팅 전략 (B)
    - **STEP C:** 배합비 개발 (C)
    - **STEP R:** 요약 & 과제
    """)

with right_col:
    st.subheader("▶ RIGHT ◀ **출력 & 시각화 대시보드**")
    st.markdown("""
    - 📌 사전기획 요약 카드
    - 🧠 AI 사고 프로세스 그래프
    - 🍓 컨셉 카드 / 관능 맵
    - 📊 3C·SWOT / 점수 / 의사결정
    - 🧪 배합비 테이블 / 그래프
    - 📜 전체 스토리 + 과제
    """)# abc_persona_app/app.py (v2.2.3 - 리디자인 포함)
import streamlit as st
import pandas as pd
import json
import time
from openai import OpenAI

# CSV 로딩 함수
@st.cache_data
def load_data():
    df_a = pd.read_csv("data/A_persona_concept.csv", encoding="utf-8-sig")
    df_b = pd.read_csv("data/B_persona_maketing.csv", encoding="utf-8-sig")
    df_roles = pd.read_csv("data/A_B_C_persona.csv", encoding="utf-8-sig")

    df_roles.columns = [col.strip().replace("\ufeff", "").lower() for col in df_roles.columns]
    role_col = next((col for col in df_roles.columns if col in ["역할", "role"]), None)

    if not role_col:
        raise ValueError("'역할' 또는 'role' 컬럼이 A_B_C_persona.csv에 존재하지 않습니다.")

    df_researchers = df_roles[df_roles[role_col].str.contains("연구원", na=False)]
    return df_a, df_b, df_researchers

# 페르소나 요약 텍스트 생성 (기획자, 마케터, 연구원 별)
def build_persona_context(df_a, df_b, df_researchers):
    a_summary = df_a[["제품명/브랜드(가칭)", "카테고리", "주요 소비층", "USP(한 문장)"]].dropna().head(3).to_string(index=False)
    b_summary = df_b.iloc[1:, 0:3].dropna().to_string(index=False)
    r_summary = df_researchers.dropna().head(3).to_string(index=False)
    return a_summary, b_summary, r_summary

# 사용자 입력 텍스트 생성
def build_user_context(user_inputs):
    return f"""
제품 목표: {user_inputs['goal']}
카테고리: {user_inputs['category']}
희망 가격: {user_inputs['price']}
출시 시즌: {user_inputs['season']}
판매 채널: {', '.join(user_inputs['channels'])}
시장 환경: {user_inputs['market_env']}
트렌드 키워드: {', '.join(user_inputs['trends'])}
출시 목표일: {user_inputs['launch_date']}
"""

# 프롬프트 생성 함수
def build_final_prompt(a_summary, b_summary, r_summary, user_context):
    return f"""
# ABC 페르소나 기반 순환 제품개발

## A. 기획자 관점 주요 제품 사례
{a_summary}

## B. 마케터 관점 마케팅 분석 요약
{b_summary}

## C. 연구원 관점 기술적 참고 페르소나
{r_summary}

## 사용자 입력 정보
{user_context}

[지금 할 일]
1. 최근 트렌드 기반으로 10개 제품 컨셉을 생성해줘.
2. 각 컨셉은 맛 조합 / 기능성 포인트 / 타깃 소비층을 포함해야 해.
3. 아래 JSON 구조로 응답해줘:
[
  {{ "name": ..., "flavor": ..., "functionality": ..., "target": ..., "score": ... }},
  ... (총 10개)
]
"""

# OpenAI 호출 함수
def call_openai(api_key, prompt):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result, None
    except Exception as e:
        return None, str(e)

# Streamlit 앱 시작
def main():
    st.set_page_config(page_title="ABC 페르소나 순환 제품개발", layout="wide")
    st.markdown("""
        <style>
        .big-title { font-size: 36px; font-weight: bold; color: #b30059; }
        .subtitle { font-size: 20px; font-weight: 500; color: #333; }
        .step-box { background: #f9f9f9; padding: 1rem; border-radius: 12px; margin-bottom: 1rem; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='big-title'>🥤 ABC 페르소나 순환 제품개발 앱 v2.2.3</div>", unsafe_allow_html=True)

    df_a, df_b, df_researchers = load_data()

    # STEP 패널 구성
    left, right = st.columns([1, 1])

    with left:
        st.markdown("<div class='subtitle'>◀ LEFT ▶ \n**입력 / 선택 패널**</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='step-box'>**PRE-STEP.** 사전 기획 정의</div>
        <div class='step-box'>**STEP 0.** 시장·트렌드 입력</div>
        <div class='step-box'>**STEP A.** 제품 컨셉</div>
        <div class='step-box'>**STEP B.** 마케팅 전략 (B)</div>
        <div class='step-box'>**STEP C.** 배합비 개발 (C)</div>
        <div class='step-box'>**STEP R.** 요약 & 과제</div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("<div class='subtitle'>▶ RIGHT ◀ \n**출력 & 시각화 대시보드**</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='step-box'>📌 사전기획 요약 카드</div>
        <div class='step-box'>🧠 AI 사고 프로세스 그래프</div>
        <div class='step-box'>🎨 컨셉 카드 / 관능 맵</div>
        <div class='step-box'>📊 3C·SWOT / 점수 / 의사결정</div>
        <div class='step-box'>🧪 배합비 테이블 / 그래프</div>
        <div class='step-box'>📝 전체 스토리 + 과제</div>
        """, unsafe_allow_html=True)

    st.divider()

    with st.sidebar:
        st.header("STEP 0. 기획자 입력 (A 페르소나)")
        goal = st.selectbox("제품 개발 목표", ["신제품 개발", "기존 제품 개선"])
        category = st.selectbox("제품 카테고리", ["RTD 티", "기능성 워터", "프리바이오틱 소다"])
        price = st.radio("희망 가격대", ["2,000원 미만", "2,000원 이상"])
        season = st.radio("출시 시즌", ["봄", "여름", "가을", "겨울"])
        channels = st.multiselect("판매 채널", ["편의점", "대형마트", "온라인몰", "카페"])

        st.header("STEP 1. 시장 트렌드 입력 (B 페르소나)")
        market_env = st.text_area("시장 환경 요약", value="2030 여성층 증가, 건강 트렌드 강화 등")
        trends = st.multiselect("적용 트렌드", ["저당", "장건강", "에너지", "향미", "기능성"])
        launch_date = st.text_input("출시 목표일 (YYYY-MM)", value="2026-06")

        api_key = st.text_input("🔑 OpenAI API Key", type="password")

    if st.button("🚀 STEP A: 제품 컨셉 후보 생성", type="primary"):
        user_inputs = {
            "goal": goal,
            "category": category,
            "price": price,
            "season": season,
            "channels": channels,
            "market_env": market_env,
            "trends": trends,
            "launch_date": launch_date,
        }

        a_summary, b_summary, r_summary = build_persona_context(df_a, df_b, df_researchers)
        user_context = build_user_context(user_inputs)
        prompt = build_final_prompt(a_summary, b_summary, r_summary, user_context)

        st.subheader("📄 생성된 프롬프트")
        st.code(prompt, language="markdown")

        with st.spinner("AI 분석 중..."):
            result, err = call_openai(api_key, prompt)

        if err:
            st.error(f"❌ 오류 발생: {err}")
            return

        st.success("✅ 후보 컨셉 생성 완료")
        st.markdown("### 🎨 추천 컨셉 Top 10")

        for i, item in enumerate(result):
            with st.expander(f"#{i+1}. {item['name']} ({item['score']}/100)"):
                st.markdown(f"**맛 조합**: {item['flavor']}")
                st.markdown(f"**기능성 포인트**: {item['functionality']}")
                st.markdown(f"**타깃 소비층**: {item['target']}")

if __name__ == "__main__":
    main()

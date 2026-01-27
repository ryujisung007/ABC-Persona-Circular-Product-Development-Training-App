# abc_persona_app/app.py
import streamlit as st
import pandas as pd
import json
import time
from openai import OpenAI

# CSV 로딩 함수
def load_data():
    df_a = pd.read_csv("data/A_persona_concept.csv")
    df_b = pd.read_csv("data/B_persona_maketing.csv")
    df_roles = pd.read_csv("data/A_B_C_persona.csv")
    df_researchers = df_roles[df_roles["역할"].str.contains("연구원")]
    return df_a, df_b, df_researchers

# 페르소나 요약 텍스트 생성 (기획자, 마케터, 연구원 별)
def build_persona_context(df_a, df_b, df_researchers):
    a_summary = df_a[["제품명/브랜드(가칭)", "카테고리", "주요 소비층", "USP(한 문장)"]].head(3).to_string(index=False)
    b_summary = df_b.iloc[1, 0:7].dropna().to_string()
    r_summary = df_researchers.head(3).to_string(index=False)
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

위 정보를 기반으로 아래 JSON 구조로 결과를 생성해줘:
{{
  "A": {{ "name": ..., "slogan": ..., "functionality": ... }},
  "B": {{ "target_fit": ..., "uniqueness": ..., "marketability": ..., "summary": ... }},
  "C": {{ "원료명": "함량%", ... }}
}}
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
    st.title("🥤 ABC 페르소나 순환 제품개발 앱")

    # 데이터 로딩
    df_a, df_b, df_researchers = load_data()

    # 사용자 입력
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

    # 실행 버튼
    if st.button("🚀 STEP A/B/C 결과 생성", type="primary"):
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

        # 컨텍스트 생성
        a_summary, b_summary, r_summary = build_persona_context(df_a, df_b, df_researchers)
        user_context = build_user_context(user_inputs)
        prompt = build_final_prompt(a_summary, b_summary, r_summary, user_context)

        st.subheader("📄 생성된 프롬프트")
        st.code(prompt, language="markdown")

        # AI 호출
        with st.spinner("AI 분석 중..."):
            result, err = call_openai(api_key, prompt)

        if err:
            st.error(f"❌ 오류 발생: {err}")
            return

        st.success("✅ 분석 완료")

        # 결과 출력
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### A. 제품 컨셉")
            st.json(result.get("A", {}))

        with col2:
            st.markdown("### B. 마케팅 평가")
            st.json(result.get("B", {}))

        with col3:
            st.markdown("### C. 제품 배합비")
            st.json(result.get("C", {}))

if __name__ == "__main__":
    main()

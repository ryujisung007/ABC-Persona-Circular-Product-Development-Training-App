# abc_persona_app/app.py (v2.2.4)
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
    role_col = next((col for col in df_roles.columns if col.strip() in ["역할", "role"]), None)
    if not role_col:
        st.error("❌ 데이터 로딩 오류: '역할' 또는 'role' 컬럼을 찾을 수 없습니다")
        st.stop()
    df_researchers = df_roles[df_roles[role_col].str.contains("연구원", na=False)]
    return df_a, df_b, df_researchers

# 페르소나 요약 텍스트 생성
def build_persona_context(df_a, df_b, df_researchers):
    a_summary = df_a[["제품명/브랜드(가칭)", "카테고리", "주요 소비층", "USP(한 문장)"]].dropna().head(3).to_string(index=False)
    b_summary = df_b.iloc[1:, 0:3].dropna().to_string(index=False)
    r_summary = df_researchers.dropna().head(3).to_string(index=False)
    return a_summary, b_summary, r_summary

# 사용자 입력 요약
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

# STEP A 프롬프트 생성
def build_step_a_prompt(a_summary, b_summary, r_summary, user_context):
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

# STEP B 프롬프트 생성
def build_step_b_prompt(concept, a_summary, b_summary):
    return f"""
다음 제품 컨셉에 대해 마케팅 전략을 B 페르소나의 시각으로 작성해줘.

📌 제품명: {concept['name']}
📌 맛 조합: {concept['flavor']}
📌 기능성: {concept['functionality']}
📌 타깃: {concept['target']}

[참고: A페르소나 요약]
{a_summary}

[참고: B페르소나 요약]
{b_summary}

💡 마케팅 전략을 아래와 같은 5개 항목으로 출력해줘:
1. 핵심 USP 요약 (한 줄)
2. 고객 인사이트 / 페인포인트
3. 시장 포지셔닝
4. 적합한 광고 메시지 예시
5. 추천 판매 채널

아래 JSON 형식으로 출력:
{{
  "usp": ..., "insight": ..., "positioning": ..., "message": ..., "channel": ...
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
    st.title("🥤 ABC 페르소나 순환 제품개발 앱 v2.2.4")

    df_a, df_b, df_researchers = load_data()

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
        prompt = build_step_a_prompt(a_summary, b_summary, r_summary, user_context)

        st.subheader("📄 생성된 프롬프트 (STEP A)")
        st.code(prompt, language="markdown")

        with st.spinner("AI 분석 중..."):
            result, err = call_openai(api_key, prompt)

        if err:
            st.error(f"❌ 오류 발생: {err}")
            return

        st.success("✅ 후보 컨셉 생성 완료")
        st.markdown("### 🎨 추천 컨셉 Top 5")
        selected_concept = None

        for i, item in enumerate(result[:5]):
            if st.button(f"선택 → #{i+1}. {item['name']} ({item['score']}/100)"):
                selected_concept = item
                st.session_state["selected_concept"] = item

        if "selected_concept" in st.session_state:
            concept = st.session_state["selected_concept"]
            st.markdown(f"### 🔄 STEP B: 마케팅 전략 생성 대상 → {concept['name']}")

            step_b_prompt = build_step_b_prompt(concept, a_summary, b_summary)
            st.code(step_b_prompt, language="markdown")

            if st.button("🧠 STEP B 실행: 마케팅 전략 생성"):
                with st.spinner("AI 마케팅 전략 분석 중..."):
                    result_b, err_b = call_openai(api_key, step_b_prompt)

                if err_b:
                    st.error(f"❌ STEP B 오류: {err_b}")
                    return

                st.success("✅ 마케팅 전략 생성 완료")
                st.json(result_b)

if __name__ == "__main__":
    main()

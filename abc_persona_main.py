# abc_persona_main.py
import streamlit as st
import pandas as pd
import json
import time
from openai import OpenAI
import matplotlib.pyplot as plt

# =========================
# 데이터 로딩
# =========================
def load_data():
    df_a = pd.read_csv("data/A_persona_concept.csv")
    df_b = pd.read_csv("data/B_persona_maketing.csv")
    df_roles = pd.read_csv("data/A_B_C_persona.csv")
    return df_a, df_b, df_roles


def build_persona_context(df_a, df_b, df_roles):
    a_summary = df_a.head(3).to_string(index=False)
    b_summary = df_b.head(3).to_string(index=False)
    r_summary = df_roles.head(3).to_string(index=False)
    return a_summary, b_summary, r_summary


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


def build_final_prompt(a_summary, b_summary, r_summary, user_context):
    return f"""
# ABC 페르소나 기반 순환 제품개발

## A. 기획자 관점
{a_summary}

## B. 마케터 관점
{b_summary}

## C. 연구원 관점
{r_summary}

## 사용자 입력
{user_context}

[요청]
- 제품 컨셉 10개 생성
- JSON 형식으로 응답
"""


def call_openai(api_key, prompt):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content)


# =========================
# 배합비 시각화
# =========================
def show_blend_table():
    st.subheader("🧪 STEP C: 배합비 비교")

    data = {
        "원료명": ["정제수", "오미자농축액", "사과농축액", "프락토올리고당"],
        "기준": [60, 15, 15, 10],
        "AI": [55, 18, 12, 15],
        "연구원": [50, 20, 15, 15],
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    df.set_index("원료명").plot(kind="bar", ax=ax)
    st.pyplot(fig)


# =========================
# ✅ 메인 진입점 (중요)
# =========================
def main():
    st.title("🥤 ABC 페르소나 순환 제품개발 앱 v3.0")

    # 🔥 중요: 여기에는 **앱 선택 selectbox 없음**
    # (app.py에서 이미 처리됨)

    df_a, df_b, df_roles = load_data()
    a_summary, b_summary, r_summary = build_persona_context(df_a, df_b, df_roles)

    with st.sidebar:
        st.header("STEP 0. 기획자 입력")

        goal = st.selectbox("제품 목표", ["신제품 개발", "리뉴얼"], key="abc_goal")
        category = st.selectbox("카테고리", ["RTD 티", "기능성 음료"], key="abc_cat")
        price = st.radio("가격대", ["2,000원 미만", "2,000원 이상"], key="abc_price")
        season = st.radio("출시 시즌", ["봄", "여름", "가을", "겨울"], key="abc_season")
        channels = st.multiselect(
            "판매 채널", ["편의점", "온라인", "카페"], key="abc_channel"
        )
        market_env = st.text_area(
            "시장 환경", "2030 여성 건강 트렌드 강화", key="abc_market"
        )
        trends = st.multiselect(
            "트렌드", ["저당", "장건강", "에너지"], key="abc_trend"
        )
        launch_date = st.text_input("출시 목표", "2026-06", key="abc_date")
        api_key = st.text_input("OpenAI API Key", type="password", key="abc_api")

    if st.button("🚀 STEP A: 컨셉 생성", key="abc_step_a"):
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
        prompt = build_final_prompt(
            a_summary, b_summary, r_summary, build_user_context(user_inputs)
        )
        st.session_state.concepts = call_openai(api_key, prompt)
        st.success("컨셉 생성 완료")

    if "concepts" in st.session_state:
        st.subheader("🎨 생성된 컨셉")
        st.json(st.session_state.concepts[:3])

        if st.button("🧪 STEP C 실행", key="abc_step_c"):
            show_blend_table()

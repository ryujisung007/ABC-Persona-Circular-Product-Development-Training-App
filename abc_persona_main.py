# abc_persona_app/app.py (v3.0) - 자동 플로우 연결
import streamlit as st
import pandas as pd
import json
import time
from openai import OpenAI
import matplotlib.pyplot as plt

# CSV 로딩 함수
def load_data():
    df_a = pd.read_csv("data/A_persona_concept.csv")
    df_b = pd.read_csv("data/B_persona_maketing.csv")
    df_roles = pd.read_csv("data/A_B_C_persona.csv")
    df_researchers = df_roles[
        df_roles.columns[df_roles.columns.str.contains("역할|role")][0]
    ]
    return df_a, df_b, df_roles

# 페르소나 요약
def build_persona_context(df_a, df_b, df_roles):
    a_summary = df_a.head(3).to_string(index=False)
    b_summary = df_b.head(3).to_string(index=False)
    r_summary = df_roles.head(3).to_string(index=False)
    return a_summary, b_summary, r_summary

# 사용자 입력 텍스트
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

# 프롬프트 생성
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

# OpenAI 호출
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

# 배합비 시각화
def show_blend_table():
    st.subheader("🧪 STEP C: 3종 배합비 비교")
    data = {
        "원료명": ["정제수", "오미자농축액", "사과농축액", "감초추출물", "프락토올리고당", "구연산"],
        "기준 배합비": [60, 10, 10, 10, 5, 5],
        "AI 추천 배합비": [52, 12, 8, 10, 8, 5],
        "연구원 배합비": [48, 15, 12, 10, 10, 5],
        "원료군": ["베이스", "향미", "향미", "기능성", "기능성", "pH 조절"]
    }
    df = pd.DataFrame(data)
    st.dataframe(df.set_index("원료명"), use_container_width=True)

    st.subheader("📈 배합비 구성비 비교 그래프")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(df))
    ax.bar([i - 0.25 for i in x], df["기준 배합비"], width=0.25, label="기준", align="center")
    ax.bar(x, df["AI 추천 배합비"], width=0.25, label="AI 추천", align="center")
    ax.bar([i + 0.25 for i in x], df["연구원 배합비"], width=0.25, label="연구원", align="center")
    ax.set_xticks(x)
    ax.set_xticklabels(df["원료명"])
    ax.set_ylabel("배합비 (%)")
    ax.set_title("3종 배합비 구성 비교")
    ax.legend()
    st.pyplot(fig)

    st.subheader("🧾 원료군 라벨 설명")
    emoji_dict = {
        "베이스": "💧", "향미": "🍓", "기능성": "🌿", "pH 조절": "⚗️"
    }
    for i in range(len(df)):
        name = df.loc[i, "원료명"]
        group = df.loc[i, "원료군"]
        emoji = emoji_dict.get(group, "❓")
        st.markdown(f"- {emoji} **{name}** → `{group}`")

# 앱 실행
def main():
    st.set_page_config(page_title="ABC 페르소나 순환 제품개발", layout="wide")
    st.title("🥤 ABC 페르소나 순환 제품개발 앱 v3.0")
    
    df_a, df_b, df_roles = load_data()
    a_summary, b_summary, r_summary = build_persona_context(df_a, df_b, df_roles)

    # 사용자 입력값
    with st.sidebar:
        st.header("STEP 0. 기획자 입력")
        goal = st.selectbox("제품 개발 목표", ["신제품 개발", "기존 제품 개선"])
        category = st.selectbox("제품 카테고리", ["RTD 티", "기능성 워터", "프리바이오틱 소다"])
        price = st.radio("희망 가격대", ["2,000원 미만", "2,000원 이상"])
        season = st.radio("출시 시즌", ["봄", "여름", "가을", "겨울"])
        channels = st.multiselect("판매 채널", ["편의점", "대형마트", "온라인몰", "카페"])
        market_env = st.text_area("시장 환경 요약", value="2030 여성층 증가, 건강 트렌드 강화 등")
        trends = st.multiselect("적용 트렌드", ["저당", "장건강", "에너지", "향미", "기능성"])
        launch_date = st.text_input("출시 목표일", value="2026-06")
        api_key = st.text_input("🔑 OpenAI API Key", type="password")

    # STEP A
    if "concepts" not in st.session_state:
        if st.button("🚀 STEP A: 제품 컨셉 생성"):
            user_inputs = {
                "goal": goal, "category": category, "price": price,
                "season": season, "channels": channels,
                "market_env": market_env, "trends": trends, "launch_date": launch_date
            }
            user_context = build_user_context(user_inputs)
            prompt = build_final_prompt(a_summary, b_summary, r_summary, user_context)
            result, err = call_openai(api_key, prompt)
            if err:
                st.error(err)
            else:
                st.session_state.concepts = result
                st.success("✅ 컨셉 생성 완료")
    else:
        st.subheader("🎨 생성된 제품 컨셉 (Top 5)")
        concepts = st.session_state.concepts[:5]
        options = [f"{c['name']} ({c['score']})" for c in concepts]
        selected = st.radio("STEP B로 전이할 컨셉을 선택하세요:", options)
        if selected:
            st.session_state.selected_concept = next(
                item for item in concepts if item['name'] in selected
            )
            st.success("선택 완료 → 마케팅 단계로 이동하세요")

    # STEP B (자동 실행)
    if "selected_concept" in st.session_state:
        st.header("📢 STEP B: 마케팅 포인트 생성")
        c = st.session_state.selected_concept
        st.markdown(f"**제품명**: {c['name']}")
        st.markdown(f"**맛 조합**: {c['flavor']} / 기능: {c['functionality']}")
        st.markdown(f"**타깃층**: {c['target']}")
        st.success("💡 마케팅 컨셉: 2030 여성 건강+맛+휴대성 강조")

        if st.button("STEP C로 이동 → 배합비 자동 생성"):
            st.session_state.to_step_c = True

    # STEP C
    if "to_step_c" in st.session_state:
        st.header("🧪 STEP C: 배합비 자동 생성")
        show_blend_table()

if __name__ == "__main__":
    main()

# abc-persona-circular-product-development-training-app/app.py

import streamlit as st
import pandas as pd
import time
import json
import hashlib
import openai
from typing import Dict, Any

st.set_page_config(page_title="ABC Persona Product Dev", layout="wide")

# 캐시 키 생성용 해시

def hash_input(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

# OpenAI 호출 래퍼 (temperature 제거)

def call_openai_once(api_key: str, prompt: str, model: str = "o4-mini") -> tuple[Dict, float]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    start = time.time()
    try:
        resp = client.responses.create(
            model=model,
            input=prompt
        )
        end = time.time()
        return json.loads(resp.output_text), round(end - start, 2)
    except Exception as e:
        st.error(f"❌ AI 실행 실패: {str(e)}")
        raise

# 사용자 입력 수집

def collect_inputs() -> Dict:
    with st.sidebar:
        st.header("🧩 STEP 0. 제품 사전 기획")
        goal = st.selectbox("제품 개발 목표", ["완전 신제품", "기존 라인 확장", "패키지 리뉴얼"])
        category = st.selectbox("제품 카테고리", ["탄산음료", "RTD 주스", "기능성 음료"])
        price = st.selectbox("희망 가격대", ["1000원", "1500원", "2000원 이상"])
        channel = st.multiselect("판매 채널", ["CU", "GS25", "마켓컬리", "온라인몰", "이마트"])
        season = st.radio("출시 시즌", ["봄", "여름", "가을", "겨울"])

        st.markdown("---")
        st.header("🌐 STEP 1. 시장 환경 입력")
        date = st.text_input("출시 목표일 (YYYY-MM)", "2026-05")
        market_env = st.text_area("시장 환경 요약", "2030세대 증가, 고령화, 1인가구 확대 등")
        trends = st.multiselect("적용 트렌드", ["웰빙", "새로운 맛", "뉴니스", "차별화", "기능성"])
        target_20f = st.text_input("20대 여성 소비자 특징", "운동을 좋아하고 직장 초년생")
        target_30m = st.text_input("30대 남성 소비자 특징", "여행, 건강소비는 아끼지 않음")
        packaging = st.text_input("선호 포장 형태", "페트병 + 친환경 소재")

    return {
        "goal": goal,
        "category": category,
        "price_tier": price,
        "channels": channel,
        "season": season,
        "launch_date": date,
        "market_env": market_env,
        "trends": trends,
        "target_20f": target_20f,
        "target_30m": target_30m,
        "packaging": packaging,
    }

# 프롬프트 생성기

def create_ai_prompt(inputs: Dict) -> str:
    lines = [
        f"[기획목표]\n{inputs['goal']}",
        f"[카테고리]\n{inputs['category']}",
        f"[희망가격대]\n{inputs['price_tier']}",
        f"[출시시즌]\n{inputs['season']}",
        f"[판매채널]\n{', '.join(inputs['channels'])}",
        f"[출시일]\n{inputs['launch_date']}",
        f"[시장환경]\n{inputs['market_env']}",
        f"[적용트렌드]\n{', '.join(inputs['trends'])}",
        f"[20대여성 특징]\n{inputs['target_20f']}",
        f"[30대남성 특징]\n{inputs['target_30m']}",
        f"[포장선호]\n{inputs['packaging']}",
        "\n[A 컨셉안]\n제품명, 포지셔닝, 주요 USP, 관능 키워드, 마케팅 포인트",
        "\n[B 마케팅 검토]\n3C분석, SWOT분석, 수치 평가(회사적합성, 제조난이도, 원가, 수용성 등)",
        "\n[C 제품배합비 개발]\n제품유형/기준배합비/관능버전 2개/설명 요약으로 구성",
        "\n모든 출력은 JSON 형식으로 구성하라."
    ]
    return "\n".join(lines)

# 메인 실행

def run_streamlit_app():
    st.title("🥤 ABC 페르소나 순환 제품개발 앱")
    user_input = collect_inputs()
    key = hash_input(user_input)
    api_key = st.secrets["OPENAI_API_KEY"]

    if "ai_cache" not in st.session_state:
        st.session_state["ai_cache"] = {}

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🚀 실행")
        if st.button("AI에게 맡기기"):
            if key in st.session_state["ai_cache"]:
                st.success("✅ 이전 결과 사용 (캐시)")
                ai_result, elapsed = st.session_state["ai_cache"][key]
            else:
                with st.spinner("AI가 생각중입니다..."):
                    prompt = create_ai_prompt(user_input)
                    ai_result, elapsed = call_openai_once(api_key=api_key, prompt=prompt)
                    st.session_state["ai_cache"][key] = (ai_result, elapsed)
            st.session_state["result"] = (ai_result, elapsed)

    with col2:
        st.subheader("📊 대시보드")
        if "result" in st.session_state:
            data, elapsed = st.session_state["result"]
            st.markdown(f"**⏱ 소요시간**: {elapsed}초")
            st.markdown("### A. 제품 컨셉")
            st.json(data.get("A", {}))
            st.markdown("### B. 마케팅 평가")
            st.json(data.get("B", {}))
            st.markdown("### C. 제품 배합비")
            st.json(data.get("C", {}))
        else:
            st.info("STEP 0까지 입력 후 실행해주세요")

# 진입점

def main():
    run_streamlit_app()

if __name__ == "__main__":
    main()

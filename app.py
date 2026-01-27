# app.py
# ============================================================
# ABC Persona Circular Product Development Training App
# (String-safe version: NO multiline string literals)
# ============================================================

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

Decision = Literal["GO", "HOLD", "DROP"]

# ============================================================
# 1. Core business logic (NO Streamlit dependency)
# ============================================================

@dataclass(frozen=True)
class BScoreWeights:
    company_fit: float = 0.20
    cost_stability: float = 0.20
    manufacturability: float = 0.15
    customer_acceptance: float = 0.15
    repurchase: float = 0.20


def compute_b_score(
    company_fit: int,
    cost_stability: int,
    manufacturability: int,
    customer_acceptance: int,
    repurchase: int,
    w: BScoreWeights = BScoreWeights(),
) -> float:
    vals = [company_fit, cost_stability, manufacturability, customer_acceptance, repurchase]
    if not all(isinstance(v, int) and 1 <= v <= 5 for v in vals):
        raise ValueError("All scores must be int in [1,5]")

    score = (
        company_fit * w.company_fit
        + cost_stability * w.cost_stability
        + manufacturability * w.manufacturability
        + customer_acceptance * w.customer_acceptance
        + repurchase * w.repurchase
    )
    return round(score, 2)


def decision_from_score(score: float) -> Decision:
    if score >= 3.2:
        return "GO"
    if score >= 3.0:
        return "HOLD"
    return "DROP"


# ============================================================
# 2. SAFE prompt builder (★ 핵심 변경점 ★)
#    → 문자열 줄바꿈 오류 원천 차단
# ============================================================

def build_prompt(lines: List[str]) -> str:
    """Always join with \n. No multiline literals anywhere."""
    return "\n".join(lines)


# ============================================================
# 3. Persona prompt generators (string-safe)
# ============================================================

def persona_A_prompt(payload: Dict[str, Any]) -> str:
    return build_prompt([
        "[ROLE] 식품기획자(A)",
        "- 관능 중심 제품 컨셉 1안 도출",
        "",
        "[INPUT]",
        f"출시목표일: {payload['launch_date']}",
        f"시장환경: {payload['market_env']}",
        f"주요트렌드: {', '.join(payload['trends'])}",
        f"20대여성: {payload['target_20f']}",
        f"30대남성: {payload['target_30m']}",
        "",
        "[OUTPUT JSON]",
        "{",
        "  \"product_name\": \"...\",",
        "  \"positioning\": \"...\",",
        "  \"sensory_keywords\": [\"...\"],",
        "  \"marketing_points\": [\"...\"]",
        "}",
    ])


def persona_B_prompt(a: Dict[str, Any]) -> str:
    return build_prompt([
        "[ROLE] 식품음료 마케터(B)",
        f"제품명: {a['product_name']}",
        f"포지셔닝: {a['positioning']}",
        "",
        "[EVALUATE]",
        "Company / Cost / Manufacturing / Customer / Repurchase",
        "",
        "[OUTPUT JSON]",
        "{",
        "  \"scores\": {",
        "    \"company_fit\": 1,",
        "    \"cost_stability\": 1,",
        "    \"manufacturability\": 1,",
        "    \"customer_acceptance\": 1,",
        "    \"repurchase\": 1",
        "  },",
        "  \"weighted_score\": 0.0,",
        "  \"decision\": \"GO|HOLD|DROP\"",
        "}",
    ])


def persona_C_prompt(context: Dict[str, Any]) -> str:
    return build_prompt([
        "[ROLE] 20년차 음료개발 연구원(C)",
        f"제품유형: {context['product_type']}",
        f"제품종류: {context['product_category']}",
        f"판매가: {context['price']}",
        "",
        "[TASK]",
        "- 표준배합비",
        "- 연구원 배합비",
        "- 관능 A/B 배합비",
        "",
        "[OUTPUT JSON]",
        "{",
        "  \"standard_formula\": { ... },",
        "  \"r_and_d_formula\": { ... },",
        "  \"sensory_A\": { ... },",
        "  \"sensory_B\": { ... }",
        "}",
    ])


# ============================================================
# 4. Streamlit UI (safe import)
# ============================================================

def run_streamlit():
    import streamlit as st
    from openai import OpenAI

    st.set_page_config(page_title="ABC Persona Training", layout="wide")
    st.title("ABC 페르소나 순환형 제품개발 교육앱")

    api_key = st.secrets.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    if "A" not in st.session_state:
        st.session_state.A = None
        st.session_state.B = None
        st.session_state.C = None

    st.header("0. 사전 기획")
    launch_date = st.text_input("출시 목표일")
    market_env = st.text_area("시장환경")
    trends = st.multiselect("트렌드", ["웰빙", "뉴니스", "차별화", "기능성"])

    if st.button("AI 실행"):
        with st.status("AI가 생각중입니다…"):
            a_prompt = persona_A_prompt({
                "launch_date": launch_date,
                "market_env": market_env,
                "trends": trends,
                "target_20f": "운동 좋아함",
                "target_30m": "미혼·건강중시",
            })
            a = client.responses.create(model="o4-mini", input=a_prompt).output_text
            st.session_state.A = a

    st.subheader("A 결과")
    st.code(st.session_state.A or "아직 없음")


# ============================================================
# 5. Entrypoint
# ============================================================

def main():
    try:
        import streamlit  # noqa
    except ModuleNotFoundError:
        print("streamlit not installed")
        return

    run_streamlit()


if __name__ == "__main__":
    main()

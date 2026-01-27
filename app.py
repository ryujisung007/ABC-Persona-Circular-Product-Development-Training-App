"""ABC Persona Circular Product Development Training App (AI-driven)

교육용 목표
- 신입사원 교육용: 오류(크래시) 최소화 + 화면은 충분히 풍부
- Stage 0 → A → B → C 페르소나가 '정의된 스크립트'에 따라 모두 AI로 동작
- AI가 작동할 때는 "AI가 생각중입니다…" 프로그레스 시그널 표시

실행 방법(로컬)
  pip install streamlit pandas openai
  streamlit run app.py

Streamlit Secrets
  OPENAI_API_KEY = "sk-..."
  (선택) OPENAI_MODEL = "o4-mini"  # 기본값 사용 가능

Self-test (Streamlit 없이도 실행 가능)
  python app.py --self-test

주의
- 본 앱은 교육용으로, 외부 웹 스크래핑(구글 검색)을 코드로 직접 수행하지 않습니다.
  대신 AI에게 '산업 관행(표준 레시피)' 기반의 표준배합비를 생성하도록 요청합니다.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple


Decision = Literal["GO", "HOLD", "DROP"]


# =========================
# Pure business logic (testable)
# =========================

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
    weights: BScoreWeights = BScoreWeights(),
) -> float:
    """Weighted marketing score. Inputs must be ints in [1,5]."""
    for name, v in [
        ("company_fit", company_fit),
        ("cost_stability", cost_stability),
        ("manufacturability", manufacturability),
        ("customer_acceptance", customer_acceptance),
        ("repurchase", repurchase),
    ]:
        if not isinstance(v, int):
            raise TypeError(f"{name} must be int")
        if v < 1 or v > 5:
            raise ValueError(f"{name} must be in [1,5]")

    score = (
        company_fit * weights.company_fit
        + cost_stability * weights.cost_stability
        + manufacturability * weights.manufacturability
        + customer_acceptance * weights.customer_acceptance
        + repurchase * weights.repurchase
    )
    return round(float(score), 2)


def decision_from_score(score: float, go_threshold: float = 3.2, hold_threshold: float = 3.0) -> Decision:
    if score >= go_threshold:
        return "GO"
    if score >= hold_threshold:
        return "HOLD"
    return "DROP"


# =========================
# Helpers
# =========================

def sanitize_lines(text: str) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r"^[-*•]+\s+", "", s).strip()
        if s:
            out.append(s)
    return out


def safe_json_loads(text: str) -> Dict[str, Any]:
    """Best-effort JSON parsing (handles extra prose around JSON)."""
    try:
        return json.loads(text)
    except Exception:
        # Try to find the first JSON object
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        return json.loads(m.group(0))


def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return ""
    return f"{v:.2f}%"


def fmt_gpl(v: Optional[float]) -> str:
    if v is None:
        return ""
    return f"{v:.2f} g/L"


def ingredient_schema() -> List[Tuple[str, str, str]]:
    """(key, label, unit)"""
    return [
        ("water", "정제수", "qs"),
        ("orange_juice", "오렌지주스(농축환원)", "%"),
        ("sugar", "설탕(자당)", "%"),
        ("glucose_syrup", "포도당시럽(DE42)", "%"),
        ("citric_acid", "구연산", "%"),
        ("malic_acid", "말산", "%"),
        ("flavor", "오렌지 향료", "%"),
        ("cloud", "클라우드 시스템", "%"),
        ("co2", "CO₂", "g/L"),
    ]


def default_researcher_formula() -> Dict[str, float]:
    return {
        "orange_juice": 3.8,
        "sugar": 5.2,
        "glucose_syrup": 0.3,
        "citric_acid": 0.24,
        "malic_acid": 0.03,
        "flavor": 0.045,
        "cloud": 0.09,
        "co2": 4.0,
    }


# =========================
# OpenAI / AI Personas
# =========================

def get_openai_key_from_streamlit_or_env(st: Optional[Any] = None) -> Optional[str]:
    # Streamlit secrets first
    if st is not None:
        try:
            v = st.secrets.get("OPENAI_API_KEY", None)
            if v:
                return str(v)
        except Exception:
            pass
    # Then environment variable
    return os.environ.get("OPENAI_API_KEY")


def get_openai_model_from_streamlit_or_env(st: Optional[Any] = None) -> str:
    if st is not None:
        try:
            m = st.secrets.get("OPENAI_MODEL", None)
            if m:
                return str(m)
        except Exception:
            pass
    return os.environ.get("OPENAI_MODEL", "o4-mini")


def call_openai_json(model: str, api_key: str, system: str, user: str, timeout_note: str = "") -> Dict[str, Any]:
    """Call OpenAI Responses API and return parsed JSON."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = resp.output_text
    return safe_json_loads(text)


def persona_A(system_style: str = "") -> str:
    return (
        "당신은 식품기획자(A) 페르소나입니다.\n"
        "목표: 입력(출시일/시장환경/트렌드/타깃)을 바탕으로 제품 컨셉을 1개로 수렴합니다.\n"
        "원칙: (1) 관능 중심, (2) 소비자 언어, (3) 차별화 1문장, (4) 마케팅 포인트 3개.\n"
        "출력은 반드시 JSON만 반환합니다." + ("\n" + system_style if system_style else "")
    )


def persona_B(system_style: str = "") -> str:
    return (
        "당신은 식품음료 마케터(B) 페르소나입니다.\n"
        "목표: A의 컨셉(제품명/포지셔닝/마케팅포인트)을 3C·SWOT 관점으로 검증하고 점수화합니다.\n"
        "주의: 실행가능성(원가/제조/채널/반복구매)을 최우선으로 평가합니다.\n"
        "출력은 반드시 JSON만 반환합니다." + ("\n" + system_style if system_style else "")
    )


def persona_C(system_style: str = "") -> str:
    return (
        "당신은 20년차 음료 전문 개발연구원(C) 페르소나입니다(마케팅 근무 5년 포함).\n"
        "목표: A/B 결과를 관능·색상·상품성·차별화 중심으로 배합비로 구현합니다.\n"
        "필수: (1) 표준배합비(업계 관행 기반)와 비교, (2) 연구원 배합비, (3) 관능특성 A/B 대안 배합비 제시.\n"
        "출력은 반드시 JSON만 반환합니다." + ("\n" + system_style if system_style else "")
    )


def stage0_to_A_payload(
    launch_date: str,
    market_env: str,
    trends: List[str],
    target_20f: str,
    target_30m: str,
    packaging: str,
    season_note: str,
) -> str:
    return (
        "[입력값]\n"
        f"- 출시 목표일: {launch_date}\n"
        f"- 시장환경(키워드/문장):\n{market_env}\n"
        f"- 주요 트렌드: {', '.join(trends)}\n"
        f"- 타깃 20대 여성: {target_20f}\n"
        f"- 타깃 30대 남성: {target_30m}\n"
        f"- 패키징 제약: {packaging}\n"
        f"- 시즌/출시 맥락: {season_note}\n\n"
        "[요구]\n"
        "다음을 만족하는 제품 컨셉 1개를 제시하세요.\n"
        "- 제품명(짧게, 한국어)\n"
        "- 포지셔닝 1문장\n"
        "- 핵심 관능 키워드 3~5개(영어)\n"
        "- 마케팅 포인트 3개(한국어)\n"
        "- 리스크 2개 및 회피전략 2개\n\n"
        "[출력 JSON 스키마]\n"
        "{\n"
        "  \"product_name\": \"...\",\n"
        "  \"positioning\": \"...\",\n"
        "  \"sensory_keywords\": [\"...\"],\n"
        "  \"marketing_points\": [\"...\"],\n"
        "  \"risks\": [\"...\"],\n"
        "  \"mitigations\": [\"...\"]\n"
        "}\n"
    )


def A_to_B_payload(a: Dict[str, Any]) -> str:
    return (
        "[A 컨셉안]\n"
        f"- 제품명: {a.get('product_name','')}\n"
        f"- 포지셔닝: {a.get('positioning','')}\n"
        f"- 관능키워드: {', '.join(a.get('sensory_keywords', []))}\n"
        f"- 마케팅포인트: {', '.join(a.get('marketing_points', []))}\n\n"
        "[요구]\n"
        "3C·SWOT 관점으로 평가하고 아래 평가항목을 1~5점으로 채점 후 가중치로 종합점수 산출.\n"
        "- Company 적합성(0.2)\n"
        "- 원가 안정성(0.2)\n"
        "- 제조 난이도(0.15)\n"
        "- Customer 수용성(0.15)\n"
        "- 반복구매 가능성(0.2)\n"
        "결과로 GO/HOLD/DROP 판정 및 개선 코멘트 3개.\n\n"
        "[출력 JSON 스키마]\n"
        "{\n"
        "  \"scores\": {\"company_fit\":1,\"cost_stability\":1,\"manufacturability\":1,\"customer_acceptance\":1,\"repurchase\":1},\n"
        "  \"weighted_score\": 0.0,\n"
        "  \"decision\": \"GO|HOLD|DROP\",\n"
        "  \"3c_swot_summary\": {\"3c\": {\"company\":\"...\",\"customer\":\"...\",\"competitor\":\"...\"}, \"swot\": {\"strengths\":[\"...\"], \"weaknesses\":[\"...\"], \"opportunities\":[\"...\"], \"threats\":[\"...\"]}},\n"
        "  \"improvement_comments\": [\"...\"]\n"
        "}\n"
    ) -> str:
    return (
        "[컨텍스트]\n"
        f"- 제품유형: {product_type}\n"
        f"- 제품종류: {product_category}\n"
        f"- 패키지: {packaging}\n"
        f"- 판매가: {price}\n\n"
        "[A 컨셉]\n"
        f"- 제품명: {a.get('product_name','')}\n"
        f"- 포지셔닝: {a.get('positioning','')}\n"
        f"- 관능키워드: {', '.join(a.get('sensory_keywords', []))}\n"
        f"- 마케팅포인트: {', '.join(a.get('marketing_points', []))}\n\n"
        "[B 검증]\n"
        f"- 종합점수: {b.get('weighted_score','')}\n"
        f"- 판정: {b.get('decision','')}\n"
        f"- 개선코멘트: {', '.join(b.get('improvement_comments', []))}\n\n"
        "[요구]\n"
        "업계 관행(표준) 기반의 '표준배합비'와 이를 기반으로 A/B를 만족하는 '연구원 배합비'를 제시하세요.\n"
        "또한 관능특성 A(산미/탄산 강조)와 관능특성 B(주스감/바디 강조) 대안 배합비를 각각 제시하세요.\n"
        "원료는 아래 키만 사용하세요(누락 금지, 값은 숫자, 단위는 키에 내재).\n"
        "- orange_juice(%) sugar(%) glucose_syrup(%) citric_acid(%) malic_acid(%) flavor(%) cloud(%) co2(g/L)\n"
        "water는 q.s.로 처리하므로 JSON에 포함하지 마세요.\n\n"
        "[출력 JSON 스키마]\n"
        "{\n"
        "  \"standard_formula\": {\"orange_juice\":0.0,\"sugar\":0.0,\"glucose_syrup\":0.0,\"citric_acid\":0.0,\"malic_acid\":0.0,\"flavor\":0.0,\"cloud\":0.0,\"co2\":0.0},\n"
        "  \"r_and_d_formula\": {\"orange_juice\":0.0,\"sugar\":0.0,\"glucose_syrup\":0.0,\"citric_acid\":0.0,\"malic_acid\":0.0,\"flavor\":0.0,\"cloud\":0.0,\"co2\":0.0},\n"
        "  \"sensory_A\": {\"label\":\"Sharp & Active\", \"formula\": { ...same keys... }},\n"
        "  \"sensory_B\": {\"label\":\"Juicy & Smooth\", \"formula\": { ...same keys... }},\n"
        "  \"commentary\": \"...관능/색상/상품성 관점 코멘트...\"\n"
        "}\n"
    )


def C_recommend_from_researcher_payload(
    product_type: str,
    product_category: str,
    a: Dict[str, Any],
    b: Dict[str, Any],
    researcher: Dict[str, float],
) -> str:
    return (
        "[컨텍스트]\n"
        f"- 제품유형: {product_type}\n"
        f"- 제품종류: {product_category}\n\n"
        "[A/B 요약]\n"
        f"- A 제품명: {a.get('product_name','')}\n"
        f"- A 포지셔닝: {a.get('positioning','')}\n"
        f"- B 코멘트: {', '.join(b.get('improvement_comments', []))}\n\n"
        "[연구원 배합비(현재 슬라이더 값)]\n"
        + json.dumps(researcher, ensure_ascii=False)
        + "\n\n"
        "[요구]\n"
        "연구원 배합비를 기준으로 관능특성 A/B 대안 배합비를 다시 제안하세요.\n"
        "원료 키는 동일. water는 제외.\n\n"
        "[출력 JSON 스키마]\n"
        "{\n"
        "  \"sensory_A\": {\"label\":\"Sharp & Active\", \"formula\": { ...same keys... }},\n"
        "  \"sensory_B\": {\"label\":\"Juicy & Smooth\", \"formula\": { ...same keys... }},\n"
        "  \"commentary\": \"...\"\n"
        "}\n"
    )


# =========================
# Table builder
# =========================

def normalize_formula(d: Dict[str, Any]) -> Dict[str, float]:
    keys = [
        "orange_juice",
        "sugar",
        "glucose_syrup",
        "citric_acid",
        "malic_acid",
        "flavor",
        "cloud",
        "co2",
    ]
    out: Dict[str, float] = {}
    for k in keys:
        v = d.get(k, 0.0)
        try:
            out[k] = float(v)
        except Exception:
            out[k] = 0.0
    return out


def build_formula_table(
    product_name: str,
    standard: Dict[str, float],
    researcher: Dict[str, float],
    sensory_a: Dict[str, float],
    sensory_b: Dict[str, float],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    schema = ingredient_schema()

    def val_for(unit: str, key: str, source: Dict[str, float]) -> str:
        if key == "water":
            return "q.s."  # water is always q.s.
        if key not in source:
            return ""
        v = source[key]
        if unit == "%":
            return fmt_pct(v)
        if unit == "g/L":
            return fmt_gpl(v)
        return str(v)

    for key, label, unit in schema:
        row = {
            "원재료": label,
            "제품명": product_name if key == "water" else "",
            "표준배합비 (AI 추천)": val_for(unit, key, standard),
            "연구원 작성배합비": val_for(unit, key, researcher),
            "관능특성 A 추천배합비": val_for(unit, key, sensory_a),
            "관능특성 B 추천배합비": val_for(unit, key, sensory_b),
        }
        rows.append(row)
    return rows


# =========================
# Streamlit UI
# =========================

def run_streamlit_app() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="ABC Product Development (AI Personas)", layout="wide")

    st.title("🥤 ABC 페르소나 기반 제품개발 교육용 시뮬레이터")
    st.caption("Stage 0 → A(기획) → B(마케팅) → C(배합) : 정의된 스크립트에 따라 AI가 자동 구동")

    if "cycle" not in st.session_state:
        st.session_state.cycle = {}

    api_key = get_openai_key_from_streamlit_or_env(st)
    model = get_openai_model_from_streamlit_or_env(st)

    with st.sidebar:
        st.header("⚙️ 실행 설정")
        st.write(f"모델: `{model}`")
        st.write("API Key: " + ("✅ 설정됨" if api_key else "❌ 없음(템플릿/수동 모드)"))
        st.markdown("---")
        chapter = st.radio(
            "📘 챕터",
            ["00. 사전 기획(Stage 0)", "01. A(제품기획)", "02. B(마케팅검증)", "03. C(배합비개발)", "04. 요약/내보내기"],
        )

    # -------------------------
    # Stage 0
    # -------------------------
    if chapter == "00. 사전 기획(Stage 0)":
        st.header("0) 사전 기획 – 입력값 정의 & AI 컨셉 도출")

        col1, col2 = st.columns(2)
        with col1:
            launch_date = st.date_input("1. 제품 출시 목표일")
            market_env = st.text_area(
                "2. 시장환경(인구/사회/경제)",
                placeholder="예)\n- 고물가 지속\n- 20대 1인가구 증가\n- 헬스·운동 인구 확산",
                height=140,
            )

        with col2:
            trends = st.multiselect(
                "3. 주요 트렌드",
                ["웰빙", "새로운맛", "뉴니스", "차별화", "기능성"],
                default=["새로운맛", "차별화"],
            )
            st.caption("교육용: 구글 스크래핑은 직접 수행하지 않고, AI가 산업 관행을 기반으로 해석합니다.")

        st.markdown("---")
        st.subheader("타깃/제약조건")
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            target_20f = st.text_input(
                "주요 소비층 1 (20대 여성)",
                "운동을 좋아하고 사회생활 초년생",
            )
            packaging = st.text_input(
                "패키지 제약",
                "친환경 포장소재 선호 (예: rPET, 라벨/잉크 최소화)",
            )

        with tcol2:
            target_30m = st.text_input(
                "주요 소비층 2 (30대 남성)",
                "여행을 좋아하고 미혼, 건강 위해 지출을 아끼지 않음",
            )
            season_note = st.text_input(
                "시즌/출시 맥락(메모)",
                "5월 출시(초여름 진입), 상큼·리프레시 수요",
            )

        st.markdown("---")
        st.subheader("AI 실행")

        if st.button("AI로 A→B→C 전체 사이클 실행", type="primary"):
            launch_str = launch_date.isoformat() if launch_date else ""

            if not api_key:
                st.error("OPENAI_API_KEY가 설정되어 있지 않습니다. Streamlit secrets에 넣어주세요.")
            else:
                with st.status("🤖 AI가 생각중입니다…", expanded=True) as status:
                    try:
                        status.write("Stage 0 입력값을 정리합니다…")

                        # A
                        status.write("A 페르소나: 제품 컨셉/제품명/마케팅포인트를 도출합니다…")
                        a_json = call_openai_json(
                            model=model,
                            api_key=api_key,
                            system=persona_A(),
                            user=stage0_to_A_payload(
                                launch_date=launch_str,
                                market_env=market_env,
                                trends=trends,
                                target_20f=target_20f,
                                target_30m=target_30m,
                                packaging=packaging,
                                season_note=season_note,
                            ),
                        )

                        # B
                        status.write("B 페르소나: 3C·SWOT 검증 및 점수화를 수행합니다…")
                        b_json = call_openai_json(
                            model=model,
                            api_key=api_key,
                            system=persona_B(),
                            user=A_to_B_payload(a_json),
                        )

                        # C (requires product type/category)
                        status.write("C 페르소나: 표준배합비/연구원배합비/관능 A/B 배합비를 제시합니다…")

                        # default type/category for this training app
                        product_type = "탄산음료"
                        product_category = "오렌지 탄산음료"
                        price = "1500원"

                        c_json = call_openai_json(
                            model=model,
                            api_key=api_key,
                            system=persona_C(),
                            user=B_to_C_payload(
                                a=a_json,
                                b=b_json,
                                product_type=product_type,
                                product_category=product_category,
                                packaging=packaging,
                                price=price,
                            ),
                        )

                        st.session_state.cycle = {
                            "stage0": {
                                "launch_date": launch_str,
                                "market_env": sanitize_lines(market_env),
                                "trends": trends,
                                "targets": {"20f": target_20f, "30m": target_30m},
                                "packaging": packaging,
                                "season_note": season_note,
                            },
                            "A": a_json,
                            "B": b_json,
                            "C": c_json,
                            "C_product": {
                                "product_type": product_type,
                                "product_category": product_category,
                                "price": price,
                            },
                            "researcher_formula": normalize_formula(default_researcher_formula()),
                        }

                        status.update(label="✅ AI 사이클 완료", state="complete", expanded=False)
                        st.success("AI 사이클 실행이 완료되었습니다. 사이드바에서 A/B/C 단계로 이동하세요.")

                    except Exception as e:
                        status.update(label="❌ AI 실행 실패", state="error", expanded=True)
                        st.exception(e)

        # Preview current concept if exists
        if st.session_state.cycle.get("A"):
            st.markdown("---")
            st.subheader("현재 도출된 컨셉(미리보기)")
            st.write(f"**제품명:** {st.session_state.cycle['A'].get('product_name','')}")
            st.write(f"**포지셔닝:** {st.session_state.cycle['A'].get('positioning','')}")
            st.write("**마케팅 포인트:**")
            for p in st.session_state.cycle['A'].get('marketing_points', []):
                st.write(f"- {p}")

    # -------------------------
    # Stage A
    # -------------------------
    elif chapter == "01. A(제품기획)":
        st.header("1) A 페르소나 – AI 제품컨셉기획")

        if not st.session_state.cycle.get("A"):
            st.warning("먼저 Stage 0에서 'AI로 전체 사이클 실행'을 수행하세요.")
        else:
            a = st.session_state.cycle["A"]
            st.subheader("A 산출물")
            st.write(f"**제품명:** {a.get('product_name','')}")
            st.write(f"**포지셔닝:** {a.get('positioning','')}")

            c1, c2 = st.columns(2)
            with c1:
                st.write("**관능 키워드**")
                for k in a.get("sensory_keywords", []):
                    st.write(f"- {k}")

            with c2:
                st.write("**마케팅 포인트(3)**")
                for p in a.get("marketing_points", []):
                    st.write(f"- {p}")

            st.write("**리스크/회피전략**")
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                for r in a.get("risks", []):
                    st.write(f"- (리스크) {r}")
            with rcol2:
                for m in a.get("mitigations", []):
                    st.write(f"- (회피) {m}")

    # -------------------------
    # Stage B
    # -------------------------
    elif chapter == "02. B(마케팅검증)":
        st.header("2) B 페르소나 – AI 마케팅 검증")

        if not st.session_state.cycle.get("B"):
            st.warning("먼저 Stage 0에서 AI 사이클을 실행하세요.")
        else:
            b = st.session_state.cycle["B"]
            st.subheader("평가 결과")
            st.write(f"**판정:** {b.get('decision','')}")
            st.write(f"**가중 종합점수:** {b.get('weighted_score','')} (참고: 가중치 합 0.90)")

            scores = b.get("scores", {})
            # If AI didn't compute weighted score reliably, compute locally
            try:
                local_score = compute_b_score(
                    int(scores.get("company_fit", 3)),
                    int(scores.get("cost_stability", 3)),
                    int(scores.get("manufacturability", 3)),
                    int(scores.get("customer_acceptance", 3)),
                    int(scores.get("repurchase", 3)),
                )
            except Exception:
                local_score = None

            col1, col2 = st.columns(2)
            with col1:
                st.write("**항목별 점수(1~5)**")
                for k, v in scores.items():
                    st.write(f"- {k}: {v}")
            with col2:
                if local_score is not None:
                    st.info(f"로컬 재계산 종합점수: {local_score}")

            st.markdown("---")
            st.subheader("3C·SWOT 요약")
            s = b.get("3c_swot_summary", {})
            c3 = s.get("3c", {})
            sw = s.get("swot", {})
            ccol1, ccol2 = st.columns(2)
            with ccol1:
                st.write("**3C**")
                st.write(f"- Company: {c3.get('company','')}")
                st.write(f"- Customer: {c3.get('customer','')}")
                st.write(f"- Competitor: {c3.get('competitor','')}")
            with ccol2:
                st.write("**SWOT**")
                st.write(f"- Strengths: {', '.join(sw.get('strengths', []))}")
                st.write(f"- Weaknesses: {', '.join(sw.get('weaknesses', []))}")
                st.write(f"- Opportunities: {', '.join(sw.get('opportunities', []))}")
                st.write(f"- Threats: {', '.join(sw.get('threats', []))}")

            st.markdown("---")
            st.subheader("개선 코멘트")
            for c in b.get("improvement_comments", []):
                st.write(f"- {c}")

    # -------------------------
    # Stage C
    # -------------------------
    else:
        import pandas as pd
        import streamlit as st

        if chapter == "03. C(배합비개발)":
            st.header("3) C 페르소나 – AI 배합비 개발 대시보드")

            if not (st.session_state.cycle.get("A") and st.session_state.cycle.get("B")):
                st.warning("먼저 Stage 0에서 AI 사이클을 실행하세요.")
            else:
                a = st.session_state.cycle.get("A", {})
                b = st.session_state.cycle.get("B", {})

                # Product type/category selectors
                st.subheader("제품 타입 설정")
                c1, c2, c3 = st.columns(3)
                with c1:
                    product_type = st.selectbox("제품 유형", ["탄산음료", "비탄산 음료", "기능성 음료", "에너지 드링크"], index=0)
                with c2:
                    product_category = st.selectbox(
                        "제품 종류",
                        ["오렌지 탄산음료", "레몬라임 탄산", "과즙 스파클링", "기능성 스파클링"],
                        index=0,
                    )
                with c3:
                    price = st.text_input("판매가", st.session_state.cycle.get("C_product", {}).get("price", "1500원"))

                st.session_state.cycle["C_product"] = {
                    "product_type": product_type,
                    "product_category": product_category,
                    "price": price,
                }

                st.markdown("---")
                st.subheader("연구원 배합비(슬라이더) – 이 값이 표의 '연구원 작성배합비'를 실시간 갱신")

                # Initialize researcher formula state
                if "researcher_formula" not in st.session_state.cycle:
                    st.session_state.cycle["researcher_formula"] = normalize_formula(default_researcher_formula())

                rf = dict(st.session_state.cycle["researcher_formula"])

                s1, s2, s3, s4 = st.columns(4)
                with s1:
                    rf["orange_juice"] = st.slider("오렌지 주스(%)", 0.5, 8.0, float(rf.get("orange_juice", 3.8)), 0.1)
                    rf["sugar"] = st.slider("설탕(%)", 1.0, 12.0, float(rf.get("sugar", 5.2)), 0.1)
                with s2:
                    rf["glucose_syrup"] = st.slider("포도당시럽(%)", 0.0, 3.0, float(rf.get("glucose_syrup", 0.3)), 0.05)
                    rf["citric_acid"] = st.slider("구연산(%)", 0.05, 0.40, float(rf.get("citric_acid", 0.24)), 0.01)
                with s3:
                    rf["malic_acid"] = st.slider("말산(%)", 0.0, 0.12, float(rf.get("malic_acid", 0.03)), 0.005)
                    rf["flavor"] = st.slider("향료(%)", 0.0, 0.15, float(rf.get("flavor", 0.045)), 0.005)
                with s4:
                    rf["cloud"] = st.slider("클라우드(%)", 0.0, 0.25, float(rf.get("cloud", 0.09)), 0.01)
                    rf["co2"] = st.slider("CO₂ (g/L)", 2.0, 5.0, float(rf.get("co2", 4.0)), 0.1)

                st.session_state.cycle["researcher_formula"] = normalize_formula(rf)

                st.markdown("---")
                left, right = st.columns([1.2, 1])

                with left:
                    st.subheader("배합비 비교표")
                    # Ensure we have C base recommendations; if absent, ask AI to generate
                    if "C" not in st.session_state.cycle:
                        st.info("C 표준/대안 배합비가 없습니다. 아래 버튼으로 생성하세요.")

                    if st.button("AI로 표준배합비/대안배합비 생성(제품 타입 반영)"):
                        if not api_key:
                            st.error("OPENAI_API_KEY가 설정되어 있지 않습니다.")
                        else:
                            with st.status("🤖 AI가 생각중입니다…", expanded=True) as status:
                                try:
                                    status.write("C 페르소나: 업계 표준배합비와 비교안을 생성합니다…")
                                    c_json = call_openai_json(
                                        model=model,
                                        api_key=api_key,
                                        system=persona_C(),
                                        user=B_to_C_payload(
                                            a=a,
                                            b=b,
                                            product_type=product_type,
                                            product_category=product_category,
                                            packaging=st.session_state.cycle.get("stage0", {}).get("packaging", "PET"),
                                            price=price,
                                        ),
                                    )
                                    st.session_state.cycle["C"] = c_json
                                    status.update(label="✅ 생성 완료", state="complete", expanded=False)
                                except Exception as e:
                                    status.update(label="❌ 생성 실패", state="error", expanded=True)
                                    st.exception(e)

                    c_json = st.session_state.cycle.get("C", {})
                    standard = normalize_formula(c_json.get("standard_formula", {}))
                    # r_and_d_formula from AI is a suggestion, but our 'researcher' column is slider-driven.
                    researcher = normalize_formula(st.session_state.cycle.get("researcher_formula", default_researcher_formula()))
                    sA = normalize_formula((c_json.get("sensory_A", {}) or {}).get("formula", {}))
                    sB = normalize_formula((c_json.get("sensory_B", {}) or {}).get("formula", {}))

                    product_name = a.get("product_name", "제품") or "제품"

                    table_rows = build_formula_table(
                        product_name=product_name,
                        standard=standard,
                        researcher=researcher,
                        sensory_a=sA,
                        sensory_b=sB,
                    )
                    df = pd.DataFrame(table_rows)
                    st.dataframe(df, use_container_width=True, height=420)

                    # Download
                    st.download_button(
                        "배합비 비교표 CSV 다운로드",
                        data=df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="formulation_compare.csv",
                        mime="text/csv",
                    )

                with right:
                    st.subheader("관능 A/B 재추천 (슬라이더 연동)")
                    st.caption("연구원 배합비(슬라이더)가 바뀌면, 버튼을 눌러 A/B 대안 배합비를 AI가 재계산합니다.")

                    if st.button("AI로 관능 A/B 재추천"):
                        if not api_key:
                            st.error("OPENAI_API_KEY가 설정되어 있지 않습니다.")
                        else:
                            with st.status("🤖 AI가 생각중입니다…", expanded=True) as status:
                                try:
                                    status.write("C 페르소나: 현재 연구원 배합비를 기준으로 관능 A/B 대안을 재계산합니다…")
                                    rec = call_openai_json(
                                        model=model,
                                        api_key=api_key,
                                        system=persona_C(),
                                        user=C_recommend_from_researcher_payload(
                                            product_type=product_type,
                                            product_category=product_category,
                                            a=a,
                                            b=b,
                                            researcher=normalize_formula(st.session_state.cycle["researcher_formula"]),
                                        ),
                                    )
                                    # merge back into C
                                    c_prev = st.session_state.cycle.get("C", {})
                                    c_prev["sensory_A"] = rec.get("sensory_A", c_prev.get("sensory_A"))
                                    c_prev["sensory_B"] = rec.get("sensory_B", c_prev.get("sensory_B"))
                                    if rec.get("commentary"):
                                        c_prev["commentary"] = rec.get("commentary")
                                    st.session_state.cycle["C"] = c_prev
                                    status.update(label="✅ 재추천 완료", state="complete", expanded=False)
                                except Exception as e:
                                    status.update(label="❌ 재추천 실패", state="error", expanded=True)
                                    st.exception(e)

                    st.markdown("---")
                    st.subheader("C 코멘트")
                    c_json = st.session_state.cycle.get("C", {})
                    commentary = c_json.get("commentary", "")
                    if commentary:
                        st.info(commentary)
                    else:
                        st.write("(코멘트가 아직 없습니다. 'AI로 표준배합비/대안배합비 생성'을 실행하세요.)")

        elif chapter == "04. 요약/내보내기":
            st.header("4) 요약/내보내기")
            if not st.session_state.cycle:
                st.warning("아직 실행된 데이터가 없습니다. Stage 0에서 AI 사이클을 실행하세요.")
            else:
                st.subheader("전체 상태")
                st.json(st.session_state.cycle)

                # Compact export
                a = st.session_state.cycle.get("A", {})
                b = st.session_state.cycle.get("B", {})
                c = st.session_state.cycle.get("C", {})
                prod = st.session_state.cycle.get("C_product", {})

                export = {
                    "stage0": st.session_state.cycle.get("stage0", {}),
                    "A": a,
                    "B": b,
                    "C_product": prod,
                    "C": c,
                    "researcher_formula": st.session_state.cycle.get("researcher_formula", {}),
                }

                st.download_button(
                    "전체 결과 JSON 다운로드",
                    data=json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name="abc_cycle_result.json",
                    mime="application/json",
                )


# =========================
# Self tests (no Streamlit required)
# =========================

def _self_test() -> None:
    # B score
    assert compute_b_score(3, 3, 4, 4, 4) == 3.2
    assert decision_from_score(3.2) == "GO"
    assert decision_from_score(3.0) == "HOLD"
    assert decision_from_score(2.9) == "DROP"

    # sanitize
    assert sanitize_lines("- a\n\n• b\n* c") == ["a", "b", "c"]

    # json parser
    d = safe_json_loads('{"a":1}')
    assert d["a"] == 1
    d2 = safe_json_loads('hello\n{"a":2}\nbye')
    assert d2["a"] == 2

    # table
    product = "테스트"
    standard = normalize_formula({"orange_juice": 2, "sugar": 9, "co2": 2.7})
    researcher = normalize_formula(default_researcher_formula())
    sA = normalize_formula({"orange_juice": 3.5, "sugar": 5.0, "co2": 4.2})
    sB = normalize_formula({"orange_juice": 4.5, "sugar": 6.0, "co2": 3.8})
    rows = build_formula_table(product, standard, researcher, sA, sB)
    assert rows[0]["원재료"] == "정제수"
    assert rows[0]["표준배합비 (AI 추천)"] == "q.s."


def main(argv: List[str]) -> int:
    if "--self-test" in argv:
        _self_test()
        print("Self-test passed")
        return 0

    # Streamlit is required to run UI
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        print(
            "ERROR: 'streamlit' is not installed in this environment.\n\n"
            "To run locally:\n  pip install streamlit pandas openai\n  streamlit run app.py\n"
        )
        return 1

    run_streamlit_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

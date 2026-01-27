# app.py
# ============================================================
# ABC Persona Circular Product Development Training App (v1.0)
# - Left: step selection + inputs
# - Right: outputs dashboard
# - Includes STEP -1 (사전기획) before giving concept to A
# - Single OpenAI call ONLY at STEP 0 (A/B/C are returned together)
# - C formulation dashboard: standard vs researcher vs sensory A/B
# - RateLimit-safe: cache by input hash + exponential backoff
# - String-safe for GitHub: NO multiline string literals; prompts use "\n".join(list)
# ============================================================

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple


Decision = Literal["GO", "HOLD", "DROP"]


# =========================
# 1) Core business logic (testable)
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
    return round(float(score), 2)


def decision_from_score(score: float, go_th: float = 3.2, hold_th: float = 3.0) -> Decision:
    if score >= go_th:
        return "GO"
    if score >= hold_th:
        return "HOLD"
    return "DROP"


# =========================
# 2) Utilities (string-safe)
# =========================


def build_prompt(lines: List[str]) -> str:
    return "\n".join(lines)


def safe_json_loads(text: str) -> Dict[str, Any]:
    # Best-effort JSON extraction
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output")
    try:
        return json.loads(text)
    except Exception:
        # extract first JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def sha_key(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def clamp_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def clamp_int(x: Any, default: int = 3) -> int:
    try:
        v = int(x)
        return v
    except Exception:
        return int(default)


def fmt_pct(v: float) -> str:
    return f"{v:.2f}%"


def fmt_gpl(v: float) -> str:
    return f"{v:.2f} g/L"


# =========================
# 3) Formulation schema
# =========================


def ingredient_schema() -> List[Tuple[str, str, str]]:
    # key, label, unit
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
        out[k] = clamp_float(d.get(k, 0.0), 0.0)
    return out


def default_researcher_formula() -> Dict[str, float]:
    # baseline for orange sparkling
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


def build_formula_table(
    product_name: str,
    standard: Dict[str, float],
    researcher: Dict[str, float],
    sensory_a: Dict[str, float],
    sensory_b: Dict[str, float],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    def val(unit: str, key: str, src: Dict[str, float]) -> str:
        if key == "water":
            return "q.s."
        v = float(src.get(key, 0.0))
        if unit == "%":
            return fmt_pct(v)
        if unit == "g/L":
            return fmt_gpl(v)
        return str(v)

    for key, label, unit in ingredient_schema():
        row = {
            "원재료": label,
            "제품명": product_name if key == "water" else "",
            "표준배합비 (AI 추천)": val(unit, key, standard),
            "연구원 작성배합비": val(unit, key, researcher),
            "관능특성 A 추천배합비": val(unit, key, sensory_a),
            "관능특성 B 추천배합비": val(unit, key, sensory_b),
        }
        rows.append(row)
    return rows


# =========================
# 4) AI call (single call at STEP 0)
# =========================


def get_openai_key(st: Any) -> Optional[str]:
    try:
        v = st.secrets.get("OPENAI_API_KEY")
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY")


def get_openai_model(st: Any) -> str:
    try:
        m = st.secrets.get("OPENAI_MODEL")
        if m:
            return str(m)
    except Exception:
        pass
    return os.environ.get("OPENAI_MODEL", "o4-mini")


def ai_step0_prompt(stage_minus1: Dict[str, Any], stage0: Dict[str, Any]) -> str:
    # Prompt design to make outputs vary with different inputs
    # - Use higher temperature
    # - Force distinctiveness and require explicit input reflection
    # - Ask for ABC outputs in one JSON
    lines: List[str] = []
    lines.append("[SYSTEM]")
    lines.append("너는 하나의 AI이지만, A(기획) / B(마케팅) / C(개발) 페르소나를 순서대로 수행한다.")
    lines.append("실제 외부 검색은 하지 말고, 최근 2~3년 일반적인 시장 경향(구글검색/보도/트렌드리포트 수준)을 참고한 것처럼 사고하라.")
    lines.append("단, 특정 수치/출처를 단정하지 말고 '일반화된 경향' 형태로만 반영하라.")
    lines.append("같은 답을 반복하지 말고, 입력이 달라지면 반드시 다른 플레이버/포지셔닝/배합비 방향으로 바꿔라.")
    lines.append("출력은 반드시 JSON만 반환한다. JSON 이외의 텍스트 금지.")
    lines.append("")
    lines.append("[STEP -1: 사전 기획 정의]")
    lines.append(f"기획목적: {stage_minus1.get('goal','')}")
    lines.append(f"제품카테고리: {stage_minus1.get('category','')}")
    lines.append(f"가격대: {stage_minus1.get('price_tier','')}")
    lines.append(f"유통채널: {', '.join(stage_minus1.get('channels', []))}")
    lines.append(f"출시시즌: {stage_minus1.get('season','')}")
    lines.append("")
    lines.append("[STEP 0: 시장/트렌드 입력]")
    lines.append(f"출시목표일: {stage0.get('launch_date','')}")
    lines.append(f"시장환경(인구/사회/경제): {stage0.get('market_env','')}")
    lines.append(f"주요트렌드: {', '.join(stage0.get('trends', []))}")
    lines.append(f"타깃1: {stage0.get('target_20f','')}")
    lines.append(f"타깃2: {stage0.get('target_30m','')}")
    lines.append(f"패키지제약: {stage0.get('packaging','')}")
    lines.append("")
    lines.append("[요구사항]")
    lines.append("A: 제품 컨셉 1안 도출 (제품명/포지셔닝/관능키워드/마케팅포인트/리스크/대응)")
    lines.append("B: 마케팅 전략 검증 (3C·SWOT 요약 + 5개 항목 1~5점 제안 + 개선코멘트)")
    lines.append("C: 개발 방향 (표준배합비 + 관능A/B 대안배합비 + 코멘트). 단위: % 또는 g/L")
    lines.append("- 제품유형은 사전기획 카테고리를 우선 반영하되, 탄산/비탄산 여부를 명시")
    lines.append("- 배합비 원료키는 다음만 사용: orange_juice, sugar, glucose_syrup, citric_acid, malic_acid, flavor, cloud, co2")
    lines.append("")
    lines.append("[OUTPUT JSON SCHEMA]")
    lines.append("{")
    lines.append("  \"A\": {")
    lines.append("    \"product_name\": \"...\",")
    lines.append("    \"positioning\": \"...\",")
    lines.append("    \"sensory_keywords\": [\"Juicy\", \"Sharp\"],")
    lines.append("    \"marketing_points\": [\"...\"],")
    lines.append("    \"risks\": [\"...\"],")
    lines.append("    \"mitigations\": [\"...\"]")
    lines.append("  },")
    lines.append("  \"B\": {")
    lines.append("    \"scores\": {\"company_fit\": 3, \"cost_stability\": 3, \"manufacturability\": 3, \"customer_acceptance\": 3, \"repurchase\": 3},")
    lines.append("    \"3c\": {\"company\": \"...\", \"customer\": \"...\", \"competitor\": \"...\"},")
    lines.append("    \"swot\": {\"strengths\": [\"...\"], \"weaknesses\": [\"...\"], \"opportunities\": [\"...\"], \"threats\": [\"...\"]},")
    lines.append("    \"improvement_comments\": [\"...\"]")
    lines.append("  },")
    lines.append("  \"C\": {")
    lines.append("    \"product_type\": \"...\",")
    lines.append("    \"product_category\": \"...\",")
    lines.append("    \"standard_formula\": {\"orange_juice\": 0.0, \"sugar\": 0.0, \"glucose_syrup\": 0.0, \"citric_acid\": 0.0, \"malic_acid\": 0.0, \"flavor\": 0.0, \"cloud\": 0.0, \"co2\": 0.0},")
    lines.append("    \"sensory_A\": {\"label\": \"Sharp & Active\", \"formula\": {\"orange_juice\": 0.0, \"sugar\": 0.0, \"glucose_syrup\": 0.0, \"citric_acid\": 0.0, \"malic_acid\": 0.0, \"flavor\": 0.0, \"cloud\": 0.0, \"co2\": 0.0}},")
    lines.append("    \"sensory_B\": {\"label\": \"Juicy & Smooth\", \"formula\": {\"orange_juice\": 0.0, \"sugar\": 0.0, \"glucose_syrup\": 0.0, \"citric_acid\": 0.0, \"malic_acid\": 0.0, \"flavor\": 0.0, \"cloud\": 0.0, \"co2\": 0.0}},")
    lines.append("    \"commentary\": \"...\"")
    lines.append("  }")
    lines.append("}")
    return build_prompt(lines)


def call_openai_once(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.75,
    max_retries: int = 4,
    base_sleep: float = 1.2,
) -> Tuple[Dict[str, Any], float]:
    # Returns (json, elapsed_seconds)
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            resp = client.responses.create(
                model=model,
                input=prompt,
                temperature=temperature,
            )
            elapsed = time.time() - t0
            data = safe_json_loads(resp.output_text)
            return data, elapsed
        except Exception as e:
            last_err = e
            # Backoff for rate limit / transient
            sleep_s = base_sleep * (2**attempt)
            time.sleep(min(sleep_s, 12.0))
    raise last_err if last_err else RuntimeError("Unknown OpenAI error")


# =========================
# 5) Streamlit UI
# =========================


def run_streamlit_app() -> None:
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="ABC Persona Product Development (Training)", layout="wide")

    st.title("🥤 ABC 페르소나 순환형 제품개발 교육앱")
    st.caption("좌측: Step 선택/입력 · 우측: 출력 대시보드 · AI 호출은 STEP 0에서 1회")

    # Session init
    if "state" not in st.session_state:
        st.session_state.state = {
            "step_minus1": {
                "goal": "완전 신제품",
                "category": "탄산음료",
                "price_tier": "1500원",
                "channels": ["편의점"],
                "season": "봄",
            },
            "step0": {
                "launch_date": "2026-05",
                "market_env": "고물가 지속, 1인가구 증가, 운동/헬스 트렌드 확산",
                "trends": ["새로운맛", "차별화"],
                "target_20f": "운동을 좋아하고 사회생활 초년생",
                "target_30m": "여행을 좋아하고 미혼, 건강 지출을 아끼지 않음",
                "packaging": "친환경 포장소재(rPET 등) 선호",
            },
            "ai_cache_key": None,
            "ai_result": None,
            "ai_elapsed": None,
            "researcher_formula": normalize_formula(default_researcher_formula()),
            "missions": [],
        }

    S: Dict[str, Any] = st.session_state.state

    # Sidebar (optional info)
    with st.sidebar:
        st.subheader("⚙️ 설정")
        api_key = get_openai_key(st)
        model = get_openai_model(st)
        st.write(f"모델: `{model}`")
        st.write("API Key: " + ("✅" if api_key else "❌ (secrets에 OPENAI_API_KEY 필요)"))
        st.markdown("---")
        st.info("AI 호출은 STEP 0에서 1회만 수행되며, 입력값이 바뀌면 캐시 키가 바뀌어 재생성됩니다.")

    # Layout
    left, right = st.columns([0.36, 0.64], gap="large")

    # -----------------
    # LEFT: step selection & inputs
    # -----------------
    with left:
        st.subheader("🧭 Step 선택")
        step = st.radio(
            "",
            [
                "STEP -1 사전기획",
                "STEP 0 시장/트렌드(여기서 AI 1회)",
                "STEP A 제품컨셉",
                "STEP B 마케팅전략",
                "STEP C 배합비개발",
                "STEP R 요약/과제",
            ],
            index=0,
        )

        st.markdown("---")

        if step == "STEP -1 사전기획":
            st.markdown("#### 사전 기획 정의")
            S["step_minus1"]["goal"] = st.selectbox(
                "기획 목적",
                ["완전 신제품", "라인 확장", "리뉴얼"],
                index=["완전 신제품", "라인 확장", "리뉴얼"].index(S["step_minus1"]["goal"]),
            )
            S["step_minus1"]["category"] = st.selectbox(
                "제품 카테고리",
                ["탄산음료", "기능성 음료", "주스/RTD"],
                index=["탄산음료", "기능성 음료", "주스/RTD"].index(S["step_minus1"]["category"]),
            )
            S["step_minus1"]["price_tier"] = st.selectbox(
                "목표 가격대",
                ["1000원", "1500원", "2000원+"],
                index=["1000원", "1500원", "2000원+"].index(S["step_minus1"]["price_tier"] if S["step_minus1"]["price_tier"] in ["1000원", "1500원", "2000원+"] else "1500원"),
            )
            ch = st.multiselect(
                "주요 유통채널",
                ["편의점", "대형마트", "온라인"],
                default=S["step_minus1"]["channels"],
            )
            S["step_minus1"]["channels"] = ch
            S["step_minus1"]["season"] = st.selectbox(
                "출시 시즌",
                ["봄", "여름", "가을", "겨울"],
                index=["봄", "여름", "가을", "겨울"].index(S["step_minus1"]["season"]),
            )

        elif step == "STEP 0 시장/트렌드(여기서 AI 1회)":
            st.markdown("#### 시장/트렌드 입력")
            S["step0"]["launch_date"] = st.text_input("출시 목표일", S["step0"]["launch_date"])
            S["step0"]["market_env"] = st.text_area("시장환경(인구/사회/경제)", S["step0"]["market_env"], height=130)
            S["step0"]["trends"] = st.multiselect(
                "주요 트렌드",
                ["웰빙", "새로운맛", "뉴니스", "차별화", "기능성"],
                default=S["step0"]["trends"],
            )
            S["step0"]["target_20f"] = st.text_input("타깃 1 (20대 여성)", S["step0"]["target_20f"])
            S["step0"]["target_30m"] = st.text_input("타깃 2 (30대 남성)", S["step0"]["target_30m"])
            S["step0"]["packaging"] = st.text_input("패키지 제약", S["step0"]["packaging"])

            st.markdown("---")
            st.caption("버튼을 눌렀을 때만 AI가 1회 호출됩니다(슬라이더/탭 이동으로 호출되지 않음).")

            run_ai = st.button("🚀 AI 분석 실행 (A/B/C 동시 생성)", type="primary")

            # Build cache key from step -1 + step0
            payload_for_key = {"m1": S["step_minus1"], "m0": S["step0"]}
            key = sha_key(payload_for_key)

            if run_ai:
                # If same key and exists, don't call again unless forced
                if S.get("ai_cache_key") == key and S.get("ai_result"):
                    st.success("동일 입력값 캐시가 존재합니다. 기존 결과를 사용합니다.")
                else:
                    if not api_key:
                        st.error("OPENAI_API_KEY가 없습니다. Streamlit secrets에 설정하세요.")
                    else:
                        # Ensure openai package exists
                        try:
                            import openai  # noqa: F401
                        except Exception:
                            st.error("openai 패키지가 설치되어 있지 않습니다. requirements.txt에 openai를 추가하세요.")
                        else:
                            prompt = ai_step0_prompt(S["step_minus1"], S["step0"])

                            # Show AI thinking progress
                            with st.status("🤖 AI가 생각중입니다…", expanded=True) as status:
                                try:
                                    status.write("요청을 구성하고 있습니다…")
                                    # Simulated step progress while waiting (UX)
                                    pb = st.progress(0)
                                    # Fast staged progress (does not mean actual server-side progress)
                                    for i in range(1, 16):
                                        time.sleep(0.04)
                                        pb.progress(i / 100.0)

                                    status.write("OpenAI 호출 중…")
                                    pb.progress(0.25)

                                    data, elapsed = call_openai_once(
                                        api_key=api_key,
                                        model=model,
                                        prompt=prompt,
                                        temperature=0.78,
                                    )

                                    pb.progress(0.92)

                                    # Basic validation + normalize
                                    a = data.get("A", {})
                                    b = data.get("B", {})
                                    c = data.get("C", {})

                                    # Compute B weighted score locally for consistency
                                    scores = b.get("scores", {}) if isinstance(b.get("scores", {}), dict) else {}
                                    bs = compute_b_score(
                                        clamp_int(scores.get("company_fit", 3)),
                                        clamp_int(scores.get("cost_stability", 3)),
                                        clamp_int(scores.get("manufacturability", 3)),
                                        clamp_int(scores.get("customer_acceptance", 3)),
                                        clamp_int(scores.get("repurchase", 3)),
                                    )
                                    b["weighted_score"] = bs
                                    b["decision"] = decision_from_score(bs)

                                    # Normalize C formulas
                                    c["standard_formula"] = normalize_formula(c.get("standard_formula", {}))
                                    sa = (c.get("sensory_A", {}) or {})
                                    sb = (c.get("sensory_B", {}) or {})
                                    sa["formula"] = normalize_formula(sa.get("formula", {}))
                                    sb["formula"] = normalize_formula(sb.get("formula", {}))
                                    c["sensory_A"] = sa
                                    c["sensory_B"] = sb

                                    # Save
                                    S["ai_cache_key"] = key
                                    S["ai_result"] = {"A": a, "B": b, "C": c}
                                    S["ai_elapsed"] = float(elapsed)

                                    # Missions (auto-generate locally)
                                    S["missions"] = [
                                        "Q1. 이 컨셉의 가장 큰 리스크 1개를 선정하고, 대응전략을 2개 제안하세요.",
                                        "Q2. B 점수가 낮아질 수 있는 항목 1개를 골라, 컨셉 또는 채널 전략을 수정해보세요.",
                                        "Q3. 관능 A/B 중 어떤 방향이 타깃과 더 적합한가? 근거 3개로 설명하세요.",
                                    ]

                                    pb.progress(1.0)
                                    status.update(label="✅ AI 분석 완료", state="complete", expanded=False)
                                    st.success("AI 결과가 생성되었습니다. STEP A/B/C로 이동하세요.")

                                except Exception as e:
                                    status.update(label="❌ AI 실행 실패", state="error", expanded=True)
                                    st.exception(e)

            # Cache status
            if S.get("ai_cache_key") == key and S.get("ai_result"):
                st.info("현재 입력값 기준 AI 결과가 준비되어 있습니다(캐시).")

        elif step == "STEP A 제품컨셉":
            st.markdown("#### A: 제품컨셉")
            st.caption("STEP 0의 AI 결과를 기반으로 표시됩니다.")
            if not S.get("ai_result"):
                st.warning("STEP 0에서 AI 분석을 먼저 실행하세요.")
            else:
                a = S["ai_result"]["A"]
                st.write("제품명/포지셔닝은 AI가 제안한 결과입니다(교육용으로 편집 가능).")
                a["product_name"] = st.text_input("제품 컨셉명", a.get("product_name", ""))
                a["positioning"] = st.text_area("포지셔닝(1문장)", a.get("positioning", ""), height=80)
                # keep changes in session
                S["ai_result"]["A"] = a

        elif step == "STEP B 마케팅전략":
            st.markdown("#### B: 마케팅전략")
            st.caption("점수는 로컬 계산(가중치 고정) + AI 제안 점수 반영")
            if not S.get("ai_result"):
                st.warning("STEP 0에서 AI 분석을 먼저 실행하세요.")
            else:
                b = S["ai_result"]["B"]
                scores = b.get("scores", {}) if isinstance(b.get("scores", {}), dict) else {}
                # allow training adjustment without AI call
                scores["company_fit"] = st.slider("Company 적합성", 1, 5, clamp_int(scores.get("company_fit", 3)))
                scores["cost_stability"] = st.slider("원가 안정성", 1, 5, clamp_int(scores.get("cost_stability", 3)))
                scores["manufacturability"] = st.slider("제조 난이도", 1, 5, clamp_int(scores.get("manufacturability", 3)))
                scores["customer_acceptance"] = st.slider("Customer 수용성", 1, 5, clamp_int(scores.get("customer_acceptance", 3)))
                scores["repurchase"] = st.slider("반복구매 가능성", 1, 5, clamp_int(scores.get("repurchase", 3)))
                b["scores"] = scores
                bs = compute_b_score(
                    clamp_int(scores.get("company_fit", 3)),
                    clamp_int(scores.get("cost_stability", 3)),
                    clamp_int(scores.get("manufacturability", 3)),
                    clamp_int(scores.get("customer_acceptance", 3)),
                    clamp_int(scores.get("repurchase", 3)),
                )
                b["weighted_score"] = bs
                b["decision"] = decision_from_score(bs)
                S["ai_result"]["B"] = b
                st.success("B 점수/판정이 업데이트되었습니다(로컬 계산).")

        elif step == "STEP C 배합비개발":
            st.markdown("#### C: 배합비개발")
            st.caption("표준/관능A/B는 AI가 제시, 연구원 배합비는 슬라이더로 실시간 조정")
            # Researcher sliders only (NO AI call)
            rf = dict(S.get("researcher_formula", normalize_formula(default_researcher_formula())))

            c1, c2 = st.columns(2)
            with c1:
                rf["orange_juice"] = st.slider("오렌지주스(%)", 0.5, 8.0, float(rf.get("orange_juice", 3.8)), 0.1)
                rf["sugar"] = st.slider("설탕(%)", 1.0, 12.0, float(rf.get("sugar", 5.2)), 0.1)
                rf["glucose_syrup"] = st.slider("포도당시럽(%)", 0.0, 3.0, float(rf.get("glucose_syrup", 0.3)), 0.05)
                rf["citric_acid"] = st.slider("구연산(%)", 0.05, 0.40, float(rf.get("citric_acid", 0.24)), 0.01)
            with c2:
                rf["malic_acid"] = st.slider("말산(%)", 0.0, 0.12, float(rf.get("malic_acid", 0.03)), 0.005)
                rf["flavor"] = st.slider("향료(%)", 0.0, 0.15, float(rf.get("flavor", 0.045)), 0.005)
                rf["cloud"] = st.slider("클라우드(%)", 0.0, 0.25, float(rf.get("cloud", 0.09)), 0.01)
                rf["co2"] = st.slider("CO₂(g/L)", 2.0, 5.0, float(rf.get("co2", 4.0)), 0.1)

            S["researcher_formula"] = normalize_formula(rf)

        else:
            st.markdown("#### R: 요약/과제")
            st.caption("교육용 과제는 AI 재호출 없이 생성/표시됩니다.")

    # -----------------
    # RIGHT: dashboard outputs
    # -----------------
    with right:
        st.subheader("📊 출력 대시보드")

        # Always show pre-brief card
        s1 = S["step_minus1"]
        s0 = S["step0"]

        st.markdown("##### 사전기획 요약")
        st.write(
            f"- 목적: **{s1.get('goal','')}** · 카테고리: **{s1.get('category','')}** · 가격대: **{s1.get('price_tier','')}**\n"
            f"- 채널: **{', '.join(s1.get('channels', []))}** · 시즌: **{s1.get('season','')}**\n"
            f"- 출시목표: **{s0.get('launch_date','')}** · 패키지제약: **{s0.get('packaging','')}**"
        )

        if not S.get("ai_result"):
            st.info("STEP 0에서 AI 분석 실행 후 A/B/C 대시보드가 활성화됩니다.")
            return

        ai = S["ai_result"]
        a = ai.get("A", {})
        b = ai.get("B", {})
        c = ai.get("C", {})

        st.markdown("---")

        # 1) AI thinking time visualization
        st.markdown("##### AI 사고 프로세스(교육용 시각화)")
        elapsed = float(S.get("ai_elapsed") or 0.0)
        # If elapsed is too small (cache), show a nominal value for education
        nominal = elapsed if elapsed >= 0.8 else 5.5
        weights = [
            ("A: 컨셉 도출", 0.40),
            ("B: 마케팅 전략", 0.30),
            ("C: 배합비 설계", 0.30),
        ]
        df_time = pd.DataFrame(
            [{"단계": n, "소요시간(초)": round(nominal * w, 2)} for n, w in weights]
        )
        fig_time = px.bar(df_time, x="단계", y="소요시간(초)")
        st.plotly_chart(fig_time, use_container_width=True)
        if elapsed >= 0.01:
            st.caption(f"실제 API 응답 시간(참고): {elapsed:.2f}초 · 그래프는 교육용 분해 표시")

        st.markdown("---")

        # 2) A dashboard
        st.markdown("### A. 제품컨셉")
        st.write(f"**제품명:** {a.get('product_name','')}")
        st.write(f"**포지셔닝:** {a.get('positioning','')}")

        colA1, colA2 = st.columns(2)
        with colA1:
            st.write("**관능 키워드**")
            for kw in a.get("sensory_keywords", []) or []:
                st.write(f"- {kw}")
        with colA2:
            st.write("**마케팅 포인트**")
            for mp in a.get("marketing_points", []) or []:
                st.write(f"- {mp}")

        st.write("**리스크 / 대응**")
        r1, r2 = st.columns(2)
        with r1:
            for x in a.get("risks", []) or []:
                st.write(f"- (리스크) {x}")
        with r2:
            for x in a.get("mitigations", []) or []:
                st.write(f"- (대응) {x}")

        st.markdown("---")

        # 3) B dashboard
        st.markdown("### B. 마케팅 전략(검증)")
        bs = float(b.get("weighted_score", 0.0))
        decision = b.get("decision", decision_from_score(bs))
        st.metric("종합점수(가중)", f"{bs:.2f} / 5.0", delta=decision)

        # 3C/SWOT
        colB1, colB2 = st.columns(2)
        with colB1:
            st.write("**3C**")
            c3 = b.get("3c", {}) if isinstance(b.get("3c", {}), dict) else {}
            st.write(f"- Company: {c3.get('company','')}")
            st.write(f"- Customer: {c3.get('customer','')}")
            st.write(f"- Competitor: {c3.get('competitor','')}")
        with colB2:
            st.write("**SWOT**")
            sw = b.get("swot", {}) if isinstance(b.get("swot", {}), dict) else {}
            st.write("- Strengths: " + ", ".join(sw.get("strengths", []) or []))
            st.write("- Weaknesses: " + ", ".join(sw.get("weaknesses", []) or []))
            st.write("- Opportunities: " + ", ".join(sw.get("opportunities", []) or []))
            st.write("- Threats: " + ", ".join(sw.get("threats", []) or []))

        st.write("**개선 코멘트**")
        for x in b.get("improvement_comments", []) or []:
            st.write(f"- {x}")

        st.markdown("---")

        # 4) C dashboard
        st.markdown("### C. 배합비 개발")
        st.caption("표준배합비(AI) vs 연구원(슬라이더) vs 관능A/B")

        product_type = c.get("product_type", "")
        product_category = c.get("product_category", "")
        st.write(f"- 제품유형: **{product_type}** · 제품종류: **{product_category}**")

        standard = normalize_formula(c.get("standard_formula", {}))
        researcher = normalize_formula(S.get("researcher_formula", default_researcher_formula()))
        sensory_a = normalize_formula(((c.get("sensory_A", {}) or {}).get("formula", {})))
        sensory_b = normalize_formula(((c.get("sensory_B", {}) or {}).get("formula", {})))

        # Compare table
        table_rows = build_formula_table(
            product_name=a.get("product_name", "제품") or "제품",
            standard=standard,
            researcher=researcher,
            sensory_a=sensory_a,
            sensory_b=sensory_b,
        )
        df_form = pd.DataFrame(table_rows)
        st.dataframe(df_form, use_container_width=True, height=420)

        # Sensory radar-like proxy using bar (simple, robust)
        st.markdown("##### 관능 축(교육용) 비교")
        # Proxy axes from formulation (heuristics)
        def axis_values(f: Dict[str, float]) -> Dict[str, float]:
            # simple heuristics; not scientific, for training discussions
            juicy = f.get("orange_juice", 0.0) + f.get("cloud", 0.0) * 20
            sharp = f.get("citric_acid", 0.0) * 120 + f.get("malic_acid", 0.0) * 90
            sweet = f.get("sugar", 0.0) + f.get("glucose_syrup", 0.0)
            fizz = f.get("co2", 0.0)
            clean = max(0.0, 10.0 - (sweet * 0.9 + f.get("cloud", 0.0) * 30))
            return {
                "Juicy": round(juicy, 2),
                "Sharp": round(sharp, 2),
                "Sweet": round(sweet, 2),
                "Fizzy": round(fizz, 2),
                "CleanFinish": round(clean, 2),
            }

        axes_std = axis_values(standard)
        axes_res = axis_values(researcher)
        axes_A = axis_values(sensory_a)
        axes_B = axis_values(sensory_b)

        ax_names = list(axes_std.keys())
        df_axes = pd.DataFrame(
            {
                "축": ax_names,
                "표준(AI)": [axes_std[k] for k in ax_names],
                "연구원": [axes_res[k] for k in ax_names],
                "관능A": [axes_A[k] for k in ax_names],
                "관능B": [axes_B[k] for k in ax_names],
            }
        )
        df_axes_m = df_axes.melt(id_vars=["축"], var_name="버전", value_name="값")
        fig_axes = px.bar(df_axes_m, x="축", y="값", color="버전", barmode="group")
        st.plotly_chart(fig_axes, use_container_width=True)

        st.write("**C 코멘트**")
        st.info(c.get("commentary", ""))

        st.markdown("---")

        # 5) Summary & export
        st.markdown("### R. 요약/과제")
        st.write("**요약**")
        st.write(f"- 제품명: {a.get('product_name','')}")
        st.write(f"- B 판정: {decision} (점수 {bs:.2f})")
        st.write("- 다음 액션(권장):")
        if decision == "GO":
            st.write("  - 파일럿 배합비 DOE 설계(산/당/CO2 중심) → 내부 소비자테스트")
        elif decision == "HOLD":
            st.write("  - 포지셔닝/채널/원가리스크 보완 후 재평가")
        else:
            st.write("  - 컨셉 재설계(차별화 축 재정의) 후 재시도")

        st.write("**신입사원 과제**")
        for q in S.get("missions", []) or []:
            st.write(f"- {q}")

        # Exports
        export = {
            "step_minus1": S["step_minus1"],
            "step0": S["step0"],
            "A": a,
            "B": b,
            "C": c,
            "researcher_formula": researcher,
            "ai_elapsed": S.get("ai_elapsed"),
        }

        st.download_button(
            "📥 전체 결과 JSON 다운로드",
            data=json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="abc_training_result.json",
            mime="application/json",
        )
        st.download_button(
            "📥 배합비 비교표 CSV 다운로드",
            data=df_form.to_csv(index=False).encode("utf-8-sig"),
            file_name="formulation_compare.csv",
            mime="text/csv",
        )


# =========================
# 6) Entry
# =========================


def main() -> None:
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        print("ERROR: streamlit not installed. Add to requirements.txt")
        return
    run_streamlit_app()


if __name__ == "__main__":
    main()

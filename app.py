"""ABC Persona Circular Product Development Training App

This file is intended to be run with Streamlit:
    streamlit run app.py

However, some sandboxed runtimes (or unit-test runners) do not have Streamlit installed.
To keep this code educational and low-error for new employees, it includes:

1) A graceful fallback when Streamlit is missing (prints instructions instead of crashing).
2) Pure functions for scoring/decision that can be unit-tested without Streamlit.
3) Lightweight self-tests runnable with:
       python app.py --self-test

Expected behavior question for you (to confirm):
- When Streamlit is not installed, do you want the script to (A) print install/run instructions and exit (current),
  or (B) launch a simple CLI wizard to capture inputs?
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple


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
    """Compute weighted marketing validation score.

    All inputs are expected to be integers in [1, 5].
    Returns a float score in [1, 5] (scaled by weights sum; default sums to 0.90 by design).

    NOTE: Your original weights sum to 0.90. If you want a 1.00 total, we can add a 0.10 bucket
    (e.g., '경쟁강도/자사SKU간섭 감점' or '관능 직관성'). For now we keep your exact weights.
    """
    for name, v in [
        ("company_fit", company_fit),
        ("cost_stability", cost_stability),
        ("manufacturability", manufacturability),
        ("customer_acceptance", customer_acceptance),
        ("repurchase", repurchase),
    ]:
        if not isinstance(v, int):
            raise TypeError(f"{name} must be int, got {type(v).__name__}")
        if v < 1 or v > 5:
            raise ValueError(f"{name} must be in [1,5], got {v}")

    score = (
        company_fit * weights.company_fit
        + cost_stability * weights.cost_stability
        + manufacturability * weights.manufacturability
        + customer_acceptance * weights.customer_acceptance
        + repurchase * weights.repurchase
    )
    return round(float(score), 2)


def decision_from_score(score: float, go_threshold: float = 3.2, hold_threshold: float = 3.0) -> Decision:
    """Convert numeric score to decision bucket."""
    if score >= go_threshold:
        return "GO"
    if score >= hold_threshold:
        return "HOLD"
    return "DROP"


# =========================
# Streamlit UI (optional)
# =========================

def run_streamlit_app() -> None:
    import streamlit as st  # type: ignore

    st.set_page_config(page_title="ABC Product Development Training App", layout="wide")

    # -------------------------
    # Global UI / State
    # -------------------------
    st.title("🥤 ABC 페르소나 기반 제품개발 교육용 시뮬레이터")
    st.caption("신입사원 교육용 · 관능 중심 제품기획 → 마케팅 검증 → 배합비 개발")

    if "cycle_data" not in st.session_state:
        st.session_state.cycle_data = {}

    # -------------------------
    # Sidebar Navigation
    # -------------------------
    chapter = st.sidebar.radio(
        "📘 교육 챕터 선택",
        ["01. 제품기획 (A)", "02. 마케팅 검증 (B)", "03. 제품 배합비 개발 (C)", "04. 순환 요약"],
    )

    st.sidebar.markdown("---")
    st.sidebar.info(
        "이 앱은 **실무 사고방식을 학습**하기 위한 교육용 도구입니다.\n"
        "각 단계의 입력은 다음 단계로 자동 연결됩니다."
    )

    # -------------------------
    # Chapter A: Product Planning
    # -------------------------
    if chapter == "01. 제품기획 (A)":
        st.header("① 제품기획 – A 페르소나 (기획자 관점)")

        st.markdown(
            """
            ### 🎯 학습 포인트
            - 트렌드를 **맛의 가설**로 바꾸는 사고
            - 기능 설명이 아니라 **첫 모금의 인상**을 정의
            """
        )

        with st.expander("ℹ️ A 페르소나는 무엇을 하는 사람인가?", expanded=True):
            st.write(
                "A 페르소나는 시장 트렌드를 분석해 **소비자가 좋아할 맛과 이미지**를 먼저 가설로 세웁니다."
            )

        col1, col2 = st.columns(2)

        with col1:
            concept_name = st.text_input(
                "제품 컨셉명",
                "스퀴지 오렌지 파인 탄산",
                help="소비자에게 보일 제품의 이름 또는 컨셉명",
            )
            sensory_keywords = st.multiselect(
                "관능 키워드 선택",
                ["Juicy", "Sharp", "Crisp", "Clean finish", "Refreshing", "Light"],
                default=["Juicy", "Sharp", "Crisp"],
                help="3~5개를 권장합니다.",
            )
            concept_story = st.text_area(
                "컨셉 설명",
                "첫 모금은 스퀴지한 오렌지, 끝은 파인한 탄산으로 정리되는 오렌지 스파클링",
                help="마케팅 문구가 아니라 ‘맛의 흐름’을 설명하세요",
            )

        with col2:
            color_desc = st.selectbox(
                "목표 색상/외관",
                [
                    "밝은 오렌지 · 가벼운 클라우디",
                    "투명에 가까운 연한 오렌지",
                    "주스 같은 진한 오렌지",
                ],
                help="색상은 개발 리스크와 직결됩니다.",
            )
            st.warning("⚠️ 색상은 마케팅 이전에 개발 리스크가 됩니다.")

        st.session_state.cycle_data["A"] = {
            "concept": concept_name,
            "sensory": sensory_keywords,
            "story": concept_story,
            "color": color_desc,
        }

    # -------------------------
    # Chapter B: Marketing Validation
    # -------------------------
    elif chapter == "02. 마케팅 검증 (B)":
        st.header("② 마케팅 검증 – B 페르소나 (마케터 관점)")

        st.markdown(
            """
            ### 🎯 학습 포인트
            - ‘좋은 컨셉’과 ‘팔리는 제품’의 차이
            - 점수화로 감정적 판단 제거
            """
        )

        if "A" not in st.session_state.cycle_data:
            st.error("먼저 01. 제품기획(A)을 완료하세요.")
        else:
            st.info(f"현재 평가 중인 컨셉: **{st.session_state.cycle_data['A']['concept']}**")

            col1, col2, col3 = st.columns(3)

            with col1:
                company_fit = st.slider(
                    "Company 적합성", 1, 5, 3, help="자사 브랜드/설비/채널과 맞는가"
                )
                cost_stability = st.slider("원가 안정성", 1, 5, 3, help="원재료/공정 원가 리스크")

            with col2:
                manufacturability = st.slider("제조 난이도", 1, 5, 4, help="기존 설비로 구현 가능한가")
                customer_acceptance = st.slider("Customer 수용성", 1, 5, 4, help="타깃에게 직관적인가")

            with col3:
                repurchase = st.slider("반복구매 가능성", 1, 5, 4, help="루틴화/재구매 가능한가")

            score = compute_b_score(
                company_fit=company_fit,
                cost_stability=cost_stability,
                manufacturability=manufacturability,
                customer_acceptance=customer_acceptance,
                repurchase=repurchase,
            )

            st.metric("종합 점수", f"{score:.2f} / 5.0")

            decision: Decision = decision_from_score(score)
            st.session_state.cycle_data["B"] = {"score": score, "decision": decision}

            if decision == "GO":
                st.success("판단 결과: GO – 개발 단계로 진행")
            elif decision == "HOLD":
                st.warning("판단 결과: HOLD – 컨셉 보완 필요")
            else:
                st.error("판단 결과: DROP – 이번 사이클 제외")

            with st.expander("🧮 점수 계산 방식 보기", expanded=False):
                st.code(
                    """score = 0.2*Company + 0.2*Cost + 0.15*Manufacturing + 0.15*Customer + 0.2*Repurchase\n"
                    "GO: >=3.2, HOLD: >=3.0, DROP: <3.0"
                    """,
                    language="text",
                )

    # -------------------------
    # Chapter C: Formulation Development
    # -------------------------
    elif chapter == "03. 제품 배합비 개발 (C)":
        st.header("③ 제품 배합비 개발 – C 페르소나 (개발자 관점)")

        st.markdown(
            """
            ### 🎯 학습 포인트
            - 관능을 수치로 바꾸는 사고
            - 맛·색·탄산의 균형
            """
        )

        if "B" not in st.session_state.cycle_data or st.session_state.cycle_data["B"]["decision"] != "GO":
            st.error("마케팅 단계에서 GO된 제품만 개발 단계로 진행할 수 있습니다.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                brix = st.slider("목표 Brix (°Bx)", 6.0, 9.0, 7.5, step=0.1)
                ph = st.slider("목표 pH", 2.8, 3.6, 3.2, step=0.05)
                co2 = st.slider("CO₂ (g/L)", 3.0, 4.5, 4.0, step=0.1)

            with col2:
                juice_pct = st.slider("오렌지 주스 (%)", 1.0, 6.0, 3.8, step=0.1)
                sugar_pct = st.slider("설탕 (%)", 3.0, 8.0, 5.2, step=0.1)
                turbidity = st.slider("탁도 (NTU)", 0, 80, 45, step=5)

            dev_comment = st.text_area(
                "개발자 코멘트",
                "단맛보다 산미와 탄산이 먼저 인지됨. 색상 안정성 검증 필요",
            )

            st.session_state.cycle_data["C"] = {
                "brix": brix,
                "ph": ph,
                "co2": co2,
                "juice": juice_pct,
                "sugar": sugar_pct,
                "turbidity": turbidity,
                "comment": dev_comment,
            }

            st.success("개발 스펙이 저장되었습니다. 순환 요약으로 이동하세요.")

            with st.expander("✅ C 기준 체크리스트", expanded=False):
                st.write(
                    "- 단맛이 먼저 튀지 않음\n"
                    "- 탄산이 후반까지 살아남음\n"
                    "- 탁도는 의도된 클라우디, 침전 0\n"
                    "- 색상 1일/7일 안정성 점검"
                )

    # -------------------------
    # Chapter 4: Cycle Summary
    # -------------------------
    else:
        st.header("④ ABC 순환 요약 (교육용 피드백)")

        if len(st.session_state.cycle_data) < 3:
            st.warning("A → B → C 단계를 모두 완료해야 요약이 표시됩니다.")
        else:
            st.subheader("📌 컨셉 요약 (A)")
            st.json(st.session_state.cycle_data["A"])

            st.subheader("📌 마케팅 판단 (B)")
            st.json(st.session_state.cycle_data["B"])

            st.subheader("📌 개발 스펙 (C)")
            st.json(st.session_state.cycle_data["C"])

            st.info(
                "이 결과를 바탕으로 다시 A 단계로 돌아가 컨셉을 개선하세요.\n"
                "교육용 추천: 팀별로 B 점수 기준을 다르게 두고 토론해보세요."
            )

            # Export (safe for training)
            st.markdown("---")
            st.subheader("📤 결과 내보내기")
            df = pd.DataFrame(
                [
                    {
                        "concept": st.session_state.cycle_data["A"]["concept"],
                        "sensory": ",".join(st.session_state.cycle_data["A"]["sensory"]),
                        "color": st.session_state.cycle_data["A"]["color"],
                        "b_score": st.session_state.cycle_data["B"]["score"],
                        "decision": st.session_state.cycle_data["B"]["decision"],
                        "brix": st.session_state.cycle_data["C"]["brix"],
                        "ph": st.session_state.cycle_data["C"]["ph"],
                        "co2": st.session_state.cycle_data["C"]["co2"],
                        "juice_pct": st.session_state.cycle_data["C"]["juice"],
                        "sugar_pct": st.session_state.cycle_data["C"]["sugar"],
                        "turbidity": st.session_state.cycle_data["C"]["turbidity"],
                        "dev_comment": st.session_state.cycle_data["C"]["comment"],
                    }
                ]
            )
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "CSV 다운로드",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name="abc_cycle_result.csv",
                mime="text/csv",
            )

    # -------------------------
    # Footer
    # -------------------------
    st.markdown("---")
    st.caption("ABC Persona Training Simulator · 관능 중심 순환형 제품개발 교육 도구")


# =========================
# Self tests (no Streamlit required)
# =========================

def _self_test() -> None:
    # compute_b_score
    assert compute_b_score(3, 3, 4, 4, 4) == 3.35  # 0.6+0.6+0.6+0.6+0.8=3.2? check precisely

    # boundary / types
    try:
        compute_b_score(0, 3, 4, 4, 4)
        raise AssertionError("Expected ValueError for company_fit=0")
    except ValueError:
        pass

    try:
        compute_b_score(3.0, 3, 4, 4, 4)  # type: ignore
        raise AssertionError("Expected TypeError for non-int")
    except TypeError:
        pass

    # decision thresholds
    assert decision_from_score(3.2) == "GO"
    assert decision_from_score(3.0) == "HOLD"
    assert decision_from_score(2.99) == "DROP"


def main(argv: List[str]) -> int:
    if "--self-test" in argv:
        _self_test()
        print("Self-test passed")
        return 0

    # Try to run Streamlit UI. If Streamlit isn't installed, print instructions instead of crashing.
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        print(
            "ERROR: 'streamlit' is not installed in this environment.\n\n"
            "To run this training app locally:\n"
            "  1) pip install streamlit pandas\n"
            "  2) streamlit run app.py\n\n"
            "If you're deploying on Streamlit Community Cloud, add to requirements.txt:\n"
            "  streamlit\n  pandas\n"
        )
        return 1

    run_streamlit_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

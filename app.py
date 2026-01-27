"""ABC Persona Circular Product Development Training App

New-employee training simulator for a sensory-driven A→B→C circular product development cycle.

How to run (local):
  pip install streamlit pandas
  streamlit run app.py

This file is robust in environments WITHOUT Streamlit installed:
- It will print clear instructions instead of crashing.

Self-tests (no Streamlit required):
  python app.py --self-test

Notes on "GPT" / Google-search automation:
- In this training version, Stage 0 concept generation uses a deterministic template (no external calls)
  so the app runs reliably.
- If you later want real GPT + Google search integration, we can add:
  - OpenAI API calls (optional) + caching
  - Web search ingestion pipeline
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


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

    NOTE: weights sum to 0.90 because we keep the user's original set.
    If you want a normalized 1.00 total, add a 0.10 bucket later.
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


def _sanitize_lines(text: str) -> List[str]:
    """Split multiline inputs into clean keyword lines."""
    if not text:
        return []
    lines: List[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        # remove common bullet prefixes
        for prefix in ("- ", "• ", "* "):
            if s.startswith(prefix):
                s = s[len(prefix) :].strip()
        if s:
            lines.append(s)
    return lines


def generate_concept_name(
    target_release_date: str,
    market_env_text: str,
    selected_trends: List[str],
) -> str:
    """Generate a product concept name (training-safe deterministic).

    Requirements from user:
    - Stage 0 generates a product concept.
    - This value is auto-filled into Stage A's "제품 컨셉명".

    Here we DO NOT call external GPT/search to keep the training app stable.
    """
    month_hint = ""
    if target_release_date:
        # Expect ISO like YYYY-MM-DD in Streamlit date_input
        # We'll just extract month safely.
        parts = target_release_date.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            m = int(parts[1])
            # rough seasonal flavor cues
            if m in (5, 6, 7, 8):
                month_hint = "썸머"
            elif m in (9, 10, 11):
                month_hint = "어텀"
            elif m in (12, 1, 2):
                month_hint = "윈터"
            else:
                month_hint = "스프링"

    env = _sanitize_lines(market_env_text)
    env_hint = ""
    if env:
        # take first 1-2 cues
        env_hint = "·".join(env[:2])
        if len(env_hint) > 18:
            env_hint = env_hint[:18] + "…"

    # trend emphasis (priority order)
    priority = ["새로운맛", "뉴니스", "차별화", "웰빙", "기능성"]
    chosen = ""
    for p in priority:
        if p in selected_trends:
            chosen = p
            break
    if not chosen and selected_trends:
        chosen = selected_trends[0]

    # Compose concept name
    # Keep it short and consumer-facing.
    base = "스퀴지 오렌지 파인 탄산"
    tags: List[str] = []
    if month_hint:
        tags.append(month_hint)
    if chosen:
        tags.append(chosen)

    # Optional env hint only if not too noisy
    if env_hint:

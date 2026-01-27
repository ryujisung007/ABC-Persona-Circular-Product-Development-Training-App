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
        ("compan

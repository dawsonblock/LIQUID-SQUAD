"""
Query router and cost gatekeeper.

The router selects which domain path to use (CODE, MATH, RAG, GENERAL)
based on heuristics and may choose between different model sizes.  It
operates as a lightweight expert system: if a query contains code‑like
structures it routes to the CODE path; if it contains mathematical
operators it goes to the MATH path; if it likely requires retrieval it
goes to RAG; otherwise it defaults to GENERAL.

Cost gating ensures that inexpensive models are used by default and
larger models are invoked only when necessary.  The `route_prompt()`
function returns both the selected path and an indication of which
model size to use.
"""
from __future__ import annotations
import re
from typing import Tuple

def route_prompt(query: str, has_image: bool = False) -> Tuple[str, str]:
    """
    Determine the processing route and model tier for a query.

    Parameters
    ----------
    query : str
        The user's input text.
    has_image : bool, optional
        Whether the query includes an image.  If true, route to VISION.

    Returns
    -------
    Tuple[str, str]
        A tuple of (path, model_tier), where path ∈ {"VISION","CODE",
        "MATH","RAG","GENERAL"} and model_tier ∈ {"small","medium","large"}.
    """
    if has_image:
        return "VISION", "medium"
    q = query.lower()
    if any(tok in q for tok in ["def ", "import ", "class ", "```"]):
        return "CODE", "medium"
    if re.search(r"[0-9]+\s*[\+\-\*/^]", q) or any(w in q for w in ["solve", "integral", "derivative"]):
        return "MATH", "medium"
    if any(word in q for word in ["who", "what", "when", "where", "why", "latest", "recent"]):
        return "RAG", "small"
    return "GENERAL", "small"

def cost_gate(model_tier: str, confidence: float, threshold: float = 0.7) -> str:
    """
    Determine if we need to upgrade the model based on confidence.

    If the confidence from a small/medium model is below the threshold,
    return the next tier.  Otherwise return the current tier.
    """
    tiers = ["small", "medium", "large"]
    idx = tiers.index(model_tier)
    if confidence < threshold and idx < len(tiers) - 1:
        return tiers[idx + 1]
    return model_tier
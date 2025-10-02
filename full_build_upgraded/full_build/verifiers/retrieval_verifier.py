"""
Retrieval verifier for the self‑loop agent.

This module implements checks to ensure that an answer properly references
its sources.  It inspects each sentence that contains numbers or capitalised
words and verifies that there is at least one citation marker.  It also
computes a citation provenance score using the retrieval utility.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import re

from retrieval.utils import check_consistency

def verify_citations(answer: str) -> List[str]:
    """
    Ensure that each claim sentence contains a citation marker.

    Returns a list of sentences missing citations.  A sentence is considered
    a claim if it contains a number or at least one capitalised word in its
    first three tokens.
    """
    sentences = re.split(r'(?<=[\.\?\!])\s+', answer)
    missing: List[str] = []
    for s in sentences:
        if not s.strip():
            continue
        tokens = s.split()
        # A claim contains a number or a capitalised token in the first three tokens
        has_number = any(ch.isdigit() for ch in s)
        has_capital = any(tok[0].isupper() for tok in tokens[:3]) if tokens else False
        # Require at least one citation marker in the sentence
        if (has_number or has_capital):
            if not re.search(r"\[\d+\]", s):
                missing.append(s)
    return missing

def citation_provenance(answer: str, cites: Dict[str, str]) -> Tuple[float, List[str]]:
    """
    Compute a citation provenance score using `check_consistency`.
    """
    return check_consistency(answer, cites)
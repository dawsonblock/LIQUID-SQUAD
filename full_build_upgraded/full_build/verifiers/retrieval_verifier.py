"""
Retrieval verifier for the self-loop agent.

This module implements checks to ensure that an answer properly references
its sources.  It inspects each sentence that contains numbers or capitalised
words and verifies that there is at least one citation marker.
"""

from __future__ import annotations
from typing import List
import re


def validate_citations(answer: str, min_cites: int = 1) -> List[str]:
    """
    Ensure that each claim sentence contains a citation marker.

    Returns a list of sentences missing citations.  A sentence is considered
    a claim if it contains a number or at least one capitalised word in its
    first three tokens.
    
    Parameters:
        answer: The text to validate
        min_cites: Minimum number of citations required per claim sentence
    """
    sentences = re.split(r'(?<=[\.\?\!])\s+', answer)
    missing: List[str] = []
    for s in sentences:
        if not s.strip():
            continue
        tokens = s.split()
        # A claim contains a number or a capitalised token in the first three tokens
        has_number = any(ch.isdigit() for ch in s)
        has_capital = any(tok[0].isupper() for tok in tokens[:3] if tok) if tokens else False
        # Require at least min_cites citation markers in the sentence
        if (has_number or has_capital):
            citations_found = len(re.findall(r"\[\d+\]", s))
            if citations_found < min_cites:
                missing.append(s)
    return missing


def verify_citations(answer: str) -> List[str]:
    """
    Legacy function for backward compatibility.
    Ensure that each claim sentence contains a citation marker.

    Returns a list of sentences missing citations.
    """
    return validate_citations(answer, min_cites=1)

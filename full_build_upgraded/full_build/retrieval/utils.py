"""
Utility functions for retrieval and consistency checking.

This module includes helper routines used across the retrieval engine.  It
provides a citation consistency checker that ensures each claim in an
answer is properly supported by a retrieved source.  The function
`check_consistency()` returns a score and a list of missing claims.

Example:

```python
answer = "Paris is the capital of France [1]. The Eiffel Tower is 300m tall."
cites = {"1": "Paris is the capital of France."}
score, missing = check_consistency(answer, cites)
```
"""
from __future__ import annotations
from typing import Dict, List, Tuple
import re
import difflib

def check_consistency(answer: str, cites: Dict[str, str],
                      k: int = 3) -> Tuple[float, List[str]]:
    """
    Compute a citation consistency score.

    Parameters
    ----------
    answer : str
        The generated answer which may contain citation markers like "[1]".
    cites : Dict[str, str]
        A mapping from citation ids to the corresponding source text.
    k : int, optional
        Currently unused; reserved for future use (e.g. nearest‑neighbour spans).

    Returns
    -------
    Tuple[float, List[str]]
        A tuple of (score, missing), where score ∈ [0,1] indicates the fraction
        of claims that are covered by a cited span, and missing is a list of
        claim sentences that lacked a matching citation.

    This function identifies candidate claim sentences by splitting the answer
    on punctuation.  A claim is considered supported if at least one cited
    span contains a reasonably similar phrase.
    """
    sentences = re.split(r'(?<=[\.\?\!])\s+', answer)
    claims = [s for s in sentences if any(ch.isdigit() for ch in s)
              or any(w.istitle() for w in s.split()[:3])]
    ok = 0
    missing: List[str] = []
    for s in claims:
        ids = re.findall(r'\[(\w+)\]', s)
        span_text = " ".join(cites.get(i, "") for i in ids)
        ratio = difflib.SequenceMatcher(a=s.lower(), b=span_text.lower()).ratio()
        if ratio > 0.35 and ids:
            ok += 1
        else:
            missing.append(s)
    score = ok / max(1, len(claims))
    return score, missing
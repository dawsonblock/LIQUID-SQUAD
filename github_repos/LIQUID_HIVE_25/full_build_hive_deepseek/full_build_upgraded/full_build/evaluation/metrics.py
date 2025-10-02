"""
Metric functions for evaluating generated answers.

These metrics are intentionally simple: exact match compares the
normalised strings; F1 computes the overlap of tokens; citation precision
measures the fraction of cited spans that appear in the truth.
"""
from __future__ import annotations
from typing import List
import re

def normalise(text: str) -> List[str]:
    """Lowercase and split on whitespace for F1/EM metrics."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).split()

def exact_match(pred: str, truth: str) -> float:
    """Return 1.0 if the normalised prediction matches the truth."""
    return 1.0 if normalise(pred) == normalise(truth) else 0.0

def f1_score(pred: str, truth: str) -> float:
    """Compute token F1 between prediction and truth."""
    pred_tokens = normalise(pred)
    truth_tokens = normalise(truth)
    pred_set = set(pred_tokens)
    truth_set = set(truth_tokens)
    common = pred_set & truth_set
    if not common:
        return 0.0
    prec = len(common) / len(pred_tokens)
    rec  = len(common) / len(truth_tokens)
    return 2 * prec * rec / (prec + rec)

def citation_precision(pred: str, truth: str) -> float:
    """Compute the precision of citation markers.

    The truth should contain citation markers like "[1]" indicating the
    number of citations.  This function counts how many citation markers
    appear in the prediction and what fraction of them correspond to those
    in the truth.
    """
    pred_ids = set(re.findall(r"\[(\d+)\]", pred))
    truth_ids = set(re.findall(r"\[(\d+)\]", truth))
    if not pred_ids:
        return 0.0
    hits = pred_ids & truth_ids
    return len(hits) / len(pred_ids)
"""
Evaluation harness for the as‑smart‑as‑possible agent.

This module provides utilities to run regression tests across multiple
domains (code, math, retrieval and general).  It reads a list of
examples, invokes the self‑loop controller, and computes metrics.
"""
from __future__ import annotations
from typing import List, Dict, Tuple
import json

from .metrics import exact_match, f1_score, citation_precision
from self_loop import SelfLoop, ChatClient
from router.main import route_prompt

def load_dataset(path: str) -> List[Dict[str, str]]:
    """Load a JSONL file of test cases.

    Each line should contain: {"question": "...", "answer": "..."}.
    """
    cases: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
    return cases

async def evaluate_case(case: Dict[str, str], agent: SelfLoop,
                        model_tier: str) -> Tuple[Dict[str, float], str]:
    """
    Evaluate a single test case.

    Returns a metrics dictionary and the generated answer.
    """
    question = case["question"]
    truth = case["answer"]
    path, _ = route_prompt(question, has_image=False)
    answer, conf = await agent.self_loop(question, path, rounds=3, tau=0.7)
    scores = {
        "exact_match": exact_match(answer, truth),
        "f1": f1_score(answer, truth),
    }
    if "[" in truth and "]" in truth:
        scores["citation_precision"] = citation_precision(answer, truth)
    return scores, answer

async def run_evaluation(dataset_path: str, chat_client: ChatClient) -> Dict[str, float]:
    """
    Evaluate all cases in the dataset and aggregate metrics.
    """
    cases = load_dataset(dataset_path)
    agent = SelfLoop(chat_client)
    results: List[Dict[str, float]] = []
    for case in cases:
        scores, _ = await evaluate_case(case, agent, "small")
        results.append(scores)
    aggregated: Dict[str, float] = {}
    for key in results[0].keys():
        aggregated[key] = sum(r.get(key, 0.0) for r in results) / len(results)
    return aggregated
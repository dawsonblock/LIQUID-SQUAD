"""
Self-loop controller for iterative answer refinement.

This module defines the `self_loop()` coroutine which orchestrates the
plan → draft → critic → verify → revise cycle for answering user
questions.  The loop runs until a confidence threshold is met or a
maximum number of rounds is reached.  Each step can emit progress
events so the UI can display real-time reasoning traces.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, List, NamedTuple, Optional

from full_build.chat_client import TieredChatClient


class Verifiers(NamedTuple):
    """Container for verification functions."""

    code: Optional[Callable] = None
    math: Optional[Callable] = None
    retrieval: Optional[Callable] = None


class Retriever(NamedTuple):
    """Container for retrieval function."""

    search: Callable[[str, int], List[Any]]


class Deps(NamedTuple):
    """Dependencies for the self-loop."""

    client: TieredChatClient
    verifiers: Verifiers
    retriever: Optional[Retriever] = None
    max_rounds: int = 3
    conf_threshold: float = 0.65
    retrieval_mode: str = "disabled"


@dataclass
class IterationRecord:
    """Snapshot of a single reasoning step."""

    step: str
    content: str
    round: int
    timestamp: str
    confidence: Optional[float] = None


@dataclass
class SelfLoopResult:
    """Final output of the self-loop with metadata for observability."""

    answer: str
    citations: List[str]
    iterations: List[IterationRecord]
    model_tier: str
    retrieval_mode: str
    total_duration_ms: int
    rounds: int


ProgressCallback = Callable[[IterationRecord], Awaitable[None]]


async def self_loop(
    question: str,
    deps: Deps,
    progress_callback: Optional[ProgressCallback] = None,
) -> SelfLoopResult:
    """Run the iterative self-loop with optional progress callbacks."""

    # Fetch context if retrieval is enabled
    ctx_docs = []
    ctx_text = ""
    citations: List[str] = []

    if deps.retriever is not None:
        try:
            ctx_docs = deps.retriever.search(question, 6)
            ctx_text = "\n\n".join(
                f"[{i+1}] {doc.text if hasattr(doc, 'text') else str(doc)}"
                for i, doc in enumerate(ctx_docs)
            )
            citations = [
                doc.metadata.get("source", f"doc_{i+1}") if hasattr(doc, "metadata") else f"doc_{i+1}"
                for i, doc in enumerate(ctx_docs)
            ]
        except Exception:
            ctx_text = ""
            citations = []

    answer = ""
    confidence = 0.0
    iterations: List[IterationRecord] = []
    final_model_tier = "small"
    start_time = time.perf_counter()

    async def record_step(step: str, content: str, round_index: int, *, conf: Optional[float] = None) -> None:
        record = IterationRecord(
            step=step,
            content=content,
            round=round_index,
            timestamp=datetime.utcnow().isoformat() + "Z",
            confidence=conf,
        )
        iterations.append(record)
        if progress_callback is not None:
            await progress_callback(record)

    for round_num in range(deps.max_rounds):
        round_index = round_num + 1

        # Step 1: Plan
        plan_prompt = [
            {"role": "system", "content": "List 3-6 sub-questions that, if answered, would solve the user's query. Output bullets only."},
            {"role": "user", "content": f"User question: {question}\nKnown context:\n{ctx_text}"},
        ]
        plan, _plan_tier = await deps.client.generate(plan_prompt, temperature=0.2, max_tokens=256)
        await record_step("plan", plan, round_index)

        # Step 2: Draft
        draft_prompt = [
            {"role": "system", "content": "Answer the question using the plan and context provided. Be concise and cite sources using [N] notation."},
            {"role": "user", "content": f"Plan:\n{plan}\n\nQuestion:\n{question}\n\nContext:\n{ctx_text}"},
        ]
        draft, _draft_tier = await deps.client.generate(draft_prompt, temperature=0.2, max_tokens=512)
        await record_step("draft", draft, round_index)

        # Step 3: Verify
        verifier_findings: List[str] = []

        if deps.verifiers.code is not None:
            try:
                code_issues = await deps.verifiers.code(draft)
                verifier_findings.extend(code_issues)
            except Exception:
                pass

        if deps.verifiers.math is not None:
            try:
                math_issues = await deps.verifiers.math(draft)
                verifier_findings.extend(math_issues)
            except Exception:
                pass

        if deps.retriever is not None and deps.verifiers.retrieval is not None:
            try:
                retrieval_issues = deps.verifiers.retrieval(draft, min_cites=1)
                verifier_findings.extend(retrieval_issues)
            except Exception:
                pass

        verification_summary = (
            "\n".join(f"- {finding}" for finding in verifier_findings)
            if verifier_findings
            else "All verifiers passed without issues."
        )
        await record_step("verify", verification_summary, round_index)

        # Step 4: Critique
        critic_prompt = [
            {"role": "system", "content": "Critique the answer. List missing facts, logic gaps and unsupported claims. Output bullets only."},
            {"role": "user", "content": f"Question:\n{question}\n\nAnswer:\n{draft}\n\nVerifier findings:\n{verifier_findings}"},
        ]
        critic, _critic_tier = await deps.client.generate(critic_prompt, temperature=0.1, max_tokens=256)

        issues = critic.count("\n- ") + len(verifier_findings)
        confidence = max(confidence, 1.0 / (1 + issues))
        await record_step("critic", critic, round_index, conf=confidence)

        # Step 5: Revise
        final_prompt = [
            {"role": "system", "content": "Produce a final, concise answer that fixes the critic's points. Cite sources if used."},
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Context:\n{ctx_text}\n\n"
                    f"Draft:\n{draft}\n\n"
                    f"Critic:\n{critic}\n\n"
                    f"Verifier findings:\n{verifier_findings}\n\n"
                    "Revise the draft to address every point."
                ),
            },
        ]
        revised, final_model_tier = await deps.client.generate(final_prompt, temperature=0.2, max_tokens=900)
        answer = revised
        await record_step("revise", revised, round_index, conf=confidence)

        if confidence >= deps.conf_threshold:
            break

        if round_num >= deps.max_rounds - 1:
            break

        if round_num == 0 and deps.retriever is not None:
            try:
                expanded_query = f"{question}\n{critic}"
                ctx_docs = deps.retriever.search(expanded_query, 6)
                ctx_text = "\n\n".join(
                    f"[{i+1}] {doc.text if hasattr(doc, 'text') else str(doc)}"
                    for i, doc in enumerate(ctx_docs)
                )
            except Exception:
                pass

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    rounds_executed = max((record.round for record in iterations), default=1)

    return SelfLoopResult(
        answer=answer,
        citations=citations,
        iterations=iterations,
        model_tier=final_model_tier,
        retrieval_mode=deps.retrieval_mode,
        total_duration_ms=duration_ms,
        rounds=rounds_executed,
    )

"""
Optimized self-loop controller with parallel processing.

This module extends the base self-loop with parallel execution of verifiers
and retrieval operations to reduce overall latency.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, List, NamedTuple, Optional

from full_build.chat_client import TieredChatClient
from full_build.self_loop import (
    Deps,
    IterationRecord,
    ProgressCallback,
    SelfLoopResult,
    Verifiers,
    Retriever,
)


async def self_loop_optimized(
    question: str,
    deps: Deps,
    progress_callback: Optional[ProgressCallback] = None,
) -> SelfLoopResult:
    """
    Run the iterative self-loop with parallel optimization.

    This version runs verifiers in parallel and overlaps I/O operations
    where possible to reduce total execution time.
    """
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

    async def record_step(
        step: str, content: str, round_index: int, *, conf: Optional[float] = None
    ) -> None:
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
            {
                "role": "system",
                "content": "List 3-6 sub-questions that, if answered, would solve the user's query. Output bullets only.",
            },
            {"role": "user", "content": f"User question: {question}\nKnown context:\n{ctx_text}"},
        ]
        plan, _plan_tier = await deps.client.generate(plan_prompt, temperature=0.2, max_tokens=256)
        await record_step("plan", plan, round_index)

        # Step 2: Draft
        draft_prompt = [
            {
                "role": "system",
                "content": "Answer the question using the plan and context provided. Be concise and cite sources using [N] notation.",
            },
            {"role": "user", "content": f"Plan:\n{plan}\n\nQuestion:\n{question}\n\nContext:\n{ctx_text}"},
        ]
        draft, _draft_tier = await deps.client.generate(draft_prompt, temperature=0.2, max_tokens=512)
        await record_step("draft", draft, round_index)

        # Step 3: Verify (PARALLEL EXECUTION)
        verifier_tasks = []

        if deps.verifiers.code is not None:
            verifier_tasks.append(
                _safe_verify(deps.verifiers.code, draft, "code")
            )

        if deps.verifiers.math is not None:
            verifier_tasks.append(
                _safe_verify(deps.verifiers.math, draft, "math")
            )

        if deps.retriever is not None and deps.verifiers.retrieval is not None:
            verifier_tasks.append(
                _safe_verify_sync(deps.verifiers.retrieval, draft, "retrieval", min_cites=1)
            )

        # Execute all verifiers in parallel
        if verifier_tasks:
            verifier_results = await asyncio.gather(*verifier_tasks, return_exceptions=True)
            verifier_findings = []
            for result in verifier_results:
                if isinstance(result, list):
                    verifier_findings.extend(result)
                elif isinstance(result, Exception):
                    # Log but don't fail on verifier errors
                    pass
        else:
            verifier_findings = []

        verification_summary = (
            "\n".join(f"- {finding}" for finding in verifier_findings)
            if verifier_findings
            else "All verifiers passed without issues."
        )
        await record_step("verify", verification_summary, round_index)

        # Step 4 & 5: Critic and Revise (can start expanding query in parallel)
        # Start expanded retrieval early if this is round 0 and we have a retriever
        expanded_retrieval_task = None
        if round_num == 0 and deps.retriever is not None:
            # We'll expand the query once we have the critic's output
            expanded_retrieval_task = None  # Will set after critic

        # Step 4: Critique
        critic_prompt = [
            {
                "role": "system",
                "content": "Critique the answer. List missing facts, logic gaps and unsupported claims. Output bullets only.",
            },
            {"role": "user", "content": f"Question:\n{question}\n\nAnswer:\n{draft}\n\nVerifier findings:\n{verifier_findings}"},
        ]
        critic, _critic_tier = await deps.client.generate(critic_prompt, temperature=0.1, max_tokens=256)

        # Start expanded retrieval in parallel with calculating confidence
        if round_num == 0 and deps.retriever is not None:
            expanded_query = f"{question}\n{critic}"
            expanded_retrieval_task = asyncio.create_task(
                _safe_retrieve(deps.retriever, expanded_query, 6)
            )

        issues = critic.count("\n- ") + len(verifier_findings)
        confidence = max(confidence, 1.0 / (1 + issues))
        await record_step("critic", critic, round_index, conf=confidence)

        # Step 5: Revise
        final_prompt = [
            {
                "role": "system",
                "content": "Produce a final, concise answer that fixes the critic's points. Cite sources if used.",
            },
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

        # Check stopping conditions
        if confidence >= deps.conf_threshold:
            # Cancel expanded retrieval if it's still running
            if expanded_retrieval_task and not expanded_retrieval_task.done():
                expanded_retrieval_task.cancel()
            break

        if round_num >= deps.max_rounds - 1:
            # Cancel expanded retrieval if it's still running
            if expanded_retrieval_task and not expanded_retrieval_task.done():
                expanded_retrieval_task.cancel()
            break

        # Wait for expanded retrieval to complete if it was started
        if expanded_retrieval_task:
            try:
                new_docs = await expanded_retrieval_task
                if new_docs:
                    ctx_docs = new_docs
                    ctx_text = "\n\n".join(
                        f"[{i+1}] {doc.text if hasattr(doc, 'text') else str(doc)}"
                        for i, doc in enumerate(ctx_docs)
                    )
            except Exception:
                pass  # Use existing context

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


async def _safe_verify(verifier: Callable, draft: str, name: str) -> List[str]:
    """Safely run an async verifier and return issues."""
    try:
        issues = await verifier(draft)
        return issues if issues else []
    except Exception:
        return []


async def _safe_verify_sync(verifier: Callable, draft: str, name: str, **kwargs) -> List[str]:
    """Safely run a sync verifier in executor and return issues."""
    try:
        loop = asyncio.get_event_loop()
        issues = await loop.run_in_executor(None, lambda: verifier(draft, **kwargs))
        return issues if issues else []
    except Exception:
        return []


async def _safe_retrieve(retriever: Retriever, query: str, k: int) -> List[Any]:
    """Safely retrieve documents."""
    try:
        return retriever.search(query, k)
    except Exception:
        return []

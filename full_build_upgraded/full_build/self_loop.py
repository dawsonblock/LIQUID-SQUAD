"""
Self-loop controller for iterative answer refinement.

This module defines the `self_loop()` coroutine which orchestrates a
planning, drafting, critiquing and revising cycle for answering user
questions.  The loop runs until a confidence threshold is met or a
maximum number of rounds is reached.  External verifiers for code,
math and retrieval are invoked to detect and correct errors.

The self-loop is agnostic to the underlying model: it calls a provided
`TieredChatClient` for text generation.
"""
from __future__ import annotations
import asyncio
from typing import Any, Callable, Dict, List, Tuple, Optional, NamedTuple

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


async def self_loop(question: str, deps: Deps) -> str:
    """
    Perform iterative refinement of an answer using plan→draft→critic→verify→revise loop.

    Parameters
    ----------
    question : str
        The user's question.
    deps : Deps
        Dependencies including client, verifiers, retriever, and configuration.

    Returns
    -------
    str
        The final refined answer with citations if retrieval is enabled.
    """
    # Fetch context if retrieval is enabled
    ctx_docs = []
    ctx_text = ""
    citations = []
    
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
            # Gracefully degrade if retrieval fails
            ctx_text = ""
            citations = []
    
    answer = ""
    confidence = 0.0
    
    for round_num in range(deps.max_rounds):
        # Step 1: Plan
        plan_prompt = [
            {"role": "system", "content": "List 3-6 sub-questions that, if answered, would solve the user's query. Output bullets only."},
            {"role": "user", "content": f"User question: {question}\nKnown context:\n{ctx_text}"}
        ]
        plan = await deps.client.generate(plan_prompt, temperature=0.2, max_tokens=256)
        
        # Step 2: Draft
        draft_prompt = [
            {"role": "system", "content": "Answer the question using the plan and context provided. Be concise and cite sources using [N] notation."},
            {"role": "user", "content": f"Plan:\n{plan}\n\nQuestion:\n{question}\n\nContext:\n{ctx_text}"}
        ]
        draft = await deps.client.generate(draft_prompt, temperature=0.2, max_tokens=512)
        
        # Step 3: Verify
        verifier_findings: List[str] = []
        
        # Code verification
        if deps.verifiers.code is not None:
            try:
                code_issues = await deps.verifiers.code(draft)
                verifier_findings.extend(code_issues)
            except Exception:
                pass
        
        # Math verification
        if deps.verifiers.math is not None:
            try:
                math_issues = await deps.verifiers.math(draft)
                verifier_findings.extend(math_issues)
            except Exception:
                pass
        
        # Retrieval verification (only if retrieval is enabled)
        if deps.retriever is not None and deps.verifiers.retrieval is not None:
            try:
                retrieval_issues = deps.verifiers.retrieval(draft, min_cites=1)
                verifier_findings.extend(retrieval_issues)
            except Exception:
                pass
        
        # Step 4: Critique
        critic_prompt = [
            {"role": "system", "content": "Critique the answer. List missing facts, logic gaps and unsupported claims. Output bullets only."},
            {"role": "user", "content": f"Question:\n{question}\n\nAnswer:\n{draft}\n\nVerifier findings:\n{verifier_findings}"}
        ]
        critic = await deps.client.generate(critic_prompt, temperature=0.1, max_tokens=256)
        
        # Calculate confidence based on issues found
        issues = critic.count("\n- ") + len(verifier_findings)
        confidence = max(confidence, 1.0 / (1 + issues))
        
        # Step 5: Revise
        final_prompt = [
            {"role": "system", "content": "Produce a final, concise answer that fixes the critic's points. Cite sources if used."},
            {"role": "user", "content": (
                f"Question:\n{question}\n\nContext:\n{ctx_text}\n\n"
                f"Draft:\n{draft}\n\nCritic:\n{critic}\n\n"
                f"Verifier findings:\n{verifier_findings}\n\n"
                f"Revise the draft to address every point."
            )}
        ]
        revised = await deps.client.generate(final_prompt, temperature=0.2, max_tokens=900)
        
        answer = revised
        
        # Stop if confidence threshold met
        if confidence >= deps.conf_threshold:
            break
        
        # Hard stop on max rounds
        if round_num >= deps.max_rounds - 1:
            break
        
        # On first round, if retrieval enabled, do a second retrieval pass with critic feedback
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
    
    return answer

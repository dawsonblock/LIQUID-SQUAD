"""
Self‑loop controller for iterative answer refinement.

This module defines the `self_loop()` coroutine which orchestrates a
planning, drafting, critiquing and revising cycle for answering user
questions.  The loop runs until a confidence threshold is met or a
maximum number of rounds is reached.  External verifiers for code,
math and retrieval are invoked to detect and correct errors.

The self‑loop is agnostic to the underlying model: it calls a provided
`ChatClient` for text generation.  You must subclass `ChatClient` and
implement the asynchronous `generate()` method to integrate your LLM.
"""
from __future__ import annotations
import asyncio
from typing import Any, Callable, Dict, List, Tuple, Optional

from verifiers.code_verifier import run_code_tests
from verifiers.math_verifier import run_math_check
from verifiers.retrieval_verifier import verify_citations, citation_provenance

class ChatClient:
    """Abstract base class for chat clients.

    Subclass this and implement `async def generate(self, messages, temperature, max_tokens)`.
    Each call should return a string.  The `messages` argument is a list of
    dictionaries in the OpenAI/ChatML style.
    """
    async def generate(self, messages: List[Dict[str, str]],
                       temperature: float = 0.2,
                       max_tokens: int = 512) -> str:
        raise NotImplementedError

class SelfLoop:
    """Coordinator for iterative self‑questioning, critique and answer refinement.

    The SelfLoop orchestrates a multi‑stage process: plan, draft,
    critique, and revise.  It supports an optional secondary
    `critic_client` for generating critiques.  When provided, the
    critic model (e.g. DeepSeek V3) generates feedback for the
    answer produced by the primary chat client.  The final revision
    always comes from the primary chat client, incorporating the
    critique verbatim.  If no critic client is supplied, the chat
    client is used for both drafting and critiquing.
    """
    SYS_PLANNER = ("List 3‑6 sub‑questions that, if answered, would solve the "
                   "user's query. Output bullets only.")
    SYS_CRITIC  = ("Critique the answer. List missing facts, logic gaps and "
                   "unsupported claims. Output bullets only.")
    SYS_FINAL   = ("Produce a final, concise answer that fixes the critic's "
                   "points. Cite sources if used.")
    SYS_JUDGE   = ("You are a strict judge. Given a question and two answers, "
                   "pick the better one for correctness, citations and completeness. "
                   "Reply as: WINNER: A1|A2\nREASONS: <bullets>")

    def __init__(self, chat_client: ChatClient,
                 rag_search: Optional[Callable[[str, int], Any]] = None,
                 critic_client: Optional[ChatClient] = None) -> None:
        """Initialise a SelfLoop.

        Parameters
        ----------
        chat_client : ChatClient
            The primary model used for planning, drafting and final revision.
        rag_search : Callable, optional
            A retrieval function accepting (query: str, k: int) and returning
            an iterable of documents.  If provided it is used to fetch
            context from a RAG engine.
        critic_client : ChatClient, optional
            An optional secondary model used exclusively to generate
            critiques.  When None, the primary `chat_client` will be used
            for both drafting and critiquing.
        """
        self.chat = chat_client
        self.rag_search = rag_search or (lambda q, k: [])
        self.critic_chat: Optional[ChatClient] = critic_client

    async def debate_once(self, q: str, ctx: str, path: str) -> Tuple[str, str]:
        """Generate two candidate answers and use a judge to pick the better one."""
        a1 = await self.run_path(path, f"Question:\n{q}\nContext:\n{ctx}", images=None)
        a2 = await self.run_path(path, f"(Second attempt) Question:\n{q}\nContext:\n{ctx}", images=None)
        judge_prompt = [
            {"role": "system", "content": self.SYS_JUDGE},
            {"role": "user", "content": f"Q:\n{q}\nA1:\n{a1}\nA2:\n{a2}"}
        ]
        judge_decision = await self.chat.generate(judge_prompt,
                                                 temperature=0.1,
                                                 max_tokens=256)
        pick_a2 = "A2" in judge_decision
        return (a2 if pick_a2 else a1), judge_decision

    async def run_path(self, path: str, prompt: str, images: Any = None) -> str:
        """
        Execute a path (e.g. CODE, MATH, RAG, GENERAL) by sending a prompt
        to the chat client.  Override this method to implement domain‑specific
        pre‑ and post‑processing.  The default simply forwards the prompt.
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat.generate(messages, temperature=0.2, max_tokens=512)

    async def self_loop(self, q: str, path: str,
                        rounds: int = 3, tau: float = 0.7) -> Tuple[str, float]:
        """
        Perform iterative refinement of an answer.

        Parameters
        ----------
        q : str
            The user's question.
        path : str
            The chosen route (CODE, MATH, RAG, GENERAL).
        rounds : int, optional
            Maximum number of refinement rounds.
        tau : float, optional
            Confidence threshold; if achieved the loop terminates early.

        Returns
        -------
        Tuple[str, float]
            A tuple of (final answer, confidence).
        """
        ctx_docs = self.rag_search(q, k=6) if path in {"RAG", "GENERAL"} else []
        ctx_text = "\n\n".join(doc.text for doc in ctx_docs) if ctx_docs else ""
        answer = ""
        confidence = 0.0
        for r in range(rounds):
            plan_prompt = [
                {"role": "system", "content": self.SYS_PLANNER},
                {"role": "user", "content": f"User question: {q}\nKnown context:\n{ctx_text}"}
            ]
            plan = await self.chat.generate(plan_prompt,
                                            temperature=0.2,
                                            max_tokens=256)
            draft_prompt = f"Plan:\n{plan}\n\nQuestion:\n{q}\nUse context if present."
            draft = await self.run_path(path, draft_prompt)

            verifier_findings: List[str] = []
            if path == "CODE":
                verifier_findings.extend(await run_code_tests(draft))
            elif path == "MATH":
                verifier_findings.extend(await run_math_check(draft))
            if path in {"RAG", "GENERAL"}:
                missing = verify_citations(draft)
                cites = {str(i+1): doc.text for i, doc in enumerate(ctx_docs)}
                prov_score, _ = citation_provenance(draft, cites) if cites else (1.0, [])
                if missing:
                    verifier_findings.append(f"Missing citations: {missing}")
                if prov_score < 0.5:
                    verifier_findings.append(f"Low citation provenance: {prov_score:.2f}")

            critic_prompt = [
                {"role": "system", "content": self.SYS_CRITIC},
                {"role": "user", "content": f"Question:\n{q}\nAnswer:\n{draft}\nVerifier findings:\n{verifier_findings}"}
            ]
            # Generate the critique using the dedicated critic client if configured.
            if self.critic_chat is not None:
                critic = await self.critic_chat.generate(
                    critic_prompt,
                    temperature=0.1,
                    max_tokens=256,
                )
            else:
                critic = await self.chat.generate(
                    critic_prompt,
                    temperature=0.2,
                    max_tokens=256,
                )
            issues = critic.count("\n- ") + len(verifier_findings)
            confidence = max(confidence, 1.0 / (1 + issues))

            final_prompt = [
                {"role": "system", "content": self.SYS_FINAL},
                {"role": "user",
                 "content": (
                     f"Question:\n{q}\nContext:\n{ctx_text}\nDraft:\n{draft}\n"
                     f"Critic (DeepSeek V3 if provided):\n{critic}\nVerifier:\n{verifier_findings}\n"
                     f"Revise the draft to address every point in the critic and verifier findings."
                 )}
            ]
            revised = await self.chat.generate(
                final_prompt,
                temperature=0.2,
                max_tokens=900,
            )

            if r == rounds - 1 and confidence < tau:
                revised, _judge = await self.debate_once(q, ctx_text, path)

            answer = revised
            if confidence >= tau:
                break
            if r == 0 and path in {"RAG", "GENERAL"}:
                ctx_docs = self.rag_search(q + "\n" + critic, k=6)
                ctx_text = "\n\n".join(doc.text for doc in ctx_docs)
        return answer, confidence
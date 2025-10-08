"""
Export utilities for saving conversation results in various formats.

This module provides functionality to export self-loop results, conversations,
and iterations in JSON, Markdown, and other formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from full_build.self_loop import IterationRecord, SelfLoopResult


class ResultExporter:
    """Exporter for self-loop results."""

    @staticmethod
    def to_json(result: SelfLoopResult, pretty: bool = True) -> str:
        """
        Export result as JSON.

        Args:
            result: The SelfLoopResult to export
            pretty: Whether to use pretty-printing

        Returns:
            JSON string
        """
        data = {
            "answer": result.answer,
            "citations": result.citations,
            "iterations": [
                {
                    "step": it.step,
                    "content": it.content,
                    "round": it.round,
                    "timestamp": it.timestamp,
                    "confidence": it.confidence,
                }
                for it in result.iterations
            ],
            "model_tier": result.model_tier,
            "retrieval_mode": result.retrieval_mode,
            "total_duration_ms": result.total_duration_ms,
            "rounds": result.rounds,
        }

        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)

    @staticmethod
    def to_markdown(
        result: SelfLoopResult,
        include_iterations: bool = True,
        include_metadata: bool = True,
    ) -> str:
        """
        Export result as Markdown.

        Args:
            result: The SelfLoopResult to export
            include_iterations: Whether to include iteration details
            include_metadata: Whether to include metadata section

        Returns:
            Markdown string
        """
        lines = []

        # Title
        lines.append("# Query Result")
        lines.append("")

        # Answer section
        lines.append("## Answer")
        lines.append("")
        lines.append(result.answer)
        lines.append("")

        # Citations section
        if result.citations:
            lines.append("## Sources")
            lines.append("")
            for i, citation in enumerate(result.citations, 1):
                lines.append(f"{i}. {citation}")
            lines.append("")

        # Metadata section
        if include_metadata:
            lines.append("## Metadata")
            lines.append("")
            lines.append(f"- **Model Tier**: {result.model_tier}")
            lines.append(f"- **Retrieval Mode**: {result.retrieval_mode}")
            lines.append(f"- **Rounds**: {result.rounds}")
            lines.append(f"- **Duration**: {result.total_duration_ms}ms")
            lines.append("")

        # Iterations section
        if include_iterations and result.iterations:
            lines.append("## Reasoning Process")
            lines.append("")

            current_round = 0
            for iteration in result.iterations:
                if iteration.round != current_round:
                    current_round = iteration.round
                    lines.append(f"### Round {current_round}")
                    lines.append("")

                # Step header
                step_emoji = {
                    "plan": "📋",
                    "draft": "✏️",
                    "verify": "✅",
                    "critic": "🔍",
                    "revise": "🔄",
                }.get(iteration.step, "•")

                confidence_str = ""
                if iteration.confidence is not None:
                    confidence_str = f" (Confidence: {iteration.confidence:.2%})"

                lines.append(f"#### {step_emoji} {iteration.step.title()}{confidence_str}")
                lines.append("")
                lines.append(iteration.content)
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_html(result: SelfLoopResult) -> str:
        """
        Export result as HTML.

        Args:
            result: The SelfLoopResult to export

        Returns:
            HTML string
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Query Result</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }",
            "h1, h2, h3 { color: #333; }",
            ".answer { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }",
            ".citation { background: #e3f2fd; padding: 10px; margin: 10px 0; border-left: 4px solid #2196f3; }",
            ".metadata { background: #f5f5f5; padding: 15px; border-radius: 4px; }",
            ".iteration { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }",
            ".step-header { font-weight: bold; color: #1976d2; margin-bottom: 10px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Query Result</h1>",
        ]

        # Answer
        html_parts.append("<h2>Answer</h2>")
        html_parts.append(f"<div class='answer'>{ResultExporter._escape_html(result.answer)}</div>")

        # Citations
        if result.citations:
            html_parts.append("<h2>Sources</h2>")
            for i, citation in enumerate(result.citations, 1):
                html_parts.append(
                    f"<div class='citation'>{i}. {ResultExporter._escape_html(citation)}</div>"
                )

        # Metadata
        html_parts.append("<h2>Metadata</h2>")
        html_parts.append("<div class='metadata'>")
        html_parts.append(f"<p><strong>Model Tier:</strong> {result.model_tier}</p>")
        html_parts.append(f"<p><strong>Retrieval Mode:</strong> {result.retrieval_mode}</p>")
        html_parts.append(f"<p><strong>Rounds:</strong> {result.rounds}</p>")
        html_parts.append(f"<p><strong>Duration:</strong> {result.total_duration_ms}ms</p>")
        html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )


class ConversationExporter:
    """Exporter for conversations."""

    @staticmethod
    def to_json(
        turns: List[dict],
        conversation_id: Optional[str] = None,
        pretty: bool = True,
    ) -> str:
        """
        Export conversation as JSON.

        Args:
            turns: List of conversation turns
            conversation_id: Optional conversation ID
            pretty: Whether to use pretty-printing

        Returns:
            JSON string
        """
        data = {
            "conversation_id": conversation_id,
            "turns": turns,
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }

        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)

    @staticmethod
    def to_markdown(turns: List[dict]) -> str:
        """
        Export conversation as Markdown.

        Args:
            turns: List of conversation turns

        Returns:
            Markdown string
        """
        lines = []
        lines.append("# Conversation")
        lines.append("")
        lines.append(f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        lines.append("")

        for i, turn in enumerate(turns, 1):
            lines.append(f"## Turn {i}")
            lines.append("")

            # Question
            lines.append("**User:**")
            lines.append("")
            lines.append(turn.get("question", ""))
            lines.append("")

            # Answer
            lines.append("**Assistant:**")
            lines.append("")
            lines.append(turn.get("answer", ""))
            lines.append("")

            # Citations if present
            citations = turn.get("citations", [])
            if citations:
                lines.append("**Sources:**")
                lines.append("")
                for j, citation in enumerate(citations, 1):
                    lines.append(f"{j}. {citation}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def export_result(
    result: SelfLoopResult,
    format: str = "json",
    **kwargs,
) -> str:
    """
    Export a result in the specified format.

    Args:
        result: The SelfLoopResult to export
        format: Export format ("json", "markdown", "html")
        **kwargs: Additional format-specific arguments

    Returns:
        Exported string in the specified format
    """
    exporter = ResultExporter()

    if format == "json":
        return exporter.to_json(result, **kwargs)
    elif format == "markdown" or format == "md":
        return exporter.to_markdown(result, **kwargs)
    elif format == "html":
        return exporter.to_html(result)
    else:
        raise ValueError(f"Unknown export format: {format}")

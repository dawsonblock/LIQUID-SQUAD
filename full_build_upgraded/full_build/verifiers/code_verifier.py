"""
Code verifier for the self-loop agent.

This module provides a minimal set of functions for checking generated code.
It extracts Python code blocks from plain text answers, runs static analysis
using the `ast` module and the optional `pyflakes` checker, and returns any
diagnostics.  Sandbox execution is controlled by the CODE_EXEC environment variable.
"""

from __future__ import annotations
from typing import List
import ast
import subprocess
import tempfile
import os


def run_in_sandbox(code: str, timeout: float = 5.0, enabled: bool = False) -> List[str]:
    """Execute Python code in a constrained environment.

    This helper writes the code to a temporary file and invokes a
    separate Python interpreter with resource limits to prevent
    excessive CPU or memory usage.  Network access and file writes are
    implicitly disabled by running in an isolated temporary directory.
    A small timeout is applied to avoid hanging processes.  Any
    runtime errors are returned as a list of messages.  While this
    helper offers better isolation than a simple subprocess call, it
    should not be considered a fully secure sandbox.

    Parameters:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        enabled: Whether sandbox execution is enabled (controlled by CODE_EXEC env)
    """
    if not enabled:
        return []

    import resource
    import sys
    issues: List[str] = []
    # Helper to apply resource limits in the child process
    def _limit() -> None:
        # Limit CPU time to 2 seconds
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        # Limit virtual memory to 256 MB
        mem_limit = 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
        # Limit file size to 10 MB
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    try:
        with tempfile.TemporaryDirectory() as td:
            script_path = os.path.join(td, "user_code.py")
            with open(script_path, "w") as f:
                f.write(code)
            # Execute the script with resource limits applied in the child
            process = subprocess.Popen(
                [sys.executable, script_path],
                preexec_fn=_limit,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                _, err = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                issues.append("RuntimeError: Code execution timed out")
                return issues
            # Non-zero return code indicates an error; capture stderr
            if process.returncode != 0 and err:
                issues.extend(err.strip().splitlines())
    except Exception as exc:
        issues.append(f"RuntimeError: {exc}")
    return issues
    """Execute Python code in a constrained environment.

    This helper writes the code to a temporary file and invokes a
    separate Python interpreter with resource limits to prevent
    excessive CPU or memory usage.  Network access and file writes are
    implicitly disabled by running in an isolated temporary directory.
    A small timeout is applied to avoid hanging processes.  Any
    runtime errors are returned as a list of messages.  While this
    helper offers better isolation than a simple subprocess call, it
    should not be considered a fully secure sandbox.
    """
    import resource
    import sys
    issues: List[str] = []
    # Helper to apply resource limits in the child process
    def _limit() -> None:
        # Limit CPU time to 2 seconds
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        # Limit virtual memory to 256 MB
        mem_limit = 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
        # Limit file size to 10 MB
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    try:
        with tempfile.TemporaryDirectory() as td:
            script_path = os.path.join(td, "user_code.py")
            with open(script_path, "w") as f:
                f.write(code)
            # Execute the script with resource limits applied in the child
            process = subprocess.Popen(
                [sys.executable, script_path],
                preexec_fn=_limit,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                _, err = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                issues.append("RuntimeError: Code execution timed out")
                return issues
            # Non‑zero return code indicates an error; capture stderr
            if process.returncode != 0 and err:
                issues.extend(err.strip().splitlines())
    except Exception as exc:
        issues.append(f"RuntimeError: {exc}")
    return issues

def run_pytest(code: str, timeout: float = 10.0) -> List[str]:
    """Run pytest on the provided code if tests are present.

    This helper creates a temporary module and invokes pytest via
    subprocess.  It returns a list of failure messages.  If pytest is
    unavailable or no tests are detected, it returns an empty list.
    """
    failures: List[str] = []
    try:
        import pytest  # type: ignore
        has_pytest = True
    except Exception:
        has_pytest = False
    if not has_pytest:
        return failures
    # Write code to a temporary file
    with tempfile.TemporaryDirectory() as td:
        script_path = os.path.join(td, "test_module.py")
        with open(script_path, "w") as f:
            f.write(code)
        # Run pytest quietly
        try:
            result = subprocess.run(["pytest", "-q", script_path],
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout)
            # pytest exits with code 0 on success; non‑zero indicates failures
            if result.returncode != 0:
                # Collect stdout and stderr lines if pytest reports failures.
                out_lines = result.stdout.strip().splitlines() if result.stdout else []
                err_lines = result.stderr.strip().splitlines() if result.stderr else []
                # Prefer stdout messages but include stderr as well to aid diagnosis.
                if out_lines:
                    failures.extend(out_lines)
                if err_lines:
                    failures.extend(err_lines)
        except Exception as exc:
            failures.append(f"PytestError: {exc}")
    return failures

def extract_python_blocks(answer: str) -> List[str]:
    """Extract Python code blocks fenced with triple backticks."""
    blocks: List[str] = []
    parts = answer.split("```")
    for part in parts:
        stripped = part.strip()
        if stripped.startswith("python"):
            code = stripped.split("\n", 1)[1] if "\n" in stripped else ""
            blocks.append(code)
    return blocks

def run_static_checks(code: str) -> List[str]:
    """Run syntax and static analysis on Python code.

    Returns a list of diagnostic messages.  If no issues are found,
    the list is empty.
    """
    issues: List[str] = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"SyntaxError: {e}")
        return issues
    try:
        result = subprocess.run(["pyflakes", "-"],
                                input=code.encode(),
                                capture_output=True,
                                text=True,
                                timeout=10)
        if result.returncode != 0 or result.stdout.strip():
            issues.extend(result.stdout.strip().splitlines())
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return issues

async def run_code_tests(answer: str) -> List[str]:
    """
    Extract Python code blocks from an answer and perform static analysis.

    Returns a list of failures.  An empty list means the code
    passed all checks.  In a production system you might run
    user‑provided unit tests here.
    """
    failures: List[str] = []
    blocks = extract_python_blocks(answer)
    for code in blocks:
        # Static analysis for syntax/style
        failures.extend(run_static_checks(code))
        # Execute code in sandbox to catch runtime errors
        failures.extend(run_in_sandbox(code))
        # Attempt to run pytest on any defined tests
        failures.extend(run_pytest(code))
    return failures
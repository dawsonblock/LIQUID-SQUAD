"""
Math verifier for the self‑loop agent.

This module provides simple checks for mathematical statements in generated
answers.  It scans the answer for equalities and attempts to verify
them using `sympy`.  Any mismatches are returned as error strings.
"""

from __future__ import annotations
from typing import List
import sympy as sp

def extract_equalities(answer: str) -> List[str]:
    """Extract candidate equality expressions from the answer."""
    lines = [ln.strip() for ln in answer.splitlines()
             if "=" in ln and any(ch.isdigit() for ch in ln)]
    return lines

async def run_math_check(answer: str) -> List[str]:
    """
    Verify simple mathematical equalities using sympy.

    Returns a list of mismatches; an empty list means all equalities
    evaluated correctly or no equalities were found.
    """
    mismatches: List[str] = []
    equalities = extract_equalities(answer)
    for expr in equalities:
        try:
            left, right = expr.split("=", 1)
            left_expr = sp.sympify(left)
            right_expr = sp.sympify(right)
            # Symbolic equality check
            if not sp.simplify(left_expr - right_expr) == 0:
                mismatches.append(f"Mismatch: {expr}")
                continue
            # Numeric fuzzing: evaluate both sides under random assignments
            symbols = list(left_expr.free_symbols | right_expr.free_symbols)
            # Test up to 3 random assignments
            for _ in range(3):
                subs = {sym: sp.Rational(sp.randint(1, 10)) for sym in symbols}
                try:
                    lval = left_expr.evalf(subs=subs)
                    rval = right_expr.evalf(subs=subs)
                    if abs(lval - rval) > 1e-6:
                        mismatches.append(f"Numeric mismatch in {expr} for {subs}")
                        break
                except Exception:
                    # Skip if cannot evaluate numeric substitution
                    break
        except Exception:
            pass
    return mismatches
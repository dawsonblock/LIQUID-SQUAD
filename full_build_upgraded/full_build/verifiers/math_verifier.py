"""
Math verifier for the self-loop agent.

This module provides simple checks for mathematical statements in generated
answers.  It scans the answer for equalities and attempts to verify
them using `sympy`.  Any mismatches are returned as error strings.
"""

from __future__ import annotations
from typing import List
import sympy as sp


def check_equivalence(expr_str_a: str, expr_str_b: str) -> bool:
    """Check if two mathematical expressions are symbolically equivalent.
    
    Parameters:
        expr_str_a: First expression as string
        expr_str_b: Second expression as string
        
    Returns:
        True if expressions are equivalent, False otherwise
    """
    try:
        expr_a = sp.sympify(expr_str_a)
        expr_b = sp.sympify(expr_str_b)
        return sp.simplify(expr_a - expr_b) == 0
    except Exception:
        return False


def spot_check(expr_str: str, subs_ranges: dict = None, num_checks: int = 3) -> List[str]:
    """Perform random numeric spot checks on an expression.
    
    Parameters:
        expr_str: Expression to check
        subs_ranges: Dictionary mapping symbol names to (min, max) ranges
        num_checks: Number of random checks to perform
        
    Returns:
        List of error messages if checks fail
    """
    issues: List[str] = []
    try:
        expr = sp.sympify(expr_str)
        symbols = list(expr.free_symbols)
        
        if not symbols:
            return issues
        
        for _ in range(num_checks):
            subs = {}
            for sym in symbols:
                if subs_ranges and str(sym) in subs_ranges:
                    min_val, max_val = subs_ranges[str(sym)]
                    subs[sym] = sp.Rational(sp.randint(min_val, max_val))
                else:
                    subs[sym] = sp.Rational(sp.randint(1, 10))
            
            try:
                val = expr.evalf(subs=subs)
                # Check for NaN or infinity
                if not val.is_finite:
                    issues.append(f"Expression evaluates to non-finite value for {subs}")
            except Exception as e:
                issues.append(f"Evaluation error for {subs}: {e}")
    except Exception as e:
        issues.append(f"Failed to parse expression: {e}")
    
    return issues


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
            
            # Use check_equivalence
            if not check_equivalence(left, right):
                mismatches.append(f"Mismatch: {expr}")
                continue
            
            # Use spot_check for numeric validation
            left_expr = sp.sympify(left)
            right_expr = sp.sympify(right)
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

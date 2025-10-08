"""
Input validation and sanitization utilities.

This module provides robust input validation to prevent injection attacks,
ensure data quality, and provide clear error messages for invalid inputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationError:
    """Container for validation error details."""

    field: str
    message: str
    value: Any = None


class ValidationResult:
    """Result of input validation with detailed error information."""

    def __init__(self) -> None:
        self.errors: List[ValidationError] = []

    def add_error(self, field: str, message: str, value: Any = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, value=value))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "valid": self.is_valid,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                }
                for e in self.errors
            ],
        }


class QuestionValidator:
    """Validator for user questions."""

    # Pattern for detecting potentially malicious input
    SUSPICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"eval\s*\(",  # Eval calls
        r"\\x[0-9a-fA-F]{2}",  # Hex escapes
        r"\\u[0-9a-fA-F]{4}",  # Unicode escapes that could be obfuscation
    ]

    def __init__(
        self,
        min_length: int = 3,
        max_length: int = 5000,
        allow_special_chars: bool = True,
    ) -> None:
        """
        Initialize the validator.

        Args:
            min_length: Minimum question length
            max_length: Maximum question length
            allow_special_chars: Whether to allow special characters
        """
        self.min_length = min_length
        self.max_length = max_length
        self.allow_special_chars = allow_special_chars
        self.suspicious_pattern = re.compile(
            "|".join(self.SUSPICIOUS_PATTERNS), re.IGNORECASE | re.DOTALL
        )

    def validate(self, question: str) -> ValidationResult:
        """
        Validate a user question.

        Args:
            question: The question text to validate

        Returns:
            ValidationResult with any errors found
        """
        result = ValidationResult()

        # Check if question is None or not a string
        if question is None:
            result.add_error("question", "Question cannot be null")
            return result

        if not isinstance(question, str):
            result.add_error("question", "Question must be a string")
            return result

        # Strip whitespace for length checks
        stripped = question.strip()

        # Check length constraints
        if len(stripped) < self.min_length:
            result.add_error(
                "question",
                f"Question must be at least {self.min_length} characters",
                value=len(stripped),
            )

        if len(stripped) > self.max_length:
            result.add_error(
                "question",
                f"Question must not exceed {self.max_length} characters",
                value=len(stripped),
            )

        # Check for empty or whitespace-only
        if not stripped:
            result.add_error("question", "Question cannot be empty or whitespace-only")

        # Check for suspicious patterns
        if self.suspicious_pattern.search(question):
            result.add_error(
                "question",
                "Question contains potentially unsafe content",
            )

        # Check for excessive special characters (possible injection attempt)
        if not self.allow_special_chars:
            special_char_count = sum(1 for c in stripped if not c.isalnum() and not c.isspace())
            if special_char_count > len(stripped) * 0.3:  # More than 30% special chars
                result.add_error(
                    "question",
                    "Question contains too many special characters",
                )

        # Check for null bytes
        if "\x00" in question:
            result.add_error("question", "Question contains null bytes")

        # Check for control characters (except common whitespace)
        control_chars = [c for c in question if ord(c) < 32 and c not in "\n\r\t"]
        if control_chars:
            result.add_error("question", "Question contains invalid control characters")

        return result

    def sanitize(self, question: str) -> str:
        """
        Sanitize a question by removing potentially harmful content.

        Args:
            question: The question to sanitize

        Returns:
            Sanitized question string
        """
        if not isinstance(question, str):
            return ""

        # Remove null bytes
        sanitized = question.replace("\x00", "")

        # Remove control characters except newline, tab, and carriage return
        sanitized = "".join(
            c for c in sanitized if ord(c) >= 32 or c in "\n\r\t"
        )

        # Normalize whitespace
        sanitized = " ".join(sanitized.split())

        # Limit length
        if len(sanitized) > self.max_length:
            sanitized = sanitized[: self.max_length]

        return sanitized


class ConfigValidator:
    """Validator for configuration parameters."""

    @staticmethod
    def validate_max_rounds(max_rounds: int) -> ValidationResult:
        """Validate max_rounds parameter."""
        result = ValidationResult()

        if not isinstance(max_rounds, int):
            result.add_error("max_rounds", "Must be an integer", value=max_rounds)
            return result

        if max_rounds < 1:
            result.add_error("max_rounds", "Must be at least 1", value=max_rounds)
        elif max_rounds > 10:
            result.add_error("max_rounds", "Must not exceed 10", value=max_rounds)

        return result

    @staticmethod
    def validate_conf_threshold(conf_threshold: float) -> ValidationResult:
        """Validate confidence threshold parameter."""
        result = ValidationResult()

        if not isinstance(conf_threshold, (int, float)):
            result.add_error(
                "conf_threshold", "Must be a number", value=conf_threshold
            )
            return result

        if conf_threshold < 0.0:
            result.add_error(
                "conf_threshold", "Must be at least 0.0", value=conf_threshold
            )
        elif conf_threshold > 1.0:
            result.add_error(
                "conf_threshold", "Must not exceed 1.0", value=conf_threshold
            )

        return result

    @staticmethod
    def validate_temperature(temperature: float) -> ValidationResult:
        """Validate temperature parameter."""
        result = ValidationResult()

        if not isinstance(temperature, (int, float)):
            result.add_error("temperature", "Must be a number", value=temperature)
            return result

        if temperature < 0.0:
            result.add_error("temperature", "Must be at least 0.0", value=temperature)
        elif temperature > 2.0:
            result.add_error("temperature", "Must not exceed 2.0", value=temperature)

        return result

    @staticmethod
    def validate_retrieval_mode(retrieval_mode: str) -> ValidationResult:
        """Validate retrieval mode parameter."""
        result = ValidationResult()
        valid_modes = ["disabled", "qdrant", "elasticsearch", "hybrid"]

        if not isinstance(retrieval_mode, str):
            result.add_error(
                "retrieval_mode", "Must be a string", value=retrieval_mode
            )
            return result

        if retrieval_mode not in valid_modes:
            result.add_error(
                "retrieval_mode",
                f"Must be one of: {', '.join(valid_modes)}",
                value=retrieval_mode,
            )

        return result


def validate_ask_request(
    question: str,
    max_rounds: Optional[int] = None,
    conf_threshold: Optional[float] = None,
    retrieval_mode: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a complete ask request.

    Args:
        question: The user's question
        max_rounds: Optional max rounds override
        conf_threshold: Optional confidence threshold override
        retrieval_mode: Optional retrieval mode override

    Returns:
        ValidationResult with all validation errors
    """
    combined_result = ValidationResult()

    # Validate question
    question_validator = QuestionValidator()
    question_result = question_validator.validate(question)
    combined_result.errors.extend(question_result.errors)

    # Validate optional parameters
    if max_rounds is not None:
        rounds_result = ConfigValidator.validate_max_rounds(max_rounds)
        combined_result.errors.extend(rounds_result.errors)

    if conf_threshold is not None:
        threshold_result = ConfigValidator.validate_conf_threshold(conf_threshold)
        combined_result.errors.extend(threshold_result.errors)

    if retrieval_mode is not None:
        mode_result = ConfigValidator.validate_retrieval_mode(retrieval_mode)
        combined_result.errors.extend(mode_result.errors)

    return combined_result

"""
Configuration validation for startup checks.

This module validates all environment variables and configuration settings
to catch errors early before the application starts serving requests.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class ValidationIssue:
    """A configuration validation issue."""

    level: str  # "error", "warning", "info"
    category: str
    message: str
    variable: Optional[str] = None
    suggestion: Optional[str] = None


class ConfigValidator:
    """Validator for application configuration."""

    def __init__(self) -> None:
        self.issues: List[ValidationIssue] = []

    def add_error(
        self,
        category: str,
        message: str,
        variable: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add an error issue."""
        self.issues.append(
            ValidationIssue(
                level="error",
                category=category,
                message=message,
                variable=variable,
                suggestion=suggestion,
            )
        )

    def add_warning(
        self,
        category: str,
        message: str,
        variable: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a warning issue."""
        self.issues.append(
            ValidationIssue(
                level="warning",
                category=category,
                message=message,
                variable=variable,
                suggestion=suggestion,
            )
        )

    def add_info(
        self,
        category: str,
        message: str,
        variable: Optional[str] = None,
    ) -> None:
        """Add an info issue."""
        self.issues.append(
            ValidationIssue(
                level="info",
                category=category,
                message=message,
                variable=variable,
            )
        )

    def validate_url(
        self, var_name: str, required: bool = True, schemes: Optional[List[str]] = None
    ) -> Optional[str]:
        """Validate a URL environment variable."""
        value = os.getenv(var_name)

        if not value:
            if required:
                self.add_error(
                    "url",
                    f"{var_name} is required but not set",
                    variable=var_name,
                    suggestion=f"Set {var_name} to a valid URL",
                )
            return None

        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                self.add_error(
                    "url",
                    f"{var_name} is not a valid URL",
                    variable=var_name,
                    suggestion=f"URL must include scheme and host (e.g., http://localhost:8000)",
                )
                return None

            if schemes and parsed.scheme not in schemes:
                self.add_error(
                    "url",
                    f"{var_name} has invalid scheme '{parsed.scheme}'",
                    variable=var_name,
                    suggestion=f"Use one of: {', '.join(schemes)}",
                )
                return None

        except Exception as e:
            self.add_error(
                "url",
                f"{var_name} failed to parse: {e}",
                variable=var_name,
            )
            return None

        return value

    def validate_enum(
        self,
        var_name: str,
        valid_values: List[str],
        default: Optional[str] = None,
        required: bool = False,
    ) -> str:
        """Validate an enum environment variable."""
        value = os.getenv(var_name, default)

        if not value:
            if required:
                self.add_error(
                    "enum",
                    f"{var_name} is required but not set",
                    variable=var_name,
                    suggestion=f"Set {var_name} to one of: {', '.join(valid_values)}",
                )
            return default or valid_values[0]

        if value not in valid_values:
            self.add_error(
                "enum",
                f"{var_name} has invalid value '{value}'",
                variable=var_name,
                suggestion=f"Use one of: {', '.join(valid_values)}",
            )
            return default or valid_values[0]

        return value

    def validate_int(
        self,
        var_name: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        required: bool = False,
    ) -> Optional[int]:
        """Validate an integer environment variable."""
        value_str = os.getenv(var_name)

        if not value_str:
            if required:
                self.add_error(
                    "int",
                    f"{var_name} is required but not set",
                    variable=var_name,
                )
            return default

        try:
            value = int(value_str)
        except ValueError:
            self.add_error(
                "int",
                f"{var_name} is not a valid integer: '{value_str}'",
                variable=var_name,
                suggestion=f"Set {var_name} to an integer value",
            )
            return default

        if min_value is not None and value < min_value:
            self.add_error(
                "int",
                f"{var_name} is below minimum value {min_value}",
                variable=var_name,
                suggestion=f"Set {var_name} to at least {min_value}",
            )

        if max_value is not None and value > max_value:
            self.add_warning(
                "int",
                f"{var_name} exceeds recommended maximum {max_value}",
                variable=var_name,
                suggestion=f"Consider setting {var_name} to at most {max_value}",
            )

        return value

    def validate_float(
        self,
        var_name: str,
        default: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        required: bool = False,
    ) -> Optional[float]:
        """Validate a float environment variable."""
        value_str = os.getenv(var_name)

        if not value_str:
            if required:
                self.add_error(
                    "float",
                    f"{var_name} is required but not set",
                    variable=var_name,
                )
            return default

        try:
            value = float(value_str)
        except ValueError:
            self.add_error(
                "float",
                f"{var_name} is not a valid float: '{value_str}'",
                variable=var_name,
                suggestion=f"Set {var_name} to a numeric value",
            )
            return default

        if min_value is not None and value < min_value:
            self.add_error(
                "float",
                f"{var_name} is below minimum value {min_value}",
                variable=var_name,
                suggestion=f"Set {var_name} to at least {min_value}",
            )

        if max_value is not None and value > max_value:
            self.add_warning(
                "float",
                f"{var_name} exceeds recommended maximum {max_value}",
                variable=var_name,
                suggestion=f"Consider setting {var_name} to at most {max_value}",
            )

        return value

    def validate_bool(
        self, var_name: str, default: bool = False
    ) -> bool:
        """Validate a boolean environment variable."""
        value_str = os.getenv(var_name, "").lower()

        if not value_str:
            return default

        if value_str in ("true", "yes", "1", "on"):
            return True
        elif value_str in ("false", "no", "0", "off"):
            return False
        else:
            self.add_warning(
                "bool",
                f"{var_name} has ambiguous value '{value_str}', using default {default}",
                variable=var_name,
                suggestion="Use 'true'/'false', 'yes'/'no', '1'/'0', or 'on'/'off'",
            )
            return default

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.level == "error" for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(issue.level == "warning" for issue in self.issues)

    def get_report(self) -> str:
        """Get a formatted report of all issues."""
        if not self.issues:
            return "✅ Configuration validation passed with no issues"

        lines = ["Configuration Validation Report", "=" * 50, ""]

        # Group by level
        errors = [i for i in self.issues if i.level == "error"]
        warnings = [i for i in self.issues if i.level == "warning"]
        infos = [i for i in self.issues if i.level == "info"]

        if errors:
            lines.append(f"❌ ERRORS ({len(errors)}):")
            for issue in errors:
                lines.append(f"  [{issue.category}] {issue.message}")
                if issue.variable:
                    lines.append(f"    Variable: {issue.variable}")
                if issue.suggestion:
                    lines.append(f"    Suggestion: {issue.suggestion}")
                lines.append("")

        if warnings:
            lines.append(f"⚠️  WARNINGS ({len(warnings)}):")
            for issue in warnings:
                lines.append(f"  [{issue.category}] {issue.message}")
                if issue.variable:
                    lines.append(f"    Variable: {issue.variable}")
                if issue.suggestion:
                    lines.append(f"    Suggestion: {issue.suggestion}")
                lines.append("")

        if infos:
            lines.append(f"ℹ️  INFO ({len(infos)}):")
            for issue in infos:
                lines.append(f"  [{issue.category}] {issue.message}")
                lines.append("")

        return "\n".join(lines)


def validate_configuration() -> ConfigValidator:
    """
    Validate all application configuration.

    Returns:
        ConfigValidator with validation results
    """
    validator = ConfigValidator()

    # Validate model URLs (optional, depends on deployment)
    validator.validate_url("SMALL_MODEL_URL", required=False, schemes=["http", "https"])
    validator.validate_url("MEDIUM_MODEL_URL", required=False, schemes=["http", "https"])
    validator.validate_url("LARGE_MODEL_URL", required=False, schemes=["http", "https"])

    # Validate retrieval service URLs
    retrieval_mode = validator.validate_enum(
        "RETRIEVAL_MODE",
        ["disabled", "qdrant", "elasticsearch", "hybrid"],
        default="disabled",
    )

    if retrieval_mode in ["qdrant", "hybrid"]:
        validator.validate_url("QDRANT_URL", required=True, schemes=["http", "https"])

    if retrieval_mode in ["elasticsearch", "hybrid"]:
        validator.validate_url("ES_URL", required=True, schemes=["http", "https"])

    # Validate rate limiting
    validator.validate_int("RATE_LIMIT_QPS", default=5, min_value=1, max_value=1000)
    validator.validate_int("RATE_LIMIT_WINDOW", default=60, min_value=1, max_value=3600)

    # Validate self-loop parameters
    validator.validate_int("MAX_ROUNDS", default=3, min_value=1, max_value=10)
    validator.validate_float("CONF_THRESHOLD", default=0.65, min_value=0.0, max_value=1.0)

    # Validate timeouts
    validator.validate_float("TIMEOUT_MODEL", default=30.0, min_value=1.0, max_value=300.0)
    validator.validate_float("TIMEOUT_RETRIEVAL", default=10.0, min_value=1.0, max_value=60.0)
    validator.validate_float("TIMEOUT_SELFLOOP", default=180.0, min_value=10.0, max_value=600.0)
    validator.validate_float("TIMEOUT_REQUEST", default=300.0, min_value=30.0, max_value=1800.0)

    # Validate cache settings
    validator.validate_int("CACHE_MAX_SIZE", default=100, min_value=10, max_value=10000)
    validator.validate_float("CACHE_TTL_SECONDS", default=3600.0, min_value=60.0, max_value=86400.0)

    # Validate logging
    validator.validate_enum(
        "LOG_LEVEL",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    validator.validate_bool("LOG_STRUCTURED", default=True)

    # Validate CORS
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins == "*":
        validator.add_warning(
            "security",
            "CORS_ORIGINS is set to '*' which allows all origins",
            variable="CORS_ORIGINS",
            suggestion="Set specific allowed origins for production",
        )

    # Check for auth token in production
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        validator.add_warning(
            "security",
            "AUTH_TOKEN is not set - API will allow unauthenticated access",
            variable="AUTH_TOKEN",
            suggestion="Set AUTH_TOKEN for production deployments",
        )

    return validator

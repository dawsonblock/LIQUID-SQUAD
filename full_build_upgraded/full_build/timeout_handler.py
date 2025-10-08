"""
Request timeout and cancellation handling.

This module provides utilities for managing timeouts and graceful cancellation
of long-running operations.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout."""

    def __init__(self, timeout: float, operation: str = "operation") -> None:
        self.timeout = timeout
        self.operation = operation
        super().__init__(f"{operation} timed out after {timeout} seconds")


class CancellationError(Exception):
    """Raised when an operation is cancelled."""

    def __init__(self, message: str = "Operation cancelled") -> None:
        super().__init__(message)


async def with_timeout(
    coro: Awaitable[T],
    timeout: float,
    operation_name: str = "operation",
) -> T:
    """
    Execute a coroutine with a timeout.

    Args:
        coro: The coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name of the operation for error messages

    Returns:
        The result of the coroutine

    Raises:
        TimeoutError: If the operation exceeds the timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError as e:
        raise TimeoutError(timeout, operation_name) from e


def timeout(seconds: float, operation_name: Optional[str] = None):
    """
    Decorator to add timeout to async functions.

    Args:
        seconds: Timeout in seconds
        operation_name: Optional name for the operation

    Example:
        @timeout(30.0, "model_inference")
        async def call_model():
            ...
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            op_name = operation_name or func.__name__
            return await with_timeout(func(*args, **kwargs), seconds, op_name)

        return wrapper

    return decorator


class CancellationToken:
    """Token that can be used to check if an operation should be cancelled."""

    def __init__(self) -> None:
        self._cancelled = False
        self._reason: Optional[str] = None

    def cancel(self, reason: str = "User requested cancellation") -> None:
        """Cancel the operation."""
        self._cancelled = True
        self._reason = reason

    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self._cancelled

    def check_cancelled(self) -> None:
        """Raise CancellationError if the operation has been cancelled."""
        if self._cancelled:
            raise CancellationError(self._reason or "Operation cancelled")

    @property
    def reason(self) -> Optional[str]:
        """Get the cancellation reason."""
        return self._reason


class TimeoutConfig:
    """Configuration for various timeout settings."""

    def __init__(
        self,
        model_inference: float = 30.0,
        retrieval: float = 10.0,
        verifier: float = 15.0,
        self_loop: float = 180.0,
        total_request: float = 300.0,
    ) -> None:
        """
        Initialize timeout configuration.

        Args:
            model_inference: Timeout for a single model inference call
            retrieval: Timeout for retrieval operations
            verifier: Timeout for verifier operations
            self_loop: Timeout for the entire self-loop
            total_request: Maximum total request timeout
        """
        self.model_inference = model_inference
        self.retrieval = retrieval
        self.verifier = verifier
        self.self_loop = self_loop
        self.total_request = total_request

    @classmethod
    def from_env(cls) -> TimeoutConfig:
        """Create configuration from environment variables."""
        import os

        return cls(
            model_inference=float(os.getenv("TIMEOUT_MODEL", "30.0")),
            retrieval=float(os.getenv("TIMEOUT_RETRIEVAL", "10.0")),
            verifier=float(os.getenv("TIMEOUT_VERIFIER", "15.0")),
            self_loop=float(os.getenv("TIMEOUT_SELFLOOP", "180.0")),
            total_request=float(os.getenv("TIMEOUT_REQUEST", "300.0")),
        )


# Global timeout configuration
_global_timeout_config: Optional[TimeoutConfig] = None


def get_timeout_config() -> TimeoutConfig:
    """Get the global timeout configuration."""
    global _global_timeout_config
    if _global_timeout_config is None:
        _global_timeout_config = TimeoutConfig.from_env()
    return _global_timeout_config


def configure_timeouts(config: TimeoutConfig) -> None:
    """Configure global timeouts."""
    global _global_timeout_config
    _global_timeout_config = config


async def with_cancellation(
    coro: Awaitable[T],
    token: CancellationToken,
    check_interval: float = 0.5,
) -> T:
    """
    Execute a coroutine with cancellation support.

    Args:
        coro: The coroutine to execute
        token: Cancellation token to check
        check_interval: How often to check for cancellation (seconds)

    Returns:
        The result of the coroutine

    Raises:
        CancellationError: If the operation is cancelled
    """
    task = asyncio.create_task(coro)

    async def check_cancellation():
        while not task.done():
            token.check_cancelled()
            await asyncio.sleep(check_interval)

    checker = asyncio.create_task(check_cancellation())

    try:
        result = await task
        checker.cancel()
        try:
            await checker
        except asyncio.CancelledError:
            pass
        return result
    except CancellationError:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        raise


async def race(
    *awaitables: Awaitable[T],
    return_first: bool = True,
) -> tuple[T, int]:
    """
    Race multiple awaitables and return the first to complete.

    Args:
        *awaitables: The awaitables to race
        return_first: If True, cancel other tasks when first completes

    Returns:
        Tuple of (result, index of winning awaitable)
    """
    tasks = [asyncio.create_task(awaitable) for awaitable in awaitables]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    winner = list(done)[0]
    winner_index = tasks.index(winner)
    result = winner.result()

    if return_first:
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    return result, winner_index

"""Shared Result object for use case boundaries."""

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Result:
    ok: bool
    value: Any = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @staticmethod
    def success(value: Any = None) -> "Result":
        return Result(ok=True, value=value)

    @staticmethod
    def failure(code: str, message: str) -> "Result":
        return Result(ok=False, error_code=code, error_message=message)

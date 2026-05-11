from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from backend import config as _config  # noqa: F401  Loads local .env before checking Langfuse keys.


F = TypeVar("F", bound=Callable[..., Any])


try:
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        raise ImportError
    from langfuse import observe as observe
except ImportError:

    def observe(*args: Any, **kwargs: Any) -> Callable[[F], F] | F:
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]

        def decorator(func: F) -> F:
            return func

        return decorator

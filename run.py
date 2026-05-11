from __future__ import annotations

from backend.run import _main

import asyncio
import sys


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is required. Create a 3.11+ environment, then rerun `python run.py`.")
    asyncio.run(_main())

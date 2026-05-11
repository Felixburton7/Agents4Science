from __future__ import annotations

import argparse
import asyncio
import sys
import warnings


warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change.*",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the hypothesis steering pipeline.")
    parser.add_argument("hypothesis", help="Raw hypothesis text to evaluate.")
    return parser.parse_args()


async def _main() -> None:
    try:
        from backend.pipeline import run_pipeline
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required package"
        raise SystemExit(
            f"Missing dependency: {missing}. Install with `python -m pip install -r requirements.txt` "
            "inside a Python 3.11+ environment."
        ) from exc

    args = _parse_args()
    final_state = await run_pipeline(args.hypothesis)
    memo = final_state["final_memo"]
    print(memo.to_markdown())


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is required. Create a 3.11+ environment, then rerun `python run.py`.")
    asyncio.run(_main())

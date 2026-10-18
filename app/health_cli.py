"""Print the full health report from inside the stack.

Usage:  docker compose exec api python -m app.health_cli
Exit code 0 when every dependency is healthy, 1 otherwise. Used instead of exposing the
detailed /health endpoint to browsers.
"""

from __future__ import annotations

import asyncio
import json
import sys

from .config import ConfigError, load_settings
from .health import DEFAULT_CHECKS, run_checks


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as e:
        print(str(e), file=sys.stderr)
        return 2
    ok, body = asyncio.run(run_checks(settings, DEFAULT_CHECKS))
    print(json.dumps(body, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

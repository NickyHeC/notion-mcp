# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Server entrypoint (Dedalus platform expects main.py at repo root)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv


load_dotenv()

from server import main  # noqa: E402


if __name__ == "__main__":
    asyncio.run(main())

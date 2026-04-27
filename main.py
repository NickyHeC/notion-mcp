# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Server entrypoint."""

import sys
import traceback

try:
    from dotenv import load_dotenv

    load_dotenv()

    from server import create_server  # noqa: E402
    from tools import notion_tools  # noqa: E402

    server = create_server()
    server.collect(*notion_tools)
except Exception:
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    import asyncio

    asyncio.run(server.serve(host="0.0.0.0"))

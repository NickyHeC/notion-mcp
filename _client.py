# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Test client for the Notion MCP server.

Two modes:

1. Test connection only (no server needed):
       uv run src/_client.py --test-connection

   Uses ConnectionTester to verify your Connection config and credentials
   work against the Notion API.

2. Test tools (server must be running):
       uv run src/main.py            # in one terminal
       uv run src/_client.py         # in another
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()


async def test_connection() -> None:
    """Verify the DAuth connection config and credentials without a running server."""
    from dedalus_mcp.testing import ConnectionTester, TestRequest

    from notion.config import notion

    tester = ConnectionTester.from_env(notion)

    response = await tester.request(
        TestRequest(path="/users/me", headers={"Notion-Version": "2026-03-11"}),
    )

    if response.success:
        print(f"OK {response.status} — Connection works!")
        print(f"Response: {response.body}")
    else:
        print(f"FAIL {response.status}")
        print(f"Response: {response.body}")


async def test_tools() -> None:
    """Connect to the running server and call tools."""
    from dedalus_mcp.client import MCPClient

    client = await MCPClient.connect("http://127.0.0.1:8080/mcp")

    tools = await client.list_tools()
    print("Available tools:", [t.name for t in tools.tools])

    result = await client.call_tool("notion_search", {"query": "", "page_size": 3})
    print("notion_search result:", result.content[0].text)

    result = await client.call_tool("notion_list_users", {})
    print("notion_list_users result:", result.content[0].text)

    await client.close()


if __name__ == "__main__":
    if "--test-connection" in sys.argv:
        asyncio.run(test_connection())
    else:
        asyncio.run(test_tools())

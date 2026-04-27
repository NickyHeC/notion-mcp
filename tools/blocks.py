# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Block (page content) tools.

Tools:
  notion_get_page_content    -- get child blocks of a page or block
  notion_append_page_content -- append blocks to a page or block
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import (
    _bool,
    _extract_block_text,
    _str,
    api_request,
)
from notion.types import BlockInfo, JSONObject, NotionResult


# --- Helpers ---


def _parse_block(raw: JSONObject) -> BlockInfo:
    """Parse a raw Notion block object into a BlockInfo.

    Args:
        raw: Untyped block object from a Notion API response.

    Returns:
        Parsed BlockInfo with extracted text.

    """
    result = BlockInfo(
        id=_str(raw.get("id")),
        type=_str(raw.get("type")),
        text=_extract_block_text(raw),
        has_children=_bool(raw.get("has_children")),
    )
    return result


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_get_page_content(
    block_id: str,
    page_size: int = 100,
    start_cursor: str | None = None,
) -> list[BlockInfo] | str:
    """Get the child blocks (content) of a page or block.

    Returns top-level blocks only. Blocks with nested content
    have ``has_children=True``; call again with their ``id`` to
    retrieve children.

    Args:
        block_id: UUID of the page or parent block.
        page_size: Number of blocks per page (max 100).
        start_cursor: Cursor for pagination. Optional.

    Returns:
        List of BlockInfo objects, or an error string on failure.

    """
    query_params: dict[str, Any] = {"page_size": page_size}
    if start_cursor:
        query_params["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.GET,
        f"/blocks/{block_id}/children",
        query_params=query_params,
    )
    if not response.success:
        return response.error or "Failed to fetch page content"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    result = [_parse_block(b) for b in results if isinstance(b, dict)]
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_append_page_content(
    block_id: str,
    children: list[JSONObject],
    after: str | None = None,
) -> str:
    """Append blocks to a page or existing block.

    Adds new content blocks as children of the specified page or block.
    Use Notion block objects in the ``children`` array.

    Common block format example::

        {"type": "paragraph", "paragraph": {
            "rich_text": [{"text": {"content": "Hello world"}}]
        }}

    Args:
        block_id: UUID of the page or parent block.
        children: List of Notion block objects to append.
        after: Block ID to insert after. Appends at end if omitted.

    Returns:
        Success message or error string.

    """
    body: dict[str, Any] = {"children": children}
    if after:
        body["after"] = after

    response: NotionResult = await api_request(
        HttpMethod.PATCH,
        f"/blocks/{block_id}/children",
        body=body,
    )
    if not response.success:
        return response.error or "Failed to append content"
    data = response.data
    if isinstance(data, dict):
        results = data.get("results", [])
        count = len(results) if isinstance(results, list) else 0
        return f"Successfully appended {count} block(s)"
    return "Content appended"


block_tools = [
    notion_get_page_content,
    notion_append_page_content,
]

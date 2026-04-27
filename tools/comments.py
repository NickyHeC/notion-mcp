# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Comment tools.

Tools:
  notion_get_comments -- list comments on a page or block
  notion_add_comment  -- add a comment to a page or discussion
"""

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import (
    _extract_plain_text,
    _opt_str,
    _str,
    api_request,
)
from notion.types import CommentInfo, JSONObject, NotionResult


# --- Helpers ---


def _parse_comment(raw: JSONObject) -> CommentInfo:
    """Parse a raw Notion comment object into a CommentInfo.

    Args:
        raw: Untyped comment object from a Notion API response.

    Returns:
        Parsed CommentInfo.

    """
    rich_text = raw.get("rich_text", [])
    body = _extract_plain_text(rich_text)

    author = None
    created_by = raw.get("created_by")
    if isinstance(created_by, dict):
        author = _opt_str(created_by.get("name") or created_by.get("id"))

    result = CommentInfo(
        id=_str(raw.get("id")),
        body=body,
        author=author,
        created_time=_opt_str(raw.get("created_time")),
    )
    return result


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_get_comments(
    block_id: str,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> list[CommentInfo] | str:
    """List comments on a page or block.

    Args:
        block_id: UUID of the page or block to list comments for.
        start_cursor: Cursor for pagination. Optional.
        page_size: Number of comments per page (max 100).

    Returns:
        List of CommentInfo objects, or an error string on failure.

    """
    query_params: dict[str, Any] = {
        "block_id": block_id,
        "page_size": page_size,
    }
    if start_cursor:
        query_params["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.GET, "/comments", query_params=query_params,
    )
    if not response.success:
        return response.error or "Failed to fetch comments"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    result = [_parse_comment(c) for c in results if isinstance(c, dict)]
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_add_comment(
    body: str,
    page_id: str | None = None,
    discussion_id: str | None = None,
) -> CommentInfo | str:
    """Add a comment to a page or an existing discussion thread.

    Provide either ``page_id`` to start a new top-level comment
    on a page, or ``discussion_id`` to reply to an existing
    comment thread.

    Args:
        body: Comment text content.
        page_id: UUID of the page for a new top-level comment. Optional.
        discussion_id: UUID of the discussion thread to reply to. Optional.

    Returns:
        Created CommentInfo, or an error string on failure.

    """
    if not page_id and not discussion_id:
        return "Either page_id or discussion_id is required"

    request_body: dict[str, Any] = {
        "rich_text": [{"text": {"content": body}}],
    }
    if page_id:
        request_body["parent"] = {"page_id": page_id}
    if discussion_id:
        request_body["discussion_id"] = discussion_id

    response: NotionResult = await api_request(
        HttpMethod.POST, "/comments", body=request_body,
    )
    if not response.success:
        return response.error or "Failed to add comment"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_comment(data)
    return result


comment_tools = [
    notion_get_comments,
    notion_add_comment,
]

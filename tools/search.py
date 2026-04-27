# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Search tools.

Tools:
  notion_search -- search across pages and databases in workspace
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import (
    _bool,
    _extract_parent,
    _extract_plain_text,
    _extract_title,
    _opt_str,
    _simplify_properties,
    _str,
    api_request,
)
from notion.types import JSONObject, NotionResult, PageInfo


# --- Helpers ---


def _parse_search_result(raw: JSONObject) -> PageInfo:
    """Parse a search result into a PageInfo.

    Args:
        raw: Untyped page or database object from search results.

    Returns:
        Parsed PageInfo.

    """
    obj_type = raw.get("object")
    properties = raw.get("properties", {})

    if obj_type == "database":
        title = _extract_plain_text(raw.get("title", []))
        simplified_props = None
    elif isinstance(properties, dict):
        title = _extract_title(properties)
        simplified_props = _simplify_properties(properties)
    else:
        title = ""
        simplified_props = None

    parent = raw.get("parent", {})
    parent_type, parent_id = _extract_parent(parent)

    result = PageInfo(
        id=_str(raw.get("id")),
        title=title,
        url=_opt_str(raw.get("url")),
        parent_type=parent_type,
        parent_id=parent_id,
        created_time=_opt_str(raw.get("created_time")),
        last_edited_time=_opt_str(raw.get("last_edited_time")),
        archived=_bool(raw.get("archived")),
        properties=simplified_props,
    )
    return result


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_search(
    query: str = "",
    filter_type: str | None = None,
    sort_direction: str = "descending",
    sort_timestamp: str = "last_edited_time",
    start_cursor: str | None = None,
    page_size: int = 20,
) -> list[PageInfo] | str:
    """Search across all pages and databases in the workspace.

    Returns pages and databases matching the query string. Results
    are sorted by relevance and recency by default.

    Args:
        query: Search query string. Empty string returns recent items.
        filter_type: Filter to ``page`` or ``database`` results only. Optional.
        sort_direction: Sort order — ``ascending`` or ``descending``.
        sort_timestamp: Sort field — ``last_edited_time``.
        start_cursor: Cursor for pagination (from a previous response).
        page_size: Number of results per page (max 100).

    Returns:
        List of PageInfo objects, or an error string on failure.

    """
    body: dict[str, Any] = {"page_size": page_size}
    if query:
        body["query"] = query
    if filter_type in ("page", "database"):
        body["filter"] = {"value": filter_type, "property": "object"}
    if sort_direction in ("ascending", "descending"):
        body["sort"] = {
            "direction": sort_direction,
            "timestamp": sort_timestamp,
        }
    if start_cursor:
        body["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.POST, "/search", body=body,
    )
    if not response.success:
        return response.error or "Search failed"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    result = [
        _parse_search_result(r)
        for r in results
        if isinstance(r, dict)
    ]
    return result


search_tools = [
    notion_search,
]

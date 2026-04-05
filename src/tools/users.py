# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""User tools.

Tools:
  notion_list_users -- list all users in workspace
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import _opt_str, _str, api_request
from notion.types import JSONObject, NotionResult, UserInfo


# --- Helpers ---


def _parse_user(raw: JSONObject) -> UserInfo:
    """Parse a raw Notion user object into a UserInfo.

    Args:
        raw: Untyped user object from a Notion API response.

    Returns:
        Parsed UserInfo.

    """
    person = raw.get("person")
    email = None
    if isinstance(person, dict):
        email = _opt_str(person.get("email"))

    result = UserInfo(
        id=_str(raw.get("id")),
        name=_str(raw.get("name")),
        type=_str(raw.get("type"), "person"),
        email=email,
        avatar_url=_opt_str(raw.get("avatar_url")),
    )
    return result


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_list_users(
    start_cursor: str | None = None,
    page_size: int = 100,
) -> list[UserInfo] | str:
    """List all users in the workspace.

    Returns both person and bot users visible to the integration.

    Args:
        start_cursor: Cursor for pagination. Optional.
        page_size: Number of users per page (max 100).

    Returns:
        List of UserInfo objects, or an error string on failure.

    """
    query_params: dict[str, Any] = {"page_size": page_size}
    if start_cursor:
        query_params["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.GET, "/users", query_params=query_params,
    )
    if not response.success:
        return response.error or "Failed to list users"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    result = [_parse_user(u) for u in results if isinstance(u, dict)]
    return result


user_tools = [
    notion_list_users,
]

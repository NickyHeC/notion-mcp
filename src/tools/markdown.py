# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Markdown tools.

Tools:
  notion_get_page_markdown    -- retrieve page content as markdown
  notion_update_page_markdown -- update page content using markdown

Uses Notion's Enhanced Markdown format (API version 2026-03-11+).
See https://developers.notion.com/guides/data-apis/enhanced-markdown
"""

from __future__ import annotations

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import api_request
from notion.types import NotionResult


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_get_page_markdown(page_id: str) -> str:
    """Retrieve page content as enhanced markdown.

    Returns the full page content rendered as markdown, making it
    easy to read and process page content without parsing block
    objects.

    Args:
        page_id: UUID of the page.

    Returns:
        Markdown string of the page content, or error string.

    """
    response: NotionResult = await api_request(
        HttpMethod.GET, f"/pages/{page_id}/markdown",
    )
    if not response.success:
        return response.error or "Failed to fetch page markdown"
    data = response.data
    if isinstance(data, dict):
        markdown = data.get("markdown")
        if markdown is not None:
            return str(markdown)
        return str(data)
    if isinstance(data, str):
        return data
    return "Unexpected response format"


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_update_page_markdown(
    page_id: str,
    markdown: str,
) -> str:
    """Update page content using enhanced markdown.

    Replaces the page's block content with content parsed from
    the provided markdown string. Supports standard markdown
    syntax including headings, lists, code blocks, and more.

    Args:
        page_id: UUID of the page to update.
        markdown: Markdown content to set as the page body.

    Returns:
        Success message or error string.

    """
    response: NotionResult = await api_request(
        HttpMethod.PATCH,
        f"/pages/{page_id}/markdown",
        body={"markdown": markdown},
    )
    if not response.success:
        return response.error or "Failed to update page markdown"
    return "Page markdown updated successfully"


markdown_tools = [
    notion_get_page_markdown,
    notion_update_page_markdown,
]

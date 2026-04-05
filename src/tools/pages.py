# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Page tools.

Tools:
  notion_get_page    -- retrieve a page by ID
  notion_create_page -- create a new page
  notion_update_page -- update page properties
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import (
    _bool,
    _extract_parent,
    _extract_title,
    _opt_str,
    _simplify_properties,
    _str,
    api_request,
)
from notion.types import JSONObject, NotionResult, PageInfo


# --- Helpers ---


def _parse_page(raw: JSONObject) -> PageInfo:
    """Parse a raw Notion page object into a PageInfo.

    Args:
        raw: Untyped page object from a Notion API response.

    Returns:
        Parsed PageInfo with simplified properties.

    """
    properties = raw.get("properties", {})
    title = ""
    simplified_props = None

    if isinstance(properties, dict):
        title = _extract_title(properties)
        simplified_props = _simplify_properties(properties)

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
async def notion_get_page(page_id: str) -> PageInfo | str:
    """Retrieve a Notion page by ID.

    Returns page metadata and simplified properties. Use
    ``notion_get_page_content`` to fetch the actual block content.

    Args:
        page_id: UUID of the page (with or without dashes).

    Returns:
        PageInfo with properties, or an error string on failure.

    """
    response: NotionResult = await api_request(
        HttpMethod.GET, f"/pages/{page_id}",
    )
    if not response.success:
        return response.error or "Failed to fetch page"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_page(data)
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_create_page(
    parent_id: str,
    title: str,
    parent_type: str = "page_id",
    title_property_name: str = "title",
    properties: JSONObject | None = None,
    children: list[JSONObject] | None = None,
) -> PageInfo | str:
    """Create a new page in a workspace, under a page, or in a database.

    For standalone pages (child of another page), use ``parent_type="page_id"``
    and ``title_property_name="title"``.

    For database entries, use ``parent_type="database_id"`` and set
    ``title_property_name`` to the database's title column name
    (commonly ``"Name"``).

    Args:
        parent_id: UUID of the parent page or database.
        title: Page title text.
        parent_type: ``page_id`` or ``database_id``.
        title_property_name: Name of the title property in the schema.
            Use ``title`` for standalone pages or the database column
            name (e.g. ``Name``) for database entries.
        properties: Additional properties in raw Notion API format. Optional.
        children: Block content as Notion block objects. Optional.

    Returns:
        Created PageInfo, or an error string on failure.

    """
    title_value: dict[str, Any] = {
        "title": [{"text": {"content": title}}],
    }
    props: dict[str, Any] = {title_property_name: title_value}
    if properties:
        props.update(properties)

    body: dict[str, Any] = {
        "parent": {parent_type: parent_id},
        "properties": props,
    }
    if children:
        body["children"] = children

    response: NotionResult = await api_request(
        HttpMethod.POST, "/pages", body=body,
    )
    if not response.success:
        return response.error or "Failed to create page"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_page(data)
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_update_page(
    page_id: str,
    properties: JSONObject | None = None,
    archived: bool | None = None,
    icon: JSONObject | None = None,
    cover: JSONObject | None = None,
) -> PageInfo | str:
    """Update page properties, archive status, icon, or cover.

    Only provided fields are modified; omitted fields stay unchanged.
    To update page *content* (blocks), use ``notion_append_page_content``.

    Args:
        page_id: UUID of the page to update.
        properties: Properties to update in raw Notion API format. Optional.
        archived: Set to ``True`` to archive, ``False`` to unarchive. Optional.
        icon: Icon object (emoji or external URL). Optional.
        cover: Cover image object (external URL). Optional.

    Returns:
        Updated PageInfo, or an error string on failure.

    """
    body: dict[str, Any] = {}
    if properties is not None:
        body["properties"] = properties
    if archived is not None:
        body["archived"] = archived
    if icon is not None:
        body["icon"] = icon
    if cover is not None:
        body["cover"] = cover

    if not body:
        return "No fields to update"

    response: NotionResult = await api_request(
        HttpMethod.PATCH, f"/pages/{page_id}", body=body,
    )
    if not response.success:
        return response.error or "Failed to update page"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_page(data)
    return result


page_tools = [
    notion_get_page,
    notion_create_page,
    notion_update_page,
]

# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Database tools.

Tools:
  notion_get_database   -- retrieve database schema
  notion_query_database -- query database with filters and sorting
  notion_create_database -- create a new database
"""

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
from notion.types import (
    DatabaseInfo,
    JSONObject,
    NotionResult,
    PageInfo,
)


# --- Helpers ---


def _parse_database(raw: JSONObject) -> DatabaseInfo:
    """Parse a raw Notion database object into a DatabaseInfo.

    Args:
        raw: Untyped database object from a Notion API response.

    Returns:
        Parsed DatabaseInfo with property schema.

    """
    title = _extract_plain_text(raw.get("title", []))
    description_rich = raw.get("description", [])
    description = (
        _extract_plain_text(description_rich) if description_rich else None
    )

    props_raw = raw.get("properties", {})
    properties = None
    if isinstance(props_raw, dict):
        properties = {
            name: _str(prop.get("type"))
            for name, prop in props_raw.items()
            if isinstance(prop, dict)
        }

    ds_raw = raw.get("data_sources", [])
    data_sources = None
    if isinstance(ds_raw, list) and ds_raw:
        data_sources = [
            {"id": _str(ds.get("id")), "name": _extract_plain_text(ds.get("title", []))}
            for ds in ds_raw
            if isinstance(ds, dict)
        ]

    result = DatabaseInfo(
        id=_str(raw.get("id")),
        title=title,
        description=description,
        url=_opt_str(raw.get("url")),
        properties=properties,
        created_time=_opt_str(raw.get("created_time")),
        last_edited_time=_opt_str(raw.get("last_edited_time")),
        archived=_bool(raw.get("archived")),
        data_sources=data_sources,
    )
    return result


def _parse_database_page(raw: JSONObject) -> PageInfo:
    """Parse a database query result page into a PageInfo.

    Args:
        raw: Untyped page object from a database query response.

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
async def notion_get_database(database_id: str) -> DatabaseInfo | str:
    """Retrieve a database schema and metadata.

    Returns the database title, description, and property schema
    (column names and types).

    Args:
        database_id: UUID of the database.

    Returns:
        DatabaseInfo with schema, or an error string on failure.

    """
    response: NotionResult = await api_request(
        HttpMethod.GET, f"/databases/{database_id}",
    )
    if not response.success:
        return response.error or "Failed to fetch database"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_database(data)
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_query_database(
    database_id: str,
    filter: JSONObject | None = None,
    sorts: list[JSONObject] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> list[PageInfo] | str:
    """Query a database with optional filters and sorting.

    The ``filter`` parameter accepts a Notion filter object.
    See https://developers.notion.com/reference/post-database-query-filter
    for the full schema.

    The ``sorts`` parameter accepts a list of sort objects, e.g.
    ``[{"property": "Name", "direction": "ascending"}]``.

    Args:
        database_id: UUID of the database to query.
        filter: Notion filter object. Passed through as-is. Optional.
        sorts: List of sort criteria. Optional.
        start_cursor: Cursor for pagination. Optional.
        page_size: Number of results per page (max 100).

    Returns:
        List of PageInfo objects (database entries), or error string.

    """
    body: dict[str, Any] = {"page_size": page_size}
    if filter is not None:
        body["filter"] = filter
    if sorts is not None:
        body["sorts"] = sorts
    if start_cursor:
        body["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.POST, f"/databases/{database_id}/query", body=body,
    )
    if not response.success:
        return response.error or "Failed to query database"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    result = [
        _parse_database_page(r)
        for r in results
        if isinstance(r, dict)
    ]
    return result


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_create_database(
    parent_id: str,
    title: str,
    properties: JSONObject,
    description: str | None = None,
    is_inline: bool = False,
) -> DatabaseInfo | str:
    """Create a new database as a child of a page.

    The ``properties`` parameter defines the database schema (columns).
    At minimum, include a title property::

        {"Name": {"title": {}}}

    Other property types: ``rich_text``, ``number``, ``select``,
    ``multi_select``, ``date``, ``checkbox``, ``url``, ``email``,
    ``phone_number``, ``status``, etc.

    Args:
        parent_id: UUID of the parent page.
        title: Database title text.
        properties: Database schema — column definitions in Notion format.
        description: Database description text. Optional.
        is_inline: Create as inline database within the page. Default false.

    Returns:
        Created DatabaseInfo, or an error string on failure.

    """
    body: dict[str, Any] = {
        "parent": {"page_id": parent_id},
        "title": [{"text": {"content": title}}],
        "properties": properties,
        "is_inline": is_inline,
    }
    if description:
        body["description"] = [{"text": {"content": description}}]

    response: NotionResult = await api_request(
        HttpMethod.POST, "/databases", body=body,
    )
    if not response.success:
        return response.error or "Failed to create database"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    result = _parse_database(data)
    return result


database_tools = [
    notion_get_database,
    notion_query_database,
    notion_create_database,
]

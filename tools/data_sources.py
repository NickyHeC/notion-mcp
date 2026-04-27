# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Data source tools (API version 2026-03-11+).

Tools:
  notion_list_data_sources  -- list data sources in a database
  notion_get_data_source    -- get a single data source with full schema
  notion_query_data_source  -- query rows from a data source
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
    DataSourceInfo,
    JSONObject,
    NotionResult,
    PageInfo,
)


# --- Helpers ---


def _parse_data_source(raw: JSONObject) -> DataSourceInfo:
    """Parse a raw Notion data source object into a DataSourceInfo.

    Args:
        raw: Untyped data source object from a Notion API response.

    Returns:
        Parsed DataSourceInfo with property schema.

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

    return DataSourceInfo(
        id=_str(raw.get("id")),
        title=title,
        description=description,
        url=_opt_str(raw.get("url")),
        is_inline=_bool(raw.get("is_inline")),
        properties=properties,
        created_time=_opt_str(raw.get("created_time")),
        last_edited_time=_opt_str(raw.get("last_edited_time")),
    )


def _parse_data_source_page(raw: JSONObject) -> PageInfo:
    """Parse a data source query result row into a PageInfo.

    Args:
        raw: Untyped page object from a data source query response.

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

    return PageInfo(
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


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_list_data_sources(
    database_id: str,
) -> list[DataSourceInfo] | str:
    """List all data sources in a database.

    Fetches the database to discover its data sources, then retrieves
    the full schema (properties) for each one.

    Args:
        database_id: UUID of the database.

    Returns:
        List of DataSourceInfo with full property schemas, or error string.

    """
    db_response: NotionResult = await api_request(
        HttpMethod.GET, f"/databases/{database_id}",
    )
    if not db_response.success:
        return db_response.error or "Failed to fetch database"
    db_data = db_response.data
    if not isinstance(db_data, dict):
        return "Unexpected response"

    ds_list = db_data.get("data_sources", [])
    if not isinstance(ds_list, list):
        return "No data sources found"

    results: list[DataSourceInfo] = []
    for ds in ds_list:
        if not isinstance(ds, dict):
            continue
        ds_id = ds.get("id")
        if not ds_id:
            continue
        ds_response: NotionResult = await api_request(
            HttpMethod.GET, f"/data_sources/{ds_id}",
        )
        if not ds_response.success:
            continue
        ds_data = ds_response.data
        if isinstance(ds_data, dict):
            results.append(_parse_data_source(ds_data))

    return results


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_get_data_source(
    data_source_id: str,
) -> DataSourceInfo | str:
    """Retrieve a single data source with its full property schema.

    Args:
        data_source_id: UUID of the data source.

    Returns:
        DataSourceInfo with properties, or an error string on failure.

    """
    response: NotionResult = await api_request(
        HttpMethod.GET, f"/data_sources/{data_source_id}",
    )
    if not response.success:
        return response.error or "Failed to fetch data source"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_data_source(data)


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def notion_query_data_source(
    data_source_id: str,
    filter: JSONObject | None = None,
    sorts: list[JSONObject] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> list[PageInfo] | str:
    """Query rows from a data source with optional filters and sorting.

    Works like ``notion_query_database`` but targets a specific data
    source within a database.

    The ``filter`` parameter accepts a Notion filter object.
    The ``sorts`` parameter accepts a list of sort objects, e.g.
    ``[{"property": "Name", "direction": "ascending"}]``.

    Args:
        data_source_id: UUID of the data source to query.
        filter: Notion filter object. Passed through as-is. Optional.
        sorts: List of sort criteria. Optional.
        start_cursor: Cursor for pagination. Optional.
        page_size: Number of results per page (max 100).

    Returns:
        List of PageInfo objects (data source rows), or error string.

    """
    body: dict[str, Any] = {"page_size": page_size}
    if filter is not None:
        body["filter"] = filter
    if sorts is not None:
        body["sorts"] = sorts
    if start_cursor:
        body["start_cursor"] = start_cursor

    response: NotionResult = await api_request(
        HttpMethod.POST, f"/data_sources/{data_source_id}/query", body=body,
    )
    if not response.success:
        return response.error or "Failed to query data source"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [
        _parse_data_source_page(r)
        for r in results
        if isinstance(r, dict)
    ]


data_source_tools = [
    notion_list_data_sources,
    notion_get_data_source,
    notion_query_data_source,
]

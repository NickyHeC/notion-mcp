# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Notion REST API request dispatch and response helpers.

Notion uses standard REST endpoints with JSON bodies.
Every request requires a ``Notion-Version`` header.

Functions:
  api_request(method, path, ...)  -- dispatch REST request via Dedalus enclave

Coercion helpers (safe extraction from untyped API dicts):
  _str(val, default)              -- coerce to str
  _opt_str(val)                   -- coerce to str | None
  _bool(val, *, default)          -- coerce to bool

Rich text helpers:
  _extract_plain_text(rich_text)  -- join plain_text from rich text array
  _extract_title(properties)      -- find and extract title from properties
  _extract_parent(parent)         -- parse parent type and ID

Property helpers:
  _simplify_property(prop)        -- convert Notion property to simple value
  _simplify_properties(props)     -- simplify all properties in a dict

Block helpers:
  _extract_block_text(block)      -- extract text content from a block
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from dedalus_mcp import HttpMethod, HttpRequest, get_context

from notion.config import notion
from notion.types import NotionResult


NOTION_VERSION = "2026-03-11"


# --- REST dispatch ---


async def api_request(
    method: HttpMethod,
    path: str,
    body: dict[str, Any] | None = None,
    query_params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> NotionResult:
    """Execute a Notion API request via the Dedalus enclave.

    All Notion API interaction goes through this single function.
    The ``Notion-Version`` header is injected automatically.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE).
        path: API path relative to base_url (e.g. ``/pages/{id}``).
        body: JSON body for POST/PATCH requests. Optional.
        query_params: URL query parameters for GET requests. Optional.
        headers: Extra headers merged with defaults. Optional.

    Returns:
        NotionResult wrapping the response data or error.

    """
    request_headers: dict[str, str] = {"Notion-Version": NOTION_VERSION}
    if headers:
        request_headers.update(headers)

    if query_params:
        filtered = {k: v for k, v in query_params.items() if v is not None}
        if filtered:
            path = f"{path}?{urlencode(filtered)}"

    ctx = get_context()
    req = HttpRequest(method=method, path=path, body=body, headers=request_headers)
    resp = await ctx.dispatch(notion, req)

    if resp.success and resp.response is not None:
        resp_body = resp.response.body
        if isinstance(resp_body, dict):
            if resp_body.get("object") == "error":
                msg = resp_body.get("message", "API error")
                result = NotionResult(success=False, error=str(msg))
                return result
            result = NotionResult(success=True, data=resp_body)
            return result
        result = NotionResult(success=True, data=resp_body)
        return result

    error = resp.error.message if resp.error else "Request failed"
    result = NotionResult(success=False, error=error)
    return result


# --- Coercion helpers (safe extraction from untyped API dicts) ---


def _str(val: Any, default: str = "") -> str:  # noqa: ANN401
    """Safely coerce to string."""
    return str(val) if val is not None else default


def _opt_str(val: Any) -> str | None:  # noqa: ANN401
    """Safely coerce to optional string."""
    return str(val) if val is not None else None


def _bool(val: Any, *, default: bool = False) -> bool:  # noqa: ANN401
    """Safely coerce to bool."""
    return bool(val) if val is not None else default


# --- Rich text helpers ---


def _extract_plain_text(rich_text: Any) -> str:  # noqa: ANN401
    """Join ``plain_text`` values from a Notion rich text array."""
    if not isinstance(rich_text, list):
        return ""
    return "".join(
        item.get("plain_text", "")
        for item in rich_text
        if isinstance(item, dict)
    )


def _extract_title(properties: dict[str, Any]) -> str:
    """Find the title property in a page's properties and extract plain text."""
    for prop in properties.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return _extract_plain_text(prop.get("title", []))
    return ""


def _extract_parent(parent: Any) -> tuple[str, str | None]:  # noqa: ANN401
    """Parse a Notion parent object into (type, id)."""
    if not isinstance(parent, dict):
        return ("unknown", None)
    parent_type = _str(parent.get("type"))
    parent_id = _opt_str(parent.get(parent_type))
    return (parent_type, parent_id)


# --- Property simplification ---


def _simplify_property(prop: dict[str, Any]) -> Any:  # noqa: ANN401
    """Convert a Notion property value object to a simplified Python value."""
    prop_type = prop.get("type", "")

    if prop_type == "title":
        return _extract_plain_text(prop.get("title", []))
    if prop_type == "rich_text":
        return _extract_plain_text(prop.get("rich_text", []))
    if prop_type == "number":
        return prop.get("number")
    if prop_type == "select":
        sel = prop.get("select")
        return sel.get("name") if isinstance(sel, dict) else None
    if prop_type == "multi_select":
        return [
            i.get("name")
            for i in prop.get("multi_select", [])
            if isinstance(i, dict)
        ]
    if prop_type == "date":
        date = prop.get("date")
        if isinstance(date, dict):
            start = date.get("start", "")
            end = date.get("end")
            return f"{start} \u2192 {end}" if end else start
        return None
    if prop_type == "checkbox":
        return prop.get("checkbox")
    if prop_type == "url":
        return prop.get("url")
    if prop_type == "email":
        return prop.get("email")
    if prop_type == "phone_number":
        return prop.get("phone_number")
    if prop_type == "status":
        status = prop.get("status")
        return status.get("name") if isinstance(status, dict) else None
    if prop_type == "people":
        return [
            p.get("name", p.get("id", ""))
            for p in prop.get("people", [])
            if isinstance(p, dict)
        ]
    if prop_type == "formula":
        formula = prop.get("formula", {})
        return formula.get(formula.get("type", "")) if isinstance(formula, dict) else None
    if prop_type in ("created_time", "last_edited_time"):
        return prop.get(prop_type)
    if prop_type in ("created_by", "last_edited_by"):
        user = prop.get(prop_type)
        return user.get("name", user.get("id", "")) if isinstance(user, dict) else None
    if prop_type == "relation":
        return [
            r.get("id")
            for r in prop.get("relation", [])
            if isinstance(r, dict)
        ]
    if prop_type == "rollup":
        rollup = prop.get("rollup", {})
        return rollup.get(rollup.get("type", "")) if isinstance(rollup, dict) else None
    if prop_type == "files":
        return [
            f.get("name", "")
            for f in prop.get("files", [])
            if isinstance(f, dict)
        ]
    if prop_type == "unique_id":
        uid = prop.get("unique_id")
        if isinstance(uid, dict):
            prefix = uid.get("prefix", "")
            number = uid.get("number", "")
            return f"{prefix}-{number}" if prefix else str(number)
        return None
    return None


def _simplify_properties(properties: Any) -> dict[str, Any]:  # noqa: ANN401
    """Simplify all properties in a Notion page properties dict."""
    if not isinstance(properties, dict):
        return {}
    return {
        name: _simplify_property(prop)
        for name, prop in properties.items()
        if isinstance(prop, dict)
    }


# --- Block text extraction ---


def _extract_block_text(block: dict[str, Any]) -> str | None:
    """Extract human-readable text content from a Notion block."""
    block_type = block.get("type", "")
    type_data = block.get(block_type)
    if not isinstance(type_data, dict):
        if block_type == "divider":
            return "---"
        if block_type == "breadcrumb":
            return "[breadcrumb]"
        return None

    rich_text = type_data.get("rich_text")
    if rich_text is not None:
        text = _extract_plain_text(rich_text)
        if block_type == "to_do":
            checked = "\u2611" if type_data.get("checked") else "\u2610"
            return f"{checked} {text}"
        if block_type == "code":
            lang = type_data.get("language", "")
            return f"[{lang}] {text}" if lang else text
        return text

    if block_type in ("child_page", "child_database"):
        return type_data.get("title", "")
    if block_type in ("image", "video", "file", "pdf", "audio"):
        file_data = type_data.get("file") or type_data.get("external")
        if isinstance(file_data, dict):
            return file_data.get("url")
        return None
    if block_type == "bookmark":
        return type_data.get("url")
    if block_type == "embed":
        return type_data.get("url")
    if block_type == "equation":
        return type_data.get("expression")
    if block_type == "link_to_page":
        return _opt_str(
            type_data.get("page_id") or type_data.get("database_id"),
        )
    if block_type == "table_of_contents":
        return "[table of contents]"
    if block_type == "column_list":
        return "[columns]"
    return None

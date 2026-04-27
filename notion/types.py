# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Typed models for Notion API responses.

Result types (frozen dataclasses):
  NotionResult         -- raw API result wrapper
  PageInfo             -- page summary with simplified properties
  BlockInfo            -- content block
  DatabaseInfo         -- database schema summary
  CommentInfo          -- page/block comment
  UserInfo             -- workspace user

Type aliases:
  JSONPrimitive        -- scalar JSON values
  JSONValue            -- recursive JSON value (pre-3.12 TypeAlias)
  JSONObject           -- dict[str, JSONValue]
  JSONArray            -- list[JSONValue]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias


# --- JSON types ---

JSONPrimitive: TypeAlias = str | int | float | bool | None
"""Scalar JSON values. Non-recursive, safe as plain union."""

JSONValue: TypeAlias = str | int | float | bool | dict[str, Any] | list[Any] | None
"""Recursive JSON value: primitive, object, or array.

Cannot be truly recursive with TypeAlias (pre-3.12); uses Any for nesting.
"""

JSONObject: TypeAlias = dict[str, JSONValue]
"""JSON object: string keys mapped to JSON values."""

JSONArray: TypeAlias = list[JSONValue]
"""JSON array: ordered sequence of JSON values."""


# --- Generic result ---


@dataclass(frozen=True, slots=True)
class NotionResult:
    """Raw Notion API result.

    Used as the internal request return type wrapping
    success/failure and response data.
    """

    # fmt: off
    success: bool
    data:    JSONValue | None = None
    error:   str | None       = None
    # fmt: on


# --- Pages ---


@dataclass(frozen=True, slots=True)
class PageInfo:
    """Page summary with simplified properties."""

    # fmt: off
    id:               str
    title:            str
    url:              str | None          = None
    parent_type:      str | None          = None
    parent_id:        str | None          = None
    created_time:     str | None          = None
    last_edited_time: str | None          = None
    archived:         bool                = False
    properties:       dict[str, Any] | None = None
    # fmt: on


# --- Blocks ---


@dataclass(frozen=True, slots=True)
class BlockInfo:
    """Content block from a page."""

    # fmt: off
    id:           str
    type:         str
    text:         str | None = None
    has_children: bool       = False
    # fmt: on


# --- Databases ---


@dataclass(frozen=True, slots=True)
class DatabaseInfo:
    """Database schema summary."""

    # fmt: off
    id:               str
    title:            str
    description:      str | None           = None
    url:              str | None           = None
    properties:       dict[str, str] | None = None   # name -> type
    created_time:     str | None           = None
    last_edited_time: str | None           = None
    archived:         bool                 = False
    data_sources:     list[dict[str, str]] | None = None  # [{"id": ..., "name": ...}]
    # fmt: on


# --- Data sources ---


@dataclass(frozen=True, slots=True)
class DataSourceInfo:
    """Data source within a database (API version 2026-03-11+)."""

    # fmt: off
    id:               str
    title:            str
    description:      str | None            = None
    url:              str | None            = None
    is_inline:        bool                  = False
    properties:       dict[str, str] | None = None  # column name -> type
    created_time:     str | None            = None
    last_edited_time: str | None            = None
    # fmt: on


# --- Comments ---


@dataclass(frozen=True, slots=True)
class CommentInfo:
    """Page or block comment."""

    # fmt: off
    id:           str
    body:         str
    author:       str | None = None
    created_time: str | None = None
    # fmt: on


# --- Users ---


@dataclass(frozen=True, slots=True)
class UserInfo:
    """Workspace user."""

    # fmt: off
    id:         str
    name:       str
    type:       str            = "person"
    email:      str | None     = None
    avatar_url: str | None     = None
    # fmt: on


# --- File uploads ---


@dataclass(frozen=True, slots=True)
class FileUploadInfo:
    """File upload result."""

    # fmt: off
    id:           str
    status:       str
    file_name:    str | None = None
    content_type: str | None = None
    # fmt: on

# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""MCP server entrypoint.

Expose Notion tools via Dedalus MCP framework.
API key credentials provided by DAuth at runtime.
"""

import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from notion.config import notion
from tools import notion_tools

# ---------------------------------------------------------------------------
# Workaround: dedalus_mcp wraps non-object output schemas in an envelope
# but leaves $defs nested inside properties.result, so $ref pointers that
# resolve from the schema root hit PointerToNowhere. Hoist $defs to the
# wrapper root before the envelope is sealed.
# Remove once dedalus_mcp >= 0.7.1 ships with the upstream fix.
# ---------------------------------------------------------------------------
from dedalus_mcp.utils import schema as _schema  # noqa: E402

_orig_ensure = _schema.ensure_object_schema


def _ensure_object_schema_fixed(
    schema: _schema.JsonSchema,
    *,
    wrap_scalar: bool = True,
    wrap_field: str = _schema.DEFAULT_WRAP_FIELD,
    marker: str = _schema.DEDALUS_BOX_KEY,
) -> _schema.SchemaEnvelope:
    if _schema._describes_object(schema):
        return _schema.SchemaEnvelope(schema=_schema._clone_schema(schema))

    if not wrap_scalar:
        raise _schema.SchemaError(
            "Schema describes a non-object value. "
            "Set wrap_scalar=True to comply with MCP output rules."
        )

    inner = _schema._clone_schema(schema)
    hoisted: _schema.JsonSchema = {}
    if isinstance(inner, dict):
        for key in ("$defs", "definitions"):
            if key in inner:
                hoisted[key] = inner.pop(key)

    wrapped: _schema.JsonSchema = {
        "type": "object",
        "properties": {wrap_field: inner},
        "required": [wrap_field],
        "additionalProperties": False,
        marker: {"field": wrap_field},
        **hoisted,
    }
    return _schema.SchemaEnvelope(schema=wrapped, wrap_field=wrap_field)


_schema.ensure_object_schema = _ensure_object_schema_fixed

# ---------------------------------------------------------------------------
# Second workaround: ToolsService._build_output_schema unconditionally pops
# $defs from the final schema (line 397 in tools.py). This undoes the hoist
# above, leaving $ref pointers dangling. Patch it to preserve $defs.
# Remove once dedalus_mcp >= 0.7.1 ships with the upstream fix.
# ---------------------------------------------------------------------------
import inspect

from dedalus_mcp.server.services.tools import ToolsService

_orig_build_output = ToolsService._build_output_schema


def _build_output_schema_fixed(self, fn):  # noqa: ANN001, ANN201
    signature = inspect.signature(fn)
    annotation = signature.return_annotation
    if annotation in (inspect.Signature.empty, any, None):
        return None

    try:
        from typing import Any, get_type_hints

        closure_ns: dict[str, Any] = {}
        if fn.__closure__:
            for cell in fn.__closure__:
                try:
                    value = cell.cell_contents
                except ValueError:
                    continue
                name = getattr(value, "__name__", None)
                if isinstance(name, str):
                    closure_ns.setdefault(name, value)

        resolved = get_type_hints(fn, include_extras=True, localns=closure_ns)
        annotation = resolved.get("return", annotation)
    except (NameError, TypeError):
        pass

    from dedalus_mcp.server.services.tools import _OUTPUT_SCHEMA_BLOCKLIST, _annotation_contains, _prune_titles
    from dedalus_mcp.utils.schema import SchemaError, resolve_output_schema

    if annotation in (Any, None):
        return None

    from dedalus_mcp import types as _mcp_types

    if annotation in (_mcp_types.CallToolResult, _mcp_types.ServerResult):
        return None

    if _annotation_contains(annotation, _OUTPUT_SCHEMA_BLOCKLIST):
        return None

    try:
        envelope = resolve_output_schema(annotation)
    except SchemaError:
        return None

    schema = envelope.schema
    _prune_titles(schema)
    return schema


ToolsService._build_output_schema = _build_output_schema_fixed


def create_server() -> MCPServer:
    """Create MCP server with current env config.

    Returns:
        Configured MCPServer instance.

    """
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    server = MCPServer(
        name="notion-mcp",
        connections=[notion],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )
    return server


async def main() -> None:
    """Start MCP server."""
    server = create_server()
    server.collect(*notion_tools)
    await server.serve(host="0.0.0.0")

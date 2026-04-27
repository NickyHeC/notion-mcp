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

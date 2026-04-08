# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Notion connection configuration.

Evaluated at import time, after ``load_dotenv()`` in ``main.py``
has already injected the .env file.

Notion uses an internal integration token for authentication.
The Dedalus platform handles token injection; the server only
declares the secret name it expects.

Objects:
  notion -- Connection with Bearer token auth
"""

from __future__ import annotations

from dedalus_mcp.auth import Connection, SecretKeys


notion = Connection(
    name="notion",
    secrets=SecretKeys(token="NOTION_API_KEY"),  # noqa: S106
    base_url="https://api.notion.com/v1",
    auth_header_format="Bearer {api_key}",
)

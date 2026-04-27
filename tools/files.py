# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""File upload tools.

Tools:
  notion_upload_file -- create a file upload for use in page blocks
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from notion.request import _opt_str, _str, api_request
from notion.types import FileUploadInfo, NotionResult


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def notion_upload_file(
    file_name: str,
    content_type: str,
    mode: str = "single_part",
    external_url: str | None = None,
) -> FileUploadInfo | str:
    """Create a file upload in Notion.

    Initiates a file upload that can be referenced in page blocks.
    After creating the upload, use the returned ID when adding
    file, image, or other media blocks to pages.

    Note: File upload support depends on the Dedalus enclave's
    ability to handle the upload flow. Binary content upload
    may require additional steps outside this tool.

    Args:
        file_name: Name of the file (e.g. ``report.pdf``).
        content_type: MIME type (e.g. ``application/pdf``).
        mode: Upload mode — ``single_part`` or ``multi_part``.
        external_url: URL to fetch the file from. Optional.

    Returns:
        FileUploadInfo with the upload ID, or error string.

    """
    body: dict[str, Any] = {
        "file_name": file_name,
        "content_type": content_type,
        "mode": mode,
    }
    if external_url:
        body["external_url"] = external_url

    response: NotionResult = await api_request(
        HttpMethod.POST, "/file_uploads", body=body,
    )
    if not response.success:
        return response.error or "Failed to create file upload"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"

    result = FileUploadInfo(
        id=_str(data.get("id")),
        status=_str(data.get("status"), "unknown"),
        file_name=_opt_str(data.get("file_name")),
        content_type=_opt_str(data.get("content_type")),
    )
    return result


file_tools = [
    notion_upload_file,
]

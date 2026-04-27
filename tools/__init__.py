# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Tool registry for notion-mcp.

Modules:
  search    -- notion_search
  pages     -- notion_get_page, notion_create_page, notion_update_page
  blocks    -- notion_get_page_content, notion_append_page_content
  databases -- notion_get_database, notion_query_database, notion_create_database
  markdown  -- notion_get_page_markdown, notion_update_page_markdown
  comments  -- notion_get_comments, notion_add_comment
  users     -- notion_list_users
  files     -- notion_upload_file
"""

from __future__ import annotations

from tools.blocks import block_tools
from tools.comments import comment_tools
from tools.databases import database_tools
from tools.files import file_tools
from tools.markdown import markdown_tools
from tools.pages import page_tools
from tools.search import search_tools
from tools.users import user_tools


notion_tools = [
    *search_tools,
    *page_tools,
    *block_tools,
    *database_tools,
    *markdown_tools,
    *comment_tools,
    *user_tools,
    *file_tools,
]

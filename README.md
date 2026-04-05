# notion-mcp

A Notion MCP server built on the [Dedalus](https://dedaluslabs.ai) framework.

Provides comprehensive access to Notion workspaces through the Model Context Protocol,
enabling AI agents to search, read, create, and update Notion content programmatically.

## Features

- **Search** — full-text search across all pages and databases in a workspace
- **Pages** — get, create, and update pages with simplified property handling
- **Content** — read and append block-based page content
- **Databases** — create databases, query with filters/sorting, retrieve schemas
- **Markdown** — read and write page content using Notion's enhanced markdown format
- **Comments** — list and add comments on pages and discussion threads
- **Users** — list workspace members (people and bots)
- **File uploads** — initiate file uploads for media attachments
- Automatic `Notion-Version` header injection (2026-03-11)
- Rate limited to 3 req/s — respect `Retry-After` headers on 429 responses

## Available Tools

| Tool | Description |
|------|-------------|
| `notion_search` | Search across all pages and databases in workspace |
| `notion_get_page` | Retrieve a page by ID with simplified properties |
| `notion_create_page` | Create a new page under a page or in a database |
| `notion_update_page` | Update page properties, archive status, icon, or cover |
| `notion_get_page_content` | Get child blocks (content) of a page |
| `notion_append_page_content` | Append blocks to a page |
| `notion_get_database` | Retrieve database schema and metadata |
| `notion_query_database` | Query a database with filters and sorting |
| `notion_create_database` | Create a new database under a page |
| `notion_get_page_markdown` | Get page content as enhanced markdown |
| `notion_update_page_markdown` | Update page content using markdown |
| `notion_get_comments` | List comments on a page or block |
| `notion_add_comment` | Add a comment to a page or discussion thread |
| `notion_list_users` | List all workspace users |
| `notion_upload_file` | Create a file upload for media blocks |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- A Notion internal integration ([create one here](https://www.notion.so/my-integrations))

### Installation

```bash
uv sync
```

### Configuration

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Add your Notion internal integration token:

```
NOTION_API_KEY=ntn_...
```

3. **Connect your integration** to the pages/databases you want to access
   in Notion (Share → Connections → select your integration).

### Running

```bash
uv run src/main.py
```

The server starts on port **8080** and exposes tools via the MCP protocol.

## Architecture

```
src/
├── main.py                 # Entrypoint — load_dotenv + asyncio.run
├── server.py               # MCPServer setup, tool registration
├── notion/
│   ├── config.py           # Connection + SecretKeys for Notion API
│   ├── request.py          # REST dispatch, coercion helpers, property simplification
│   └── types.py            # Frozen dataclasses (PageInfo, BlockInfo, etc.)
└── tools/
    ├── __init__.py          # Aggregates all tool lists into notion_tools
    ├── search.py            # notion_search
    ├── pages.py             # notion_get_page, notion_create_page, notion_update_page
    ├── blocks.py            # notion_get_page_content, notion_append_page_content
    ├── databases.py         # notion_get_database, notion_query_database, notion_create_database
    ├── markdown.py          # notion_get_page_markdown, notion_update_page_markdown
    ├── comments.py          # notion_get_comments, notion_add_comment
    ├── users.py             # notion_list_users
    └── files.py             # notion_upload_file
```

## Notion API Notes

- The integration must be explicitly connected to pages/databases to access them
- Maximum 100 results per paginated response
- File uploads limited to 5 MiB (free) / 5 GiB (paid workspaces)
- Some block types are read-only (e.g., AI meeting notes)
- API version is controlled by the `Notion-Version` header (2026-03-11)

## License

MIT

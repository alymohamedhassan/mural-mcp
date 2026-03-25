# Mural MCP

MCP server for working with [Mural Public API v1](https://developers.mural.co/public/reference/) from MCP-compatible clients (Cursor, Claude Desktop, and other MCP hosts).  
It supports browsing workspaces and rooms, creating/updating/deleting murals, and creating/updating/deleting mural widgets.

## Description

This project exposes Mural operations as MCP tools by wrapping Mural's REST API with a Python server built on `FastMCP`.

Highlights:

- OAuth2 authentication using `client_id`, `client_secret`, and a long-lived `refresh_token`
- Automatic access token refresh before expiration
- Tooling for:
  - workspace/room/mural navigation
  - mural CRUD
  - widget CRUD (sticky notes, shapes, text, arrows, areas, comments)

## Requirements

- Python `>=3.11`
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management and running)
- A Mural developer app with:
  - `MURAL_CLIENT_ID`
  - `MURAL_CLIENT_SECRET`
  - OAuth redirect URI configured in Mural

## Installation

Clone the repository and install dependencies:

```bash
git clone <your-repo-url>
cd arcsen-mural-mcp
uv sync
```

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Fill in:

```env
MURAL_CLIENT_ID=your-client-id
MURAL_CLIENT_SECRET=your-client-secret
MURAL_REFRESH_TOKEN=your-refresh-token
# Optional but recommended:
MURAL_REDIRECT_URI=http://localhost:8080/callback
```

## Get Initial Refresh Token (One-Time OAuth Setup)

If you only have client ID and secret, generate the first refresh token with:

```bash
./scripts/get_mural_refresh_token.sh
```

What it does:

1. Reads `MURAL_CLIENT_ID` and `MURAL_CLIENT_SECRET` from `.env`
2. Builds OAuth authorization URL
3. Prompts you for the returned authorization `code`
4. Exchanges code for tokens and prints `MURAL_REFRESH_TOKEN=...`

Then paste that value into your `.env`.

> Note: redirect URI must match exactly between:
> - your Mural app settings
> - the authorization request
> - the token exchange request

## Run the MCP Server

Start server over stdio:

```bash
uv run main.py
```

This process is intended to be launched by an MCP host (rather than visited in a browser).

## Connect to Claude Desktop

Edit:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Example:

```json
{
  "mcpServers": {
    "mural": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/arcsen-mural-mcp",
        "main.py"
      ],
      "env": {
        "MURAL_CLIENT_ID": "your-client-id",
        "MURAL_CLIENT_SECRET": "your-client-secret",
        "MURAL_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

## Available Tool Groups

The server includes the following tool categories:

- **Navigation / Read**
  - `list_workspaces`
  - `list_rooms`
  - `list_murals_in_room`
  - `get_mural`
  - `get_mural_widgets`
  - `get_mural_widget`
- **Mural CRUD**
  - `create_mural`
  - `update_mural`
  - `delete_mural`
- **Widget Create**
  - `create_sticky_notes`
  - `create_shapes`
  - `create_titles`
  - `create_textboxes`
  - `create_arrow`
  - `create_area`
  - `create_comment`
- **Widget Update**
  - `update_sticky_note`
  - `update_shape`
  - `update_text`
  - `update_arrow`
  - `update_area`
  - `update_comment`
- **Widget Delete**
  - `delete_widget`

## Arrow Accuracy Tip

To avoid randomly placed arrows, prefer anchored connectors:

- Use `create_arrow` with `start_ref_id` and `end_ref_id`
- Use widget IDs from created/fetched source and target shapes
- Avoid relying only on raw `x/y` and `points`

## Troubleshooting

- **`RuntimeError` for missing env vars**  
  Ensure `MURAL_CLIENT_ID`, `MURAL_CLIENT_SECRET`, and `MURAL_REFRESH_TOKEN` are present.

- **OAuth redirect shows "site can't be reached"**  
  This can still be fine if URL contains `?code=...`. Copy the code from the URL and continue.

- **OAuth redirect returns 404 on local server**  
  Usually means redirect reached your local server but no matching path exists. You can still copy `code` from the URL.

- **No tools appear in Claude Desktop**  
  Validate JSON config, confirm absolute path, and restart Claude Desktop fully.

## Development Notes

- Entry point: `main.py`
- Auth and token refresh logic: `MuralClient` class in `main.py`
- OAuth helper script: `scripts/get_mural_refresh_token.sh`

## License

Add your project license here (for example, MIT).

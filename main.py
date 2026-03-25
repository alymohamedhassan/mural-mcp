from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

BASE_URL = "https://app.mural.co/api/public/v1"

mcp = FastMCP("Mural")


class MuralClient:
    def __init__(self) -> None:
        token = os.environ.get("MURAL_API_TOKEN", "")
        if not token:
            raise RuntimeError("MURAL_API_TOKEN environment variable is not set")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=BASE_URL,
            headers=self._headers,
            timeout=30.0,
        )

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        async with self._client() as c:
            r = await c.get(path, params=params)
            r.raise_for_status()
            return r.json()

    async def post(self, path: str, body: Any) -> dict:
        async with self._client() as c:
            r = await c.post(path, json=body)
            r.raise_for_status()
            return r.json()

    async def patch(self, path: str, body: dict) -> dict:
        async with self._client() as c:
            r = await c.patch(path, json=body)
            r.raise_for_status()
            return r.json()

    async def delete(self, path: str) -> str:
        async with self._client() as c:
            r = await c.delete(path)
            r.raise_for_status()
            if r.status_code == 204 or not r.content:
                return json.dumps({"status": "deleted"})
            return r.text


_client = MuralClient()


def _result(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2)


def _optional_params(mapping: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in mapping.items() if v is not None}


# ---------------------------------------------------------------------------
# Navigation / Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_workspaces(limit: int | None = None, next_token: str | None = None) -> str:
    """List all workspaces the authenticated user is a member of.

    Args:
        limit: Max results to return.
        next_token: Pagination token from a previous response.
    """
    params = _optional_params({"limit": limit, "next": next_token})
    return _result(await _client.get("/workspaces", params or None))


@mcp.tool()
async def list_rooms(workspace_id: str, limit: int | None = None, next_token: str | None = None) -> str:
    """List rooms in a workspace that the authenticated user has access to.

    Args:
        workspace_id: The workspace ID.
        limit: Max results to return.
        next_token: Pagination token from a previous response.
    """
    params = _optional_params({"limit": limit, "next": next_token})
    return _result(await _client.get(f"/workspaces/{workspace_id}/rooms", params or None))


@mcp.tool()
async def list_murals_in_room(room_id: int, limit: int | None = None, next_token: str | None = None) -> str:
    """List murals in a room.

    Args:
        room_id: The room ID (integer).
        limit: Max results to return.
        next_token: Pagination token from a previous response.
    """
    params = _optional_params({"limit": limit, "next": next_token})
    return _result(await _client.get(f"/rooms/{room_id}/murals", params or None))


@mcp.tool()
async def get_mural(mural_id: str) -> str:
    """Get details of a single mural.

    Args:
        mural_id: The mural ID (format: "workspaceId.timestamp", e.g. "workspace1234.1608152669000").
    """
    return _result(await _client.get(f"/murals/{mural_id}"))


@mcp.tool()
async def get_mural_widgets(
    mural_id: str,
    type_filter: str | None = None,
    parent_id: str | None = None,
    limit: int | None = None,
    next_token: str | None = None,
) -> str:
    """Get all widgets on a mural. Use type_filter to narrow results.

    Args:
        mural_id: The mural ID.
        type_filter: Comma-separated widget types to filter. Options: areas, arrows, comments, files, sticky notes, texts, icons, images, shapes.
        parent_id: Filter widgets by their parent area ID.
        limit: Max results to return.
        next_token: Pagination token from a previous response.
    """
    params = _optional_params({
        "type": type_filter,
        "parentId": parent_id,
        "limit": limit,
        "next": next_token,
    })
    return _result(await _client.get(f"/murals/{mural_id}/widgets", params or None))


@mcp.tool()
async def get_mural_widget(mural_id: str, widget_id: str) -> str:
    """Get a single widget by its ID.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID.
    """
    return _result(await _client.get(f"/murals/{mural_id}/widgets/{widget_id}"))


# ---------------------------------------------------------------------------
# Mural CRUD
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_mural(
    room_id: int,
    title: str | None = None,
    background_color: str | None = None,
    width: int | None = None,
    height: int | None = None,
    infinite: bool | None = None,
) -> str:
    """Create a new mural in a room.

    Args:
        room_id: The room ID to create the mural in (required).
        title: Title of the mural.
        background_color: Background color in hex with alpha (e.g. "#FFFFFFFF").
        width: Width of the mural in px (3000-60000, default 9216).
        height: Height of the mural in px (3000-60000, default 6237).
        infinite: If true, canvas is borderless and grows as you add widgets.
    """
    body: dict[str, Any] = {"roomId": room_id}
    body.update(_optional_params({
        "title": title,
        "backgroundColor": background_color,
        "width": width,
        "height": height,
        "infinite": infinite,
    }))
    return _result(await _client.post("/murals", body))


@mcp.tool()
async def update_mural(
    mural_id: str,
    title: str | None = None,
    background_color: str | None = None,
) -> str:
    """Update a mural's properties.

    Args:
        mural_id: The mural ID.
        title: New title.
        background_color: New background color in hex with alpha.
    """
    body = _optional_params({
        "title": title,
        "backgroundColor": background_color,
    })
    return _result(await _client.patch(f"/murals/{mural_id}", body))


@mcp.tool()
async def delete_mural(mural_id: str) -> str:
    """Delete a mural.

    Args:
        mural_id: The mural ID to delete.
    """
    return await _client.delete(f"/murals/{mural_id}")


# ---------------------------------------------------------------------------
# Widget Create tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_sticky_notes(mural_id: str, widgets: list[dict[str, Any]]) -> str:
    """Create one or more sticky note widgets on a mural (limit 1000).

    Each widget object supports:
      - x, y (required): Position in px.
      - shape (required): "circle" or "rectangle".
      - text: Plain text content.
      - htmlText: HTML-formatted text (overrides text).
      - width, height: Size in px (default 138).
      - style: { backgroundColor, bold, italic, underline, strike, font, fontSize, textAlign, border }.
      - parentId: ID of parent area widget.
      - tags: Array of tag IDs.

    Args:
        mural_id: The mural ID.
        widgets: Array of sticky note objects.
    """
    return _result(await _client.post(f"/murals/{mural_id}/widgets/sticky-note", widgets))


@mcp.tool()
async def create_shapes(mural_id: str, widgets: list[dict[str, Any]]) -> str:
    """Create one or more shape widgets on a mural (limit 1000).

    Each widget object supports:
      - x, y (required): Position in px.
      - shape (required): One of: ellipse, rectangle, rounded_square, rhombus_smart, triangle_smart,
        hexagon_smart, pentagon_smart, diamond, process, decision, terminator, start, end, delay,
        data, database, document, multiple_documents, predefined_process, manual_input, manual_loop,
        preparation, stored_data, connector, merge, or, summing_junction, display, direct_data,
        internal_storage, papertape, loop_limit, off_page_connector, cloud, cross, star, badge,
        ribbon, step, trapezoid, octagon, speech_bubble_left, speech_bubble_right, speech_bubble_center,
        thinking_bubble_left, thinking_bubble_right, arrow_right, arrow_left, arrow_down, arrow_top,
        arrow_left_right, brace_left, brace_right, note_left, note_right, teardrop_bubble, right_triangle.
      - text: Plain text content.
      - htmlText: HTML-formatted text.
      - width, height: Size in px (default 138).
      - style: { backgroundColor, borderColor, borderStyle, borderWidth, bold, italic, underline, strike, font, fontColor, fontSize, textAlign }.
      - parentId: ID of parent area widget.

    Args:
        mural_id: The mural ID.
        widgets: Array of shape objects.
    """
    return _result(await _client.post(f"/murals/{mural_id}/widgets/shape", widgets))


@mcp.tool()
async def create_titles(mural_id: str, widgets: list[dict[str, Any]]) -> str:
    """Create one or more title widgets on a mural (limit 1000). Titles auto-grow width to fit text.

    Each widget object supports:
      - text: The title text (supports HTML: <b>, <i>, <u>, <s>, <span style="color:...">>).
      - x, y: Position in px (default 0).
      - width: Width in px (default 293).
      - height: Height in px (default 62).
      - style: { backgroundColor, font, fontSize (default 48), textAlign }.
      - parentId: ID of parent area widget.

    Args:
        mural_id: The mural ID.
        widgets: Array of title objects.
    """
    return _result(await _client.post(f"/murals/{mural_id}/widgets/title", widgets))


@mcp.tool()
async def create_textboxes(mural_id: str, widgets: list[dict[str, Any]]) -> str:
    """Create one or more textbox widgets on a mural (limit 1000). Textboxes wrap text to fixed width.

    Each widget object supports:
      - text: The textbox text (supports HTML: <b>, <i>, <u>, <s>, <span style="color:...">>).
      - x, y: Position in px (default 0).
      - width: Width in px (default 296).
      - height: Height in px (default 28).
      - style: { backgroundColor, font, fontSize (default 24), textAlign }.
      - parentId: ID of parent area widget.

    Args:
        mural_id: The mural ID.
        widgets: Array of textbox objects.
    """
    return _result(await _client.post(f"/murals/{mural_id}/widgets/textbox", widgets))


@mcp.tool()
async def create_arrow(
    mural_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
    points: list[dict[str, float]],
    arrow_type: str | None = None,
    tip: str | None = None,
    start_ref_id: str | None = None,
    end_ref_id: str | None = None,
    style: dict[str, Any] | None = None,
    label: dict[str, Any] | None = None,
    parent_id: str | None = None,
) -> str:
    """Create an arrow (connector) widget on a mural.

    Args:
        mural_id: The mural ID.
        x: Horizontal position in px.
        y: Vertical position in px.
        width: Width of the bounding box in px.
        height: Height of the bounding box in px.
        points: Array of {x, y} coordinate objects defining the arrow path (min 2 points).
        arrow_type: "straight" (default), "curved", or "orthogonal".
        tip: "single" (default), "double", or "no tip".
        start_ref_id: ID of the widget the arrow starts from (snaps to it).
        end_ref_id: ID of the widget the arrow ends at (snaps to it).
        style: { strokeColor (hex+alpha), strokeStyle ("solid"|"dashed"|"dotted-spaced"|"dotted"), strokeWidth (1-7) }.
        label: { format: {color, fontFamily, bold, italic, textAlign, fontSize}, labels: [{x, y, height, width, text}] }.
        parent_id: ID of parent area widget.
    """
    body: dict[str, Any] = {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "points": points,
    }
    body.update(_optional_params({
        "arrowType": arrow_type,
        "tip": tip,
        "startRefId": start_ref_id,
        "endRefId": end_ref_id,
        "style": style,
        "label": label,
        "parentId": parent_id,
    }))
    return _result(await _client.post(f"/murals/{mural_id}/widgets/arrow", body))


@mcp.tool()
async def create_area(
    mural_id: str,
    x: float | None = None,
    y: float | None = None,
    width: float | None = None,
    height: float | None = None,
    title: str | None = None,
    layout: str | None = None,
    show_title: bool | None = None,
    style: dict[str, Any] | None = None,
    parent_id: str | None = None,
) -> str:
    """Create an area (swimlane/zone) widget on a mural.

    Args:
        mural_id: The mural ID.
        x: Horizontal position in px (default 0).
        y: Vertical position in px (default 0).
        width: Width in px (default 460).
        height: Height in px (default 503).
        title: Title text displayed on the area.
        layout: "free" (default), "column", or "row".
        show_title: Whether to display the title (default true).
        style: { backgroundColor, borderColor, borderStyle ("solid"|"dotted"), borderWidth (1-7), titleFontSize }.
        parent_id: ID of parent area widget (for nested areas).
    """
    body = _optional_params({
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "title": title,
        "layout": layout,
        "showTitle": show_title,
        "style": style,
        "parentId": parent_id,
    })
    return _result(await _client.post(f"/murals/{mural_id}/widgets/area", body))


@mcp.tool()
async def create_comment(
    mural_id: str,
    x: float,
    y: float,
    message: str,
    reference_widget_id: str | None = None,
    parent_id: str | None = None,
) -> str:
    """Create a comment widget on a mural.

    Args:
        mural_id: The mural ID.
        x: Horizontal position in px.
        y: Vertical position in px.
        message: The comment text.
        reference_widget_id: ID of the widget this comment is attached to.
        parent_id: ID of parent area widget.
    """
    body: dict[str, Any] = {"x": x, "y": y, "message": message}
    body.update(_optional_params({
        "referenceWidgetId": reference_widget_id,
        "parentId": parent_id,
    }))
    return _result(await _client.post(f"/murals/{mural_id}/widgets/comment", body))


# ---------------------------------------------------------------------------
# Widget Update tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def update_sticky_note(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update a sticky note widget on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the sticky note.
        properties: Object with fields to update. Supported fields:
            x, y, width, height, rotation, text, htmlText,
            style: { backgroundColor, bold, italic, underline, strike, font, fontSize, textAlign, border },
            tags, title, hyperlink, hyperlinkTitle, parentId, hidden.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/sticky-note/{widget_id}", properties))


@mcp.tool()
async def update_shape(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update a shape widget on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the shape.
        properties: Object with fields to update. Supported fields:
            x, y, width, height, rotation, text, htmlText,
            style: { backgroundColor, borderColor, borderStyle, borderWidth, bold, italic, underline, strike, font, fontColor, fontSize, textAlign },
            title, parentId, hidden.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/shape/{widget_id}", properties))


@mcp.tool()
async def update_text(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update a text widget (title or textbox) on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the text/title/textbox.
        properties: Object with fields to update. Supported fields:
            x, y, width, height, rotation, text,
            style: { backgroundColor, font, fontSize, textAlign },
            title, hyperlink, hyperlinkTitle, parentId, hidden.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/text/{widget_id}", properties))


@mcp.tool()
async def update_arrow(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update an arrow (connector) widget on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the arrow.
        properties: Object with fields to update. Supported fields:
            x, y, width, height, points, arrowType ("straight"|"curved"|"orthogonal"),
            tip ("single"|"double"|"no tip"), startRefId, endRefId,
            style: { strokeColor, strokeStyle, strokeWidth },
            label: { format: {...}, labels: [...] }, parentId.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/arrow/{widget_id}", properties))


@mcp.tool()
async def update_area(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update an area (swimlane/zone) widget on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the area.
        properties: Object with fields to update. Supported fields:
            x, y, width, height, title, layout ("free"|"column"|"row"), showTitle,
            style: { backgroundColor, borderColor, borderStyle, borderWidth, titleFontSize },
            parentId, hidden.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/area/{widget_id}", properties))


@mcp.tool()
async def update_comment(mural_id: str, widget_id: str, properties: dict[str, Any]) -> str:
    """Update a comment widget on a mural.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID of the comment.
        properties: Object with fields to update. Supported fields:
            x, y, message, referenceWidgetId, parentId.
    """
    return _result(await _client.patch(f"/murals/{mural_id}/widgets/comment/{widget_id}", properties))


# ---------------------------------------------------------------------------
# Widget Delete
# ---------------------------------------------------------------------------


@mcp.tool()
async def delete_widget(mural_id: str, widget_id: str) -> str:
    """Delete any widget from a mural by its ID.

    Args:
        mural_id: The mural ID.
        widget_id: The widget ID to delete.
    """
    return await _client.delete(f"/murals/{mural_id}/widgets/{widget_id}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()

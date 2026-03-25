---
name: mural-diagrams
description: "Use this skill whenever the user wants to create, edit, or manage diagrams inside Mural — including flowcharts, process diagrams, swimlane diagrams, or any layout involving shapes connected by arrows. Trigger this skill when the user mentions Mural and wants to add shapes, connect them with arrows, build a flow, add sticky notes, or arrange widgets on a mural canvas. Also trigger when the user asks to \"draw\", \"diagram\", \"flow\", or \"connect\" things inside Mural, or references mural IDs, room IDs, or widget IDs. Use proactively if the user is building anything multi-step or connected inside Mural — even if they don't say \"diagram\" explicitly."
---
 
# Mural Diagrams Skill
 
A skill for building well-positioned diagrams in Mural using shapes, arrows, and sticky notes via the Mural MCP tools.
 
Before creating the diagram, proceed with using AskUserQuestions if you have any clarifications needed, whether in the process, styling or technical questions.
 
---
 
## Core Tools
 
| Tool | Purpose |
|------|---------|
| `mural:list_workspaces` | Find workspace IDs |
| `mural:list_rooms` | Find room IDs inside a workspace |
| `mural:create_mural` | Create a new mural in a room |
| `mural:create_shapes` | Add shape widgets to a mural |
| `mural:create_arrow` | Add a connector arrow between widgets |
| `mural:create_sticky_notes` | Add sticky note (Post-it style) widgets |
| `mural:get_mural_widgets` | Fetch all current widgets and their positions |
| `mural:update_shape` | Update an existing shape |
| `mural:update_arrow` | Update an existing arrow |
| `mural:delete_widget` | Delete any widget by ID |
 
---
 
## Positioning System
 
Mural uses an **absolute canvas coordinate system** (px). The origin `(0, 0)` is the top-left. X increases rightward, Y increases downward.
 
### Shape Positioning
 
Shapes are positioned by their **top-left corner** `(x, y)`:
 
```
Shape top-left = (x, y)
Shape center   = (x + width/2,  y + height/2)
Shape bottom-center = (x + width/2,  y + height)
Shape top-center    = (x + width/2,  y)
```
 
Default shape size when not specified: **168×168 px**
 
### Vertical Stacking Formula
 
To stack shapes vertically with a gap:
 
```
shape_B.y = shape_A.y + shape_A.height + gap
```
 
Recommended gap between shapes: **82 px** (visually balanced)
 
Example — three shapes stacked with 82px gaps:
- Shape A: y=206, height=168 → bottom at 374
- Shape B: y=374+82=**456** would be too tight; use y=**470** for a clean look
- Arrow from A→B: starts at y = A.y + A.height = 374, height = B.y - 374
 
---
 
## Arrow Positioning — CRITICAL RULES
 
This is the most important section. Arrows behave differently depending on whether `startRefId`/`endRefId` are set.
 
### ✅ Rule 1: Always use `startRefId` + `endRefId` for connected arrows
 
When connecting two shapes, always set both `start_ref_id` and `end_ref_id` to the widget IDs of the source and target shapes. This snaps the arrow endpoints to the shapes and keeps them connected if shapes are moved.
 
### ✅ Rule 2: Points must be RELATIVE when ref IDs are set
 
When `startRefId` and `endRefId` are set, the `points` array must be **relative to the arrow's own `(x, y)` origin**, NOT absolute canvas coordinates.
 
```json
// CORRECT — relative points
{
  "x": 456,       // arrow origin = bottom-center of source shape
  "y": 374,
  "points": [{"x": 0, "y": 0}, {"x": 0, "y": 96}],
  "startRefId": "<source-shape-id>",
  "endRefId": "<target-shape-id>"
}
```
 
```json
// WRONG — absolute points (causes arrow to render far from shapes)
{
  "x": 456,
  "y": 374,
  "points": [{"x": 456, "y": 374}, {"x": 456, "y": 470}],
  "startRefId": "<source-shape-id>",
  "endRefId": "<target-shape-id>"
}
```
 
### ✅ Rule 3: Arrow origin = bottom-center of source shape
 
For a vertical downward arrow:
 
```
arrow.x = source.x + source.width / 2
arrow.y = source.y + source.height
arrow.height = target.y - arrow.y
arrow.width = 1  (thin bounding box for straight vertical)
points = [{x: 0, y: 0}, {x: 0, y: arrow.height}]
```
 
### ✅ Rule 4: Without ref IDs, points are ABSOLUTE
 
If you omit `startRefId`/`endRefId`, the `points` array must use **absolute canvas coordinates**. The arrow will render correctly but will NOT follow shapes if they are moved.
 
---
 
## Preferred Diagram Style (from DHCM IVR Process reference)
 
**The default style for all process diagrams is the DHCM IVR pattern: horizontal flow using sticky notes, not shapes.**
 
### Widget Type: Sticky Notes (not shapes)
 
Always use `mural:create_sticky_notes` with `shape: "rectangle"` for process steps — NOT `mural:create_shapes`. Sticky notes are the standard building block for process diagrams.
 
### Color System (Semantic)
 
| Color | Hex | Meaning |
|-------|-----|---------|
| 🟡 Yellow | `#FCF281FF` | IVR / Genesys step (default process step) |
| 🔵 Blue | `#2897DCFF` | Salesforce action / external system call |
| 🟣 Purple | `#9E7EE6FF` | External trigger / inbound event |
 
Always apply color semantically based on what the step does, not randomly.
 
### Layout: Horizontal Flow (Left → Right)
 
Steps flow **left to right** along a shared Y axis (horizontal lane). Branches and sub-flows go **vertically** off the main lane. Use `arrow_type: "orthogonal"` for all connectors.
 
```
base_y = 500           # vertical center of the main flow lane
step_x_start = 200     # leftmost step
step_w = 168           # sticky note width
step_h = 168           # sticky note height
gap_h = 138            # horizontal gap between steps
 
step[i].x = step_x_start + i * (step_w + gap_h)
step[i].y = base_y
```
 
### Horizontal Arrow Formula
 
For a left-to-right arrow between two steps on the same row:
 
```
arrow.x = source.x + source.width     # right-center-x of source
arrow.y = source.y + source.height/2  # vertical center of source
arrow.width = target.x - arrow.x      # horizontal span
arrow.height = 1
points = [{x: 0, y: 0}, {x: arrow.width, y: 0}]   # relative, horizontal
```
 
For **orthogonal** arrows with waypoints (e.g. branching down then right):
```
points = [
  {x: arrow.width, y: 0},          # start (right-side of source)
  {x: arrow.width/2, y: 0},        # midpoint
  {x: arrow.width/2, y: 0},        # midpoint (Mural needs 4 points for orthogonal)
  {x: 0, y: 0}                     # end (left-side of target)
]
```
 
### Area Containers
 
Group related steps into a labeled area using `mural:create_area`. Areas have a title and a visible border, making sections of the diagram self-explanatory.
 
```python
mural:create_area(
  mural_id = "...",
  title = "Customer Validation",
  x = 495, y = 870,
  width = 1167, height = 737,
  style = {
    "backgroundColor": "#FFFFFFFF",
    "borderColor": "#EAEAEAFF",
    "borderStyle": "solid",
    "borderWidth": 3,
    "titleFontSize": 36
  },
  layout = "free",
  show_title = True
)
```
 
To place a sticky note inside an area, set `parentId` to the area's widget ID. When `parentId` is set, the sticky note's `x`/`y` are **relative to the area's top-left corner**, not absolute canvas coordinates.
 
### Arrow Labels
 
For decision branches ("Yes" / "No"), add a label to the arrow:
 
```python
label = {
  "format": {
    "bold": False,
    "color": "#000000FF",
    "fontFamily": "proxima-nova",
    "fontSize": 23,
    "italic": False,
    "textAlign": "center"
  },
  "labels": [{"height": 29, "text": "Yes", "width": 46, "x": 37, "y": -14}]
}
```
 
### Legend Area
 
Always include a **Legend** area in the top-right of the canvas. Based on the DHCM IVR reference:
 
- **Widget type**: `area` (type `mural:create_area`)
- **Title**: `"Legend"`
- **Size**: width=583, height=310
- **Position**: top-right of canvas, near the diagram title (e.g. x=1040, y=341)
- **Style**: white background `#FFFFFFFF`, light grey border `#EAEAEAFF`, borderWidth=3, titleFontSize=36
- **Contents**: small 40×40 sticky notes as color swatches (one per color in the color system), with `parentId` set to the legend area's ID so positions are relative
 
Example swatch inside the Legend area (relative coordinates):
```python
# Purple swatch at relative (43, 100) inside the legend area
{
  "x": 43, "y": 100,
  "width": 40, "height": 40,
  "shape": "rectangle",
  "style": {"backgroundColor": "#9E7EE6FF", "border": False, "fontSize": 6},
  "parentId": "<legend-area-id>"
}
```
Add a text widget next to each swatch describing what that color means.
 
### Title & Description Text
 
Add text widgets at the top-left of the canvas. Based on the DHCM IVR reference:
 
- **Title text**: x=203, y=341, fontSize=60, `textAlign: "left"`, transparent background `#FFFFFF00`, font `proxima-nova`
- **Subtitle/description**: x=203, y=429, fontSize=28, `textAlign: "left"`, `fixedWidth: true`, width=696
- **Section header** (e.g. "Process Overview"): fontSize=28, bold, placed above the diagram area
- **Section description**: fontSize=28, regular, placed below the section header, `fixedWidth: true`, width=~879
 
All text widgets use `type: "text"` and support HTML content via the `text` field with `<html v="1"><div>...</div></html>` format. Bold is done with `<b>` tags inside the HTML.
 
---
 
## Step-by-Step: Building a Vertical Flow Diagram
 
### Step 1 — Plan layout before calling any tools
 
For N shapes stacked vertically, compute all positions upfront:
 
```
base_x = 372          # left edge of shapes (adjust for visual centering)
base_y = 206          # top of first shape
shape_w = 168
shape_h = 168
gap = 82              # space between shapes
 
shape[i].x = base_x
shape[i].y = base_y + i * (shape_h + gap)
 
arrow[i].x = base_x + shape_w / 2        # = 456 with defaults
arrow[i].y = shape[i].y + shape_h        # bottom of source shape
arrow[i].height = shape[i+1].y - arrow[i].y   # = gap (82)
arrow[i].points = [{x:0, y:0}, {x:0, y:arrow[i].height}]
```
 
### Step 2 — Create all shapes first, collect their IDs
 
```python
# Create shapes, store returned IDs
start_id = response.value[0].id  # e.g. "4de882f2-..."
end_id   = response.value[0].id  # e.g. "5cdc5458-..."
```
 
### Step 3 — Create arrows with ref IDs and relative points
 
```python
mural:create_arrow(
  mural_id = "...",
  x = 456,            # bottom-center-x of source shape
  y = 374,            # bottom-y of source shape
  width = 1,
  height = 82,        # gap between shapes
  points = [{"x": 0, "y": 0}, {"x": 0, "y": 82}],
  start_ref_id = start_id,
  end_ref_id = end_id,
  arrow_type = "straight",
  tip = "single"
)
```
 
---
 
## Worked Example (from real session)
 
Three shapes stacked vertically: **Start → End → Mido**
 
| Widget | x | y | width | height | Notes |
|--------|---|---|-------|--------|-------|
| Start (shape) | 372 | 206 | 168 | 168 | bottom-center = (456, 374) |
| End (shape) | 372 | 470 | 168 | 168 | gap=96 from Start bottom; bottom-center = (456, 638) |
| Mido (shape) | 372 | 720 | 168 | 168 | gap=82 from End bottom |
| Arrow Start→End | x=456, y=374 | — | 1 | 96 | points: [{0,0},{0,96}] |
| Arrow End→Mido | x=456, y=638 | — | 1 | 82 | points: [{0,0},{0,82}] |
 
Both arrows use `startRefId` + `endRefId` with **relative** points.
 
---
 
## Sticky Notes
 
Sticky notes use the same absolute coordinate system as shapes. Default size: **168×168 px**. Default color: yellow (`#FCFE7DFF`).
 
```python
mural:create_sticky_notes(
  mural_id = "...",
  widgets = [{
    "x": 620,
    "y": 206,
    "text": "My note",
    "shape": "rectangle",  # or "circle"
    "width": 168,
    "height": 168
  }]
)
```
 
Place sticky notes to the side of existing shapes (offset x by ~250px) to avoid overlap.
 
---
 
## Common Mistakes to Avoid
 
| Mistake | Effect | Fix |
|---------|--------|-----|
| Using absolute coords in `points` when `startRefId` is set | Arrow renders far from shapes | Use `[{0,0}, {0,height}]` relative points |
| Setting `points` without `startRefId`/`endRefId` | Arrow floats, not connected | Either add ref IDs + relative points, or use absolute points without ref IDs |
| Passing `null` to `startRefId` via `update_arrow` | 400 error | Delete and recreate the arrow instead |
| Forgetting to offset `x` when placing shapes next to each other | Shapes overlap | Use `x = existing_x + existing_width + margin` |
| Not computing `arrow.y` from shape bottom | Misaligned arrows | Always use `arrow.y = source.y + source.height` |
 
---
 
## Retrieving Current Widget State
 
Before adding new widgets that must align with existing ones, always fetch current positions:
 
```python
mural:get_mural_widgets(
  mural_id = "...",
  type_filter = "shapes"   # or "arrows", "sticky notes", or omit for all
)
```
 
Use the returned `x`, `y`, `width`, `height` values to compute correct positions for new widgets.

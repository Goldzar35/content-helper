# Content Helper — Claude Code Guide

## Project Overview

Native Mac app (Python + PyQt6) for planning YouTube and Instagram video content. Videos move through a 7-stage pipeline via a card-based Kanban UI with fling gestures. Data persists in SQLite at `~/.content-helper/data.db`.

## Running from source

```bash
cd ~/content-helper
python3 main.py
```

## Building the .app

```bash
python3 build_app.py
# Then install with ditto (NOT cp -r — cp strips code signatures):
ditto "dist/Content Helper.app" ~/Desktop/"Content Helper.app"
```

Key PyInstaller flags required for macOS 15+:
- `--collect-all PyQt6` — bundles all Qt plugins (missing plugins cause PAC crash)
- `--osx-bundle-identifier com.goldzar.content-helper` — valid reverse-DNS bundle ID
- `codesign --force --deep --sign -` after build — re-signs all dylibs consistently

## File Structure

```
content-helper/
├── main.py                  # Entry point — applies GLOBAL_QSS to QApplication, launches MainWindow
├── build_app.py             # Builds Content Helper.app via PyInstaller
├── requirements.txt         # PyQt6>=6.4.0
└── app/
    ├── card.py              # VideoCard widget + fling animation
    ├── database.py          # SQLite persistence layer
    ├── detail_view.py       # Per-video detail / checklist view
    ├── models.py            # Video + ChecklistField dataclasses
    ├── new_video_dialog.py  # "New Video" modal dialog
    ├── settings_dialog.py   # Checklist field editor dialog
    ├── sounds.py            # Destruction sound on fling (afplay Basso.aiff)
    ├── stage_page.py        # Stage tab — grid of VideoCards
    ├── theme.py             # All colors, fonts, GLOBAL_QSS
    └── window.py            # MainWindow, TabButton, stack navigation
```

## Architecture

### Global Stylesheet
`GLOBAL_QSS` is applied to `QApplication` in `main.py` — NOT to `MainWindow`. This is critical: dialogs are separate top-level windows and don't inherit `QMainWindow` stylesheets. The QApplication-level stylesheet applies to everything.

### Navigation
`MainWindow` owns a `QStackedWidget` with indices 0–6 for the 7 `StagePage` instances, and index 7 for the single `DetailView`. `_DETAIL_IDX = 7`.

### Stages
Defined in `theme.py`:
```python
STAGE_KEYS = ["ideas", "planning", "filming", "editing", "posting", "review", "completed"]
STAGES     = ["Ideas", "Planning", "Filming", "Editing", "Posting", "Review", "Completed"]
```
`advance_stage` / `retreat_stage` in `database.py` move a video through the list by index — bounds-checked, no special casing needed.

### Color Palette

**Stage colors** (gold gradient — used for tab text + underline, section headers, progress rings):
```python
"ideas":     "#f5e6a3"   # pale champagne
"planning":  "#e8c84a"   # warm gold
"filming":   "#d4a017"   # classic gold
"editing":   "#b8860b"   # amber
"posting":   "#9a6e08"   # deep amber
"review":    "#7a5206"   # burnished bronze
"completed": "#5c3d04"   # dark bronze
```

**Category colors** (FigJam-inspired pastels — solid fill, white text):
```python
"armwrestling": "#e07a6a"   # coral
"gamedev":      "#6ac49a"   # mint green
"misc":         "#6aaee0"   # sky blue
```

**App chrome:**
- `BG_MAIN = "#141414"`, `BG_ELEVATED = "#1e1e1e"`, `BG_CARD = "#242424"`
- `ACCENT = "#d4a017"` (gold — New Video button, checkbox fill, selection)
- `ACCENT_TEXT = "#1a0e00"` (near-black for text on gold backgrounds)

### Card Fling Animation
`VideoCard` in `card.py` uses `QParallelAnimationGroup` (position + opacity). A ghost widget (pixmap of the card, tilted 4°) is parented to `self.window()` so it can fly past scroll area boundaries. After fling: `MainWindow._fling_navigate()` slides the destination stage tab in from the same direction, + window shake + `play_fling()` sound on a daemon thread.

**GC rule:** Always store `QPropertyAnimation` / `QParallelAnimationGroup` as `self._anim_*` instance vars. Local variables are GC'd mid-animation causing silent failures.

### Detail View Modes
`_rebuild_body()` in `detail_view.py` has three rendering paths:
1. **Normal stage** (ideas–posting): current stage fields expanded, previous stages collapsed under "Review" header.
2. **Review stage**: all 5 pipeline stages (ideas–posting) expanded, fully editable.
3. **Completed stage**: all 5 pipeline stages expanded, entirely read-only. `_collect_values()` returns early — nothing saves.

**Auto-save:** an 800ms `QTimer` debounces all field changes. `_save_and_back()` stops the timer and flushes immediately.

### Stage is Read-Only in Detail View
The Stage field in the detail view is a non-editable `QLabel` — stage changes only happen via fling. This prevents bypassing the pipeline UX.

### Single Source of Truth for Stage Moves
All advance/retreat DB logic lives in `MainWindow._on_advance()` / `_on_retreat()`. `StagePage` only emits signals — never touches DB or calls refresh. This prevents double-refresh race conditions.

### Geometry Persistence
Saved to `~/.content-helper/prefs.json` on close, restored on launch. Stored as `{x, y, w, h}`.

### Settings Dialog
Fields must be assigned to one of the 5 pipeline stages (ideas–posting). The "— all —" option was removed — stage-None fields are never shown in the detail view. `SettingsDialog` uses `STAGE_KEYS[:5]` / `STAGES[:5]`.

## Known QSS Quirks

- **8-character hex colors** (`#RRGGBBAA`) don't work reliably in QSS on macOS — use 6-char hex only.
- **QComboBox `::down-arrow`** requires an `image:` property to show a custom indicator; CSS border tricks don't work in QSS. Currently using the Qt default native arrow.
- **CollapsibleSection divider line**: uses `background:{color}` (solid, 1px) — the former `{color}30` alpha suffix rendered incorrectly on macOS.

## Known Issues / Next Steps

- Search / filter across all videos — not implemented.
- Drag to reorder cards within a stage — not implemented.
- Export (CSV, Notion, etc.) — not implemented.
- No drag-and-drop reorder for checklist fields in Settings (order is set by row position).
- `go_home()` / back-button logic from legacy whatnot-bot CLAUDE.md does not apply here.

# Content Helper — Claude Code Guide

## Project Overview

Native Mac app (Python + PyQt6) for planning YouTube and Instagram video content. Videos move through a 7-stage pipeline via a card-based Kanban UI with fling gestures. Data persists in SQLite at `~/.content-helper/data.db`.

## Running

```bash
cd ~/content-helper
python3 main.py
```

## File Structure

```
content-helper/
├── main.py                  # Entry point — just launches MainWindow
├── requirements.txt
├── app/
│   ├── card.py              # VideoCard widget + fling animation
│   ├── database.py          # SQLite persistence layer
│   ├── detail_view.py       # Per-video detail / checklist view
│   ├── models.py            # Video + ChecklistField dataclasses
│   ├── new_video_dialog.py  # "New Video" modal dialog
│   ├── settings_dialog.py   # Checklist field editor dialog
│   ├── sounds.py            # Destruction sound on fling (afplay Basso.aiff)
│   ├── stage_page.py        # Stage tab — grid of VideoCards
│   ├── theme.py             # All colors, fonts, global QSS
│   └── window.py            # MainWindow, TabButton, stack navigation
```

## Architecture

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

**Stage colors** (gold gradient, used for tab text + underline, section headers, progress rings):
```python
"ideas":     "#f5e6a3"   # pale champagne
"planning":  "#e8c84a"   # warm gold
"filming":   "#d4a017"   # classic gold
"editing":   "#b8860b"   # amber
"posting":   "#9a6e08"   # deep amber
"review":    "#7a5206"   # burnished bronze
"completed": "#5c3d04"   # dark bronze
```

**Category colors** (FigJam-inspired pastels, used for card pill + left border, white text on pill):
```python
"armwrestling": "#e07a6a"   # coral
"gamedev":      "#6ac49a"   # mint green
"misc":         "#6aaee0"   # sky blue
```

**App chrome:**
- `BG_MAIN = "#141414"`, `BG_ELEVATED = "#1e1e1e"`, `BG_CARD = "#242424"`
- `ACCENT = "#d4a017"` (gold — used for "+ New Video" button, checkbox fill, selection)
- `ACCENT_TEXT = "#1a0e00"` (near-black for text on gold backgrounds)

### Card Fling Animation
`VideoCard` in `card.py` uses `QParallelAnimationGroup` (position + opacity). A ghost widget (pixmap of the card, tilted 4°) is parented to `self.window()` so it can fly past scroll area boundaries. Animation refs stored as instance vars to prevent Python GC. After fling: `play_fling()` plays Basso.aiff on a daemon thread via `subprocess`.

**GC rule:** Always store `QPropertyAnimation` / `QParallelAnimationGroup` as `self._anim_*` instance vars — local variables get GC'd mid-animation causing silent failures.

### Detail View Modes
`_rebuild_body()` in `detail_view.py` has three rendering paths:
1. **Normal stage** (ideas–posting): current stage fields expanded, previous stages collapsed under "Review" header.
2. **Review stage**: all 5 pipeline stages (ideas–posting) expanded, fully editable.
3. **Completed stage**: all 5 pipeline stages expanded, entirely read-only (`setReadOnly(True)` on inputs, `setEnabled(False)` on checkboxes/combos). `_collect_values()` returns early — nothing is saved.

### Single Source of Truth for Stage Moves
All advance/retreat logic lives in `MainWindow._on_advance()` / `_on_retreat()`. `StagePage` only emits signals — it does not touch the DB or call refresh itself. This prevents double-refresh race conditions.

### Settings Dialog
`SettingsDialog` (`settings_dialog.py`) lets users add/edit/delete/reorder checklist fields. Each `FieldRow` has: label edit, type combo (text/textarea/checkbox), stage combo (all stages + "— all —"), active checkbox, delete button. "— all —" (`stage=None`) fields are not currently shown in the detail view (only stage-specific fields are fetched via `get_fields_for_stage`).

## Known Issues / Next Steps

- "— all —" fields (stage=None) are stored in DB but never shown in the detail view — `get_fields_for_stage` only fetches fields with a matching stage. Either remove the "— all —" option or implement a fallback fetch.
- Card progress ring shows 0% for Review and Completed cards (those stages have no checklist fields). Consider using overall completion across all stages instead.
- No drag-to-reorder for cards within a stage.
- No search / filter across videos.
- No export (CSV, Notion, etc.).

## What NOT to Do

- Do not add a `driver.quit()` equivalent — there's no persistent connection here, but don't close the DB in non-`closeEvent` paths.
- Do not call `refresh()` from inside `StagePage` after a stage change — route all state changes through `MainWindow`.
- Do not store animation objects as local variables — they will be GC'd before completion.
- Do not use 8-character hex colors (`#RRGGBBAA`) in QSS — Qt on macOS may not parse the alpha suffix correctly. Use the base 6-character hex instead.

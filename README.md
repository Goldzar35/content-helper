# Content Helper

A native Mac app for planning and tracking YouTube and Instagram video content. Dark gold theme, card-based Kanban UI, fully offline — your data never leaves your machine.

---

## Installation

### Option A — Download the app (easiest)

1. Go to the [Releases](../../releases) page and download `Content.Helper.app.zip`
2. Unzip it
3. Drag **Content Helper.app** to your `/Applications` folder (or Desktop)
4. **First launch only:** right-click the app → **Open** → click **Open** in the dialog
   *(macOS blocks unsigned apps by default — this one-time step tells it you trust it)*

### Option B — Run from source

Requires Python 3.10+.

```bash
# Clone
git clone https://github.com/Goldzar35/content-helper.git
cd content-helper

# Install dependencies
pip install -r requirements.txt

# Run
python3 main.py
```

### Option C — Build the .app yourself

```bash
pip install pyinstaller pillow
python3 build_app.py
```

Then install with:
```bash
ditto "dist/Content Helper.app" ~/Desktop/"Content Helper.app"
```

> **Important:** Use `ditto` not `cp -r` — regular copy strips macOS code signatures and the app will crash on launch.

---

## Features

### Pipeline stages
Videos move through 7 stages in order:

| Stage | Purpose |
|---|---|
| **Ideas** | Concept, target audience, unique angle, inspiration |
| **Planning** | Hook, script/outline, thumbnail concept, description, tags |
| **Filming** | Shot list, equipment, location notes, recording reminders, transitions |
| **Editing** | Edit notes, music/audio, graphics/overlays, color grade |
| **Posting** | Final title, description, tags, thumbnail sign-off, publish date, CTA |
| **Review** | All fields open and editable — full quality check before archiving |
| **Completed** | All fields visible, read-only — permanent archive of finished videos |

### Fling to advance
Drag a card left or right past the threshold to move it to the previous or next stage. A window shake and sound effect confirm the move. After flinging, the app automatically switches to the destination stage tab.

### Detail view
Click any card to open its detail view. Fields are organized by stage and auto-save as you type (800ms debounce — no Save button needed). Press **Escape** or **← Back** to return.

### Keyboard shortcuts
| Shortcut | Action |
|---|---|
| `Cmd + N` | New video |
| `Escape` | Close detail view / go back |

### Categories
Three content categories, color-coded on every card:
- **Arm Wrestling** — coral
- **Game Dev** — mint green
- **Misc** — sky blue

### Customizable checklist fields
Click **⚙** in the top bar to open Settings. You can:
- Add new fields with custom labels
- Choose field type: text, textarea, or checkbox
- Assign each field to a specific pipeline stage
- Toggle fields active/inactive without deleting them
- Reorder fields by dragging

### Progress rings
Each card shows a progress ring reflecting how many fields for that stage have been filled in. Review and Completed cards show overall completion across all pipeline stages.

### Data & persistence
- All data stored locally at `~/.content-helper/data.db` (SQLite)
- Window size and position remembered between launches (`~/.content-helper/prefs.json`)
- No account, no cloud, no telemetry

---

## File structure

```
content-helper/
├── main.py                  # Entry point
├── build_app.py             # Builds Content Helper.app
├── requirements.txt
└── app/
    ├── card.py              # VideoCard widget + fling animation
    ├── database.py          # SQLite persistence
    ├── detail_view.py       # Per-video checklist / detail view
    ├── models.py            # Video + ChecklistField dataclasses
    ├── new_video_dialog.py  # New Video modal
    ├── settings_dialog.py   # Checklist field editor
    ├── sounds.py            # Fling sound effect
    ├── stage_page.py        # Stage tab — card grid
    ├── theme.py             # Colors, fonts, global stylesheet
    └── window.py            # Main window, tabs, navigation
```

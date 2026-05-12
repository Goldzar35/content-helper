# Content Helper

A native Mac app for planning and tracking YouTube / Instagram video content. Built with Python + PyQt6.

## What it does

Videos move through a 5-stage production pipeline — Ideas → Planning → Filming → Editing → Posting — via a card-based Kanban UI. Each stage shows relevant checklist fields so you know exactly what needs to be done at each step. Once a video ships, fling it into Review (full edit) or Completed (read-only archive).

## Stages

| Stage | Purpose |
|---|---|
| Ideas | Concept, audience, angle, inspiration |
| Planning | Hook, script, thumbnail, description, tags |
| Filming | Shot list, equipment, location, reminders |
| Editing | Edit notes, music, graphics, color grade |
| Posting | Final title/description/tags, thumbnail, schedule, CTA |
| Review | All fields open and editable — final quality check |
| Completed | All fields visible, read-only — finished archive |

## Categories

- **Arm Wrestling** — sport / competition content
- **Game Dev** — devlog / game development content
- **Misc** — everything else

## Installation

### Option A — Download the app (easiest)

1. Go to the [Releases](../../releases) page and download `Content.Helper.app.zip`
2. Unzip and drag **Content Helper.app** to your Applications folder
3. First launch: **right-click → Open** (macOS will warn about an unverified developer — this is expected for unsigned apps. Click Open to proceed. You only need to do this once.)

### Option B — Run from source

Requires Python 3.10+.

```bash
# Clone the repo
git clone https://github.com/Goldzar35/content-helper.git
cd content-helper

# Install dependencies
pip install -r requirements.txt

# Run
python3 main.py
```

Data is stored at `~/.content-helper/data.db` (SQLite) — your videos persist between launches.

### Building the .app yourself

```bash
pip install pyinstaller pillow
python3 build_app.py
```

The app will be built at `dist/Content Helper.app`.

## Customizing checklist fields

Click the ⚙ gear icon in the top bar to open Settings. You can add, rename, reorder, toggle active/inactive, and assign fields to specific stages. Changes take effect immediately on all videos.

## Flinging cards

Drag a card left or right past the threshold to advance or retreat its stage. A window shake + sound confirms the move.

## File structure

```
content-helper/
├── main.py                  # Entry point
├── requirements.txt
├── app/
│   ├── card.py              # VideoCard widget + fling animation
│   ├── database.py          # SQLite persistence
│   ├── detail_view.py       # Per-video detail / checklist view
│   ├── models.py            # Video + ChecklistField dataclasses
│   ├── new_video_dialog.py  # "New Video" modal
│   ├── settings_dialog.py   # Checklist field editor
│   ├── sounds.py            # Fling sound (afplay)
│   ├── stage_page.py        # Stage tab grid view
│   ├── theme.py             # Colors, fonts, global QSS
│   └── window.py            # MainWindow + tab bar + stack
```

import sqlite3
import json
import uuid
import time
from pathlib import Path

from .models import Video, ChecklistField

DB_DIR  = Path.home() / ".content-helper"
DB_PATH = DB_DIR / "data.db"

# (id, label, field_type, required, order, stage)
DEFAULT_FIELDS = [
    # Ideas ── brainstorming
    ("concept",         "Concept / Idea",            "textarea", False,  0, "ideas"),
    ("target_audience", "Target Audience",            "text",     False,  1, "ideas"),
    ("video_angle",     "Unique Angle / Take",        "text",     False,  2, "ideas"),
    ("inspo",           "Inspiration / References",   "textarea", False,  3, "ideas"),

    # Planning ── pre-production
    ("hook",            "Hook / Opening Line",        "text",     False, 10, "planning"),
    ("script",          "Script / Outline",           "textarea", False, 11, "planning"),
    ("duration",        "Estimated Length",           "text",     False, 12, "planning"),
    ("thumbnail",       "Thumbnail Concept",          "text",     False, 13, "planning"),
    ("description",     "Description Draft",          "textarea", False, 14, "planning"),
    ("tags",            "Tags",                       "text",     False, 15, "planning"),

    # Filming ── production
    ("shot_list",       "Shot List",                  "textarea", False, 20, "filming"),
    ("equipment",       "Equipment / Setup",          "text",     False, 21, "filming"),
    ("location",        "Location / Setup Notes",     "text",     False, 22, "filming"),
    ("rec_reminders",   "Recording Reminders",        "textarea", False, 23, "filming"),
    ("transitions",     "Transitions to Capture",     "textarea", False, 24, "filming"),

    # Editing ── post-production
    ("edit_notes",      "Edit Notes",                 "textarea", False, 30, "editing"),
    ("music",           "Music / Audio",              "text",     False, 31, "editing"),
    ("graphics",        "Graphics / Text Overlays",   "textarea", False, 32, "editing"),
    ("color_grade",     "Color Grade / Look",         "text",     False, 33, "editing"),

    # Posting ── publishing
    ("final_title",     "Final Title",                "text",     False, 40, "posting"),
    ("final_desc",      "Final Description",          "textarea", False, 41, "posting"),
    ("final_tags",      "Final Tags",                 "text",     False, 42, "posting"),
    ("thumbnail_done",  "Thumbnail Finalized",        "checkbox", False, 43, "posting"),
    ("schedule_date",   "Schedule / Publish Date",    "text",     False, 44, "posting"),
    ("cta",             "CTA / End Screen",           "text",     False, 45, "posting"),
]

_DEFAULT_IDS = {row[0] for row in DEFAULT_FIELDS}


class Database:
    def __init__(self):
        DB_DIR.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                stage TEXT NOT NULL,
                checklist_values TEXT DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS checklist_fields (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                field_type TEXT NOT NULL DEFAULT 'text',
                required INTEGER DEFAULT 0,
                order_idx INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                stage TEXT DEFAULT NULL
            )
        """)

        # Migration: add stage column to older DBs — wipe all fields and reseed
        c.execute("PRAGMA table_info(checklist_fields)")
        cols = {row[1] for row in c.fetchall()}
        if "stage" not in cols:
            c.execute("ALTER TABLE checklist_fields ADD COLUMN stage TEXT DEFAULT NULL")
            c.execute("DELETE FROM checklist_fields")   # reseed with stage groupings
            self.conn.commit()

        # Seed defaults (INSERT OR IGNORE so user-added fields survive)
        for fid, label, ftype, req, order, stage in DEFAULT_FIELDS:
            c.execute(
                "INSERT OR IGNORE INTO checklist_fields VALUES (?,?,?,?,?,1,?)",
                (fid, label, ftype, int(req), order, stage),
            )
        self.conn.commit()

    # ── Fields ────────────────────────────────────────────────────────────────

    def get_fields_for_stage(self, stage: str) -> list:
        """Active fields belonging to a specific stage."""
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM checklist_fields WHERE stage=? AND active=1 ORDER BY order_idx",
            (stage,),
        )
        return [self._row_to_field(r) for r in c.fetchall()]

    def get_fields(self) -> list:
        """All active fields (for progress calculation)."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM checklist_fields WHERE active=1 ORDER BY order_idx")
        return [self._row_to_field(r) for r in c.fetchall()]

    def get_all_fields(self) -> list:
        """All fields including inactive (for settings)."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM checklist_fields ORDER BY stage, order_idx")
        return [self._row_to_field(r) for r in c.fetchall()]

    def save_fields(self, fields: list):
        c = self.conn.cursor()
        c.execute("DELETE FROM checklist_fields")
        for f in fields:
            c.execute(
                "INSERT INTO checklist_fields VALUES (?,?,?,?,?,?,?)",
                (f.id, f.label, f.field_type, int(f.required), f.order, int(f.active), f.stage),
            )
        self.conn.commit()

    def add_field(self, label: str, field_type: str, stage: str = None) -> ChecklistField:
        c = self.conn.cursor()
        c.execute("SELECT MAX(order_idx) FROM checklist_fields")
        max_order = (c.fetchone()[0] or 0) + 1
        fid = str(uuid.uuid4())[:8]
        f = ChecklistField(fid, label, field_type, False, max_order, True, stage)
        c.execute(
            "INSERT INTO checklist_fields VALUES (?,?,?,?,?,1,?)",
            (f.id, f.label, f.field_type, 0, f.order, f.stage),
        )
        self.conn.commit()
        return f

    # ── Videos ────────────────────────────────────────────────────────────────

    def get_videos_by_stage(self, stage: str) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM videos WHERE stage=? ORDER BY updated_at DESC", (stage,))
        return [self._row_to_video(r) for r in c.fetchall()]

    def get_video(self, vid: str):
        c = self.conn.cursor()
        c.execute("SELECT * FROM videos WHERE id=?", (vid,))
        row = c.fetchone()
        return self._row_to_video(row) if row else None

    def create_video(self, title: str, category: str) -> Video:
        v = Video(
            id=str(uuid.uuid4()),
            title=title,
            category=category,
            stage="ideas",
            checklist_values={},
            created_at=time.time(),
            updated_at=time.time(),
        )
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO videos VALUES (?,?,?,?,?,?,?)",
            (v.id, v.title, v.category, v.stage,
             json.dumps(v.checklist_values), v.created_at, v.updated_at),
        )
        self.conn.commit()
        return v

    def update_video(self, v: Video):
        v.updated_at = time.time()
        c = self.conn.cursor()
        c.execute(
            "UPDATE videos SET title=?,category=?,stage=?,checklist_values=?,updated_at=? WHERE id=?",
            (v.title, v.category, v.stage,
             json.dumps(v.checklist_values), v.updated_at, v.id),
        )
        self.conn.commit()

    def delete_video(self, vid: str):
        c = self.conn.cursor()
        c.execute("DELETE FROM videos WHERE id=?", (vid,))
        self.conn.commit()

    def advance_stage(self, vid: str):
        from .theme import STAGE_KEYS
        v = self.get_video(vid)
        if not v:
            return
        idx = STAGE_KEYS.index(v.stage)
        if idx < len(STAGE_KEYS) - 1:
            v.stage = STAGE_KEYS[idx + 1]
            self.update_video(v)

    def retreat_stage(self, vid: str):
        from .theme import STAGE_KEYS
        v = self.get_video(vid)
        if not v:
            return
        idx = STAGE_KEYS.index(v.stage)
        if idx > 0:
            v.stage = STAGE_KEYS[idx - 1]
            self.update_video(v)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _row_to_video(self, row) -> Video:
        return Video(
            id=row["id"], title=row["title"],
            category=row["category"], stage=row["stage"],
            checklist_values=json.loads(row["checklist_values"]),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def _row_to_field(self, row) -> ChecklistField:
        keys = row.keys()
        return ChecklistField(
            id=row["id"], label=row["label"],
            field_type=row["field_type"], required=bool(row["required"]),
            order=row["order_idx"], active=bool(row["active"]),
            stage=row["stage"] if "stage" in keys else None,
        )

    def close(self):
        self.conn.close()

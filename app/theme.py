STAGES = ["Ideas", "Planning", "Filming", "Editing", "Posting"]
STAGE_KEYS = ["ideas", "planning", "filming", "editing", "posting"]

CATEGORIES = ["Arm Wrestling", "Game Dev", "Misc"]
CATEGORY_KEYS = ["armwrestling", "gamedev", "misc"]
CATEGORY_DISPLAY = {
    "armwrestling": "Arm Wrestling",
    "gamedev": "Game Dev",
    "misc": "Misc",
}

BG_MAIN     = "#141414"
BG_ELEVATED = "#1e1e1e"
BG_CARD     = "#242424"
BG_CARD_HOVER = "#2c2c2c"
BG_INPUT    = "#1a1a1a"
BORDER      = "#333333"
BORDER_FOCUS = "#555555"

TEXT_PRIMARY   = "#f0f0f0"
TEXT_SECONDARY = "#888888"
TEXT_MUTED     = "#484848"

ACCENT = "#0d99ff"

STAGE_COLORS = {
    "ideas":    "#3b82f6",
    "planning": "#f59e0b",
    "filming":  "#ef4444",
    "editing":  "#a855f7",
    "posting":  "#10b981",
}

CATEGORY_COLORS = {
    "armwrestling": "#f97316",
    "gamedev":      "#a855f7",
    "misc":         "#22c55e",
}

FONT_FAMILY = "-apple-system, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial"

GLOBAL_QSS = f"""
* {{
    font-family: {FONT_FAMILY};
    color: {TEXT_PRIMARY};
}}

QMainWindow, QDialog {{
    background-color: {BG_MAIN};
}}

QWidget {{
    background-color: transparent;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {BG_ELEVATED};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #444;
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 0;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {BORDER_FOCUS};
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: #2a2a2a;
    border-color: {BORDER_FOCUS};
}}
QPushButton:pressed {{
    background-color: #222222;
}}

QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
}}

QCheckBox {{
    spacing: 8px;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid {BORDER_FOCUS};
    background: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: none;
}}

QComboBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {BORDER_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    selection-background-color: #333;
    color: {TEXT_PRIMARY};
    padding: 4px;
}}
"""

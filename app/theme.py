STAGES = ["Ideas", "Planning", "Filming", "Editing", "Posting", "Review", "Completed"]
STAGE_KEYS = ["ideas", "planning", "filming", "editing", "posting", "review", "completed"]

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

ACCENT      = "#d4a017"   # gold
ACCENT_TEXT = "#1a0e00"   # near-black for text on gold buttons

STAGE_COLORS = {
    "ideas":     "#f5e6a3",
    "planning":  "#e8c84a",
    "filming":   "#d4a017",
    "editing":   "#b8860b",
    "posting":   "#9a6e08",
    "review":    "#7a5206",
    "completed": "#5c3d04",
}

CATEGORY_COLORS = {
    "armwrestling": "#e07a6a",
    "gamedev":      "#6ac49a",
    "misc":         "#6aaee0",
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

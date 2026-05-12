from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QWidget,
)
from PyQt6.QtCore import Qt

from .theme import (
    BG_ELEVATED, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    CATEGORY_KEYS, CATEGORY_DISPLAY, ACCENT, ACCENT_TEXT,
)


class NewVideoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Video")
        self.setFixedSize(420, 260)
        self.setModal(True)
        self.setStyleSheet(
            f"QDialog {{ background:{BG_ELEVATED}; border:1px solid {BORDER}; border-radius:12px; }}"
        )
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        title_lbl = QLabel("New Video")
        title_lbl.setStyleSheet(
            f"font-size:17px; font-weight:700; color:{TEXT_PRIMARY}; background:transparent;"
        )
        lay.addWidget(title_lbl)

        # Title input
        name_lbl = QLabel("Title")
        name_lbl.setStyleSheet(
            f"font-size:11px; color:{TEXT_SECONDARY}; text-transform:uppercase; "
            "letter-spacing:0.8px; background:transparent;"
        )
        lay.addWidget(name_lbl)

        self._title = QLineEdit()
        self._title.setPlaceholderText("Give your video a working title…")
        self._title.setFixedHeight(38)
        lay.addWidget(self._title)

        # Category picker
        cat_lbl = QLabel("Category")
        cat_lbl.setStyleSheet(
            f"font-size:11px; color:{TEXT_SECONDARY}; text-transform:uppercase; "
            "letter-spacing:0.8px; background:transparent;"
        )
        lay.addWidget(cat_lbl)

        self._cat = QComboBox()
        for key in CATEGORY_KEYS:
            self._cat.addItem(CATEGORY_DISPLAY[key], key)
        lay.addWidget(self._cat)

        # Buttons
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(
            "background:#2a2a2a; color:#aaaaaa; border:1px solid #333;"
            "border-radius:6px; padding:8px 20px;"
        )
        cancel.clicked.connect(self.reject)

        create = QPushButton("Create →")
        create.setStyleSheet(
            f"background:{ACCENT}; color:{ACCENT_TEXT}; border:none; border-radius:6px;"
            "padding:8px 20px; font-weight:700;"
        )
        create.setCursor(Qt.CursorShape.PointingHandCursor)
        create.clicked.connect(self._on_create)

        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(create)
        lay.addLayout(btn_row)

        self._title.returnPressed.connect(self._on_create)

    def _on_create(self):
        if self._title.text().strip():
            self.accept()

    def get_values(self):
        return self._title.text().strip(), self._cat.currentData()

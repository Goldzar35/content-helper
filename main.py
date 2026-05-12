import sys
from PyQt6.QtWidgets import QApplication
from app.window import MainWindow
from app.theme import GLOBAL_QSS


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Content Helper")
    app.setOrganizationName("Goldzar")
    app.setStyleSheet(GLOBAL_QSS)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

import sys
from PyQt6.QtWidgets import QApplication
from app import MainWindow, DARK_STYLE


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Web to PDF")
    app.setStyleSheet(DARK_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

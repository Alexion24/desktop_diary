import sys

from PySide6.QtWidgets import QApplication, QMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Дневник")
    window.resize(640, 480)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

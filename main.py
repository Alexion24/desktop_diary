import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
)


class DiaryWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Дневник")
        self.resize(640, 480)

        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(self.windowTitle())

        self.reminder = QMessageBox(self)
        self.reminder.setWindowTitle("Напоминание")
        self.reminder.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.reminder.setIcon(QMessageBox.Icon.Information)
        self.reminder.setText("Пора заполнить дневник")
        self.reminder.setStandardButtons(QMessageBox.StandardButton.Close)
        self.reminder.button(QMessageBox.StandardButton.Close).setText("Закрыть")

        menu = QMenu(self)
        menu.addAction("Открыть дневник", self.open_window)
        menu.addAction("Проверить уведомление", self.show_reminder)
        menu.addAction("Выход", QApplication.quit)
        self.tray.setContextMenu(menu)
        QApplication.instance().aboutToQuit.connect(self.tray.hide)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.tray.isVisible() and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
        else:
            super().closeEvent(event)

    def open_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_reminder(self) -> None:
        self.reminder.showNormal()
        self.reminder.raise_()


def main() -> int:
    app = QApplication(sys.argv)
    window = DiaryWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

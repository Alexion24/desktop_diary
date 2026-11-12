import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from sqlite3 import Error as DatabaseError

from PySide6.QtCore import QSettings, QSignalBlocker, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from autostart import STARTUP_ARG, set_autostart
from entries import EntryStore
from entry_editor import EntryEditor
from monthly_report import render_month
from reminders import ReminderStore


class DiaryWindow(QMainWindow):
    def __init__(self, store: ReminderStore, *, allow_autostart: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("Дневник")
        self.resize(640, 480)
        self.store = store
        self.entries = EntryStore(store.path)
        self.minutes = set(store.load())
        self.last_checked = datetime.now().replace(second=0, microsecond=0)
        self.delivered: set[int] = set()

        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        self.schedule = QListWidget()
        self.schedule.setAccessibleName("Ежедневные напоминания")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setAccessibleName("Время напоминания")
        self.add_button = QPushButton("Добавить ежедневное напоминание")
        self.add_button.clicked.connect(self.add_reminder)
        self.remove_button = QPushButton("Удалить выбранное время")
        self.remove_button.clicked.connect(self.remove_reminder)
        self.schedule.currentItemChanged.connect(self.update_schedule_buttons)
        self.time_edit.timeChanged.connect(self.update_schedule_buttons)
        for widget in (
            self.schedule,
            self.time_edit,
            self.add_button,
            self.remove_button,
        ):
            layout.addWidget(widget)
        tabs = QTabWidget(self)
        calendar_panel = QWidget()
        calendar_layout = QVBoxLayout(calendar_panel)
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        open_entry = QPushButton("Открыть запись за выбранную дату")
        open_entry.clicked.connect(self.open_entry)
        self.calendar.activated.connect(self.open_entry)
        calendar_layout.addWidget(self.calendar)
        calendar_layout.addWidget(open_entry)
        export_report = QPushButton("Сохранить таблицу за открытый месяц")
        export_report.clicked.connect(self.export_month)
        calendar_layout.addWidget(export_report)
        tabs.addTab(calendar_panel, "Дневник")
        tabs.addTab(panel, "Напоминания")
        self.setCentralWidget(tabs)
        self.refresh_schedule()

        if sys.platform == "win32" and allow_autostart:
            self.settings = QSettings("DesktopDiary", "DesktopDiary")
            self.autostart_checkbox = QCheckBox("Запускать дневник при входе в Windows")
            layout.addWidget(self.autostart_checkbox)
            self.autostart_checkbox.setChecked(
                self.settings.value("autostart", False, type=bool)
            )
            self.autostart_checkbox.toggled.connect(self.change_autostart)

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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)

    def change_autostart(self, enabled: bool) -> None:
        try:
            set_autostart(enabled)
        except OSError:
            with QSignalBlocker(self.autostart_checkbox):
                self.autostart_checkbox.setChecked(
                    self.settings.value("autostart", False, type=bool)
                )
            QMessageBox.warning(
                self, "Автозапуск", "Не удалось изменить автозапуск в Windows."
            )
            return
        self.settings.setValue("autostart", enabled)
        self.settings.sync()
        with QSignalBlocker(self.autostart_checkbox):
            self.autostart_checkbox.setChecked(enabled)

    def open_entry(self) -> None:
        try:
            editor = EntryEditor(
                self.entries, self.calendar.selectedDate().toPython(), self
            )
        except DatabaseError:
            QMessageBox.warning(self, "Запись", "Не удалось загрузить запись.")
            return
        editor.exec()
        editor.deleteLater()

    def export_month(self) -> None:
        year, month = self.calendar.yearShown(), self.calendar.monthShown()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить таблицу за месяц",
            f"diary-{year:04d}-{month:02d}.html",
            "HTML (*.html)",
        )
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(".html")
        try:
            entries = self.entries.load_month(year, month)
            path.write_text(render_month(year, month, entries), encoding="utf-8")
        except (DatabaseError, OSError):
            QMessageBox.warning(self, "Отчёт", "Не удалось сохранить таблицу.")

    def selected_minute(self) -> int:
        time = self.time_edit.time()
        return time.hour() * 60 + time.minute()

    def update_schedule_buttons(self) -> None:
        self.add_button.setEnabled(self.selected_minute() not in self.minutes)
        self.remove_button.setEnabled(self.schedule.currentItem() is not None)

    def refresh_schedule(self) -> None:
        self.schedule.clear()
        for minute in sorted(self.minutes):
            hour, minute_of_hour = divmod(minute, 60)
            item = QListWidgetItem(f"{hour:02d}:{minute_of_hour:02d}")
            item.setData(Qt.ItemDataRole.UserRole, minute)
            self.schedule.addItem(item)
        self.update_schedule_buttons()

    def add_reminder(self) -> None:
        self.save_schedule(self.minutes | {self.selected_minute()})

    def remove_reminder(self) -> None:
        item = self.schedule.currentItem()
        if item is not None:
            self.save_schedule(self.minutes - {item.data(Qt.ItemDataRole.UserRole)})

    def save_schedule(self, minutes: set[int]) -> None:
        try:
            self.store.save(minutes)
        except DatabaseError:
            QMessageBox.warning(self, "Расписание", "Не удалось сохранить расписание.")
            return
        self.minutes = minutes
        self.refresh_schedule()

    def check_reminders(self) -> None:
        now = datetime.now().replace(second=0, microsecond=0)
        if now == self.last_checked:
            return
        if now.date() != self.last_checked.date():
            self.delivered.clear()
        self.last_checked = now
        minute = now.hour * 60 + now.minute
        if minute in self.minutes and minute not in self.delivered:
            self.delivered.add(minute)
            self.show_reminder()

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
    parser = ArgumentParser(add_help=False)
    parser.add_argument(STARTUP_ARG, action="store_true")
    parser.add_argument("--data-dir", type=Path)
    args, qt_args = parser.parse_known_args()
    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName("DesktopDiary")
    data_dir = args.data_dir or Path(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
    )
    try:
        window = DiaryWindow(
            ReminderStore(data_dir / "diary.sqlite3"),
            allow_autostart=args.data_dir is None,
        )
    except (DatabaseError, OSError):
        QMessageBox.critical(
            None, "Дневник", "Не удалось открыть локальную базу данных."
        )
        return 1
    if sys.platform == "win32" and not args.autostart and args.data_dir is None:
        if not window.settings.contains("autostart") or (
            getattr(sys, "frozen", False) and window.autostart_checkbox.isChecked()
        ):
            window.change_autostart(True)
    if not args.autostart or not window.tray.isVisible():
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

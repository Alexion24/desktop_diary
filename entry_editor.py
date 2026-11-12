from datetime import date
from sqlite3 import Error as DatabaseError

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QPlainTextEdit,
    QWidget,
)

from entries import Entry, EntryStore


class EntryEditor(QDialog):
    def __init__(self, store: EntryStore, day: date, parent: QWidget) -> None:
        super().__init__(parent)
        self.store = store
        self.day = day
        self.setWindowTitle(f"Запись за {day:%d.%m.%Y}")
        self.resize(480, 420)
        entry = store.load(day)

        layout = QFormLayout(self)
        self.feelings = QPlainTextEdit(entry.feelings)
        self.methods = QPlainTextEdit(entry.methods)
        self.notes = QPlainTextEdit(entry.notes)
        layout.addRow("Ощущения", self.feelings)
        layout.addRow("Методы", self.methods)
        layout.addRow("Заметки", self.notes)

        save = QDialogButtonBox.StandardButton.Save
        cancel = QDialogButtonBox.StandardButton.Cancel
        buttons = QDialogButtonBox(save | cancel)
        buttons.button(save).setText("Сохранить")
        buttons.button(cancel).setText("Отмена")
        buttons.accepted.connect(self.save_entry)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save_entry(self) -> None:
        entry = Entry(
            feelings=self.feelings.toPlainText().strip(),
            methods=self.methods.toPlainText().strip(),
            notes=self.notes.toPlainText().strip(),
        )
        if not any((entry.feelings, entry.methods, entry.notes)):
            QMessageBox.information(self, "Запись", "Заполните хотя бы одно поле.")
            return
        try:
            self.store.save(self.day, entry)
        except DatabaseError:
            QMessageBox.warning(self, "Запись", "Не удалось сохранить запись.")
            return
        self.accept()

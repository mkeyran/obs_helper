#!/usr/bin/env python3
import argparse
import sys

from PySide6.QtCore import QSharedMemory, Qt, QObject, Signal, Slot, SLOT
from PySide6.QtGui import QTextCursor

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMenu,
    QSystemTrayIcon,
)
from PySide6.QtGui import QIcon
from PySide6.QtDBus import QDBusConnection, QDBusInterface
from config import config, dbus_serice_name
from functions import functions
import sqlite3

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, required=False)
    return parser.parse_args()


class MainWindow(QMainWindow):

    # Signal to be emitted when the hotkey is pressed
    hotkey_pressed = Signal(str)

    def __init__(self, action = None):
        super().__init__()
        if (self.single_check()) is False:
            print("Another instance is already running")
            self.close()
        self.setWindowRole("ObsidianHelper")
        self.setMinimumSize(1024, 768)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.action = action
        
        self.bus = QDBusConnection.sessionBus()
        self.bus.registerObject("/", self, QDBusConnection.ExportAllSlots)
        self.bus.registerService(dbus_serice_name)

        # Open or create a sqlit db with a table cursors, which contains the cursor position of each note
        self.conn = sqlite3.connect('cursors.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS cursors (note TEXT PRIMARY KEY, cursor INTEGER)''')
        self.conn.commit()

        self.setGeometry(0, 0, 1024, 768)
        self.text_field = QTextEdit(self)
        self.button = QPushButton(action, self)
        self.button.clicked.connect(self.on_button_clicked)
        layout = QVBoxLayout()
        layout.addWidget(self.text_field)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.init_tray_icon()
        self.hotkey_pressed.connect(self.on_tray_action)
        if action is not None:
            try:
                self.function = functions[action](self.text_field)
                self.restore_cursor(action)
                self.show()
            except KeyError:
                raise ValueError(f"Invalid action: {action}")
    
    @Slot(str)
    def runFunction(self, action):
        print(action)
        try:
            self.on_tray_action(action)
        except Exception as e:
            print(e)

    def restore_cursor(self, note):
        self.c.execute('SELECT cursor FROM cursors WHERE note = ?', (note,))
        cursor = self.c.fetchone()
        if cursor is not None:
            print(cursor[0])
            temp_cursor = self.text_field.textCursor()
            temp_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, cursor[0])
            self.text_field.setTextCursor(temp_cursor)

    def save_cursor(self, note):
        cursor = self.text_field.textCursor().position()
        self.c.execute('INSERT OR REPLACE INTO cursors VALUES (?, ?)', (note, cursor))
        self.conn.commit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.on_button_clicked()

    def on_button_clicked(self):
        text = self.text_field.toPlainText()
        self.save_cursor(self.action)
        self.function.run(text)
        self.close()

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("document-open"))
        tray_menu = QMenu()
        for action in functions.keys():
            print(action)
            fun = lambda _, arg = action: self.on_tray_action(arg)
            tray_menu.addAction(action).triggered.connect(fun)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def on_tray_action(self, action):
        print("Tray action:", action)
        self.text_field.setPlainText("")
        self.button.setText(action)
        self.function = functions[action](self.text_field)
        self.action = action
        self.function.update()
        self.restore_cursor(action)
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


    def single_check(self):
        shared_memory = QSharedMemory("ObsidianHelper")
        shared_memory.setKey("ObsidianHelper")
        if shared_memory.create(1) is False:
            return False
        return True


def main():
    args = parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("ObsidianHelper")

    window = MainWindow(args.action)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

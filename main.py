#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QSharedMemory, Qt, QObject, Signal
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
from datetime import datetime
from PyHotKey import Key, keyboard_manager as manager

import toml

# Load configuration from TOML file
config_path = Path(__file__).parent / "config.toml"
config = toml.load(str(config_path))

class Function:
    def __init__(self, ui):
        self._ui: QTextEdit = ui

    def run(self, *args):
        raise NotImplementedError


class Journal(Function):
    def __init__(self, ui):
        super().__init__(ui)
        self.journal_path = Path(config["obsidian_path"])/config["journal_folder"]
        self.template_path = Path(config["obsidian_path"])/config["journal_template"]
        print (self.template_path)
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_path = self.journal_path / f"{today}.md"

        if not self.file_path.exists():
            self.create_from_template()
        self.load_note()

    def create_from_template(self):
        if self.template_path.exists():
            with open(self.template_path, "r") as template_file:
                content = template_file.read()
            with open(self.file_path, "w") as new_file:
                new_file.write(content)
        else:
            with open(self.file_path, "w") as new_file:
                new_file.write("# " + datetime.now().strftime("%Y-%m-%d") + "")

    def load_note(self):
        with open(self.file_path, "r") as file:
            self.text = file.read()
        self._ui.setText(self.text)
        self._ui.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

    def run(self, text):
        with open(self.file_path, "w") as file:
            file.write(text)


class Scratchpad(Function):
    def __init__(self, ui):
        super().__init__(ui)
        try:
            with open(Path(config["obsidian_path"]) / config["scratchpad_name"], "r") as f:
                self.text = f.read()
        except FileNotFoundError:
            self.text = ""
        self._ui.setText(self.text)
        self._ui.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
    
    def run(self, text):
        with open(Path(config["obsidian_path"]) / config["scratchpad_name"], "w") as f:
            f.write(text)

class DistractionList(Function):
    def __init__(self, ui):
        super().__init__(ui)

    def run(self, text):
        with open(Path(config["obsidian_path"]) / config["distraction_list_name"], "a") as f:
            f.write("- " + text + "\n")


functions = {
    "scratchpad": Scratchpad,
    "distraction_list": DistractionList,
    "journal": Journal,

}


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
        self.setGeometry(0, 0, 1024, 768)
        self.text_field = QTextEdit(self)
        self.button = QPushButton(action, self)
        self.button.clicked.connect(self.on_button_clicked)
        id = manager.register_hotkey([Key.cmd, Key.alt_l, 'z'], None,
                              lambda: print("test"))
        print(id)
        layout = QVBoxLayout()
        layout.addWidget(self.text_field)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.init_tray_icon()
        self.registerGlobalHotkeys()
        self.hotkey_pressed.connect(self.on_tray_action)
        if action is not None:
            try:
                self.function = functions[action](self.text_field)
                self.show()
            except KeyError:
                raise ValueError(f"Invalid action: {action}")
    
    def _parse_shortcut(self, shortcut):
        """Parse something like Meta+Control+z and return a manager-compatible list"""
        keys = shortcut.split("+")
        lst = []
        for key in keys:
            if key == "Meta":
                lst.append(Key.cmd)
            elif key == "Control":
                lst.append(Key.ctrl)
            elif key == "Alt":
                lst.append(Key.alt_l)
            else:
                lst.append(key)
        return lst

    def print_action(self, action):
        self.hotkey_pressed.emit(action)
        

    def registerGlobalHotkeys(self):
        for action in functions.keys():ddd
            if config["shortcuts"][action] is not None:
                ret = manager.register_hotkey(self._parse_shortcut(config["shortcuts"][action]), None, 
                                        lambda action = action: self.print_action(action))
                print(ret)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.on_button_clicked()

    def on_button_clicked(self):
        text = self.text_field.toPlainText()
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

#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QSharedMemory, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import toml

# Load configuration from TOML file
config_path = Path(__file__).parent / "config.toml"
config = toml.load(str(config_path))

class Function:
    def __init__(self, ui):
        self._ui: QTextEdit = ui

    def run(self, *args):
        raise NotImplementedError

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
        with open(config["obsidian_path"] / config["scrathpad_name"], "w") as f:
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
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, required=True)
    return parser.parse_args()


class MainWindow(QMainWindow):
    def __init__(self, action):
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
        # add keyboard shortcut Ctrl+Enter to the button
        self.button.setShortcut("Ctrl+Return")
        # add keyboard shortcut Esc to quit the application

        try:
            self.function = functions[action](self.text_field)
        except KeyError:
            raise ValueError(f"Invalid action: {action}")
            QApplication.quit()
        layout = QVBoxLayout()
        layout.addWidget(self.text_field)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def on_button_clicked(self):
        text = self.text_field.toPlainText()
        self.function.run(text)
        self.close()

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
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

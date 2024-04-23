from pathlib import Path
from PySide6.QtWidgets import (
    QTextEdit
    )
from PySide6.QtGui import QTextCursor

from config import config
from datetime import datetime

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

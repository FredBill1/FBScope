from .FBWidget import FBWidget
from tkinter import ttk
import tkinter as tk


class FBButton(FBWidget):
    def construct(self, frame: ttk.Frame) -> None:
        self.button = ttk.Button(frame, text=self.name, command=lambda: (frame.focus_set(), self._callback("click")))
        self.button.pack(fill="both", expand=True)

    def applyConfig(self):
        self.frame.pack_propagate(False)
        self.frame["width"] = int(self.config.setdefault("宽度", "100"))
        self.frame["height"] = int(self.config.setdefault("高度", "30"))

    def rename(self):
        super().rename()
        self.button["text"] = self.name

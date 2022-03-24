from .FBWidget import FBWidget
import ttkbootstrap as ttk
import tkinter as tk
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from utils import ValEntry


class FBFloatEntry(FBWidget):
    def construct(self, frame: ttk.Frame) -> None:
        self.data.setdefault("text", tk.StringVar(value="0.0"))
        self.label = ttk.Label(frame, text=self.name)
        self.entry = ValEntry(ValEntry.type_validator(float), frame, textvariable=self.data["text"])
        self.entry.bind("<Return>", lambda _: self._callback("enter"))
        self.label.pack(side="left")
        self.entry.pack(side="left")

    def applyConfig(self):
        self.entry["width"] = int(self.config.setdefault("宽度", "20"))

    def rename(self, newName: str) -> None:
        self.label["text"] = newName


__all__ = ["FBFloatEntry"]

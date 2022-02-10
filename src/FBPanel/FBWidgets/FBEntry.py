from .FBWidget import FBWidget
from tkinter import ttk
import tkinter as tk


class FBEntry(FBWidget):
    def construct(self, frame: ttk.Frame) -> None:
        self.data.setdefault("text", tk.StringVar())
        self.label = ttk.Label(frame, text=self.name)
        self.entry = ttk.Entry(frame, textvariable=self.data["text"])
        self.entry.bind("<Return>", lambda _: self._callback("enter"))
        self.label.pack(side="left")
        self.entry.pack(side="left")

    def applyConfig(self):
        self.entry["width"] = int(self.config.setdefault("宽度", "20"))

    def rename(self):
        super().rename()
        self.label["text"] = self.name

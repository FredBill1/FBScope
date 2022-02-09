from .FBWidget import FBWidget
from tkinter import ttk


class FBButton(FBWidget):
    def construct(self, frame: ttk.LabelFrame) -> None:
        self.button = ttk.Button(frame, text=self.name, command=lambda: (frame.focus_set(), self._callback("click")))
        self.button.pack(fill="both", expand=True)

    def rename(self):
        super().rename()
        self.button["text"] = self.name

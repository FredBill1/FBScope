from .FBWidget import FBWidget
import ttkbootstrap as ttk
import tkinter as tk


class FBToggle(FBWidget):
    def construct(self, frame: ttk.Frame) -> None:
        self.button = ttk.Checkbutton(
            frame, text=self.name, bootstyle=("success", "outline", "toolbutton"), command=self._toggle
        )
        self.button.pack(fill="both", expand=True)

    def _toggle(self, *_):
        if self.button.instate(["selected"]):
            self._callback("on")
            self._callback("period")
        else:
            self._callback("off")

    def checkPeriod(self) -> bool:
        return self.button.instate(["selected"])

    def applyConfig(self):
        self.frame.pack_propagate(False)
        self.frame["width"] = int(self.config.setdefault("宽度", "100"))
        self.frame["height"] = int(self.config.setdefault("高度", "30"))

    def rename(self):
        super().rename()
        self.button["text"] = self.name


__all__ = ["FBToggle"]

from .FBWidget import FBWidget
import ttkbootstrap as ttk
import tkinter as tk
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from utils import ValEntry


class FBScaleEntry(FBWidget):
    def constructWithBorder(self, frame: ttk.Frame) -> None:
        self.data.setdefault("text", tk.StringVar(value="0.0"))

        topFrame = ttk.Frame(frame)
        self.label = ttk.Label(topFrame, text=self.name)
        self.entry = ValEntry(ValEntry.type_validator(float), topFrame, textvariable=self.data["text"])

        self.scale = ttk.Scale(frame, orient="horizontal", from_=0, to=100, command=self._onScaleChange)

        rangeFrame = ttk.Frame(frame)
        self.lowLabel = ttk.Label(rangeFrame)
        self.highLabel = ttk.Label(rangeFrame)

        self.entry.bind("<Return>", lambda _: self._callback("enter"))
        self.entry.bindUpdate(self._calcScale)
        self.scale.bind("<ButtonRelease-1>", lambda _: self._callback("release"))

        topFrame.pack()
        self.label.pack(side="left")
        self.entry.pack(side="left")

        self.scale.pack(fill="x", expand=True)

        rangeFrame.pack(fill="x", expand=True)
        self.lowLabel.pack(side="left")
        self.highLabel.pack(side="right")

    def _calcScale(self, *_):
        value = float(self.entry.get())
        self.scale.configure(value=max(0, min(100, (value - self.low) / (self.high - self.low) * 100)))

    def _onScaleChange(self, scale):
        scale = round(float(scale))
        value = f"%.{self.displayPrecision}f" % (self.low + (self.high - self.low) * scale / 100)
        if value != self.entry.get():
            self.entry.set(value)
            self._callback("change")

    def applyConfig(self):
        self.entry["width"] = int(self.config.setdefault("宽度", "20"))
        self.low = float(self.config.setdefault("最小值", "0.0"))
        self.high = float(self.config.setdefault("最大值", "100.0"))
        self.displayPrecision = int(self.config.setdefault("显示精度", "2"))
        self.lowLabel["text"] = self.config["最小值"]
        self.highLabel["text"] = self.config["最大值"]
        self._calcScale()

    def rename(self):
        super().rename()
        self.label["text"] = self.name


__all__ = ["FBScaleEntry"]

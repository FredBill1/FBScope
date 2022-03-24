import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import List
import threading
from collections import deque

import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils import ValEntry


class FBPlotFrame(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)

        self._fig = plt.Figure()

        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="wesn")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._ax = self._fig.add_subplot(1, 1, 1)

        self._dataLock = threading.Lock()
        self._updateFlag = False

        self.samplecnt = 1000
        self.datacnt = 2

        self._opFrame = ttk.Frame(self)
        self._opFrame.grid(row=1, column=0, sticky="we")

        self._autoscaleCheckButton = ttk.Checkbutton(
            self._opFrame, text="自动缩放", bootstyle=("success", "round", "toggle"), command=self._toggleAutoscaleCB
        )
        self._autoscaleCheckButton.state(["selected"])
        self._autoscaleCheckButton.pack(side="left", padx=5, pady=5)

        self._ylowEntry = ValEntry(ValEntry.type_validator(float), self._opFrame, text="-1.0", width=7)
        self._yhighEntry = ValEntry(ValEntry.type_validator(float), self._opFrame, text="1.0", width=7)
        self._applyYButton = ttk.Button(self._opFrame, text="应用", command=self._fixedscale)

        for entry in (self._ylowEntry, self._yhighEntry):
            entry.bind("<Return>", self._fixedscale)

        ttk.Label(self._opFrame, text="y轴范围: 下限").pack(side="left", padx=5, pady=5)
        self._ylowEntry.pack(side="left", padx=5, pady=5)
        ttk.Label(self._opFrame, text="上限").pack(side="left", padx=5, pady=5)
        self._yhighEntry.pack(side="left", padx=5, pady=5)
        self._applyYButton.pack(side="left", padx=5, pady=5)

        self._pauseButton = ttk.Checkbutton(self._opFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))
        self._pauseButton.pack(side="left", padx=5, pady=5)

        # self.applyDataConfig()

        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=100, blit=True)

    def applyDataConfig(self):
        with self._dataLock:
            self._ax.cla()
            self._initPlot()
            self._ax.grid(True)
            self._ax.set_xlim(0, self.samplecnt)
        self._toggleAutoscaleCB()

    def _initPlot(self):
        self._x = np.arange(self.samplecnt)
        self._y = [deque([0.0] * self.samplecnt, self.samplecnt) for _ in range(self.datacnt)]
        self._lines: List[plt.Line2D] = [l for i in range(self.datacnt) for l in self._ax.plot(self._x, self._y[i])]
        self._visible = [False] * self.datacnt
        for line in self._lines:
            line.remove()
        self._updateFlag = False

    def setVisible(self, idx: int, visible: bool):
        if self._visible[idx] == visible:
            return
        self._visible[idx] = visible
        if visible:
            self._ax.add_line(self._lines[idx])
        else:
            self._lines[idx].remove()
        if self._autoscaleCheckButton.instate(["selected"]):
            self._autoscale()

    def updateData(self, data: List[float]):
        if self._pauseButton.instate(["selected"]):
            return
        with self._dataLock:
            for y, v in zip(self._y, data):
                y.append(v)
            self._updateFlag = True

    def _toggleAutoscaleCB(self, *_):
        if self._autoscaleCheckButton.instate(["selected"]):
            self._ylowEntry.state(["disabled"])
            self._yhighEntry.state(["disabled"])
            self._applyYButton.state(["disabled"])
            self._autoscale()
        else:
            self._ylowEntry.state(["!disabled"])
            self._yhighEntry.state(["!disabled"])
            self._applyYButton.state(["!disabled"])
            self._fixedscale()

    def _fixedscale(self, *_):
        low, high = float(self._ylowEntry.get()), float(self._yhighEntry.get())
        self._ax.set_ylim((min(low, high), max(low, high)))

    def _autoscale(self, *_):
        self._ylowEntry.state(["disabled"])
        self._yhighEntry.state(["disabled"])
        self._doAutoScale()

    def _doAutoScale(self):
        self._ax.set_autoscaley_on(True)
        self._ax.relim(visible_only=True)
        self._ax.autoscale_view(scalex=False, scaley=True)
        self._ylowEntry.set("{:.2f}".format(self._ax.get_ylim()[0]))
        self._yhighEntry.set("{:.2f}".format(self._ax.get_ylim()[1]))

    def _updatePlot(self, *_):
        with self._dataLock:
            if not self._updateFlag:
                return []
            self._updateFlag = False
            for i, (vis, line) in enumerate(zip(self._visible, self._lines)):
                if vis:
                    line.set_ydata(np.array(self._y[i], copy=True))
            if self._autoscaleCheckButton.instate(["selected"]):
                self._doAutoScale()
            return (line for vis, line in zip(self._visible, self._lines) if vis)


if __name__ == "__main__":

    from FBSocket import FBServer
    from FBRecv import FBFloatRecv

    root = tk.Tk()
    frame = FBPlotFrame(root)
    frame.pack(fill="both", expand=True)
    frame.applyDataConfig()

    server = FBServer()
    recv = FBFloatRecv()
    server.registerRecvCallback(recv.input)
    recv.registerRecvCallback(frame.updateData)

    recv.setConfig(cnt=2)
    recv.start()
    server.start()

    root.mainloop()

    server.shutdown()
    recv.shutdown()

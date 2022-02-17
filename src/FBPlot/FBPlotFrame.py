import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import List
import threading

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
            self._opFrame, text="自动缩放", bootstyle=("success", "round", "toggle"), command=self._autoscale
        )
        self._autoscaleCheckButton.state(["selected"])
        self._autoscaleCheckButton.pack(side="left", padx=5, pady=5)

        def _valFloat(s: str) -> bool:
            try:
                float(s)
                return True
            except ValueError:
                return False

        self._ylowEntry = ValEntry(_valFloat, self._opFrame, text="-1.0", width=7)
        self._yhighEntry = ValEntry(_valFloat, self._opFrame, text="1.0", width=7)
        for entry in (self._ylowEntry, self._yhighEntry):
            entry.bind("<Return>", self._autoscale)
        ttk.Label(self._opFrame, text="y轴范围: 下限").pack(side="left", padx=5, pady=5)
        self._ylowEntry.pack(side="left", padx=5, pady=5)
        ttk.Label(self._opFrame, text="上限").pack(side="left", padx=5, pady=5)
        self._yhighEntry.pack(side="left", padx=5, pady=5)

        self.applyDataConfig()

        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=100, blit=False)

    def applyDataConfig(self):
        with self._dataLock:
            self._ax.cla()
            self._initPlot()
            self._ax.grid(True)
            self._ax.set_xlim(0, self.samplecnt)
        self._autoscale()

    def _initPlot(self):
        self._x = np.arange(self.samplecnt)
        self._y = np.zeros((self.samplecnt, self.datacnt), dtype=np.float32)
        self._lines: List[plt.Line2D] = self._ax.plot(self._x, self._y)
        self._updateFlag = False

    def updateData(self, data: List[float]):
        with self._dataLock:
            self._y = np.roll(self._y, -1, 0)
            self._y[-1, :] = data
            self._updateFlag = True

    def _autoscale(self, *_):
        if self._autoscaleCheckButton.instate(["selected"]):
            self._ylowEntry.state(["disabled"])
            self._yhighEntry.state(["disabled"])
            self._ax.set_autoscaley_on(True)
            self._ax.relim(visible_only=True)
            self._ax.autoscale_view(scalex=False, scaley=True)
            self._ylowEntry.set("{:.2f}".format(self._ax.get_ylim()[0]))
            self._yhighEntry.set("{:.2f}".format(self._ax.get_ylim()[1]))
        else:
            self._ylowEntry.state(["!disabled"])
            self._yhighEntry.state(["!disabled"])
            low, high = float(self._ylowEntry.get()), float(self._yhighEntry.get())
            self._ax.set_ylim((min(low, high), max(low, high)))

    def _updatePlot(self, *_):
        with self._dataLock:
            if self._updateFlag:
                self._updateFlag = False
                for i, line in enumerate(self._lines):
                    line.set_ydata(self._y[:, i])
                self._autoscale()


if __name__ == "__main__":

    from FBSocket import FBServer
    from FBFloatRecv import FBFloatRecv

    root = tk.Tk()
    frame = FBPlotFrame(root)
    frame.pack(fill="both", expand=True)

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
import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
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
    def __init__(self, root=None, **kw):
        super().__init__(root._root if root is not None else None, **kw)
        self.root = root

        self._fig = plt.Figure()
        self._fig.subplots_adjust(top=0.95, bottom=0.05, left=0.072, right=0.97, wspace=0, hspace=0)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="wesn")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.drag_pan = self._drag_pan

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

        self._resetXlimButton = ttk.Button(self._opFrame, text="重置X轴", command=self._resetXlim)
        self._resetXlimButton.pack(side="left", padx=5, pady=5)

        self._pauseButton = ttk.Checkbutton(self._opFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))
        self._pauseButton.pack(side="left", padx=5, pady=5)

        self._toolbar = NavigationToolbar2Tk(self._canvas, self._opFrame, pack_toolbar=False)
        self._toolbar.update()
        self._toolbar.pan()

        # self.applyDataConfig()

        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=100, blit=True)

    def _drag_pan(self, button, key, x, y):
        points = self._ax._get_pan_points(button, key, x, y)
        if points is not None:
            self._autoscaleCheckButton.state(["!selected"])
            xlim = points[:, 0]
            if button == 1:
                if xlim[0] < 0:
                    xlim[1] -= xlim[0]
                    xlim[0] = 0
                elif xlim[1] > self.samplecnt:
                    xlim[0] -= xlim[1] - self.samplecnt
                    xlim[1] = self.samplecnt
            else:
                xlim = [max(0, xlim[0]), min(self.samplecnt, xlim[1])]
            self._ax.set_xlim(xlim)
            self._ax.set_ylim(points[:, 1])

    def _resetXlim(self):
        self._ax.set_xlim(0, self.samplecnt)

    def applyDataConfig(self):
        with self._dataLock:
            self._ax.cla()
            self._initPlot()
            self._ax.grid(True)
            self._resetXlim()
        self._toggleAutoscaleCB()

    def _initPlot(self):
        self._x = np.arange(self.samplecnt)
        self._x[-1] = self.samplecnt
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
            self._autoscale()

    def _autoscale(self):
        self._ax.set_autoscaley_on(True)
        self._ax.relim(visible_only=True)
        self._ax.autoscale_view(scalex=False, scaley=True)

    def _updatePlot(self, *_):
        with self._dataLock:
            if not self._updateFlag:
                return []
            self._updateFlag = False
            for i, (vis, line) in enumerate(zip(self._visible, self._lines)):
                if vis:
                    line.set_ydata(np.array(self._y[i], copy=True))
            if self._autoscaleCheckButton.instate(["selected"]):
                self._autoscale()
            self.root.setVar([self._y[i][-1] for i in range(self.datacnt)])
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

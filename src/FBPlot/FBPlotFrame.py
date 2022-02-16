import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import List
import threading


class FBPlotFrame(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)

        self._fig = plt.Figure()

        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._ax = self._fig.add_subplot(1, 1, 1)

        self._dataLock = threading.Lock()
        self._updateFlag = False

        self.samplecnt = 1000
        self.datacnt = 2

        self.applyDataConfig()

        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=100, blit=False)

    def applyDataConfig(self):
        with self._dataLock:
            self._ax.cla()
            self._initPlot()
            self._ax.grid(True)
            self._ax.set_xlim(0, self.samplecnt)

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

    def _updatePlot(self, *_):
        with self._dataLock:
            if self._updateFlag:
                self._updateFlag = False
                for i, line in enumerate(self._lines):
                    line.set_ydata(self._y[:, i])
                self._ax.relim(visible_only=True)
                self._ax.autoscale_view(scalex=False, scaley=True)


if __name__ == "__main__":
    import os.path, sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
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

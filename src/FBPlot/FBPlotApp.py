import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.colors as mcolors
import itertools

import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from FBPlotFrame import FBPlotFrame
from FBFloatRecv import FBFloatRecvGUI
from FBSocket import FBClient, FBServer
from utils import ValEntry


class _RecvGUI(FBFloatRecvGUI):
    def extraBody(self, master: ttk.Frame) -> ttk.Frame:
        res = ttk.Frame(master)
        res.columnconfigure(1, weight=1)
        ttk.Label(res, text="采样").grid(row=0, column=0, sticky="w")
        self._sampleCntEntry = ValEntry(lambda s: s.isdigit() and int(s) > 0, res, width=5, text="1000")
        self._sampleCntEntry.grid(row=0, column=1, sticky="we")
        return res

    def getSampleCnt(self):
        return int(self._sampleCntEntry.get())


class FBPlotApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(1, weight=1)

        self._panel = ttk.Frame(self._root)
        self._panel.grid(row=0, column=0, sticky="nswe")
        self._panel.rowconfigure(1, weight=1)
        recvlf = ttk.LabelFrame(self._panel, text="接收器")
        recvlf.grid(row=0, column=0)
        self._recvGUI = _RecvGUI(recvlf)
        self._recvGUI.pack(padx=5, pady=5)

        self._plotFrame = FBPlotFrame(self._root)
        self._plotFrame.grid(row=0, column=1, sticky="nswe")

        self._client = FBServer() if isServer else FBClient()
        self._client.registerRecvCallback(self._recvGUI.input)
        self._recvGUI.registerRecvCallback(self._plotFrame.updateData)
        self._recvGUI.registerClickCallback(self._setDataCnt)

        self._visibleFrame: ttk.Frame = None

        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def _setDataCnt(self):
        self._buildVisibleFrame()
        self._plotFrame.datacnt = self._recvGUI.getCnt()
        self._plotFrame.samplecnt = self._recvGUI.getSampleCnt()
        self._plotFrame.applyDataConfig()

    def _buildVisibleFrame(self):
        if self._visibleFrame is not None:
            self._visibleFrame.destroy()
        self._visibleFrame = ttk.LabelFrame(self._panel, text="可视化")
        self._visibleFrame.grid(row=1, column=0, sticky="nswe")
        self._visibleFrame.grid_propagate(False)
        self._visibleToggle = [
            ttk.Checkbutton(
                self._visibleFrame,
                text="{:>2d}".format(i + 1),
                bootstyle=("success", "round", "toggle"),
                command=lambda i=i: self._plotFrame.setVisible(i, self._visibleToggle[i].instate(["selected"])),
            )
            for i in range(self._recvGUI.getCnt())
        ]
        for i, (toggle, color) in enumerate(zip(self._visibleToggle, itertools.cycle(mcolors.TABLEAU_COLORS.values()))):
            c = tk.Canvas(self._visibleFrame, width=10, height=10)
            c.config(bg=color)
            c.grid(row=i, column=0, sticky="w")
            toggle.grid(row=i, column=1, sticky="w")

    def mainloop(self):
        self._client.start()
        self._recvGUI.start()
        self._setDataCnt()
        self._root.mainloop()

    def shutdown(self):
        self._recvGUI.shutdown()
        self._client.shutdown()
        self._root.destroy()


__all__ = ["FBPlotApp"]

if __name__ == "__main__":
    app = FBPlotApp(True)
    app.mainloop()

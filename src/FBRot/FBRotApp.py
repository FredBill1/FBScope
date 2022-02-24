import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import threading
import numpy as np
from math import sin, cos
from typing import List, Callable
from scipy.spatial.transform import Rotation as R

import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from FBSocket import FBClient, FBServer
from FBRecv import FBFloatRecvGUI
from utils import ValEntry


class FBRotApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBRot")
        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(0, weight=1)
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self._root.geometry("608x588+150+150")

        self._drawLock = threading.Lock()
        self._dataLock = threading.Lock()
        self._updateFlag = False

        self._init_fig()

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._root)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="wesn")

        opFrame = ttk.Frame(self._root)
        opFrame.grid(row=1, column=0, sticky="we")
        opFrame.columnconfigure(0, weight=1)

        recvFrame = ttk.Frame(opFrame)
        recvFrame.grid(row=0, column=0, sticky="we")

        ttk.Label(recvFrame, text="接收器:").pack(side="left")
        self._recvGUI = FBFloatRecvGUI(recvFrame, is_vertical=False)
        self._recvGUI.pack(side="left", padx=5, pady=5)

        self._client = FBServer() if isServer else FBClient()
        self._client.registerRecvCallback(self._recvGUI.input)
        self._recvGUI.registerRecvCallback(self.updateData)

        ttk.Label(recvFrame, text="坐标范围:").pack(side="left")
        self._limEntry = ValEntry(
            lambda s: ValEntry.type_validator(float)(s) and float(s) > 0, recvFrame, text="5.0", width=5
        )
        self._limEntry.pack(side="left", padx=5, pady=5)
        self._limEntry.bind("<Return>", self._init_ax)
        ttk.Button(recvFrame, text="应用", command=self._init_ax).pack(side="left", padx=5, pady=5)

        dataFrame = ttk.Frame(opFrame)
        dataFrame.grid(row=1, column=0, sticky="we")

        self.modes = ["三维向量", "欧拉角(弧度)", "欧拉角(角度)", "四元数"]
        self.modeDataCnt = [3, 3, 3, 4]
        self._modeFunc: List[Callable[[List[float]], None]] = [
            self._drawVector,
            self._drawEuler,
            self._drawEulerDegree,
            self._drawQuaternion,
        ]

        self._modeCombo = ttk.Combobox(dataFrame, width=10, state="readonly", values=self.modes)
        self._modeCombo.current(0)
        _validate = lambda s: all(v.strip() == "_" or ValEntry.type_validator(int)(v.strip()) for v in s.split(","))
        self._dataEntry = ValEntry(_validate, dataFrame, text="0,1,2", width=40)
        self._dataEntry.bind("<Return>", self._applyData)

        ttk.Label(dataFrame, text="模式:").pack(side="left", pady=5)
        self._modeCombo.pack(side="left", padx=5, pady=5)
        ttk.Label(dataFrame, text="数据索引:").pack(side="left", pady=5)
        self._dataEntry.pack(side="left", padx=3, pady=5)
        ttk.Button(dataFrame, text="应用", command=self._applyData).pack(side="left", padx=5, pady=5)

        self._pauseButton = ttk.Checkbutton(dataFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))
        self._pauseButton.pack(side="left", padx=4, pady=5)

        self._collection3Ds = []
        self._init_ax()
        self._applyData()

        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=100, blit=False)

    def _drawVector(self, data: List[float]) -> None:
        self._draw_quiver(0, 0, 0, *data)

    def _drawRotMat(self, mat: np.ndarray):
        vec = self._lim * mat.T
        for i, (c, s) in enumerate(zip("rgb", (0.62, 0.31, 0.31))):
            self._draw_quiver(0, 0, 0, *(vec[i, :] * s), color=c, linewidths=5)

    def _drawEuler(self, data: List[float]) -> None:
        self._drawRotMat(R.from_euler("xyz", data, degrees=False).as_matrix())

    def _drawEulerDegree(self, data: List[float]) -> None:
        self._drawRotMat(R.from_euler("xyz", data, degrees=True).as_matrix())

    def _drawQuaternion(self, data: List[float]) -> None:
        self._drawRotMat(R.from_quat(data).as_matrix())

    def _applyData(self, *_):
        mode = self._modeCombo.current()
        s = self._dataEntry.get().split(",")
        dataIdx = [-1 if v.strip() == "_" else abs(int(v)) for v in s]
        if len(dataIdx) != self.modeDataCnt[mode]:
            messagebox.showerror(
                "错误",
                f"模式`{self.modes[mode]}`需要{self.modeDataCnt[mode]}个数据, 但是你输入了{len(dataIdx)}个数据索引",
                master=self._root,
            )
            return
        sgn = [v.strip() != "_" and int(v) < 0 for v in s]
        with self._dataLock:
            self._updateFlag = False
            self._mode = mode
            self._dataIdx = dataIdx
            self._sgn = sgn

    def updateData(self, data: List[float]):
        if self._pauseButton.instate(["selected"]):
            return
        with self._dataLock:
            self._data = [
                -data[i] if s else data[i] if 0 <= i < len(data) else 0.0 for i, s in zip(self._dataIdx, self._sgn)
            ]
            self._updateFlag = True

    def _updatePlot(self, *_):
        with self._dataLock:
            if not self._updateFlag:
                return
            self._updateFlag = False
            data = self._data
            mode = self._mode
            self._clear_quivers()
        self._modeFunc[mode](data)

    def _draw_quiver(self, *args, color="black", linewidths=4, arrow_length_ratio=0.2, **kwargs):
        with self._drawLock:
            self._collection3Ds.append(
                self._ax.quiver(
                    *args, color=color, linewidths=linewidths, arrow_length_ratio=arrow_length_ratio, **kwargs
                )
            )

    def _clear_quivers(self):
        for q in self._collection3Ds:
            q.remove()
        self._collection3Ds = []

    def _init_fig(self):
        self._fig = plt.Figure()
        PAD = 0.17
        self._fig.subplots_adjust(top=1 + PAD, bottom=-PAD, left=-PAD, right=1 + PAD, wspace=0, hspace=0)
        self._ax = self._fig.add_subplot(projection="3d", box_aspect=(1, 1, 1))

    def _init_ax(self, *_):
        with self._drawLock:
            self._ax.cla()
            self._ax._axis3don = False  # 关闭坐标轴

            self._lim = float(self._limEntry.get())

            self._ax.quiver(-self._lim, 0, 0, self._lim * 2, 0, 0, color="r", arrow_length_ratio=0.03)  # x-axis
            self._ax.quiver(0, -self._lim, 0, 0, self._lim * 2, 0, color="g", arrow_length_ratio=0.03)  # y-axis
            self._ax.quiver(0, 0, -self._lim, 0, 0, self._lim * 2, color="b", arrow_length_ratio=0.03)  # z-axis

            TIP = 0.04
            self._ax.text(self._lim * (1 + TIP), 0, 0, "x", fontsize="large", color="r")
            self._ax.text(0, self._lim * (1 + TIP), 0, "y", fontsize="large", color="g")
            self._ax.text(0, 0, self._lim * (1 + TIP), "z", fontsize="large", color="b")

            RATIO = 0.85
            self._ax.set_xlim([-self._lim * RATIO, self._lim * RATIO])
            self._ax.set_ylim([-self._lim * RATIO, self._lim * RATIO])
            self._ax.set_zlim([-self._lim * RATIO, self._lim * RATIO])

            for q in self._collection3Ds:
                self._ax.add_collection3d(q)

    def mainloop(self):
        self._client.start()
        self._recvGUI.start()
        self._root.mainloop()

    def shutdown(self):
        self._recvGUI.shutdown()
        self._client.shutdown()
        self._root.destroy()


if __name__ == "__main__":
    app = FBRotApp(True)
    app.mainloop()

import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyArrow, Polygon
from types import SimpleNamespace
from math import sqrt, atan2
import threading
import numpy as np
from typing import List, Optional, Tuple

import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from FBRecv import FBFloatMultiRecv
from FBSocket import FBServer, FBClient
from FBFunc import as_float

HEADER = b"\x00\xff\x80\x7f"
CONTROL_ID = b"\x08"
STATE_ID = b"\x0A"


class Robot(Polygon):
    DEFAULT_SHAPE = np.array([[0.14, 0.11], [0.16, 0], [0.14, -0.11], [-0.14, -0.11], [-0.14, 0.11]], dtype=np.float32)

    def __init__(self, verts: np.ndarray = None, x=0.0, y=0.0, yaw=0.0, fill=False, *args, **kwargs):
        self.lock = threading.Lock()
        self._updateFlag = self._queryUpdateFlag = False
        self.verts = verts if verts is not None else self.DEFAULT_SHAPE
        super().__init__([[0, 0], [0, 0]], *args, fill=fill, **kwargs)
        self.set_pose(x, y, yaw)

    def set_pose(self, x: float, y: float, yaw: float):
        with self.lock:
            self.x, self.y, self.yaw = x, y, yaw
            self._queryUpdateFlag = self._updateFlag = True

    def update_pose(self):
        with self.lock:
            if not self._updateFlag:
                return
            self._updateFlag = False
            x, y, yaw = self.x, self.y, self.yaw
        vert = self.verts.copy()
        rot = np.array([[np.cos(yaw), np.sin(yaw)], [-np.sin(yaw), np.cos(yaw)]], dtype=np.float32)
        vert = vert @ rot
        vert[:, 0] += x
        vert[:, 1] += y
        self.set_xy(vert)

    def get_pose(self) -> Tuple[float]:
        with self.lock:
            return (self.x, self.y, self.yaw)

    def get_updated(self):
        with self.lock:
            res = self._queryUpdateFlag
            self._queryUpdateFlag = False
        return res


class Scatter:
    def __init__(self, ax: plt.Axes, robotRef: Optional[Robot] = None, data=[], **kwargs):
        self.data = np.reshape(data, (-1, 2))
        self._updateFlag = False
        self.scatter = ax.scatter(*self.data.T, **kwargs)
        self.robotRef = robotRef
        self.lock = threading.Lock()

    def get_artist(self):
        return self.scatter

    def set_data(self, data):
        with self.lock:
            self._updateFlag = True
            self.data = data

    def update_data(self):
        with self.lock:
            updated = self._updateFlag
        if not updated and self.robotRef is not None and not self.robotRef.get_updated():
            return False
        with self.lock:
            self._updateFlag = False
            data = self.data
        if self.robotRef is not None:
            x, y, yaw = self.robotRef.get_pose()
            rot = np.array([[np.cos(yaw), np.sin(yaw)], [-np.sin(yaw), np.cos(yaw)]], dtype=np.float32)
            data = data @ rot + np.array([x, y], dtype=np.float32)
        self.scatter.set_offsets(data)


class FBPosApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBPos")
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(0, weight=1)

        self._recv = FBFloatMultiRecv()
        self._client = FBServer() if isServer else FBClient()
        self._client.registerRecvCallback(self._recv.input)

        self._plotFrame = ttk.Frame(self._root)
        self._plotFrame.grid(row=0, column=0, sticky="wesn")
        self._plotFrame.rowconfigure(0, weight=1)
        self._plotFrame.columnconfigure(0, weight=1)

        self._fig = plt.Figure()
        self._fig.subplots_adjust(top=0.965, bottom=0.055, left=0.115, right=0.97, wspace=0, hspace=0)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._plotFrame)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="wesn")
        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.set_aspect("equal", adjustable="datalim")

        self._toolbar = NavigationToolbar2Tk(self._canvas, self._plotFrame, pack_toolbar=False)
        self._toolbar.update()
        self._hiddenPanButton = self._toolbar._buttons["Pan"]
        self._prePanState = False

        self._canvas.mpl_connect("button_press_event", self._control_on_press)
        self._canvas.mpl_connect("button_release_event", self._control_on_release)
        self._canvas.mpl_connect("motion_notify_event", self._control_on_move)
        self._control_event: SimpleNamespace = None
        self._control_event_lock = threading.Lock()
        self._control_arrow = FancyArrow(0, 0, 1, 0, width=0.1)
        self._ax.add_patch(self._control_arrow)
        self._control_arrow.set_visible(False)

        self._opFrame = ttk.Frame(self._root)
        self._opFrame.grid(row=1, column=0, sticky="we")

        self._resetLimButton = ttk.Button(self._opFrame, text="视野重置", command=self._resetLim)
        self._resetLimButton.pack(side="left", padx=5, pady=5)

        self._panButton = ttk.Checkbutton(
            self._opFrame, text="拖拽", bootstyle=("warning", "outline", "toolbutton"), command=self._onPanClick,
        )
        self._panButton.pack(side="left", padx=5, pady=5)

        self._controlButton = ttk.Checkbutton(
            self._opFrame, text="控制", bootstyle=("error", "outline", "toolbutton"), command=self._onControlClick,
        )
        self._controlButton.pack(side="left", padx=5, pady=5)

        self._pauseButton = ttk.Checkbutton(self._opFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))
        self._pauseButton.pack(side="left", padx=5, pady=5)

        self._resetPosButton = ttk.Button(self._opFrame, text="重置位置", command=self._resetPos)
        self._resetPosButton.pack(side="left", padx=5, pady=5)

        self._robots: List[Robot] = []
        self._scatters: List[Scatter] = []

    def _resetPos(self):
        data = HEADER + STATE_ID + b"".join(map(as_float, (0, 0, 0, 0, 0, 0)))
        self._client.send(data)

    def _get_control_data(self):
        return (
            self._control_event.x,
            self._control_event.y,
            self._control_event.dx,
            self._control_event.dy,
        )

    def _control_on_press(self, event):
        if event.xdata is None:
            return
        if self._controlButton.instate(["selected"]):
            with self._control_event_lock:
                self._control_event = SimpleNamespace(x=event.xdata, y=event.ydata, dx=0, dy=0)

    def _control_on_move(self, event):
        if event.xdata is None:
            return
        with self._control_event_lock:
            if self._control_event is not None:
                self._control_event.dx, self._control_event.dy = (
                    event.xdata - self._control_event.x,
                    event.ydata - self._control_event.y,
                )

    def _control_on_release(self, event):
        with self._control_event_lock:
            if self._control_event is None or self._control_event.dx == self._control_event.dy == 0:
                self._control_event = None
                return
            x, y, dx, dy = self._get_control_data()
            self._control_event = None
        yaw = atan2(dy, dx)
        print("x:%.2f y:%.2f yaw:%.2f" % (x, y, yaw))
        if event.button == 1:
            data = HEADER + CONTROL_ID + b"".join(map(as_float, (x, y, yaw)))
        else:
            data = HEADER + STATE_ID + b"".join(map(as_float, (x, y, yaw, 0, 0, 0)))
        self._client.send(data)

    def _getLimScale(self):
        xlim, ylim = self._ax.get_xlim(), self._ax.get_ylim()
        return min(xlim[1] - xlim[0], ylim[1] - ylim[0])

    def _updateControlArrow(self):
        with self._control_event_lock:
            if self._control_event is None or self._control_event.dx == self._control_event.dy == 0:
                self._control_arrow.set_visible(False)
                return [self._control_arrow]
            else:
                self._control_arrow.set_visible(True)
                x, y, dx, dy = self._get_control_data()
        k = self._getLimScale() * 0.2 / sqrt(dx * dx + dy * dy)
        self._control_arrow.set_data(x=x, y=y, dx=dx * k, dy=dy * k)
        return [self._control_arrow]

    def registerScatter(self, id: int, *args, **kwargs) -> Scatter:
        scatter = Scatter(self._ax, *args, **kwargs)
        self._recv.setConfig(id, 0, 4, True)
        self._recv.registerRecvCallback(id, lambda data: scatter.set_data(np.reshape(data, (-1, 2))))
        self._scatters.append(scatter)
        return scatter

    def _updateScatters(self):
        if not self._pauseButton.instate(["selected"]):
            for scatter in self._scatters:
                scatter.update_data()
        return [scatter.get_artist() for scatter in self._scatters]

    def registerRobot(self, id: Optional[int] = None, *args, **kwargs) -> Robot:
        robot = Robot(*args, **kwargs)
        if id is not None:
            self._recv.setConfig(id, 3, 4, True)
            self._recv.registerRecvCallback(id, lambda data: robot.set_pose(*data))
            self._robots.append(robot)
        return robot

    def _updateRobots(self):
        if not self._pauseButton.instate(["selected"]):
            for robot in self._robots:
                robot.update_pose()
        return self._robots

    def _updatePlot(self, *_):
        changed = []
        changed.extend(self._updateControlArrow())
        changed.extend(self._updateRobots())
        changed.extend(self._updateScatters())
        return changed

    def _onPanClick(self, *_):
        cur = self._panButton.instate(["selected"])
        if cur != self._prePanState:
            self._toolbar.pan()
            self._prePanState = cur
        if cur:
            self._controlButton.state(["!selected"])

    def _onControlClick(self, *_):
        if self._controlButton.instate(["selected"]):
            self._panButton.state(["!selected"])
            self._onPanClick()

    def _initPlot(self):
        self._ax.cla()
        self._ax.grid(True)
        for robot in self._robots:
            self._ax.add_patch(robot)
        self._resetLim()

    def _resetLim(self, *_):
        self._ax.set_ylim((-1, 8))
        self._ax.set_xlim((-1, 8))

    def mainloop(self):
        self._client.start()
        self._recv.start()

        self._initPlot()
        self._animation = animation.FuncAnimation(self._fig, self._updatePlot, interval=20, blit=True)
        self._root.mainloop()

    def shutdown(self):
        self._recv.shutdown()
        self._client.shutdown()

        self._root.destroy()


if __name__ == "__main__":
    app = FBPosApp(True)
    app.registerRobot(30)
    app.mainloop()

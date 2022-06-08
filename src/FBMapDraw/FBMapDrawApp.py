import tkinter as tk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os, os.path

SAVE_DIR = os.path.expanduser("~/Desktop")
SAVE_NAME_TXT = "map.txt"
SAVE_NAME = "map.pdf"
SAVE_NAME_WITHLABEL = "map_with_label.pdf"

CM = 1 / 2.54  # 1英尺=2.54厘米

# A4纸属性
A4_W = 29.7 * CM
A4_H = 21 * CM

# 地图大小
W = 7.0  # 米
H = 5.0  # 米

# 边框留白
MIN_PAD = 1.0 * CM

# 边框粗细
BORDER_WIDTH = 0.15  # 厘米

# 圆直径
CIRCLE_SIZE = 0.5  # 厘米


if (A4_H - MIN_PAD * 2) / (A4_W - MIN_PAD * 2) < H / W:
    SIZE_H = A4_H - MIN_PAD * 2
    SIZE_W = SIZE_H * W / H
else:
    SIZE_W = A4_W - MIN_PAD * 2
    SIZE_H = SIZE_W * H / W

W_PAD = (A4_W - SIZE_W) / 2
H_PAD = (A4_H - SIZE_H) / 2


class FBMapDrawApp:
    def __init__(self) -> None:
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBMapDraw - 左键删除 右键添加")
        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(0, weight=1)

        self._plotFrame = ttk.Frame(self._root)
        self._plotFrame.grid(row=0, column=0, sticky="wesn")
        self._plotFrame.rowconfigure(0, weight=1)
        self._plotFrame.columnconfigure(0, weight=1)
        self._fig = plt.Figure()
        self._setA4Size()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._plotFrame)
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="wesn")
        self._ax = self._fig.add_subplot(1, 1, 1)
        self._ax.set_picker(True)
        self._ax.set_aspect("equal")
        self._canvas.mpl_connect("pick_event", self._onPick)

        self._opFrame = ttk.Frame(self._root)
        self._opFrame.grid(row=1, column=0, sticky="we")
        self._clearButton = ttk.Button(self._opFrame, text="清空", command=self.clear)
        self._saveButton = ttk.Button(self._opFrame, text="保存", command=self.save)
        self._clearButton.pack(side="left", padx=5, pady=5)
        self._saveButton.pack(side="left", padx=5, pady=5)

        ttk.Label(self._opFrame, text=f"保存路径: {os.path.join(SAVE_DIR, SAVE_NAME)}\t点数: ").pack(side="left", pady=5)

        self.pointCnt = tk.IntVar(self._root, value=0)
        ttk.Label(self._opFrame, textvariable=self.pointCnt).pack(side="left", pady=5)

        self.circles = {}

    def _onPick(self, event):
        artist, mouse = event.artist, event.mouseevent
        if mouse.button == 1:
            if isinstance(artist, plt.Circle):
                artist.remove()
                self.circles[artist].remove()
                del self.circles[artist]
                self.pointCnt.set(self.pointCnt.get() - 1)
                self._canvas.draw()
        else:
            if isinstance(artist, plt.Circle):
                return
            x, y = mouse.xdata, mouse.ydata
            r = self.get_circle_r(CIRCLE_SIZE)
            circle = plt.Circle((x, y), r, color="black", picker=True)
            label = plt.Text(x + r, y + r, f"({x:.2f}, {y:.2f})", color="black")
            self._ax.add_patch(circle)
            self._ax.add_artist(label)
            self.circles[circle] = label
            self.pointCnt.set(self.pointCnt.get() + 1)
            self._canvas.draw()

    def _setA4Size(self):
        self._fig.set_size_inches(A4_W, A4_H)

    def _initPlot(self):
        self._fig.subplots_adjust(
            left=W_PAD / A4_W,
            bottom=H_PAD / A4_H,
            right=1.0 - W_PAD / A4_W,
            top=1.0 - H_PAD / A4_H,
        )
        self._ax.cla()
        self._ax.axes.xaxis.set_visible(False)
        self._ax.axes.yaxis.set_visible(False)
        self._ax.set_xlim(0, W)
        self._ax.set_ylim(0, H)
        for x in self._ax.spines.values():
            x.set_linewidth(self.get_width(BORDER_WIDTH))
        self.pointCnt.set(0)

    def clear(self):
        print([x.get_center() for x in self.circles.keys()])
        self._initPlot()
        self.circles.clear()
        self._canvas.draw()

    def save(self):
        with open(os.path.join(SAVE_DIR, SAVE_NAME_TXT), "w") as f:
            f.write(f"{len(self.circles)}\n")
            for c in self.circles.keys():
                f.write(f"{c.get_center()[0]:.2f} {c.get_center()[1]:.2f}\n")

        self._setA4Size()
        for label in self.circles.values():
            label.set_visible(False)
        with PdfPages(os.path.join(SAVE_DIR, SAVE_NAME)) as pdf:
            pdf.savefig(self._fig)
        for label in self.circles.values():
            label.set_visible(True)
        with PdfPages(os.path.join(SAVE_DIR, SAVE_NAME_WITHLABEL)) as pdf:
            pdf.savefig(self._fig)

    def get_width(self, width_cm):
        width_cm *= CM * W / SIZE_W
        ppd = 72.0 / self._ax.figure.dpi
        trans = self._ax.transData.transform
        return ((trans((1, width_cm)) - trans((0, 0))) * ppd)[1]

    def get_circle_r(self, size_cm):
        return size_cm * CM * W / SIZE_W * 0.5

    def mainloop(self):
        self._initPlot()
        self._root.mainloop()


if __name__ == "__main__":
    app = FBMapDrawApp()
    app.mainloop()

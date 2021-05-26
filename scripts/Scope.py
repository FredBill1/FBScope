from .Main import Main


class Scope:
    def __init__(self, main: Main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.transfering = False
        self.T = [0]
        self.data = [[0]] * 8
        self.getConfig()
        self.setProperty()
        self.drawData()
        self.drawWorker()

    def getConfig(self):
        self.CHECK = self.main.Config["SERIAL"]["CHECK"]
        self.Config = self.main.Config["SCOPE"]

    def setProperty(self):
        from tkinter import StringVar, BooleanVar, LabelFrame as LF
        from tkinter.ttk import Button, Combobox, Label, Frame, Entry, Checkbutton, LabelFrame

        self.uiFrame = Frame(self.root)
        self.startFrame = LabelFrame(self.uiFrame, text="控制")
        self.countLabel = Label(self.startFrame, text="数量:")
        self.countCombobox = Combobox(self.startFrame, values=list(range(1, 9)), width=2, state="readonly")
        self.sampleLabel = Label(self.startFrame, text="点数:")
        self.sampleVar = StringVar(value=str(self.Config["SAMPLECOUNT"]))
        self.sampleEntry = Entry(self.startFrame, textvariable=self.sampleVar, validate="focusout", validatecommand=self.entryCallback, width=5)
        self.startButton = Button(self.startFrame, text="开始", state="disabled", command=self.toggleTransfer)
        self.sepVar = BooleanVar(value=False)
        self.sepButton = Checkbutton(self.startFrame, text="分行显示", variable=self.sepVar, command=self.drawData)

        fgs = ("steel blue", "orange", "dark green", "red", "purple", "cyan", "deep pink", "gray")
        types = ("int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float", "double")
        self.lineFrames = [LF(self.uiFrame, fg=fgs[i], text="第%d条线" % (i + 1)) for i in range(8)]
        self.typeCombobox = [Combobox(self.lineFrames[i], width=6, values=types, state="readonly") for i in range(8)]

        self.enabled = [BooleanVar(value=True) for i in range(8)]
        self.enableButton = [Checkbutton(self.lineFrames[i], variable=self.enabled[i], command=self.drawData) for i in range(8)]

        self.imgFrame = LabelFrame(self.root, text="图像")
        self.setImg()

        self.root.title("FBScope - 虚拟示波器")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.uiFrame.pack(side="left", padx=3, pady=3, fill="y")
        self.startFrame.pack()
        self.countLabel.grid(row=0, column=0, padx=3, pady=3)
        self.countCombobox.current(self.Config["LINES"] - 1)
        self.countCombobox.grid(row=0, column=1, padx=3, pady=3)
        self.countCombobox.bind("<<ComboboxSelected>>", self.countCallback)
        self.Config["LINES"] = 8
        self.countCallback()
        self.sampleLabel.grid(row=1, column=0, padx=3, pady=3)
        self.sampleEntry.grid(row=1, column=1, padx=3, pady=3)
        self.sepButton.grid(row=2, column=0, columnspan=2, padx=3, pady=1, sticky="w")
        self.startButton.grid(row=3, column=0, columnspan=2, padx=3, pady=3)

        for i in range(8):
            self.lineFrames[i].pack(fill="x")
            self.enableButton[i].pack(side="left", padx=1, pady=3)
            self.typeCombobox[i].pack(side="left", pady=3)
            self.typeCombobox[i].bind("<<ComboboxSelected>>", lambda event, i=i: self.typeCallback(i))
            self.typeCombobox[i].current(self.Config["TYPES"][i])

        self.imgFrame.pack(side="left", padx=3, pady=3, fill="both", expand=True)

        if "Scope" in self.main.Config["WINDOWPOSITION"]:
            self.root.geometry(self.main.Config["WINDOWPOSITION"]["Scope"])

    def setImg(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        self.fig = Figure()
        self.canvas = FigureCanvasTkAgg(self.fig, self.imgFrame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.imgFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def countCallback(self, event=None):
        t = self.countCombobox.current() + 1
        cur = self.Config["LINES"]
        if t < cur:
            for i in range(t, cur):
                self.enableButton[i]["state"] = self.typeCombobox[i]["state"] = "disabled"
        else:
            for i in range(cur, t):
                self.typeCombobox[i]["state"] = "readonly"
                self.enableButton[i]["state"] = "normal"
        self.Config["LINES"] = t
        self.drawData()

    def entryCallback(self):
        try:
            val = int(self.sampleVar.get())
            if val > 0:
                self.Config["SAMPLECOUNT"] = int(self.sampleVar.get())
                return True
        except:
            pass
        self.sampleVar.set(int(self.Config["SAMPLECOUNT"]))
        return False

    def typeCallback(self, i):
        self.Config["TYPES"][i] = self.typeCombobox[i].current()

    def toggleTransfer(self):
        if self.startButton["text"] == "开始":
            self.startButton["text"] = "停止"
            self.countCombobox["state"] = "disabled"
            self.sampleEntry["state"] = "disabled"
            for i in range(self.Config["LINES"]):
                self.typeCombobox[i]["state"] = "disabled"
            self.main.setActivate(False)
            self.main.camera.setActivate(False)
            self.startTransfer()
        else:
            self.startButton["text"] = "开始"
            self.countCombobox["state"] = "readonly"
            self.sampleEntry["state"] = "normal"
            for i in range(self.Config["LINES"]):
                self.typeCombobox[i]["state"] = "readonly"
            self.main.setActivate(True)
            self.main.camera.setActivate(True)
            self.transfering = False

    def startTransfer(self):
        from threading import Thread
        from collections import deque

        self.T = [i for i in range(self.Config["SAMPLECOUNT"])]
        self.data = [deque([0] * self.Config["SAMPLECOUNT"], maxlen=self.Config["SAMPLECOUNT"]) for i in range(self.Config["LINES"])]

        self.transfering = True
        Thread(target=self.transfer).start()

    def transfer(self):
        from struct import unpack

        while self.transfering:
            buf = b"\x00\x00\x00\x00"
            while self.transfering and buf != self.CHECK:
                buf = (buf + self.main.read())[-4:]
            for i in range(self.Config["LINES"]):
                cur = self.Config["TYPES"][i]
                if cur < 8:
                    Len, signed = 1 << (cur >> 1), not (cur & 1)
                    buf = b""
                    while self.transfering and len(buf) < Len:
                        buf += self.main.read()
                    if self.transfering:
                        res = int.from_bytes(buf, "little", signed=signed)
                        self.data[i].append(res)
                else:
                    Len, format = 4 << (cur - 8), "d" if cur - 8 else "f"
                    buf = b""
                    while self.transfering and len(buf) < Len:
                        buf += self.main.read()
                    if self.transfering:
                        res = unpack(format, buf)[0]
                        self.data[i].append(res)

    def drawData(self):
        colors = ("tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:cyan", "tab:pink", "tab:gray")
        self.fig.clf()
        if self.sepVar.get():
            count = sum(self.enabled[i].get() for i in range(self.Config["LINES"]))
            cur = 0
            for i in range(self.Config["LINES"]):
                if self.enabled[i].get():
                    cur += 1
                    ax = self.fig.add_subplot(count, 1, cur)
                    ax.grid()
                    ax.set_xlim(0, self.Config["SAMPLECOUNT"])
                    if i < len(self.data):
                        ax.plot(self.T, self.data[i], color=colors[i])
        else:
            ax = self.fig.add_subplot(1, 1, 1)
            ax.grid()
            ax.set_xlim(0, self.Config["SAMPLECOUNT"])
            for i in range(self.Config["LINES"]):
                if self.enabled[i].get():
                    if i < len(self.data):
                        ax.plot(self.T, self.data[i], color=colors[i])
        self.canvas.draw()

    def drawWorker(self):
        if self.transfering:
            self.drawData()
        if self.sepVar.get():
            self.root.after(200, self.drawWorker)
        else:
            self.root.after(100, self.drawWorker)

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.startButton["state"] = state[activate]

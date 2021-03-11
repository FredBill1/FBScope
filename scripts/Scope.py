from .Main import Main


class Scope:
    def __init__(self, main: Main) -> None:
        self.main = main

        from tkinter import Toplevel

        self.root = Toplevel(self.main.root)
        self.getConfig()
        self.setProperty()

    def getConfig(self):
        self.CHECK = self.main.Config["SERIAL"]["CHECK"]
        self.Config = self.main.Config["SCOPE"]

    def setProperty(self):
        from tkinter import StringVar, Label as LB
        from tkinter.ttk import Button, Combobox, Label, Frame, LabelFrame, Entry

        self.uiFrame = Frame(self.root)
        self.startFrame = LabelFrame(self.uiFrame, text="控制")
        self.countLabel = Label(self.startFrame, text="数量:")
        self.countCombobox = Combobox(self.startFrame, values=list(range(1, 9)), width=2, state="readonly")
        self.sampleLabel = Label(self.startFrame, text="点数:")
        self.sampleVar = StringVar(value=str(self.Config["SAMPLECOUNT"]))
        self.sampleEntry = Entry(self.startFrame, textvariable=self.sampleVar, validate="focusout", validatecommand=self.entryCallback, width=5)
        self.startButton = Button(self.startFrame, text="开始", state="disabled", command=self.toggleTransfer)

        bgs = ("blue", "orange", "dark green", "red", "purple", "cyan", "maroon", "gray")
        types = ("int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float", "double")
        self.lineFrames = [LabelFrame(self.uiFrame, text="第%d条线" % (i + 1)) for i in range(8)]
        self.colorLabel = [LB(self.lineFrames[i], text="[X]", fg=bgs[i]) for i in range(8)]
        self.typeCombobox = [Combobox(self.lineFrames[i], width=1, values=types, state="readonly") for i in range(8)]

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
        self.startButton.grid(row=2, column=0, columnspan=2, padx=3, pady=3)

        for i in range(8):
            self.lineFrames[i].pack(fill="x")
            self.colorLabel[i].pack(side="left", pady=3)
            self.typeCombobox[i].pack(side="left", padx=3, pady=3, fill="x", expand=True)
            self.typeCombobox[i].bind("<<ComboboxSelected>>", lambda event, i=i: self.typeCallback(i))
            self.typeCombobox[i].current(self.Config["TYPES"][i])

        self.imgFrame.pack(side="left", padx=3, pady=3, fill="both", expand=True)

    def setImg(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        from matplotlib.backend_bases import key_press_handler

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.grid()
        self.canvas = FigureCanvasTkAgg(self.fig, self.imgFrame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.imgFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def countCallback(self, event=None):
        t = self.countCombobox.current() + 1
        cur = self.Config["LINES"]
        if t < cur:
            for i in range(t, cur):
                self.typeCombobox[i]["state"] = "disabled"
        else:
            for i in range(cur, t):
                self.typeCombobox[i]["state"] = "readonly"

        self.Config["LINES"] = t

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

    def setTdata(self):
        pass

    def setLines(self):
        pass

    def plot(self):
        pass

    def toggleTransfer(self):
        pass


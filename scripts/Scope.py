from Main import Main


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
        from tkinter.ttk import Button, LabelFrame, Combobox, Label, Frame

        self.uiFrame = Frame(self.root)
        self.startFrame = LabelFrame(self.uiFrame, text="控制")
        self.countLabel = Label(self.startFrame, text="数量:")
        self.countCombobox = Combobox(self.startFrame, values=list(range(1, 9)), width=2, state="readonly")
        self.startButton = Button(self.startFrame, text="开始", state="disabled", command=self.toggleTransfer)

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
        self.countCallback()
        self.startButton.grid(row=1, column=0, columnspan=2, padx=3, pady=3)

        self.imgFrame.pack(side="left", padx=3, pady=3, fill="both", expand=True)

    def setImg(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        from matplotlib.backend_bases import key_press_handler

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.imgFrame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.imgFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def countCallback(self, event=None):
        self.Config["LINES"] = self.countCombobox.current() + 1
        print(self.Config["LINES"])

    def setTdata(self):
        pass

    def setLines(self):
        pass

    def plot(self):
        pass

    def toggleTransfer(self):
        pass

    def poop(self):
        from collections import deque

        self.tData = list(range(100))
        self.yData = deque([1] * 100)
        self.line.set_data(self.tData, self.yData)
        # self.ax.plot(self.tData, self.yData)
        # self.canvas.draw()


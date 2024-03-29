from .Main import Main


class Remote:
    def __init__(self, main: Main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.pressed = [[False] * 3 for i in range(2)]
        self.direction = 0
        self.getConfig()
        self.setProperty()

    def getConfig(self) -> None:
        self.Config = self.main.Config["REMOTE"]

    def setProperty(self) -> None:
        from tkinter import StringVar, Button as BT
        from tkinter.ttk import Button, LabelFrame, Label, Entry

        self.uiFrame = LabelFrame(self.root, text="设定")
        self.speedLabel = Label(self.uiFrame, text="速度:")
        self.speedVar = StringVar(value=str(self.Config["SPEED"]))
        self.speedEntry = Entry(self.uiFrame, textvariable=self.speedVar, validate="focusout", validatecommand=lambda: self.entryCallback(self.speedVar, "SPEED"), width=5)
        self.turnLabel = Label(self.uiFrame, text="转向:")
        self.turnVar = StringVar(value=str(self.Config["TURN"]))
        self.turnEntry = Entry(self.uiFrame, textvariable=self.turnVar, validate="focusout", validatecommand=lambda: self.entryCallback(self.turnVar, "TURN"), width=5)
        self.startButton = Button(self.uiFrame, text="启动", state="disabled", width=10, command=self.toggleTransfer)

        texts = (("左切Q", "直行W", "右切E"), ("左转A", "后退S", "右转D"))
        self.ctrlFrame = LabelFrame(self.root, text="控制 - 前↑")
        self.buttons = [[BT(self.ctrlFrame, text=texts[i][j], width=6) for j in range(3)] for i in range(2)]

        self.root.title("FBScope - 遥控器")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.uiFrame.pack(side="left", padx=3, pady=3)
        self.speedLabel.grid(row=0, column=0, padx=3, pady=3)
        self.speedEntry.grid(row=0, column=1, padx=3, pady=3)
        self.turnLabel.grid(row=1, column=0, padx=3, pady=3)
        self.turnEntry.grid(row=1, column=1, padx=3, pady=3)
        self.startButton.grid(row=2, column=0, columnspan=2, padx=3, pady=3)

        self.ctrlFrame.pack(side="left", padx=3, pady=3, fill="y")

        keys = (("q", "w", "e"), ("a", "s", "d"))
        for i in range(2):
            for j in range(3):
                self.ctrlFrame.grid_rowconfigure(i, weight=1)
                self.buttons[i][j].grid(row=i, column=j, padx=1, pady=1, sticky="EWNS")
                self.root.bind("<%s>" % keys[i][j], lambda event, i=i, j=j: self.pressCallback(i, j))
                self.root.bind("<KeyRelease-%s>" % keys[i][j], lambda event, i=i, j=j: self.releaseCallback(i, j))

        if "Remote" in self.main.Config["WINDOWPOSITION"]:
            self.root.geometry(self.main.Config["WINDOWPOSITION"]["Remote"])

    def toggleTransfer(self):
        if self.startButton["text"] == "启动":
            self.startButton["text"] = "停止"
            self.speedEntry["state"] = self.turnEntry["state"] = "disabled"
            self.main.setActivate(False)
            self.main.setstate.setActivate(False)
            self.main.adrc.setActivate(False)
            self.main.patrol.setActivate(False)
            for i in range(5):
                self.main.setstate.checked[i].set(i != 4)
                self.main.setstate.buttons[i]["state"] = "disabled"
            self.main.setstate.uploadState()
            self.transfering = True
        else:
            self.transfering = False
            self.startButton["text"] = "启动"
            self.speedEntry["state"] = self.turnEntry["state"] = "normal"
            self.main.setActivate(True)
            self.main.setstate.setActivate(True)
            self.main.adrc.setActivate(True)
            self.main.patrol.setActivate(True)
            for i in range(5):
                self.main.setstate.buttons[i]["state"] = "normal"
            self.transfering = False

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.startButton["state"] = state[activate]

    def entryCallback(self, sv, key) -> bool:
        try:
            t = int(sv.get())
            if -32768 <= t < 32768:
                self.Config[key] = t
                return True
        except:
            pass
        sv.set(str(self.Config[key]))
        return False

    def transfer(self) -> None:
        if self.transfering:
            turn = 0 if self.pressed[1][0] == self.pressed[1][2] else -self.Config["TURN"] if self.pressed[1][0] else self.Config["TURN"]
            speed = 0 if self.pressed[0][1] == self.pressed[1][1] else self.Config["SPEED"] if self.pressed[0][1] else -self.Config["SPEED"]
            self.main.write(self.Config["CHECK"] + bytes([self.direction]) + speed.to_bytes(2, "little", signed=True) + turn.to_bytes(2, "little", signed=True))

    def pressCallback(self, i, j) -> None:
        if not self.pressed[i][j]:
            self.buttons[i][j]["fg"] = "red"
            self.buttons[i][j].config(relief="sunken")
            self.pressed[i][j] = True
            if i == j == 0:
                self.direction = (self.direction - 1) % 4
                self.setFrameTitle()
            if i == 0 and j == 2:
                self.direction = (self.direction + 1) % 4
                self.setFrameTitle()
            self.transfer()

    def releaseCallback(self, i, j) -> None:
        self.buttons[i][j]["fg"] = "black"
        self.buttons[i][j].config(relief="raised")
        self.pressed[i][j] = False
        self.transfer()

    def setFrameTitle(self) -> None:
        directs = ("前↑", "右→", "后↓", "左←")
        self.ctrlFrame["text"] = "控制 - " + directs[self.direction]

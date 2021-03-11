class SetState:
    def __init__(self, main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.getConfig()
        self.setProperty()

    def getConfig(self):
        self.RESET = self.main.Config["SETSTATE"]["RESET"]
        self.CHECK = self.main.Config["SETSTATE"]["CHECK"]
        self.SPEED = self.main.Config["SETSTATE"]["SPEED"]
        self.PWM = self.main.Config["SETSTATE"]["PWM"]

    def setProperty(self) -> None:
        from tkinter import BooleanVar, StringVar
        from tkinter.ttk import Checkbutton, Button, LabelFrame, Combobox, Label, Entry

        title = ("编码器", "控制器")
        names = ["L1", "L2", "R1", "R2"]
        states = ("disabled", "normal")
        self.toggleFrame = LabelFrame(self.root, text="状态控制")
        self.checked = [[BooleanVar(value=0) for j in range(2)] for j in range(4)]
        self.buttons = [[Checkbutton(self.toggleFrame, text=title[j] + names[i], variable=self.checked[i][j], state=states[not j], command=lambda i=i, j=j: self.toggleCallback(i, j),) for j in range(2)] for i in range(4)]
        self.stateButton = Button(self.toggleFrame, text="上传", state="disabled", command=self.uploadState)
        self.resetButton = Button(self.toggleFrame, text="紧急重置", state="disabled", command=self.urgentReset)

        self.controlFrame = LabelFrame(self.root, text="速度控制")
        self.motorLabel = Label(self.controlFrame, text="电机:")
        self.motorCombobox = Combobox(self.controlFrame, values=names, width=2, state="readonly")
        self.speedLabel = Label(self.controlFrame, text="速度:")
        self.speedVar = StringVar(value="0")
        self.speedEntry = Entry(self.controlFrame, textvariable=self.speedVar, validate="focusout", validatecommand=lambda sv=self.speedVar: self.entryCallback(sv), width=5,)
        self.pwmLabel = Label(self.controlFrame, text="pwm:")
        self.pwmVar = StringVar(value="0")
        self.pwmEntry = Entry(self.controlFrame, textvariable=self.pwmVar, validate="focusout", validatecommand=lambda sv=self.pwmVar: self.entryCallback(sv), width=5,)
        self.speedButton = Button(self.controlFrame, text="上传速度", state="disabled", command=self.uploadSpeed)
        self.pwmButton = Button(self.controlFrame, text="上传pwm", state="disabled", command=self.uploadPwm)

        self.root.title("FBScope - 电机控制")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.toggleFrame.pack(side="left", padx=3, pady=3)
        for i in range(4):
            for j in range(2):
                self.buttons[i][j].grid(row=i, column=j, padx=3, pady=3)
        self.stateButton.grid(row=4, column=0, padx=3, pady=3)
        self.resetButton.grid(row=4, column=1, padx=3, pady=3)

        self.controlFrame.pack(side="left", padx=3, pady=3, fill="y")
        self.motorLabel.grid(row=0, column=0, padx=3, pady=3)
        self.motorCombobox.current(0)
        self.motorCombobox.grid(row=0, column=1, padx=3, pady=3)
        self.speedLabel.grid(row=1, column=0, padx=3, pady=3)
        self.speedEntry.grid(row=1, column=1, padx=3, pady=3)
        self.pwmLabel.grid(row=2, column=0, padx=3, pady=3)
        self.pwmEntry.grid(row=2, column=1, padx=3, pady=3)
        self.speedButton.grid(row=3, column=0, columnspan=2, padx=3, pady=3)
        self.pwmButton.grid(row=4, column=0, columnspan=2, padx=3, pady=3)

    def toggleCallback(self, i, j):
        cur = j ^ self.checked[i][j].get()
        self.buttons[i][j ^ 1]["state"] = "normal" if cur else "disabled"

    def entryCallback(self, sv):
        try:
            t = int(sv.get())
            if -32768 <= t < 32768:
                return True
        except:
            pass
        sv.set("0")
        return False

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.stateButton["state"] = self.resetButton["state"] = self.speedButton["state"] = self.pwmButton["state"] = state[activate]

    def uploadState(self):
        state = 0
        for i in range(4):
            state |= (self.checked[i][0].get() << i) + (self.checked[i][1].get() << (i + 4))
        print(bytes([state]))
        self.main.write(self.CHECK + bytes([state]))
        self.root.bell()

    def urgentReset(self):
        self.main.write(self.RESET)
        self.root.bell()

    def uploadSpeed(self):
        i = self.motorCombobox.current()
        self.checked[i][0].set(True)
        self.checked[i][1].set(True)
        self.buttons[i][0]["state"] = "disabled"
        self.buttons[i][1]["state"] = "normal"
        self.uploadState()
        self.main.write(self.SPEED + bytes([i]) + int(self.speedVar.get()).to_bytes(2, "little", signed=True))

    def uploadPwm(self):
        i = self.motorCombobox.current()
        self.checked[i][1].set(False)
        self.toggleCallback(i, 1)
        self.uploadState()
        self.main.write(self.PWM + bytes([i]) + int(self.pwmVar.get()).to_bytes(2, "little", signed=True))

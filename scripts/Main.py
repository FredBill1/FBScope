class Main:
    def __init__(self, Config) -> None:
        from tkinter import Tk
        from serial import Serial
        from .Camera import Camera
        from .ADRC import ADRC
        from .SetState import SetState
        from .Scope import Scope
        from .Remote import Remote
        from .Patrol import Patrol
        from .Manager import Manager

        self.Config = Config
        self.serial = Serial(baudrate=int(self.Config["SERIAL"]["BAUD"]))

        self.root = Tk()
        self.camera = Camera(self)
        self.adrc = ADRC(self)
        self.setstate = SetState(self)
        self.scope = Scope(self)
        self.remote = Remote(self)
        self.patrol = Patrol(self)
        self.manager = Manager(self)
        self.setProperty()
        self.getPorts()
        self.activate = 0
        self.mainloop = self.root.mainloop

    def setProperty(self) -> None:
        from tkinter.ttk import LabelFrame, Combobox, Button

        self.portFrame = LabelFrame(self.root, text="端口", labelanchor="nw")
        self.portCombobox = Combobox(self.portFrame, state="readonly")
        self.refreshButton = Button(master=self.root, text="刷新", width=6, command=self.getPorts)
        self.activateButton = Button(master=self.root, text="连接", width=6, command=self.toggleConnection)
        self.quitButton = Button(master=self.root, text="退出", width=6, command=self.__onClose)

        self.root.title("FBScope - 串口选择")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", self.__onClose)
        self.portFrame.grid(row=0, column=0, columnspan=3, padx=3, pady=3)
        self.portCombobox.pack(fill="x")
        self.refreshButton.grid(row=1, column=0, padx=3, pady=3)
        self.activateButton.grid(row=1, column=1, padx=3, pady=3)
        self.quitButton.grid(row=1, column=2, padx=3, pady=3)

    def read(self):
        try:
            return self.serial.read()
        except:
            self.serial.close()
            quit()

    def write(self, data: bytes):
        try:
            self.serial.write(self.Config["SERIAL"]["SEND"] + data)
        except:
            self.serial.close()
            quit()

    def getPorts(self):
        from serial.tools.list_ports import comports

        li = [str(com) for com in comports()]
        if not li:
            li = ["无可用端口"]
            self.activateButton["state"] = "disabled"
        else:
            self.activateButton["state"] = "normal"
        last = self.portCombobox.get()
        self.portCombobox["values"] = li
        self.portCombobox.current(li.index(last) if last in li else 0)

    def toggleConnection(self):
        if self.activateButton["text"] == "连接" and self.startCOM():
            self.activateButton["text"] = "断开"
            self.portCombobox["state"] = self.refreshButton["state"] = self.quitButton["state"] = "disabled"
            self.camera.setActivate(True)
            self.adrc.setActivate(True)
            self.setstate.setActivate(True)
            self.scope.setActivate(True)
            self.remote.setActivate(True)
            self.patrol.setActivate(True)
        else:
            self.activateButton["text"] = "连接"
            self.portCombobox["state"] = self.refreshButton["state"] = self.quitButton["state"] = "normal"
            self.camera.setActivate(False)
            self.adrc.setActivate(False)
            self.setstate.setActivate(False)
            self.scope.setActivate(False)
            self.remote.setActivate(False)
            self.patrol.setActivate(False)
            self.serial.close()

    def startCOM(self):
        self.serial.port = self.portCombobox.get().split()[0]
        try:
            self.serial.open()
            return True
        except:
            self.getPorts()
            self.toggleConnection()
            return False

    def setActivate(self, activate: bool):
        self.activate += 1 if activate else -1
        state = ("disabled", "normal")
        self.portCombobox["state"] = self.refreshButton["state"] = self.activateButton["state"] = state[self.activate == 0]
        if activate:
            self.getPorts()

    def __onClose(self):
        if self.activateButton["text"] == "连接":
            self.Config.write()
            quit()


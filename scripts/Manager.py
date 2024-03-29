from .Main import Main


class Manager:
    def __init__(self, main: Main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)

        self.getConfig()
        self.setProperty()

    def getConfig(self):
        self.WINDOWON = self.main.Config["MANAGER"]["WINDOWON"]
        self.toplevels = [self.main.camera.root, self.main.adrc.root, self.main.pid.root, self.main.setstate.root, self.main.scope.root, self.main.remote.root, self.main.patrol.root]

    def setProperty(self) -> None:
        from tkinter.ttk import Button

        titles = ("摄像头", "ADRC", "PID", "电机控制", "虚拟示波器", "遥控器", "循迹控制")
        self.buttons = [Button(self.root, text=titles[i], command=lambda i=i: self.toggleVisibility(i)) for i in range(len(titles))]

        self.root.title("窗口管理")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        if "Manager" in self.main.Config["WINDOWPOSITION"]:
            self.root.geometry(self.main.Config["WINDOWPOSITION"]["Manager"])

        for i in range(len(titles)):
            self.buttons[i].pack(padx=3, pady=3)
            self.applyVisibility(i)

    def toggleVisibility(self, i):
        self.WINDOWON[i] ^= 1
        self.applyVisibility(i)

    def applyVisibility(self, i):
        if self.WINDOWON[i]:
            self.toplevels[i].deiconify()
        else:
            self.toplevels[i].withdraw()


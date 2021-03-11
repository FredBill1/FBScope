class Camera:
    def __init__(self, main) -> None:
        self.main = main
        self.getConfig()
        from os import listdir
        from numpy import zeros
        from tkinter import Toplevel

        self.root = Toplevel(self.main.root)
        self.img = zeros((self.HEIGHT, self.WIDTH))
        self.curCount = len(listdir(self.IMGDIR))

        self.transfering = False
        self.recording = False

        self.setProperty()

    def getConfig(self):
        self.CHECK = self.main.Config["SERIAL"]["CHECK"]
        self.WIDTH = self.main.Config["CAMERA"]["WIDTH"]
        self.HEIGHT = self.main.Config["CAMERA"]["HEIGHT"]
        self.ZOOM = self.main.Config["CAMERA"]["ZOOM"]
        self.IMGDIR = self.main.Config["CAMERA"]["DIR"]

    def setProperty(self) -> None:
        from tkinter import Canvas, StringVar
        from tkinter.ttk import LabelFrame, Button, Label

        self.imgFrame = LabelFrame(self.root, text="图像", labelanchor="nw")
        self.imgCanvas = Canvas(self.imgFrame, width=self.WIDTH * self.ZOOM, height=self.HEIGHT * self.ZOOM)
        self.startButton = Button(self.root, text="开始", state="disabled", command=self.toggleTransfer)
        self.shotButton = Button(self.root, text="拍照", command=self.shotImg)
        self.recordButton = Button(self.root, text="录制", state="disabled", command=self.toggleRecord)
        self.countStr = StringVar()
        self.countText = Label(self.root, textvariable=self.countStr, width=15)

        self.root.title("FBScope - 摄像头")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.imgFrame.pack(padx=3)
        self.imgCanvas.pack()
        self.startButton.pack(side="left", padx=3, pady=2)
        self.shotButton.pack(side="left", padx=3, pady=2)
        self.recordButton.pack(side="left", padx=3, pady=2)
        self.countText.pack(side="left", padx=3, pady=2, fill="x")

        self.showImg()
        self.showCount()

    def toggleTransfer(self):
        from threading import Thread

        if self.startButton["text"] == "开始":
            self.startButton["text"] = "停止"
            self.recordButton["state"] = "normal"
            self.transfering = True
            self.main.setActivate(False)
            self.main.scope.setActivate(False)
            Thread(target=self.transfer).start()
        else:
            self.startButton["text"] = "开始"
            self.recordButton["state"] = "disabled"
            self.transfering = False
            self.main.setActivate(True)
            self.main.scope.setActivate(True)

    def toggleRecord(self):
        if self.recordButton["text"] == "录制":
            self.recordButton["text"] = "终止"
            self.startButton["state"] = "disabled"
        else:
            self.recordButton["text"] = "录制"
            self.startButton["state"] = "normal"
        self.recording = not self.recording

    def showCount(self):
        self.countStr.set("照片数: %d" % self.curCount)

    def showImg(self):
        from cv2 import resize, INTER_NEAREST
        from PIL import Image
        from PIL.ImageTk import PhotoImage

        img = resize(self.img, (0, 0), fx=self.ZOOM, fy=self.ZOOM, interpolation=INTER_NEAREST)
        self.imgTk = PhotoImage(image=Image.fromarray(img))
        self.imgCanvas.create_image(0, 0, anchor="nw", image=self.imgTk)

    def shotImg(self):
        from cv2 import imwrite

        imwrite(self.IMGDIR + str(self.curCount) + ".png", self.img)
        self.curCount += 1
        self.showCount()

    def transfer(self):
        from numpy import frombuffer

        while self.transfering:
            buf = b"\x00\x00\x00\x00"
            while self.transfering and buf != self.CHECK:
                buf = (buf + self.main.read())[-4:]
            buf = b""
            while self.transfering and len(buf) < self.HEIGHT * self.WIDTH:
                buf += self.main.read()
            if self.transfering:
                self.img = frombuffer(buf, "uint8").reshape((self.HEIGHT, self.WIDTH))
                if self.recording:
                    self.shotImg()
                self.showImg()

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.startButton["state"] = state[activate]


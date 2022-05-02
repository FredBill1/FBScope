from FBPosApp import FBPosApp


if __name__ == "__main__":
    app = FBPosApp()
    app.registerRobot(30, color="red")
    app.registerRobot(31, color="green")
    app.registerRobot(32)
    app.mainloop()

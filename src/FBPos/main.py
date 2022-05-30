from FBPosApp import FBPosApp


if __name__ == "__main__":
    app = FBPosApp()
    ref_bot = app.registerRobot()
    cur_pose_bot = app.registerRobot(30, color="red")
    cur_target_bot = app.registerRobot(31, color="green")
    targets_scatter = app.registerScatter(32)
    app.mainloop()

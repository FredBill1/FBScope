import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import os, os.path
from FBWidgetCanvas import *
from FBWidgets import *
from FBWidgetTabs import *
from FBWidgetCmdTable import *

CFG_DIR = os.path.expanduser("~/.FBScope/panel")
os.makedirs(CFG_DIR, exist_ok=True)


# style = Style(theme="cosmo")
# root = style.master
root = tk.Tk()

# nb = ttk.Notebook(root)
# nb.pack(fill="both", expand=True)
# canvas = FBWidgetCanvas(nb)
# nb.add(canvas, text="Canvas")
# entry = canvas.createWidgetFromDict(
#     {"name": "testEntry", "type": "FBEntry", "pos": [10.0, 10.0], "data": {"text": "test1"}, "config": {},}
# )
# button = canvas.createWidgetFromDict(
#     {"name": "testButton", "type": "FBButton", "pos": [10.0, 50.0], "data": {}, "config": {"高度": 200},}
# )
# print(entry.toDict())


ttt = {
    "canvases": [
        {
            "name": "1",
            "cmds": [["新命令1", 1, 2], ["新命令2", 3, 4]],
            "widgets": [
                {
                    "name": "asdf",
                    "type": "FBButton",
                    "pos": [20.0, 17.0],
                    "data": {},
                    "config": {"宽度": "100", "高度": "30"},
                },
                {
                    "name": "fdas",
                    "type": "FBEntry",
                    "pos": [202.0, 44.0],
                    "data": {"text": "asdfsdfasdf"},
                    "config": {"宽度": "20"},
                },
            ],
        },
        {
            "name": "asdfasdf",
            "cmds": [],
            "widgets": [
                {
                    "name": "fff",
                    "type": "FBEntry",
                    "pos": [36.0, 12.0],
                    "data": {"text": "asdfasdfsdf"},
                    "config": {"宽度": "20"},
                },
                {
                    "name": "sss",
                    "type": "FBButton",
                    "pos": [132.0, 81.0],
                    "data": {},
                    "config": {"宽度": "100", "高度": "30"},
                },
            ],
        },
    ]
}

# nb = FBWidgetTabs(root)
nb = FBWidgetTabs.fromDict(root, ttt)
nb.pack(fill="both", expand=True)
# table = FBWidgetCmdTable.fromList(root, [["新命令1", "a", "1"], ["新命令2", "b", "2"], ["新命令3", "c", "3"]])

root.mainloop()
print(nb.toDict())

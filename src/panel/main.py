import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import os, os.path
from FBWidgetCanvas import *
from FBWidgets import *

CFG_DIR = os.path.expanduser("~/.FBScope/panel")
os.makedirs(CFG_DIR, exist_ok=True)


style = Style(theme="cosmo")
root = style.master

nb = ttk.Notebook(root)
nb.pack(fill="both", expand=True)
canvas = FBWidgetCanvas(nb)
nb.add(canvas, text="Canvas")
entry = canvas.createWidgetByDict(
    {"name": "testEntry", "type": "FBEntry", "pos": [10.0, 10.0], "data": {"text": "test1"}, "config": {},}
)
button = canvas.createWidgetByDict(
    {"name": "testButton", "type": "FBButton", "pos": [10.0, 50.0], "data": {}, "config": {"高度": 200},}
)
print(entry.toDict())
root.mainloop()

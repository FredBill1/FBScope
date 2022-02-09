import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import os, os.path
from FBWidgetCanvas import *

CFG_DIR = os.path.expanduser("~/.FBScope/pannel")
os.makedirs(CFG_DIR, exist_ok=True)


style = Style(theme="cosmo")
root = style.master

nb = ttk.Notebook(root)
nb.pack(fill="both", expand=True)
canvas = FBWidgetCanvas(nb)
nb.add(canvas, text="Canvas")

root.mainloop()

import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import os, os.path

CFG_DIR = os.path.expanduser("~/.FBScope/pannel")
os.makedirs(CFG_DIR, exist_ok=True)


style = Style(theme="darkly")
root = style.master


root.mainloop()

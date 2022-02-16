from tkinter import ttk
import tkinter as tk
from typing import Callable


class ValEntry(ttk.Entry):
    def __init__(self, pred: Callable[[str], bool], master=None, **kwargs):
        self._pred = pred
        self._preval = ""
        self._var = tk.StringVar()
        super().__init__(master, textvariable=self._var, validate="focusout", validatecommand=self._validator, **kwargs)
        self.get = self._var.get

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(value)
        self._preval = value

    def _validator(self, *_):
        cur = self.get()
        if self._pred(cur):
            self._preval = cur
        else:
            self.set(self._preval)
        return True


__all__ = ["ValEntry"]

if __name__ == "__main__":
    root = tk.Tk()

    def pred(s: str):
        return s.isdigit()

    ValEntry(pred, master=root, width=10).pack()
    ValEntry(pred, master=root, width=10).pack()
    root.mainloop()
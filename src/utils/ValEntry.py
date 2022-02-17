import ttkbootstrap as ttk
import tkinter as tk
from typing import Callable, Optional


class ValEntry(ttk.Entry):
    def __init__(
        self,
        pred: Callable[[str], bool],
        master=None,
        text: Optional[str] = None,
        textvariable: Optional[tk.StringVar] = None,
        **kwargs
    ):
        self._pred = pred
        self._preval = ""
        self._var = tk.StringVar() if textvariable is None else textvariable
        if text is not None:
            self._var.set(text)
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

    def bind(self, event, func, add=None):
        def wrapper(arg):
            self._validator()
            return func(arg)

        super().bind(event, wrapper, add)

    @staticmethod
    def type_validator(Type: callable) -> Callable[[str], bool]:
        def wrapper(s: str) -> bool:
            try:
                Type(s)
                return True
            except:
                return False

        return wrapper


__all__ = ["ValEntry"]

if __name__ == "__main__":
    root = tk.Tk()

    def pred(s: str):
        return s.isdigit()

    ValEntry(pred, master=root, width=10).pack()
    ValEntry(pred, master=root, width=10).pack()
    root.mainloop()

def recursiveSetState(widget, disable: bool):
    for child in widget.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ("Frame", "Labelframe"):
            child.configure(state="disable" if disable else "!disable")
        else:
            recursiveSetState(child)


def recursiveConfigure(widget, func: callable):
    func(widget)
    for child in widget.winfo_children():
        recursiveConfigure(child, func)


__all__ = ["recursiveSetState", "recursiveConfigure"]


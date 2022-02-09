def recursiveSetState(widget, disable: bool):
    for child in widget.winfo_children():
        wtype = child.winfo_class()
        if wtype in ("Frame", "Labelframe"):
            recursiveSetState(child)
        else:
            try:
                child.configure(state="disable" if disable else "!disable")
            except:
                pass


def recursiveConfigure(widget, func: callable):
    func(widget)
    for child in widget.winfo_children():
        recursiveConfigure(child, func)


__all__ = ["recursiveSetState", "recursiveConfigure"]


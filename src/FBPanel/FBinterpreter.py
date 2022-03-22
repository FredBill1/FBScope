from typing import TYPE_CHECKING, Optional, List
from tkinter import messagebox
from FBFunc import *

if TYPE_CHECKING:
    from FBWidgetCanvas import FBWidgetCanvas

MAX_RECURSION_DEPTH = 20
AS_FLOAT_CHECKSUM = True


def interpretCmd(canvas: "FBWidgetCanvas", cmd: str, depth: int = 0) -> Optional[bytes]:
    if depth >= MAX_RECURSION_DEPTH:
        messagebox.showerror("执行错误", f"递归深度超过{MAX_RECURSION_DEPTH}层", parent=canvas)
        return None

    def getVar(var: List[str]) -> list:
        def getValue(variable: str):
            if variable.startswith("("):
                if not variable.endswith(")"):
                    messagebox.showerror("错误的变量", f"`{variable}`应以`)`结尾", parent=canvas)
                    return None
                try:
                    return eval(variable[1:-1])
                except:
                    messagebox.showerror("错误的变量", f"`{variable}`无法被解析", parent=canvas)
                    return None
            variable = variable.split(".")
            if len(variable) == 1:
                messagebox.showerror("错误的变量", f"`{variable[0]}`没有用`.`指定属性, 或应使用`()`将其指定为字面常量", parent=canvas)
                return None
            elif len(variable) == 2:
                name, attr = variable
                if name.startswith("<") and name.endswith(">"):
                    if len(name) == 3 and "a" <= name[1] <= "z":
                        if attr == "pressed":
                            return canvas._pressed[ord(name[1]) - ord("a")]
                        elif attr == "released":
                            return not canvas._pressed[ord(name[1]) - ord("a")]
                        else:
                            messagebox.showerror(
                                "错误的属性", f"按键`{name}`没有属性`{attr}`\n应为`pressed`或`released`", parent=canvas
                            )
                            return None
                    else:
                        messagebox.showerror("错误的按键", f"不支持`{name}`", parent=canvas)
                        return None
                else:
                    if name in canvas.widgets:
                        widget = canvas.widgets[name]
                        if attr in widget.data:
                            return widget.data[attr].get()
                        else:
                            messagebox.showerror("错误的属性", f"组件`{name}`没有属性{attr}", parent=canvas)
                            return None
                    else:
                        messagebox.showerror("错误的组件", f"组件`{name}`不存在", parent=canvas)
                        return None
            else:
                messagebox.showerror("错误的变量", "变量`{}`不合法, `.`应该且只应出现一次".format(".".join(variable)), parent=canvas)
                return None

        res = []
        for v in var:
            res.append(getValue(v))
            if res[-1] is None:
                return None
        return res

    def evaluate(command: List[str], var: list) -> Optional[bytes]:
        def getValue(cmd: str, var: list) -> Optional[bytes]:
            if cmd.startswith("%"):
                res = b""
                for fmt in cmd[1:].split("%"):
                    fmt = fmt.strip()
                    if not var:
                        messagebox.showerror("错误的变量", "变量数量少于指令所需数量", parent=canvas)
                        return None
                    cur = var.pop()
                    try:
                        if fmt == "b":
                            res += as_bytes(cur)
                        elif fmt == "s":
                            res += as_str(cur)
                        elif fmt == "f":
                            res += as_float(cur, 4, AS_FLOAT_CHECKSUM)
                        elif fmt == "lf":
                            res += as_float(cur, 8, AS_FLOAT_CHECKSUM)
                        else:
                            messagebox.showerror("错误的指令", f"类型`%{fmt}`不存在", parent=canvas)
                            return None
                    except:
                        messagebox.showerror("错误的变量", f"`{cur}`无法被转换为`%{fmt}`", parent=canvas)
                        return None
                return res
            elif cmd.startswith("#"):
                cmd = cmd[1:]
                if cmd in canvas.cmdDict:
                    cmd, var = canvas.cmdDict[cmd]
                    return interpretCmd(canvas, "$$".join(("", cmd, var)), depth + 1)
            elif cmd.startswith("!"):
                i = cmd.find("(")
                if i == -1 or not cmd.endswith(")"):
                    messagebox.showerror("错误的命令", f"函数调用语句`{cmd}`应出现`(`且以`)`结尾", parent=canvas)
                    return None
                if not 1 == cmd.count("(") == cmd.count(")"):
                    messagebox.showerror("错误的命令", f"函数调用语句`{cmd}`中`(`与`)`均应仅出现一次", parent=canvas)
                    return None
                name = cmd[1:i]
                if name not in FBFUNC_DICT:
                    messagebox.showerror("错误的调用", f"函数`{name}`不存在", parent=canvas)
                    return None
                param = cmd[i + 1 : -1]
                if not param:
                    messagebox.showerror("错误的调用", f"函数{name}没有指定参数数量", parent=canvas)
                    return None
                try:
                    var_cnt = int(param)
                except:
                    messagebox.showerror("错误的调用", f"函数{name}的参数数量应为整数", parent=canvas)
                    return None
                if var_cnt > len(var):
                    messagebox.showerror("错误的变量", f"变量数量少于指令所需数量", parent=canvas)
                    return None
                tmp = [var.pop() for _ in range(var_cnt)]
                try:
                    return FBFUNC_DICT[name](*tmp)
                except Exception as e:
                    messagebox.showerror("错误的调用", f"函数`{name}`以{tmp}为参数调用时出错\n{e}", parent=canvas)
                    return None
            else:
                messagebox.showerror("错误的命令", f"命令`{cmd}`必须以`%``!``#`之一开头", parent=canvas)
                return None

        var.reverse()
        res = []
        for cmd in command:
            res.append(getValue(cmd, var))
            if res[-1] is None:
                return None
        if var:
            messagebox.showerror("错误的变量", "变量数量多于指令所需数量", parent=canvas)
            return None
        return b"".join(res)

    _, command, variables = (s.strip() for s in cmd.split("$$"))
    if not command:
        messagebox.showerror("错误的命令", "命令不能为空", parent=canvas)
        return None
    var = getVar([v.strip() for v in variables.split(";") if v.split()] if variables else [])
    if var is None:
        return None
    return evaluate([c.strip() for c in command.split(";") if c.strip()], var)


__all__ = ["interpretCmd"]


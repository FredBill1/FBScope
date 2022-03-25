import struct


def as_bytes(x: int) -> bytes:
    if isinstance(x, bytes):
        return x
    if isinstance(x, str):
        if x.startswith("0x"):
            return bytes.fromhex(x[2:])
        return as_bytes(int(x))
    if isinstance(x, int):
        x = hex(x)[2:]
        return bytes.fromhex("0" + x if len(x) & 1 else x)
    raise TypeError(f"`{x}`的类型应为int,bytes或str, 而不是{type(x)}")


def as_str(s) -> bytes:
    return str(s).encode("ascii")


def as_float(x, bits: int = 4, check: bool = True) -> bytes:
    if bits == 4:
        fmt = "f"
    elif bits == 8:
        fmt = "d"
    else:
        raise ValueError(f"`{x}`转换为浮点数的位数必须为`4`或`8`, 而不是`{bits}`")
    res = struct.pack(fmt, float(x))
    return res + bytes([sum(res) & 255]) if check else res


__all__ = ["as_bytes", "as_str", "as_float"]

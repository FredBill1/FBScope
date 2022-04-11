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


def to_bitset(*args) -> bytes:
    AVAILABLE = [1, 2, 4, 8]
    need = (len(args) + 7) >> 3
    for v in AVAILABLE:
        if v >= need:
            need = v
            break
    else:
        raise ValueError(f"转换成二进制串的参数必须少于64个, 而不是{len(args)}")
    res = 0
    for v in reversed(args):
        if isinstance(v, str):
            v = int(bool(eval(v)))
        else:
            v = int(v)
        res = res << 1 | v

    return res.to_bytes(need, "big")


__all__ = ["as_bytes", "as_str", "as_float", "to_bitset"]

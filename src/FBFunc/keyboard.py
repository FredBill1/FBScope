def two_key(x, y) -> bytes:
    if isinstance(x, str):
        x = repr(x)
    if isinstance(y, str):
        y = repr(y)
    res = 0
    if x != y:
        res = 1 if x else 2
    return res.to_bytes(1, "big")


__all__ = ["two_key"]

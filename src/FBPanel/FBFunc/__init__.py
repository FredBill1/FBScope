from typing import Dict, List
from .basics import as_bytes, as_str, as_float

FBFUNC_LIST: List[callable] = [as_bytes, as_str, as_float]
FBFUNC_DICT: Dict[str, callable] = {
    "as_bytes": as_bytes,
    "as_str": as_str,
    "as_float": as_float,
}


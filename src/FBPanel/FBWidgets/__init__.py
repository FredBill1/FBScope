from typing import Dict, Any, List

from .FBWidget import FBWidget
from .FBButton import FBButton
from .FBEntry import FBEntry
from .FBFloatEntry import FBFloatEntry
from .FBScaleEntry import FBScaleEntry

FBWIDGET_LIST: List[FBWidget] = [FBButton, FBEntry, FBFloatEntry, FBScaleEntry]
FBWIDGET_DICT: Dict[Any, FBWidget] = {cls.__name__: cls for cls in FBWIDGET_LIST}

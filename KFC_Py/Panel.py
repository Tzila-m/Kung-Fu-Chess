from __future__ import annotations
import cv2, numpy as np
from typing import Tuple, TYPE_CHECKING  # <= שימו לב

if TYPE_CHECKING:
    from GameDisplay import GameDisplay  # רק לבדיקת טיפוסים בזמן קומפילציה

class Panel:
    """
    מחלקה בסיסית: כל Panel מחזיק מצביע אל GameDisplay
    ולכן יכול לשאוב margin, sidebar_w, גודל‑חלון, וכו'.
    """
    def __init__(self, display: "GameDisplay", size: Tuple[int, int]):
        self.display = display          # <‑‑‑‑‑‑‑‑‑‑‑‑ NEW
        self.size = size                # (h, w)

    def draw(self, canvas: np.ndarray):
        raise NotImplementedError

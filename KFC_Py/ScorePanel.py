from __future__ import annotations
import cv2, numpy as np
from typing import Tuple, TYPE_CHECKING  # <= שימו לב

if TYPE_CHECKING:
    from GameDisplay import GameDisplay  # רק לבדיקת טיפוסים בזמן קומפילציה
from Panel import Panel

class ScorePanel(Panel):
    def __init__(self, display: "GameDisplay",
                 title: str, score_obs, is_left: bool = True):
        super().__init__(display, (40, display.sidebar_w))
        self.title, self.score_obs, self.is_left = title, score_obs, is_left

    def draw(self, canvas):
        m   = self.display.margin
        h,_ = self.size
        y0  = m[0]
        x0  = m[3] if self.is_left else canvas.shape[1] - m[1] - self.size[1]
        text = f"{self.title}  |  Score: {self.score_obs.get_score()}"
        cv2.putText(canvas, text, (x0+10, y0+26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0,0,0), 2)

from __future__ import annotations
import cv2, numpy as np
from typing import Tuple, TYPE_CHECKING  # <= שימו לב

if TYPE_CHECKING:
    from GameDisplay import GameDisplay  # רק לבדיקת טיפוסים בזמן קומפילציה
from Panel import Panel

class MovesPanel(Panel):
    ROW_H = 22
    def __init__(self, display: "GameDisplay",
                 moves_obs, is_left: bool = True):
        super().__init__(display, (MovesPanel.ROW_H*11, display.sidebar_w))
        self.moves_obs, self.is_left = moves_obs, is_left

    def draw(self, canvas):
        m   = self.display.margin
        x0  = m[3] if self.is_left else canvas.shape[1] - m[1] - self.size[1]
        y0  = m[0] + 60

        # כותרת
        cv2.rectangle(canvas, (x0, y0-25),
                      (x0+self.size[1], y0), (0,0,0), cv2.FILLED)
        cv2.putText(canvas, "# Piece Move  Time", (x0+5, y0-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)

        # 10 המהלכים האחרונים
        for i, mv in enumerate(self.moves_obs.get_history()[-10:], 1):
            line = (f"{i:2d} {mv['piece']:^5} "
                    f"{mv['from']}→{mv['to']}  {mv['time']}")
            cv2.putText(canvas, line,
                        (x0+5, y0 + i*MovesPanel.ROW_H - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 1)

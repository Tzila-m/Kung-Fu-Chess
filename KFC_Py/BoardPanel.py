from __future__ import annotations
import cv2, numpy as np
from typing import Tuple, TYPE_CHECKING
from Panel import Panel

if TYPE_CHECKING:
    from GameDisplay import GameDisplay
    from Board import Board

class BoardPanel(Panel):
    def __init__(self, display: "GameDisplay", game):
        h, w = game.board.img.img.shape[:2]
        super().__init__(display, (h, w))
        self.game = game

    def draw(self, canvas):
        m  = self.display.margin
        x0 = m[3] + self.display.sidebar_w
        y0 = m[0]

        board_img = (
            self.game.curr_board.img.img
            if getattr(self.game, "curr_board", None) is not None
            else self.game.board.img.img
        )

        canvas[y0:y0+self.size[0], x0:x0+self.size[1]] = board_img[..., :3]
       
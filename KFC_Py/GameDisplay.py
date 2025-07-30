from __future__ import annotations
from typing import Tuple, List
import cv2, numpy as np

from Panel      import Panel
from BoardPanel import BoardPanel
from ScorePanel import ScorePanel
from MovesPanel import MovesPanel


class GameDisplay:
    def __init__(
        self,
        game,                                   # <-- מקבלים את‑game כולו
        sidebar_w: int = 230,
        margin: Tuple[int,int,int,int] = (20,20,20,20),
        bg_color: Tuple[int,int,int] = (193,157,122)
    ):
        self.game        = game
        self.margin      = margin
        self.sidebar_w   = sidebar_w
        self.bg_color    = bg_color

        # -------- 1) יצירת פאנלים --------
        self.board_panel  = BoardPanel(self, game)          # לוח חי
        self.score_panel1 = ScorePanel(self, "White",
                                       game.score_observer_1,  is_left=True)
        self.score_panel2 = ScorePanel(self, "Black",
                                       game.score_observer_2,  is_left=False)
        self.moves_panel1 = MovesPanel(self, game.move_history_1, is_left=True)
        self.moves_panel2 = MovesPanel(self, game.move_history_2, is_left=False)

        # -------- 2) רישום ברשימה --------
        self.panels: List[Panel] = [
            self.board_panel,
            self.score_panel1, self.score_panel2,
            self.moves_panel1, self.moves_panel2,
        ]

        # -------- 3) רישום מאזינים --------
        for obs in (
            game.score_observer_1, game.score_observer_2,
            game.move_history_1,   game.move_history_2
        ):
            if hasattr(obs, "add_listener"):
                obs.add_listener(lambda *_: self.refresh())

        # -------- 4) ציור ראשוני ----------
        self.refresh()

    # ---------- עזר ----------
    def _build_canvas(self) -> np.ndarray:
        h, w = self.board_panel.size
        h += self.margin[0] + self.margin[2]
        w += self.margin[3] + self.margin[1] + self.sidebar_w * 2
        return np.full((h, w, 3), self.bg_color, dtype=np.uint8)

    def refresh(self):
        canvas = self._build_canvas()
        for p in self.panels:
            p.draw(canvas)
        cv2.imshow("Two‑Player Chess Game", canvas)
        cv2.waitKey(1)

    def show(self):
        self.refresh()

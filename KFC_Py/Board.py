from dataclasses import dataclass

import numpy as np

from img import Img

@dataclass
class Board:
    cell_H_pix: int  # cell height in pixels
    cell_W_pix: int  # cell width in pixels
    W_cells: int     # num cells in width
    H_cells: int     # num cells in height
    img: Img         # image of the board
    cell_H_m: float = 1.0  # cell height in meters (default 1.0 for back-compat)
    cell_W_m: float = 1.0  # cell width  in meters (default 1.0 for back-compat)

    # convenience, not required by dataclass
    def clone(self) -> "Board":
        return Board(self.cell_H_pix, self.cell_W_pix,
                     self.W_cells,    self.H_cells,
                     self.img.copy())

    def show(self):
        self.img.show()

    # ──────────────────────────────────────────────────────────────
    def m_to_cell(self, pos_m: tuple[float, float]) -> tuple[int, int]:
        """Convert *(x, y)* in metres to board cell *(row, col)*."""
        x_m, y_m = pos_m
        col = int(round(x_m / self.cell_W_m))
        row = int(round(y_m / self.cell_H_m))
        return row, col

    def cell_to_m(self, cell: tuple[int, int]) -> tuple[float, float]:
        """Convert a cell *(row, col)* to its top-left corner in metres."""
        r, c = cell
        return c * self.cell_W_m, r * self.cell_H_m

    def m_to_pix(self, pos_m: tuple[float, float]) -> tuple[int, int]:
        """Convert *(x, y)* in metres to pixel coordinates."""
        x_m, y_m = pos_m
        x_px = int(round(x_m / self.cell_W_m * self.cell_W_pix))
        y_px = int(round(y_m / self.cell_H_m * self.cell_H_pix))
        return x_px, y_px
        # Board.py  – בתוך class Board

    def render(self) -> "np.ndarray":
        """
        מחזיר תמונת‑לוח עדכנית (רקע + חיילים חיים).
        מניח self.img.img = רקע RGBA
        self.pieces = iterable של Piece עם .sprite rgba ו‑.cell = (row,col)
        """
        frame = self.img.img.copy()
        for p in self.pieces:
            if getattr(p, "is_captured", False):
                continue
            r, c = p.cell
            y = r * self.cell_H_pix
            x = c * self.cell_W_pix
            h, w = p.sprite.shape[:2]
            alpha = p.sprite[..., 3:] / 255.0
            roi   = frame[y:y+h, x:x+w, :3]
            frame[y:y+h, x:x+w, :3] = (
                roi * (1 - alpha) + p.sprite[..., :3] * alpha
            ).astype("uint8")
        return frame



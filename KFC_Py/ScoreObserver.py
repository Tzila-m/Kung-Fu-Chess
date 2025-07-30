class ScoreObserver:
    PIECE_POINTS = {
        "P": 1,   # Pawn
        "N": 3,   # Knight
        "B": 3,   # Bishop
        "R": 5,   # Rook
        "Q": 9,   # Queen
        "K": 20   # King
    }
    def __init__(self):
        self._score = 0
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def notify(self):
        for listener in self._listeners:
            listener(self._score)

    def add_points(self, points):
        self._score += points
        self.notify()

    def add_piece_points(self, piece_type):
        """
        Add points according to the piece type (first letter, e.g. 'P', 'N', ...)
        """
        points = self.PIECE_POINTS.get(piece_type[0].upper(), 0)
        self.add_points(points)

    def reset(self):
        self._score = 0
        self.notify()

    def get_score(self):
        return self._score

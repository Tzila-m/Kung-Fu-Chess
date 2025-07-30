class MoveHistoryObserver:
    def __init__(self):
        self.history = []  # כל מהלך: (piece, from_cell, to_cell, time)
        self.listeners = []

    def add_move(self, piece, from_cell, to_cell, move_time=None):
        if piece is not None:  # Ensure valid moves
            self.history.append({
                'piece': piece,
                'from': from_cell,
                'to': to_cell,
                'time': move_time
            })
            for listener in self.listeners:
                listener(self.history)

    def get_history(self):
        return self.history

    def add_listener(self, listener):
        self.listeners.append(listener)

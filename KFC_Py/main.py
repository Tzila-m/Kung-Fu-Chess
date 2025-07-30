import logging
from GameFactory import create_game
from GraphicsFactory import ImgFactory
from datetime import timedelta


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    game = create_game("../pieces", ImgFactory())
    def print_scores(_=None):
        print(f"White Score: {game.score_observer_1.get_score()} | Black Score: {game.score_observer_2.get_score()}")
    # הדפסה ראשונית
    print_scores()
    # הדפסה אוטומטית בכל שינוי ניקוד
    game.score_observer_1.add_listener(print_scores)
    game.score_observer_2.add_listener(print_scores)
    def format_row(index, piece, from_pos, to_pos, time):
        from_pos_str = f"({from_pos[0]}, {from_pos[1]})"
        to_pos_str = f"({to_pos[0]}, {to_pos[1]})"
        time_str = str(timedelta(milliseconds=time))  # Convert milliseconds to HH:MM:SS.mmm
        return f"{index:<3} | {piece:<10} | {from_pos_str:<10} -> {to_pos_str:<10} | {time_str:<15}"

    def print_moves(_=None):
        print("White Moves:")
        print("#   | Piece      | From  -> To    | Time")
        print("-" * 40)
        for i, move in enumerate(game.move_history_1.get_history(), 1):
            if tuple(move['from']) != tuple(move['to']) and move['piece'] is not None:  # Ensure valid moves
                print(format_row(i, move['piece'], move['from'], move['to'], move['time']))
        print("Black Moves:")
        print("#   | Piece      | From  -> To    | Time")
        print("-" * 40)
        for i, move in enumerate(game.move_history_2.get_history(), 1):
            if tuple(move['from']) != tuple(move['to']) and move['piece'] is not None:  # Ensure valid moves
                print(format_row(i, move['piece'], move['from'], move['to'], move['time']))
        print("-" * 40)
    # הדפסה אוטומטית של היסטוריית מהלכים
    game.move_history_1.add_listener(print_moves)
    game.move_history_2.add_listener(print_moves)

    print([attr for attr in dir(game.board) if not attr.startswith("__")])

    game.run()


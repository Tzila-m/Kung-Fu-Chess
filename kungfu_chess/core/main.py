
import logging
from .gamefactory import create_game
from .graphicsfactory import ImgFactory

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    game = create_game("../pieces", ImgFactory())
    game.run()


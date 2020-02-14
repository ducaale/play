import random
import play.position
from . import cfg

def random_number(lowest=0, highest=100):
    # if user supplies whole numbers, return whole numbers
    if type(lowest) == int and type(highest) == int:
        return random.randint(lowest, highest)
    else:
        # if user supplied any floats, return decimals
        return round(random.uniform(lowest, highest), 2)


def random_color():
    return (random_number(0, 255), random_number(0, 255), random_number(0, 255))


def random_position():
    """
    Returns a random position on the screen. A position has an `x` and `y` e.g.:
        position = play.random_position()
        sprite.x = position.x
        sprite.y = position.y

    or equivalently:
        sprite.go_to(play.random_position())
    """
    return play.position.Position(
        random_number(cfg.screen.left, cfg.screen.right),
        random_number(cfg.screen.bottom, cfg.screen.top))

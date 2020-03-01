import math
from .utils import point_touching_sprite, make_async

class Mouse(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self._is_clicked = False
        self._when_clicked_callbacks = []
        self._when_click_released_callbacks = []

    @property
    def is_clicked(self):
        # this is a property instead of a method because if a new programmer does:
        #    if play.mouse.is_clicked: # <-- forgetting parentheses causes bad behavior
        #        ...
        # and is_clicked is a method (they forgot the parens), then it will always
        # return True. Better to eliminate the need for parens.
        return self._is_clicked

    def is_touching(self, other):
        return point_touching_sprite(self, other)

    # @decorator
    def when_clicked(self, func):
        async_callback = make_async(func)
        self._when_clicked_callbacks.append(async_callback)
        return async_callback

    # @decorator
    def when_click_released(self, func):
        async_callback = make_async(func)
        self._when_click_released_callbacks.append(async_callback)
        return async_callback

    def distance_to(self, x=None, y=None):
        assert (x is not None)

        try:
            # x can either by a number or a sprite. If it's a sprite:
            x = x.x
            y = x.y
        except AttributeError:
            x = x
            y = y

        dx = self.x - x
        dy = self.y - y

        return math.sqrt(dx**2 + dy**2)

mouse = Mouse()

# @decorator
def when_mouse_clicked(func):
    return mouse.when_clicked(func)


# @decorator
def when_click_released(func):
    return mouse.when_click_released(func)

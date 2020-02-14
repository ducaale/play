import pygame
from . import physics

class Screen(object):
    def __init__(self, width=800, height=600):
        self._width = width
        self._height = height

        physics.create_walls(self)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, _width):
        self._width = _width

        physics.remove_walls()
        physics.create_walls(self)

        pygame.display.set_mode((self._width, self._height))

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, _height):
        self._height = _height

        physics.remove_walls()
        physics.create_walls(self)

        pygame.display.set_mode((self._width, self._height))

    @property
    def top(self):
        return self.height / 2

    @property
    def bottom(self):
        return self.height / -2

    @property
    def left(self):
        return self.width / -2

    @property
    def right(self):
        return self.width / 2
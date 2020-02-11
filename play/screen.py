class _Screen(object):
    def __init__(self, width=800, height=600):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, _width):
        self._width = _width

        _remove_walls()
        _create_walls()

        pygame.display.set_mode((self._width, self._height))

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, _height):
        self._height = _height

        _remove_walls()
        _create_walls()

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

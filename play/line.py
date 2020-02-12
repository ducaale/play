import pygame
import math
from .sprite import Sprite 
from .play import all_sprites
from .color import color_name_to_rgb

class Line(Sprite):
    def __init__(self, color='black', x=0, y=0, length=None, angle=None,
                 thickness=1, x1=None, y1=None, transparency=100, size=100):
        self._x = x
        self._y = y
        self._color = color
        self._thickness = thickness

        # can set either (length, angle) or (x1,y1), otherwise a default is used
        if length is not None and angle is not None:
            self._length = length
            self._angle = angle
            self._x1, self._y1 = self._calc_endpoint()
        elif x1 is not None and y1 is not None:
            self._x1 = x1
            self._y1 = y1
            self._length, self._angle = self._calc_length_angle()
        else:
            # default values
            self._length = length or 100
            self._angle = angle or 0
            self._x1, self._y1 = self._calc_endpoint()

        self._transparency = transparency
        self._size = size
        self._is_hidden = False
        self._is_clicked = False
        self.physics = None

        self._when_clicked_callbacks = []

        self._compute_primary_surface()

        all_sprites.append(self)

    def clone(self):
        return self.__class__(
            color=self.color,
            length=self.length,
            thickness=self.thickness,
            **self._common_properties())

    def _compute_primary_surface(self):
        # Make a surface that just contains the line and no white-space around the line.
        # If line isn't horizontal, this surface will be drawn rotated.
        width = self.length
        height = self.thickness + 1

        self._primary_pygame_surface = pygame.Surface((width, height),
                                                      pygame.SRCALPHA)
        # self._primary_pygame_surface.set_colorkey((255,255,255, 255)) # set background to transparent

        # # @hack
        # if self.thickness == 1:
        #     pygame.draw.aaline(self._primary_pygame_surface, _color_name_to_rgb(self.color), (0,1), (width,1), True)
        # else:
        #     pygame.draw.line(self._primary_pygame_surface, _color_name_to_rgb(self.color), (0,_math.floor(height/2)), (width,_math.floor(height/2)), self.thickness)

        # line is actually drawn in _game_loop because coordinates work different

        self._should_recompute_primary_surface = False
        self._compute_secondary_surface(force=True)

    def _compute_secondary_surface(self, force=False):
        self._secondary_pygame_surface = self._primary_pygame_surface.copy()

        if force or self._transparency != 100:
            self._secondary_pygame_surface.set_alpha(
                round((self._transparency / 100.) * 255))

        self._should_recompute_secondary_surface = False

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, _color):
        self._color = _color
        self._should_recompute_primary_surface = True

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, _thickness):
        self._thickness = _thickness
        self._should_recompute_primary_surface = True

    def _calc_endpoint(self):
        radians = math.radians(self._angle)
        return self._length * math.cos(
            radians) + self.x, self._length * math.sin(radians) + self.y

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, _length):
        self._length = _length
        self._x1, self._y1 = self._calc_endpoint()
        self._should_recompute_primary_surface = True

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, _angle):
        self._angle = _angle
        self._x1, self._y1 = self._calc_endpoint()
        if self.physics:
            self.physics._pymunk_body.angle = math.radians(_angle)

    def _calc_length_angle(self):
        dx = self.x1 - self.x
        dy = self.y1 - self.y

        # TODO: this doesn't work at all
        return math.sqrt(dx**2 + dy**2), math.degrees(math.atan2(dy, dx))

    @property
    def x1(self):
        return self._x1

    @x1.setter
    def x1(self, _x1):
        self._x1 = _x1
        self._length, self._angle = self._calc_length_angle()
        self._should_recompute_primary_surface = True

    @property
    def y1(self):
        return self._y1

    @y1.setter
    def y1(self, _y1):
        self._angle = _y1
        self._length, self._angle = self._calc_length_angle()
        self._should_recompute_primary_surface = True


def new_line(color='black', x=0, y=0, length=None, angle=None, thickness=1, x1=None, y1=None, transparency=100, size=100):
    return Line(color=color, x=x, y=y, length=length, angle=angle, thickness=thickness, x1=x1, y1=y1, transparency=transparency, size=size)
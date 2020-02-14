__version__ = '0.0.23'

from .box import new_box
from .sprite import new_image, when_sprite_clicked
from .text import new_text
from .circle import new_circle
from .line import new_line
from .background import set_backdrop

from .play import (
    repeat_forever,
    when_program_starts,
    timer,
    repeat,
    animate,
    start_program
)

from .mouse import mouse, when_mouse_clicked, when_click_released
from .keyboard import (
    key_is_pressed,
    when_key_pressed,
    when_any_key_pressed,
    when_key_released,
    when_any_key_released
)

from .physics import set_gravity
from .cfg import screen, all_sprites, backdrop
from .random import random_number, random_color, random_position
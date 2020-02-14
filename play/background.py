from .color import color_name_to_rgb
from . import cfg

def set_backdrop(color_or_image_name):
    # I chose to make set_backdrop a function so that we can give
    # good error messages at the call site if a color isn't recognized.
    # If we didn't have a function and just set backdrop like this:
    #
    #       play.backdrop = 'gbluereen'
    #
    # then any errors resulting from that statement would appear somewhere
    # deep in this library instead of in the user code.

    # this line will raise a useful exception
    color_name_to_rgb(color_or_image_name)
    cfg.backdrop = color_or_image_name

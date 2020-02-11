import os as _os
import logging as _logging
import warnings as _warnings
import inspect as _inspect

import pygame
import pygame.gfxdraw
import pymunk as _pymunk

import asyncio as _asyncio
import random as _random
import math as _math
from statistics import mean as _mean

from .keypress import pygame_key_to_name as _pygame_key_to_name # don't pollute user-facing namespace with library internals
from .color import color_name_to_rgb as _color_name_to_rgb
from .exceptions import Oops, Hmm

pygame.init()

screen = _Screen()
_pygame_display = pygame.display.set_mode((screen.width, screen.height), pygame.DOUBLEBUF)
pygame.display.set_caption("Python Play")

all_sprites = []

mouse = _Mouse()

_keys_pressed_this_frame = []
_keys_released_this_frame = []
_keys_to_skip = (pygame.K_MODE,)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])

_loop = _asyncio.get_event_loop()
_loop.set_debug(False)

_clock = pygame.time.Clock()
def _game_loop():
    _keys_pressed_this_frame.clear() # do this instead of `_keys_pressed_this_frame = []` to save a tiny bit of memory
    _keys_released_this_frame.clear()
    click_happened_this_frame = False
    click_release_happened_this_frame = False

    _clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_q and (
                pygame.key.get_mods() & pygame.KMOD_META or pygame.key.get_mods() & pygame.KMOD_CTRL
        )):
            # quitting by clicking window's close button or pressing ctrl+q / command+q
            _loop.stop()
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_happened_this_frame = True
            mouse._is_clicked = True
        if event.type == pygame.MOUSEBUTTONUP:
            click_release_happened_this_frame = True
            mouse._is_clicked = False
        if event.type == pygame.MOUSEMOTION:
            mouse.x, mouse.y = (event.pos[0] - screen.width/2.), (screen.height/2. - event.pos[1])
        if event.type == pygame.KEYDOWN:
            if not (event.key in _keys_to_skip):
                name = _pygame_key_to_name(event)
                _pressed_keys[event.key] = name
                _keys_pressed_this_frame.append(name)
        if event.type == pygame.KEYUP:
            if not (event.key in _keys_to_skip) and event.key in _pressed_keys:
                _keys_released_this_frame.append(_pressed_keys[event.key])
                del _pressed_keys[event.key]



    ############################################################
    # @when_any_key_pressed and @when_key_pressed callbacks
    ############################################################
    for key in _keys_pressed_this_frame:
        for callback in _keypress_callbacks:
            if not callback.is_running and (callback.keys is None or key in callback.keys):
                _loop.create_task(callback(key))

    ############################################################
    # @when_any_key_released and @when_key_released callbacks
    ############################################################
    for key in _keys_released_this_frame:
        for callback in _keyrelease_callbacks:
            if not callback.is_running and (callback.keys is None or key in callback.keys):
                _loop.create_task(callback(key))


    ####################################
    # @mouse.when_clicked callbacks
    ####################################
    if click_happened_this_frame and mouse._when_clicked_callbacks:
        for callback in mouse._when_clicked_callbacks:
            _loop.create_task(callback())

    ########################################
    # @mouse.when_click_released callbacks
    ########################################
    if click_release_happened_this_frame and mouse._when_click_released_callbacks:
        for callback in mouse._when_click_released_callbacks:
            _loop.create_task(callback())

    #############################
    # @repeat_forever callbacks
    #############################
    for callback in _repeat_forever_callbacks:
        if not callback.is_running:
            _loop.create_task(callback())

    #############################
    # physics simulation
    #############################
    _loop.call_soon(_simulate_physics)


    # 1.  get pygame events
    #       - set mouse position, clicked, keys pressed, keys released
    # 2.  run when_program_starts callbacks
    # 3.  run physics simulation
    # 4.  compute new pygame_surfaces (scale, rotate)
    # 5.  run repeat_forever callbacks
    # 6.  run mouse/click callbacks (make sure more than one isn't running at a time)
    # 7.  run keyboard callbacks (make sure more than one isn't running at a time)
    # 8.  run when_touched callbacks
    # 9.  render background
    # 10. render sprites (with correct z-order)
    # 11. call event loop again



    _pygame_display.fill(_color_name_to_rgb(backdrop))

    # BACKGROUND COLOR
    # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
    #       does not support fill() on OpenGL surfaces
    # gl.glClearColor(_background_color[0], _background_color[1], _background_color[2], 1)
    # gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    for sprite in all_sprites:

        sprite._is_clicked = False

        if sprite.is_hidden:
            continue

        ######################################################
        # update sprites with results of physics simulation
        ######################################################
        if sprite.physics and sprite.physics.can_move:

            body = sprite.physics._pymunk_body
            angle = _math.degrees(body.angle)
            if isinstance(sprite, line):
                sprite._x = body.position.x - (sprite.length/2) * _math.cos(angle)
                sprite._y = body.position.y - (sprite.length/2) * _math.sin(angle)
                sprite._x1 = body.position.x + (sprite.length/2) * _math.cos(angle)
                sprite._y1 = body.position.y + (sprite.length/2) * _math.sin(angle)
                # sprite._length, sprite._angle = sprite._calc_length_angle()
            else:
                if str(body.position.x) != 'nan': # this condition can happen when changing sprite.physics.can_move
                    sprite._x = body.position.x
                if str(body.position.y) != 'nan':
                    sprite._y = body.position.y

            sprite.angle = angle # needs to be .angle, not ._angle so surface gets recalculated
            sprite.physics._x_speed, sprite.physics._y_speed = body.velocity

        #################################
        # @sprite.when_clicked events
        #################################
        if mouse.is_clicked and not type(sprite) == line:
            if _point_touching_sprite(mouse, sprite):
                # only run sprite clicks on the frame the mouse was clicked
                if click_happened_this_frame:
                    sprite._is_clicked = True
                    for callback in sprite._when_clicked_callbacks:
                        if not callback.is_running:
                            _loop.create_task(callback())


        # do sprite image transforms (re-rendering images/fonts, scaling, rotating, etc)

        # we put it in the event loop instead of just recomputing immediately because if we do it
        # synchronously then the data and rendered image may get out of sync
        if sprite._should_recompute_primary_surface:
            # recomputing primary surface also recomputes secondary surface
            _loop.call_soon(sprite._compute_primary_surface)
        elif sprite._should_recompute_secondary_surface:
            _loop.call_soon(sprite._compute_secondary_surface)

        if type(sprite) == line:
            # @hack: Line-drawing code should probably be in the line._compute_primary_surface function
            # but the coordinates work different for lines than other sprites.


            # x = screen.width/2 + sprite.x
            # y = screen.height/2 - sprite.y - sprite.thickness
            # _pygame_display.blit(sprite._secondary_pygame_surface, (x,y) )

            x = screen.width/2 + sprite.x
            y = screen.height/2 - sprite.y
            x1 = screen.width/2 + sprite.x1
            y1 = screen.height/2 - sprite.y1
            if sprite.thickness == 1:
                 pygame.draw.aaline(_pygame_display, _color_name_to_rgb(sprite.color), (x,y), (x1,y1), True)
            else:
                 pygame.draw.line(_pygame_display, _color_name_to_rgb(sprite.color), (x,y), (x1,y1), sprite.thickness)
        else:
            _pygame_display.blit(sprite._secondary_pygame_surface, (sprite._pygame_x(), sprite._pygame_y()) )

    pygame.display.flip()
    _loop.call_soon(_game_loop)
    return True


async def timer(seconds=1.0):
    """
    Wait a number of seconds. Used with the await keyword like this:

    @play.repeat_forever
    async def do():
        await play.timer(seconds=2)
        print('hi')

    """
    await _asyncio.sleep(seconds)
    return True

async def animate():

    await _asyncio.sleep(0)

# def _get_class_that_defined_method(meth):
#     if inspect.ismethod(meth):
#         for cls in inspect.getmro(meth.__self__.__class__):
#            if cls.__dict__.get(meth.__name__) is meth:
#                 return cls
#         meth = meth.__func__  # fallback to __qualname__ parsing
#     if inspect.isfunction(meth):
#         cls = getattr(inspect.getmodule(meth),
#                       meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
#         if isinstance(cls, type):
#             return cls
#     return getattr(meth, '__objclass__', None)  # handle special descriptor objects

_repeat_forever_callbacks = []
# @decorator
def repeat_forever(func):
    """
    Calls the given function repeatedly in the game loop.

    Example:

        text = play.new_text(words='hi there!', x=0, y=0, font='Arial.ttf', font_size=20, color='black')

        @play.repeat_forever
        async def do():
            text.turn(degrees=15)

    """
    async_callback = _make_async(func)
    async def repeat_wrapper():
        repeat_wrapper.is_running = True
        await async_callback()
        repeat_wrapper.is_running = False

    repeat_wrapper.is_running = False
    _repeat_forever_callbacks.append(repeat_wrapper)
    return func


_when_program_starts_callbacks = []
# @decorator
def when_program_starts(func):
    """
    Call code right when the program starts.

    Used like this:

    @play.when_program_starts
    def do():
        print('the program just started!')
    """
    async_callback = _make_async(func)
    async def wrapper(*args, **kwargs):
        return await async_callback(*args, **kwargs)
    _when_program_starts_callbacks.append(wrapper)
    return func

def repeat(number_of_times):
    """
    Repeat a set of commands a certain number of times. 

    Equivalent to `range(1, number_of_times+1)`.

    Used like this:

    @play.repeat_forever
    async def do():
        for count in play.repeat(10):
            print(count)
    """
    return range(1, number_of_times+1)

def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    for func in _when_program_starts_callbacks:
        _loop.create_task(func())

    _loop.call_soon(_game_loop)
    try:
        _loop.run_forever()
    finally:
        _logging.getLogger("asyncio").setLevel(_logging.CRITICAL)
        pygame.quit()
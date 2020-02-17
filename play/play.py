import math

import asyncio
import logging
import pygame

from . import cfg
from .keyboard import pygame_key_to_name, pressed_keys, keypress_callbacks, keyrelease_callbacks
from .color import color_name_to_rgb
from .physics import simulate_physics
from .mouse import mouse
from .events import process_custom_event_callbacks
from .utils import point_touching_sprite, make_async, is_line

pygame.init()
screen = cfg.screen
pygame_display = pygame.display.set_mode((screen.width, screen.height), pygame.DOUBLEBUF)
pygame.display.set_caption("Python Play")

pygame.key.set_repeat(200, 16)
keys_pressed_this_frame = []
keys_released_this_frame = []
keys_to_skip = (pygame.K_MODE,)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])

loop = asyncio.get_event_loop()
loop.set_debug(False)

clock = pygame.time.Clock()
def gameloop():
    keys_pressed_this_frame.clear() # do this instead of `keys_pressed_this_frame = []` to save a tiny bit of memory
    keys_released_this_frame.clear()
    click_happened_this_frame = False
    click_release_happened_this_frame = False

    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_q and (
                pygame.key.get_mods() & pygame.KMOD_META or pygame.key.get_mods() & pygame.KMOD_CTRL
        )):
            # quitting by clicking window's close button or pressing ctrl+q / command+q
            loop.stop()
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
            if not (event.key in keys_to_skip):
                name = pygame_key_to_name(event)
                pressed_keys[event.key] = name
                keys_pressed_this_frame.append(name)
        if event.type == pygame.KEYUP:
            if not (event.key in keys_to_skip) and event.key in pressed_keys:
                keys_released_this_frame.append(pressed_keys[event.key])
                del pressed_keys[event.key]



    ############################################################
    # @when_any_key_pressed and @when_key_pressed callbacks
    ############################################################
    for key in keys_pressed_this_frame:
        for callback in keypress_callbacks:
            if not callback.is_running and (callback.keys is None or key in callback.keys):
                loop.create_task(callback(key))

    ############################################################
    # @when_any_key_released and @when_key_released callbacks
    ############################################################
    for key in keys_released_this_frame:
        for callback in keyrelease_callbacks:
            if not callback.is_running and (callback.keys is None or key in callback.keys):
                loop.create_task(callback(key))


    ####################################
    # @mouse.when_clicked callbacks
    ####################################
    if click_happened_this_frame and mouse._when_clicked_callbacks:
        for callback in mouse._when_clicked_callbacks:
            loop.create_task(callback())

    ########################################
    # @mouse.when_click_released callbacks
    ########################################
    if click_release_happened_this_frame and mouse._when_click_released_callbacks:
        for callback in mouse._when_click_released_callbacks:
            loop.create_task(callback())
    
    process_custom_event_callbacks(loop)

    #############################
    # @repeat_forever callbacks
    #############################
    for callback in repeat_forever_callbacks:
        if not callback.is_running:
            loop.create_task(callback())

    #############################
    # physics simulation
    #############################
    loop.call_soon(simulate_physics)


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



    pygame_display.fill(color_name_to_rgb(cfg.backdrop))

    # BACKGROUND COLOR
    # note: cannot use screen.fill((1, 1, 1)) because pygame's screen
    #       does not support fill() on OpenGL surfaces
    # gl.glClearColor(_background_color[0], _background_color[1], _background_color[2], 1)
    # gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    for sprite in cfg.all_sprites:

        sprite._is_clicked = False

        if sprite.is_hidden:
            continue

        ######################################################
        # update sprites with results of physics simulation
        ######################################################
        if sprite.physics and sprite.physics.can_move:

            body = sprite.physics._pymunk_body
            angle = math.degrees(body.angle)
            if is_line(sprite):
                sprite._x = body.position.x - (sprite.length/2) * math.cos(angle)
                sprite._y = body.position.y - (sprite.length/2) * math.sin(angle)
                sprite._x1 = body.position.x + (sprite.length/2) * math.cos(angle)
                sprite._y1 = body.position.y + (sprite.length/2) * math.sin(angle)
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
        if mouse.is_clicked and not is_line(sprite):
            if point_touching_sprite(mouse, sprite):
                # only run sprite clicks on the frame the mouse was clicked
                if click_happened_this_frame:
                    sprite._is_clicked = True
                    for callback in sprite._when_clicked_callbacks:
                        if not callback.is_running:
                            loop.create_task(callback())


        # do sprite image transforms (re-rendering images/fonts, scaling, rotating, etc)

        # we put it in the event loop instead of just recomputing immediately because if we do it
        # synchronously then the data and rendered image may get out of sync
        if sprite._should_recompute_primary_surface:
            # recomputing primary surface also recomputes secondary surface
            loop.call_soon(sprite._compute_primary_surface)
        elif sprite._should_recompute_secondary_surface:
            loop.call_soon(sprite._compute_secondary_surface)

        if is_line(sprite):
            # @hack: Line-drawing code should probably be in the line._compute_primary_surface function
            # but the coordinates work different for lines than other sprites.


            # x = screen.width/2 + sprite.x
            # y = screen.height/2 - sprite.y - sprite.thickness
            # pygame_display.blit(sprite._secondary_pygame_surface, (x,y) )

            x = screen.width/2 + sprite.x
            y = screen.height/2 - sprite.y
            x1 = screen.width/2 + sprite.x1
            y1 = screen.height/2 - sprite.y1
            if sprite.thickness == 1:
                 pygame.draw.aaline(pygame_display, color_name_to_rgb(sprite.color), (x,y), (x1,y1), True)
            else:
                 pygame.draw.line(pygame_display, color_name_to_rgb(sprite.color), (x,y), (x1,y1), sprite.thickness)
        else:
            pygame_display.blit(sprite._secondary_pygame_surface, (sprite._pygame_x(screen), sprite._pygame_y(screen)))

    pygame.display.flip()
    loop.call_soon(gameloop)
    return True


async def timer(seconds=1.0):
    """
    Wait a number of seconds. Used with the await keyword like this:

    @play.repeat_forever
    async def do():
        await play.timer(seconds=2)
        print('hi')

    """
    await asyncio.sleep(seconds)
    return True

async def animate():

    await asyncio.sleep(0)


repeat_forever_callbacks = []
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
    async_callback = make_async(func)
    async def repeat_wrapper():
        repeat_wrapper.is_running = True
        await async_callback()
        repeat_wrapper.is_running = False

    repeat_wrapper.is_running = False
    repeat_forever_callbacks.append(repeat_wrapper)
    return func


when_program_starts_callbacks = []
# @decorator
def when_program_starts(func):
    """
    Call code right when the program starts.

    Used like this:

    @play.when_program_starts
    def do():
        print('the program just started!')
    """
    async_callback = make_async(func)
    async def wrapper(*args, **kwargs):
        return await async_callback(*args, **kwargs)
    when_program_starts_callbacks.append(wrapper)
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
    for func in when_program_starts_callbacks:
        loop.create_task(func())

    loop.call_soon(gameloop)
    try:
        loop.run_forever()
    finally:
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
        pygame.quit()
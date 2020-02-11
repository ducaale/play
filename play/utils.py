def _clamp(num, min_, max_):
    if num < min_:
        return min_
    elif num > max_:
        return max_
    return num


def _point_touching_sprite(point, sprite):
    # todo: custom code for circle, line, rotated rectangley sprites
    return sprite.left <= point.x <= sprite.right and sprite.bottom <= point.y <= sprite.top


def _sprite_touching_sprite(a, b):
    # todo: custom code for circle, line, rotated rectangley sprites
    # use physics engine if both sprites have physics on
    # if a.physics and b.physics:
    if a.left >= b.right or a.right <= b.left or a.top <= b.bottom or a.bottom >= b.top:
        return False
    return True

def _raise_on_await_warning(func):
    """
    If someone doesn't put 'await' before functions that require 'await'
    like play.timer() or play.animate(), raise an exception.
    """
    async def f(*args, **kwargs):
        with _warnings.catch_warnings(record=True) as w:
            await func(*args, **kwargs)
            for warning in w:
                str_message = warning.message.args[0] # e.g. "coroutine 'timer' was never awaited"
                if 'was never awaited' in str_message:
                    unawaited_function_name = str_message.split("'")[1]
                    raise Oops(f"""Looks like you forgot to put "await" before play.{unawaited_function_name} on line {warning.lineno} of file {warning.filename}.
To fix this, just add the word 'await' before play.{unawaited_function_name} on line {warning.lineno} of file {warning.filename} in the function {func.__name__}.""")
                else:
                    print(warning.message)
    return f

def _make_async(func):
    """
    Turn a non-async function into an async function. 
    Used mainly in decorators like @repeat_forever.
    """
    if _asyncio.iscoroutinefunction(func):
        # if it's already async just return it
        return _raise_on_await_warning(func)
    @_raise_on_await_warning
    async def async_func(*args, **kwargs):
        return func(*args, **kwargs)
    return async_func

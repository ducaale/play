import asyncio
from .utils import make_async

custom_events = []
custom_event_callbacks = []

def still_running_callbacks(event):
    for callback in custom_event_callbacks:
        if callback.event == event and callback.is_running:
            return True
    return False


def broadcast(event='default'):
    custom_events.append(event)


async def broadcast_and_wait(event='default'):
    custom_events.append(event)
    while still_running_callbacks(event):
        await asyncio.sleep(0)


# @decorator
def when_event_recieved(event):
    def decorator(func):
        async_callback = make_async(func)
        # TODO: move wrapper to utils
        async def wrapper(*args, **kwargs):
            wrapper.is_running = True
            await async_callback(*args, **kwargs)
            wrapper.is_running = False
        wrapper.is_running = False
        wrapper.event = event
        custom_event_callbacks.append(wrapper)
        return wrapper
    return decorator

# TODO: fix broadcast_and_wait not working correctly
def process_custom_event_callbacks(loop):
    for callback in custom_event_callbacks:
        if not callback.is_running and callback.event in custom_events:
            loop.create_task(callback())

    custom_events.clear()
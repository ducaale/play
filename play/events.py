import asyncio
from .utils import make_async

custom_events = set()
custom_event_callbacks = []

def running_callbacks(event):
    for callback in custom_event_callbacks:
        if callback.event == event and callback.is_running:
            return True
    return False

def broadcast(event='default'):
    custom_events.add(event)

async def broadcast_and_wait(event='default'):
    custom_events.add(event)
    await asyncio.sleep(0)
    while running_callbacks(event): await asyncio.sleep(0)

def wrap_promise(async_func):
    async def wrapper(*args, **kwargs):
        await async_func(*args, **kwargs)
        wrapper.is_running = False
    wrapper.is_running = False
    return wrapper

# @decorator
def when_event_recieved(event):
    def decorator(func):
        wrapper = wrap_promise(make_async(func))
        wrapper.event = event
        custom_event_callbacks.append(wrapper)
        return wrapper
    return decorator

def process_custom_event_callbacks(loop):
    for callback in custom_event_callbacks:
        if not callback.is_running and callback.event in custom_events:
            callback.is_running = True
            loop.create_task(callback())

    custom_events.clear()
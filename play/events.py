import asyncio
from .utils import make_async, track_async_status

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

# @decorator
def when_event_recieved(event):
    def decorator(func):
        async_callback = track_async_status(make_async(func))
        async_callback.event = event
        custom_event_callbacks.append(async_callback)
        return async_callback
    return decorator

def process_custom_event_callbacks(loop):
    for callback in custom_event_callbacks:
        if not callback.is_running and callback.event in custom_events:
            callback.is_running = True
            loop.create_task(callback())

    custom_events.clear()
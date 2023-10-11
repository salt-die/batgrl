import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pygame as pg

from .console_input import events

__all__ = [
    "attach",
    "raw_mode",
    "events",
]


@contextmanager
def attach(callback):
    """
    Context manager that makes this input active in the current event loop.
    """

    async def poll_events():
        while True:
            if pg.event.peek():
                callback()

            await asyncio.sleep(0)

    try:
        poll_task = asyncio.create_task(poll_events())

        yield

    finally:
        poll_task.cancel()


@contextmanager
def raw_mode():
    yield


PygameInput = SimpleNamespace(attach=attach, raw_mode=raw_mode, events=events)

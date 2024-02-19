"""Win32 input."""
from asyncio import get_event_loop
from contextlib import contextmanager
from ctypes import byref, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE

from ...win32_types import SECURITY_ATTRIBUTES, STD_INPUT_HANDLE
from .console_input import events

__all__ = [
    "attach",
    "raw_mode",
    "events",
]


@contextmanager
def attach(callback):
    """Context manager that makes this input active in the current event loop."""
    try:
        loop = get_event_loop()

        wait_for = windll.kernel32.WaitForMultipleObjects

        REMOVE_EVENT = HANDLE(
            windll.kernel32.CreateEventA(
                SECURITY_ATTRIBUTES(), BOOL(True), BOOL(False), None
            )
        )

        EVENTS = (HANDLE * 2)(REMOVE_EVENT, STD_INPUT_HANDLE)

        def ready():
            try:
                callback()
            finally:
                loop.run_in_executor(None, wait)

        def wait():
            if wait_for(2, EVENTS, BOOL(False), DWORD(-1)) == 0:
                windll.kernel32.CloseHandle(REMOVE_EVENT)
            else:
                loop.call_soon_threadsafe(ready)

        loop.run_in_executor(None, wait)

        yield

    finally:
        windll.kernel32.SetEvent(REMOVE_EVENT)


@contextmanager
def raw_mode():
    """Put terminal into raw mode."""
    original_mode = DWORD()

    windll.kernel32.GetConsoleMode(STD_INPUT_HANDLE, byref(original_mode))

    try:
        ENABLE_ECHO_INPUT = 0x0004
        ENABLE_LINE_INPUT = 0x0002
        ENABLE_PROCESSED_INPUT = 0x0001

        windll.kernel32.SetConsoleMode(
            STD_INPUT_HANDLE,
            original_mode.value
            & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT),
        )

        yield

    finally:
        windll.kernel32.SetConsoleMode(STD_INPUT_HANDLE, original_mode)

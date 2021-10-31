"""
Win32 Input.
"""
from asyncio import get_event_loop
from contextlib import contextmanager

from ctypes import pointer, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE

from ...win32_types import SECURITY_ATTRIBUTES
from .console_input_reader import STDIN_HANDLE, read_keys

__all__ = (
    "attach",
    "raw_input",
    "read_keys",
)

@contextmanager
def attach(callback):
    """
    Context manager that makes this input active in the current event loop.
    """
    try:
        loop = get_event_loop()
        run_in_executor = loop.run_in_executor
        call_soon_threadsafe = loop.call_soon_threadsafe
        wait_for = windll.kernel32.WaitForMultipleObjects
        FALSE = BOOL(False)
        NO_TIMEOUT = DWORD(-1)

        # Anonymous win32 event.
        REMOVE_EVENT = HANDLE(
            windll.kernel32.CreateEventA(
                pointer(SECURITY_ATTRIBUTES()),
                BOOL(True),
                FALSE,
                None,
            )
        )

        EVENTS = (HANDLE * 2)(REMOVE_EVENT, STDIN_HANDLE)

        def ready():
            try:
                callback()
            finally:
                run_in_executor(None, wait)

        def wait():
            if wait_for(2, EVENTS, FALSE, NO_TIMEOUT) == 0:
                windll.kernel32.CloseHandle(REMOVE_EVENT)
            else:
                call_soon_threadsafe(ready)

        run_in_executor(None, wait)

        yield

    finally:
        windll.kernel32.SetEvent(REMOVE_EVENT)

@contextmanager
def raw_mode():
    original_mode = DWORD()
    windll.kernel32.GetConsoleMode(STDIN_HANDLE, pointer(original_mode))

    try:
        ENABLE_ECHO_INPUT = 0x0004
        ENABLE_LINE_INPUT = 0x0002
        ENABLE_PROCESSED_INPUT = 0x0001

        windll.kernel32.SetConsoleMode(
            STDIN_HANDLE,
            original_mode.value
            & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT),
        )

        yield

    finally:
        windll.kernel32.SetConsoleMode(STDIN_HANDLE, original_mode)

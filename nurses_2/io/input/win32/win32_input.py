"""
Win32 Input.

This namespace has functions analogous to Vt100Input's methods. `read_keys` is brought in from `console_input_reader`.
"""
from asyncio import get_event_loop
from contextlib import contextmanager

from ctypes import pointer, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE

from ...win32_types import SECURITY_ATTRIBUTES
from .console_input_reader import STDIN_HANDLE, read_keys  # read_keys is expected to be in this namespace

TWO_ARR = HANDLE * 2

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

        # Anonymous win32 event.
        remove_event = HANDLE(
            windll.kernel32.CreateEventA(
                pointer(SECURITY_ATTRIBUTES()),
                BOOL(True),
                BOOL(False),
                None,
            )
        )

        def ready():
            try:
                callback()
            finally:
                run_in_executor(None, wait)

        def wait():
            if wait_for(2, TWO_ARR(remove_event, STDIN_HANDLE), BOOL(False), DWORD(-1)) == 0:
                windll.kernel32.CloseHandle(remove_event)
                return

            call_soon_threadsafe(ready)

        run_in_executor(None, wait)

        yield

    finally:
        windll.kernel32.SetEvent(remove_event)

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

def flush_keys():
    """
    Provided for combatibility with Vt100Input.
    """
    return ()

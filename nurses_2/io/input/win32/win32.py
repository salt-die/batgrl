import sys
from asyncio import get_event_loop
from contextlib import contextmanager

from ctypes import pointer, windll
from ctypes.wintypes import DWORD, HANDLE

from ...win32_types import STD_INPUT_HANDLE
from .console_input_reader import ConsoleInputReader
from .handles import create_win32_event, wait_for_handle, wait_for_handles


class Win32Input:
    """
    Class that reads from the Windows console.
    """
    def __init__(self):
        self.console_input_reader = ConsoleInputReader()  # ? Can we combine these classes?

    @contextmanager
    def attach(self, callback):
        """
        Context manager that makes this input active in the current event loop.
        """
        handle = self.handle

        try:
            loop = get_event_loop()
            run_in_executor = loop.run_in_executor
            call_soon_threadsafe = loop.call_soon_threadsafe

            remove_event = create_win32_event()

            def ready():
                try:
                    callback()
                finally:
                    run_in_executor(None, wait)

            def wait():
                if wait_for_handles([remove_event, handle]) is remove_event:
                    windll.kernel32.CloseHandle(remove_event)
                    return

                call_soon_threadsafe(ready)

            run_in_executor(None, wait)

            yield

        finally:
            windll.kernel32.SetEvent(remove_event)

    def read_keys(self):
        return list(self.console_input_reader.read())

    def flush(self):
        pass

    def flush_keys(self):
        return [ ]

    @contextmanager
    def raw_mode(self):
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))
        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))

        try:
            ENABLE_ECHO_INPUT = 0x0004
            ENABLE_LINE_INPUT = 0x0002
            ENABLE_PROCESSED_INPUT = 0x0001

            windll.kernel32.SetConsoleMode(
                handle,
                original_mode.value
                & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT),
            )

            yield

        finally:
            windll.kernel32.SetConsoleMode(handle, original_mode)

    def fileno(self):
        return sys.stdin.fileno()

    def close(self):
        pass

    @property
    def handle(self) -> HANDLE:
        return self.console_input_reader.handle

"""Platform specific VT100 terminals."""

import platform
import sys
from collections.abc import Callable
from contextlib import contextmanager
from typing import ContextManager

from .events import Event
from .vt100_terminal import Vt100Terminal

__all__ = ["Vt100Terminal", "get_platform_terminal", "app_mode"]


def get_platform_terminal() -> Vt100Terminal:
    """
    Return a platform-specific terminal.

    Returns
    -------
    Vt100Terminal
        A platform-specific VT100 terminal.

    Raises
    ------
    RuntimeError
        If terminal isn't interactive or terminal doesn't support VT100 sequences.
    """
    if not sys.stdin.isatty():
        raise RuntimeError("Terminal is non-interactive.")

    if platform.system() == "Windows":
        from .windows_terminal import WindowsTerminal, is_vt100_enabled

        if not is_vt100_enabled():
            raise RuntimeError("Terminal doesn't support VT100 sequences.")

        return WindowsTerminal()
    else:
        from .linux_terminal import LinuxTerminal

        return LinuxTerminal()


@contextmanager
def app_mode(
    terminal: Vt100Terminal, event_handler: Callable[[list[Event]], None]
) -> ContextManager[None]:
    """
    Put terminal into app mode and dispatch input events.

    Parameters
    ----------
    terminal : Vt100Terminal
        Terminal to put in app mode.
    event_handler : Callable[[list[Event]], None]
        A callable that handles terminal input events.
    """
    try:
        terminal.raw_mode()
        terminal.attach(event_handler)
        terminal.enable_mouse_support()
        terminal.enable_bracketed_paste()
        terminal.enable_reporting_focus()
        terminal.hide_cursor()
        terminal.flush()
        yield
    finally:
        if terminal.in_alternate_screen:
            terminal.exit_alternate_screen()
        else:
            terminal.erase_in_display()
        terminal.reset_attributes()
        terminal.show_cursor()
        terminal.disable_reporting_focus()
        terminal.disable_bracketed_paste()
        terminal.disable_mouse_support()
        terminal.flush()
        terminal.unattach()
        terminal.restore_console()

"""Platform specific VT100 terminals."""

import asyncio
import platform
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Final

from ..geometry import Size
from .events import DeviceAttributesReportEvent, Event, PixelGeometryReportEvent
from .vt100_terminal import DRS_REQUEST_TIMEOUT, Vt100Terminal

__all__ = [
    "Vt100Terminal",
    "app_mode",
    "get_platform_terminal",
    "get_sixel_info",
]

_SIXEL_SUPPORT: Final = 4
"""Terminal attribute for sixel support."""


@contextmanager
def app_mode(
    terminal: Vt100Terminal, event_handler: Callable[[list[Event]], None]
) -> Iterator[None]:
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


async def get_sixel_info(terminal: Vt100Terminal) -> tuple[bool, Size]:
    """
    Determine if terminal has sixel support and, if supported, its pixel geometry.

    Parameters
    ----------
    terminal : VT100Terminal
        A VT100 terminal to query for sixel support.

    Returns
    -------
    tuple[bool, Size]
        Whether sixel is supported and the pixel geometry.
    """
    sixel_support: bool = False
    pixel_geometry: Size = Size(20, 10)
    report_timeout: asyncio.TimerHandle
    terminal_info_reported: asyncio.Event = asyncio.Event()
    cell_reported: bool = False

    def report_handler(events: list[Event]) -> None:
        """Handle terminal reports."""
        nonlocal sixel_support, pixel_geometry, cell_reported, report_timeout

        for event in events:
            if isinstance(event, DeviceAttributesReportEvent):
                report_timeout.cancel()
                sixel_support = _SIXEL_SUPPORT in event.device_attributes
                if sixel_support:
                    terminal.request_pixel_geometry()
                    terminal.request_terminal_geometry()
                    report_timeout = asyncio.get_running_loop().call_later(
                        DRS_REQUEST_TIMEOUT, terminal_info_reported.set
                    )
                else:
                    terminal_info_reported.set()
            elif isinstance(event, PixelGeometryReportEvent):
                report_timeout.cancel()
                if event.kind == "cell":
                    pixel_geometry = event.geometry
                    cell_reported = True
                elif not cell_reported:
                    ph, pw = event.geometry
                    th, tw = terminal.get_size()
                    pixel_geometry = Size(ph // th, pw // tw)
                terminal_info_reported.set()

    old_handler = terminal._event_handler
    terminal._event_handler = report_handler
    terminal.request_device_attributes()
    report_timeout = asyncio.get_running_loop().call_later(
        DRS_REQUEST_TIMEOUT, terminal_info_reported.set
    )
    await terminal_info_reported.wait()
    terminal._event_handler = old_handler
    return sixel_support, pixel_geometry

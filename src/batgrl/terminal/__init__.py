"""Platform specific VT100 terminals."""

import asyncio
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Final

from ..geometry import Size
from ..logging import get_logger
from .events import (
    DECReplyModeEvent,
    DeviceAttributesReportEvent,
    Event,
    PixelGeometryReportEvent,
)
from .vt100_terminal import DSR_REQUEST_TIMEOUT, Vt100Terminal

__all__ = [
    "Vt100Terminal",
    "app_mode",
    "determine_terminal_capabilities",
    "get_platform_terminal",
]

logger = get_logger(__name__)

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
    if sys.platform == "win32":
        from .windows_terminal import WindowsTerminal

        return WindowsTerminal()
    else:
        from .linux_terminal import LinuxTerminal

        return LinuxTerminal()


async def determine_terminal_capabilities(terminal: Vt100Terminal) -> tuple[bool, Size]:
    """
    Determine various terminal capabilities.

    Try to determine terminal's pixel geometry. If pixel geometry is determined,
    determine if terminal has sixel support and attempt to turn on SGR-PIXELS mouse
    mode. Additionally, query for synchronized update mode support.

    Parameters
    ----------
    terminal : VT100Terminal
        The VT100 terminal to query.

    Returns
    -------
    tuple[bool, Size]
        Return whether sixel is supported and pixel geometry.
    """
    logger.info("Determining terminal capabilities...")

    pixel_geometry: Size | None = None
    sixel_support: bool = False
    terminal_info_reported: asyncio.Event = asyncio.Event()
    report_timeout: asyncio.TimerHandle

    def report_handler(events: list[Event]) -> None:
        """Handle terminal reports."""
        nonlocal sixel_support, pixel_geometry, report_timeout

        for event in events:
            if isinstance(event, DeviceAttributesReportEvent):
                sixel_support = _SIXEL_SUPPORT in event.device_attributes
            elif isinstance(event, PixelGeometryReportEvent):
                if event.kind == "cell":
                    pixel_geometry = event.geometry
                else:
                    ph, pw = event.geometry
                    th, tw = terminal.get_size()
                    pixel_geometry = Size(ph // th, pw // tw)
            elif isinstance(event, DECReplyModeEvent):
                if event.mode == 1016:
                    if event.value:
                        logger.info("SGR Pixels supported")
                        terminal.enable_sgr_pixels()
                    else:
                        logger.info("SGR-Pixels not supported")
                elif event.mode == 2026:
                    if event.value:
                        logger.info("Synchronized update mode (SUM) supported")
                    else:
                        logger.info("Synchronized update mode (SUM) not supported")
                else:
                    continue
            else:
                continue

            report_timeout.cancel()
            terminal_info_reported.set()

    async def wait_for_report():
        nonlocal report_timeout
        report_timeout = asyncio.get_running_loop().call_later(
            DSR_REQUEST_TIMEOUT, terminal_info_reported.set
        )
        await terminal_info_reported.wait()
        terminal_info_reported.clear()

    old_handler = terminal._event_handler
    terminal._event_handler = report_handler

    terminal.request_synchronized_update_mode_supported()
    await wait_for_report()

    terminal.request_pixel_geometry()
    await wait_for_report()

    if pixel_geometry is None:
        # Fallback to terminal geometry from which pixel geometry can be calculated.
        terminal.request_terminal_geometry()
        await wait_for_report()

    if pixel_geometry is None:
        logger.info("Pixel geometry not reported")
        logger.info("Sixel not supported")
        # No pixel geometry reported; don't even attempt SGR-PIXELS or SIXEL.
        return False, Size(20, 10)

    logger.info("Pixel geometry reported as: %s", pixel_geometry)

    terminal.request_sgr_pixels_supported()
    await wait_for_report()

    terminal.request_device_attributes()
    await wait_for_report()

    if sixel_support:
        logger.info("Sixel supported")
    else:
        logger.info("Sixel not supported")

    terminal._event_handler = old_handler
    return sixel_support, pixel_geometry

"""
Logging related classes and functions.

Because default logging opens stdout/stderr which disables batgrl output, logging must
be setup with a file handler instead. To ensure a file handler has been added, all
library logging should use ``get_logger`` (essentially, just an alias of stdlib
``logging.getLogger``) from this module.

Additional log levels, ``ANSI`` and ``EVENTS``, are added to standard logging levels.
"""
# Inspiration taken from:
# <https://github.com/python-discord/bot-core/blob/main/pydis_core/utils/logging.py>.
# python-discord/bot-core is licensed under the MIT License.

import logging
import typing
from enum import IntEnum
from pathlib import Path
from typing import Final

__all__ = ["LogLevel", "get_logger"]

LOG_FILE = Path() / "batgrl.log"  # TODO: Customize path.
ANSI_LEVEL: Final = 3
"""
``ANSI`` log level.

Show generated ANSI in logs.
"""
EVENTS_LEVEL: Final = 5
"""
``EVENTS`` log level.

Show generated input events.
"""


class LogLevel(IntEnum):
    """Standard logging levels with additional ``ANSI`` and ``EVENTS`` levels."""

    ANSI = ANSI_LEVEL
    """Show generated ANSI in logs."""
    EVENTS = EVENTS_LEVEL
    """Show generated input events."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


if typing.TYPE_CHECKING:
    LoggerClass = logging.Logger
else:
    LoggerClass = logging.getLoggerClass()


class CustomLogger(LoggerClass):
    """A standard logger with methods for ``ANSI`` and ``EVENTS`` logging."""

    def ansi(self, msg: str, *args, **kwargs) -> None:
        """Log the given message with the severity ``"ANSI"``."""
        if self.isEnabledFor(logging.ANSI):
            self.log(logging.ANSI, msg, *args, **kwargs)

    def events(self, msg: str, *args, **kwargs) -> None:
        """Log the given message with the severity ``"EVENTS"``."""
        if self.isEnabledFor(logging.EVENTS):
            self.log(logging.EVENTS, msg, *args, **kwargs)

    def is_enabled_for(self, log_level: LogLevel | str) -> bool:
        """Similar to ``Logger.isEnabledFor``, but also accepts level names."""
        if isinstance(log_level, str):
            return self.isEnabledFor(logging._nameToLevel[log_level])
        return self.isEnabledFor(log_level)


def get_logger(name: str | None = None) -> CustomLogger:
    """
    Return a logger with a specified name.

    Because there are several entry points into batgrl and default logging opens
    stderr/stdout which will disable batgrl output, all library logging must use this
    alias of ``logging.getLogger`` to ensure logging has been set to output to a file.

    Parameters
    ----------
    name : str | None, default: None
        Name of logger. If not specified, return the root logger.

    Returns
    -------
    CustomLogger
        The specified logger.
    """
    return typing.cast(CustomLogger, logging.getLogger(name))


logging.ANSI: Final = ANSI_LEVEL
logging.EVENTS: Final = EVENTS_LEVEL
logging.addLevelName(ANSI_LEVEL, "ANSI")
logging.addLevelName(EVENTS_LEVEL, "EVENTS")
logging.setLoggerClass(CustomLogger)

log_format = logging.Formatter(
    "{asctime} | {levelname} | {name} | {message}", style="{"
)

log_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
log_handler.setFormatter(log_format)

logger = logging.getLogger("batgrl")
logger.addHandler(log_handler)
logger.setLevel(LogLevel.INFO)

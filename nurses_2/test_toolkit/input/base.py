"""
Abstraction of CLI Input.
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from contextlib import contextmanager
from typing import Callable, ContextManager, Generator, List

from ..key_binding import KeyPress

__all__ = "Input",


class Input(metaclass=ABCMeta):
    """
    Abstraction for any input.

    An instance of this class can be given to the constructor of a
    :class:`~prompt_toolkit.application.Application` and will also be
    passed to the :class:`~prompt_toolkit.eventloop.base.EventLoop`.
    """

    @abstractmethod
    def fileno(self) -> int:
        """
        Fileno for putting this in an event loop.
        """

    @abstractmethod
    def typeahead_hash(self) -> str:
        """
        Identifier for storing type ahead key presses.
        """

    @abstractmethod
    def read_keys(self) -> List[KeyPress]:
        """
        Return a list of Key objects which are read/parsed from the input.
        """

    def flush_keys(self) -> List[KeyPress]:
        """
        Flush the underlying parser. and return the pending keys.
        (Used for vt100 input.)
        """
        return []

    def flush(self) -> None:
        "The event loop can call this when the input has to be flushed."
        pass

    @abstractproperty
    def closed(self) -> bool:
        "Should be true when the input stream is closed."
        return False

    @abstractmethod
    def raw_mode(self) -> ContextManager[None]:
        """
        Context manager that turns the input into raw mode.
        """

    @abstractmethod
    def attach(self, input_ready_callback: Callable[[], None]) -> ContextManager[None]:
        """
        Return a context manager that makes this input active in the current
        event loop.
        """

    def close(self) -> None:
        "Close input."
        pass

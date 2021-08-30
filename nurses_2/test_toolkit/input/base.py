from abc import ABCMeta, abstractmethod


class Input(metaclass=ABCMeta):
    """
    Abstraction for any input.
    """

    @abstractmethod
    def fileno(self) -> int:
        """
        Fileno for putting this in an event loop.
        """

    @abstractmethod
    def read_keys(self):
        """
        Return a list of Key objects which are read/parsed from the input.
        """

    def flush_keys(self):
        """
        Flush the underlying parser. and return the pending keys.
        (Used for vt100 input.)
        """
        return []

    def flush(self):
        """
        Flush input.
        """

    @abstractmethod
    def raw_mode(self):
        """
        Context manager that turns the input into raw mode.
        """

    @abstractmethod
    def attach(self, input_ready_callback):
        """
        Return a context manager that makes this input active in the current
        event loop.
        """

    def close(self) -> None:
        "Close input."
        pass

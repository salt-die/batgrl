"""A growable bytes buffer."""

class BytesBuffer:
    """A growable bytes buffer."""

    def __len__(self) -> int:
        """Length of bytes buffer."""

    def __bool__(self) -> bool:
        """Whether bytes buffer is nonempty."""

    def write(self, s: bytes) -> None:
        """Write bytes to buffer."""

    def flush(self) -> None:
        """Flush bytes to stdout."""

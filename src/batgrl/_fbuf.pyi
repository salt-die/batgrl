"""
A growable string buffer.

This wrapper around ``fbuf`` should be removed shortly after sixel branch is merged and
Vt100Terminal can be rewritten in cython to handle `fbuf` directly.
"""

class FBufWrapper:
    """A growable string buffer."""

    def __len__(self) -> int:
        """Length of string buffer."""

    def __bool__(self) -> bool:
        """Whether string buffer is nonempty."""

    def write(self, s: bytes) -> None:
        """Write bytes to string buffer."""

    def flush(self) -> None:
        """Flush bytes to stdout."""

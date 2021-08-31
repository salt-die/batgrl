import os
import select
from codecs import getincrementaldecoder

MAX_BYTES = 1024


class PosixStdinReader:
    """
    Wrapper around stdin which reads (nonblocking) the next available 1024
    bytes and decodes it.
    """
    def __init__(self, stdin_fd):
        self.stdin_fd = stdin_fd
        self._stdin_decoder_cls = getincrementaldecoder("utf-8")
        self._stdin_decoder = self._stdin_decoder_cls("surrogateescape")

    def read(self):
        if not select.select([self.stdin_fd], [], [], 0)[0]:
            return ""

        # Note: the following works better than wrapping `self.stdin` like
        #       `codecs.getreader('utf-8')(stdin)` and doing `read(1)`.
        #       Somehow that causes some latency when the escape
        #       character is pressed. (Especially on combination with the `select`.)
        try:
            data = os.read(self.stdin_fd, MAX_BYTES)
        except OSError:
            data = b""

        return self._stdin_decoder.decode(data)

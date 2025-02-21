from ._fbuf cimport fbuf_flush, fbuf_free, fbuf_init, fbuf_putn, fbuf_small_init


cdef class BytesBuffer:
    def __init__(self, small: bool=False) -> None:
        if small:
            if fbuf_small_init(&self.f):
                raise MemoryError
        else:
            if fbuf_init(&self.f):
                raise MemoryError

    def __dealloc__(self) -> None:
        fbuf_free(&self.f)

    def __len__(self) -> int:
        return self.f.len

    def __bool__(self) -> bool:
        return self.f.len > 0

    def endswith(self, suffix: bytes) -> bool:
        cdef size_t slen = len(suffix), i

        if slen > self.f.len:
            return False

        for i in range(slen):
            if suffix[i] != self.f.buf[self.f.len - slen + i]:
                return False

        return True

    def getvalue(self) -> bytes:
        return self.f.buf[:self.f.len]

    def clear(self) -> None:
        self.f.len = 0

    def write(self, s: bytes) -> None:
        if fbuf_putn(&self.f, s, len(s)):
            raise MemoryError

    def flush(self) -> None:
        fbuf_flush(&self.f)

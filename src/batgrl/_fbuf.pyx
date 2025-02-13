from ._fbuf cimport fbuf_flush, fbuf_free, fbuf_init, fbuf_init_small, fbuf_putn


cdef class FBufWrapper:
    def __init__(self, small: bool=False) -> None:
        if small:
            if fbuf_init_small(&self.f):
                raise MemoryError

        if fbuf_init(&self.f):
            raise MemoryError

    def clear(self):
        self.f.len = 0

    def getvalue(self) -> bytes:
        return self.f.buf[:self.f.len]

    def endswith(self, suffix: bytes) -> bool:
        cdef size_t slen = len(suffix)
        cdef size_t flen = self.f.len

        if slen > flen:
            return False

        cdef size_t i
        for i in range(slen):
            if suffix[i] != self.f.buf[flen - slen + i]:
                return False

        return True

    def __dealloc__(self) -> None:
        fbuf_free(&self.f)

    def __len__(self) -> int:
        return self.f.len

    def __bool__(self) -> bool:
        return self.f.len > 0

    def write(self, s: bytes) -> None:
        if fbuf_putn(&self.f, s, len(s)):
            raise MemoryError

    def flush(self) -> None:
        fbuf_flush(&self.f)

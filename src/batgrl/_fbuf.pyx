from ._fbuf cimport fbuf_flush, fbuf_free, fbuf_init, fbuf_putn


cdef class FBufWrapper:
    def __init__(self) -> None:
        if fbuf_init(&self.f):
            raise MemoryError

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

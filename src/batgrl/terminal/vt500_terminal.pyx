from libc.string cimport memset, strlen

from .._fbuf cimport  (
    fbuf,
    fbuf_flush,
    fbuf_free,
    fbuf_grow,
    fbuf_init,
    fbuf_init_small,
    fbuf_putn,
    fbuf_putucs4,
)
from .vt500_terminal cimport TermInfo, vtparse, action_t, state_t

ctypedef void (*callback_t)(vtparse*, action_t, unsigned char)

cdef class Vt100Terminal:
    def __cinit__(self):
        if fbuf_init_small(&self.escape_buffer):
            raise MemoryError
        if fbuf_init(&self.paste_buffer):
            fbuf_free(&self.escape_buffer)
            raise MemoryError
        if fbuf_init(&self.out_buffer):
            fbuf_free(&self.escape_buffer)
            fbuf_free(&self.paste_buffer)
            raise MemoryError

        memset(&self.terminfo, 0, sizeof(TermInfo))

    def __dealloc__(self):
        fbuf_free(&self.escape_buffer)
        fbuf_free(&self.paste_buffer)
        fbuf_free(&self.out_buffer)

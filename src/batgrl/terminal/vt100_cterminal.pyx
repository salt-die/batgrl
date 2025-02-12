import re
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
from .vt100_cterminal cimport (
    GROUND,
    ESCAPE,
    CSI,
    OSC,
    PARAMS,
    PASTE,
    EXECUTE_NEXT,
    TermInfo,
)

cdef: 
    char ESC = "\x1b"
    char *BRACKETED_PASTE_END = "\x1b[201~"
    char *PARAMS_RE = r"[0-9;]"

cdef inline bint endswith(fbuf *f, const char *suffix):
    cdef int i, n = strlen(suffix)
    if n > f.len:
        return 0

    for i in range(n):
        if f.buf[f.len - n + i] != suffix[i]:
            return 0

    return 1


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

        self.parser_state = GROUND
        memset(&self.terminfo, 0, sizeof(TermInfo))

    def __dealloc__(self):
        fbuf_free(&self.escape_buffer)
        fbuf_free(&self.paste_buffer)
        fbuf_free(&self.out_buffer)

    cpdef void _feed1(self, Py_UCS4 char):
        if fbuf_flush(&self.f, 4):
            raise MemoryError
        
        if self.parser_state == OSC:
            fbuf_putucs4(&self.escape_buffer, char)
            if (
                char == u"\\" and
                self.escape_buffer.len >= 2 and
                self.escape_buffer.buf[self.escape_buffer.len - 2] == ESC
            ):
                self.execute()
        elif self.parser_state != PASTE and char == ESC:
            self.escape_buffer.len = 0
            fbuf_putucs4(&self.escape_buffer, char)
            self.state = ESCAPE
        elif self.parser_state == EXECUTE_NEXT:
            fbuf_putucs4(&self.escape_buffer, char)
            self.execute()
        elif self.parser_state == PASTE:
            fbuf_putucs4(&self.paste_buffer, char)
            if char == u"~":
                if endswith(&self.paste_buffer, BRACKETED_PASTE_END):
                    #FIXME
                    self.paste_buffer.len = 0
                    self.parser_state = GROUND
        elif self.parser_state == GROUND:
            if char < 0x20 or char == u"\x7f" or char == "\x9b":
                self.escape_buffer.len = 0
                fbuf_putucs4(&self.escape_buffer, char)
        elif self.parser_state == ESCAPE:
            fbuf_putucs4(&self.escape_buffer, char)
            if char == u"[":
                self.parser_state = CSI
            elif char == u"O":
                self.parser_state = EXECUTE_NEXT
            elif char == u"]":
                self.parser_state = OSC
            else:
                self.execute()
        elif self.parser_state == CSI:
            fbuf_putucs4(&self.escape_buffer, char)
            if char == u"[":
                self.parser_state = EXECUTE_NEXT
            elif char == u"<" or char == u"?":
                self.parser_state = PARAMS
            elif 0x30 <= char <= 0x39 or char == 0x3B:
                self.parser_state = PARAMS
            else:
                self.execute()
        elif self.parser_state == PARAMS:
            fbuf_putucs4(&self.escape_buffer, char)
            if not (0x30 <= char <= 0x39 or char == 0x3B):
                self.execute()

    cdef void execute(self):
        pass
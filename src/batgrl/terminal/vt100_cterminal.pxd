from .._fbuf cimport fbuf

ctypedef unsigned char uint8
ctypedef unsigned int uint


cdef struct TermInfo:
    const char *termname  # FIXME: necessary?
    bint in_alternate_screen
    int last_mouse_y
    int last_mouse_x
    int cursor_y
    int cursor_x
    uint8[3] fg_rgb
    uint8[3] bg_rgb
    uint[24] device_attributes  # FIXME: Find max size
    uint pixels_h
    uint pixels_w
    uint term_h
    uint term_w


ctypedef enum ParserState: GROUND, ESCAPE, CSI, OSC, PARAMS, PASTE, EXECUTE_NEXT


cdef class Vt100Terminal:
    cdef TermInfo terminfo
    cdef ParserState parser_state
    cdef fbuf escape_buffer
    cdef fbuf paste_buffer
    cdef fbuf out_buffer

    cpdef void _feed1(self, Py_UCS4 char)
    cdef void execute(self)

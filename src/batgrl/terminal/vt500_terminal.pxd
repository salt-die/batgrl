# distutils: language = c
# distutils: sources = src/batgrl/terminal/vt500_parser.c

from .._fbuf cimport fbuf

ctypedef unsigned char uint8
ctypedef unsigned int uint

cdef extern from "vt500_parser.h":
    enum state_t:
        CSI_ENTRY = 1
        CSI_IGNORE = 2
        CSI_INTERMEDIATE = 3
        CSI_PARAM = 4
        DCS_ENTRY = 5
        DCS_IGNORE = 6
        DCS_INTERMEDIATE = 7
        DCS_PARAM = 8
        DCS_PASSTHROUGH = 9
        ESCAPE = 10
        ESCAPE_INTERMEDIATE = 11
        GROUND = 12
        OSC_STRING = 13
        SOS_PM_APC_STRING = 14

    enum action_t:
        CLEAR = 1
        COLLECT = 2
        CSI_DISPATCH = 3
        ESC_DISPATCH = 4
        EXECUTE = 5
        HOOK = 6
        IGNORE = 7
        OSC_END = 8
        OSC_PUT = 9
        OSC_START = 10
        PARAM = 11
        PRINT = 12
        PUT = 13
        UNHOOK = 14
        ERROR = 15

    struct vtparse:
        state_t state
        callback_t callback_t
        unsigned char[2] intermediate_chars
        int intermediate_chars_len
        char ignore_flagged
        int[16] params
        int params_len
        unsigned int utf8_char
        int utf8_char_bytes

    ctypedef void (*callback_t)(vtparse*, action_t, Py_UCS4)

    void feed1(vtparse*, Py_UCS4 ch)

cdef struct TermInfo:
    const char *termname  # FIXME: necessary?
    bint in_alternate_screen
    bint in_paste
    bint in_ground
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


cdef class Vt100Terminal:
    cdef:
        vtparse parser_state
        TermInfo terminfo
        fbuf escape_buffer
        fbuf paste_buffer
        fbuf out_buffer

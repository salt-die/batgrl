from ._fbuf cimport fbuf
from .events import Event

ctypedef unsigned char uint8
ctypedef unsigned int uint
ctypedef enum ParserState: 
    CSI,
    CSI_PARAMS,
    DECRPM,
    ESCAPE,
    EXECUTE_NEXT,
    GROUND,
    OSC,
    PASTE,


cdef class Vt100Terminal:
    cdef:
        fbuf read_buf, in_buf, out_buf
        ParserState state
        int last_y, last_x
        bint skip_newline
        bint sum_supported
        bint sgr_pixels_mode

    cdef void add_event(Vt100Terminal, Event)
    cdef void feed1(Vt100Terminal, uint8)
    cdef void execute_ansi_escapes(Vt100Terminal)
    cdef void execute_csi(Vt100Terminal)
    cdef void execute_csi_params(Vt100Terminal)
    cdef void execute_mouse(Vt100Terminal, uint*, char)
    cdef void execute_osc(Vt100Terminal)
    cdef void execute_decrpm(Vt100Terminal)
    cdef void dsr_request(Vt100Terminal, bytes)
    cpdef void process_stdin(Vt100Terminal)

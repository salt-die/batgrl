# <https://vt100.net/emu/dec_ansi_parser>

ctypedef enum Actions: 
    NONE,
    IGNORE,
    EXECUTE,
    PRINT,
    CLEAR,
    COLLECT,
    ESC_DISPATCH,
    CSI_DISPATCH,
    HOOK,
    UNHOOK,
    PUT,
    OSC_START,
    OSC_END,
    OSC_PUT,

ctypedef enum States: 
    GROUND,
    ESCAPE,
    ESCAPE_INTERMEDIATE,
    SOS_PM_APC_STRING,
    DCS_ENTRY,
    DCS_INTERMEDIATE,
    DCS_PARAM,
    DCS_PASSTHROUGH,
    DCS_IGNORE,
    OSC_STRING,
    CSI_ENTRY,
    CSI_INTERMEDIATE,
    CSI_PARAM,
    CSI_IGNORE,

# [STATE][EVENTS][ACTION, TRANSITION]
cdef char[14][128][2] STATE_TRANSITIONS

cdef void setup_ground():
    cdef int i
    for i in range(0x18):
        char[GROUND][i][0] = EXECUTE
        char[GROUND][i][1] = NONE

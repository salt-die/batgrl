/*
 * This parser is based on <https://github.com/haberman/vtparse> which itself is based
 * on Paul Williams' DEC compatible state machine parser
 * <https://vt100.net/emu/dec_ansi_parser>.
 */

#define MAX_INTERMEDIATE_CHARS 2
#define MAX_PARAMS 16
#define ACTION(state_change) (state_change & 0x0F)
#define STATE(state_change)  (state_change >> 4)

typedef enum {
    CSI_ENTRY = 1,
    CSI_IGNORE = 2,
    CSI_INTERMEDIATE = 3,
    CSI_PARAM = 4,
    DCS_ENTRY = 5,
    DCS_IGNORE = 6,
    DCS_INTERMEDIATE = 7,
    DCS_PARAM = 8,
    DCS_PASSTHROUGH = 9,
    ESCAPE = 10,
    ESCAPE_INTERMEDIATE = 11,
    GROUND = 12,
    OSC_STRING = 13,
    SOS_PM_APC_STRING = 14,
 } state_t;

 typedef enum {
    CLEAR = 1,
    COLLECT = 2,
    CSI_DISPATCH = 3,
    ESC_DISPATCH = 4,
    EXECUTE = 5,
    HOOK = 6,
    IGNORE = 7,
    OSC_END = 8,
    OSC_PUT = 9,
    OSC_START = 10,
    PARAM = 11,
    PRINT = 12,
    PUT = 13,
    UNHOOK = 14,
    ERROR = 15,
 } action_t;

typedef void (*callback_t)(vtparse*, action_t, unsigned int);

typedef struct vtparse {
    state_t state;
    callback_t callback;
    unsigned char intermediate_chars[MAX_INTERMEDIATE_CHARS + 1];
    int intermediate_chars_len;
    char ignore_flagged;
    int params[MAX_PARAMS];
    int params_len;
    unsigned int utf8_char;
    int utf8_char_bytes;
} vtparse;

void feed1(vtparse *parser, unsigned int ch);

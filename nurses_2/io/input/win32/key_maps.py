from ..keys import Keys

__all__ = (
    "ANSI_SEQUENCES",
    "KEY_CODES",
    "CONTROL_SHIFT_KEYS",
    "CONTROL_KEYS",
    "SHIFT_KEYS",
)

ANSI_SEQUENCES = {
    b"\x1b": Keys.Escape,
    b"\x00": Keys.ControlSpace,        # Control-Space (Also for Ctrl-@)
    b"\x01": Keys.ControlA,            # Control-A (home)
    b"\x02": Keys.ControlB,            # Control-B (emacs cursor left)
    b"\x03": Keys.ControlC,            # Control-C (interrupt)
    b"\x04": Keys.ControlD,            # Control-D (exit)
    b"\x05": Keys.ControlE,            # Control-E (end)
    b"\x06": Keys.ControlF,            # Control-F (cursor forward)
    b"\x07": Keys.ControlG,            # Control-G
    b"\x08": Keys.ControlH,            # Control-H (8) (Identical to '\b')
    b"\x09": Keys.ControlI,            # Control-I (9) (Identical to '\t')
    b"\x0a": Keys.ControlJ,            # Control-J (10) (Identical to '\n')
    b"\x0b": Keys.ControlK,            # Control-K (delete until end of line; vertical tab)
    b"\x0c": Keys.ControlL,            # Control-L (clear; form feed)
    b"\x0d": Keys.ControlM,            # Control-M (enter)
    b"\x0e": Keys.ControlN,            # Control-N (14) (history forward)
    b"\x0f": Keys.ControlO,            # Control-O (15)
    b"\x10": Keys.ControlP,            # Control-P (16) (history back)
    b"\x11": Keys.ControlQ,            # Control-Q
    b"\x12": Keys.ControlR,            # Control-R (18) (reverse search)
    b"\x13": Keys.ControlS,            # Control-S (19) (forward search)
    b"\x14": Keys.ControlT,            # Control-T
    b"\x15": Keys.ControlU,            # Control-U
    b"\x16": Keys.ControlV,            # Control-V
    b"\x17": Keys.ControlW,            # Control-W
    b"\x18": Keys.ControlX,            # Control-X
    b"\x19": Keys.ControlY,            # Control-Y (25)
    b"\x1a": Keys.ControlZ,            # Control-Z
    b"\x1c": Keys.ControlBackslash,    # Both Control-\ and Ctrl-|
    b"\x1d": Keys.ControlSquareClose,  # Control-]
    b"\x1e": Keys.ControlCircumflex,   # Control-^
    b"\x1f": Keys.ControlUnderscore,   # Control-underscore (Also for Ctrl-hyphen.)
    b"\x7f": Keys.Backspace,           # (127) Backspace   (ASCII Delete.)
}

KEY_CODES = {
    # Home/End
    33: Keys.PageUp,
    34: Keys.PageDown,
    35: Keys.End,
    36: Keys.Home,
    # Arrows
    37: Keys.Left,
    38: Keys.Up,
    39: Keys.Right,
    40: Keys.Down,
    45: Keys.Insert,
    46: Keys.Delete,
    # F-keys.
    112: Keys.F1,
    113: Keys.F2,
    114: Keys.F3,
    115: Keys.F4,
    116: Keys.F5,
    117: Keys.F6,
    118: Keys.F7,
    119: Keys.F8,
    120: Keys.F9,
    121: Keys.F10,
    122: Keys.F11,
    123: Keys.F12,
}

CONTROL_SHIFT_KEYS = {
    Keys.Left: Keys.ControlShiftLeft,
    Keys.Right: Keys.ControlShiftRight,
    Keys.Up: Keys.ControlShiftUp,
    Keys.Down: Keys.ControlShiftDown,
    Keys.Home: Keys.ControlShiftHome,
    Keys.End: Keys.ControlShiftEnd,
    Keys.Insert: Keys.ControlShiftInsert,
    Keys.PageUp: Keys.ControlShiftPageUp,
    Keys.PageDown: Keys.ControlShiftPageDown,
}

CONTROL_KEYS = {
    Keys.Left: Keys.ControlLeft,
    Keys.Right: Keys.ControlRight,
    Keys.Up: Keys.ControlUp,
    Keys.Down: Keys.ControlDown,
    Keys.Home: Keys.ControlHome,
    Keys.End: Keys.ControlEnd,
    Keys.Insert: Keys.ControlInsert,
    Keys.Delete: Keys.ControlDelete,
    Keys.PageUp: Keys.ControlPageUp,
    Keys.PageDown: Keys.ControlPageDown,
}

SHIFT_KEYS = {
    Keys.Tab: Keys.BackTab,
    Keys.Left: Keys.ShiftLeft,
    Keys.Right: Keys.ShiftRight,
    Keys.Up: Keys.ShiftUp,
    Keys.Down: Keys.ShiftDown,
    Keys.Home: Keys.ShiftHome,
    Keys.End: Keys.ShiftEnd,
    Keys.Insert: Keys.ShiftInsert,
    Keys.Delete: Keys.ShiftDelete,
    Keys.PageUp: Keys.ShiftPageUp,
    Keys.PageDown: Keys.ShiftPageDown,
}

from ..keys import Key

__all__ = (
    "ANSI_SEQUENCES",
    "KEY_CODES",
    "CONTROL_SHIFT_KEYS",
    "CONTROL_KEYS",
    "SHIFT_KEYS",
)

ANSI_SEQUENCES = {
    b"\x1b": Key.Escape,
    b"\x00": Key.ControlSpace,        # Control-Space (Also for Ctrl-@)
    b"\x01": Key.ControlA,            # Control-A (home)
    b"\x02": Key.ControlB,            # Control-B (emacs cursor left)
    b"\x03": Key.ControlC,            # Control-C (interrupt)
    b"\x04": Key.ControlD,            # Control-D (exit)
    b"\x05": Key.ControlE,            # Control-E (end)
    b"\x06": Key.ControlF,            # Control-F (cursor forward)
    b"\x07": Key.ControlG,            # Control-G
    b"\x08": Key.ControlH,            # Control-H (8) (Identical to '\b')
    b"\x09": Key.ControlI,            # Control-I (9) (Identical to '\t')
    b"\x0a": Key.ControlJ,            # Control-J (10) (Identical to '\n')
    b"\x0b": Key.ControlK,            # Control-K (delete until end of line; vertical tab)
    b"\x0c": Key.ControlL,            # Control-L (clear; form feed)
    b"\x0d": Key.ControlM,            # Control-M (enter)
    b"\x0e": Key.ControlN,            # Control-N (14) (history forward)
    b"\x0f": Key.ControlO,            # Control-O (15)
    b"\x10": Key.ControlP,            # Control-P (16) (history back)
    b"\x11": Key.ControlQ,            # Control-Q
    b"\x12": Key.ControlR,            # Control-R (18) (reverse search)
    b"\x13": Key.ControlS,            # Control-S (19) (forward search)
    b"\x14": Key.ControlT,            # Control-T
    b"\x15": Key.ControlU,            # Control-U
    b"\x16": Key.ControlV,            # Control-V
    b"\x17": Key.ControlW,            # Control-W
    b"\x18": Key.ControlX,            # Control-X
    b"\x19": Key.ControlY,            # Control-Y (25)
    b"\x1a": Key.ControlZ,            # Control-Z
    b"\x1c": Key.ControlBackslash,    # Both Control-\ and Ctrl-|
    b"\x1d": Key.ControlSquareClose,  # Control-]
    b"\x1e": Key.ControlCircumflex,   # Control-^
    b"\x1f": Key.ControlUnderscore,   # Control-underscore (Also for Ctrl-hyphen.)
    b"\x7f": Key.Backspace,           # (127) Backspace   (ASCII Delete.)
}

KEY_CODES = {
    # Home/End
    33: Key.PageUp,
    34: Key.PageDown,
    35: Key.End,
    36: Key.Home,
    # Arrows
    37: Key.Left,
    38: Key.Up,
    39: Key.Right,
    40: Key.Down,
    45: Key.Insert,
    46: Key.Delete,
    # F-keys.
    112: Key.F1,
    113: Key.F2,
    114: Key.F3,
    115: Key.F4,
    116: Key.F5,
    117: Key.F6,
    118: Key.F7,
    119: Key.F8,
    120: Key.F9,
    121: Key.F10,
    122: Key.F11,
    123: Key.F12,
}

CONTROL_SHIFT_KEYS = {
    Key.Left: Key.ControlShiftLeft,
    Key.Right: Key.ControlShiftRight,
    Key.Up: Key.ControlShiftUp,
    Key.Down: Key.ControlShiftDown,
    Key.Home: Key.ControlShiftHome,
    Key.End: Key.ControlShiftEnd,
    Key.Insert: Key.ControlShiftInsert,
    Key.PageUp: Key.ControlShiftPageUp,
    Key.PageDown: Key.ControlShiftPageDown,
}

CONTROL_KEYS = {
    " ": Key.ControlSpace,
    Key.ControlJ: Key.Escape,  # I'm unsure why prompt-toolkit converted this to Escape.

    Key.Left: Key.ControlLeft,
    Key.Right: Key.ControlRight,
    Key.Up: Key.ControlUp,
    Key.Down: Key.ControlDown,
    Key.Home: Key.ControlHome,
    Key.End: Key.ControlEnd,
    Key.Insert: Key.ControlInsert,
    Key.Delete: Key.ControlDelete,
    Key.PageUp: Key.ControlPageUp,
    Key.PageDown: Key.ControlPageDown,

    Key.F1: Key.ControlF1,
    Key.F2: Key.ControlF2,
    Key.F3: Key.ControlF3,
    Key.F4: Key.ControlF4,
    Key.F5: Key.ControlF5,
    Key.F6: Key.ControlF6,
    Key.F7: Key.ControlF7,
    Key.F8: Key.ControlF8,
    Key.F9: Key.ControlF9,
    Key.F10: Key.ControlF10,
    Key.F11: Key.ControlF11,
    Key.F12: Key.ControlF12,
    Key.F13: Key.ControlF13,
    Key.F14: Key.ControlF14,
    Key.F15: Key.ControlF15,
    Key.F16: Key.ControlF16,
    Key.F17: Key.ControlF17,
    Key.F18: Key.ControlF18,
    Key.F19: Key.ControlF19,
    Key.F20: Key.ControlF20,
    Key.F21: Key.ControlF21,
    Key.F22: Key.ControlF22,
    Key.F23: Key.ControlF23,
    Key.F24: Key.ControlF24,
}

SHIFT_KEYS = {
    Key.Tab: Key.BackTab,
    Key.Left: Key.ShiftLeft,
    Key.Right: Key.ShiftRight,
    Key.Up: Key.ShiftUp,
    Key.Down: Key.ShiftDown,
    Key.Home: Key.ShiftHome,
    Key.End: Key.ShiftEnd,
    Key.Insert: Key.ShiftInsert,
    Key.Delete: Key.ShiftDelete,
    Key.PageUp: Key.ShiftPageUp,
    Key.PageDown: Key.ShiftPageDown,
}

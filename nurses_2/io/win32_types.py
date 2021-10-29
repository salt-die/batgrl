from ctypes import Structure, Union, c_char, c_long, c_short, c_ulong
from ctypes.wintypes import BOOL, DWORD, LPVOID, WCHAR, WORD

STD_INPUT_HANDLE = c_ulong(-10)
STD_OUTPUT_HANDLE = c_ulong(-11)


class COORD(Structure):
    """
    Struct in wincon.h
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119(v=vs.85).aspx
    """

    _fields_ = [
        ("X", c_short),  # Short
        ("Y", c_short),  # Short
    ]

    def __repr__(self):
        return (
            f"{self.__class__.__name__,}("
            f"X={self.X!r}, "
            f"Y={self.Y!r}, "
            f"type_x={type(self.X)!r}, "
            f"type_y={type(self.Y)!r})"
        )


class UNICODE_OR_ASCII(Union):
    _fields_ = [
        ("AsciiChar", c_char),
        ("UnicodeChar", WCHAR),
    ]


class KEY_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684166(v=vs.85).aspx
    """
    _fields_ = [
        ("KeyDown", c_long),  # bool
        ("RepeatCount", c_short),  # word
        ("VirtualKeyCode", c_short),  # word
        ("VirtualScanCode", c_short),  # word
        ("uChar", UNICODE_OR_ASCII),  # Unicode or ASCII.
        ("ControlKeyState", c_long),  # double word
    ]


class MOUSE_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684239(v=vs.85).aspx
    """
    _fields_ = [
        ("MousePosition", COORD),
        ("ButtonState", c_long),  # dword
        ("ControlKeyState", c_long),  # dword
        ("EventFlags", c_long),  # dword
    ]


class WINDOW_BUFFER_SIZE_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687093(v=vs.85).aspx
    """
    _fields_ = [("Size", COORD)]


class MENU_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684213(v=vs.85).aspx
    """
    _fields_ = [("CommandId", c_long)]  # uint


class FOCUS_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683149(v=vs.85).aspx
    """
    _fields_ = [("SetFocus", c_long)]  # bool


class EVENT_RECORD(Union):
    _fields_ = [
        ("KeyEvent", KEY_EVENT_RECORD),
        ("MouseEvent", MOUSE_EVENT_RECORD),
        ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ("MenuEvent", MENU_EVENT_RECORD),
        ("FocusEvent", FOCUS_EVENT_RECORD),
    ]


class INPUT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683499(v=vs.85).aspx
    """
    _fields_ = [("EventType", c_short), ("Event", EVENT_RECORD)]  # word  # Union.


EventTypes = {
    1: "KeyEvent",
    2: "MouseEvent",
    4: "WindowBufferSizeEvent",
    8: "MenuEvent",
    16: "FocusEvent",
}


class SMALL_RECT(Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("Left", c_short),
        ("Top", c_short),
        ("Right", c_short),
        ("Bottom", c_short),
    ]


class CONSOLE_SCREEN_BUFFER_INFO(Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]

    def __repr__(self) -> str:
        return (
            "CONSOLE_SCREEN_BUFFER_INFO("
            f"{self.dwSize.Y}, "
            f"{self.dwSize.X}, "
            f"{self.dwCursorPosition.Y}, "
            f"{self.dwCursorPosition.X}, "
            f"{self.wAttributes}, "
            f"{self.srWindow.Top}, "
            f"{self.srWindow.Left}, "
            f"{self.srWindow.Bottom}, "
            f"{self.srWindow.Right}, "
            f"{self.dwMaximumWindowSize.Y}, "
            f"{self.dwMaximumWindowSize.X})"
        )


class SECURITY_ATTRIBUTES(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa379560(v=vs.85).aspx
    """
    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", BOOL),
    ]

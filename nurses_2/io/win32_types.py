from ctypes import Structure, Union, c_char, c_long, c_short, c_ulong, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPVOID, WCHAR, WORD

STD_INPUT_HANDLE = HANDLE(windll.kernel32.GetStdHandle(c_ulong(-10)))
STD_OUTPUT_HANDLE = HANDLE(windll.kernel32.GetStdHandle(c_ulong(-11)))


class COORD(Structure):
    """
    Struct in wincon.h
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119(v=vs.85).aspx
    """
    _fields_ = [
        ("X", c_short),
        ("Y", c_short),
    ]


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
        ("KeyDown", c_long),
        ("RepeatCount", c_short),
        ("VirtualKeyCode", c_short),
        ("VirtualScanCode", c_short),
        ("uChar", UNICODE_OR_ASCII),
        ("ControlKeyState", c_long),
    ]


class MOUSE_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684239(v=vs.85).aspx
    """
    _fields_ = [
        ("MousePosition", COORD),
        ("ButtonState", c_long),
        ("ControlKeyState", c_long),
        ("EventFlags", c_long),
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
    _fields_ = [("CommandId", c_long)]


class FOCUS_EVENT_RECORD(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683149(v=vs.85).aspx
    """
    _fields_ = [("SetFocus", c_long)]


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
    _fields_ = [("EventType", c_short), ("Event", EVENT_RECORD)]


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


class SECURITY_ATTRIBUTES(Structure):
    """
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa379560(v=vs.85).aspx
    """
    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", BOOL),
    ]

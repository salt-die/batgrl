"""Ctypes for windows."""
from ctypes import Structure, Union, windll
from ctypes.wintypes import BOOL, CHAR, DWORD, HANDLE, LONG, LPVOID, SHORT, WCHAR

STD_INPUT_HANDLE = HANDLE(windll.kernel32.GetStdHandle(DWORD(-10)))
STD_OUTPUT_HANDLE = HANDLE(windll.kernel32.GetStdHandle(DWORD(-11)))


class COORD(Structure):
    """
    Windows coord struct.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119(v=vs.85).aspx
    """

    _fields_ = [("X", SHORT), ("Y", SHORT)]


class UNICODE_OR_ASCII(Union):
    """Windows character."""

    _fields_ = [("AsciiChar", CHAR), ("UnicodeChar", WCHAR)]


class KEY_EVENT_RECORD(Structure):
    """
    Windows key event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684166(v=vs.85).aspx
    """

    _fields_ = [
        ("KeyDown", LONG),
        ("RepeatCount", SHORT),
        ("VirtualKeyCode", SHORT),
        ("VirtualScanCode", SHORT),
        ("uChar", UNICODE_OR_ASCII),
        ("ControlKeyState", LONG),
    ]


class MOUSE_EVENT_RECORD(Structure):
    """
    Windows mouse event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684239(v=vs.85).aspx
    """

    _fields_ = [
        ("MousePosition", COORD),
        ("ButtonState", LONG),
        ("ControlKeyState", LONG),
        ("EventFlags", LONG),
    ]


class WINDOW_BUFFER_SIZE_RECORD(Structure):
    """
    Windows buffer size record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687093(v=vs.85).aspx
    """

    _fields_ = [("Size", COORD)]


class MENU_EVENT_RECORD(Structure):
    """
    Windows menu event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684213(v=vs.85).aspx
    """

    _fields_ = [("CommandId", LONG)]


class FOCUS_EVENT_RECORD(Structure):
    """
    Windows focus event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683149(v=vs.85).aspx
    """

    _fields_ = [("SetFocus", LONG)]


class EVENT_RECORD(Union):
    """Windows event record."""

    _fields_ = [
        ("KeyEvent", KEY_EVENT_RECORD),
        ("MouseEvent", MOUSE_EVENT_RECORD),
        ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ("MenuEvent", MENU_EVENT_RECORD),
        ("FocusEvent", FOCUS_EVENT_RECORD),
    ]


class INPUT_RECORD(Structure):
    """
    Windows input record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683499(v=vs.85).aspx
    """

    _fields_ = [("EventType", SHORT), ("Event", EVENT_RECORD)]


class SECURITY_ATTRIBUTES(Structure):
    """
    Windows security attributes.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa379560(v=vs.85).aspx
    """

    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", BOOL),
    ]

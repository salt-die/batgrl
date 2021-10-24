from ctypes import pointer
from ctypes import windll
from ctypes.wintypes import BOOL, DWORD, HANDLE

from ...win32_types import SECURITY_ATTRIBUTES

WAIT_TIMEOUT = 0x00000102
INFINITE = -1

def wait_for_handles(*handles, timeout=INFINITE):
    arrtype = HANDLE * len(handles)
    handle_array = arrtype(*handles)

    ret = windll.kernel32.WaitForMultipleObjects(
        len(handle_array), handle_array, BOOL(False), DWORD(timeout)
    )

    if ret != WAIT_TIMEOUT:
        return handles[ret]

def create_win32_event() -> HANDLE:
    """
    Creates a Win32 unnamed Event .
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682396(v=vs.85).aspx
    """
    return HANDLE(
        windll.kernel32.CreateEventA(
            pointer(SECURITY_ATTRIBUTES()),
            BOOL(True),  # Manual reset event.
            BOOL(False),  # Initial state.
            None,  # Unnamed event object.
        )
    )

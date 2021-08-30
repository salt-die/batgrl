import os
import sys
from ctypes import (
    ArgumentError,
    byref,
    c_char,
    c_long,
    c_short,
    c_uint,
    c_ulong,
    pointer,
)
from ctypes import windll
from ctypes.wintypes import DWORD, HANDLE

from ...widgets.widget_data_structures import Size
from ..win32_types import (
    CONSOLE_SCREEN_BUFFER_INFO,
    COORD,
    SMALL_RECT,
    STD_INPUT_HANDLE,
    STD_OUTPUT_HANDLE,
)

def _coord_byval(coord: COORD):
    """
    Turns a COORD object into a c_long.
    This will cause it to be passed by value instead of by reference. (That is what I think at least.)

    When running ``ptipython`` is run (only with IPython), we often got the following error::

         Error in 'SetConsoleCursorPosition'.
         ArgumentError("argument 2: <class 'TypeError'>: wrong type",)
     argument 2: <class 'TypeError'>: wrong type

    It was solved by turning ``COORD`` parameters into a ``c_long`` like this.

    More info: http://msdn.microsoft.com/en-us/library/windows/desktop/ms686025(v=vs.85).aspx
    """
    return c_long(coord.Y * 0x10000 | coord.X & 0xFFFF)


class NoConsoleScreenBufferError(Exception):
    """
    Raised when the application is not running inside a Windows Console, but
    the user tries to instantiate Win32Output.
    """

    def __init__(self):
        # Are we running in 'xterm' on Windows, like git-bash for instance?
        xterm = "xterm" in os.environ.get("TERM", "")

        if xterm:
            message = (
                "Found %s, while expecting a Windows console. "
                'Maybe try to run this program using "winpty" '
                "or run it in cmd.exe instead. Or otherwise, "
                "in case of Cygwin, use the Python executable "
                "that is compiled for Cygwin." % os.environ["TERM"]
            )
        else:
            message = "No Windows console found. Are you running cmd.exe?"
        super().__init__(message)


class Win32Output:
    """
    I/O abstraction for rendering to Windows consoles.
    (cmd.exe and similar.)
    """

    def __init__(self):
        self._buffer = [ ]
        self.stdout = sys.stdout
        self.hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))

        self._in_alternate_screen = False

        # Remember the default console colors.
        info = self.get_win32_screen_buffer_info()
        self.default_attrs = info.wAttributes if info else 15

    def fileno(self):
        "Return file descriptor."
        return self.stdout.fileno()

    def encoding(self):
        "Return encoding used for stdout."
        return self.stdout.encoding

    def write(self, data):
        self._buffer.append(data)

    def write_raw(self, data):
        "For win32, there is no difference between write and write_raw."
        self.write(data)

    def get_size(self) -> Size:
        info = self.get_win32_screen_buffer_info()

        width = info.srWindow.Right - info.srWindow.Left

        height = info.srWindow.Bottom - info.srWindow.Top + 1

        # We avoid the right margin, windows will wrap otherwise.
        maxwidth = info.dwSize.X - 1
        width = min(maxwidth, width)

        # Create `Size` object.
        return Size(height, width)

    def _winapi(self, func, *args, **kwargs):
        """
        Flush and call win API function.
        """
        self.flush()
        return func(*args, **kwargs)

    def get_win32_screen_buffer_info(self) -> CONSOLE_SCREEN_BUFFER_INFO:
        """
        Return Screen buffer info.
        """
        # NOTE: We don't call the `GetConsoleScreenBufferInfo` API through
        #     `self._winapi`. Doing so causes Python to crash on certain 64bit
        #     Python versions. (Reproduced with 64bit Python 2.7.6, on Windows
        #     10). It is not clear why. Possibly, it has to do with passing
        #     these objects as an argument, or through *args.

        # The Python documentation contains the following - possibly related - warning:
        #     ctypes does not support passing unions or structures with
        #     bit-fields to functions by value. While this may work on 32-bit
        #     x86, it's not guaranteed by the library to work in the general
        #     case. Unions and structures with bit-fields should always be
        #     passed to functions by pointer.

        # Also see:
        #    - https://github.com/ipython/ipython/issues/10070
        #    - https://github.com/jonathanslenders/python-prompt-toolkit/issues/406
        #    - https://github.com/jonathanslenders/python-prompt-toolkit/issues/86

        self.flush()
        sbinfo = CONSOLE_SCREEN_BUFFER_INFO()
        success = windll.kernel32.GetConsoleScreenBufferInfo(
            self.hconsole, byref(sbinfo)
        )

        # success = self._winapi(windll.kernel32.GetConsoleScreenBufferInfo,
        #                        self.hconsole, byref(sbinfo))

        if success:
            return sbinfo
        else:
            raise NoConsoleScreenBufferError()

    def set_title(self, title):
        """
        Set terminal title.
        """
        self._winapi(windll.kernel32.SetConsoleTitleW, title)

    def clear_title(self):
        self._winapi(windll.kernel32.SetConsoleTitleW, "")

    def erase_screen(self):
        start = COORD(0, 0)
        sbinfo = self.get_win32_screen_buffer_info()
        length = sbinfo.dwSize.X * sbinfo.dwSize.Y

        self.cursor_goto(row=0, column=0)
        self._erase(start, length)

    def erase_down(self):
        sbinfo = self.get_win32_screen_buffer_info()
        size = sbinfo.dwSize

        start = sbinfo.dwCursorPosition
        length = (size.X - size.X) + size.X * (size.Y - sbinfo.dwCursorPosition.Y)

        self._erase(start, length)

    def erase_end_of_line(self):
        """"""
        sbinfo = self.get_win32_screen_buffer_info()
        start = sbinfo.dwCursorPosition
        length = sbinfo.dwSize.X - sbinfo.dwCursorPosition.X

        self._erase(start, length)

    def _erase(self, start: COORD, length: int):
        chars_written = c_ulong()

        self._winapi(
            windll.kernel32.FillConsoleOutputCharacterA,
            self.hconsole,
            c_char(b" "),
            DWORD(length),
            _coord_byval(start),
            byref(chars_written),
        )

        # Reset attributes.
        sbinfo = self.get_win32_screen_buffer_info()
        self._winapi(
            windll.kernel32.FillConsoleOutputAttribute,
            self.hconsole,
            sbinfo.wAttributes,
            length,
            _coord_byval(start),
            byref(chars_written),
        )

    def reset_attributes(self):
        "Reset the console foreground/background color."
        self._winapi(
            windll.kernel32.SetConsoleTextAttribute, self.hconsole, self.default_attrs
        )

    def disable_autowrap(self):
        # Not supported by Windows.
        pass

    def enable_autowrap(self):
        # Not supported by Windows.
        pass

    def cursor_goto(self, row=0, column=0):
        pos = COORD(X=column, Y=row)
        self._winapi(
            windll.kernel32.SetConsoleCursorPosition, self.hconsole, _coord_byval(pos)
        )

    def cursor_up(self, amount):
        sr = self.get_win32_screen_buffer_info().dwCursorPosition
        pos = COORD(X=sr.X, Y=sr.Y - amount)
        self._winapi(
            windll.kernel32.SetConsoleCursorPosition, self.hconsole, _coord_byval(pos)
        )

    def cursor_down(self, amount):
        self.cursor_up(-amount)

    def cursor_forward(self, amount):
        sr = self.get_win32_screen_buffer_info().dwCursorPosition
        #        assert sr.X + amount >= 0, 'Negative cursor position: x=%r amount=%r' % (sr.X, amount)

        pos = COORD(X=max(0, sr.X + amount), Y=sr.Y)
        self._winapi(
            windll.kernel32.SetConsoleCursorPosition, self.hconsole, _coord_byval(pos)
        )

    def cursor_backward(self, amount):
        self.cursor_forward(-amount)

    def flush(self):
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            # Only flush stdout buffer. (It could be that Python still has
            # something in its buffer. -- We want to be sure to print that in
            # the correct color.)
            self.stdout.flush()
            return

        data = "".join(self._buffer)

        # Print characters one by one. This appears to be the best solution
        # in oder to avoid traces of vertical lines when the completion
        # menu disappears.
        for b in data:
            written = DWORD()

            retval = windll.kernel32.WriteConsoleW(
                self.hconsole, b, 1, byref(written), None
            )
            assert retval != 0

        self._buffer = []

    def get_rows_below_cursor_position(self):
        info = self.get_win32_screen_buffer_info()
        return info.srWindow.Bottom - info.dwCursorPosition.Y + 1

    def scroll_buffer_to_prompt(self):
        """
        To be called before drawing the prompt. This should scroll the console
        to left, with the cursor at the bottom (if possible).
        """
        # Get current window size
        info = self.get_win32_screen_buffer_info()
        sr = info.srWindow
        cursor_pos = info.dwCursorPosition

        result = SMALL_RECT()

        # Scroll to the left.
        result.Left = 0
        result.Right = sr.Right - sr.Left

        # Scroll vertical
        win_height = sr.Bottom - sr.Top
        if 0 < sr.Bottom - cursor_pos.Y < win_height - 1:
            # no vertical scroll if cursor already on the screen
            result.Bottom = sr.Bottom
        else:
            result.Bottom = max(win_height, cursor_pos.Y)
        result.Top = result.Bottom - win_height

        # Scroll API
        self._winapi(
            windll.kernel32.SetConsoleWindowInfo, self.hconsole, True, byref(result)
        )

    def enter_alternate_screen(self):
        """
        Go to alternate screen buffer.
        """
        if not self._in_alternate_screen:
            GENERIC_READ = 0x80000000
            GENERIC_WRITE = 0x40000000

            # Create a new console buffer and activate that one.
            handle = HANDLE(
                self._winapi(
                    windll.kernel32.CreateConsoleScreenBuffer,
                    GENERIC_READ | GENERIC_WRITE,
                    DWORD(0),
                    None,
                    DWORD(1),
                    None,
                )
            )

            self._winapi(windll.kernel32.SetConsoleActiveScreenBuffer, handle)
            self.hconsole = handle
            self._in_alternate_screen = True

    def quit_alternate_screen(self):
        """
        Make stdout again the active buffer.
        """
        if self._in_alternate_screen:
            stdout = HANDLE(
                self._winapi(windll.kernel32.GetStdHandle, STD_OUTPUT_HANDLE)
            )
            self._winapi(windll.kernel32.SetConsoleActiveScreenBuffer, stdout)
            self._winapi(windll.kernel32.CloseHandle, self.hconsole)
            self.hconsole = stdout
            self._in_alternate_screen = False

    def enable_mouse_support(self):
        ENABLE_MOUSE_INPUT = 0x10

        # This `ENABLE_QUICK_EDIT_MODE` flag needs to be cleared for mouse
        # support to work, but it's possible that it was already cleared
        # before.
        ENABLE_QUICK_EDIT_MODE = 0x0040

        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        self._winapi(windll.kernel32.GetConsoleMode, handle, pointer(original_mode))
        self._winapi(
            windll.kernel32.SetConsoleMode,
            handle,
            (original_mode.value | ENABLE_MOUSE_INPUT) & ~ENABLE_QUICK_EDIT_MODE,
        )

    def disable_mouse_support(self):
        ENABLE_MOUSE_INPUT = 0x10
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        self._winapi(windll.kernel32.GetConsoleMode, handle, pointer(original_mode))
        self._winapi(
            windll.kernel32.SetConsoleMode,
            handle,
            original_mode.value & ~ENABLE_MOUSE_INPUT,
        )

    def hide_cursor(self):
        pass

    def show_cursor(self):
        pass

    @classmethod
    def win32_refresh_window(cls):
        """
        Call win32 API to refresh the whole Window.

        This is sometimes necessary when the application paints background
        for completion menus. When the menu disappears, it leaves traces due
        to a bug in the Windows Console. Sending a repaint request solves it.
        """
        # Get console handle
        handle = HANDLE(windll.kernel32.GetConsoleWindow())

        RDW_INVALIDATE = 0x0001
        windll.user32.RedrawWindow(handle, None, None, c_uint(RDW_INVALIDATE))

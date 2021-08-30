from ...widgets.widget_data_structures import Size
from .vt100 import Vt100_Output
from .win32 import Win32Output


class ConEmuOutput:
    """
    ConEmu (Windows) output abstraction.
    """

    def __init__(self):
        self.win32_output = Win32Output(stdout)
        self.vt100_output = Vt100_Output(stdout, lambda: Size(0, 0))

    def __getattr__(self, name):
        if name in (
            "get_size",
            "get_rows_below_cursor_position",
            "enable_mouse_support",
            "disable_mouse_support",
            "scroll_buffer_to_prompt",
            "get_win32_screen_buffer_info",
            "enable_bracketed_paste",
            "disable_bracketed_paste",
        ):
            return getattr(self.win32_output, name)
        else:
            return getattr(self.vt100_output, name)

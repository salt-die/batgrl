"""
Patch prompt_toolkit's Vt100_Output's enable_mouse_support to receive mouse movement events.
"""

from prompt_toolkit.output.vt100 import Vt100_Output

def patch_vt100_output():
    def enable_mouse_support(self):
        self.write_raw("\x1b[?1000h")
        self.write_raw("\x1b[?1003h")  # ANY_EVENT_MOUSE
        self.write_raw("\x1b[?1015h")
        self.write_raw("\x1b[?1006h")

    def disable_mouse_support(self):
        self.write_raw("\x1b[?1000l")
        self.write_raw("\x1b[?1003l")  # DISABLE ANY_EVENT_MOUSE
        self.write_raw("\x1b[?1015l")
        self.write_raw("\x1b[?1006l")

    Vt100_Output.enable_mouse_support = enable_mouse_support
    Vt100_Output.disable_mouse_support = disable_mouse_support

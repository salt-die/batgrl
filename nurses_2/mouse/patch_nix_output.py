def patch_nix_output(nix_input):
    """
    Add ANY_EVENT_MOUSE mode to other mouse modes.  This to allow mouse movement tracking.
    """
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

    input_cls = type(nix_input)
    input_cls.enable_mouse_support = enable_mouse_support
    input_cls.disable_mouse_support = disable_mouse_support

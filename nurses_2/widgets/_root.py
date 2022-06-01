"""
Root widget.
"""
import numpy as np

from ..colors import ColorPair
from ..data_structures import *
from ..io import KeyPressEvent, MouseEvent, PasteEvent
from .widget import Widget


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(
        self,
        app: "App",
        env_out: "Vt100_Output",
        background_char: str,
        background_color_pair: ColorPair,
    ):
        self._app = app
        self.children = [ ]
        self.env_out = env_out
        self.background_char = background_char
        self.background_color_pair = background_color_pair

        self.size = env_out.get_size()

    def on_size(self):
        """
        Erase last render and re-make buffers.
        """
        h, w = self._size

        self.env_out.erase_screen()
        self.env_out.flush()

        self._last_canvas = np.full((h, w), self.background_char, dtype=object)
        self._last_colors = np.full((h, w, 6), self.background_color_pair, dtype=np.uint8)

        invalidate_char = "a" if "a" != self.background_char else "b"  # A character that guarantees full-screen redraw.
        self.canvas = np.full_like(self._last_canvas, invalidate_char)
        self.colors = self._last_colors.copy()

        # Buffer arrays to re-use in the `render` method:
        self._char_diffs = np.zeros_like(self.canvas, dtype=bool)
        self._color_diffs = np.zeros_like(self.colors, dtype=bool)
        self._reduced_color_diffs = np.zeros_like(self.canvas, dtype=bool)

    @property
    def pos(self):
        return Point(0, 0)

    @property
    def absolute_pos(self):
        return Point(0, 0)

    @property
    def is_transparent(self):
        return False

    @property
    def is_visible(self):
        return True

    @property
    def is_enabled(self):
        return True

    @property
    def parent(self):
        return None

    @property
    def root(self):
        return self

    @property
    def app(self):
        return self._app

    def to_local(self, point: Point) -> Point:
        return point

    def collides_point(self, point: Point) -> bool:
        return True

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        # Swap canvas with last render:
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.colors, self._last_colors = self._last_colors, self.colors

        # Bring arrays into locals:
        canvas = self.canvas
        colors = self.colors

        char_diffs = self._char_diffs
        color_diffs = self._color_diffs
        reduced_color_diffs = self._reduced_color_diffs

        env_out = self.env_out
        write = env_out._buffer.append

        # Erase canvas:
        canvas[:] = self.background_char
        colors[:, :] = self.background_color_pair

        height, width = canvas.shape

        self.render_children(np.s_[0: height, 0: width], canvas, colors)

        # Find differences between current render and last render:
        # (`(last_canvas != canvas) | np.any(last_colors != colors, axis=-1)` with buffers.)
        np.not_equal(self._last_canvas, canvas, out=char_diffs)
        np.not_equal(self._last_colors, colors, out=color_diffs)
        np.any(color_diffs, axis=-1, out=reduced_color_diffs)
        np.logical_or(char_diffs, reduced_color_diffs, out=char_diffs)

        if char_diffs.any():
            write("\x1b[?25l")  # Hide cursor

            ys, xs = np.nonzero(char_diffs)
            for y, x, color, char in zip(ys, xs, colors[ys, xs], canvas[ys, xs]):
                # The escape codes for moving the cursor and setting the color concatenated:
                write("\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m{}".format(y + 1, x + 1, *color, char))

            write("\x1b[0m")  # Reset attributes
            env_out.flush()

    def dispatch_press(self, key_press_event: KeyPressEvent):
        """
        Dispatch key press to descendants until handled.
        """
        any(
            widget.dispatch_press(key_press_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        )

    def dispatch_click(self, mouse_event: MouseEvent):
        """
        Dispatch mouse event to descendents until handled.
        """
        any(
            widget.dispatch_click(mouse_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        )

    def dispatch_paste(self, paste_event: PasteEvent):
        """
        Dispatch paste event to descendents until handled.
        """
        any(
            widget.dispatch_paste(paste_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        )

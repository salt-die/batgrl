"""
A gadget that replaces SGR parameters of cells beneath it.

Cursor over sixel cells will do nothing.
"""

import numpy as np
from numpy.typing import NDArray

from .._rendering import cursor_render
from ..colors import Color
from ..geometry import Point, Size
from .gadget import Cell, Gadget, PosHint, SizeHint


class Cursor(Gadget):
    """
    A gadget that replaces SGR parameters of cells beneath it.

    Cursor over sixel cells will do nothing.
    """

    def __init__(
        self,
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        strikethrough: bool | None = None,
        overline: bool | None = None,
        reverse: bool | None = None,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
        size: Size = Size(1, 1),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.bold: bold | None = bold
        "Whether cursor is bold."
        self.italic: bold | None = italic
        "Whether cursor is italic."
        self.underline: bold | None = underline
        "Whether cursor is underlined."
        self.strikethrough: bold | None = strikethrough
        "Whether cursor is strikethrough."
        self.overline: bold | None = overline
        "Whether cursor is overlined."
        self.reverse: bold | None = reverse
        "Whether cursor is reversed."
        self.fg_color: Color | None = fg_color
        """Foreground color of gadget."""
        self.bg_color: Color | None = bg_color
        """Background color of gadget."""
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    def _render(
        self, cells: NDArray[Cell], graphics: NDArray[np.uint8], kind: NDArray[np.uint8]
    ) -> None:
        """Render visible region of gadget."""
        cursor_render(
            cells,
            kind,
            self.bold,
            self.italic,
            self.underline,
            self.strikethrough,
            self.overline,
            self.reverse,
            self.fg_color,
            self.bg_color,
            self._is_transparent,
            self._region,
        )

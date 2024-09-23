"""Root gadget."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Literal, Self

import numpy as np

if TYPE_CHECKING:
    from ..app import App

from ..colors import Color
from ..text_tools import new_cell
from .gadget import Gadget, Point, Region, Size, _GadgetList


class _Root(Gadget):
    """
    Root gadget of the gadget tree.

    Instantiated only by :class:`batgrl.app.App`.
    """

    def __init__(
        self,
        app: App,
        render_mode: Literal["regions", "painter"],
        bg_color: Color,
        size: Size,
    ):
        self._render_lock = RLock()
        self._size = -1, -1
        self._region_valid = False
        self.children = _GadgetList()

        self._app = app
        self.render_mode = render_mode
        self._cell = new_cell(bg_color=bg_color)
        self.size = size

    def on_size(self):
        """Remake buffers and set ``_resized`` flag on resize."""
        self._resized = True
        self._last_canvas = np.full(self._size, self._cell)
        self.canvas = self._last_canvas.copy()

    @property
    def _pos(self) -> Point:
        return Point(0, 0)

    @property
    def absolute_pos(self) -> Point:
        return Point(0, 0)

    @property
    def is_transparent(self) -> Literal[False]:
        return False

    @property
    def is_visible(self) -> Literal[True]:
        return True

    @property
    def is_enabled(self) -> Literal[True]:
        return True

    @property
    def parent(self) -> Literal[None]:
        return None

    @property
    def root(self) -> Self:
        return self

    @property
    def app(self) -> App:
        """The running app."""
        return self._app

    @property
    def bg_color(self) -> Color:
        return Color(*self._cell["bg_color"].item())

    @bg_color.setter
    def bg_color(self, color: Color):
        self._cell["bg_color"] = color

    def to_local(self, point: Point) -> Point:
        return point

    def collides_point(self, point: Point) -> bool:
        return point in self.size

    def _render(self):
        """Render gadget tree into `canvas`."""
        with self._render_lock:
            if not self._region_valid:
                self._clipping_region = Region.from_rect(self.pos, self.size)
                self._region = self._clipping_region

            for child in self.walk():
                if not child._region_valid:
                    child._clipping_region = (
                        child.parent._clipping_region
                        & Region.from_rect(child.absolute_pos, child.size)
                        if child.is_enabled and child.is_visible
                        else Region()
                    )

            skip_valid_regions = True
            for child in self.walk_reverse():
                if skip_valid_regions and child._region_valid:
                    continue

                if child._region_valid and child._root_region_before == self._region:
                    skip_valid_regions = True
                    continue

                child._root_region_before = self._region
                child._region = self._region & child._clipping_region
                if not child.is_transparent:
                    self._region -= child._region

                child._region_valid = True
                skip_valid_regions = False

            self.canvas, self._last_canvas = self._last_canvas, self.canvas
            self.canvas[:] = self._cell

            for child in self.walk():
                if child.is_enabled and child.is_visible:
                    child._render(self.canvas)

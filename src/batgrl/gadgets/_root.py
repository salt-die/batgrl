"""Root gadget."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Literal, Self

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ..app import App

from ..colors import BLACK, Color
from ..text_tools import Cell, new_cell
from .gadget import Gadget, Point, Region, Size, _GadgetList
from .graphics import Graphics, _scale_geometry


class _Root(Gadget):
    """
    Root gadget of the gadget tree.

    Instantiated only by :class:`batgrl.app.App`.
    """

    def __init__(self, app: App, size: Size):
        self.children = _GadgetList()

        self._render_lock = RLock()
        """Lock held during rendering to prevent errors related to invalid geometry."""
        self._app = app
        """The running app."""
        self._cell = new_cell()
        """Default cell of root canvas."""
        self._bg_color = BLACK
        """Background color of the app."""
        self._all_regions_valid = False
        """Whether all regions in gadget tree are valid."""
        self._region_valid = False

        self._resized: bool
        """Whether terminal has resized since last render."""
        self._last_sixel: NDArray[np.uint8]
        """Previous sixel rendering."""
        self._last_canvas: NDArray[Cell]
        """Previous rendering of gadget tree."""
        self.sixel_canvas: NDArray[np.uint8]
        """Current sixel rendering."""
        self.canvas: NDArray[Cell]
        """Current rendering of gadget tree."""

        self._pos = Point(0, 0)
        self._size = size
        """Size of root gadget."""
        self.on_size()

    def __repr__(self):
        return f"_Root(size={self._size}, pos={self._pos})"

    def on_size(self):
        """Remake buffers and set ``_resized`` flag on resize."""
        self._resized = True
        self._last_canvas = np.full(self._size, self._cell)
        self.canvas = self._last_canvas.copy()

        if Graphics._sixel_support:
            h, w = _scale_geometry("sixel", self._size)
            self._last_sixel = np.full((h, w, 3), self._bg_color)
            self.sixel_canvas = self._last_sixel.copy()

    @property
    def bg_color(self) -> Color:
        """Background color of the app."""
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._bg_color = self._cell["bg_color"] = bg_color

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

    def _set_regions(self) -> None:
        """Recompute valid regions for all gadgets with invalid regions."""
        if not self._region_valid:
            self._clipping_region = Region.from_rect(self.absolute_pos, self.size)
            self._region = self._clipping_region

        for child in self.walk():
            if not child._region_valid:
                child._clipping_region = (
                    child.parent._clipping_region
                    & Region.from_rect(child.absolute_pos, child.size)
                    if child._is_enabled and child._is_visible
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
            if not child._is_transparent:
                self._region -= child._region

            child._region_valid = True
            skip_valid_regions = False

        self._all_regions_valid = True
        self._resized = False

    def _render(self):
        """Render gadget tree into :attr:``canvas``."""
        with self._render_lock:
            if not self._all_regions_valid:
                self._set_regions()

            self.canvas, self._last_canvas = self._last_canvas, self.canvas
            canvas = self.canvas
            canvas[:] = self._cell
            # self.sixel_canvas, self._last_sixel = self._last_sixel, self.sixel_canvas
            # sixel_canvas = self.sixel_canvas
            # sixel_canvas[:] = self.bg_color

            for child in self.walk():
                if not child._is_enabled or not child._is_visible:
                    continue

                child._render(canvas)

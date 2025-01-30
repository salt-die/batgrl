"""Root gadget."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Literal, Self

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ..app import App

from typing import Final

from ..colors import BLACK, Color
from ..text_tools import Cell, _Cell, new_cell
from .gadget import Gadget, Point, Region, Size, _GadgetList
from .graphics import Graphics, scale_geometry


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
        self._cell: Cell = new_cell()
        """Default cell of root canvas."""
        self._bg_color = BLACK
        """Background color of the app."""
        self._all_regions_valid = False
        """Whether all regions in gadget tree are valid."""
        self._region_valid = False
        """Whether current region is valid."""
        self._pos: Final = Point(0, 0)
        """Position of root gadget."""
        self._size = size
        """Size of root gadget."""

        # Following attributes set in `on_size()`:
        self._resized: bool
        """Whether terminal has resized since last render."""
        self.cells: NDArray[_Cell]
        """Current rendering of gadget tree."""
        self.graphics: NDArray[np.uint8] = np.empty((0, 0, 4), np.uint8)
        """Current graphics rendering."""
        self.kind: NDArray[np.uint8]
        """Whether a cell should use canvas, graphics or both."""
        self._widths: NDArray[np.int32]
        """Column widths of characters in canvas."""
        self._last_cells: NDArray[_Cell]
        """Previous rendering of gadget tree."""
        self._last_graphics: NDArray[np.uint8] = self.graphics.copy()
        """Previous graphics rendering."""
        self._last_kind: NDArray[np.uint8]
        """Previous kind."""
        self._palette: NDArray[np.uint8] = np.empty((256, 3), np.uint8)
        """Stores quantized colors when generating sixel."""
        self._indices: NDArray[np.uint8] = np.empty((0, 0), np.uint8)
        """Indices into palette for quantized graphics."""

    def on_size(self):
        """Remake buffers and set ``_resized`` flag on resize."""
        self._resized = True
        self.cells = np.full(self._size, self._cell.view(_Cell))
        self._last_cells = self.cells.copy()
        self._widths = np.zeros(self._size, dtype=np.int32)
        self.kind = np.zeros(self._size, np.uint8)
        self._last_kind = self.kind.copy()

        if Graphics._sixel_support:
            h, w = scale_geometry("sixel", self.size)
            self.graphics = np.full((h, w, 4), (*self._bg_color, 0), np.uint8)
            self._last_graphics = self.graphics.copy()
            self._indices = np.empty((h, w), np.uint8)

    @property
    def bg_color(self) -> Color:
        """Background color of the app."""
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._bg_color = self._cell["bg_color"] = bg_color

    @property
    def pos(self) -> Point:
        return self._pos

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
            self._clipping_region = Region.from_rect(self._pos, self.size)
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

            self.cells, self._last_cells = self._last_cells, self.cells
            self.graphics, self._last_graphics = self._last_graphics, self.graphics
            self.kind, self._last_kind = self._last_kind, self.kind

            self.cells[:] = self._cell.view(_Cell)
            self.graphics[:] = (*self.bg_color, 0)
            self.kind[:] = 0

            for child in self.walk():
                if not child._is_enabled or not child._is_visible:
                    continue

                child._render(self.cells, self.graphics, self.kind)

"""Root gadget."""
from threading import RLock
from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from ..app import App

from ..colors import Color
from .gadget import Gadget, Point, Region, Size
from .text_tools import style_char


class _Root(Gadget):
    """
    Root gadget of the gadget tree.

    Instantiated only by :class:`batgrl.app.App`.
    """

    def __init__(
        self,
        bg_color: Color,
        render_mode: Literal["regions", "painter"],
        size: Size,
    ):
        self._cell = style_char(" ", bg_color=bg_color)
        self._render_lock = RLock()
        self._size = -1, -1  # Forces `on_size()` when size is set.
        self.children = []
        self.render_mode = render_mode
        self.size = size

    def on_size(self):
        """Erase last render and re-make buffers."""
        h, w = self._size
        self.canvas = np.full((h, w), self._cell)
        self._last_canvas = self.canvas.copy()
        self._resized = True

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
    def root(self) -> "_Root":
        return self

    @property
    def app(self) -> "App":
        return self._app

    def to_local(self, point: Point) -> Point:
        return point

    def collides_point(self, point: Point) -> bool:
        y, x = point
        return 0 <= y < self.height and 0 <= x < self.width

    def _render(self):
        """Render gadget tree into `canvas`."""
        # TODO: Optimize...
        # - Recalculating all regions every frame isn't necessary if gadget geometry
        #   hasn't changed.
        # - If there *is* a change to geometry, regions that are later in z-order can be
        #   reused.
        # - Checking for changes in geometry can be done once every few frames if
        #   geometry has been static for some time.

        with self._render_lock:
            self.region = Region.from_rect(self.pos, self.size)

            for child in self.walk():
                child.region = (
                    child.parent.region
                    & Region.from_rect(child.absolute_pos, child.size)
                    if child.is_enabled and child.is_visible
                    else Region()
                )

            if self.render_mode == "regions":
                for child in self.walk_reverse():
                    if child.is_enabled:
                        child.region &= self.region
                        if child.is_visible and not child.is_transparent:
                            self.region -= child.region

            self.canvas, self._last_canvas = self._last_canvas, self.canvas

            self.canvas[:] = self._cell

            for child in self.walk():
                if child.is_enabled and child.is_visible:
                    child._render(self.canvas)

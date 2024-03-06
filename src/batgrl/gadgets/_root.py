"""Root gadget."""
from threading import RLock
from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from ..app import App

from ..colors import Color
from .gadget import Gadget, Point, Region, Size
from .text_tools import cell


class _Root(Gadget):
    """
    Root gadget of the gadget tree.

    Instantiated only by :class:`batgrl.app.App`.
    """

    def __init__(
        self,
        app: "App",
        render_mode: Literal["regions", "painter"],
        bg_color: Color,
        size: Size,
    ):
        self._render_lock = RLock()
        self._size = -1, -1
        self.children = []

        self._app = app
        self.render_mode = render_mode
        self._cell = cell(bg_color=bg_color)
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
            self._region = Region.from_rect(self.pos, self.size)

            for child in self.walk():
                child._region = (
                    child.parent._region
                    & Region.from_rect(child.absolute_pos, child.size)
                    if child.is_enabled and child.is_visible
                    else Region()
                )

            if self.render_mode == "regions":
                for child in self.walk_reverse():
                    if child.is_enabled:
                        child._region &= self._region
                        if child.is_visible and not child.is_transparent:
                            self._region -= child._region

            self.canvas, self._last_canvas = self._last_canvas, self.canvas

            self.canvas[:] = self._cell

            for child in self.walk():
                if child.is_enabled and child.is_visible:
                    child._render(self.canvas)

"""Root gadget."""
from threading import RLock
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ..app import App

from .gadget import Char, ColorPair, Gadget, Point, Region, Size


class _Root(Gadget):
    """
    Root gadget of the gadget tree.

    Instantiated only by :class:`batgrl.app.App`.
    """

    def __init__(
        self,
        background_char: NDArray[Char] | str,
        background_color_pair: ColorPair,
        render_mode: Literal["regions", "painter"],
        size: Size,
    ):
        self._render_lock = RLock()
        self.children = []
        self.background_char = background_char
        self.background_color_pair = background_color_pair
        self.render_mode = render_mode
        self._size = -1, -1
        self.size = size

    def on_size(self):
        """Erase last render and re-make buffers."""
        h, w = self._size

        self.canvas = np.full((h, w), self.background_char)
        self.colors = np.full((h, w, 6), self.background_color_pair, dtype=np.uint8)

        self._last_canvas = self.canvas.copy()
        self._last_colors = self.colors.copy()

        self._resized = True

    @property
    def pos(self) -> Point:
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

    def render(self):
        """Render gadget tree into `canvas` and `colors`."""
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
            self.colors, self._last_colors = self._last_colors, self.colors

            self.canvas[:] = self.background_char
            self.colors[:] = self.background_color_pair

            for child in self.walk():
                if child.is_enabled and child.is_visible:
                    child.render(self.canvas, self.colors)

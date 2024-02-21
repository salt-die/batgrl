"""A gadget that re-colors cells beneath it."""
from numpy.typing import NDArray

from ..colors import BLACK, WHITE, Color
from .gadget import Cell, Gadget


class Cursor(Gadget):
    """A gadget that re-colors cells beneath it."""

    def __init__(self, fg_color: Color = WHITE, bg_color: Color = BLACK, **kwargs):
        super().__init__(size=(1, 1), is_transparent=True, is_enabled=False, **kwargs)
        self.fg_color: Color = fg_color
        """Foreground color of gadget."""
        self.bg_color: Color = bg_color
        """Background color of gadget."""

    def _render(self, canvas: NDArray[Cell]):
        """Render visible region of gadget."""
        for rect in self._region.rects():
            dst = rect.to_slices()
            canvas[dst]["fg_color"] = self.fg_color
            canvas[dst]["bg_color"] = self.bg_color

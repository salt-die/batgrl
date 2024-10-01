"""A sixel graphics gadget."""

from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from ..geometry import rect_slice
from ..texture_tools import Interpolation, _composite, resize_texture
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .graphics import Graphics

__all__ = ["SixelGraphics", "Interpolation", "Point", "Size"]


class SixelGraphics(Gadget):
    """
    A sixel graphics gadget.

    If sixel is not supported, :class:``SixelGraphics`` will fallback to rendering with
    upper half block characters.
    """

    _sixel_supported: bool = False
    """Whether sixel is supported."""
    _pixel_geometry: Size = Size(20, 10)
    """Pixel geometry as reported by terminal. (Default: Size(20, 10))"""

    def __init__(
        self,
        *,
        texture: NDArray[np.uint8],
        interpolation: Interpolation = "linear",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.texture = texture
        self._graphics: Graphics | None = None
        """Fallback graphics if sixel isn't supported."""
        self._bitmap: NDArray[np.uint8] | None = None
        """Sixel bitmap."""
        self.interpolation = interpolation
        self._rebuild_bitmap()

    @classmethod
    def _scale_by_pixel_geometry[T: (Point, Size)](cls, point_or_size: T) -> T:
        """Scale a point or size by current pixel geometry."""
        ph, pw = cls._pixel_geometry
        a, b = point_or_size
        return type(point_or_size)(a * ph, b * pw)

    def _rebuild_bitmap(self):
        if self._sixel_supported:
            if self._graphics is not None:
                self._graphics.destroy()
                self._graphics = None
            scaled_size = self._scale_by_pixel_geometry(self._size)
            self._bitmap = resize_texture(self.texture, scaled_size, self.interpolation)
        else:
            if self._graphics is None:
                self._graphics = Graphics(
                    size=self.size, is_transparent=self.is_transparent
                )
                self.add_gadget(self._graphics)
                self.children.insert(self.children.pop(0))
            else:
                self._graphics.size = self.size
            self._bitmap = None
            self._graphics.texture = resize_texture(
                self.texture, self.size, self.interpolation
            )

    def on_transparency(self) -> None:
        """Update fallback graphics transparency on transparency."""
        if self._graphics is not None:
            self._graphics.is_transparent = self.is_transparent

    @property
    def interpolation(self) -> Interpolation:
        """Interpolation used when gadget is resized."""
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        if interpolation not in Interpolation.__args__:
            raise TypeError(f"{interpolation} is not a valid interpolation type.")
        self._interpolation = interpolation

    def on_size(self):
        """Remake bitmap."""
        self._rebuild_bitmap()

    def _render(self, canvas: NDArray[np.uint8]):
        """Render visible region of gadget."""
        root_pos = self._scale_by_pixel_geometry(self.root._pos)
        abs_pos = self._scale_by_pixel_geometry(self.absolute_pos)
        alpha = self.alpha
        for pos, size in self._region.rects():
            scaled_pos = self._scale_by_pixel_geometry(pos)
            scaled_size = self._scale_by_pixel_geometry(size)
            dst = rect_slice(scaled_pos - root_pos, scaled_size)
            src = rect_slice(scaled_pos - abs_pos, scaled_size)
            if self.is_transparent:
                _composite(
                    canvas[dst],
                    self._bitmap[src, :3],
                    self._bitmap[src, 3, None],
                    alpha,
                )
            else:
                canvas[dst] = self._bitmap[src]

    def to_png(self, path: Path):
        """Write :attr:`texture` to provided path as a `png` image."""
        BGRA = cv2.cvtColor(self.texture, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path.absolute()), BGRA)

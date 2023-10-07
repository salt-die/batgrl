"""
A text particle field.

A particle field specializes in handling many single "pixel" children.
"""
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ..colors import ColorPair
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    style_char,
)

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "TextParticleField",
]

NDArray[np.float64]
dict[str, NDArray[Any]]


class TextParticleField(Gadget):
    """
    A text particle field.

    A particle field specializes in rendering many single "pixel" children by
    setting particle positions, chars, and color pairs. This is more efficient than
    rendering many 1x1 gadgets.

    Parameters
    ----------
    particle_positions : NDArray[np.int32] | None, default: None
        Positions of particles. Expect int array with shape `N, 2`.
    particle_chars : NDArray[Char] | None, default: None
        An array of characters. Expect a `Char` array with shape `N,`.
    particle_color_pairs : NDArray[np.uint8] | None, default: None
        Color pairs of particles. Expect uint8 array with shape `N, 6`.
    particle_properties : dict[str, NDArray[Any]] | None, default: None
        Additional particle properties.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    nparticles : int
        Number of particles in particle field.
    particle_positions : NDArray[np.int32]
        Positions of particles.
    particle_chars : NDArray[Char]
        Characters of alphas.
    particle_color_pairs : NDArray[np.uint8]
        Color pairs of particles.
    particle_properties : dict[str, NDArray[Any]]
        Additional particle properties.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        particle_positions: NDArray[np.int32] | None = None,
        particle_chars: NDArray[Char] | None = None,
        particle_color_pairs: NDArray[np.uint8] | None = None,
        particle_properties: dict[str, NDArray[Any]] = None,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        if particle_positions is None:
            self.particle_positions = np.zeros((0, 2), dtype=int)
        else:
            self.particle_positions = particle_positions

        if particle_chars is None:
            self.particle_chars = np.full(len(self.particle_positions), style_char(" "))
        else:
            self.particle_chars = particle_chars

        if particle_color_pairs is None:
            self.particle_color_pairs = np.zeros(
                (len(self.particle_positions), 6), dtype=np.uint8
            )
        else:
            self.particle_color_pairs = particle_color_pairs

        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

    @property
    def nparticles(self) -> int:
        """
        Number of particles in particle field.
        """
        return len(self.particle_positions)

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        if self.background_char is not None:
            for rect in self.region.rects():
                canvas[rect.to_slices()] = style_char(self.background_char)

        if self.background_color_pair is not None:
            for rect in self.region.rects():
                colors[rect.to_slices()] = self.background_color_pair

        offy, offx = self.absolute_pos
        pchars = self.particle_chars
        pcolors = self.particle_color_pairs
        ppos = self.particle_positions
        if self.is_transparent:
            not_whitespace = np.isin(pchars["char"], (" ", "⠀"), invert=True)
            for rect in self.region.rects():
                height = rect.bottom - rect.top
                width = rect.right - rect.left
                pos = ppos - (rect.top - offy, rect.left - offx)
                inbounds = (((0, 0) <= pos) & (pos < (height, width))).all(axis=1)
                where_inbounds = np.nonzero(inbounds & not_whitespace)
                ys, xs = pos[where_inbounds].T
                dst = rect.to_slices()
                colors[dst][..., :3][ys, xs] = pcolors[where_inbounds][..., :3]
                canvas[dst][ys, xs] = pchars[where_inbounds]
        else:
            for rect in self.region.rects():
                height = rect.bottom - rect.top
                width = rect.right - rect.left
                pos = ppos - (rect.top - offy, rect.left - offx)
                inbounds = (((0, 0) <= pos) & (pos < (height, width))).all(axis=1)
                where_inbounds = np.nonzero(inbounds)
                ys, xs = pos[where_inbounds].T
                dst = rect.to_slices()
                colors[dst][ys, xs] = pcolors[where_inbounds]
                canvas[dst][ys, xs] = pchars[where_inbounds]

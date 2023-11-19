"""
A graphic particle field.

A particle field specializes in handling many single "pixel" children.
"""
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .gadget_base import (
    Char,
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    style_char,
)

__all__ = [
    "GraphicParticleField",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class GraphicParticleField(GadgetBase):
    r"""
    A graphic particle field.

    A particle field specializes in rendering many single "pixel" children by
    setting particle positions, colors, and alphas. (Note that alpha channel
    of particle colors and particle alphas are independent and both control
    particle transparency.) This is more efficient than rendering many 1x1 gadgets.

    Parameters
    ----------
    particle_positions : NDArray[np.int32] | None, default: None
        Positions of particles. Expect int array with shape `N, 2`.
    particle_colors : NDArray[np.uint8] | None, default: None
        Colors of particles. Expect uint8 array with shape `N, 4`.
    particle_alphas : NDArray[np.float64] | None, default: None
        Alphas of particles. Expect float array of values between
        0 and 1 with shape `N,`.
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
    is_transparent : bool, default: True
        A transparent gadget allows regions beneath it to be painted. Additionally,
        non-transparent graphic gadgets are not alpha composited.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    nparticles : int
        Number of particles in particle field.
    particle_positions : NDArray[np.int32]
        Positions of particles.
    particle_colors : NDArray[np.uint8]
        Colors of particles.
    particle_alphas : NDArray[np.float64]
        Alphas of particles.
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
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
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
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        particle_positions: NDArray[np.int32] | None = None,
        particle_colors: NDArray[np.uint8] | None = None,
        particle_alphas: NDArray[np.float64] | None = None,
        particle_properties: dict[str, NDArray[Any]] = None,
        is_transparent: bool = True,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        if particle_positions is None:
            self.particle_positions = np.zeros((0, 2), dtype=int)
        else:
            self.particle_positions = particle_positions

        if particle_colors is None:
            self.particle_colors = np.zeros(
                (len(self.particle_positions), 4), dtype=np.uint8
            )
        else:
            self.particle_colors = particle_colors

        if particle_alphas is None:
            self.particle_alphas = np.ones(len(self.particle_positions), dtype=np.float)
        else:
            self.particle_alphas = particle_alphas

        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

    @property
    def nparticles(self) -> int:
        """Number of particles in particle field."""
        return len(self.particle_positions)

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """Render visible region of gadget into root's `canvas` and `colors` arrays."""
        offy, offx = self.absolute_pos
        palphas = self.particle_alphas
        pcolors = self.particle_colors
        ppos = self.particle_positions
        for rect in self.region.rects():
            height = rect.bottom - rect.top
            width = rect.right - rect.left
            pos = ppos - (rect.top - offy, rect.left - offx)
            where_inbounds = np.nonzero(
                (((0, 0) <= pos) & (pos < (2 * height, width))).all(axis=1)
            )
            ys, xs = pos[where_inbounds].T

            dst = rect.to_slices()
            texture = (
                colors[dst]
                .reshape(height, width, 2, 3)
                .swapaxes(1, 2)
                .reshape(2 * height, width, 3)
            )
            painted = pcolors[where_inbounds]

            if not self.is_transparent:
                texture[ys, xs] = painted[..., :3]
            else:
                mask = canvas["char"][dst] != "▀"
                colors[dst][..., :3][mask] = colors[dst][..., 3:][mask]

                buffer = np.subtract(painted[:, :3], texture[ys, xs], dtype=float)
                buffer *= painted[:, 3, None]
                buffer *= palphas[where_inbounds][:, None]
                buffer /= 255
                texture[ys, xs] = (buffer + texture[ys, xs]).astype(np.uint8)

            colors[dst] = (
                texture.reshape(height, 2, width, 3)
                .swapaxes(1, 2)
                .reshape(height, width, 6)
            )
            canvas[dst] = style_char("▀")

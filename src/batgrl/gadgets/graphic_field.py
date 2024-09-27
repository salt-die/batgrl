"""
A graphic particle field.

A particle field specializes in handling many single "pixel" children.
"""

from typing import Any

import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured
from numpy.typing import NDArray

from ..geometry import rect_slice
from ..text_tools import cell_sans
from ..texture_tools import _composite
from .gadget import Cell, Gadget, Point, PosHint, Size, SizeHint, bindable, clamp

__all__ = ["GraphicParticleField", "particle_data_from_texture", "Point", "Size"]


class GraphicParticleField(Gadget):
    r"""
    A graphic particle field.

    A particle field specializes in rendering many single "pixel" children with just
    particle positions and  colors. This is more efficient than rendering many 1x1
    gadgets.

    Parameters
    ----------
    particle_positions : NDArray[np.int32] | None, default: None
        An array of particle positions with shape `(N, 2)`.
    particle_colors : NDArray[np.uint8] | None, default: None
        An array of particle colors with shape `(N, 4)`.
    particle_properties : dict[str, NDArray[Any]] | None, default: None
        Additional particle properties.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        Whether gadget is transparent.
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
        An array of particle positions with shape `(N, 2)`.
    particle_colors : NDArray[np.uint8]
        An array of particle colors with shape `(N, 4)`.
    particle_properties : dict[str, NDArray[Any]]
        Additional particle properties.
    alpha : float
        Transparency of gadget.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    particles_from_texture(texture)
        Return positions and colors of visible pixels of an RGBA texture.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        particle_positions: NDArray[np.int32] | None = None,
        particle_colors: NDArray[np.uint8] | None = None,
        particle_properties: dict[str, NDArray[Any]] = None,
        alpha: float = 1.0,
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

        if particle_positions is None:
            self.particle_positions = np.zeros((0, 2), dtype=int)
        else:
            self.particle_positions = np.asarray(particle_positions, dtype=int)

        if particle_colors is None:
            self.particle_colors = np.zeros(
                (len(self.particle_positions), 4), dtype=np.uint8
            )
        else:
            self.particle_colors = np.asarray(particle_colors, dtype=np.uint8)

        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

        self.alpha = alpha

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    @bindable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    @property
    def nparticles(self) -> int:
        """Number of particles in particle field."""
        return len(self.particle_positions)

    def _render(self, canvas: NDArray[Cell]):
        """Render visible region of gadget."""
        chars = canvas["char"]
        styles = canvas[cell_sans("char", "fg_color", "bg_color")]
        colors = structured_to_unstructured(canvas[["fg_color", "bg_color"]], np.uint8)
        root_pos = self.root._pos
        abs_pos = self.absolute_pos
        ppos = self.particle_positions
        pcolors = self.particle_colors
        for pos, (h, w) in self._region.rects():
            abs_ppos = ppos - (pos - abs_pos)
            where_inbounds = np.nonzero(
                (((0, 0) <= abs_ppos) & (abs_ppos < (2 * h, w))).all(axis=1)
            )
            ys, xs = abs_ppos[where_inbounds].T

            dst = rect_slice(pos - root_pos, (h, w))
            color_rect = colors[dst]

            if self.is_transparent:
                mask = chars[dst] != "▀"
                color_rect[..., :3][mask] = color_rect[..., 3:][mask]

            texture = (
                color_rect.reshape(h, w, 2, 3).swapaxes(1, 2).reshape(2 * h, w, 3)
            )  # Not a view.
            painted = pcolors[where_inbounds]

            if self.is_transparent:
                background = texture[ys, xs]
                _composite(background, painted[:, :3], painted[:, 3, None], self.alpha)
                texture[ys, xs] = background
            else:
                texture[ys, xs] = painted[..., :3]

            color_rect[:] = texture.reshape(h, 2, w, 3).swapaxes(1, 2).reshape(h, w, 6)
            chars[dst] = "▀"
            styles[dst] = False


def particle_data_from_texture(
    texture: NDArray[np.uint8],
) -> tuple[NDArray[np.int32], NDArray[np.uint8]]:
    """
    Return positions and colors of visible pixels of an RGBA texture.

    Parameters
    ----------
    texture : NDArray[np.uint8]
        A uint8 RGBA numpy array.

    Returns
    -------
    tuple[NDArray[np.int32], NDArray[np.uint8]]
        Position and colors of visible pixels of the texture.
    """
    positions = np.argwhere(texture[..., 3])
    pys, pxs = positions.T
    return positions, texture[pys, pxs]

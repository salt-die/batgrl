"""A gadget that replaces SGR parameters of cells beneath it."""

import numpy as np
from numpy.typing import NDArray

from .._rendering import cursor_render
from ..colors import Color
from ..geometry import Point, Size
from .gadget import Cell, Gadget, PosHint, SizeHint


class Cursor(Gadget):
    r"""
    A gadget that replaces SGR parameters of cells beneath it.

    Parameters
    ----------
    bold : bool | None, default: None
        Whether cursor is bold.
    italic : bool | None, default: None
        Whether cursor is italic.
    underline : bool | None, default: None
        Whether cursor is underlined.
    strikethrough : bool | None, default: None
        Whether cursor is strikethrough.
    overline : bool | None, default: None
        Whether cursor is overlined.
    reverse : bool | None, default: True
        Whether cursor is reversed.
    fg_color : Color | None, default: None
        Foreground color of cursor.
    bg_color : Color | None, default: None
        Background color of cursor.
    size : Size, default: Size(1, 1)
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
    parent : Gadget | None
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
        Update gadget after transparency enabled/disabled.
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
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        strikethrough: bool | None = None,
        overline: bool | None = None,
        reverse: bool | None = True,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
        size: Size = Size(1, 1),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.bold: bool | None = bold
        "Whether cursor is bold."
        self.italic: bool | None = italic
        "Whether cursor is italic."
        self.underline: bool | None = underline
        "Whether cursor is underlined."
        self.strikethrough: bool | None = strikethrough
        "Whether cursor is strikethrough."
        self.overline: bool | None = overline
        "Whether cursor is overlined."
        self.reverse: bool | None = reverse
        "Whether cursor is reversed."
        self.fg_color: Color | None = fg_color
        """Foreground color of cursor."""
        self.bg_color: Color | None = bg_color
        """Background color of cursor."""
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    def _render(
        self, cells: NDArray[Cell], graphics: NDArray[np.uint8], kind: NDArray[np.uint8]
    ) -> None:
        """Render visible region of gadget."""
        cursor_render(
            cells,
            self.bold,
            self.italic,
            self.underline,
            self.strikethrough,
            self.overline,
            self.reverse,
            self.fg_color,
            self.bg_color,
            self._region,
        )

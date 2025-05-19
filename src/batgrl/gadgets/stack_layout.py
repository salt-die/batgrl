"""Horizontal and vertical stack layout gadgets."""

import math

from ..geometry import Point, Size
from .gadget import Gadget, Pointlike, PosHint, SizeHint, Sizelike

__all__ = ["HStackLayout", "Point", "Size", "VStackLayout"]


class _StackLayoutBase(Gadget):
    def __init__(
        self,
        *,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
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
        self._proportions = ()

    @property
    def proportions(self) -> tuple[float, ...]:
        """Size of children as proportions of the stack layout size."""
        return self._proportions

    @proportions.setter
    def proportions(self, proportions: tuple[float, ...]):
        if not self.children:
            self._proportions = ()
            return

        total_proportion = sum(proportions)
        if len(proportions) != len(self.children) or total_proportion == 0:
            self._proportions = (1 / len(self.children),) * len(self.children)
        elif not math.isclose(total_proportion, 1):
            if total_proportion == 0:
                self._proportions = (1 / len(self.children),) * len(self.children)
            else:
                factor = 1 / total_proportion
                self._proportions = tuple(
                    proportion * factor for proportion in proportions
                )
        self._reposition_children()

    def _reposition_children(self) -> None:
        pass

    def on_size(self):
        """Resize children on resize."""
        self.proportions = self.proportions

    def add_gadget(self, gadget: Gadget):
        """Remove hints from gadget and resize children when child is added."""
        gadget.size_hint = {}
        gadget.pos_hint = {}
        super().add_gadget(gadget)
        self.proportions = self.proportions

    def remove_gadget(self, gadget: Gadget):
        """Resize children when child is removed."""
        super().remove_gadget(gadget)
        self.proportions = self.proportions


class VStackLayout(_StackLayoutBase):
    r"""
    A vertical stack layout gadget.

    A vertical stack layout positions its children vertically and resizes them
    to use all of its available space. By default, each child will take an
    (almost) equal amount of space, but this can be adjusted by setting
    :attr:`proportions`. The nth proportion adjusts the height of the nth child
    gadget. Extra unfilled rows or columns are divided among the children.

    Parameters
    ----------
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    proportions : tuple[float, ...]
        Height of children as proportions of stack layout height.
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
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
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
    app : App | None
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
    add_gadgets(gadget_it, \*gadgets)
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

    Notes
    -----
    Stack layouts remove size and pos hints from their children.
    """

    def _reposition_children(self) -> None:
        for proportion, child in zip(self._proportions, self.children):
            child.size = int(proportion * self.height), self.width

        total_height = sum(child.height for child in self.children)
        offset_all, offset_few = divmod(self.height - total_height, len(self.children))
        for i, child in enumerate(reversed(self.children)):
            child.height += offset_all + i < offset_few

        y = 0
        for child in self.children:
            child.pos = y, 0
            y += child.height


class HStackLayout(_StackLayoutBase):
    r"""
    A horizontal stack layout gadget.

    A horizontal stack layout positions its children horizontally and resizes
    them to use all of its available space. By default, each child will take an
    (almost) equal amount of space, but this can be adjusted by setting
    :attr:`proportions`. The nth proportion adjusts the width of the nth child
    gadget. Extra unfilled rows or columns are divided among the children.

    Parameters
    ----------
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    proportions : tuple[float, ...]
        Width of children as proportions of stack layout width.
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
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
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
    app : App | None
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
    add_gadgets(gadget_it, \*gadgets)
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

    Notes
    -----
    Stack layouts remove size and pos hints from their children.
    """

    def _reposition_children(self) -> None:
        for proportion, child in zip(self._proportions, self.children):
            child.size = self.height, int(proportion * self.width)

        total_width = sum(child.width for child in self.children)
        offset_all, offset_few = divmod(self.width - total_width, len(self.children))
        for i, child in enumerate(reversed(self.children)):
            child.width += offset_all + i < offset_few

        x = 0
        for child in self.children:
            child.pos = 0, x
            x += child.width

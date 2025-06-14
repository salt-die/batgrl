"""
A base for creating tree-like views. Tree views are composed of nodes that
can be selected and toggled open or closed.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Self, cast

from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
from .gadget import (
    Cell0D,
    Gadget,
    Point,
    Pointlike,
    PosHint,
    Size,
    SizeHint,
    Sizelike,
    _GadgetList,
)
from .text import Text

__all__ = ["ButtonState", "Point", "Size", "TreeView", "TreeViewNode"]


class TreeViewNode(Themable, ButtonBehavior, Text):
    r"""
    A node of a :class:`TreeView`.

    Parameters
    ----------
    is_leaf : bool, default: True
        Whether node is a leaf node.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    default_cell : Cell0D | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 0.0
        Transparency of gadget.
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
    root_node : TreeViewNode
        Root node of tree.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of `NORMAL`, `HOVER`, `DOWN`.
    canvas : Cell2D
        The array of characters for the gadget.
    chars : Unicode2D
        Return a view of the ords field of the canvas as 1-character unicode strings.
    default_cell : Cell0D
        Default cell of text canvas.
    default_fg_color : Color
        Foreground color of default cell.
    default_bg_color : Color
        Background color of default cell.
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
    iter_open_nodes()
        Yield all open descendent nodes.
    add_node(node: TreeViewNode)
        Add a child node.
    remove_node(node: TreeViewNode)
        Remove a child node.
    toggle()
        Toggle node open or closed.
    select()
        Select this node.
    unselect()
        Unselect this node.
    get_color(color_name)
        Get a color by name from the current color theme.
    update_theme()
        Paint the gadget with current theme.
    update_normal()
        Paint the normal state.
    update_hover()
        Paint the hover state.
    update_down()
        Paint the down state.
    on_release()
        Triggered when a button is released.
    add_border(style="light", ...)
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style)
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...)
        Add a single line of text to the canvas.
    set_text(text, ...)
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    clear()
        Fill canvas with default cell.
    shift(n=1)
        Shift content in canvas up (or down in case of negative `n`).
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
    """

    def __init__(
        self,
        is_leaf=True,
        always_release: bool = False,
        default_cell: Cell0D | str = " ",
        alpha: float = 0.0,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.is_leaf: bool = is_leaf
        self.is_open: bool = False
        self.is_selected: bool = False
        self.parent_node: Self | None = None
        self.child_nodes: list[Self] = []
        self.tree_view: TreeView | None = None
        self.level: int = -1
        super().__init__(
            always_release=always_release,
            default_cell=default_cell,
            alpha=alpha,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    def _repaint(self):
        if self.is_selected:
            fg = self.get_color("menu_item_selected_fg")
            bg = self.get_color("menu_item_selected_bg")
        elif self.button_state == "normal":
            fg = self.get_color("primary_fg")
            bg = self.get_color("primary_bg")
        else:
            fg = self.get_color("menu_item_hover_fg")
            bg = self.get_color("menu_item_hover_bg")
        self.canvas["fg_color"] = fg
        self.canvas["bg_color"] = bg

    def on_size(self):
        """Repaint tree on resize."""
        super().on_size()
        self._repaint()

    def update_theme(self):
        """Paint the gadget with current theme."""
        self._repaint()

    def update_normal(self):
        """Paint the normal state."""
        self._repaint()

    def update_hover(self):
        """Paint the hover state."""
        self._repaint()

    def update_down(self):
        """Paint the down state."""
        self._repaint()

    @property
    def root_node(self) -> Self:
        """Root node of tree."""
        if self.parent_node is None:
            return self
        return self.parent_node.root_node

    def iter_open_nodes(self) -> Iterator[Self]:
        """
        Yield all open descendent nodes.

        Yields
        ------
        TreeViewNode
            A descendent open node.
        """
        for child in self.child_nodes:
            yield child

            if child.is_open:
                yield from child.iter_open_nodes()

    def add_node(self, node: Self):
        """
        Add a child node.

        Parameters
        ----------
        node : TreeViewNode
            The node to add.
        """
        self.child_nodes.append(node)

        node.level = self.level + 1
        node.parent_node = self

    def remove_node(self, node: Self):
        """
        Remove a child node.

        Parameters
        ----------
        node : TreeViewNode
            The node to remove.
        """
        self.child_nodes.remove(node)

        node.level = -1
        node.parent_node = None

    def _toggle_update(self):
        """Update state after :meth:`toggle` is called."""

    def toggle(self):
        """Toggle node open or closed."""
        if not self.is_leaf:
            self.is_open = not self.is_open
            self._toggle_update()
            cast(TreeView, self.root_node.tree_view).update_tree_layout()

    def select(self):
        """Select node."""
        tree_view = cast(TreeView, self.root_node.tree_view)
        if tree_view.selected_node is not None:
            tree_view.selected_node.unselect()

        self.is_selected = True
        tree_view.selected_node = self
        self._repaint()

    def unselect(self):
        """Unselect node."""
        self.is_selected = False
        cast(TreeView, self.root_node.tree_view).selected_node = None
        self._repaint()

    def on_release(self):
        """Select and toggle node on release."""
        self.select()
        self.toggle()


class TreeView[T: TreeViewNode](Gadget):
    r"""
    Base for creating tree-like views.

    Parameters
    ----------
    root_node : TreeViewNode
        Root node of tree view.
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
    root_node : TreeViewNode
        Root node of tree view
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
    update_tree_layout()
        Update tree layout after a child node is toggled open or closed.
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
    """

    def __init__(
        self,
        root_node: T,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.selected_node: T | None = None
        self.children: _GadgetList[T]
        self.root_node = root_node
        root_node.tree_view = self

        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        root_node.toggle()

    def update_tree_layout(self) -> None:
        """Update tree layout after a child node is opened or closed."""

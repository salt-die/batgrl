"""
A base for creating tree-like views. Tree views are composed of nodes that
can be selected and toggled open or closed.
"""
from ..colors import WHITE_ON_BLACK, ColorPair
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
from .gadget import Gadget, Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict
from .text import Text

__all__ = [
    "ButtonState",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "TreeView",
    "TreeViewNode",
]


class TreeViewNode(Themable, ButtonBehavior, Text):
    """
    A node of a :class:`TreeView`.

    Parameters
    ----------
    is_leaf : bool, default: True
        True if node is a leaf node.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width
        grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of gadget.
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
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of `NORMAL`, `HOVER`, `DOWN`.
    canvas : NDArray[Char]
        The array of characters for the gadget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str
        Default background character.
    default_color_pair : ColorPair
        Default color pair of gadget.
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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
    iter_open_nodes:
        Yield all child nodes and recursively yield from:
        all open child nodes.
    add_node:
        Add a child node.
    remove_node:
        Remove a child node.
    toggle:
        Close node if node is open else open node.
    select:
        Select this node.
    unselect:
        Unselect this node.
    update_theme:
        Paint the gadget with current theme.
    update_normal:
        Paint the normal state.
    update_hover:
        Paint the hover state.
    update_down:
        Paint the down state.
    on_release:
        Triggered when a button is released.
    add_border:
        Add a border to the gadget.
    add_str:
        Add a single line of text to the canvas.
    set_text:
        Resize gadget to fit text, erase canvas, then fill canvas with text.
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
        is_leaf=True,
        always_release: bool = False,
        default_char: str = " ",
        default_color_pair: ColorPair = WHITE_ON_BLACK,
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
        self.is_leaf = is_leaf

        self.is_open = False
        self.is_selected = False

        self.parent_node = None
        self.child_nodes = []
        self.level = -1

        self.normal_color_pair = (0,) * 6  # Temporary assignment

        super().__init__(
            always_release=always_release,
            default_char=default_char,
            default_color_pair=default_color_pair,
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

    def _repaint(self):
        if self.is_selected:
            self.colors[:] = self.color_theme.menu_item_selected
        elif self.state is ButtonState.NORMAL:
            self.colors[:] = self.color_theme.primary
        elif self.state is ButtonState.HOVER:
            self.colors[:] = self.color_theme.menu_item_hover

    def on_size(self):
        super().on_size()
        self._repaint()

    def update_theme(self):
        self._repaint()

    def update_normal(self):
        self._repaint()

    def update_hover(self):
        self._repaint()

    def update_down(self):
        self._repaint()

    @property
    def root_node(self):
        if self.parent_node is None:
            return self

        return self.parent_node.root_node

    def iter_open_nodes(self):
        """
        Yield all child nodes and recursively yield from
        all open child nodes.
        """
        for child in self.child_nodes:
            yield child

            if child.is_open:
                yield from child.iter_open_nodes()

    def add_node(self, node):
        """
        Add a child node.
        """
        self.child_nodes.append(node)

        node.level = self.level + 1
        node.parent_node = self

    def remove_node(self, node):
        """
        Remove a child node.
        """
        self.child_nodes.remove(node)

        node.level = -1
        node.parent_node = None

    def _toggle_update(self):
        """
        Update state after :meth:`toggle` is called.
        """

    def toggle(self):
        """
        Toggle node open or closed.
        """
        if not self.is_leaf:
            self.is_open = not self.is_open
            self._toggle_update()
            self.root_node.tree_view.update_tree_layout()

    def unselect(self):
        """
        Unselect node.
        """
        self.is_selected = False
        self.root_node.tree_view.selected_node = None
        self._repaint()

    def select(self):
        """
        Select node.
        """
        if self.root_node.tree_view.selected_node is not None:
            self.root_node.tree_view.selected_node.unselect()

        self.is_selected = True
        self.root_node.tree_view.selected_node = self
        self._repaint()

    def on_release(self):
        self.select()
        self.toggle()


class TreeView(Gadget):
    """
    Base for creating tree-like views.

    Parameters
    ----------
    root_node : TreeViewNode
        Root node of tree view.
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
    update_tree_layout:
        Update tree layout after a child node is toggled open or closed.
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
        root_node: TreeViewNode,
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
        self.selected_node = None
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        root_node.toggle()

    def update_tree_layout(self):
        """
        Update tree layout after a child node is opened or closed.
        """

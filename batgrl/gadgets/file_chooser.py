"""
A file chooser gadget.
"""
import platform
from collections.abc import Callable
from pathlib import Path

from wcwidth import wcswidth

from ..colors import Color, ColorPair
from ..io import MouseButton
from .behaviors.themable import Themable
from .scroll_view import (
    DEFAULT_INDICATOR_HOVER,
    DEFAULT_INDICATOR_NORMAL,
    DEFAULT_INDICATOR_PRESS,
    DEFAULT_SCROLLBAR_COLOR,
    Point,
    PosHint,
    PosHintDict,
    ScrollView,
    Size,
    SizeHint,
    SizeHintDict,
)
from .tree_view import TreeView, TreeViewNode

__all__ = [
    "FileChooser",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

FILE_PREFIX = "  📄 "
FOLDER_PREFIX = "▶ 📁 "
NESTED_PREFIX = "  "
OPEN_FOLDER_PREFIX = "▼ 📂 "

if platform.system() == "Windows":
    from ctypes import windll

    # https://docs.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
    FILE_ATTRIBUTE_HIDDEN = 0x2
    FILE_ATTRIBUTE_SYSTEM = 0x4

    IS_HIDDEN = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM

    def _is_hidden(path: Path):
        attrs = windll.kernel32.GetFileAttributesW(str(path.absolute()))
        return attrs != -1 and bool(attrs & IS_HIDDEN)

else:

    def _is_hidden(path: Path):
        return path.stem.startswith(".")


class _FileViewNode(TreeViewNode):
    def __init__(self, path: Path, **kwargs):
        super().__init__(is_leaf=path.is_file(), **kwargs)
        self.path = path

    @property
    def label(self) -> str:
        if self.path.is_file():
            prefix = FILE_PREFIX
        elif self.is_open:
            prefix = OPEN_FOLDER_PREFIX
        else:
            prefix = FOLDER_PREFIX
        return f"{NESTED_PREFIX * self.level}{prefix}{self.path.name}"

    def _toggle_update(self):
        if not self.child_nodes:
            paths = sorted(
                self.path.iterdir(),
                key=lambda path: (path.is_file(), path.name),
            )

            for path in paths:
                self.add_node(_FileViewNode(path=path))

    def on_mouse(self, mouse_event):
        if (
            mouse_event.nclicks == 2
            and self.is_leaf
            and self.parent.selected_node is self
            and self.collides_point(mouse_event.position)
        ):
            self.parent.select_callback(self.path)
            return True

        return super().on_mouse(mouse_event)


class _FileView(TreeView):
    def __init__(
        self,
        root_node: _FileViewNode,
        directories_only: bool = False,
        show_hidden: bool = True,
        select_callback: Callable[[Path], None] = lambda path: None,
        **kwargs,
    ):
        self.directories_only = directories_only
        self.show_hidden = show_hidden
        self.select_callback = select_callback
        super().__init__(root_node=root_node, **kwargs)

    def update_tree_layout(self):
        self.prolicide()

        it = self.root_node.iter_open_nodes()
        if self.directories_only:
            it = (node for node in it if node.path.is_dir())
        if not self.show_hidden:
            it = (node for node in it if not _is_hidden(node.path))

        max_width = self.parent and self.parent.port_width or 1
        for y, node in enumerate(it):
            max_width = max(max_width, wcswidth(node.label))
            node.y = y
            self.add_gadget(node)
        self.size = y + 1, max_width

        for node in self.children:
            node.size = 1, max_width
            node.add_str(node.label)

    def on_key(self, key_event):
        if not self.children:
            return False

        match key_event.key:
            case "up":
                if self.selected_node is None:
                    self.children[0].select()
                else:
                    try:
                        index = self.children.index(self.selected_node)
                        if index == 0:
                            index += 1
                    except ValueError:
                        index = 1

                    self.children[index - 1].select()
            case "down":
                if self.selected_node is None:
                    self.children[0].select()
                else:
                    try:
                        index = self.children.index(self.selected_node)
                        if index == len(self.children) - 1:
                            index -= 1
                    except ValueError:
                        index = -1
                    self.children[index + 1].select()
            case "left":
                if self.selected_node is None:
                    self.children[0].select()
                elif self.selected_node.is_open:
                    self.selected_node.toggle()
                elif self.selected_node.parent_node is not self.root_node:
                    self.selected_node.parent_node.select()
            case "right":
                if self.selected_node is None:
                    self.children[0].select()
                elif self.selected_node.is_leaf:
                    pass
                elif not self.selected_node.is_open:
                    self.selected_node.toggle()
                elif self.selected_node.child_nodes:
                    self.selected_node.child_nodes[0].select()
            case "enter":
                if self.selected_node is not None:
                    self.select_callback(self.selected_node.path)
            case _:
                return super().on_key(key_event)

        top = self.selected_node.top + self.top
        if top < 0:
            self.parent._scroll_up(-top)
        elif top >= self.parent.height - 1:
            self.parent._scroll_down(self.parent.height - top)

        return True


class FileChooser(Themable, ScrollView):
    """
    A file chooser gadget.

    Parameters
    ----------
    root_dir : Path | None, default: None
        The root directory of the file chooser. If None, then
        root_dir will be cwd.
    directories_only : bool, default: False
        If true, show only directories in the file view.
    show_hidden : bool, default: True
        If false, hidden files won't be rendered.
    select_callback : Callable[[Path], None], default: lambda path: None
        Called with path of selected node when node is double-clicked
        or `enter` is pressed.
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    scrollbar_color : Color, default: DEFAULT_SCROLLBAR_COLOR
        Background color of scrollbar.
    indicator_normal_color : Color, default: DEFAULT_INDICATOR_NORMAL
        Scrollbar indicator normal color.
    indicator_hover_color : Color, default: DEFAULT_INDICATOR_HOVER
        Scrollbar indicator hover color.
    indicator_press_color : Color, default: DEFAULT_INDICATOR_PRESS
        Scrollbar indicator press color.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
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
    root_dir : Path
        The root directory of the file chooser.
    directories_only : bool
        If true, show only directories in the file view.
    show_hidden : bool
        If false, hidden files won't be rendered.
    select_callback : Callable[[Path], None]
        Called with path of selected node when node is double-clicked
        or `enter` is pressed.
    view : Gadget | None
        The scrolled gadget.
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    scrollbar_color : Color
        Background color of scrollbar.
    indicator_normal_color : Color
        Scrollbar indicator normal color.
    indicator_hover_color : Color
        Scrollbar indicator hover color.
    indicator_press_color : Color
        Scrollbar indicator press color.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        True if gadget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
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
    update_theme:
        Paint the gadget with current theme.
    grab:
        Grab the gadget.
    ungrab:
        Ungrab the gadget.
    grab_update:
        Update gadget with incoming mouse events while grabbed.
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
        root_dir: Path | None = None,
        directories_only: bool = False,
        show_hidden: bool = True,
        select_callback: Callable[[Path], None] = lambda path: None,
        arrow_keys_enabled: bool = False,
        allow_vertical_scroll: bool = True,
        allow_horizontal_scroll: bool = True,
        show_vertical_bar: bool = True,
        show_horizontal_bar: bool = True,
        scrollwheel_enabled: bool = True,
        scrollbar_color: Color = DEFAULT_SCROLLBAR_COLOR,
        indicator_normal_color: Color = DEFAULT_INDICATOR_NORMAL,
        indicator_hover_color: Color = DEFAULT_INDICATOR_HOVER,
        indicator_press_color: Color = DEFAULT_INDICATOR_PRESS,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
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
            arrow_keys_enabled=arrow_keys_enabled,
            allow_vertical_scroll=allow_vertical_scroll,
            allow_horizontal_scroll=allow_horizontal_scroll,
            show_vertical_bar=show_vertical_bar,
            show_horizontal_bar=show_horizontal_bar,
            scrollwheel_enabled=scrollwheel_enabled,
            scrollbar_color=scrollbar_color,
            indicator_normal_color=indicator_normal_color,
            indicator_hover_color=indicator_hover_color,
            indicator_press_color=indicator_press_color,
            is_grabbable=is_grabbable,
            disable_ptf=disable_ptf,
            mouse_button=mouse_button,
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
        path = root_dir or Path()
        self.view = _FileView(
            root_node=_FileViewNode(path=path),
            directories_only=directories_only,
            show_hidden=show_hidden,
            select_callback=select_callback,
        )
        self._root_dir = path

    def update_theme(self):
        self.background_color_pair = self.color_theme.primary.bg_color * 2

    def on_size(self):
        super().on_size()
        if self._view is not None:
            self._view.update_tree_layout()

    @property
    def directories_only(self):
        return self._view.directories_only

    @directories_only.setter
    def directories_only(self, directories_only):
        self._view.directories_only = directories_only
        self._view.update_tree_layout()

    @property
    def show_hidden(self):
        return self._view.show_hidden

    @show_hidden.setter
    def show_hidden(self, show_hidden):
        self._view.show_hidden = show_hidden
        self._view.update_tree_layout()

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    @root_dir.setter
    def root_dir(self, path: Path):
        self._root_dir = path
        if selected := self._view.selected_node:
            selected.unselect()
        root = self._view.root_node
        for node in root.child_nodes:
            node.level = -1
            node.parent_node = None
        root.child_nodes.clear()
        root.is_open = False
        root.path = path
        root.toggle()
        self.vertical_proportion = 0
        self.horizontal_proportion = 0

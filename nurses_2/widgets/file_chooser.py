"""
A file chooser widget.
"""
import platform
from pathlib import Path
from collections.abc import Callable

from wcwidth import wcswidth

from .scroll_view import ScrollView
from .tree_view import TreeViewNode, TreeView
from .behaviors.themable import Themable

__all__ = "FileChooser",

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
        return (
            f"{NESTED_PREFIX * self.level}"
            f"{FILE_PREFIX if self.path.is_file() else OPEN_FOLDER_PREFIX if self.is_open else FOLDER_PREFIX}"
            f"{self.path.name}"
        )

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
        directories_only: bool=False,
        show_hidden: bool=True,
        select_callback: Callable[[Path], None]=lambda path: None,
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
            self.add_widget(node)
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

        top = self.selected_node.top + self.top + self.parent.top
        if top < 0:
            self.parent._scroll_up(-top)
        elif top >= self.parent.bottom - 1:
            self.parent._scroll_down(self.parent.bottom - top)

        return True


class FileChooser(Themable, ScrollView):
    """
    A file chooser widget.

    Parameters
    ----------
    root_dir : Path | None, default: None
        The root directory of the file chooser. If None, then
        root_dir will be cwd.
    directories_only : bool, default: False
        If true, show only directories in the file view.
    show_hidden : bool, default: True
        If False, hidden files won't be rendered.
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
    is_grabbable : bool, default: True
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: False
        Allow scrolling with arrow keys. Navigating the file chooser with arrow keys
        will be disabled if scrolling with arrow keys is enabled.
    vertical_proportion : float, default: 0.0
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float, default: 0.0
        Horizontal scroll position as a proportion of total.
    is_grabbable : bool, default: True
        If False, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    root_dir : Path
        The root directory of the file chooser.
    directories_only : bool
        If true, show only directories in the file view.
    show_hidden : bool
        If False, hidden files won't be rendered.
    select_callback : Callable[[Path], None]
        Called with path of selected node when node is double-clicked
        or `enter` is pressed.
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    is_grabbable : bool
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys. Navigating the file chooser with arrow keys
        will be disabled if scrolling with arrow keys is enabled.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    view : Widget | None
        The scroll view's child.
    is_grabbable : bool
        If False, grabbable behavior is disabled.
    disable_ptf : bool
        If True, widget will not be pulled to front when grabbed.
    is_grabbed : bool
        True if widget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to `pos_hint`.
    background_char : str | None
        Background character.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    grab:
        Grab the widget.
    ungrab:
        Ungrab the widget.
    grab_update:
        Update widget with incoming mouse events while grabbed.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is True).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
    """
    def __init__(
        self,
        root_dir: Path | None=None,
        directories_only: bool=False,
        show_hidden: bool=True,
        select_callback: Callable[[Path], None]=lambda path: None,
        arrow_keys_enabled=False,
        **kwargs
    ):
        super().__init__(arrow_keys_enabled=arrow_keys_enabled, **kwargs)
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

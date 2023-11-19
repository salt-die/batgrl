"""A file chooser gadget."""
import platform
from collections.abc import Callable
from pathlib import Path

from wcwidth import wcswidth

from .gadget_base import (
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .scroll_view import ScrollView
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

        max_width = self.parent.port_width if self.parent else 1
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


class FileChooser(GadgetBase):
    r"""
    A file chooser gadget.

    Parameters
    ----------
    root_dir : Path | None, default: None
        The root directory of the file chooser or the cwd if not given.
    directories_only : bool, default: False
        If true, show only directories in the file view.
    show_hidden : bool, default: True
        If true, show hidden files.
    select_callback : Callable[[Path], None], default: lambda path: None
        Called with path of selected node when node is double-clicked
        or `enter` is pressed.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    root_dir : Path
        The root directory of the file chooser.
    directories_only : bool
        If true, show only directories in the file view.
    show_hidden : bool
        If true, show hidden files.
    select_callback : Callable[[Path], None]
        Called with path of selected node when node is double-clicked or `enter` is
        pressed.
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
        root_dir: Path | None = None,
        directories_only: bool = False,
        show_hidden: bool = True,
        select_callback: Callable[[Path], None] = lambda path: None,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
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
        self._root_dir = root_dir or Path()
        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1, "width_hint": 1},
            arrow_keys_enabled=False,
        )
        self._scroll_view.view = _FileView(
            root_node=_FileViewNode(path=self._root_dir),
            directories_only=directories_only,
            show_hidden=show_hidden,
            select_callback=select_callback,
        )
        self.add_gadget(self._scroll_view)

    def on_size(self):
        """Update tree layout on resize."""
        super().on_size()
        if self._scroll_view is not None:
            self._scroll_view._view.update_tree_layout()

    @property
    def directories_only(self):
        """If true, show only directories in the file view."""
        return self._view.directories_only

    @directories_only.setter
    def directories_only(self, directories_only):
        self._view.directories_only = directories_only
        self._view.update_tree_layout()

    @property
    def show_hidden(self):
        """If true, show hidden files."""
        return self._view.show_hidden

    @show_hidden.setter
    def show_hidden(self, show_hidden):
        self._view.show_hidden = show_hidden
        self._view.update_tree_layout()

    @property
    def root_dir(self) -> Path:
        """The root directory of the file chooser."""
        return self._root_dir

    @root_dir.setter
    def root_dir(self, path: Path):
        self._root_dir = path
        if selected := self._scroll_view._view.selected_node:
            selected.unselect()
        root = self._scroll_view._view.root_node
        for node in root.child_nodes:
            node.level = -1
            node.parent_node = None
        root.child_nodes.clear()
        root.is_open = False
        root.path = path
        root.toggle()
        self.vertical_proportion = 0
        self.horizontal_proportion = 0

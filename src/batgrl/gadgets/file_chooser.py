"""A file chooser gadget."""

import platform
from collections.abc import Callable
from pathlib import Path

from ..text_tools import str_width
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .scroll_view import ScrollView
from .tree_view import TreeView, TreeViewNode

__all__ = ["FileChooser", "Point", "Size"]

_FILE_PREFIX = "  📄 "
_FOLDER_PREFIX = "▶ 📁 "
_NESTED_PREFIX = "  "
_OPEN_FOLDER_PREFIX = "▼ 📂 "

if platform.system() == "Windows":
    from ctypes import windll

    def _is_hidden(path: Path) -> bool:
        attrs = windll.kernel32.GetFileAttributesW(str(path.absolute()))
        # https://docs.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
        is_hidden = 0x2 | 0x4
        return attrs != -1 and bool(attrs & is_hidden)

else:

    def _is_hidden(path: Path) -> bool:
        return path.stem.startswith(".")


class _ParentDirectory(TreeViewNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = ".."
        self.set_text(self.label)

    def on_mouse(self, mouse_event):
        if (
            mouse_event.nclicks == 2
            and self.parent.selected_node is self
            and self.collides_point(mouse_event.pos)
        ):
            for ancestor in self.ancestors():
                if isinstance(ancestor, FileChooser):
                    break
            else:
                return False

            root_dir = ancestor.root_dir
            root_dir_parent = root_dir.parent
            if root_dir != root_dir_parent:
                ancestor.root_dir = root_dir_parent
            return True

        return super().on_mouse(mouse_event)


class _FileViewNode(TreeViewNode):
    def __init__(self, path: Path, **kwargs):
        super().__init__(is_leaf=path.is_file(), **kwargs)
        self.path = path

    @property
    def label(self) -> str:
        if self.path.is_file():
            prefix = _FILE_PREFIX
        elif self.is_open:
            prefix = _OPEN_FOLDER_PREFIX
        else:
            prefix = _FOLDER_PREFIX
        return f"{_NESTED_PREFIX * self.level}{prefix}{self.path.name}"

    def _toggle_update(self):
        if not self.child_nodes:
            try:
                paths = sorted(
                    self.path.iterdir(), key=lambda path: (path.is_file(), path.name)
                )

                for path in paths:
                    self.add_node(_FileViewNode(path=path))
            except PermissionError:
                return

    def on_mouse(self, mouse_event):
        if (
            mouse_event.nclicks == 2
            and self.is_leaf
            and self.parent.select_callback is not None
            and self.parent.selected_node is self
            and self.collides_point(mouse_event.pos)
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
        show_parent_dir: bool = False,
        select_callback: Callable[[Path], None] | None = None,
        filter: Callable[[Path], bool] | None = None,
        **kwargs,
    ):
        self.directories_only = directories_only
        self.show_hidden = show_hidden
        self.show_parent_dir = show_parent_dir
        self.select_callback = select_callback
        self.filter = filter
        super().__init__(root_node=root_node, **kwargs)

    def on_add(self):
        self.update_tree_layout()

    def update_tree_layout(self):
        if self.root is None:
            return

        self.prolicide()

        alpha = self.root_node.alpha
        is_transparent = self.root_node.is_transparent
        it = self.root_node.iter_open_nodes()
        if self.directories_only:
            it = (node for node in it if node.path.is_dir())
        if not self.show_hidden:
            it = (node for node in it if not _is_hidden(node.path))
        if self.filter is not None:
            it = (node for node in it if self.filter(node.path))

        sv: ScrollView = self.parent
        sv.size = sv.parent.size
        max_width = sv.port_width

        if self.show_parent_dir:
            parent_dir = _ParentDirectory()
            parent_dir.parent_node = self.root_node
            parent_dir.alpha = alpha
            parent_dir.is_transparent = is_transparent
            max_width = max(max_width, str_width(parent_dir.label))
            self.add_gadget(parent_dir)
            start = 1
        else:
            start = 0

        for y, node in enumerate(it, start=start):
            node.alpha = alpha
            node.is_transparent = is_transparent
            node.y = y
            max_width = max(max_width, str_width(node.label))
            self.add_gadget(node)
        self.size = y + 1, max_width

        node: TreeViewNode
        for node in self.children:
            node.size = 1, max_width
            node.add_str(node.label)

    def on_key(self, key_event):
        if not self.children:
            return False

        if key_event.key == "up":
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
        elif key_event.key == "down":
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
        elif key_event.key == "left":
            if self.selected_node is None:
                self.children[0].select()
            elif self.selected_node.is_open:
                self.selected_node.toggle()
            elif self.selected_node.parent_node is not self.root_node:
                self.selected_node.parent_node.select()
        elif key_event.key == "right":
            if self.selected_node is None:
                self.children[0].select()
            elif self.selected_node.is_leaf:
                pass
            elif not self.selected_node.is_open:
                self.selected_node.toggle()
            elif self.selected_node.child_nodes:
                self.selected_node.child_nodes[0].select()
        elif key_event.key == "enter":
            if self.selected_node is not None and self.select_callback is not None:
                self.select_callback(self.selected_node.path)
        else:
            return super().on_key(key_event)

        if self.selected_node is not None:
            self.parent.scroll_to_rect(self.selected_node.pos)

        return True


class FileChooser(Gadget):
    r"""
    A file chooser gadget.

    Parameters
    ----------
    root_dir : Path | None, default: None
        The root directory of the file chooser or the cwd if not given.
    directories_only : bool, default: False
        Whether to show only directories in the file view.
    show_hidden : bool, default: True
        Whether to show hidden files.
    show_parent_dir : bool, default: False
        Whether parent directory is shown as "..". Double-clicking or pressing enter
        while selected will change the root directory of the file chooser to the parent
        directory.
    select_callback : Callable[[Path], None] | None, default: None
        Called with selected path on double-click or if enter is pressed.
    filter : Callable[[Path], bool] | None, default: None
        Determines whether a path is displayed.
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
    root_dir : Path
        The root directory of the file chooser.
    directories_only : bool
        Whether to show only directories in the file view.
    show_hidden : bool
        Whether to show hidden files.
    show_parent_dir : bool, default: False
        Whether parent directory is shown as "..".
    select_callback : Callable[[Path], None]
        Called with selected path on double-click or if `enter` is pressed.
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
        root_dir: Path | None = None,
        directories_only: bool = False,
        show_hidden: bool = True,
        show_parent_dir: bool = False,
        select_callback: Callable[[Path], None] | None = None,
        filter: Callable[[Path], bool] | None = None,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._root_dir = root_dir or Path()
        self._root_node = _FileViewNode(
            path=self._root_dir, is_transparent=is_transparent
        )
        self._file_view = _FileView(
            root_node=self._root_node,
            directories_only=directories_only,
            show_hidden=show_hidden,
            show_parent_dir=show_parent_dir,
            select_callback=select_callback,
            filter=filter,
            is_transparent=is_transparent,
        )
        self._scroll_view = ScrollView(
            dynamic_bars=True,
            arrow_keys_enabled=False,
            is_transparent=is_transparent,
            alpha=0,
        )
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.alpha = alpha
        self._scroll_view.view = self._file_view
        self.add_gadget(self._scroll_view)

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._root_node.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._root_node.alpha = alpha
        for node in self._root_node.iter_open_nodes():
            node.alpha = alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._root_node.is_transparent = self.is_transparent
        for node in self._root_node.iter_open_nodes():
            node.is_transparent = self.is_transparent
        self._file_view.is_transparent = self.is_transparent
        self._scroll_view.is_transparent = self.is_transparent

    def on_size(self):
        """Update tree layout on resize."""
        self._file_view.update_tree_layout()

    @property
    def directories_only(self):
        """Whether to show only directories in the file view."""
        return self._file_view.directories_only

    @directories_only.setter
    def directories_only(self, directories_only):
        self._file_view.directories_only = directories_only
        self._file_view.update_tree_layout()

    @property
    def show_hidden(self):
        """Whether to show hidden files."""
        return self._file_view.show_hidden

    @show_hidden.setter
    def show_hidden(self, show_hidden):
        self._file_view.show_hidden = show_hidden
        self._file_view.update_tree_layout()

    @property
    def show_parent_dir(self):
        """Whether parent directory is shown as ".."."""
        return self._file_view.show_parent_dir

    @show_parent_dir.setter
    def show_parent_dir(self, show_parent_dir):
        self._file_view.show_parent_dir = show_parent_dir
        self._file_view.update_tree_layout()

    @property
    def root_dir(self) -> Path:
        """The root directory of the file chooser."""
        return self._root_dir

    @root_dir.setter
    def root_dir(self, path: Path):
        self._root_dir = path
        if selected := self._file_view.selected_node:
            selected.unselect()
        root = self._root_node
        for node in root.child_nodes:
            node.level = -1
            node.parent_node = None
        root.child_nodes.clear()
        root.is_open = False
        root.path = path
        root.toggle()
        self.vertical_proportion = 0
        self.horizontal_proportion = 0

from pathlib import Path
from typing import Callable

from ..io.environ import is_windows
from .scroll_view import ScrollView
from .tree_view import TreeViewNode, TreeView

FILE_PREFIX = "  📄 "
FOLDER_PREFIX = "▶ 📁 "
NESTED_PREFIX = "  "
OPEN_FOLDER_PREFIX = "▼ 📂 "

if is_windows():
    from win32api import GetFileAttributes
    from win32con import FILE_ATTRIBUTE_HIDDEN, FILE_ATTRIBUTE_SYSTEM

    IS_HIDDEN = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM

    def is_hidden(path: Path):
        return GetFileAttributes(str(path.absolute())) & IS_HIDDEN

else:
    def is_hidden(path: Path):
        return path.stem.startswith(".")


class FileViewNode(TreeViewNode):
    def __init__(self, path: Path, **kwargs):
        self.path = path

        super().__init__(is_leaf=path.is_file(), **kwargs)

    def _toggle_update(self):
        if not self.child_nodes:
            prefix = NESTED_PREFIX * (self.level + 1)

            paths = sorted(
                self.path.iterdir(),
                key=lambda path: (path.is_file(), path.name),
            )

            for path in paths:
                file_view_node = FileViewNode(path=path)

                self.add_node(file_view_node)

                file_view_node.label = (
                    f"{prefix}"
                    f"{FOLDER_PREFIX if file_view_node.path.is_dir() else FILE_PREFIX}"
                    f"{file_view_node.path.name}"
                )

        self.label = (
            f"{NESTED_PREFIX * self.level}"
            f"{OPEN_FOLDER_PREFIX if self.is_open else FOLDER_PREFIX}"
            f"{self.path.name}"
        )


class FileView(TreeView):
    def __init__(
        self,
        root_node: FileViewNode,
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
        for widget in self.children:
            widget.parent = None

        self.children.clear()

        it = self.root_node.iter_open_nodes()

        if self.directories_only:
            it = (node for node in it if node.path.is_dir())

        if not self.show_hidden:
            it = (node for node in it if not is_hidden(node.path))

        max_width = self.parent and self.parent.width or -1
        for i, node in enumerate(it):
            if len(node.label) + 1 > max_width:
                max_width = len(node.label) + 1

            node.top = i
            self.add_widget(node)

        for node in self.children:
            node.resize((1, max_width))
            node.repaint()
            node.add_text(f"{node.label:<{max_width}}")

        self.resize((i + 1, max_width))

    def on_press(self, key_press_event):
        if not self.children:
            return False

        match key_press_event.key:
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
                return super().on_press(key_press_event)

        top = self.selected_node.top + self.top + self.parent.top
        if top < 0:
            self.parent._scroll_up(-top)
        elif top >= self.parent.bottom - 1:
            self.parent._scroll_down(self.parent.bottom - top)

        return True

    def on_double_click(self, mouse_event):
        if (
            self.selected_node is not None
            and self.selected_node.collides_point(mouse_event.position)
        ):
            self.select_callback(self.selected_node.path)
            return True


class FileChooser(ScrollView):
    def __init__(
        self,
        root_dir: Path | None=None,
        directories_only: bool=False,
        show_hidden: bool=True,
        select_callback: Callable[[Path], None]=lambda path: None,
        **kwargs
    ):
        kwargs.pop("arrow_keys_enabled", None)
        super().__init__(arrow_keys_enabled=False, **kwargs)

        self.add_widget(
            FileView(
                root_node=FileViewNode(path=root_dir or Path()),
                directories_only=directories_only,
                show_hidden=show_hidden,
                select_callback=select_callback,
            )
        )
        self._view.update_tree_layout()

    def resize(self, size):
        super().resize(size)
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
        self._view.updated_tree_layout()

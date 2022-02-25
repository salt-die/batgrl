from pathlib import Path
from typing import Callable

from ..io.environ import is_windows
from ..colors import ColorPair
from .scroll_view import ScrollView
from .tree_view import (
    BRIGHT_PURPLE_ON_PURPLE,
    VERY_BRIGHT_PURPLE_ON_LIGHT_PURPLE,
    WHITE_ON_LIGHT_PURPLE,
    WHITE_ON_PURPLE,
    TreeViewNode,
    TreeView,
)

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
            paths = sorted(
                self.path.iterdir(),
                key=lambda path: (path.is_file(), path.name)
            )
            prefix = NESTED_PREFIX * (self.level + 1)

            for path in paths:
                file_view_node = FileViewNode(
                    path=path,
                    default_color_pair=self.default_color_pair,
                    hover_color_pair=self.hover_color_pair,
                    selected_color_pair=self.selected_color_pair,
                    hover_selected_color_pair=self.hover_selected_color_pair,
                )
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

    def on_double_click(self, mouse_event):
        if self.collides_point(mouse_event.position):
            self.root_node.container.select_callback(self.path)
            return True


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
            it = filter(lambda node: node.path.is_dir(), it)

        if not self.show_hidden:
            it = filter(lambda node: not is_hidden(node.path), it)

        max_width = -1
        for i, node in enumerate(it):
            if len(node.label) + 1 > max_width:
                max_width = len(node.label) + 1

            node.top = i
            self.add_widget(node)

        for node in self.children:
            node.resize((1, max_width))
            node.add_text(f"{node.label:<{max_width}}")

        self.resize((i + 1, max_width))


class FileChooser(ScrollView):
    def __init__(
        self,
        root_dir: Path | None=None,
        directories_only: bool=False,
        show_hidden: bool=True,
        select_callback: Callable[[Path], None]=lambda path: None,
        default_color_pair: ColorPair=BRIGHT_PURPLE_ON_PURPLE,
        hover_color_pair: ColorPair=VERY_BRIGHT_PURPLE_ON_LIGHT_PURPLE,
        selected_color_pair: ColorPair=WHITE_ON_PURPLE,
        hover_selected_color_pair: ColorPair=WHITE_ON_LIGHT_PURPLE,
        **kwargs,
    ):
        super().__init__(default_color_pair=default_color_pair, **kwargs)

        if root_dir is None:
            root_dir = Path()

        self.add_widget(
            FileView(
                root_node=FileViewNode(
                    path=root_dir,
                    default_color_pair=default_color_pair,
                    hover_color_pair=hover_color_pair,
                    selected_color_pair=selected_color_pair,
                    hover_selected_color_pair=hover_selected_color_pair,
                ),
                directories_only=directories_only,
                show_hidden=show_hidden,
                select_callback=select_callback,
            )
        )

    @property
    def directories_only(self):
        return self._view.directories_only

    @directories_only.setter
    def directories_only(self, directories_only):
        self._view.directories_only = directories_only

    @property
    def show_hidden(self):
        return self._view.show_hidden

    @show_hidden.setter
    def show_hidden(self, show_hidden):
        self._view.show_hidden = show_hidden

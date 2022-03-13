from ..colors import ColorPair
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
from .text_widget import TextWidget
from .widget import Widget


class TreeViewNode(Themable, ButtonBehavior, TextWidget):
    def __init__(self, is_leaf=True, **kwargs):
        self.is_leaf = is_leaf

        self.is_open = False
        self.is_selected = False

        self.parent_node = None
        self.child_nodes = [ ]
        self.level = -1

        self.normal_color_pair = (0, ) * 6  # Temporary assignment

        super().__init__(**kwargs)

        self.update_theme()

    def update_theme(self):
        ct = self.color_theme

        self.normal_color_pair = ct.primary_color_pair
        self.hover_color_pair = ct.primary_light_color_pair
        self.selected_color_pair = ct.secondary_color_pair
        self.hover_selected_color_pair = ColorPair.from_colors(ct.secondary_fg, ct.primary_bg_light)

        self.repaint()

    def repaint(self):
        if self.state is ButtonState.NORMAL:
            self.update_normal()
        else:
            self.update_hover()

    @property
    def root_node(self):
        if self.parent_node is None:
            return self

        return self.parent_node.root_node

    def iter_open_nodes(self):
        for child in self.child_nodes:
            yield child

            if child.is_open:
                yield from child.iter_open_nodes()

    def add_node(self, node):
        self.child_nodes.append(node)

        node.level = self.level + 1
        node.parent_node = self

    def remove_node(self, node):
        self.child_nodes.remove(node)

        node.level = -1
        node.parent_node = None

    def _toggle_update(self):
        """
        Update state after `toggle` is called.
        """

    def toggle(self):
        if not self.is_leaf:
            self.is_open = not self.is_open
            self._toggle_update()
            self.root_node.tree_view.update_tree_layout()

    def unselect(self):
        self.is_selected = False
        self.root_node.tree_view.selected_node = None
        self.repaint()

    def select(self):
        if self.root_node.tree_view.selected_node is not None:
            self.root_node.tree_view.selected_node.unselect()

        self.is_selected = True
        self.root_node.tree_view.selected_node = self
        self.repaint()

    def update_hover(self):
        if self.is_selected:
            self.colors[:] = self.hover_selected_color_pair
        else:
            self.colors[:] = self.hover_color_pair

    def update_normal(self):
        if self.is_selected:
            self.colors[:] = self.selected_color_pair
        else:
            self.colors[:] = self.normal_color_pair

    def on_release(self):
        self.select()
        self.toggle()


class TreeView(Widget):
    def __init__(self, root_node: TreeViewNode, **kwargs):
        self.selected_node = None
        self.root_node = root_node
        root_node.tree_view = self

        super().__init__(**kwargs)

        root_node.toggle()

    def update_tree_layout(self):
        """
        Update tree layout after a child node is opened or closed.
        """

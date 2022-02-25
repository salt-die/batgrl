from ..colors import Color, ColorPair, WHITE
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .text_widget import TextWidget

PURPLE = Color.from_hex("#462270")
LIGHT_PURPLE = Color.from_hex("#5e2f92")
BRIGHT_PURPLE = Color.from_hex("#9976e0")
VERY_BRIGHT_PURPLE = Color.from_hex("#bba4ea")

BRIGHT_PURPLE_ON_PURPLE = ColorPair.from_colors(BRIGHT_PURPLE, PURPLE)
VERY_BRIGHT_PURPLE_ON_LIGHT_PURPLE = ColorPair.from_colors(VERY_BRIGHT_PURPLE, LIGHT_PURPLE)
WHITE_ON_PURPLE = ColorPair.from_colors(WHITE, PURPLE)
WHITE_ON_LIGHT_PURPLE = ColorPair.from_colors(WHITE, LIGHT_PURPLE)


class TreeViewNode(ButtonBehavior, TextWidget):
    def __init__(
        self,
        is_leaf=True,
        default_color_pair=BRIGHT_PURPLE_ON_PURPLE,
        hover_color_pair=VERY_BRIGHT_PURPLE_ON_LIGHT_PURPLE,
        selected_color_pair=WHITE_ON_PURPLE,
        hover_selected_color_pair=WHITE_ON_LIGHT_PURPLE,
        **kwargs
    ):
        self.is_leaf = is_leaf

        self.is_open = False
        self.is_selected = False

        self.parent_node = None
        self.child_nodes = [ ]
        self.level = -1

        self.hover_color_pair = hover_color_pair
        self.selected_color_pair = selected_color_pair
        self.hover_selected_color_pair= hover_selected_color_pair

        super().__init__(default_color_pair=default_color_pair, **kwargs)

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

        if self.state is ButtonState.NORMAL:
            self.update_normal()
        else:
            self.update_hover()

    def select(self):
        if self.root_node.tree_view.selected_node is not None:
            self.root_node.tree_view.selected_node.unselect()

        self.is_selected = True
        self.root_node.tree_view.selected_node = self

        if self.state is ButtonState.NORMAL:
            self.update_normal()
        else:
            self.update_hover()

    def update_hover(self):
        if self.is_selected:
            self.colors[:] = self.hover_selected_color_pair
        else:
            self.colors[:] = self.hover_color_pair

    def update_normal(self):
        if self.is_selected:
            self.colors[:] = self.selected_color_pair
        else:
            self.colors[:] = self.default_color_pair

    def on_release(self):
        self.select()
        self.toggle()


class TreeView(TextWidget):
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

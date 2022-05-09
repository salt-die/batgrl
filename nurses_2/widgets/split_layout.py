from ..clamp import clamp
from ..colors import AColor
from .behaviors.grabbable_behavior import GrabbableBehavior
from .graphic_widget import GraphicWidget
from .widget import Widget

__all__ = "HSplitLayout", "VSplitLayout",

AGRAY = AColor(127, 127, 127, 255)


class _Handle(GrabbableBehavior, GraphicWidget):
    def __init__(self, size_hint):
        super().__init__(
            alpha=.5,
            default_color=AGRAY,
            size=(1, 1),
            size_hint=size_hint,
            is_visible=False,
        )

    def on_click(self, mouse_event):
        self.is_visible = (
            self.is_grabbable
            and self.is_grabbed or self.collides_point(mouse_event.position)
        )
        return super().on_click(mouse_event)


class _HSplitHandle(_Handle):
    def grab_update(self, mouse_event):
        if self.parent.anchor_left_pane:
            self.parent.split_col += self.mouse_dx
        else:
            self.parent.split_col -= self.mouse_dx


class _VSplitHandle(_Handle):
    def grab_update(self, mouse_event):
        if self.parent.anchor_top_pane:
            self.parent.split_row += self.mouse_dy
        else:
            self.parent.split_row -= self.mouse_dy


class HSplitLayout(Widget):
    """
    A horizontal split layout. Add widgets to the `left_pane` or `right_pane`,
    e.g., `my_hsplit.left_pane.add_widget(my_widget)`.

    Parameters
    ----------
    split_col : int, default: 1
        The column to split the layout. If `anchor_left_pane`
        is true, then split will be `split_col` from the left,
        else from the right.
    anchor_left_pane : bool, default: True
        If true, `split_col` will be calculated from the left,
        else from the right.
    split_resizable : bool, default: True
        If true, the split will be resizable with a grabbable
        handle.
    """
    def __init__(
        self,
        split_col: int=1,
        anchor_left_pane: bool=True,
        split_resizable: bool=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.left_pane = Widget(size_hint=(1.0, None))
        self.right_pane = Widget(size_hint=(1.0, None))

        self._handle = _HSplitHandle((1.0, None))
        def adjust(event):
            self.right_pane.left = self._handle.left = event.source.right
        self._handle.subscribe(self.left_pane, "size", adjust)

        self.add_widgets(self.left_pane, self.right_pane, self._handle)

        self.split_resizable = split_resizable
        self.anchor_left_pane = anchor_left_pane

        self.split_col = split_col

    @property
    def split_col(self) -> int:
        return self._split_row

    @split_col.setter
    def split_col(self, split_col: int):
        self._split_row = clamp(split_col, 1, self.width - 1)
        self.on_size()

    @property
    def split_resizable(self) -> bool:
        return self._handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self._handle.is_grabbable = split_resizable

    def on_size(self):
        if self.anchor_left_pane:
            anchored = self.left_pane
            not_anchored = self.right_pane
        else:
            anchored = self.right_pane
            not_anchored = self.left_pane

        if self.split_col < self.width:
            anchored.width = self.split_col
            not_anchored.width = self.width - self.split_col
        else:
            anchored.width = self.width - 1
            not_anchored.width = 1


class VSplitLayout(Widget):
    """
    A vertical split layout. Add widgets to the `top_pane` or `bottom_pane`,
    e.g., `my_vsplit.top_pane.add_widget(my_widget)`.

    Parameters
    ----------
    split_row : int, default: 1
        The row to split the layout. If `anchor_top_pane`
        is true, then split will be `split_row` from the top,
        else from the bottom.
    anchor_top_pane : bool, default: True
        If true, `split_row` will be calculated from the top,
        else from the bottom.
    split_resizable : bool, default: True
        If true, the split will be resizable with a grabbable
        handle.
    """
    def __init__(
        self,
        split_row: int=1,
        anchor_top_pane: bool=True,
        split_resizable: bool=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.top_pane = Widget(size_hint=(None, 1.0))
        self.bottom_pane = Widget(size_hint=(None, 1.0))

        self._handle = _VSplitHandle((None, 1.0))
        def adjust(event):
            self.bottom_pane.top = self._handle.top = event.source.bottom
        self._handle.subscribe(self.top_pane, "size", adjust)

        self.add_widgets(self.top_pane, self.bottom_pane, self._handle)

        self.split_resizable = split_resizable
        self.anchor_top_pane = anchor_top_pane

        self.split_row = split_row

    @property
    def split_row(self) -> int:
        return self._split_col

    @split_row.setter
    def split_row(self, split_row: int):
        self._split_col = clamp(split_row, 1, self.height - 1)
        self.on_size()

    @property
    def split_resizable(self) -> bool:
        return self._handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self._handle.is_grabbable = split_resizable

    def on_size(self):
        if self.anchor_top_pane:
            anchored = self.top_pane
            not_anchored = self.bottom_pane
        else:
            anchored = self.bottom_pane
            not_anchored = self.top_pane

        if self.split_row < self.height:
            anchored.height = self.split_row
            not_anchored.height = self.height - self.split_row
        else:
            anchored.height = self.height - 1
            not_anchored.height = 1


from ..colors import Color, ColorPair
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.grab_resize_behavior import GrabResizeBehavior
from .text_widget import TextWidget
from .widget_base import WidgetBase, Size, Anchor

YELLOW = Color.from_hex("dbd006")
PURPLE = Color.from_hex("462270")
DARK_PURPLE = Color.from_hex("20073a")
YELLOW_ON_PURPLE = ColorPair.from_colors(YELLOW, PURPLE)


class _TitleBar(GrabbableBehavior, TextWidget):
    def __init__(self, title="", **kwargs):
        super().__init__(disable_ptf=True, **kwargs)

        self._label = TextWidget(
            size=(1, len(title)),
            pos_hint=(None, .5),
            anchor=Anchor.TOP_CENTER,
            default_color_pair=self.default_color_pair,
        )
        self._label.add_text(title)
        self.add_widget(self._label)

    def grab(self, mouse_event):
        self.parent.pull_to_front()
        super().grab(mouse_event)

    def grab_update(self, mouse_event):
        self.parent.top += self.mouse_dy
        self.parent.left += self.mouse_dx


class _Border(TextWidget):
    def resize(self, size: Size):
        super().resize(size)
        self.canvas[:] = " "
        self.canvas[[0, -1]] = self.canvas[:, [0, 1, -2, -1]] = "█"


class Window(GrabResizeBehavior, WidgetBase):
    """
    A movable, resizable window widget.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    title_color_pair : ColorPair, default: YELLOW_ON_PURPLE
        Color pair of title.
    border_color_pair : Color, default: DARK_PURPLE
        Color of border.
    """
    def __init__(
        self,
        title="",
        title_color_pair: ColorPair=YELLOW_ON_PURPLE,
        border_color: Color=DARK_PURPLE,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._border = _Border(
            default_color_pair=ColorPair.from_colors(border_color, border_color),
            is_transparent=True,
        )
        self._titlebar = _TitleBar(title=title, default_color_pair=title_color_pair, pos=(1, 2))
        self._view = TextWidget(pos=(2, 2))
        self._border.parent = self._titlebar.parent = self._view.parent = self

        self.children = [self._titlebar, self._view]

        self.resize(self.size)

    def resize(self, size: Size):
        h, w = size
        self._size = Size(h, w)

        self._border.resize(size)
        self._titlebar.resize((1, w - 4))
        self._view.resize((h - 3, w - 4))

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self._border.render_intersection(source, canvas_view, colors_view)
        self._titlebar.render_intersection(source, canvas_view, colors_view)
        self._view.render_intersection(source, canvas_view, colors_view)

    def add_widget(self, widget):
        self._view.add_widget(widget)

    def remove_widget(self, widget):
        self._view.remove_widget(widget)

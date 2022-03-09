
from ..clamp import clamp
from ..colors import ColorPair, AColor
from .behaviors.focus_behavior import FocusBehavior
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.grab_resize_behavior import GrabResizeBehavior
from .behaviors.themable import Themable
from .graphic_widget import GraphicWidget
from .text_widget import TextWidget
from .widget import Widget, Size, Anchor


class TitleBar(GrabbableBehavior, TextWidget):
    def __init__(self, **kwargs):
        super().__init__(disable_ptf=True, **kwargs)

        self._label = TextWidget(pos_hint=(None, .5), anchor=Anchor.TOP_CENTER)
        self.add_widget(self._label)

    def grab_update(self, mouse_event):
        self.parent.top += self.mouse_dy
        self.parent.left += self.mouse_dx


class Window(Themable, FocusBehavior, GrabResizeBehavior, Widget):
    """
    A movable, resizable window widget.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    alpha : float, default: 1.0
        Transparency of window background and border.
    """
    def __init__(self, title="", alpha=1.0, min_height=3, min_width=None, **kwargs):
        if min_width is None:
            min_width = len(title) + 6

        super().__init__(min_height=min_height, min_width=min_width, **kwargs)

        self._border = GraphicWidget()
        self._titlebar = TitleBar(pos=(1, 2))
        self._view = GraphicWidget(pos=(2, 2))

        self._titlebar.parent = self._view.parent = self
        self.children = [self._view, self._titlebar]

        self.title = title
        self.alpha = alpha

        self.update_theme()

        self.resize(self.size)

    @property
    def title(sef):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.resize((1, len(title)))
        self._titlebar._label.add_text(title)

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(alpha, min=0.0, max=1.0)
        self._border.alpha = self._view.alpha = self._alpha

    def update_theme(self):
        ct = self.color_theme

        view_background = AColor(*ct.primary_bg_light, 255)
        self._view.default_color = view_background
        self._view.texture[:] = view_background

        if self.is_focused:
            border_color = AColor(*ct.secondary_bg, 255)
        else:
            border_color = AColor(*ct.primary_bg, 255)

        self._border.default_color = border_color
        self._border.texture[:] = border_color

        title_bar_color_pair = ColorPair.from_colors(ct.secondary_bg, ct.primary_bg_dark)
        self._titlebar.default_color_pair = title_bar_color_pair
        self._titlebar.colors[:] = title_bar_color_pair
        self._titlebar._label.default_color_pair = title_bar_color_pair
        self._titlebar._label.colors[:] = title_bar_color_pair

    def on_focus(self):
        self.update_theme()

    def on_blur(self):
        self.update_theme()

    def resize(self, size: Size):
        h, w = size
        self._size = h, w = Size(clamp(h, 1, None), clamp(w, 1, None))

        self._border.resize(size)
        self._titlebar.resize((1, w - 4))
        self._view.resize((h - 3, w - 4))

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self._border.render_intersection(source, canvas_view, colors_view)

        h, w = self.size

        if w > 4:
            if h > 2:
                self._titlebar.render_intersection(source, canvas_view, colors_view)
            if h > 3:
                self._view.render_intersection(source, canvas_view, colors_view)

    def add_widget(self, widget):
        self._view.add_widget(widget)

    def remove_widget(self, widget):
        self._view.remove_widget(widget)

    def dispatch_click(self, mouse_event):
        return super().dispatch_click(mouse_event) or self.collides_point(mouse_event.position)

    def dispatch_double_click(self, mouse_event):
        return super().dispatch_double_click(mouse_event) or self.collides_point(mouse_event.position)

    def dispatch_triple_click(self, mouse_event):
        return super().dispatch_triple_click(mouse_event) or self.collides_point(mouse_event.position)

import numpy as np

from ...colors import Color
from ...io import MouseEvent, MouseEventType
from ..text_widget import TextWidget, SizeHint, Anchor
from ..scroll_view import ScrollView
from ._legend import _Legend
from ._traces import _Traces

PLOT_SIZES = [SizeHint(x, x) for x in (1.0, 1.25, 1.75, 2.75, 5.0)]


class LinePlot(TextWidget):
    def __init__(
        self,
        *points: list[float] | np.ndarray,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        xlabel: str | None=None,
        ylabel: str | None=None,
        legend: list[str] | None=None,
        colors: list[Color] | None=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._trace_size_hint = 0

        self._traces = _Traces(*points, xmin, xmax, ymin, ymax)

        self._scrollview = ScrollView(
            show_vertical_bar=False,
            show_horizontal_bar=False,
            scrollwheel_enabled=False,
        )
        self._scrollview.add_widget(self._traces) # Scrollview needs to be positioned next to ticks.
        self.add_widget(self._scrollview)

        if xlabel is not None:
            self.xlabel = TextWidget(size=(1, len(xlabel)), pos_hint=(1.0, .5), anchor=Anchor.BOTTOM_CENTER)
            self.xlabel.add_text(xlabel)
            self.add_widget(self.xlabel)

        if ylabel is not None:
            self.ylabel = TextWidget(size=(len(ylabel), 1), pos_hint=(.5, 0.0), anchor=Anchor.LEFT_CENTER)
            self.ylabel.get_view[:, 0].add_text(ylabel)
            self.add_widget(self.ylabel)

        self.add_widgets(
            self._traces.xticks,
            self._traces.yticks,
        )

        if legend is not None:
            self._legend = _Legend(
                legend,
                colors,
                pos_hint=(.9, .9),
                anchor=Anchor.BOTTOM_RIGHT
            )
            self.add_widget(self._legend)

    def on_click(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        match mouse_event.event_type:
            case MouseEventType.SCROLL_UP:
                self._trace_size_hint = min(self._trace_size_hint + 1, len(PLOT_SIZES))
            case MouseEventType.SCROLL_DOWN:
                self._trace_size_hint = max(0, self._trace_size_hint - 1)
            case _:
                return super().on_click(mouse_event)

        self._traces.size_hint = PLOT_SIZES[self._trace_size_hint]
        return True

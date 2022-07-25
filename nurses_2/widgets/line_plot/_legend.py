"""
Legend for :class:`nurses_2.widgets.line_plot.LinePlot`.
"""
from wcwidth import wcswidth

from ...colors import Color
from ..behaviors.grab_move_behavior import GrabMoveBehavior
from ..text_widget import TextWidget


class _Legend(GrabMoveBehavior, TextWidget):
    def __init__(self, labels: list[str], colors: list[Color], **kwargs):
        height = len(labels) + 2
        width = 6 + max(map(wcswidth, labels))

        super().__init__(size=(height, width), disable_oob=True, **kwargs)

        self.add_border()

        self.canvas[1:-1, 2] = "█"
        self.colors[1:-1, 2, :3] = colors

        for i, name in enumerate(labels, start=1):
            self.add_text(name, i, 4)

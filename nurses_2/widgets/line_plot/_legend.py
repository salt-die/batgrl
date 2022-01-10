from ...colors import Color
from ..behaviors.draggable_behavior import DraggableBehavior
from ..text_widget import TextWidget


class _Legend(DraggableBehavior, TextWidget):
    def __init__(self, labels: list[str], colors: list[Color], **kwargs):
        if len(labels) != len(colors):
            raise ValueError("Not enough labels provided for legend.")

        height = len(labels) + 2
        width = 6 + max(map(len, labels))

        super().__init__(size=(height, width), disable_oob=True, **kwargs)

        self.add_border()

        self.canvas[1:-1, 2] = "█"
        self.colors[1:-1, 2, :3] = colors

        for i, name in enumerate(labels, start=1):
            self.add_text(name, i, 4)

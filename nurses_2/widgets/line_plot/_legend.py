from ..behaviors.draggable_behavior import DraggableBehavior
from ..text_widget import TextWidget


class _Legend(DraggableBehavior, TextWidget):
    def __init__(self, names: list[str], colors: list[Color], **kwargs):
        height = len(names) * 2 + 1
        width = 6 + max(map(len, names))

        super().__init__(size=(height, width), disable_oob=True, **kwargs)

        self.add_border()

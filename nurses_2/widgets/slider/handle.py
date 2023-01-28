from ...colors import ColorPair
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class _Handle(GrabbableBehavior, Widget):
    """
    Vertical handle for horizontal slider.
    """
    def __init__(self, *, color):
        super().__init__(
            size=(1, 1),
            background_char=" ",
            background_color_pair=ColorPair.from_colors(color, color),
        )

    def on_add(self):
        super().on_add()

        slider = self.parent

        def update_size_pos():
            self.y = slider.height // 2
            self.x = x = round(slider.proportion * slider.fill_width)
            slider.colors[self.y, :x, :3] = slider.fill_color
            slider.colors[self.y, x:, :3] = slider.default_fg_color

        update_size_pos()
        self.subscribe(slider, "size", update_size_pos)
        self.subscribe(slider, "proportion", update_size_pos)

    def on_remove(self):
        self.unsubscribe(self.parent, "size")
        self.unsubscribe(self.parent, "proportion")

    def grab_update(self, mouse_event):
        _, x = self.to_local(mouse_event.position)
        dx = self.mouse_dx
        if dx > 0 and x < 0 or dx < 0 and x > 0:
            return

        slider = self.parent
        slider.proportion += dx / slider.fill_width

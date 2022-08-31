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

    def update_geometry(self):
        self.y = self.parent.height // 2
        self.update_handle()

    def update_handle(self):
        slider = self.parent
        self.x = x = round(slider.proportion * slider.fill_width)
        slider.colors[self.y, :x, :3] = slider.fill_color
        slider.colors[self.y, x:, :3] = slider.default_fg_color

    def grab_update(self, mouse_event):
        _, x = self.to_local(mouse_event.position)
        dx = self.mouse_dx
        if dx > 0 and x < 0 or dx < 0 and x > 0:
            return

        slider = self.parent
        slider.proportion += dx / slider.fill_width

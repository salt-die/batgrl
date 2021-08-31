from ...colors import BLACK, color_pair
from ...io import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class _Handle(GrabbableBehavior, Widget):
    """
    Vertical handle for horizontal slider.
    """
    def __init__(self, color):
        super().__init__(size=(1, 1), default_color_pair=color_pair(color, BLACK), default_char="█")

    def update_geometry(self):
        slider = self.parent
        self.left = round(slider.proportion * slider.fill_width)

    def grab_update(self, mouse_event):
        _, x = self.absolute_to_relative_coords(mouse_event.position)
        dx = self.mouse_dx
        if dx > 0 and x < 0 or dx < 0 and x > 0:
            return

        slider = self.parent
        slider.proportion += dx / slider.fill_width

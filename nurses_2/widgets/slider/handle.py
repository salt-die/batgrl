from ...colors import BLACK, color_pair
from ...mouse import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class _Handle(GrabbableBehavior, Widget):
    """
    Vertical handle for horizontal slider.
    """
    def __init__(self, color):
        super().__init__(dim=(1, 1), default_color_pair=color_pair(color, BLACK), default_char="█")

    def update_geometry(self):
        slider = self.parent
        self.left = round(slider.proportion * slider.fill_width)

    def grab_update(self, mouse_event):
        slider = self.parent
        slider.proportion += self.mouse_dx / slider.fill_width

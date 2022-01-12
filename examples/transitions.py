from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.widget_data_structures import Transition

IMAGE_DIR = Path("images")
PATH_TO_LOGO = IMAGE_DIR / "logo_solo_flat_256.png"

class MyApp(App):
    async def on_start(self):
        rect = Image(path=PATH_TO_LOGO, size=(10, 20))

        self.add_widget(rect)

        await rect.transition(pos=(20, 75), alpha=0.0, duration=2, transition_type=Transition.IN_CUBIC)

        await rect.transition(pos=(0, 0), alpha=1.0, duration=3, transition_type=Transition.OUT_BOUNCE)

        # Hints must not be `None` or transition will error.
        rect.size_hint = .1, .1
        rect.y_hint = 0

        await rect.transition(y_hint=1.0, size_hint=(1.0, 1.0), alpha=0.0, duration=4, transition_type=Transition.OUT_SINE)

        rect.size_hint = None, None
        rect.y_hint = None

        await rect.transition(y=0, x=0, height=10, width=20, alpha=1, duration=5, transition_type=Transition.IN_OUT_EXP)


MyApp().run()

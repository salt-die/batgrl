from nurses_2.app import App
from nurses_2.widgets.behaviors import AutoSizeBehavior

from .cloth import Cloth

MESH_SIZE = 10, 20


class AutoSizeCloth(AutoSizeBehavior, Cloth):
    ...


class ClothApp(App):
    async def on_start(self):
        cloth = AutoSizeCloth(mesh_size=MESH_SIZE)

        self.root.add_widget(cloth)

        await cloth.step_forever()



ClothApp().run()

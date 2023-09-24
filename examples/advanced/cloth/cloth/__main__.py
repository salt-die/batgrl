from nurses_2.app import App

from .cloth import Cloth

MESH_SIZE = 11, 21


class ClothApp(App):
    async def on_start(self):
        cloth = Cloth(mesh_size=MESH_SIZE, size_hint=(1.0, 1.0))

        self.add_widget(cloth)

        await cloth.step_forever()


if __name__ == "__main__":
    ClothApp(title="Cloth Simulation").run()

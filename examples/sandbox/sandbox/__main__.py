from nurses_2.app import App
from .sandbox import Sandbox


class SandboxApp(App):
    async def on_start(self):
        self.root.add_widget(Sandbox(size=(31, 100)))


SandboxApp().run()

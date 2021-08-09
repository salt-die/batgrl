from nurses_2.app import App
from nurses_2.widgets.behaviors import AutoPositionBehavior, AutoSizeBehavior, Anchor

from .rubiks_cube import RubiksCube


class AutoGeometryRubiksCube(AutoSizeBehavior, AutoPositionBehavior, RubiksCube):
    ...


# class RubiksApp(App):
#     async def on_start(self):
#         self.root.add_widget(
#             AutoGeometryRubiksCube(
#                 size_hint=(.75, .75),
#                 pos_hint=(.5, .5),
#                 anchor=Anchor.CENTER,
#             )
#         )


# RubiksApp().run()

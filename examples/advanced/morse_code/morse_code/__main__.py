# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "audioplayer",
# ]
# ///
import asyncio
from pathlib import Path
from time import perf_counter

import audioplayer
from batgrl.app import App
from batgrl.colors import GREEN, NEPTUNE_PRIMARY_FG
from batgrl.gadgets.button import Button
from batgrl.gadgets.progress_bar import ProgressBar
from batgrl.gadgets.text import Text, new_cell

from .diagrams import DIAGRAM, LINE_NOS, PARTIAL_PATHS
from .tree import TREE

ASSETS = Path(__file__).parent.parent.parent.parent / "assets"
SOUND_FILE = str((ASSETS / "440Hz_44100Hz_16bit_05sec.mp3").absolute())
MIN_DOT_DURATION = 0.15
MIN_DASH_DURATION = MIN_DOT_DURATION * 3
RESTART_DURATION = MIN_DASH_DURATION * 3


class MorseButton(Button):
    def __init__(
        self, press_event: asyncio.Event, release_event: asyncio.Event, **kwargs
    ):
        super().__init__(**kwargs)
        self._audio_player = audioplayer.AudioPlayer(SOUND_FILE)
        self._audio_player.play(block=False)
        self._audio_player.stop()

        self._press_event = press_event
        self._release_event = release_event

    def update_down(self):
        """Play sound when button is pressed."""
        super().update_down()
        self._audio_player.play(loop=True, block=False)
        self._press_event.set()

    def on_release(self):
        """Stop sound when button is released."""
        super().on_release()
        self._audio_player.stop()
        self._release_event.set()


class MorseCodeApp(App):
    async def on_start(self) -> None:
        diagram = Text(
            pos_hint={"x_hint": 0.5, "anchor": "center"},
            is_transparent=True,
            default_cell=new_cell(fg_color=NEPTUNE_PRIMARY_FG),
        )
        diagram.set_text(DIAGRAM)
        diagram_overlay = Text(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_transparent=True,
            default_cell=new_cell(fg_color=GREEN),
        )
        diagram.add_gadget(diagram_overlay)

        progress_label = Text(
            pos_hint={"x_hint": 0.5, "anchor": "center"},
            default_cell=new_cell(fg_color=NEPTUNE_PRIMARY_FG),
            size=(1, 16),
            is_transparent=True,
        )
        progress_bar = ProgressBar(
            animation_delay=0.01,
            pos_hint={"x_hint": 0.5, "anchor": "center"},
            size=(1, 16),
        )
        press_event = asyncio.Event()
        release_event = asyncio.Event()
        button = MorseButton(
            press_event=press_event,
            release_event=release_event,
            label="Press and Hold",
            always_release=True,
            size=(3, 16),
            pos_hint={"x_hint": 0.5, "anchor": "center"},
        )
        progress_label.top = diagram.bottom
        progress_bar.top = progress_label.bottom
        button.top = progress_bar.bottom + 1
        self.add_gadgets(diagram, progress_label, progress_bar, button)

        current_node = TREE
        while True:
            press_event.clear()
            release_event.clear()

            press_task = asyncio.create_task(press_event.wait())
            restart_task = asyncio.create_task(asyncio.sleep(RESTART_DURATION))

            wait_start = perf_counter()
            while not press_task.done():
                if restart_task and restart_task.done():
                    current_node = TREE
                    diagram_overlay.clear()
                    restart_task = None
                    progress_label.clear()
                    if progress_bar.progress is not None:
                        progress_bar.progress = None
                elif current_node.letter is not None:
                    duration = perf_counter() - wait_start
                    progress_label.set_text(
                        "Resetting in " f"{RESTART_DURATION - duration:.2f}" " seconds"
                    )
                    progress_bar.progress = duration / RESTART_DURATION
                await asyncio.sleep(0.0)

            press_start = perf_counter()
            progress_label.clear()
            while not release_event.is_set():
                duration = perf_counter() - press_start
                if duration > MIN_DASH_DURATION:
                    progress_label.set_text("—")
                elif duration > MIN_DOT_DURATION:
                    progress_label.set_text("○")
                progress_bar.progress = duration / MIN_DASH_DURATION
                await asyncio.sleep(0.0)

            duration = perf_counter() - press_start
            if duration > MIN_DASH_DURATION and current_node.dash is not None:
                current_node = current_node.dash
            elif (
                MIN_DASH_DURATION > duration > MIN_DOT_DURATION
                and current_node.dot is not None
            ):
                current_node = current_node.dot
            else:
                continue

            for i, line in enumerate(
                PARTIAL_PATHS[current_node.letter].splitlines(),
                start=LINE_NOS[current_node.letter],
            ):
                diagram_overlay.add_str(line, pos=(i, 0))


MorseCodeApp(inline=True, inline_height=20).run()

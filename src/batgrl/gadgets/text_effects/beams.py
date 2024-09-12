"""A beam effect."""

import asyncio
from collections.abc import Callable
from random import random, shuffle
from typing import Coroutine, Literal

import numpy as np
from numpy.typing import NDArray

from ...colors import WHITE, Color, gradient
from ..text import Text

HORIZONTAL_BEAM = "▁▁▁▁▁▁▁▁▂▂▂▂▂▂▂▂▃▃▃▃▃▃▃▃▄▄▄▄▄▄▄▄"
VERTICAL_BEAM = "▏\n▏\n▏\n▏\n▎\n▎\n▎\n▎\n▍\n▍\n▍\n▍\n▌\n▌\n▌\n▌"
BEAM_BLUE = Color.from_hex("00d1ff")
BEAM_PURP = Color.from_hex("8a008a")
HORIZONTAL_GRAD = gradient(BEAM_PURP, BEAM_BLUE, 16) + gradient(BEAM_BLUE, WHITE, 16)
VERTICAL_GRAD = gradient(BEAM_PURP, BEAM_BLUE, 8) + gradient(BEAM_BLUE, WHITE, 8)


async def beams_effect(text: Text):
    """
    Create a beams effect.

    Parameters
    ----------
    text : Text
        The text gadget which to run the effect.

    Warnings
    --------
    Modifying `text` size while effect is running will break the effect.
    """
    cover = Text(size=text.size)
    cover.canvas[:] = text.canvas
    cover.canvas["fg_color"] = cover.canvas["bg_color"]

    pass_count = np.zeros(text.size, int)
    beams, tweens = _create_beams(pass_count, cover)
    shuffle(tweens)

    cover.add_gadgets(beams)
    text.add_gadget(cover)

    tasks = [asyncio.create_task(_fade_cover(pass_count, cover, text))]
    for tween in tweens:
        tasks.append(asyncio.create_task(tween))
        await asyncio.sleep(0.1 * random())

    await asyncio.gather(*tasks)

    text.remove_gadget(cover)


def _create_on_progress(
    pass_count: NDArray[np.int32],
    cover: Text,
    beam: Text,
    kind: Literal["down", "left", "right", "up"],
) -> Callable[[], None]:
    if kind == "down":
        last_bottom = beam.bottom

        def on_progress(*args):
            nonlocal last_bottom
            if beam.bottom != last_bottom:
                pass_count[last_bottom + 1 : beam.bottom + 1, beam.x] += 1
                cover.canvas[last_bottom + 1 : beam.bottom + 1, beam.x]["fg_color"] = (
                    WHITE
                )
                last_bottom = beam.bottom

    elif kind == "left":
        last_left = beam.left

        def on_progress(*args):
            nonlocal last_left
            if beam.left != last_left:
                left = max(beam.left, 0)
                pass_count[beam.y, left:last_left] += 1
                cover.canvas[beam.y, left:last_left]["fg_color"] = WHITE
                last_left = beam.left

    elif kind == "right":
        last_right = beam.right

        def on_progress(*args):
            nonlocal last_right
            if beam.right != last_right:
                pass_count[beam.y, last_right + 1 : beam.right + 1] += 1
                cover.canvas[beam.y, last_right + 1 : beam.right + 1]["fg_color"] = (
                    WHITE
                )
                last_right = beam.right

    else:
        last_top = beam.top

        def on_progress(*args):
            nonlocal last_top
            if beam.top != last_top:
                top = max(beam.top, 0)
                pass_count[top:last_top, beam.x] += 1
                cover.canvas[top:last_top, beam.x]["fg_color"] = WHITE
                last_top = beam.top

    return on_progress


def _create_beams(
    pass_count: NDArray[np.int32], cover: Text
) -> tuple[list[Text], list[Coroutine]]:
    h, w = cover.size
    beams = []
    tweens = []
    for y in range(h):
        beam = Text(is_transparent=True)
        beam.y = y
        duration = 0.3 + random()
        if round(random()):
            beam.set_text(HORIZONTAL_BEAM)
            beam.canvas["fg_color"] = HORIZONTAL_GRAD
            beam.right = -1
            tween = beam.tween(
                duration=duration,
                on_progress=_create_on_progress(pass_count, cover, beam, "right"),
                left=w,
            )
        else:
            beam.set_text(HORIZONTAL_BEAM[::-1])
            beam.canvas["fg_color"] = HORIZONTAL_GRAD[::-1]
            beam.left = w
            tween = beam.tween(
                duration=duration,
                on_progress=_create_on_progress(pass_count, cover, beam, "left"),
                right=-1,
            )
        beams.append(beam)
        tweens.append(tween)

    for x in range(w):
        beam = Text(is_transparent=True)
        beam.x = x
        duration = 0.3 + random()
        if round(random()):
            beam.set_text(VERTICAL_BEAM)
            beam.canvas["fg_color"][:, 0] = VERTICAL_GRAD
            beam.bottom = -1
            tween = beam.tween(
                duration=duration,
                on_progress=_create_on_progress(pass_count, cover, beam, "down"),
                top=h,
            )
        else:
            beam.set_text(VERTICAL_BEAM[::-1])
            beam.canvas["fg_color"][:, 0] = VERTICAL_GRAD[::-1]
            beam.top = h
            tween = beam.tween(
                duration=duration,
                on_progress=_create_on_progress(pass_count, cover, beam, "up"),
                bottom=-1,
            )
        beams.append(beam)
        tweens.append(tween)
    return beams, tweens


async def _fade_cover(pass_count: NDArray[np.int32], cover: Text, text: Text):
    cover_fg = cover.canvas["fg_color"]
    text_fg = text.canvas["fg_color"].astype(float)
    while not np.array_equal(cover_fg, text_fg):
        passed_mask = pass_count >= 1
        faded = cover_fg * 0.99 + text_fg * 0.01
        cover_fg[passed_mask] = faded.astype(np.uint8)[passed_mask]
        await asyncio.sleep(0)

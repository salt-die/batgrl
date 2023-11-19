"""A markdown gadget."""
import asyncio
import re
import webbrowser
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from mistletoe import Document, block_token, span_token
from mistletoe.base_renderer import BaseRenderer
from pygments.lexers import get_lexer_by_name
from pygments.style import Style
from pygments.util import ClassNotFound

from ..colors import ColorPair, Neptune, lerp_colors
from ..emojis import EMOJIS
from ..geometry import Point, Size
from .behaviors.button_behavior import ButtonBehavior
from .behaviors.themable import Themable
from .gadget import Gadget
from .gadget_base import GadgetBase, PosHint, PosHintDict, SizeHint, SizeHintDict
from .graphics import Graphics
from .grid_layout import GridLayout
from .image import Image
from .scroll_view import ScrollView
from .text import Border, Text
from .video_player import VideoPlayer

__all__ = ["Markdown"]

TASK_LIST_ITEM_RE = re.compile(r" {,3}\[([xX ])\]\s+(.*)", re.DOTALL)
BULLETS = "●○◼◻▶▷◆◇"
MIN_MARKDOWN_WIDTH = 24
MIN_RENDER_WIDTH = 12
# How to scale images? Because of the lower resolution of a terminal vs a normal
# markdown viewer, small images can be drawn fairly large on the terminal. To prevent
# this, `_MarkdownImage` and `_MarkdownGif` approximate `PIXELS_PER_CHAR` pixels per
# half-width character.
PIXELS_PER_CHAR = 8

# TODO: Html blocks and spans
# TODO: Wrap Tables
# TODO: Use list prefix for render_width calculation.
# ? TODO: Download images / preview links


def _is_task_list_item(list_item: block_token.ListItem) -> re.Match | None:
    if list_item.leader != "-":
        return False
    # Match the first raw text item
    current_token = list_item
    while True:
        if isinstance(current_token, span_token.RawText):
            return TASK_LIST_ITEM_RE.match(current_token.content)
        if current_token.children:
            current_token = current_token.children[0]
        else:
            return None


class BlankLine(block_token.BlockToken):
    pattern = re.compile(r"\s*\n$")

    def __init__(self, _):
        self.children = []

    @classmethod
    def start(cls, line):
        return cls.pattern.match(line)

    @classmethod
    def read(cls, lines):
        return [next(lines)]


# Spaces are tokenized so that `_BatgrlRenderer.render_inner` wraps at words.
class Spaces(span_token.SpanToken):
    pattern = re.compile(r"\b( +)\b")


class EmojiCode(span_token.SpanToken):
    pattern = re.compile(r":([+-]?\w*):")

    def __init__(self, match_obj):
        self.content = EMOJIS.get(match_obj.group(1), match_obj.group(0))


class _BorderedContent(Text):
    def __init__(
        self,
        default_color_pair: ColorPair,
        border: Border,
        border_color_pair: ColorPair | None = None,
        padding: int = 0,
        content: Gadget | None = None,
    ):
        super().__init__(default_color_pair=default_color_pair)

        if content is None:
            self.content = Text(
                pos=(1 + padding, 1 + padding), default_color_pair=default_color_pair
            )
        else:
            self.content = content
            content.pos = 1 + padding, 1 + padding

        self.add_gadget(self.content)

        def update():
            h, w = self.content.size
            self.size = h + 2 * (padding + 1), w + 2 * (padding + 1)
            self.add_border(border, color_pair=border_color_pair or default_color_pair)

        self.subscribe(self.content, "size", update)
        update()


class _HasTitle:
    """Title hint behavior for links and images."""

    def __init__(self, title: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title

    def add_gadget(self, gadget):
        super().add_gadget(gadget)
        for child in self.walk():
            if isinstance(child, _HasTitle) and child.title:
                self.title = ""
                break

    def on_add(self):
        for ancestor in self.ancestors():
            if isinstance(ancestor, Markdown):
                self.link_hint = ancestor._link_hint
                self._hint_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
                break
        super().on_add()

    def on_mouse(self, mouse_event):
        if not self.title:
            return super().on_mouse(mouse_event)

        self._myx = mouse_event.position

        self._hint_task.cancel()
        if self.collides_point(mouse_event.position):
            self.link_hint.content.set_text(self.title)
            self._hint_task = asyncio.create_task(self.show_hint_soon())
        else:
            self.link_hint.is_enabled = False
        return super().on_mouse(mouse_event)

    async def show_hint_soon(self):
        await asyncio.sleep(1)
        y, x = self.link_hint.parent.to_local(self._myx)
        if y + 1 < self.link_hint.parent.height:
            self.link_hint.pos = y + 1, x
        else:
            self.link_hint.pos = y - 1, x
        self.link_hint.is_enabled = True


class _Link(_HasTitle, ButtonBehavior, GadgetBase):
    def __init__(self, title, target, content):
        super().__init__(title=title)
        self.target = target
        self.texts = []
        self.graphics = []
        self.add_gadget(content)
        for child in self.walk():
            if isinstance(child, Text):
                underline = child.canvas["underline"].copy()
                mask = np.all(child.colors == Themable.color_theme.primary, axis=-1)
                child.colors[mask] = Themable.color_theme.markdown_link
                self.texts.append((child, underline, mask))
            # ! This condition can add to the gadget-tree while walking it, careful.
            elif isinstance(child, (_MarkdownImage, _MarkdownGif)):
                if not hasattr(child, "outline"):
                    child.outline = Graphics(size=child.size, is_enabled=False)
                    child.outline.texture[[0, -1]] = (75,) * 4
                    child.outline.texture[:, [0, -1]] = (75,) * 4
                    child.add_gadget(child.outline)
                self.graphics.append(child)
        self.size = content.size

    def on_release(self):
        webbrowser.open(self.target)

    def update_normal(self):
        for text, underline, mask in self.texts:
            text.colors[mask] = Themable.color_theme.markdown_link
            text.canvas["underline"] = underline
        for graphic in self.graphics:
            graphic.outline.is_enabled = False

    def update_hover(self):
        for text, _, mask in self.texts:
            text.colors[mask] = Themable.color_theme.markdown_link_hover
            text.canvas["underline"] = True
        for graphic in self.graphics:
            graphic.outline.is_enabled = True


class _MarkdownImage(_HasTitle, Image):
    def __init__(self, title: str, path: Path, width: int):
        super().__init__(title=title, path=path)
        oh, ow, _ = self._otexture.shape
        width = min(ow / PIXELS_PER_CHAR, width)
        self.size = int(oh * width / ow) // 2, width


class _MarkdownGif(_HasTitle, VideoPlayer):
    def __init__(self, title: str, path: Path, width: int):
        super().__init__(title=title, source=path)
        oh = self._resource.get(cv2.CAP_PROP_FRAME_HEIGHT)
        ow = self._resource.get(cv2.CAP_PROP_FRAME_WIDTH)
        width = min(ow / PIXELS_PER_CHAR, width)
        self.size = int(oh * width / ow) // 2, width

    def on_add(self):
        super().on_add()
        self.play()

    def on_remove(self):
        self.stop()
        super().on_remove()


class _TextImage(_HasTitle, GadgetBase):
    def __init__(self, title, content):
        super().__init__(title=title)
        self.add_gadget(content)
        self.size = content.size


class _BlockCode(Text):
    def __init__(self):
        super().__init__(default_color_pair=Themable.color_theme.primary)


class _List(GridLayout):
    def __init__(self, items, prefix):
        super().__init__(
            grid_rows=len(items),
            grid_columns=2,
            horizontal_spacing=1,
            background_color_pair=Themable.color_theme.primary,
        )
        if isinstance(prefix, int):  # ordered list
            for i, item in enumerate(items, start=prefix):
                number = Text(default_color_pair=Themable.color_theme.primary)
                number.set_text(f"{i}.")
                self.add_gadgets(number, item)
        else:  # unordered list
            for item in items:
                bullet = Text(default_color_pair=Themable.color_theme.primary)
                bullet.set_text(getattr(item, "check", prefix))
                self.add_gadgets(bullet, item)

        self.size = self.minimum_grid_size


class _Quote(GridLayout):
    def __init__(self, content: Gadget, depth):
        super().__init__(grid_rows=1, grid_columns=2)
        margin = Text(
            default_char="▎",
            size=(content.height, 1),
            default_color_pair=Themable.color_theme.markdown_quote,
        )
        self.depth = depth
        self.background_color = lerp_colors(
            Themable.color_theme.markdown_quote.fg_color,
            Themable.color_theme.markdown_quote.bg_color,
            1 / (0.1 * depth + 1),
        )
        self.background_color_pair = (0, 0, 0, *self.background_color)
        self.add_gadgets(margin, content)
        self.color_content()

        self.size = self.minimum_grid_size

    def color_content(self):
        self.is_colored = True
        for child in self.walk():
            if hasattr(child, "is_colored"):
                continue

            child.is_colored = True
            if isinstance(child, _BlockCode):
                child.colors[
                    ..., 3:
                ] = Themable.color_theme.markdown_quote_block_code_background
            elif isinstance(child, Text):
                child.colors[..., 3:] = self.background_color
            elif isinstance(child, Gadget):
                child.background_color_pair = self.background_color_pair


class _BatgrlRenderer(BaseRenderer):
    list_depth: int = 0
    quote_depth: int = 0
    last_token: span_token.SpanToken | block_token.BlockToken | None = None

    def __init__(self, width, syntax_highlighting_style):
        super().__init__(BlankLine, Spaces, EmojiCode)
        block_token.remove_token(block_token.Footnote)
        self.width = max(width, MIN_MARKDOWN_WIDTH)
        self.syntax_highlighting_style = syntax_highlighting_style
        self.render_map["SetextHeading"] = self.render_setext_heading
        self.render_map["CodeFence"] = self.render_block_code

    @property
    def render_width(self):
        return max(
            self.width - 3 * self.list_depth - 2 * self.quote_depth, MIN_RENDER_WIDTH
        )

    def render(
        self, token: span_token.SpanToken | block_token.BlockToken
    ) -> GadgetBase:
        if isinstance(self.last_token, BlankLine) and isinstance(
            token, block_token.Paragraph
        ):
            self.last_rendered.skip_blank_line = True
        self.last_rendered = super().render(token)
        self.last_token = token
        return self.last_rendered

    def render_blank_line(self, token: BlankLine) -> GadgetBase:
        return GadgetBase(size=(1, 1), is_transparent=True)

    def render_spaces(self, token: Spaces) -> Literal[" "]:
        return " "

    def render_raw_text(self, token: span_token.RawText) -> Text:
        text = Text(default_color_pair=Themable.color_theme.primary)
        text.set_text(token.content)
        width = self.render_width
        if text.width > width:
            new_lines, line_end = divmod(text.width, width)
            text.height += new_lines
            for i in range(1, new_lines):
                text.canvas[i, :width] = text.canvas[0, i * width : (i + 1) * width]
            last_line = new_lines * width
            text.canvas[new_lines, :line_end] = text.canvas[
                0, last_line : last_line + line_end
            ]
            text.line_end = line_end
            text.width = width
        return text

    def render_emoji_code(self, token: EmojiCode) -> Text:
        return self.render_raw_text(token)

    def render_inner(self, token: span_token.SpanToken) -> Text:
        width = self.render_width
        text = Text(size=(1, 1), default_color_pair=Themable.color_theme.primary)
        current_line_end = 0
        current_line_height = 1
        current_line_gadgets = []
        for content in map(self.render, token.children):
            if content == "\n" or content == " " and current_line_end + 1 == text.width:
                text.height += 1
                current_line_end = 0
                current_line_height = 1
                current_line_gadgets = []
                continue

            if content == " ":
                current_line_end += 1
                continue

            new_line_end = current_line_end + content.width
            if new_line_end > text.width:
                if new_line_end <= width:
                    text.width = new_line_end
                else:
                    text.height += 1
                    new_line_end = content.width
                    if text.width < new_line_end:
                        text.width = new_line_end
                    current_line_end = 0
                    current_line_height = 1
                    current_line_gadgets = []

            if isinstance(content, Text):
                if content.height > 1:
                    text.height += content.height - 1

                text.canvas[
                    -content.height :, current_line_end:new_line_end
                ] = content.canvas
                text.colors[
                    -content.height :, current_line_end:new_line_end
                ] = content.colors
                current_line_end = getattr(content, "line_end", new_line_end)
                continue

            if content.height > current_line_height:
                height_dif = content.height - current_line_height
                current_line_height = content.height
                text.height += height_dif
                # Move text on current line down
                old_text = text.canvas[:-height_dif, :current_line_end]
                old_colors = text.colors[:-height_dif, :current_line_end]
                text.canvas[height_dif:, :current_line_end] = old_text
                text.colors[height_dif:, :current_line_end] = old_colors
                old_text[:] = text.default_char
                old_colors[:] = text.default_color_pair
                # Move links and images on current line down.
                for gadget in current_line_gadgets:
                    gadget.y += height_dif

            content.pos = text.height - content.height, current_line_end
            current_line_end = new_line_end
            current_line_gadgets.append(content)
            text.add_gadget(content)

        return text

    def render_strong(self, token: span_token.Strong) -> Text:
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["bold"] = True
            text.canvas[-1, : text.line_end]["bold"] = True
        else:
            text.canvas["bold"] = True
        return text

    def render_emphasis(self, token: span_token.Emphasis) -> Text:
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["italic"] = True
            text.canvas[-1, : text.line_end]["italic"] = True
        else:
            text.canvas["italic"] = True
        return text

    def render_strikethrough(self, token: span_token.Strikethrough) -> Text:
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["strikethrough"] = True
            text.canvas[-1, : text.line_end]["strikethrough"] = True
        else:
            text.canvas["strikethrough"] = True
        return text

    def render_inline_code(self, token: span_token.InlineCode) -> Text:
        text = self.render_raw_text(token.children[0])
        if text.height > 1:
            text.colors[:-1] = Themable.color_theme.markdown_inline_code
            text.colors[-1, : text.line_end] = Themable.color_theme.markdown_inline_code
        else:
            text.colors[:] = Themable.color_theme.markdown_inline_code
        return text

    def render_image(
        self, token: span_token.Image
    ) -> _MarkdownGif | _MarkdownImage | _TextImage:
        path = Path(token.src)
        if path.exists():
            if path.suffix == ".gif":
                return _MarkdownGif(
                    path=path, title=token.title, width=self.render_width
                )
            return _MarkdownImage(path=path, title=token.title, width=self.render_width)
        token.children.insert(0, span_token.RawText("🖼️ "))
        content = self.render_inner(token)
        content.colors[:] = Themable.color_theme.markdown_image
        return _TextImage(title=token.title, content=content)

    def render_link(self, token: span_token.Link) -> _Link:
        line = _Link(
            target=token.target, title=token.title, content=self.render_inner(token)
        )
        return line

    def render_auto_link(self, token: span_token.AutoLink) -> _Link:
        target = f"mailto:{token.target}" if token.mailto else token.target
        return _Link(
            target=target, title=token.target, content=self.render_inner(token)
        )

    def render_escape_sequence(self, token: span_token.EscapeSequence) -> Text:
        text = Text(default_color_pair=Themable.color_theme.primary)
        text.set_text(f"\\{token.children[0].content}")
        return text

    def render_heading(self, token: block_token.Heading) -> Text:
        text = self.render_inner(token)
        text.colors[..., 3:] = Themable.color_theme.markdown_header_background
        if token.level % 2 == 1:
            text.canvas["bold"] = True

        if token.level < 5:
            default_color_pair = ColorPair.from_colors(
                Themable.color_theme.primary.fg_color,
                Themable.color_theme.markdown_header_background,
            )
            return _BorderedContent(
                default_color_pair=default_color_pair,
                border_color_pair=Themable.color_theme.primary,
                border="mcgugan_wide",
                padding=int(token.level < 3),
                content=text,
            )
        text.colors[..., 3:] = Themable.color_theme.markdown_header_background
        text.height += 1
        text.canvas["char"][-1] = "▔"
        return text

    def render_setext_heading(self, token: block_token.SetextHeading) -> Text:
        text = self.render_inner(token)
        if token.level == 1:
            text.canvas["bold"] = True
        text.height += 1
        text.width = max(text.width, self.render_width)
        text.canvas["char"][-1, :] = "━" if token.level == 1 else "─"
        return text

    def render_quote(self, token: block_token.Quote) -> _Quote:
        self.quote_depth += 1
        items = list(map(self.render, token.children))
        self.quote_depth -= 1

        if len(items) == 1:
            quote = _Quote(items[0], self.quote_depth)
            quote.width = max(quote.width, self.render_width)
            return quote

        grid = GridLayout(grid_rows=len(items))
        grid.add_gadgets(items)
        grid.size = grid.minimum_grid_size
        quote = _Quote(grid, self.quote_depth)
        quote.width = max(quote.width, self.render_width)
        return quote

    def render_paragraph(self, token: block_token.Paragraph) -> Text:
        return self.render_inner(token)

    def render_block_code(
        self, token: block_token.BlockCode | block_token.CodeFence
    ) -> _BlockCode:
        text = _BlockCode()
        text.set_text(token.content.rstrip())
        text.width = max(text.width, self.render_width)
        try:
            lexer = get_lexer_by_name(token.language)
        except ClassNotFound:
            lexer = None
        text.add_syntax_highlighting(lexer=lexer, style=self.syntax_highlighting_style)
        text.colors[..., 3:] = Themable.color_theme.markdown_block_code_background
        return text

    def render_list(self, token: block_token.List) -> _List:
        prefix = (
            BULLETS[self.list_depth % len(BULLETS)]
            if token.start is None
            else token.start
        )

        self.list_depth += 1
        checks = list(map(_is_task_list_item, token.children))
        if all(checks):
            items = [
                self.render_task_list_item(child, match)
                for child, match in zip(token.children, checks)
            ]
        else:
            items = [self.render_list_item(child) for child in token.children]
        self.list_depth -= 1
        return _List(items, prefix)

    def render_task_list_item(
        self, token: block_token.ListItem, match: re.Match
    ) -> Gadget:
        current_token = token
        while True:
            if isinstance(current_token, span_token.RawText):
                current_token.content = match[2]
                list_item = self.render_list_item(token)
                list_item.check = "🟩" if match[1] == " " else "❎"
                return list_item
            current_token = current_token.children[0]

    def render_list_item(self, token: block_token.ListItem) -> Gadget:
        blocks = list(map(self.render, token.children))

        if len(blocks) == 1:
            return blocks[0]
        list_item = GridLayout(
            grid_columns=1,
            grid_rows=len(blocks),
            background_color_pair=Themable.color_theme.primary,
        )
        list_item.add_gadgets(blocks)
        list_item.size = list_item.minimum_grid_size
        return list_item

    def render_table(self, token: block_token.Table) -> Text:
        header = token.header.children if hasattr(token, "header") else []
        rows = [header, *(row.children for row in token.children)]
        rendered_rows = [[self.render_inner(cell) for cell in row] for row in rows]

        MIN_COLUMN_WIDTH = 3
        row_heights = []
        column_widths = [MIN_COLUMN_WIDTH] * len(header)
        alignments = token.column_align.copy()
        for row in rendered_rows:
            row_height = 1
            column_widths.extend([MIN_COLUMN_WIDTH] * (len(row) - len(column_widths)))
            alignments.extend([None] * (len(row) - len(alignments)))
            for i, cell in enumerate(row):
                if cell.width > column_widths[i]:
                    column_widths[i] = cell.width
                if cell.height > row_height:
                    row_height = cell.height
            row_heights.append(row_height)

        for row, row_height in zip(rendered_rows, row_heights):
            for cell, column_width, alignment in zip(row, column_widths, alignments):
                if cell.height < row_height:
                    cell.height = row_height

                if column_width == cell.width:
                    continue

                diff = column_width - cell.width
                cell.width += diff
                if alignment == 0:  # centered
                    offset_left = diff // 2
                    offset_right = diff - offset_left
                    cell.canvas[:, offset_left:-offset_right] = cell.canvas[:, :-diff]
                    cell.colors[:, offset_left:-offset_right] = cell.colors[:, :-diff]
                    cell.canvas[:, :offset_left] = cell.default_char
                    cell.colors[:, :offset_left] = cell.default_color_pair
                elif alignment == 1:  # right-aligned
                    cell.canvas[:, diff:] = cell.canvas[:, :-diff]
                    cell.colors[:, diff:] = cell.colors[:, :-diff]
                    cell.canvas[:, :diff] = cell.default_char
                    cell.colors[:, :diff] = cell.default_color_pair

        OUTER_PAD = 1
        INNER_PAD = 2
        table = Text(
            size=(
                sum(row_heights) + len(rows) - 1,
                sum(column_widths)
                + OUTER_PAD * 2
                + INNER_PAD * (len(column_widths) - 1),
            ),
            default_color_pair=Themable.color_theme.primary,
        )
        y = 0
        for i, row in enumerate(rendered_rows):
            x = OUTER_PAD
            for cell in row:
                h, w = cell.size
                table.canvas[y : y + h, x : x + w] = cell.canvas
                table.colors[y : y + h, x : x + w] = cell.colors
                children = cell.children.copy()
                for child in children:
                    cell.remove_gadget(child)
                    cy, cx = child.pos
                    child.pos = cy + y, cx + x
                    table.add_gadgets(child)
                x += w + INNER_PAD
            y += h
            if i == 0:
                table.canvas["bold"][:y] = True
                table.canvas["char"][y] = "━"
            elif i < len(rows) - 1:
                table.canvas["char"][y] = "─"
            y += 1

        return table

    def render_thematic_break(self, token: block_token.ThematicBreak) -> Text:
        return Text(
            size=(1, self.render_width),
            default_char="─",
            default_color_pair=Themable.color_theme.primary,
        )

    def render_line_break(self, token: span_token.LineBreak) -> Literal[" ", "\n"]:
        return " " if token.soft else "\n"

    def render_document(self, token: block_token.Document) -> GridLayout:
        # All blocks need to be rendered before skipped blank lines can be determined.
        rendered = [self.render(child) for child in token.children]
        blocks = [block for block in rendered if not hasattr(block, "skip_blank_line")]
        grid = GridLayout(
            grid_rows=len(blocks), background_color_pair=Themable.color_theme.primary
        )
        grid.add_gadgets(blocks)
        grid.size = grid.minimum_grid_size
        grid.footnotes = token.footnotes
        return grid


class Markdown(Themable, Gadget):
    r"""
    A markdown gadget.

    Parameters
    ----------
    background_char : NDArray[Char] | str | None, default: None
        The background character of the gadget. If not given and not transparent, the
        background characters of the root gadget are painted. If not given and
        transparent, characters behind the gadget are visible. The character must be
        single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget. If not given and not transparent, the
        background color pair of the root gadget is painted. If not given and
        transparent, the color pairs behind the gadget are visible.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    markdown : str
        The markdown string.
    syntax_highlighting_style : pygments.style.Style
        The syntax highlighting style for code blocks.
    background_char : NDArray[Char] | None
        The background character of the gadget.
    background_color_pair : ColorPair | None
        The background color pair of the gadget.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    update_theme():
        Paint the gadget with current theme.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        markdown: str,
        syntax_highlighting_style: Style = Neptune,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._scroll_view = ScrollView(
            size_hint={
                "height_hint": 1.0,
                "width_hint": 1.0,
                "min_width": MIN_MARKDOWN_WIDTH,
            },
            show_horizontal_bar=False,
            disable_ptf=True,
        )
        self._link_hint = _BorderedContent(
            default_color_pair=Themable.color_theme.markdown_title, border="outer"
        )
        self._link_hint.is_enabled = False
        self.add_gadgets(self._scroll_view, self._link_hint)
        self.markdown = markdown
        self.syntax_highlighting_style = syntax_highlighting_style
        """The syntax highlighting style for code blocks."""

    @property
    def markdown(self) -> str:
        """The markdown string."""
        return self._markdown

    @markdown.setter
    def markdown(self, markdown: str):
        self._markdown = markdown
        self._build_markdown()

    def _build_markdown(self):
        if not self.root:
            return

        with _BatgrlRenderer(
            self._scroll_view.port_width, self.syntax_highlighting_style
        ) as renderer:
            rendered = renderer.render(Document(self.markdown))

        self._scroll_view.view = rendered
        self._scroll_view.show_horizontal_bar = rendered.width > self.width

    def update_theme(self):
        """Paint the gadget with current theme."""
        self.background_color_pair = self.color_theme.primary
        self._link_hint.default_color_pair = Themable.color_theme.markdown_title
        self._link_hint.content.default_color_pair = Themable.color_theme.markdown_title
        self._link_hint.colors[:] = Themable.color_theme.markdown_title
        self._link_hint.content.colors[:] = Themable.color_theme.markdown_title
        self._build_markdown()

    def on_size(self):
        """Rebuild markdown on resize."""
        self._build_markdown()

    def on_add(self):
        """Build markdown on add."""
        super().on_add()
        self._build_markdown()

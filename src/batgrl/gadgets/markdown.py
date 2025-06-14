"""A markdown gadget."""

import asyncio
import re
import webbrowser
from pathlib import Path
from typing import Literal, cast

import cv2
import numpy as np
from mistletoe import Document, block_token, span_token
from mistletoe.base_renderer import BaseRenderer
from pygments.lexers import get_lexer_by_name
from pygments.style import Style as PygmentsStyle
from pygments.util import ClassNotFound

from ..colors import Neptune, lerp_colors
from ..emojis import EMOJIS
from ..geometry import Point, Size
from ..text_tools import Style
from .behaviors import Behavior
from .behaviors.button_behavior import ButtonBehavior
from .behaviors.themable import Themable
from .gadget import Gadget, Pointlike, PosHint, SizeHint, Sizelike
from .graphics import _BLITTER_GEOMETRY, Blitter, Graphics
from .grid_layout import GridLayout
from .image import Image
from .pane import Pane
from .scroll_view import ScrollView
from .text import Border, Cell0D, Text, new_cell
from .video import Video

__all__ = ["Markdown", "Point", "Size"]

_TASK_LIST_ITEM_RE = re.compile(r" {,3}\[([xX ])\]\s+(.*)", re.DOTALL)
_BULLETS = "●○◼◻▶▷◆◇"
_MIN_MARKDOWN_WIDTH = 24
_MIN_RENDER_WIDTH = 12

# TODO: Html blocks and spans
# TODO: Wrap Tables
# TODO: Use list prefix for render_width calculation.


def _image_size(texture_h: float, texture_w: float, max_width: float) -> Size:
    """
    Use terminal pixel geometry to scale images.

    If markdown gadgets are created before the terminal pixel geometry has been queried
    then images are scaled by the default pixel geometry of `Size(20, 10)`.
    """
    pixels_per_h, pixels_per_w = _BLITTER_GEOMETRY["sixel"]
    h = int(texture_h / pixels_per_h)
    w = int(texture_w / pixels_per_w)
    if w <= max_width:
        return Size(h, w)

    pct = max_width / w
    return Size(int(h * pct), int(w * pct))


def _is_task_list_item(list_item: block_token.ListItem) -> re.Match | None:
    if list_item.leader != "-":
        return None
    # Match the first raw text item
    current_token = list_item
    while True:
        if isinstance(current_token, span_token.RawText):
            return _TASK_LIST_ITEM_RE.match(current_token.content)
        if current_token.children:
            current_token = current_token.children[0]
        else:
            return None


def _default_cell():
    return new_cell(
        fg_color=Themable.get_color("primary_fg"),
        bg_color=Themable.get_color("primary_bg"),
    )


class BlankLine(block_token.BlockToken):
    pattern = re.compile(r"\s*\n$")

    def __init__(self, _):
        self.children = []

    @classmethod
    def start(cls, line):
        return cls.pattern.match(line)

    @staticmethod
    def read(lines):
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
        default_cell: Cell0D,
        border: Border,
        padding: int = 0,
        content: Gadget | None = None,
        bind: bool = False,
    ):
        super().__init__(default_cell=default_cell)

        if content is None:
            self.content = Text(
                pos=(1 + padding, 1 + padding), default_cell=default_cell
            )
        else:
            self.content = content
            content.pos = 1 + padding, 1 + padding

        self.add_gadget(self.content)

        def update():
            h, w = self.content.size
            self.size = h + 2 * (padding + 1), w + 2 * (padding + 1)
            self.add_border(border)

        update()
        if bind:
            self.content.bind("size", update)


class _HasTitle(Behavior):
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

        self._myx = mouse_event.pos

        self._hint_task.cancel()
        if self.collides_point(mouse_event.pos):
            cast(Text, self.link_hint.content).set_text(self.title)
            self._hint_task = asyncio.create_task(self.show_hint_soon())
        else:
            self.link_hint.is_enabled = False
        return super().on_mouse(mouse_event)

    async def show_hint_soon(self):
        await asyncio.sleep(1)
        parent = cast(Gadget, self.link_hint.parent)
        y, x = parent.to_local(self._myx)
        if y + 1 < parent.height:
            self.link_hint.pos = y + 1, x
        else:
            self.link_hint.pos = y - 1, x
        self.link_hint.is_enabled = True


class _Link(_HasTitle, ButtonBehavior, Gadget):
    def __init__(self, title, target, content):
        super().__init__(title=title)
        self.target = target
        self.texts = []
        self.graphics = []
        self.add_gadget(content)

        for child in self.walk():
            if isinstance(child, Text):
                style = child.canvas["style"].copy()
                colors = child.canvas[["fg_color", "bg_color"]]
                primary_fg = Themable.get_color("primary_fg")
                primary_bg = Themable.get_color("primary_bg")
                mask = colors == np.array((primary_fg, primary_bg), colors.dtype)
                colors[mask] = (
                    Themable.get_color("markdown_link_fg"),
                    Themable.get_color("markdown_link_bg"),
                )
                self.texts.append((child, style, mask))
            # ! This condition can add to the gadget tree while walking it, careful.
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
        link_fg = Themable.get_color("markdown_link_fg")
        link_bg = Themable.get_color("markdown_link_bg")
        for text, style, mask in self.texts:
            text.canvas["fg_color"][mask] = link_fg
            text.canvas["bg_color"][mask] = link_bg
            text.canvas["style"] = style
        for graphic in self.graphics:
            graphic.outline.is_enabled = False

    def update_hover(self):
        hover_fg = Themable.get_color("markdown_link_hover_fg")
        hover_bg = Themable.get_color("markdown_link_hover_bg")
        for text, _, mask in self.texts:
            text.canvas["fg_color"][mask] = hover_fg
            text.canvas["bg_color"][mask] = hover_bg
            text.canvas["style"] |= Style.UNDERLINE
        for graphic in self.graphics:
            graphic.outline.is_enabled = True


class _MarkdownImage(_HasTitle, Image):
    outline: Graphics

    def __init__(self, title: str, path: Path, width: int, blitter: Blitter):
        oh, ow, _ = self._otexture.shape
        size = _image_size(oh, ow, width)
        super().__init__(title=title, path=path, blitter=blitter, size=size)


class _MarkdownGif(_HasTitle, Video):
    outline: Graphics

    def __init__(self, title: str, path: Path, width: int, blitter: Blitter):
        super().__init__(title=title, source=path, blitter=blitter)
        if self._resource is not None:
            oh = self._resource.get(cv2.CAP_PROP_FRAME_HEIGHT)
            ow = self._resource.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.size = _image_size(oh, ow, width)

    def on_add(self):
        super().on_add()
        self.play()

    def on_remove(self):
        self.stop()
        super().on_remove()


class _TextImage(_HasTitle, Gadget):
    def __init__(self, title, content):
        super().__init__(title=title)
        self.add_gadget(content)
        self.size = content.size


class _BlockCode(Text):
    def __init__(self):
        super().__init__(default_cell=_default_cell())


class _List(GridLayout):
    def __init__(self, items, prefix: str | int):
        super().__init__(
            grid_rows=len(items),
            grid_columns=2,
            horizontal_spacing=1,
            is_transparent=True,
        )
        if isinstance(prefix, int):  # ordered list
            for i, item in enumerate(items, start=prefix):
                number = Text(default_cell=_default_cell())
                number.set_text(f"{i}.")
                self.add_gadgets(number, item)
        else:  # unordered list
            for item in items:
                bullet = Text(default_cell=_default_cell())
                bullet.set_text(getattr(item, "check", prefix))
                self.add_gadgets(bullet, item)

        self.size = self.min_grid_size


class _Quote(Pane):
    def __init__(self, content: Gadget, depth):
        super().__init__()
        quote_fg = Themable.get_color("markdown_quote_fg")
        quote_bg = Themable.get_color("markdown_quote_bg")
        margin = Text(
            default_cell=new_cell(ord=ord("▎"), fg_color=quote_fg, bg_color=quote_bg),
            size=(content.height, 1),
        )
        self.depth = depth
        self.bg_color = lerp_colors(quote_fg, quote_bg, 1 / (0.1 * depth + 1))
        self.grid = GridLayout(grid_rows=1, grid_columns=2, is_transparent=True)
        self.grid.add_gadgets(margin, content)
        self.add_gadget(self.grid)
        self.size = self.grid.size = self.grid.min_grid_size
        self.color_content()

    def color_content(self):
        self._is_quote_colored = True
        for child in self.walk():
            if hasattr(child, "_is_quote_colored"):
                continue

            child._is_quote_colored = True  # type: ignore
            if isinstance(child, _BlockCode):
                child.canvas["bg_color"] = Themable.get_color(
                    "markdown_quote_block_code_bg"
                )
            elif isinstance(child, Text):
                child.canvas["bg_color"] = self.bg_color
            elif isinstance(child, Pane):
                child.bg_color = self.bg_color


class _MarkdownText(Text):
    line_end: int


class _BatgrlRenderer(BaseRenderer):
    list_depth: int = 0
    quote_depth: int = 0
    last_token: span_token.SpanToken | block_token.BlockToken | None = None

    def __init__(self, width, syntax_highlighting_style: type[PygmentsStyle], blitter):
        super().__init__(BlankLine, Spaces, EmojiCode)
        block_token.remove_token(block_token.Footnote)
        self.width = max(width, _MIN_MARKDOWN_WIDTH)
        self.syntax_highlighting_style: type[PygmentsStyle] = syntax_highlighting_style
        self.blitter = blitter
        self.render_map["SetextHeading"] = self.render_setext_heading
        self.render_map["CodeFence"] = self.render_block_code

    @property
    def render_width(self):
        return max(
            self.width - 3 * self.list_depth - 2 * self.quote_depth, _MIN_RENDER_WIDTH
        )

    def render(self, token: span_token.SpanToken | block_token.BlockToken) -> Gadget:
        if isinstance(self.last_token, BlankLine) and isinstance(
            token, block_token.Paragraph
        ):
            self.last_rendered.skip_blank_line = True
        self.last_rendered = super().render(token)
        self.last_token = token
        return self.last_rendered

    def render_blank_line(self, token: BlankLine) -> Gadget:
        return Gadget(size=(1, 1), is_transparent=True)

    def render_spaces(self, token: Spaces) -> Literal[" "]:
        return " "

    def render_raw_text(  # type: ignore
        self, token: span_token.RawText | EmojiCode
    ) -> _MarkdownText:
        text = _MarkdownText(default_cell=_default_cell())
        text.set_text(cast(str, token.content))
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

    def render_emoji_code(self, token: EmojiCode) -> _MarkdownText:
        return self.render_raw_text(token)

    def render_inner(  # type: ignore
        self, token: span_token.SpanToken | block_token.BlockToken
    ) -> _MarkdownText:
        width = self.render_width
        text = _MarkdownText(size=(1, 1), default_cell=_default_cell())
        current_line_end = 0
        current_line_height = 1
        current_line_gadgets = []
        for content in map(self.render, token.children):  # type: ignore
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

                text.canvas[-content.height :, current_line_end:new_line_end] = (
                    content.canvas
                )
                current_line_end = getattr(content, "line_end", new_line_end)
                continue

            if content.height > current_line_height:
                height_dif = content.height - current_line_height
                current_line_height = content.height
                text.height += height_dif
                # Move text on current line down
                old = text.canvas[:-height_dif, :current_line_end]
                text.canvas[height_dif:, :current_line_end] = old
                old[:] = text.default_cell
                # Move links and images on current line down.
                for gadget in current_line_gadgets:
                    gadget.y += height_dif

            content.pos = text.height - content.height, current_line_end
            current_line_end = new_line_end
            current_line_gadgets.append(content)
            text.add_gadget(content)

        return text

    def render_strong(self, token: span_token.Strong) -> _MarkdownText:  # type: ignore
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["style"] |= Style.BOLD
            text.canvas[-1, : text.line_end]["style"] |= Style.BOLD
        else:
            text.canvas["style"] |= Style.BOLD
        return text

    def render_emphasis(  # type: ignore
        self, token: span_token.Emphasis
    ) -> _MarkdownText:
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["style"] |= Style.ITALIC
            text.canvas[-1, : text.line_end]["style"] |= Style.ITALIC
        else:
            text.canvas["style"] |= Style.ITALIC
        return text

    def render_strikethrough(  # type: ignore
        self, token: span_token.Strikethrough
    ) -> _MarkdownText:
        text = self.render_inner(token)
        if text.height > 1:
            text.canvas[:-1]["style"] = Style.STRIKETHROUGH
            text.canvas[-1, : text.line_end]["style"] = Style.STRIKETHROUGH
        else:
            text.canvas["style"] = Style.STRIKETHROUGH
        return text

    def render_inline_code(  # type: ignore
        self, token: span_token.InlineCode
    ) -> _MarkdownText:
        text = self.render_raw_text(token.children[0])
        inline_fg = Themable.get_color("markdown_inline_code_fg")
        inline_bg = Themable.get_color("markdown_inline_code_bg")
        if text.height > 1:
            text.canvas["fg_color"][:-1] = inline_fg
            text.canvas["bg_color"][:-1] = inline_bg
            text.canvas["fg_color"][-1, : text.line_end] = inline_fg
            text.canvas["bg_color"][-1, : text.line_end] = inline_bg
        else:
            text.canvas["fg_color"] = inline_fg
            text.canvas["bg_color"] = inline_bg
        return text

    def render_image(  # type: ignore
        self, token: span_token.Image
    ) -> _MarkdownGif | _MarkdownImage | _TextImage:
        path = Path(token.src)
        if path.exists():
            if path.suffix == ".gif":
                return _MarkdownGif(
                    path=path,
                    title=token.title,
                    width=self.render_width,
                    blitter=self.blitter,
                )
            return _MarkdownImage(
                path=path,
                title=token.title,
                width=self.render_width,
                blitter=self.blitter,
            )
        token.children.insert(0, span_token.RawText("🖼️  "))  # type: ignore
        content = self.render_inner(token)
        content.canvas["fg_color"] = Themable.get_color("markdown_image_fg")
        content.canvas["bg_color"] = Themable.get_color("markdown_image_bg")
        return _TextImage(title=token.title, content=content)

    def render_link(self, token: span_token.Link) -> _Link:  # type: ignore
        line = _Link(
            target=token.target, title=token.title, content=self.render_inner(token)
        )
        return line

    def render_auto_link(self, token: span_token.AutoLink) -> _Link:  # type: ignore
        target = f"mailto:{token.target}" if token.mailto else token.target
        return _Link(
            target=target, title=token.target, content=self.render_inner(token)
        )

    def render_escape_sequence(  # type: ignore
        self, token: span_token.EscapeSequence
    ) -> _MarkdownText:
        text = _MarkdownText(default_cell=_default_cell())
        text.set_text(f"\\{token.children[0].content}")
        return text

    def render_heading(  # type: ignore
        self, token: block_token.Heading
    ) -> _MarkdownText | _BorderedContent:
        text = self.render_inner(token)
        if token.level % 2 == 1:
            text.canvas["style"] |= Style.BOLD
        if token.level < 5:
            primary_fg = Themable.get_color("primary_fg")
            primary_bg = Themable.get_color("primary_bg")
            header_bg = Themable.get_color("markdown_header_bg")
            text.canvas["bg_color"] = header_bg
            header = _BorderedContent(
                default_cell=new_cell(fg_color=primary_fg, bg_color=header_bg),
                border="mcgugan_wide",
                padding=int(token.level < 3),
                content=text,
            )
            header.canvas["bg_color"][[0, -1]] = primary_bg
            return header
        text.height += 1
        text.chars[-1] = "▔"
        return text

    def render_setext_heading(self, token: block_token.SetextHeading) -> _MarkdownText:
        text = self.render_inner(token)
        if token.level == 1:
            text.canvas["style"] |= Style.BOLD
        text.height += 1
        text.width = max(text.width, self.render_width)
        text.chars[-1, :] = "━" if token.level == 1 else "─"
        return text

    def render_quote(self, token: block_token.Quote) -> _Quote:  # type: ignore
        self.quote_depth += 1
        items = list(map(self.render, token.children))
        self.quote_depth -= 1

        if len(items) == 1:
            quote = _Quote(items[0], self.quote_depth)
        else:
            grid = GridLayout(grid_rows=len(items), is_transparent=True)
            grid.add_gadgets(items)
            grid.size = grid.min_grid_size
            quote = _Quote(grid, self.quote_depth)

        quote.width = max(quote.width, self.render_width)
        return quote

    def render_paragraph(self, token: block_token.Paragraph) -> Text:  # type: ignore
        return self.render_inner(token)

    def render_block_code(  # type: ignore
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
        text.canvas["bg_color"] = Themable.get_color("markdown_block_code_bg")
        return text

    def render_list(self, token: block_token.List) -> _List:  # type: ignore
        prefix: str | int
        if token.start is None:
            nbullets = len(_BULLETS)
            prefix = _BULLETS[self.list_depth % nbullets]
        else:
            prefix = cast(int, token.start)

        self.list_depth += 1
        checks = list(map(_is_task_list_item, token.children))
        if all(checks):
            items = [
                self.render_task_list_item(child, cast(re.Match, match))
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
                list_item.check = "🟩" if match[1] == " " else "❎"  # type: ignore
                return list_item
            current_token = current_token.children[0]

    def render_list_item(self, token: block_token.ListItem) -> Gadget:  # type: ignore
        blocks = list(map(self.render, token.children))

        if len(blocks) == 1:
            return blocks[0]
        list_item = GridLayout(
            grid_columns=1, grid_rows=len(blocks), is_transparent=True
        )
        list_item.add_gadgets(blocks)
        list_item.size = list_item.min_grid_size
        return list_item

    def render_table(self, token: block_token.Table) -> _MarkdownText:  # type: ignore
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
                    cell.canvas[:, :offset_left] = cell.default_cell
                elif alignment == 1:  # right-aligned
                    cell.canvas[:, diff:] = cell.canvas[:, :-diff]
                    cell.canvas[:, :diff] = cell.default_cell

        OUTER_PAD = 1
        INNER_PAD = 2
        table = _MarkdownText(
            size=(
                sum(row_heights) + len(rows) - 1,
                sum(column_widths)
                + OUTER_PAD * 2
                + INNER_PAD * (len(column_widths) - 1),
            ),
            default_cell=_default_cell(),
        )
        y = h = 0
        for i, row in enumerate(rendered_rows):
            x = OUTER_PAD
            for cell in row:
                h, w = cell.size
                table.canvas[y : y + h, x : x + w] = cell.canvas
                children = cell.children.copy()
                for child in children:
                    cell.remove_gadget(child)
                    cy, cx = child.pos
                    child.pos = cy + y, cx + x
                    table.add_gadget(child)
                x += w + INNER_PAD
            y += h
            if i == 0:
                table.canvas["style"][:y] |= Style.BOLD
                table.chars[y] = "━"
            elif i < len(rows) - 1:
                table.chars[y] = "─"
            y += 1

        return table

    def render_thematic_break(  # type: ignore
        self, token: block_token.ThematicBreak
    ) -> _MarkdownText:
        cell = _default_cell()
        cell["ord"] = ord("─")
        return _MarkdownText(size=(1, self.render_width), default_cell=cell)

    def render_line_break(self, token: span_token.LineBreak) -> Literal[" ", "\n"]:
        return " " if token.soft else "\n"

    def render_document(  # type: ignore
        self, token: block_token.Document
    ) -> GridLayout:
        # All blocks need to be rendered before skipped blank lines can be determined.
        rendered = [self.render(child) for child in token.children]
        blocks = [block for block in rendered if not hasattr(block, "skip_blank_line")]
        grid = GridLayout(grid_rows=len(blocks), is_transparent=True)
        grid.add_gadgets(blocks)
        grid.size = grid.min_grid_size
        grid.footnotes = token.footnotes  # type: ignore
        return grid


class Markdown(Themable, Gadget):
    r"""
    A markdown gadget.

    Parameters
    ----------
    markdown : str
        The markdown string.
    syntax_highlighting_style : type[pygments.style.Style], default: Neptune
        The syntax highlighting style for code blocks.
    blitter : Blitter, default: "half"
        Determines how images are rendered.
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
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
    syntax_highlighting_style : type[pygments.style.Style]
        The syntax highlighting style for code blocks.
    blitter : Blitter, default: "half"
        Determines how images are rendered.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App | None
        The running app.

    Methods
    -------
    get_color(color_name)
        Get a color by name from the current color theme.
    update_theme()
        Paint the gadget with current theme.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(gadget_it, \*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        markdown: str,
        syntax_highlighting_style: type[PygmentsStyle] = Neptune,
        blitter: Blitter = "half",
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
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
                "min_width": _MIN_MARKDOWN_WIDTH,
            },
            dynamic_bars=True,
        )
        title_fg = Themable.get_color("markdown_title_fg")
        title_bg = Themable.get_color("markdown_title_bg")
        self._link_hint = _BorderedContent(
            default_cell=new_cell(fg_color=title_fg, bg_color=title_bg),
            border="outer",
            bind=True,
        )
        self._link_hint.is_enabled = False
        self.add_gadgets(self._scroll_view, self._link_hint)
        self.markdown = markdown
        self.syntax_highlighting_style = syntax_highlighting_style
        """The syntax highlighting style for code blocks."""
        self._blitter: Blitter
        self.blitter = blitter
        """Determines how images are rendered."""

    @property
    def markdown(self) -> str:
        """The markdown string."""
        return self._markdown

    @markdown.setter
    def markdown(self, markdown: str):
        self._markdown = markdown
        self._build_markdown()

    @property
    def syntax_highlighting_style(self) -> type[PygmentsStyle]:
        """The syntax highlighting style for code blocks."""
        return self._style

    @syntax_highlighting_style.setter
    def syntax_highlighting_style(self, syntax_highlighting_style: type[PygmentsStyle]):
        self._style = syntax_highlighting_style
        self._build_markdown()

    @property
    def blitter(self) -> Blitter:
        """Determines how images are rendered."""
        return self._blitter

    @blitter.setter
    def blitter(self, blitter: Blitter):
        self._blitter = blitter
        for child in self.walk():
            if isinstance(child, Graphics):
                child.blitter = blitter

    def _build_markdown(self):
        if not self.root:
            return

        with _BatgrlRenderer(
            self._scroll_view.port_width, self.syntax_highlighting_style, self.blitter
        ) as renderer:
            rendered = renderer.render(Document(self.markdown))

        if self._scroll_view.view is not None:
            self._scroll_view.view.destroy()
        self._scroll_view.view = rendered

    def update_theme(self):
        """Paint the gadget with current theme."""
        title_fg = Themable.get_color("markdown_title_fg")
        title_bg = Themable.get_color("markdown_title_bg")
        title_cell = new_cell(fg_color=title_fg, bg_color=title_bg)
        self._link_hint.default_cell = title_cell
        self._link_hint.clear()
        content = cast(Text, self._link_hint.content)
        content.default_cell = title_cell
        content.clear()
        self._build_markdown()

    def on_size(self):
        """Rebuild markdown on resize."""
        super().on_size()
        self._build_markdown()

    def on_add(self):
        """Build markdown on add."""
        super().on_add()
        self._build_markdown()

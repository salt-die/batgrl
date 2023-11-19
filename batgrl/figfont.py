r"""
Support for loading and rendering FIGfonts.

A `FIGFont` (class) represents a FIGfont (file) which describe how to render ascii art
from normal text. `FIGFont.render_array` will render the ascii art into a numpy array
that can be copied into a `Text` canvas. `FIGFont.render_str` will render the ascii art
into a multiline string.

References
----------
- http://www.figlet.org/
- http://www.jave.de/figlet/figfont.html
- https://github.com/cmatsuoka/figlet
- https://github.com/pwaller/pyfiglet

See Also
--------
- http://www.figlet.org/fontdb.cgi
- https://github.com/salt-die/fig-fonts
"""
import re
import zipfile
from dataclasses import dataclass, field, fields
from enum import IntFlag
from itertools import islice
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from wcwidth import wcswidth, wcwidth

__all__ = ["FullLayout", "FIGFont"]


class FullLayout(IntFlag):
    r"""
    A layout controls how characters are fitted in rendered text.

    The layout modes are:
    - FullWidth: Each character occupies the full width or height of its arrangement of
    sub-characters.
    - Kerning: Each character is moved together until they touch.
    - Smushing: Each character is moved one step closer after they touch, so that they
    overlap. Additional smushing rules determine which sub-character is used for each
    overlap.

    There are two types of smushing:
    - Universal: The sub-character from the earlier character is replaced by the
    sub-character from the later character. (This behavior can be reversed with
    `reverse_universal_smush`)
    - Controlled: Uses a set of smushing rules.

    The controlled smushing rules are:
    - Equal: Two sub-characters are smushed into a single sub-character if they are
    equal (except for hardblanks).
    - Underscore: An underscore (`"_"`) will be replaced by any of: `"|"`, `"/"`,
    `"\\"`, `"["`, `"]"`, `"{"`, `"}"`, `"("`, `")"`, `"<"`, `">"`.
    - Hierarchy: A hierarchy of six classes is used: `"|"`, `"/\"`, `"[]"`, `"{}"`,
    `"()"`, and `"<>"`. When two sub-characters are from different classes, the latter
    class will be used.
    - Pair: Replaces opposite brackets (`"[]"` or `"]["`), braces (`"{}"` or `"}{"`),
    and parentheses (`"()"` or `")("`) with a vertical bar (`"|"`).
    - BigX: Replaces `"/\\"` with `"|"`, `"\\/"` with `"Y"`, and `"><"` into `"X"`.
    - HardBlank: Two hardblanks will be replaced with a single hardblank.
    """

    FullWidth = 0
    Equal = 1
    Underscore = 2
    Hierarchy = 4
    Pair = 8
    BigX = 16
    HardBlank = 32
    Kerning = 64
    Universal = 128
    # TODO: Add vertical smushing.

    @classmethod
    def from_old_layout(cls, old_layout: int) -> "FullLayout":
        """Return a full layout from an old layout."""
        return {-1: cls.FullWidth, 0: cls.Kerning}.get(
            old_layout, cls(old_layout | 128)
        )


@dataclass
class FIGFont:
    """
    An object representation of a FIGfont.

    Parameters
    ----------
    hardblank : str, default: "$"
        This character is used to represent whitespace that shouldn't be smushed.

    reverse_text : bool, default: False
        If true, text will be rendered right-to-left.

    layout : FullLayout, default: FullLayout.Universal
        Controls how characters are fitted in rendered text.

    reverse_universal_smush : bool, default: False
        If set to true univeral smushing will display earliest sub-character (instead of
        latest).

    font : dict[str, NDArray[np.dtype("<U1")]], default: {}
        A dictionary of characters to their ascii art representations.

    comments : str, default: ""
        Additional comments about this font.

    Attributes
    ----------
    hardblank : str
        This character is used to represent whitespace that shouldn't be smushed.

    reverse_text : bool
        If true, text will be rendered right-to-left.

    layout : FullLayout.Universal
        Controls how characters are fitted in rendered text.

    reverse_universal_smush : bool
        If set to true univeral smushing will display earliest sub-character (instead of
        latest).

    font : dict[str, NDArray[np.dtype("<U1")]]
        A dictionary of characters to their ascii art representations.

    comments : str
        Additional comments about this font.

    Methods
    -------
    from_path(path):
        Load a FIGFont from a path.

    render_array(text):
        Render text as ascii art into a 2D "<U1" numpy array.

    render_str(text):
        Render text as ascii art into a multiline string.
    """

    hardblank: str = "$"
    """
    This character is used to represent whitespace that shouldn't be smushed.
    """

    reverse_text: bool = False
    """
    If true, text will be rendered right-to-left.
    """

    layout: FullLayout = FullLayout.Universal
    """
    Controls how characters are fitted in rendered text.
    """

    reverse_universal_smush: bool = False
    """
    If set to true univeral smushing will display earliest sub-character (instead of
    latest).
    """

    font: dict[str, NDArray[np.dtype("<U1")]] = field(repr=False, default_factory=dict)
    """
    A dictionary of characters to their ascii art representations.
    """

    comments: str = field(repr=False, default="")
    """
    Additional comments about this font.
    """

    @classmethod
    def from_dict(cls, d: dict) -> "FIGFont":
        """Return a FIGFont from a dictionary."""
        return cls(**{f.name: d[f.name] for f in fields(cls) if f.init and f.name in d})

    @classmethod
    def from_path(cls, path: Path) -> "FIGFont":
        """Load a FIGFont from a path."""
        HEADER_RE = (
            r"^[tf]lf2.(?P<hardblank>.) (?P<height>\d+) \d+ \d+ "
            r"(?P<old_layout>-?\d+) (?P<comment_lines>\d+)"
            r"(?: (?P<reverse_text>0|1)"
            r"(?: (?P<layout>\d+)"
            r"(?: \d+)?)?)?\s*$"
        )
        ENDMARKS_RE = re.compile(r"(\S)\1*\s*$")
        NUMBER_RE = re.compile(r"^(0[0-7]*|0x[a-fA-F0-9]+|[1-9]\d*)(?:\s+\w*)?$")

        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as f:
                figdata = f.open(f.namelist()[0]).read()
        else:
            figdata = path.read_bytes()

        header, *lines = figdata.decode(errors="ignore").splitlines()

        if not (m := re.match(HEADER_RE, header)):
            raise ValueError("Invalid FIGfont file.")

        figinfo = m.groupdict()
        for k, v in figinfo.items():
            if isinstance(v, str) and v.removeprefix("-").isdigit():
                figinfo[k] = int(v)

        figinfo["reverse_text"] = bool(figinfo["reverse_text"])

        if figinfo["layout"] is None:
            figinfo["layout"] = FullLayout.from_old_layout(figinfo["old_layout"])
        else:
            figinfo["layout"] = FullLayout(figinfo["layout"])

        figinfo["comments"] = "\n".join(lines[: figinfo["comment_lines"]])
        del lines[: figinfo["comment_lines"]]

        it = iter(lines)
        height = figinfo["height"]

        def consume_char() -> NDArray[np.dtype("<u1")] | None:
            char_lines = [ENDMARKS_RE.sub("", line) for line in islice(it, height)]
            if len(char_lines) < height:
                return None

            width = max(wcswidth(line) for line in char_lines)
            if width < 0:
                return None

            char = np.full((height, width), " ")
            for i, line in enumerate(char_lines):
                j = 0
                for subchar in line:
                    cwidth = wcwidth(subchar)
                    if cwidth == 0:
                        continue

                    char[i, j] = subchar

                    if cwidth == 2:
                        char[i, j + 1] = ""

                    j += cwidth

            return char

        font = {}
        for i in range(32, 127):
            font[chr(i)] = consume_char()

        for char in "ÄÖÜäöüß":
            font[char] = consume_char()

        # ! No support for control files, so remaining code tags will be interpreted as
        # ! unicode code points (negative code tags will be skipped).
        for line in it:
            if not (m := NUMBER_RE.match(line)):
                continue

            cap = m.group(1)
            if cap.startswith("0x"):
                code_tag = int(cap, 16)
            elif cap.startswith("0"):
                code_tag = int(cap, 8)
            else:
                code_tag = int(cap)

            if (fig_char := consume_char()) is not None:
                font[chr(code_tag)] = fig_char

        figinfo["font"] = font
        return cls.from_dict(figinfo)

    @property
    def height(self) -> int:
        """Height of characters in this font."""
        return next(v for v in self.font.values() if v is not None).shape[0]

    def _trim_char(
        self, fig_char: NDArray[np.dtype("<U1")]
    ) -> NDArray[np.dtype("<U1")]:
        """Remove leading and trailing whitespace."""
        while fig_char.shape[1] and (fig_char[:, 0] == " ").all():
            fig_char = fig_char[:, 1:]

        while fig_char.shape[1] and (fig_char[:, -1] == " ").all():
            fig_char = fig_char[:, :-1]

        return fig_char

    def _smush_subchar(self, a: str, b: str) -> str | None:
        """
        Attempt to smush two sub-characters given the current layout.
        If smushing fails, return None, else return the smushed sub-character.
        """
        if a.isspace():
            return b

        if b.isspace():
            return a

        # Universal smushing
        if not self.layout & 63:
            if a == self.hardblank:
                return b

            if b == self.hardblank:
                return a

            return a if self.reverse_text ^ self.reverse_universal_smush else b

        if (
            self.layout & FullLayout.HardBlank
            and a == self.hardblank
            and b == self.hardblank
        ):
            return a

        if a == self.hardblank or b == self.hardblank:
            return None

        if self.layout & FullLayout.Equal and a == b:
            return a

        smushes = []
        if self.layout & FullLayout.Underscore:
            smushes.append(("_", "|/\\[]{}()<>"))

        if self.layout & FullLayout.Hierarchy:
            smushes.extend(
                (
                    ("|", "|/\\[]{}()<>"),
                    ("\\/", "[]{}()<>"),
                    ("[]", "{}()<>"),
                    ("{}", "()<>"),
                    ("()", "<>"),
                )
            )

        for low, high in smushes:
            if a in low and b in high:
                return b
            if b in low and a in high:
                return a

        ab = b + a if self.reverse_text else a + b
        if self.layout & FullLayout.Pair and ab in {"[]", "][", "()", ")(", "{}", "}{"}:
            return "|"

        if self.layout & FullLayout.BigX:
            if ab == "/\\":
                return "|"
            if ab == "\\/":
                return "Y"
            if ab == "><":
                return "X"

    def _smush(
        self, a: NDArray[np.dtype("<U1")], b: NDArray[np.dtype("<U1")]
    ) -> list[str] | None:
        """
        Attempt to smush two columns of sub-characters.

        If smushing fails, return None, else return the smushed column as a list of
        characters.
        """
        c = []
        for sub_a, sub_b in zip(a, b):
            if sub_c := self._smush_subchar(sub_a, sub_b):
                c.append(sub_c)
            else:
                return None
        return c

    def _add_char(
        self, buffer: NDArray[np.dtype("<U1")], prev_char_width: int, char: str
    ) -> tuple[NDArray[np.dtype("<U1")], int]:
        """Add a character to the line buffer."""
        fig_char = self.font.get(char, self.font.get("\x00"))
        if fig_char is None:
            return buffer, 0
        else:
            fig_char = fig_char.copy()

        if self.layout:
            fig_char = self._trim_char(fig_char)
        current_char_width = fig_char.shape[1]
        a, b = (fig_char, buffer) if self.reverse_text else (buffer, fig_char)

        # If characters are wide enough and any smushing rule (controlled or universal)
        # is enabled, attempt to smush the last column of a with the first column of b.
        if (
            prev_char_width >= 2
            and current_char_width >= 2
            and self.layout & 191
            and (c := self._smush(a[:, -1], b[:, 0]))
        ):
            a[:, -1] = c
            b = b[:, 1:]

        return np.concatenate((a, b), axis=1), current_char_width

    def _render_line(self, line: str) -> NDArray[np.dtype("<U1")]:
        """Render a single line of text."""
        buffer, prev_char_width = np.zeros((self.height, 0), dtype=str), 0
        for char in line:
            buffer, prev_char_width = self._add_char(buffer, prev_char_width, char)

        buffer[buffer == self.hardblank] = " "
        return buffer

    def render_array(self, text: str) -> NDArray[np.dtype("<U1")]:
        """
        Render text as ascii art into a 2D "<U1" numpy array.

        Parameters
        ----------
        text : str
            Text to render as ascii art into an array.

        Returns
        -------
        NDArray[np.dtype("<U1")]
            The rendered array.
        """
        lines = list(map(self._render_line, text.splitlines()))
        max_width = max(line.shape[1] for line in lines)
        for i, line in enumerate(lines):
            if line.shape[1] != max_width:
                lines[i] = np.pad(
                    line,
                    ((0, 0), (0, max_width - line.shape[1])),
                    constant_values=" ",
                )

        # TODO: Add vertical smushing.

        return np.concatenate(lines, axis=0)

    def render_str(self, text: str) -> str:
        """
        Render text as ascii art into a multiline string.

        Parameters
        ----------
        text : str
            Text to render as ascii art into a multiline string.

        Returns
        -------
        str
            The rendered string.
        """
        return "\n".join("".join(line) for line in self.render_array(text))

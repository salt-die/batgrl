"""Functions and classes for syntax highlighting with tree-sitter."""

from __future__ import annotations

import importlib
from contextlib import suppress
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from tree_sitter import Language, Parser, Query, Range

from ..logging import get_logger

__all__ = ["Highlighter", "TSPoint", "get_highlighter", "register_language"]

logger = get_logger(__name__)

_REGISTERED_HIGHLIGHTERS: dict[str, Highlighter] = {}

type TSPoint = tuple[int, int]
"""A tree-sitter (row, byte_offset) tuple."""


@dataclass
class Highlighter:
    """Language, parser, and queries needed for syntax highlighting."""

    language_name: str
    """Name of language."""
    language: Language
    """A tree-sitter language."""
    parser: Parser
    """A tree-sitter parser for given language."""
    highlights: Query
    """A highlight query for syntax highlighting."""
    injections: Query | None = None
    """Optional injection query for injected languages."""


def register_language(
    language_name: str,
    language: Language,
    highlights_source: str,
    injections_source: str | None = None,
) -> None:
    """
    Register a tree-sitter language and its queries for syntax highlighting.

    Once registered, a ``Highlighter`` for ``language_name`` can be retrieved with
    ``get_highlighter``.

    Parameters
    ----------
    language_name : str
        Name of the language.
    language : tree_sitter.Language
        A tree-sitter language.
    highlights_source : str
        Source for highlight queries.
    injections_source : str | None, default: None
        Optional source for injection queries. Injection language must exist to be
        highlighted.
    """
    parser = Parser(language)
    highlights_query = Query(language, highlights_source)
    if injections_source is not None:
        injections_query = Query(language, injections_source)
    else:
        injections_query = None

    _REGISTERED_HIGHLIGHTERS[language_name] = Highlighter(
        language_name, language, parser, highlights_query, injections_query
    )
    get_highlighter.cache_clear()


def _find_tree_sitter_language(language: str) -> Language | None:
    with suppress(ImportError):
        tree_module = importlib.import_module(f"tree_sitter_{language}")
        _lang: object = tree_module.language()
        return Language(_lang)

    with suppress(ImportError):
        tree_module = importlib.import_module("tree_sitter_language_pack")
        with suppress(LookupError):
            return tree_module.get_language(language)


@cache
def get_highlighter(language: str) -> Highlighter | None:
    """
    Return a highlighter for a given language.

    Parameters
    ----------
    language : str
        Name of the language.

    Returns
    -------
    Highlighter | None
        Highlighter for a given language if found.
    """
    if language in _REGISTERED_HIGHLIGHTERS:
        return _REGISTERED_HIGHLIGHTERS[language]

    tree_lang = _find_tree_sitter_language(language)
    if tree_lang is None:
        logger.info("Could not load '%s' tree-sitter Language.", language)
        return None

    parser = Parser(tree_lang)

    queries_path = Path(__file__).parent / language
    highlights_path = queries_path / "highlights.scm"
    if not highlights_path.exists():
        logger.info(
            "Highlight query for '%s' language not found at '%s'.",
            language,
            highlights_path.resolve(),
        )
        return None
    highlights = Query(tree_lang, highlights_path.read_text())

    injections_path = queries_path / "injections.scm"
    if not injections_path.exists():
        injections = None
    else:
        injections = Query(tree_lang, injections_path.read_text())

    return Highlighter(language, tree_lang, parser, highlights, injections)


def changed_ranges_point_range(changed_ranges: list[Range]) -> tuple[TSPoint, TSPoint]:
    """
    Combine a syntax tree's changed ranges into a single range.

    Parameters
    ----------
    changed_ranges : list[Range]
        Non-empty list of changed ranges.

    Returns
    -------
    tuple[TSPoint, TSPoint]
        Combined range of changed ranges.
    """
    min_y = changed_ranges[0].start_point[0]
    max_y = changed_ranges[0].end_point[0]
    for range_ in changed_ranges:
        if range_.start_point[0] < min_y:
            min_y = range_.start_point[0]
        if range_.end_point[0] > max_y:
            max_y = range_.end_point[0]

    min_y -= 2
    if min_y < 0:
        min_y = 0

    return (min_y, 0), (max_y + 2, 0)

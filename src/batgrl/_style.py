"""
The graphic rendition parameters of a terminal cell (e.g., bold, italic, etc.).

Some time between numpy v2.0.0 and v2.1.0, numpy started casting IntFlag to int64 (See:
https://github.com/numpy/numpy/issues/28199 and https://github.com/numpy/numpy/issues/27540
). This prevents using IntFlag in bitwise operations with uint arrays. So, to remedy
this, this module defines an IntFlag-like enum using numpy dtypes instead. ``Style``
then uses this enum so that bitwise operations on uint arrays work as expected, in
particular, with the ``"style"`` field of ``Text.canvas``.
"""

from enum import KEEP, Flag, ReprEnum
from typing import no_type_check

import numpy as np

__all__ = ["Style", "Uint8Flag"]


def is_single_bit(n: np.integer):
    """Whether a single bit is set in ``n``."""
    if n == 0:
        return False
    return n & (n - 1) == 0


def bit_length(n: np.integer):
    """Return the number of bits necessary to represent ``n`` in binary."""
    return np.ceil(np.log2(n + 1)).astype(type(n))


class NpFlag(Flag, boundary=KEEP):
    """
    Flag-type enum for numpy dtypes.

    Boundary type must be KEEP as support for other boundary types is removed.
    """

    @no_type_check
    @classmethod
    def _missing_(cls, value):
        # Would like for `NpFlag(1)` and similar to work.
        if not isinstance(value, cls._member_type_):
            try:
                value = cls._member_type_(value)
            except (ValueError, OverflowError):  # ? Are there other errors to catch?
                raise ValueError("%r is not a valid %s" % (value, cls.__qualname__))

        # Masks set by EnumType will be 0 since values don't pass isinstance(value, int)
        # checks, so we fix that here.
        if cls._flag_mask_ == 0:
            cls._flag_mask_ = 0
            cls._singles_mask_ = 0
            for member in cls.__members__.values():
                if is_single_bit(member.value):
                    cls._singles_mask_ |= member.value
                cls._flag_mask_ |= member.value
            cls._all_bits_ = 2 ** bit_length(cls._flag_mask_) - 1

        flag_mask = cls._flag_mask_
        singles_mask = cls._singles_mask_
        all_bits = cls._all_bits_
        neg_value = None
        if not ~all_bits <= value <= all_bits or value & (all_bits ^ flag_mask):
            if value < 0:
                value = max(all_bits + 1, 2 ** (bit_length(value))) + value
        if value < 0:
            neg_value = value
            value = all_bits + 1 + value

        unknown = value & ~flag_mask
        aliases = value & ~singles_mask
        member_value = value & singles_mask

        if cls._member_type_ is object:
            pseudo_member = object.__new__(cls)
        else:
            pseudo_member = cls._member_type_.__new__(cls, value)

        if not hasattr(pseudo_member, "_value_"):
            pseudo_member._value_ = value

        if member_value or aliases:
            members = []
            combined_value = 0
            for m in cls._iter_member_(member_value):
                members.append(m)
                combined_value |= m._value_
            if aliases:
                value = member_value | aliases
                for _, pm in cls._member_map_.items():
                    if (
                        pm not in members
                        and pm._value_
                        and pm._value_ & value == pm._value_
                    ):
                        members.append(pm)
                        combined_value |= pm._value_
            unknown = value ^ combined_value
            pseudo_member._name_ = "|".join([m._name_ for m in members])
            if not combined_value:
                pseudo_member._name_ = None
            elif unknown:
                pseudo_member._name_ += f"|{cls._numeric_repr_(unknown)}"
        else:
            pseudo_member._name_ = None

        pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        if neg_value is not None:
            cls._value2member_map_[neg_value] = pseudo_member
        return pseudo_member


class Uint8Flag(np.uint8, ReprEnum, NpFlag):  # type: ignore
    """Integer flag with ``numpy.uint8``."""


class Style(Uint8Flag):
    """The graphic rendition parameters of a terminal cell."""

    NO_STYLE = 0
    BOLD = 0b1
    ITALIC = 0b10
    UNDERLINE = 0b100
    STRIKETHROUGH = 0b1000
    OVERLINE = 0b10000
    REVERSE = 0b100000

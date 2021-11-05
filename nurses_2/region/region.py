from .band import Band

_EMPTY_BAND = Band(0, 0, [])


class Region:
    """
    Collection of mutually exclusive, sorted bands.
    """
    __slots__ = "bands",

    def __init__(self, area: list[Band]):
        match area:
            case list():
                self.bands = area
            case _:
                self.bands = [ Band(0, area.height, [0, area.width]) ]

    def _reband(self, widget):
        """
        Adjust bands' top and bottoms to fit widget's rect. Return a region that
        covers widget.
        """
        bands = self.bands
        widget_bands = [ Band(widget.top, widget.bottom, [widget.left, widget.right]) ]

        i = 0
        while i < len(bands):
            band = bands[i]
            widget_band = widget_bands[-1]

            if band.top < widget_band.top < band.bottom:
                bands.insert(i + 1, band.split(widget_band.top))
            elif band.top < widget_band.bottom < band.bottom:
                bands.insert(i + 1, band.split(widget_band.bottom))
            elif widget_band.top < band.top < widget_band.bottom:
                widget_bands.append(widget_band.split(band.top))
            elif widget_band.top < band.bottom < widget_band.bottom:
                widget_bands.append(widget_band.split(band.bottom))
            elif band.top >= widget_band.bottom:
                break

            i += 1

        return Region(widget_bands)

    def _divmod(self, other):
        self_bands = iter(self.bands)
        other_bands = iter(other.bands)

        self_band = next(self_bands, None)
        other_band = next(other_bands, None)

        while self_band is not None or other_band is not None:
            if (
                other_band is None
                or self_band is not None and self_band.top < other_band.top
            ):
                self_band.divmod(_EMPTY_BAND)
                self_band = next(self_bands, None)

            elif self_band is None or other_band.top < self_band.top:
                other_band.divmod(_EMPTY_BAND)
                other_band = next(other_bands, None)

            else:
                self_band.divmod(other_band)
                self_band = next(self_bands, None)
                other_band = next(other_bands, None)

    def _coalesce(self):
        """
        Join contiguous bands that have identical walls.
        """
        bands = self.bands

        i = 0
        while i < len(bands) - 1:
            a, b = bands[i], bands[i + 1]
            if not a.walls:
                bands.pop(i)
            elif not b.walls:
                bands.pop(i + 1)
            elif a.top <= b.top <= a.bottom and a.walls == b.walls:
                a.bottom = b.bottom
                bands.pop(i + 1)
            else:
                i += 1

    def divmod(self, other):
        widget_region = self._reband(other)
        self._divmod(widget_region)

        self._coalesce()
        widget_region._coalesce()

        return widget_region

    @property
    def slices(self):
        for band in self.bands:
            yield from band.slices

    def __repr__(self):
        attrs = ', '.join(
            f'{attr}={getattr(self, attr)}'
            for attr in self.__slots__
        )
        return f'{type(self).__name__}({attrs})'

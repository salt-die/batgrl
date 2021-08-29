from typing import List, Optional, Union

from ..keys import Keys


class KeyPress:
    """
    :param key: A `Keys` instance or text (one character).
    :param data: The received string on stdin. (Often vt100 escape codes.)
    """

    def __init__(self, key: Union[Keys, str], data: Optional[str] = None) -> None:
        assert isinstance(key, Keys) or len(key) == 1

        if data is None:
            if isinstance(key, Keys):
                data = key.value
            else:
                data = key  # 'key' is a one character string.

        self.key = key
        self.data = data

    def __repr__(self) -> str:
        return "%s(key=%r, data=%r)" % (self.__class__.__name__, self.key, self.data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyPress):
            return False
        return self.key == other.key and self.data == other.data

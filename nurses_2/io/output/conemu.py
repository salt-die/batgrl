from .vt100 import Vt100_Output
from .windows10 import Windows10_Output


class ConEmuOutput(Windows10_Output):
    """
    ConEmu (Windows) output.
    """

    # Same as Windows10_Output except the `flush` method is from `Vt100_Output`
    flush = Vt100_Output.flush

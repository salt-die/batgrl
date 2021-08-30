import os
import sys

def is_windows():
    """
    True when we are using Windows.
    """
    return sys.platform.startswith("win")  # E.g. 'win32', not 'darwin' or 'linux2'

def is_conemu_ansi():
    """
    True when the ConEmu Windows console is used.
    """
    return is_windows() and os.environ.get("ConEmuANSI", "OFF") == "ON"

def get_bell_environment_variable():
    """
    True if env variable is set to true (true, TRUE, TrUe, 1).
    """
    value = os.environ.get("PROMPT_TOOLKIT_BELL", "true")
    return value.lower() in ("1", "true")

def get_term_environment_variable():
    """
    Return the $TERM environment variable.
    """
    return os.environ.get("TERM", "")

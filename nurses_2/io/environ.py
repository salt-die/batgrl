import os
import platform

def is_windows():
    """
    Return True on Windows.
    """
    return platform.system() == "Windows"

def is_conemu_ansi():
    """
    Return True if using ConEmu.
    """
    return os.environ.get("ConEmuANSI", "OFF") == "ON"

def get_term_environment_variable():
    """
    Return the $TERM environment variable.
    """
    return os.environ.get("TERM", "")

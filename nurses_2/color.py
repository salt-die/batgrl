"""
Module to grab escape codes / winattrs directly from rgb-tuples.  The goal will be to avoid the constant lookups when rendering
- we can store the escapes directly in a numpy array.
"""
from .app import get_running_app
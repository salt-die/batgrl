"""
Base output for an app.
"""
from abc import ABC, abstractmethod

from ...gadgets._root import _Root


class Output(ABC):
    """Abtract output for an app."""

    @abstractmethod
    def get_size(self):
        """Get size of app."""

    @abstractmethod
    def set_title(self, title):
        """Set title of app."""

    @abstractmethod
    def __enter__(self):
        """Setup output for app."""

    @abstractmethod
    def __exit__(self):
        """Teardown output for app."""

    @abstractmethod
    def render_frame(self, root: _Root):
        """Render the app to output."""
